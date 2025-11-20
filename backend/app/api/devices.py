from fastapi import APIRouter, HTTPException
from backend.utils.usb_manager import USBManager
from backend.utils.adb_manager import ADBManager
from backend.config.settings import get_settings
from backend.services.flash_service import flash_service
from backend.utils.json_storage import json_storage
import subprocess
import os
from pathlib import Path

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.get("")
async def get_devices():
    usb_devices = await USBManager.get_connected_tablets()
    adb_devices = await ADBManager.get_connected_devices()

    all_registered = json_storage.get_all_devices()
    registered_devices = {d['serial']: d for d in all_registered}

    adb_serials = {d['id'] for d in adb_devices}

    devices_dict = {}
    connected_serials = set()

    # First, process USB-connected devices
    for device in usb_devices:
        serial = device.get('serial')
        if serial and serial != 'N/A':
            connected_serials.add(serial)
            device['is_registered'] = serial in registered_devices
            device['connection_type'] = 'usb'
            device['adb_connected'] = serial in adb_serials

            if serial in registered_devices:
                device['registered_name'] = registered_devices[serial].get('name', '')
                json_storage.update_device(serial, {
                    'is_connected': True,
                    'usb_bus': device.get('bus', ''),
                    'usb_device': device.get('device', '')
                })

            devices_dict[serial] = device
        else:
            device['is_registered'] = False
            device['connection_type'] = 'disconnected'
            device['adb_connected'] = False
            # Use a unique ID for non-serial devices
            devices_dict[device['id']] = device

    # Add registered devices that are connected via WiFi (ADB but not USB)
    for serial in adb_serials:
        if serial not in connected_serials and serial in registered_devices:
            reg_device = registered_devices[serial]
            wifi_device = {
                'id': serial,
                'serial': serial,
                'description': reg_device.get('name', serial),
                'model': reg_device.get('model', ''),
                'manufacturer': reg_device.get('manufacturer', ''),
                'vendor_id': '',
                'product_id': '',
                'bus': '',
                'device': '',
                'status': 'ready',
                'is_registered': True,
                'registered_name': reg_device.get('name', ''),
                'connection_type': 'wifi',
                'adb_connected': True,
                'adb_ready': True,
                'adb_status': 'authorized'
            }
            devices_dict[serial] = wifi_device
            connected_serials.add(serial)
            json_storage.update_device(serial, {
                'is_connected': True,
                'usb_bus': '',
                'usb_device': ''
            })

    # Update connection status for disconnected registered devices
    for serial in registered_devices:
        if serial not in connected_serials:
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
