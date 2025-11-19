from fastapi import APIRouter, HTTPException
from backend.utils.usb_manager import USBManager
from backend.utils.adb_manager import ADBManager
from backend.config.settings import get_settings
from backend.services.flash_service import flash_service
from supabase import create_client, Client
import os
from datetime import datetime

router = APIRouter(prefix="/api/devices", tags=["devices"])

supabase_url = os.getenv('VITE_SUPABASE_URL')
supabase_key = os.getenv('VITE_SUPABASE_SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

@router.get("")
async def get_devices():
    devices = await USBManager.get_connected_tablets()

    registered_response = supabase.table('registered_devices').select('*').execute()
    registered_devices = {d['serial']: d for d in registered_response.data}

    connected_serials = set()
    for device in devices:
        serial = device.get('serial')
        if serial and serial != 'N/A':
            connected_serials.add(serial)
            device['is_registered'] = serial in registered_devices
            if serial in registered_devices:
                device['registered_name'] = registered_devices[serial].get('name', '')

                supabase.table('registered_devices').update({
                    'is_connected': True,
                    'last_seen_at': datetime.utcnow().isoformat(),
                    'usb_bus': device.get('bus', ''),
                    'usb_device': device.get('device', '')
                }).eq('serial', serial).execute()
        else:
            device['is_registered'] = False

    for serial in registered_devices:
        if serial not in connected_serials:
            supabase.table('registered_devices').update({
                'is_connected': False
            }).eq('serial', serial).execute()

    return {"devices": devices}

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
