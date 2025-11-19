from fastapi import APIRouter, HTTPException
from backend.utils.hotspot_manager import HotspotManager

router = APIRouter(prefix="/api/admin", tags=["admin"])
hotspot_manager = HotspotManager()

@router.get("/hotspot-status")
async def get_hotspot_status():
    try:
        status = hotspot_manager.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hotspot/start")
async def start_hotspot():
    try:
        result = hotspot_manager.start()
        if result["success"]:
            return {"message": "Hotspot started successfully"}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to start hotspot"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hotspot/stop")
async def stop_hotspot():
    try:
        result = hotspot_manager.stop()
        if result["success"]:
            return {"message": "Hotspot stopped successfully"}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to stop hotspot"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
