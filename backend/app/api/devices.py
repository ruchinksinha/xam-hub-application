from fastapi import APIRouter, HTTPException
from backend.utils.adb_manager import ADBManager
from backend.config.settings import get_settings

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.get("")
async def get_devices():
    devices = await ADBManager.get_connected_devices()
    return {"devices": devices}

@router.post("/{device_id}/flash")
async def flash_device(device_id: str):
    settings = get_settings()
    os_url = settings.lineage_os_url

    if not os_url:
        raise HTTPException(
            status_code=500,
            detail="Lineage OS URL not configured"
        )

    result = await ADBManager.flash_device(device_id, os_url)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])

    return {"message": result['message']}
