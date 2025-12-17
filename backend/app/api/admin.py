from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.hotspot_manager import HotspotManager
import json
import os
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["admin"])
hotspot_manager = HotspotManager()

EXAM_METADATA_FILE = "exam_metadata.json"

class HotspotConfig(BaseModel):
    ssid: str
    password: str
    interface: str
    auto_start: bool

class ExamMetadata(BaseModel):
    ssid: str
    nodeapp_apk_path: str

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

@router.delete("/wifi-clients/{ip_address}")
async def disconnect_wifi_client(ip_address: str):
    """Disconnect a device from WiFi by its IP address"""
    try:
        import subprocess
        from backend.utils.json_storage import json_storage

        # First, disconnect ADB connection if exists
        try:
            subprocess.run(
                ['adb', 'disconnect', f'{ip_address}:5555'],
                capture_output=True,
                text=True,
                timeout=5
            )
        except:
            pass

        # Get the MAC address from DHCP leases to block it temporarily
        clients = hotspot_manager.get_connected_clients()
        client = next((c for c in clients if c['ip_address'] == ip_address), None)

        if client:
            mac_address = client['mac_address']

            # Block the MAC address using iptables (this forces disconnect)
            try:
                subprocess.run(
                    ['sudo', 'iptables', '-A', 'INPUT', '-m', 'mac', '--mac-source', mac_address, '-j', 'DROP'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                subprocess.run(
                    ['sudo', 'iptables', '-A', 'FORWARD', '-m', 'mac', '--mac-source', mac_address, '-j', 'DROP'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # Remove from DHCP lease
                subprocess.run(
                    ['sudo', 'dhcp_release', mac_address, ip_address],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # Wait a moment then unblock (so they can reconnect if needed)
                import time
                time.sleep(2)

                subprocess.run(
                    ['sudo', 'iptables', '-D', 'INPUT', '-m', 'mac', '--mac-source', mac_address, '-j', 'DROP'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                subprocess.run(
                    ['sudo', 'iptables', '-D', 'FORWARD', '-m', 'mac', '--mac-source', mac_address, '-j', 'DROP'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

            except Exception as e:
                print(f"Error blocking MAC: {e}")

            # Update registered device status
            all_registered = json_storage.get_all_devices()
            for device in all_registered:
                if device.get('wifi_ip') == ip_address or device.get('wifi_mac') == mac_address:
                    json_storage.update_device(device['serial'], {
                        'is_connected': False,
                        'connection_type': 'disconnected'
                    })

            return {"success": True, "message": f"Disconnected device at {ip_address}"}
        else:
            raise HTTPException(status_code=404, detail="Client not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/wifi-clients")
async def get_wifi_clients():
    """Get list of devices currently connected to the WiFi hotspot with registered device info"""
    try:
        from backend.utils.json_storage import json_storage
        import subprocess

        clients = hotspot_manager.get_connected_clients()
        all_registered = json_storage.get_all_devices()

        # Enhance client info with registered device data
        enhanced_clients = []
        for client in clients:
            enhanced_client = client.copy()
            enhanced_client['registered_device'] = None
            enhanced_client['serial'] = None
            enhanced_client['adb_connected'] = False

            # Try to match by MAC address
            matched_device = next(
                (d for d in all_registered if d.get('wifi_mac') == client['mac_address']),
                None
            )

            # Try to match by IP address
            if not matched_device:
                matched_device = next(
                    (d for d in all_registered if d.get('wifi_ip') == client['ip_address']),
                    None
                )

            # Try to get serial via ADB if device is at this IP
            try:
                adb_result = subprocess.run(
                    ['adb', '-s', f"{client['ip_address']}:5555", 'get-serialno'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if adb_result.returncode == 0:
                    serial = adb_result.stdout.strip()
                    enhanced_client['serial'] = serial
                    enhanced_client['adb_connected'] = True

                    # Find registered device by serial if not already matched
                    if not matched_device:
                        matched_device = next(
                            (d for d in all_registered if d.get('serial') == serial),
                            None
                        )
            except:
                pass

            if matched_device:
                enhanced_client['registered_device'] = {
                    'name': matched_device.get('name', ''),
                    'serial': matched_device.get('serial', ''),
                    'model': matched_device.get('model', '')
                }
                if not enhanced_client['serial']:
                    enhanced_client['serial'] = matched_device.get('serial', '')

            enhanced_clients.append(enhanced_client)

        return {"clients": enhanced_clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diagnostics")
async def get_diagnostics():
    """Get diagnostic information for troubleshooting WiFi hotspot issues"""
    try:
        import subprocess
        diagnostics = {}

        # Check NetworkManager status
        try:
            nm_status = subprocess.run(
                ["systemctl", "is-active", "NetworkManager"],
                capture_output=True,
                text=True,
                timeout=5
            )
            diagnostics["networkmanager_status"] = nm_status.stdout.strip()
        except:
            diagnostics["networkmanager_status"] = "unknown"

        # Check active connections
        try:
            conn_result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,STATE", "connection", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            diagnostics["all_connections"] = conn_result.stdout
        except:
            diagnostics["all_connections"] = "error"

        # Check WiFi adapter capabilities
        try:
            config = hotspot_manager.get_config()
            interface = config.get("interface", "wlan0")
            iw_result = subprocess.run(
                ["iw", "dev", interface, "info"],
                capture_output=True,
                text=True,
                timeout=5
            )
            diagnostics["interface_info"] = iw_result.stdout
        except:
            diagnostics["interface_info"] = "error"

        # Check if AP mode is supported
        try:
            iw_list = subprocess.run(
                ["iw", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            diagnostics["ap_mode_supported"] = "AP" in iw_list.stdout
            diagnostics["iw_capabilities"] = iw_list.stdout[:1000]  # First 1000 chars
        except:
            diagnostics["ap_mode_supported"] = "unknown"

        # Check rfkill status
        try:
            rfkill_result = subprocess.run(
                ["rfkill", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            diagnostics["rfkill_status"] = rfkill_result.stdout
        except:
            diagnostics["rfkill_status"] = "rfkill not available"

        return diagnostics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exam-metadata")
async def get_exam_metadata():
    """Get the exam metadata from JSON file"""
    try:
        if not os.path.exists(EXAM_METADATA_FILE):
            raise HTTPException(status_code=404, detail="Metadata file not found")

        with open(EXAM_METADATA_FILE, 'r') as f:
            data = json.load(f)

        file_stats = os.stat(EXAM_METADATA_FILE)
        timestamp = datetime.fromtimestamp(file_stats.st_mtime).isoformat()

        return {
            "metadata": data,
            "timestamp": timestamp,
            "file_path": os.path.abspath(EXAM_METADATA_FILE)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exam-metadata")
async def save_exam_metadata(metadata: ExamMetadata):
    """Save exam metadata to JSON file"""
    try:
        data = metadata.dict()

        with open(EXAM_METADATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        file_stats = os.stat(EXAM_METADATA_FILE)
        timestamp = datetime.fromtimestamp(file_stats.st_mtime).isoformat()

        return {
            "metadata": data,
            "timestamp": timestamp,
            "file_path": os.path.abspath(EXAM_METADATA_FILE),
            "message": "Metadata saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
