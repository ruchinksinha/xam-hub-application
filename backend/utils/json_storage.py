import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from pathlib import Path

class JSONStorage:
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            storage_dir = base_dir / "exam_sync_data_dir"
        else:
            storage_dir = Path(storage_dir)

        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        self.devices_file = self.storage_dir / "registered_devices.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.devices_file.exists():
            self._write_data([])

    def _read_data(self) -> List[Dict]:
        try:
            with open(self.devices_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_data(self, data: List[Dict]):
        with open(self.devices_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def get_all_devices(self) -> List[Dict]:
        return self._read_data()

    def get_device_by_serial(self, serial: str) -> Optional[Dict]:
        devices = self._read_data()
        return next((d for d in devices if d['serial'] == serial), None)

    def add_device(self, device_data: Dict) -> Dict:
        devices = self._read_data()

        existing = next((d for d in devices if d['serial'] == device_data['serial']), None)
        if existing:
            existing.update(device_data)
            existing['last_seen_at'] = datetime.utcnow().isoformat()
            self._write_data(devices)
            return existing

        new_device = {
            'id': str(uuid.uuid4()),
            'serial': device_data['serial'],
            'name': device_data.get('name', device_data['serial']),
            'model': device_data.get('model', ''),
            'manufacturer': device_data.get('manufacturer', ''),
            'registered_at': datetime.utcnow().isoformat(),
            'last_seen_at': datetime.utcnow().isoformat(),
            'is_connected': device_data.get('is_connected', True),
            'usb_bus': device_data.get('usb_bus', ''),
            'usb_device': device_data.get('usb_device', ''),
            'notes': device_data.get('notes', ''),
            'wifi_mac': device_data.get('wifi_mac', ''),
            'wifi_ip': device_data.get('wifi_ip', '')
        }

        devices.append(new_device)
        self._write_data(devices)
        return new_device

    def update_device(self, serial: str, updates: Dict) -> Optional[Dict]:
        devices = self._read_data()
        device = next((d for d in devices if d['serial'] == serial), None)

        if not device:
            return None

        device.update(updates)
        self._write_data(devices)
        return device

    def delete_device(self, serial: str) -> bool:
        devices = self._read_data()
        original_length = len(devices)
        devices = [d for d in devices if d['serial'] != serial]

        if len(devices) == original_length:
            return False

        self._write_data(devices)
        return True

    def update_connection_status(self, serial: str, is_connected: bool) -> Optional[Dict]:
        return self.update_device(serial, {
            'is_connected': is_connected,
            'last_seen_at': datetime.utcnow().isoformat()
        })

    def mark_all_disconnected(self):
        devices = self._read_data()
        for device in devices:
            device['is_connected'] = False
        self._write_data(devices)

json_storage = JSONStorage()
