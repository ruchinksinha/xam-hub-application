from fastapi import APIRouter, HTTPException
from backend.utils.usb_manager import USBManager
from backend.utils.adb_manager import ADBManager
from backend.config.settings import get_settings
from backend.services.flash_service import flash_service

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.get("")
async def get_devices():
    devices = await USBManager.get_connected_tablets()
    return {"devices": devices}

@router.get("/{bus}/{device}")
async def get_device_details(bus: str, device: str):
    details = await USBManager.get_device_details(bus, device)
    return {"details": details}

@router.post("/{device_id}/flash")
async def flash_device(device_id: str):
    settings = get_settings()
    os_url = settings.lineage_os_url

    if not os_url:
        raise HTTPException(
            status_code=500,
            detail="Lineage OS URL not configured"
        )

    devices = await ADBManager.get_connected_devices()
    device_exists = any(d['id'] == device_id for d in devices)

    if not device_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Device {device_id} not found"
        )

    import asyncio
    asyncio.create_task(flash_service.flash_device_complete(device_id, os_url))

    return {
        "success": True,
        "message": f"Flashing started for device {device_id}"
    }

@router.get("/{device_id}/flash/status")
async def get_flash_status(device_id: str):
    status = flash_service.get_flash_status(device_id)
    return status
