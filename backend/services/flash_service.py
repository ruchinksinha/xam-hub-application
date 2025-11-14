import os
import aiohttp
import asyncio
import hashlib
import traceback
from pathlib import Path
from typing import Dict, Optional, Tuple

class FlashService:
    def __init__(self):
        self.download_dir = Path("/tmp/lineage_downloads")
        self.download_dir.mkdir(exist_ok=True)
        self.flash_status = {}
        self.os_cache = {}

    def get_os_filename(self, os_url: str) -> str:
        """Get consistent filename for OS image"""
        url_hash = hashlib.md5(os_url.encode()).hexdigest()[:8]
        filename = os_url.split('/')[-1]

        # Keep original extension if it's a supported format
        if not filename.endswith(('.zip', '.img')):
            # Default to .zip for LineageOS (most common format)
            filename = f"lineage_{url_hash}.zip"

        return filename

    def check_os_cached(self, os_url: str) -> Tuple[bool, Optional[str]]:
        """Check if OS image is already downloaded"""
        filename = self.get_os_filename(os_url)
        file_path = self.download_dir / filename

        if file_path.exists() and file_path.stat().st_size > 0:
            return True, str(file_path)
        return False, None

    async def download_os_image(self, os_url: str, device_id: str) -> Optional[str]:
        """Download OS image and return local file path"""
        try:
            filename = self.get_os_filename(os_url)
            file_path = self.download_dir / filename

            is_cached, cached_path = self.check_os_cached(os_url)
            if is_cached:
                self.flash_status[device_id] = {
                    'status': 'cached',
                    'progress': 100,
                    'message': 'OS image already available',
                    'download_progress': 100,
                    'download_size': file_path.stat().st_size
                }
                return cached_path

            self.flash_status[device_id] = {
                'status': 'downloading',
                'progress': 0,
                'message': 'Downloading OS image...',
                'download_progress': 0,
                'download_size': 0
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(os_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download: HTTP {response.status}")

                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0

                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                download_progress = int((downloaded / total_size) * 100)
                                self.flash_status[device_id].update({
                                    'download_progress': download_progress,
                                    'download_size': downloaded,
                                    'total_size': total_size
                                })

            self.flash_status[device_id]['status'] = 'download_complete'
            self.flash_status[device_id]['message'] = 'Download completed'
            return str(file_path)
        except Exception as e:
            error_detail = str(e)
            error_trace = traceback.format_exc()
            print(f"Download error for {device_id}: {error_detail}")
            print(f"Traceback: {error_trace}")
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Download failed: {error_detail}',
                'error_detail': error_detail,
                'error_trace': error_trace
            }
            raise

    async def reboot_to_recovery(self, device_id: str) -> bool:
        """Reboot device to recovery mode"""
        try:
            self.flash_status[device_id] = {
                'status': 'rebooting',
                'progress': 30,
                'message': 'Rebooting to recovery mode...'
            }

            result = await asyncio.create_subprocess_exec(
                'adb', '-s', device_id, 'reboot', 'recovery',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            stderr_text = stderr.decode()
            # ADB daemon startup messages are not errors
            if result.returncode != 0 and not ('daemon started successfully' in stderr_text or 'daemon not running' in stderr_text):
                raise Exception(f"Failed to reboot: {stderr_text}")

            # Wait longer for recovery to fully boot
            await asyncio.sleep(20)
            return True
        except Exception as e:
            error_detail = str(e)
            error_trace = traceback.format_exc()
            print(f"Reboot error for {device_id}: {error_detail}")
            print(f"Traceback: {error_trace}")
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 30,
                'message': f'Reboot failed: {error_detail}',
                'error_detail': error_detail,
                'error_trace': error_trace
            }
            raise

    async def sideload_via_recovery(self, device_id: str, image_path: str) -> bool:
        """Sideload image via ADB in recovery mode"""
        try:
            self.flash_status[device_id] = {
                'status': 'preparing_sideload',
                'progress': 50,
                'message': 'Preparing to sideload OS image...'
            }

            # Wait for device to be in sideload mode
            await asyncio.sleep(5)

            self.flash_status[device_id] = {
                'status': 'sideloading',
                'progress': 60,
                'message': 'Sideloading OS image (this may take several minutes)...'
            }

            # Use adb sideload to flash the image
            result = await asyncio.create_subprocess_exec(
                'adb', 'sideload', image_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            stdout_text = stdout.decode()
            stderr_text = stderr.decode()

            print(f"Sideload stdout: {stdout_text}")
            print(f"Sideload stderr: {stderr_text}")

            # Sideload returns 1 even on success sometimes, check output
            if 'failed' in stderr_text.lower() or 'error' in stderr_text.lower():
                if 'closed' not in stderr_text.lower():  # "closed" is normal after successful sideload
                    raise Exception(f"Sideload failed: {stderr_text}")

            self.flash_status[device_id] = {
                'status': 'rebooting',
                'progress': 90,
                'message': 'Installation complete. Rebooting device...'
            }

            await asyncio.sleep(10)

            return True
        except Exception as e:
            error_detail = str(e)
            error_trace = traceback.format_exc()
            print(f"Sideload error for {device_id}: {error_detail}")
            print(f"Traceback: {error_trace}")
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 70,
                'message': f'Sideload failed: {error_detail}',
                'error_detail': error_detail,
                'error_trace': error_trace
            }
            raise

    async def prepare_os_download(self, device_id: str, os_url: str) -> Dict[str, any]:
        """Prepare OS download and check if cached"""
        try:
            is_cached, cached_path = self.check_os_cached(os_url)

            if is_cached:
                file_size = Path(cached_path).stat().st_size
                self.flash_status[device_id] = {
                    'status': 'awaiting_confirmation',
                    'progress': 0,
                    'message': 'OS image ready. Awaiting flash confirmation...',
                    'os_cached': True,
                    'os_size': file_size,
                    'os_path': cached_path
                }
                return {
                    'cached': True,
                    'path': cached_path,
                    'size': file_size
                }
            else:
                self.flash_status[device_id] = {
                    'status': 'awaiting_download',
                    'progress': 0,
                    'message': 'Ready to download OS image...',
                    'os_cached': False
                }
                return {
                    'cached': False
                }
        except Exception as e:
            raise

    async def flash_device_complete(self, device_id: str, os_url: str, skip_download: bool = False) -> Dict[str, str]:
        """Complete flash process"""
        try:
            if not skip_download:
                self.flash_status[device_id] = {
                    'status': 'starting',
                    'progress': 0,
                    'message': 'Initializing flash process...'
                }

                image_path = await self.download_os_image(os_url, device_id)

                self.flash_status[device_id]['status'] = 'awaiting_confirmation'
                self.flash_status[device_id]['message'] = 'Download complete. Awaiting confirmation...'

                return {
                    'success': True,
                    'message': 'Download complete. Awaiting confirmation.'
                }
            else:
                is_cached, image_path = self.check_os_cached(os_url)
                if not is_cached:
                    raise Exception("OS image not found in cache")

            self.flash_status[device_id] = {
                'status': 'flashing_started',
                'progress': 30,
                'message': 'Starting flash process...'
            }

            # Reboot to recovery mode for sideloading
            await self.reboot_to_recovery(device_id)

            # Sideload the image file
            await self.sideload_via_recovery(device_id, image_path)

            self.flash_status[device_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Flash completed successfully'
            }

            return {
                'success': True,
                'message': 'Flash completed successfully'
            }
        except Exception as e:
            error_detail = str(e)
            error_trace = traceback.format_exc()
            print(f"Complete flash error for {device_id}: {error_detail}")
            print(f"Traceback: {error_trace}")
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Flash failed: {error_detail}',
                'error_detail': error_detail,
                'error_trace': error_trace
            }
            return {
                'success': False,
                'message': error_detail
            }

    def get_flash_status(self, device_id: str) -> Dict:
        """Get current flash status for a device"""
        return self.flash_status.get(device_id, {
            'status': 'idle',
            'progress': 0,
            'message': 'No flash operation in progress'
        })

    def check_os_availability(self, os_url: str) -> Dict:
        """Check if OS is available for flashing"""
        is_cached, cached_path = self.check_os_cached(os_url)
        if is_cached:
            file_size = Path(cached_path).stat().st_size
            return {
                'available': True,
                'size': file_size,
                'path': cached_path
            }
        return {
            'available': False
        }

flash_service = FlashService()
