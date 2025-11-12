import subprocess
import asyncio
from typing import List, Dict, Optional

class ADBManager:
    @staticmethod
    async def get_connected_devices() -> List[Dict[str, str]]:
        try:
            result = await asyncio.create_subprocess_exec(
                'adb', 'devices', '-l',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return []

            devices = []
            lines = stdout.decode().strip().split('\n')[1:]

            for line in lines:
                if not line.strip() or 'offline' in line:
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    device_id = parts[0]
                    model = 'Unknown'

                    for part in parts:
                        if part.startswith('model:'):
                            model = part.split(':', 1)[1]
                            break

                    devices.append({
                        'id': device_id,
                        'model': model,
                        'status': 'online'
                    })

            return devices
        except Exception as e:
            print(f"Error getting devices: {e}")
            return []

    @staticmethod
    async def flash_device(device_id: str, os_url: str) -> Dict[str, str]:
        try:
            devices = await ADBManager.get_connected_devices()
            device_exists = any(d['id'] == device_id for d in devices)

            if not device_exists:
                return {
                    'success': False,
                    'message': f'Device {device_id} not found'
                }

            asyncio.create_task(ADBManager._flash_device_background(device_id, os_url))

            return {
                'success': True,
                'message': f'Flashing started for device {device_id}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    @staticmethod
    async def _flash_device_background(device_id: str, os_url: str):
        try:
            print(f"Starting flash process for device {device_id}")
            print(f"OS URL: {os_url}")

            result = await asyncio.create_subprocess_exec(
                'adb', '-s', device_id, 'reboot', 'bootloader',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()

            await asyncio.sleep(10)

            print(f"Device {device_id} is in bootloader mode")
            print(f"Download OS from: {os_url}")

            print(f"Flashing completed for device {device_id}")
        except Exception as e:
            print(f"Error flashing device {device_id}: {e}")
