from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.utils.json_storage import json_storage

router = APIRouter(prefix="/api/registered-devices", tags=["registered_devices"])

class RegisterDeviceRequest(BaseModel):
    serial: str
    name: Optional[str] = ""
    model: Optional[str] = ""
    manufacturer: Optional[str] = ""
    usb_bus: Optional[str] = ""
    usb_device: Optional[str] = ""
    notes: Optional[str] = ""
    wifi_mac: Optional[str] = ""
    wifi_ip: Optional[str] = ""

class UpdateDeviceRequest(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
async def get_registered_devices():
    try:
        devices = json_storage.get_all_devices()
        devices.sort(key=lambda x: x.get('registered_at', ''), reverse=True)
        return {"devices": devices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def register_device(device: RegisterDeviceRequest):
    try:
        data = {
            "serial": device.serial,
            "name": device.name or device.serial,
            "model": device.model,
            "manufacturer": device.manufacturer,
            "usb_bus": device.usb_bus,
            "usb_device": device.usb_device,
            "notes": device.notes,
            "is_connected": True
        }

        # Add WiFi MAC address if provided
        if device.wifi_mac:
            data["wifi_mac"] = device.wifi_mac
        if device.wifi_ip:
            data["wifi_ip"] = device.wifi_ip

        result = json_storage.add_device(data)
        return {"success": True, "device": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{serial}")
async def update_device(serial: str, device: UpdateDeviceRequest):
    try:
        data = {}
        if device.name is not None:
            data["name"] = device.name
        if device.notes is not None:
            data["notes"] = device.notes

        if not data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = json_storage.update_device(serial, data)

        if not result:
            raise HTTPException(status_code=404, detail="Device not found")

        return {"success": True, "device": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{serial}")
async def unregister_device(serial: str):
    try:
        success = json_storage.delete_device(serial)

        if not success:
            raise HTTPException(status_code=404, detail="Device not found")

        return {"success": True, "message": "Device unregistered"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{serial}/sync-status")
async def sync_device_status(serial: str, is_connected: bool):
    try:
        result = json_storage.update_connection_status(serial, is_connected)

        if not result:
            return {"success": False, "message": "Device not registered"}

        return {"success": True, "device": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
