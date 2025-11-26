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
            device_ip = None

            # First, try to get the device's WiFi IP address
            try:
                print(f"Getting WiFi IP for device {device.serial}")
                ip_result = subprocess.run(
                    ['adb', '-s', device.serial, 'shell', 'ip', 'addr', 'show', 'wlan0'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if ip_result.returncode == 0:
                    # Extract IP address from output
                    ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
                    if ip_match:
                        device_ip = ip_match.group(1)
                        print(f"Found device IP: {device_ip}")
            except Exception as e:
                print(f"Failed to get IP: {e}")

            # If we have the IP, try to get MAC from WiFi clients
            if device_ip:
                try:
                    print(f"Looking up MAC for IP {device_ip} from WiFi clients")
                    wifi_clients = hotspot_manager.get_connected_clients()
                    for client in wifi_clients:
                        if client['ip_address'] == device_ip:
                            wifi_mac = client['mac_address'].lower()
                            print(f"Found MAC from WiFi clients: {wifi_mac}")
                            break
                except Exception as e:
                    print(f"Failed to get MAC from WiFi clients: {e}")

            # If still no MAC, try ADB methods
            if not wifi_mac:
                methods = [
                    ('dumpsys', ['adb', '-s', device.serial, 'shell', 'dumpsys', 'wifi']),
                    ('ip_addr', ['adb', '-s', device.serial, 'shell', 'ip', 'addr', 'show', 'wlan0']),
                    ('ifconfig', ['adb', '-s', device.serial, 'shell', 'ifconfig', 'wlan0']),
                    ('settings', ['adb', '-s', device.serial, 'shell', 'settings', 'get', 'secure', 'bluetooth_address'])
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
                            print(f"{method_name} output (first 500 chars): {output[:500]}")

                            # Extract MAC address from output
                            if method_name == 'dumpsys':
                                # Look for "MacAddress" or "mac" in dumpsys wifi output
                                mac_patterns = [
                                    r'MacAddress:\s*([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})',
                                    r'mac[=:\s]+([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})',
                                ]
                                for pattern in mac_patterns:
                                    mac_match = re.search(pattern, output.lower())
                                    if mac_match:
                                        wifi_mac = mac_match.group(1)
                                        break
                            else:
                                # Look for MAC address pattern
                                mac_match = re.search(r'([0-9a-f]{2}[:-]){5}[0-9a-f]{2}', output.lower())
                                if mac_match:
                                    wifi_mac = mac_match.group(0).replace('-', ':')

                            # Validate MAC address format
                            if wifi_mac and re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', wifi_mac):
                                # Ignore common invalid MACs
                                if wifi_mac not in ['00:00:00:00:00:00', 'ff:ff:ff:ff:ff:ff']:
                                    print(f"Successfully captured MAC address using {method_name}: {wifi_mac}")
                                    break
                                else:
                                    print(f"Invalid MAC (all zeros/ones): {wifi_mac}")
                                    wifi_mac = None
                            else:
                                print(f"Invalid MAC format from {method_name}: {wifi_mac}")
                                wifi_mac = None

                    except Exception as e:
                        print(f"{method_name} exception: {e}")
                        continue

            if wifi_mac:
                data["wifi_mac"] = wifi_mac
            if device_ip:
                data["wifi_ip"] = device_ip

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
        device_ip = None
        methods_tried = []

        # First, try to get IP and lookup MAC from WiFi clients
        try:
            ip_result = subprocess.run(
                ['adb', '-s', serial, 'shell', 'ip', 'addr', 'show', 'wlan0'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if ip_result.returncode == 0:
                ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
                if ip_match:
                    device_ip = ip_match.group(1)

                    methods_tried.append({
                        'method': 'get_ip',
                        'command': 'adb -s ' + serial + ' shell ip addr show wlan0',
                        'return_code': 0,
                        'device_ip': device_ip,
                        'success': True
                    })

                    # Try to get MAC from WiFi clients
                    wifi_clients = hotspot_manager.get_connected_clients()
                    for client in wifi_clients:
                        if client['ip_address'] == device_ip:
                            wifi_mac = client['mac_address'].lower()
                            methods_tried.append({
                                'method': 'wifi_clients_lookup',
                                'device_ip': device_ip,
                                'wifi_mac': wifi_mac,
                                'success': True
                            })
                            break
        except Exception as e:
            methods_tried.append({
                'method': 'wifi_clients_lookup',
                'error': str(e)
            })

        # If no MAC yet, try ADB methods
        if not wifi_mac:
            methods = [
                ('dumpsys', ['adb', '-s', serial, 'shell', 'dumpsys', 'wifi']),
                ('ip_addr', ['adb', '-s', serial, 'shell', 'ip', 'addr', 'show', 'wlan0']),
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
                        'stdout': mac_result.stdout.strip()[:500],  # Limit output
                        'stderr': mac_result.stderr.strip()
                    })

                    if mac_result.returncode == 0 and mac_result.stdout.strip():
                        output = mac_result.stdout.strip()

                        if method_name == 'dumpsys':
                            mac_patterns = [
                                r'MacAddress:\s*([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})',
                                r'mac[=:\s]+([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})',
                            ]
                            for pattern in mac_patterns:
                                mac_match = re.search(pattern, output.lower())
                                if mac_match:
                                    wifi_mac = mac_match.group(1)
                                    break
                        else:
                            mac_match = re.search(r'([0-9a-f]{2}[:-]){5}[0-9a-f]{2}', output.lower())
                            if mac_match:
                                wifi_mac = mac_match.group(0).replace('-', ':')

                        if wifi_mac and re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', wifi_mac):
                            if wifi_mac not in ['00:00:00:00:00:00', 'ff:ff:ff:ff:ff:ff']:
                                methods_tried[-1]['extracted_mac'] = wifi_mac
                                methods_tried[-1]['success'] = True
                                break
                            else:
                                wifi_mac = None

                        methods_tried[-1]['extracted_mac'] = wifi_mac
                        methods_tried[-1]['success'] = False

                except Exception as e:
                    methods_tried.append({
                        'method': method_name,
                        'command': ' '.join(method),
                        'error': str(e)
                    })

        return {
            "serial": serial,
            "device_ip": device_ip,
            "wifi_mac": wifi_mac,
            "methods_tried": methods_tried,
            "success": wifi_mac is not None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
