from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from supabase import create_client, Client
import os
from datetime import datetime

router = APIRouter(prefix="/api/registered-devices", tags=["registered_devices"])

supabase_url = os.getenv('VITE_SUPABASE_URL')
supabase_key = os.getenv('VITE_SUPABASE_SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

class RegisterDeviceRequest(BaseModel):
    serial: str
    name: Optional[str] = ""
    model: Optional[str] = ""
    manufacturer: Optional[str] = ""
    usb_bus: Optional[str] = ""
    usb_device: Optional[str] = ""
    notes: Optional[str] = ""

class UpdateDeviceRequest(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
async def get_registered_devices():
    try:
        response = supabase.table('registered_devices').select('*').order('registered_at', desc=True).execute()
        return {"devices": response.data}
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
            "is_connected": True,
            "last_seen_at": datetime.utcnow().isoformat()
        }

        response = supabase.table('registered_devices').upsert(data, on_conflict='serial').execute()
        return {"success": True, "device": response.data[0]}
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

        response = supabase.table('registered_devices').update(data).eq('serial', serial).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Device not found")

        return {"success": True, "device": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{serial}")
async def unregister_device(serial: str):
    try:
        response = supabase.table('registered_devices').delete().eq('serial', serial).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Device not found")

        return {"success": True, "message": "Device unregistered"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{serial}/sync-status")
async def sync_device_status(serial: str, is_connected: bool):
    try:
        data = {
            "is_connected": is_connected,
            "last_seen_at": datetime.utcnow().isoformat()
        }

        response = supabase.table('registered_devices').update(data).eq('serial', serial).execute()

        if not response.data:
            return {"success": False, "message": "Device not registered"}

        return {"success": True, "device": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
