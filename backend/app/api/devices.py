from fastapi import APIRouter, HTTPException
from backend.utils.usb_manager import USBManager
from backend.utils.adb_manager import ADBManager
from backend.utils.hotspot_manager import HotspotManager
from backend.config.settings import get_settings
from backend.services.flash_service import flash_service
from backend.utils.json_storage import json_storage
import subprocess
import os
from pathlib import Path

hotspot_manager = HotspotManager()

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.get("")
async def get_devices():
    usb_devices = await USBManager.get_connected_tablets()
    adb_devices = await ADBManager.get_connected_devices()

    all_registered = json_storage.get_all_devices()
    registered_devices = {d['serial']: d for d in all_registered}

    # Get WiFi hotspot connected clients
    wifi_clients = hotspot_manager.get_connected_clients()
    wifi_ips = {client['ip_address']: client for client in wifi_clients}
    wifi_macs = {client['mac_address']: client for client in wifi_clients}

    # Parse ADB devices to identify WiFi-connected ones
    adb_wifi_devices = {}
    adb_usb_devices = {}
    for adb_dev in adb_devices:
        device_id = adb_dev['id']
        if ':' in device_id:  # WiFi connection (IP:port format)
            ip_address = device_id.split(':')[0]
            adb_wifi_devices[ip_address] = adb_dev
        else:  # USB connection (serial number)
            adb_usb_devices[device_id] = adb_dev

    devices_dict = {}
    connected_serials = set()

    # First, process USB-connected devices
    for device in usb_devices:
        serial = device.get('serial')
        if serial and serial != 'N/A':
            connected_serials.add(serial)
            device['is_registered'] = serial in registered_devices
            device['connection_type'] = 'usb'
            device['wifi_connected'] = False

            if serial in registered_devices:
                device['registered_name'] = registered_devices[serial].get('name', '')
                reg_device = registered_devices[serial]

                # Check if this device is also connected to WiFi and capture its MAC/IP
                device_ip = reg_device.get('wifi_ip', '')
                device_mac = reg_device.get('wifi_mac', '')

                # Try to match by known IP or MAC
                matched_client = None
                if device_ip and device_ip in wifi_ips:
                    matched_client = wifi_ips[device_ip]
                elif device_mac and device_mac in wifi_macs:
                    matched_client = wifi_macs[device_mac]
                else:
                    # Try to match by hostname containing serial or device name
                    for client in wifi_clients:
                        hostname = client.get('hostname', '').lower()
                        if serial.lower() in hostname or reg_device.get('name', '').lower() in hostname:
                            matched_client = client
                            break

                # Update device with WiFi info if found
                update_data = {
                    'is_connected': True,
                    'usb_bus': device.get('bus', ''),
                    'usb_device': device.get('device', ''),
                    'connection_type': 'usb'
                }

                if matched_client:
                    update_data['wifi_ip'] = matched_client['ip_address']
                    update_data['wifi_mac'] = matched_client['mac_address']
                    device['wifi_connected'] = True

                json_storage.update_device(serial, update_data)

            devices_dict[serial] = device
        else:
            device['is_registered'] = False
            device['connection_type'] = 'disconnected'
            device['wifi_connected'] = False
            # Use a unique ID for non-serial devices
            devices_dict[device['id']] = device

    # Add registered devices that are connected via WiFi hotspot but not USB
    for serial, reg_device in registered_devices.items():
        if serial not in connected_serials:
            # Check if this device is connected via ADB WiFi
            device_ip = reg_device.get('wifi_ip', '')
            device_mac = reg_device.get('wifi_mac', '')

            # First check if device is connected via ADB WiFi
            is_adb_wifi = device_ip and device_ip in adb_wifi_devices

            # Also check if device is in WiFi clients (DHCP leases)
            matched_wifi = None
            if device_ip and device_ip in wifi_ips:
                matched_wifi = wifi_ips[device_ip]
            elif device_mac and device_mac in wifi_macs:
                matched_wifi = wifi_macs[device_mac]

            # Consider device WiFi-connected if it's either in ADB WiFi or DHCP leases
            is_wifi_connected = is_adb_wifi or matched_wifi is not None

            if is_wifi_connected:
                adb_info = adb_wifi_devices.get(device_ip, {})
                wifi_device = {
                    'id': serial,
                    'serial': serial,
                    'description': reg_device.get('name', serial),
                    'model': adb_info.get('model') or reg_device.get('model', ''),
                    'manufacturer': reg_device.get('manufacturer', ''),
                    'vendor_id': '',
                    'product_id': '',
                    'bus': '',
                    'device': '',
                    'status': 'ready' if is_adb_wifi else 'connected',
                    'is_registered': True,
                    'registered_name': reg_device.get('name', ''),
                    'connection_type': 'wifi',
                    'wifi_connected': True,
                    'adb_ready': is_adb_wifi,
                    'adb_status': 'online' if is_adb_wifi else 'offline',
                    'wifi_ip': device_ip
                }
                devices_dict[serial] = wifi_device
                connected_serials.add(serial)
                json_storage.update_device(serial, {
                    'is_connected': True,
                    'connection_type': 'wifi',
                    'wifi_ip': device_ip
                })
            else:
                # Device is registered but not connected
                disconnected_device = {
                    'id': serial,
                    'serial': serial,
                    'description': reg_device.get('name', serial),
                    'model': reg_device.get('model', ''),
                    'manufacturer': reg_device.get('manufacturer', ''),
                    'vendor_id': '',
                    'product_id': '',
                    'bus': '',
                    'device': '',
                    'status': 'offline',
                    'is_registered': True,
                    'registered_name': reg_device.get('name', ''),
                    'connection_type': 'disconnected',
                    'wifi_connected': False,
                    'adb_ready': False,
                    'adb_status': 'offline'
                }
                devices_dict[serial] = disconnected_device
                json_storage.update_connection_status(serial, False)

    return {"devices": list(devices_dict.values())}

@router.get("/{bus}/{device}")
async def get_device_details(bus: str, device: str):
    details = await USBManager.get_device_details(bus, device)
    return {"details": details}

@router.get("/os/check")
async def check_os_availability():
    settings = get_settings()
    os_url = settings.LINEAGE_OS_URL

    if not os_url:
        raise HTTPException(
            status_code=500,
            detail="Lineage OS URL not configured"
        )

    availability = flash_service.check_os_availability(os_url)
    return availability

@router.post("/{device_id}/flash/prepare")
async def prepare_flash(device_id: str):
    settings = get_settings()
    os_url = settings.LINEAGE_OS_URL

    if not os_url:
        raise HTTPException(
            status_code=500,
            detail="Lineage OS URL not configured"
        )

    usb_devices = await USBManager.get_connected_tablets()
    usb_device = next((d for d in usb_devices if d['id'] == device_id), None)

    if not usb_device:
        raise HTTPException(
            status_code=404,
            detail=f"USB device {device_id} not found"
        )

    serial = usb_device.get('serial')
    if not serial or serial == 'N/A':
        raise HTTPException(
            status_code=400,
            detail=f"Device {device_id} has no serial number. Make sure USB debugging is enabled."
        )

    adb_devices = await ADBManager.get_connected_devices()
    adb_device_exists = any(d['id'] == serial for d in adb_devices)

    if not adb_device_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Device {serial} not connected via ADB. Please enable USB debugging and authorize this computer."
        )

    import asyncio
    asyncio.create_task(flash_service.flash_device_complete(serial, os_url, skip_download=False))

    return {
        "success": True,
        "message": f"Preparing flash for device {serial}",
        "serial": serial
    }

@router.post("/{device_id}/flash/confirm")
async def confirm_flash(device_id: str):
    usb_devices = await USBManager.get_connected_tablets()
    usb_device = next((d for d in usb_devices if d['id'] == device_id), None)

    if not usb_device:
        raise HTTPException(
            status_code=404,
            detail=f"USB device {device_id} not found"
        )

    serial = usb_device.get('serial')
    if not serial or serial == 'N/A':
        raise HTTPException(
            status_code=400,
            detail=f"Device {device_id} has no serial number."
        )

    settings = get_settings()
    os_url = settings.LINEAGE_OS_URL

    import asyncio
    asyncio.create_task(flash_service.flash_device_complete(serial, os_url, skip_download=True))

    return {
        "success": True,
        "message": f"Flash confirmed for device {serial}"
    }

@router.get("/{device_id}/flash/status")
async def get_flash_status(device_id: str):
    usb_devices = await USBManager.get_connected_tablets()
    usb_device = next((d for d in usb_devices if d['id'] == device_id), None)

    if usb_device:
        serial = usb_device.get('serial')
        if serial and serial != 'N/A':
            status = flash_service.get_flash_status(serial)
            return status

    status = flash_service.get_flash_status(device_id)
    return status

@router.get("/{serial}/flash/status-by-serial")
async def get_flash_status_by_serial(serial: str):
    status = flash_service.get_flash_status(serial)
    return status

@router.post("/{serial}/publish-app")
async def publish_app(serial: str):
    """
    Publish/install an APK to a device using ADB
    """
    try:
        # Get APK path from environment
        apk_path = os.getenv('APK_FILE_PATH', '')

        if not apk_path:
            raise HTTPException(
                status_code=500,
                detail="APK_FILE_PATH not configured in .env file"
            )

        # Check if file exists
        if not Path(apk_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"APK file not found at: {apk_path}"
            )

        # Check if device is connected
        adb_devices = await ADBManager.get_connected_devices()
        device_exists = any(d['id'] == serial for d in adb_devices)

        if not device_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Device {serial} not connected via ADB"
            )

        # Install APK using ADB
        result = subprocess.run(
            ['adb', '-s', serial, 'install', '-r', apk_path],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"App published successfully to device {serial}",
                "output": result.stdout
            }
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise HTTPException(
                status_code=500,
                detail=f"Failed to install app: {error_msg}"
            )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Installation timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error publishing app: {str(e)}"
        )

@router.post("/{serial}/enable-wifi-adb")
async def enable_wifi_adb(serial: str):
    """
    Enable ADB over WiFi for a USB-connected device
    """
    try:
        # Check if device is connected via USB
        adb_devices = await ADBManager.get_connected_devices()
        device_exists = any(d['id'] == serial and ':' not in d['id'] for d in adb_devices)

        if not device_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Device {serial} not connected via USB. Connect via USB first to enable WiFi ADB."
            )

        # Enable TCP/IP mode on port 5555
        result = subprocess.run(
            ['adb', '-s', serial, 'tcpip', '5555'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise HTTPException(
                status_code=500,
                detail=f"Failed to enable WiFi ADB: {error_msg}"
            )

        # Get device IP address
        ip_result = subprocess.run(
            ['adb', '-s', serial, 'shell', 'ip', 'addr', 'show', 'wlan0'],
            capture_output=True,
            text=True,
            timeout=10
        )

        ip_address = None
        if ip_result.returncode == 0:
            import re
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
            if match:
                ip_address = match.group(1)

        # Update registered device with WiFi IP
        if ip_address:
            json_storage.update_device(serial, {'wifi_ip': ip_address})

        return {
            "success": True,
            "message": f"WiFi ADB enabled for device {serial}",
            "ip_address": ip_address,
            "next_step": f"Now connect using: adb connect {ip_address}:5555" if ip_address else "Get device IP and use: adb connect <IP>:5555"
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Command timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enabling WiFi ADB: {str(e)}"
        )

@router.post("/connect-wifi/{ip_address}")
async def connect_wifi_adb(ip_address: str):
    """
    Connect to a device via ADB WiFi
    """
    try:
        # Connect to device via ADB WiFi
        result = subprocess.run(
            ['adb', 'connect', f'{ip_address}:5555'],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0 and 'connected' in result.stdout.lower():
            return {
                "success": True,
                "message": f"Successfully connected to {ip_address}:5555",
                "output": result.stdout
            }
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect: {error_msg}"
            )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Connection timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error connecting via WiFi: {str(e)}"
        )
