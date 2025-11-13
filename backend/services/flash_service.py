import os
import aiohttp
import asyncio
from pathlib import Path
from typing import Dict, Optional

class FlashService:
    def __init__(self):
        self.download_dir = Path("/tmp/lineage_downloads")
        self.download_dir.mkdir(exist_ok=True)
        self.flash_status = {}

    async def download_os_image(self, os_url: str, device_id: str) -> Optional[str]:
        """Download OS image and return local file path"""
        try:
            filename = os_url.split('/')[-1]
            if not filename.endswith('.zip'):
                filename = f"lineage_{device_id}.zip"

            file_path = self.download_dir / filename

            self.flash_status[device_id] = {
                'status': 'downloading',
                'progress': 0,
                'message': 'Downloading OS image...'
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
                                progress = int((downloaded / total_size) * 100)
                                self.flash_status[device_id]['progress'] = progress

            return str(file_path)
        except Exception as e:
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Download failed: {str(e)}'
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

            if result.returncode != 0:
                raise Exception(f"Failed to reboot: {stderr.decode()}")

            await asyncio.sleep(15)
            return True
        except Exception as e:
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 30,
                'message': f'Reboot failed: {str(e)}'
            }
            raise

    async def push_and_flash(self, device_id: str, image_path: str) -> bool:
        """Push image to device and flash it"""
        try:
            self.flash_status[device_id] = {
                'status': 'pushing',
                'progress': 50,
                'message': 'Pushing OS image to device...'
            }

            result = await asyncio.create_subprocess_exec(
                'adb', '-s', device_id, 'push', image_path, '/sdcard/',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                raise Exception(f"Failed to push image: {stderr.decode()}")

            self.flash_status[device_id] = {
                'status': 'flashing',
                'progress': 70,
                'message': 'Flashing OS image...'
            }

            image_filename = Path(image_path).name
            result = await asyncio.create_subprocess_exec(
                'adb', '-s', device_id, 'shell',
                'twrp', 'install', f'/sdcard/{image_filename}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            await asyncio.sleep(5)

            return True
        except Exception as e:
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 70,
                'message': f'Flash failed: {str(e)}'
            }
            raise

    async def flash_device_complete(self, device_id: str, os_url: str) -> Dict[str, str]:
        """Complete flash process"""
        try:
            self.flash_status[device_id] = {
                'status': 'starting',
                'progress': 0,
                'message': 'Initializing flash process...'
            }

            image_path = await self.download_os_image(os_url, device_id)

            await self.reboot_to_recovery(device_id)

            await self.push_and_flash(device_id, image_path)

            self.flash_status[device_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Flash completed successfully'
            }

            if os.path.exists(image_path):
                os.remove(image_path)

            return {
                'success': True,
                'message': 'Flash completed successfully'
            }
        except Exception as e:
            self.flash_status[device_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Flash failed: {str(e)}'
            }
            return {
                'success': False,
                'message': str(e)
            }

    def get_flash_status(self, device_id: str) -> Dict:
        """Get current flash status for a device"""
        return self.flash_status.get(device_id, {
            'status': 'idle',
            'progress': 0,
            'message': 'No flash operation in progress'
        })

flash_service = FlashService()
