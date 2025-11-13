import asyncio
import re
from typing import List, Dict

class USBManager:
    MOBILE_DEVICE_KEYWORDS = [
        'samsung', 'galaxy', 'mediatek', 'qualcomm', 'android',
        'phone', 'tablet', 'mobile', 'mtp', 'adb', 'fastboot',
        'xiaomi', 'huawei', 'oppo', 'vivo', 'oneplus', 'lg',
        'motorola', 'google', 'pixel', 'nexus', 'htc', 'sony',
        'asus', 'lenovo', 'nokia', 'realme', 'tecno', 'infinix',
        'zte', 'alcatel', 'blackberry', 'meizu', 'cyrus'
    ]

    EXCLUDE_KEYWORDS = [
        'root hub', 'keyboard', 'mouse', 'hub', 'virtual hub',
        'ethernet', 'bluetooth', 'audio', 'webcam', 'camera'
    ]

    @staticmethod
    def is_mobile_device(description: str, vendor_id: str) -> bool:
        description_lower = description.lower()

        for exclude in USBManager.EXCLUDE_KEYWORDS:
            if exclude in description_lower:
                return False

        for keyword in USBManager.MOBILE_DEVICE_KEYWORDS:
            if keyword in description_lower:
                return True

        known_mobile_vendors = ['04e8', '0e8d', '2717', '18d1', '2a70']
        if vendor_id in known_mobile_vendors:
            return True

        return False

    @staticmethod
    async def get_serial_number(bus: str, device: str) -> str:
        try:
            result = await asyncio.create_subprocess_exec(
                'lsusb', '-v', '-s', f"{bus}:{device}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return 'N/A'

            content = stdout.decode()
            serial_match = re.search(r'iSerial\s+\d+\s+(.+)', content)
            if serial_match:
                serial = serial_match.group(1).strip()
                return serial if serial else 'N/A'

            return 'N/A'

        except Exception as e:
            print(f"Error getting serial number: {e}")
            return 'N/A'

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

            mobile_devices = []
            for line in lines:
                match = re.match(r'Bus (\d+) Device (\d+): ID ([0-9a-f]{4}):([0-9a-f]{4}) (.+)', line)
                if match:
                    bus, device, vendor_id, product_id, description = match.groups()

                    if USBManager.is_mobile_device(description, vendor_id):
                        mobile_devices.append((bus, device, vendor_id, product_id, description))

            for bus, device, vendor_id, product_id, description in mobile_devices:
                serial = await USBManager.get_serial_number(bus, device)
                device_info = {
                    'id': f"{bus}-{device}",
                    'bus': bus,
                    'device': device,
                    'vendor_id': vendor_id,
                    'product_id': product_id,
                    'description': description.strip(),
                    'serial': serial,
                    'status': 'connected'
                }
                devices.append(device_info)

            print(f"Total mobile devices found: {len(devices)}")
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
