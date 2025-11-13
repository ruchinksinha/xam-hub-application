from fastapi import APIRouter, HTTPException
from backend.utils.usb_manager import USBManager
from backend.config.settings import get_settings

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

    return {"message": f"Flash functionality for USB device {device_id} - coming soon"}
