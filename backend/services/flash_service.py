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
        if not filename.endswith(('.zip', '.img')):
            filename = f"lineage_{url_hash}.img"
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

    async def reboot_to_bootloader(self, device_id: str) -> bool:
        """Reboot device to bootloader mode"""
        try:
            self.flash_status[device_id] = {
                'status': 'rebooting',
                'progress': 30,
                'message': 'Rebooting to bootloader mode...'
            }

            result = await asyncio.create_subprocess_exec(
                'adb', '-s', device_id, 'reboot', 'bootloader',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            stderr_text = stderr.decode()
            # ADB daemon startup messages are not errors
            if result.returncode != 0 and not ('daemon started successfully' in stderr_text or 'daemon not running' in stderr_text):
                raise Exception(f"Failed to reboot: {stderr_text}")

            await asyncio.sleep(10)
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

    async def flash_image_fastboot(self, device_id: str, image_path: str) -> bool:
        """Flash image using fastboot"""
        try:
            self.flash_status[device_id] = {
                'status': 'flashing',
                'progress': 50,
                'message': 'Flashing OS image via fastboot...'
            }

            # Flash the system image
            result = await asyncio.create_subprocess_exec(
                'fastboot', '-s', device_id, 'flash', 'system', image_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                raise Exception(f"Failed to flash image: {stderr.decode()}")

            self.flash_status[device_id] = {
                'status': 'rebooting',
                'progress': 90,
                'message': 'Rebooting device...'
            }

            # Reboot device
            result = await asyncio.create_subprocess_exec(
                'fastboot', '-s', device_id, 'reboot',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            await asyncio.sleep(5)

            return True
        except Exception as e:
            error_detail = str(e)
            error_trace = traceback.format_exc()
            print(f"Flash error for {device_id}: {error_detail}")
            print(f"Traceback: {error_trace}")
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 70,
                'message': f'Flash failed: {error_detail}',
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

            # Check if image is .img format (use fastboot) or .zip (use TWRP)
            if image_path.endswith('.img'):
                await self.reboot_to_bootloader(device_id)
                await self.flash_image_fastboot(device_id, image_path)
            else:
                # For .zip files, we'd use TWRP recovery (not implemented yet)
                raise Exception("Only .img format is currently supported")

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
