from fastapi import APIRouter, HTTPException
from backend.utils.usb_manager import USBManager
from backend.utils.adb_manager import ADBManager
from backend.utils.hotspot_manager import HotspotManager
from backend.config.settings import get_settings
from backend.services.flash_service import flash_service
from backend.utils.json_storage import json_storage
import subprocess
import os
import shutil
from pathlib import Path

hotspot_manager = HotspotManager()

router = APIRouter(prefix="/api/devices", tags=["devices"])

mtp_map = {}
previous_connected_serials = set()

@router.get("")
async def get_devices():
    usb_devices = await USBManager.get_connected_tablets()
    adb_devices = await ADBManager.get_connected_devices()

    all_registered = json_storage.get_all_devices()
    registered_devices = {d['serial']: d for d in all_registered}

    # Get WiFi hotspot connected clients
    wifi_clients = hotspot_manager.get_connected_clients()
    wifi_ips = {client['ip_address']: client for client in wifi_clients}
    wifi_macs = {client['mac_address']: client for client in wifi_clients}

    # Parse ADB devices to identify WiFi-connected ones and get their serials
    adb_wifi_devices = {}  # Maps IP -> {device info + serial}
    adb_wifi_by_serial = {}  # Maps serial -> {device info + IP}
    adb_usb_devices = {}

    for adb_dev in adb_devices:
        device_id = adb_dev['id']
        if ':' in device_id:  # WiFi connection (IP:port format)
            ip_address = device_id.split(':')[0]
            # Get serial number via ADB for WiFi devices
            try:
                serial_result = subprocess.run(
                    ['adb', '-s', device_id, 'get-serialno'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if serial_result.returncode == 0:
                    serial = serial_result.stdout.strip()
                    adb_dev['serial'] = serial
                    adb_dev['ip_address'] = ip_address
                    adb_wifi_devices[ip_address] = adb_dev
                    adb_wifi_by_serial[serial] = adb_dev
                else:
                    adb_wifi_devices[ip_address] = adb_dev
            except:
                adb_wifi_devices[ip_address] = adb_dev
        else:  # USB connection (serial number)
            adb_usb_devices[device_id] = adb_dev

    devices_dict = {}
    connected_serials = set()

    # First, process USB-connected devices
    for device in usb_devices:
        serial = device.get('serial')
        if serial and serial != 'N/A':
            connected_serials.add(serial)
            device['is_registered'] = serial in registered_devices
            device['connection_type'] = 'usb'
            device['wifi_connected'] = False

            if serial in registered_devices:
                device['registered_name'] = registered_devices[serial].get('name', '')
                reg_device = registered_devices[serial]

                # Check if this device is also connected to WiFi and capture its MAC/IP
                device_ip = reg_device.get('wifi_ip', '')
                device_mac = reg_device.get('wifi_mac', '')

                # Try to match by known IP or MAC
                matched_client = None
                if device_ip and device_ip in wifi_ips:
                    matched_client = wifi_ips[device_ip]
                elif device_mac and device_mac in wifi_macs:
                    matched_client = wifi_macs[device_mac]
                else:
                    # Try to match by hostname containing serial or device name
                    for client in wifi_clients:
                        hostname = client.get('hostname', '').lower()
                        if serial.lower() in hostname or reg_device.get('name', '').lower() in hostname:
                            matched_client = client
                            break

                # Update device with WiFi info if found
                update_data = {
                    'is_connected': True,
                    'usb_bus': device.get('bus', ''),
                    'usb_device': device.get('device', ''),
                    'connection_type': 'usb'
                }

                if matched_client:
                    update_data['wifi_ip'] = matched_client['ip_address']
                    update_data['wifi_mac'] = matched_client['mac_address']
                    device['wifi_connected'] = True

                json_storage.update_device(serial, update_data)

            devices_dict[serial] = device
        else:
            device['is_registered'] = False
            device['connection_type'] = 'disconnected'
            device['wifi_connected'] = False
            # Use a unique ID for non-serial devices
            devices_dict[device['id']] = device

    # Add registered devices that are connected via WiFi hotspot but not USB
    for serial, reg_device in registered_devices.items():
        if serial not in connected_serials:
            # First check if device is connected via ADB WiFi by serial
            adb_wifi_info = adb_wifi_by_serial.get(serial)

            if adb_wifi_info:
                # Device is connected via ADB WiFi - we have its serial
                ip_address = adb_wifi_info['ip_address']
                wifi_client = wifi_ips.get(ip_address)

                # Update registered device with current WiFi info
                update_data = {
                    'is_connected': True,
                    'connection_type': 'wifi',
                    'wifi_ip': ip_address
                }
                if wifi_client:
                    update_data['wifi_mac'] = wifi_client['mac_address']

                json_storage.update_device(serial, update_data)

                wifi_device = {
                    'id': serial,
                    'serial': serial,
                    'description': reg_device.get('name', serial),
                    'model': adb_wifi_info.get('model') or reg_device.get('model', ''),
                    'manufacturer': reg_device.get('manufacturer', ''),
                    'vendor_id': '',
                    'product_id': '',
                    'bus': '',
                    'device': '',
                    'status': 'ready',
                    'is_registered': True,
                    'registered_name': reg_device.get('name', ''),
                    'connection_type': 'wifi',
                    'wifi_connected': True,
                    'adb_ready': True,
                    'adb_status': 'online',
                    'wifi_ip': ip_address,
                    'wifi_mac': wifi_client['mac_address'] if wifi_client else reg_device.get('wifi_mac', '')
                }
                devices_dict[serial] = wifi_device
                connected_serials.add(serial)
            else:
                # Check by stored IP or MAC address
                device_ip = reg_device.get('wifi_ip', '')
                device_mac = reg_device.get('wifi_mac', '')

                # Check if device is in WiFi clients by IP or MAC
                is_in_wifi_clients = False
                if device_ip and device_ip in wifi_ips:
                    is_in_wifi_clients = True
                elif device_mac and device_mac in wifi_macs:
                    is_in_wifi_clients = True
                    device_ip = wifi_macs[device_mac]['ip_address']

                if is_in_wifi_clients:
                    # Connected to WiFi but not via ADB yet
                    wifi_device = {
                        'id': serial,
                        'serial': serial,
                        'description': reg_device.get('name', serial),
                        'model': reg_device.get('model', ''),
                        'manufacturer': reg_device.get('manufacturer', ''),
                        'vendor_id': '',
                        'product_id': '',
                        'bus': '',
                        'device': '',
                        'status': 'connected',
                        'is_registered': True,
                        'registered_name': reg_device.get('name', ''),
                        'connection_type': 'wifi',
                        'wifi_connected': True,
                        'adb_ready': False,
                        'adb_status': 'offline',
                        'wifi_ip': device_ip,
                        'wifi_mac': device_mac
                    }
                    devices_dict[serial] = wifi_device
                    connected_serials.add(serial)
                    json_storage.update_device(serial, {
                        'is_connected': True,
                        'connection_type': 'wifi'
                    })
                else:
                    # Device is registered but not connected
                    disconnected_device = {
                        'id': serial,
                        'serial': serial,
                        'description': reg_device.get('name', serial),
                        'model': reg_device.get('model', ''),
                        'manufacturer': reg_device.get('manufacturer', ''),
                        'vendor_id': '',
                        'product_id': '',
                        'bus': '',
                        'device': '',
                        'status': 'offline',
                        'is_registered': True,
                        'registered_name': reg_device.get('name', ''),
                        'connection_type': 'disconnected',
                        'wifi_connected': False,
                        'adb_ready': False,
                        'adb_status': 'offline'
                    }
                    devices_dict[serial] = disconnected_device
                    json_storage.update_connection_status(serial, False)

    global previous_connected_serials, mtp_map
    current_serials = connected_serials

    if previous_connected_serials and current_serials < previous_connected_serials:
        disconnected = previous_connected_serials - current_serials
        if disconnected:
            mtp_map.clear()
            print(f"Devices disconnected: {disconnected}. MTP map cleared.")

    previous_connected_serials = current_serials.copy()

    return {"devices": list(devices_dict.values())}

@router.get("/{bus}/{device}")
async def get_device_details(bus: str, device: str):
    details = await USBManager.get_device_details(bus, device)
    return {"details": details}

@router.post("/mtp-map/scan")
async def scan_mtp_devices():
    global mtp_map
    mtp_map.clear()

    debug_info = {
        "mtp_devices": [],
        "usb_devices": [],
        "raw_mtp_output": ""
    }

    try:
        result = subprocess.run(
            ['jmtpfs', '-l'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            stderr_msg = result.stderr.strip() if result.stderr else ""
            stdout_msg = result.stdout.strip() if result.stdout else ""

            try:
                mtp_result = subprocess.run(
                    ['mtp-detect'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if mtp_result.returncode == 0:
                    mtp_output = mtp_result.stdout
                    debug_info["raw_mtp_output"] = mtp_output
                    usb_devices = await USBManager.get_connected_tablets()

                    for dev in usb_devices:
                        debug_info["usb_devices"].append({
                            "serial": dev.get('serial'),
                            "product": dev.get('product')
                        })

                    device_number = 0
                    current_device_info = {}

                    for line in mtp_output.split('\n'):
                        line = line.strip()

                        if line.startswith('Device ') and ':' in line:
                            if current_device_info.get('serial'):
                                debug_info["mtp_devices"].append(current_device_info.copy())

                                for usb_dev in usb_devices:
                                    serial = usb_dev.get('serial')
                                    if serial and serial != 'N/A' and serial == current_device_info['serial']:
                                        mtp_map[serial] = {
                                            'mtp_index': str(current_device_info['device_num']),
                                            'device_info': current_device_info.get('model', 'Unknown'),
                                            'serial': serial
                                        }
                                        break

                            current_device_info = {'device_num': device_number}
                            device_number += 1

                        elif 'Serial Number:' in line:
                            serial = line.split(':', 1)[1].strip()
                            current_device_info['serial'] = serial

                        elif 'Friendly name:' in line or 'Model:' in line:
                            model = line.split(':', 1)[1].strip()
                            current_device_info['model'] = model

                    if current_device_info.get('serial'):
                        debug_info["mtp_devices"].append(current_device_info.copy())

                        for usb_dev in usb_devices:
                            serial = usb_dev.get('serial')
                            if serial and serial != 'N/A' and serial == current_device_info['serial']:
                                mtp_map[serial] = {
                                    'mtp_index': str(current_device_info['device_num']),
                                    'device_info': current_device_info.get('model', 'Unknown'),
                                    'serial': serial
                                }
                                break

                    return {
                        "success": True,
                        "message": f"MTP map created with {len(mtp_map)} devices",
                        "map": mtp_map,
                        "debug": debug_info
                    }
                else:
                    error_detail = f"Both jmtpfs and mtp-detect failed. jmtpfs: {stderr_msg or stdout_msg}, mtp-detect: {mtp_result.stderr}"
                    raise HTTPException(
                        status_code=500,
                        detail=error_detail
                    )
            except FileNotFoundError:
                error_detail = f"jmtpfs failed: {stderr_msg or stdout_msg}. mtp-detect not found. Install with: sudo apt-get install mtp-tools"
                raise HTTPException(
                    status_code=500,
                    detail=error_detail
                )

        mtp_output = result.stdout
        debug_info["raw_mtp_output"] = mtp_output

        if not mtp_output or not mtp_output.strip():
            return {
                "success": True,
                "message": "No MTP devices found",
                "map": {},
                "debug": debug_info
            }

        usb_devices = await USBManager.get_connected_tablets()

        for dev in usb_devices:
            debug_info["usb_devices"].append({
                "bus": dev.get('bus'),
                "device": dev.get('device'),
                "serial": dev.get('serial'),
                "product": dev.get('description')
            })

        current_device_number = None
        for line in mtp_output.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith('Device'):
                import re
                match = re.match(r'Device\s+(\d+)', line)
                if match:
                    current_device_number = match.group(1)
                continue

            if line.startswith('Available') or line.startswith('Use'):
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6 and current_device_number is not None:
                bus_location = parts[0]
                dev_num = parts[1]
                product_id = parts[2]
                vendor_id = parts[3]
                product = parts[4]
                vendor = parts[5]

                mtp_device_info = {
                    'bus': bus_location,
                    'device': dev_num,
                    'product_id': product_id,
                    'vendor_id': vendor_id,
                    'product': product,
                    'vendor': vendor
                }
                debug_info["mtp_devices"].append(mtp_device_info)

                for usb_dev in usb_devices:
                    usb_bus = int(usb_dev.get('bus', '0'))
                    usb_device = int(usb_dev.get('device', '0'))
                    mtp_bus = int(bus_location)
                    mtp_device = int(dev_num)

                    if usb_bus == mtp_bus and usb_device == mtp_device:
                        serial = usb_dev.get('serial')
                        if serial and serial != 'N/A':
                            device_info = f"{vendor} {product}"

                            mtp_map[serial] = {
                                'mtp_index': current_device_number,
                                'device_info': device_info,
                                'serial': serial,
                                'bus': bus_location,
                                'device': dev_num
                            }
                            break

                current_device_number = None

        return {
            "success": True,
            "message": f"MTP map created with {len(mtp_map)} devices",
            "map": mtp_map,
            "debug": debug_info
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Timeout while scanning MTP devices (>10s)"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="jmtpfs not installed. Install with: sudo apt-get install jmtpfs mtp-tools"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in scan_mtp_devices: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {type(e).__name__}: {str(e)}"
        )

@router.get("/mtp-map")
async def get_mtp_map():
    global mtp_map
    return {
        "success": True,
        "map": mtp_map,
        "count": len(mtp_map)
    }

@router.delete("/mtp-map")
async def clear_mtp_map():
    global mtp_map
    mtp_map.clear()
    return {
        "success": True,
        "message": "MTP map cleared"
    }

@router.get("/os/check")
async def check_os_availability():
    settings = get_settings()
    os_url = settings.LINEAGE_OS_URL

    if not os_url:
        raise HTTPException(
            status_code=500,
            detail="Lineage OS URL not configured"
        )

    availability = flash_service.check_os_availability(os_url)
    return availability

@router.post("/{device_id}/flash/prepare")
async def prepare_flash(device_id: str):
    settings = get_settings()
    os_url = settings.LINEAGE_OS_URL

    if not os_url:
        raise HTTPException(
            status_code=500,
            detail="Lineage OS URL not configured"
        )

    usb_devices = await USBManager.get_connected_tablets()
    usb_device = next((d for d in usb_devices if d['id'] == device_id), None)

    if not usb_device:
        raise HTTPException(
            status_code=404,
            detail=f"USB device {device_id} not found"
        )

    serial = usb_device.get('serial')
    if not serial or serial == 'N/A':
        raise HTTPException(
            status_code=400,
            detail=f"Device {device_id} has no serial number. Make sure USB debugging is enabled."
        )

    adb_devices = await ADBManager.get_connected_devices()
    adb_device_exists = any(d['id'] == serial for d in adb_devices)

    if not adb_device_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Device {serial} not connected via ADB. Please enable USB debugging and authorize this computer."
        )

    import asyncio
    asyncio.create_task(flash_service.flash_device_complete(serial, os_url, skip_download=False))

    return {
        "success": True,
        "message": f"Preparing flash for device {serial}",
        "serial": serial
    }

@router.post("/{device_id}/flash/confirm")
async def confirm_flash(device_id: str):
    usb_devices = await USBManager.get_connected_tablets()
    usb_device = next((d for d in usb_devices if d['id'] == device_id), None)

    if not usb_device:
        raise HTTPException(
            status_code=404,
            detail=f"USB device {device_id} not found"
        )

    serial = usb_device.get('serial')
    if not serial or serial == 'N/A':
        raise HTTPException(
            status_code=400,
            detail=f"Device {device_id} has no serial number."
        )

    settings = get_settings()
    os_url = settings.LINEAGE_OS_URL

    import asyncio
    asyncio.create_task(flash_service.flash_device_complete(serial, os_url, skip_download=True))

    return {
        "success": True,
        "message": f"Flash confirmed for device {serial}"
    }

@router.get("/{device_id}/flash/status")
async def get_flash_status(device_id: str):
    usb_devices = await USBManager.get_connected_tablets()
    usb_device = next((d for d in usb_devices if d['id'] == device_id), None)

    if usb_device:
        serial = usb_device.get('serial')
        if serial and serial != 'N/A':
            status = flash_service.get_flash_status(serial)
            return status

    status = flash_service.get_flash_status(device_id)
    return status

@router.get("/{serial}/flash/status-by-serial")
async def get_flash_status_by_serial(serial: str):
    status = flash_service.get_flash_status(serial)
    return status

@router.post("/{serial}/publish-app")
async def publish_app(serial: str):
    """
    Publish/install an APK to a device using ADB
    """
    try:
        # Get APK path from environment
        apk_path = os.getenv('APK_FILE_PATH', '')

        if not apk_path:
            raise HTTPException(
                status_code=500,
                detail="APK_FILE_PATH not configured in .env file"
            )

        # Check if file exists
        if not Path(apk_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"APK file not found at: {apk_path}"
            )

        # Check if device is connected
        adb_devices = await ADBManager.get_connected_devices()
        device_exists = any(d['id'] == serial for d in adb_devices)

        if not device_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Device {serial} not connected via ADB"
            )

        # Install APK using ADB
        result = subprocess.run(
            ['adb', '-s', serial, 'install', '-r', apk_path],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"App published successfully to device {serial}",
                "output": result.stdout
            }
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise HTTPException(
                status_code=500,
                detail=f"Failed to install app: {error_msg}"
            )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Installation timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error publishing app: {str(e)}"
        )

@router.post("/{serial}/push-profile")
async def push_profile(serial: str):
    """
    Push device profile to a device via MTP
    """
    steps = [
        {"step": 1, "description": "Checking exam_metadata.json", "status": "pending", "error": None},
        {"step": 2, "description": "Listing MTP devices", "status": "pending", "error": None},
        {"step": 3, "description": "Identifying target MTP device", "status": "pending", "error": None},
        {"step": 4, "description": "Creating mount directory", "status": "pending", "error": None},
        {"step": 5, "description": "Mounting MTP device", "status": "pending", "error": None},
        {"step": 6, "description": "Creating Internal storage/XAM directory", "status": "pending", "error": None},
        {"step": 7, "description": "Copying exam_metadata.json", "status": "pending", "error": None},
        {"step": 8, "description": "Unmounting device", "status": "pending", "error": None},
    ]

    mount_path = None

    try:
        # Step 1: Check if exam_metadata.json exists
        profile_path = Path("exam_metadata.json")
        if not profile_path.exists():
            steps[0]["status"] = "failed"
            steps[0]["error"] = "exam_metadata.json not found. Please publish a profile first from Admin Centre."
            return {"success": False, "steps": steps, "message": steps[0]["error"]}
        steps[0]["status"] = "completed"

        # Step 2 & 3: Get MTP device index from map or scan
        global mtp_map
        mtp_index = None

        if serial in mtp_map:
            mtp_index = mtp_map[serial]['mtp_index']
            steps[1]["status"] = "completed"
            steps[2]["status"] = "completed"
        else:
            try:
                result = subprocess.run(
                    ['jmtpfs', '-l'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                steps[1]["status"] = "completed"

                if result.returncode != 0:
                    mtp_result = subprocess.run(
                        ['mtp-detect'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if mtp_result.returncode != 0:
                        steps[1]["status"] = "failed"
                        steps[1]["error"] = "Failed to detect MTP devices. Please ensure device is in MTP mode."
                        return {"success": False, "steps": steps, "message": steps[1]["error"]}

                    mtp_output = mtp_result.stdout
                    device_number = 0

                    for line in mtp_output.split('\n'):
                        if 'Serial Number:' in line:
                            device_serial = line.split(':', 1)[1].strip()
                            if device_serial == serial:
                                mtp_index = str(device_number)
                                break
                        elif line.startswith('Device ') and ':' in line:
                            device_number += 1
                else:
                    mtp_output = result.stdout
                    for line in mtp_output.split('\n'):
                        if serial in line:
                            parts = line.split(',')
                            if len(parts) > 0:
                                mtp_index = parts[0].strip()
                                break

            except subprocess.TimeoutExpired:
                steps[1]["status"] = "failed"
                steps[1]["error"] = "Timeout while listing MTP devices"
                return {"success": False, "steps": steps, "message": steps[1]["error"]}
            except FileNotFoundError:
                steps[1]["status"] = "failed"
                steps[1]["error"] = "MTP tools not installed. Install with: sudo apt-get install jmtpfs mtp-tools"
                return {"success": False, "steps": steps, "message": steps[1]["error"]}
            except Exception as e:
                steps[1]["status"] = "failed"
                steps[1]["error"] = f"Error listing MTP devices: {str(e)}"
                return {"success": False, "steps": steps, "message": steps[1]["error"]}

            if mtp_index is None:
                steps[2]["status"] = "failed"
                steps[2]["error"] = f"Device {serial} not found in MTP devices list. Please scan MTP map first."
                return {"success": False, "steps": steps, "message": steps[2]["error"]}
            steps[2]["status"] = "completed"

        # Step 4: Get USB bus and device info
        try:
            usb_result = subprocess.run(
                ['lsusb'],
                capture_output=True,
                text=True,
                timeout=10
            )

            bus_num = None
            dev_num = None

            for line in usb_result.stdout.split('\n'):
                if 'Bus' in line:
                    adb_check = subprocess.run(
                        ['adb', '-s', serial, 'shell', 'echo test'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if adb_check.returncode == 0:
                        parts = line.split()
                        if len(parts) >= 4:
                            bus_num = parts[1].lstrip('0') or '0'
                            dev_num = parts[3].rstrip(':').lstrip('0') or '0'
                            break

            if not bus_num or not dev_num:
                for line in usb_result.stdout.split('\n'):
                    if 'android' in line.lower() or 'samsung' in line.lower() or 'google' in line.lower():
                        parts = line.split()
                        if len(parts) >= 4:
                            bus_num = parts[1].lstrip('0') or '0'
                            dev_num = parts[3].rstrip(':').lstrip('0') or '0'
                            break

            if not bus_num or not dev_num:
                steps[3]["status"] = "failed"
                steps[3]["error"] = "Could not find USB device info"
                return {"success": False, "steps": steps, "message": steps[3]["error"]}

            steps[3]["status"] = "completed"
        except Exception as e:
            steps[3]["status"] = "failed"
            steps[3]["error"] = f"Error getting USB info: {str(e)}"
            return {"success": False, "steps": steps, "message": steps[3]["error"]}

        # Step 5: Mount MTP device using gvfs
        mount_path = None
        try:
            mtp_uri = f"mtp://[usb:{bus_num},{dev_num}]/"

            mount_result = subprocess.run(
                ['gvfs-mount', mtp_uri],
                capture_output=True,
                text=True,
                timeout=30
            )

            if mount_result.returncode != 0 and 'already mounted' not in mount_result.stderr.lower():
                steps[4]["status"] = "failed"
                steps[4]["error"] = f"Failed to mount: {mount_result.stderr or mount_result.stdout}"
                return {"success": False, "steps": steps, "message": steps[4]["error"]}

            import time
            time.sleep(2)

            gvfs_result = subprocess.run(
                ['find', '/run/user/1000/gvfs', '-type', 'd', '-maxdepth', '1'],
                capture_output=True,
                text=True,
                timeout=10
            )

            for path in gvfs_result.stdout.strip().split('\n'):
                if 'mtp' in path.lower():
                    mount_path = path.strip()
                    break

            if not mount_path:
                steps[4]["status"] = "failed"
                steps[4]["error"] = "Device mounted but mount point not found"
                return {"success": False, "steps": steps, "message": steps[4]["error"]}

            steps[4]["status"] = "completed"

        except subprocess.TimeoutExpired:
            steps[4]["status"] = "failed"
            steps[4]["error"] = "Timeout while mounting MTP device"
            return {"success": False, "steps": steps, "message": steps[4]["error"]}
        except Exception as e:
            steps[4]["status"] = "failed"
            steps[4]["error"] = f"Error mounting device: {str(e)}"
            return {"success": False, "steps": steps, "message": steps[4]["error"]}

        # Step 6: Create XAM directory
        xam_dir = Path(mount_path) / "Internal storage" / "XAM"
        try:
            xam_dir.mkdir(parents=True, exist_ok=True)
            steps[5]["status"] = "completed"
        except Exception as e:
            steps[5]["status"] = "failed"
            steps[5]["error"] = f"Failed to create XAM directory: {str(e)}"
            # Unmount before returning
            subprocess.run(['gvfs-mount', '-u', mount_path], capture_output=True)
            return {"success": False, "steps": steps, "message": steps[5]["error"]}

        # Step 7: Copy exam_metadata.json
        try:
            dest_file = xam_dir / "exam_metadata.json"
            shutil.copy2(profile_path, dest_file)
            steps[6]["status"] = "completed"
        except Exception as e:
            steps[6]["status"] = "failed"
            steps[6]["error"] = f"Failed to copy exam_metadata.json: {str(e)}"
            # Unmount before returning
            subprocess.run(['gvfs-mount', '-u', mount_path], capture_output=True)
            return {"success": False, "steps": steps, "message": steps[6]["error"]}

        # Step 8: Unmount device
        try:
            result = subprocess.run(
                ['gvfs-mount', '-u', mount_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                steps[7]["status"] = "failed"
                steps[7]["error"] = f"Failed to unmount device: {result.stderr or result.stdout}"
                return {"success": False, "steps": steps, "message": steps[7]["error"]}
            steps[7]["status"] = "completed"
        except Exception as e:
            steps[7]["status"] = "failed"
            steps[7]["error"] = f"Error unmounting device: {str(e)}"
            return {"success": False, "steps": steps, "message": steps[7]["error"]}

        return {
            "success": True,
            "steps": steps,
            "message": f"Device profile pushed successfully to {serial}"
        }

    except HTTPException:
        raise
    except Exception as e:
        # Try to unmount if mount_path was created
        if mount_path:
            subprocess.run(['gvfs-mount', '-u', mount_path], capture_output=True)

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.post("/{serial}/enable-wifi-adb")
async def enable_wifi_adb(serial: str):
    """
    Enable ADB over WiFi for a USB-connected device
    """
    try:
        # Check if device is connected via USB
        adb_devices = await ADBManager.get_connected_devices()
        device_exists = any(d['id'] == serial and ':' not in d['id'] for d in adb_devices)

        if not device_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Device {serial} not connected via USB. Connect via USB first to enable WiFi ADB."
            )

        # Enable TCP/IP mode on port 5555
        result = subprocess.run(
            ['adb', '-s', serial, 'tcpip', '5555'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise HTTPException(
                status_code=500,
                detail=f"Failed to enable WiFi ADB: {error_msg}"
            )

        # Get device IP address
        ip_result = subprocess.run(
            ['adb', '-s', serial, 'shell', 'ip', 'addr', 'show', 'wlan0'],
            capture_output=True,
            text=True,
            timeout=10
        )

        ip_address = None
        if ip_result.returncode == 0:
            import re
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
            if match:
                ip_address = match.group(1)

        # Update registered device with WiFi IP
        if ip_address:
            json_storage.update_device(serial, {'wifi_ip': ip_address})

        return {
            "success": True,
            "message": f"WiFi ADB enabled for device {serial}",
            "ip_address": ip_address,
            "next_step": f"Now connect using: adb connect {ip_address}:5555" if ip_address else "Get device IP and use: adb connect <IP>:5555"
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Command timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enabling WiFi ADB: {str(e)}"
        )

@router.post("/connect-wifi/{ip_address}")
async def connect_wifi_adb(ip_address: str):
    """
    Connect to a device via ADB WiFi
    """
    try:
        # Connect to device via ADB WiFi
        result = subprocess.run(
            ['adb', 'connect', f'{ip_address}:5555'],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0 and 'connected' in result.stdout.lower():
            # Try to get serial number and update registered device
            try:
                serial_result = subprocess.run(
                    ['adb', '-s', f'{ip_address}:5555', 'get-serialno'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if serial_result.returncode == 0:
                    serial = serial_result.stdout.strip()

                    # Get WiFi clients to find MAC address
                    wifi_clients = hotspot_manager.get_connected_clients()
                    wifi_client = next((c for c in wifi_clients if c['ip_address'] == ip_address), None)

                    # Update registered device with WiFi info
                    update_data = {
                        'wifi_ip': ip_address,
                        'is_connected': True,
                        'connection_type': 'wifi'
                    }
                    if wifi_client:
                        update_data['wifi_mac'] = wifi_client['mac_address']

                    json_storage.update_device(serial, update_data)

                    return {
                        "success": True,
                        "message": f"Successfully connected to {ip_address}:5555",
                        "serial": serial,
                        "output": result.stdout
                    }
            except:
                pass

            return {
                "success": True,
                "message": f"Successfully connected to {ip_address}:5555",
                "output": result.stdout
            }
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect: {error_msg}"
            )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Connection timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error connecting via WiFi: {str(e)}"
        )
