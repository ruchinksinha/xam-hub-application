from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.hotspot_manager import HotspotManager

router = APIRouter(prefix="/api/admin", tags=["admin"])
hotspot_manager = HotspotManager()

class HotspotConfig(BaseModel):
    ssid: str
    password: str
    interface: str
    auto_start: bool

@router.get("/hotspot-status")
async def get_hotspot_status():
    try:
        status = hotspot_manager.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hotspot-config")
async def get_hotspot_config():
    try:
        config = hotspot_manager.get_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/hotspot-config")
async def update_hotspot_config(config: HotspotConfig):
    try:
        result = hotspot_manager.update_config(config.dict())
        if result["success"]:
            return {"message": "Configuration updated successfully"}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to update configuration"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-interfaces")
async def get_available_interfaces():
    try:
        interfaces = hotspot_manager.get_available_interfaces()
        return {"interfaces": interfaces}
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

@router.get("/wifi-clients")
async def get_wifi_clients():
    """Get list of devices currently connected to the WiFi hotspot"""
    try:
        clients = hotspot_manager.get_connected_clients()
        return {"clients": clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
