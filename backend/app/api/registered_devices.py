from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.utils.json_storage import json_storage
from backend.utils.hotspot_manager import HotspotManager
import subprocess
import re

hotspot_manager = HotspotManager()

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

        # Get WiFi connected clients
        wifi_clients = hotspot_manager.get_connected_clients()
        wifi_macs = {client['mac_address'].lower(): client for client in wifi_clients}
        wifi_ips = {client['ip_address']: client for client in wifi_clients}

        # Enhance each device with WiFi connection status
        for device in devices:
            device_mac = device.get('wifi_mac', '').lower()
            device_ip = device.get('wifi_ip', '')

            # Check if device is currently connected to WiFi hotspot by MAC or IP
            is_wifi_connected = False
            if device_mac and device_mac in wifi_macs:
                is_wifi_connected = True
                # Update IP if it changed
                device['wifi_ip'] = wifi_macs[device_mac]['ip_address']
            elif device_ip and device_ip in wifi_ips:
                is_wifi_connected = True
                # Update MAC if we didn't have it
                if not device_mac:
                    device['wifi_mac'] = wifi_ips[device_ip]['mac_address']

            device['wifi_connected'] = is_wifi_connected

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

        # Try to get WiFi MAC address from device via ADB if connected via USB
        if not device.wifi_mac:
            wifi_mac = None

            # Try multiple methods to get MAC address
            methods = [
                ('sys/class/net', ['adb', '-s', device.serial, 'shell', 'cat', '/sys/class/net/wlan0/address']),
                ('ip link', ['adb', '-s', device.serial, 'shell', 'ip', 'link', 'show', 'wlan0']),
                ('ifconfig', ['adb', '-s', device.serial, 'shell', 'ifconfig', 'wlan0']),
                ('getprop', ['adb', '-s', device.serial, 'shell', 'getprop', 'ro.boot.wifimacaddr'])
            ]

            for method_name, method in methods:
                try:
                    print(f"Trying {method_name} to get MAC address for {device.serial}")
                    mac_result = subprocess.run(
                        method,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if mac_result.returncode == 0 and mac_result.stdout.strip():
                        output = mac_result.stdout.strip()
                        print(f"{method_name} output: {output}")

                        # Extract MAC address from output
                        if method_name in ['sys/class/net', 'getprop']:
                            wifi_mac = output.lower()
                        else:
                            # Look for MAC address pattern in output
                            mac_match = re.search(r'([0-9a-f]{2}[:-]){5}[0-9a-f]{2}', output.lower())
                            if mac_match:
                                wifi_mac = mac_match.group(0).replace('-', ':')

                        # Validate MAC address format
                        if wifi_mac and re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', wifi_mac):
                            data["wifi_mac"] = wifi_mac
                            print(f"Successfully captured MAC address using {method_name}: {wifi_mac}")
                            break
                        else:
                            print(f"Invalid MAC format from {method_name}: {wifi_mac}")
                            wifi_mac = None
                    else:
                        print(f"{method_name} failed with return code {mac_result.returncode}, stderr: {mac_result.stderr}")

                except Exception as e:
                    print(f"{method_name} exception: {e}")
                    continue

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

@router.get("/{serial}/wifi-mac")
async def get_device_wifi_mac(serial: str):
    """Debug endpoint to test MAC address retrieval"""
    try:
        wifi_mac = None
        methods_tried = []

        methods = [
            ('sys/class/net', ['adb', '-s', serial, 'shell', 'cat', '/sys/class/net/wlan0/address']),
            ('ip link', ['adb', '-s', serial, 'shell', 'ip', 'link', 'show', 'wlan0']),
            ('ifconfig', ['adb', '-s', serial, 'shell', 'ifconfig', 'wlan0']),
            ('getprop', ['adb', '-s', serial, 'shell', 'getprop', 'ro.boot.wifimacaddr'])
        ]

        for method_name, method in methods:
            try:
                mac_result = subprocess.run(
                    method,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                methods_tried.append({
                    'method': method_name,
                    'command': ' '.join(method),
                    'return_code': mac_result.returncode,
                    'stdout': mac_result.stdout.strip(),
                    'stderr': mac_result.stderr.strip()
                })

                if mac_result.returncode == 0 and mac_result.stdout.strip():
                    output = mac_result.stdout.strip()

                    if method_name == 'sys/class/net' or method_name == 'getprop':
                        wifi_mac = output.lower()
                    else:
                        mac_match = re.search(r'([0-9a-f]{2}[:-]){5}[0-9a-f]{2}', output.lower())
                        if mac_match:
                            wifi_mac = mac_match.group(0).replace('-', ':')

                    if wifi_mac and re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', wifi_mac):
                        methods_tried[-1]['extracted_mac'] = wifi_mac
                        methods_tried[-1]['success'] = True
                        break
                    else:
                        methods_tried[-1]['extracted_mac'] = wifi_mac
                        methods_tried[-1]['success'] = False
                        wifi_mac = None

            except Exception as e:
                methods_tried.append({
                    'method': method_name,
                    'command': ' '.join(method),
                    'error': str(e)
                })

        return {
            "serial": serial,
            "wifi_mac": wifi_mac,
            "methods_tried": methods_tried,
            "success": wifi_mac is not None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
