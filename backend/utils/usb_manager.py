import asyncio
import re
from typing import List, Dict

class USBManager:
    @staticmethod
    async def get_connected_tablets() -> List[Dict[str, str]]:
        try:
            result = await asyncio.create_subprocess_exec(
                'lsusb',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                print(f"lsusb command failed: {stderr.decode()}")
                return []

            devices = []
            lines = stdout.decode().strip().split('\n')

            for line in lines:
                match = re.match(r'Bus (\d+) Device (\d+): ID ([0-9a-f]{4}):([0-9a-f]{4}) (.+)', line)
                if match:
                    bus, device, vendor_id, product_id, description = match.groups()

                    device_info = {
                        'id': f"{bus}-{device}",
                        'bus': bus,
                        'device': device,
                        'vendor_id': vendor_id,
                        'product_id': product_id,
                        'description': description.strip(),
                        'status': 'connected'
                    }
                    devices.append(device_info)

            print(f"Total USB devices found: {len(devices)}")
            return devices

        except Exception as e:
            print(f"Error getting USB devices: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    async def get_device_details(bus: str, device: str) -> Dict[str, any]:
        try:
            result = await asyncio.create_subprocess_exec(
                'lsusb', '-v', '-s', f"{bus}:{device}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return {}

            details = {
                'raw_info': stdout.decode()
            }

            content = stdout.decode()

            manufacturer_match = re.search(r'iManufacturer\s+\d+\s+(.+)', content)
            if manufacturer_match:
                details['manufacturer'] = manufacturer_match.group(1).strip()

            product_match = re.search(r'iProduct\s+\d+\s+(.+)', content)
            if product_match:
                details['product'] = product_match.group(1).strip()

            serial_match = re.search(r'iSerial\s+\d+\s+(.+)', content)
            if serial_match:
                details['serial'] = serial_match.group(1).strip()

            return details

        except Exception as e:
            print(f"Error getting device details: {e}")
            return {}
