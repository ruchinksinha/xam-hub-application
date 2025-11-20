import subprocess
import re
import json
from pathlib import Path

class HotspotManager:
    def __init__(self):
        self.config_file = Path(__file__).parent.parent / "data" / "hotspot_config.json"
        self._ensure_config_exists()

    def _detect_wireless_interface(self):
        """Auto-detect the first available wireless interface"""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "DEVICE,TYPE", "device", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if ':wifi' in line or ':wireless' in line:
                    interface = line.split(':')[0]
                    if interface:
                        return interface

            # Fallback: check /sys/class/net for wireless interfaces
            net_path = Path("/sys/class/net")
            if net_path.exists():
                for iface in net_path.iterdir():
                    wireless_path = iface / "wireless"
                    if wireless_path.exists():
                        return iface.name

            return "wlan0"

        except Exception as e:
            print(f"Error detecting wireless interface: {e}")
            return "wlan0"

    def _ensure_config_exists(self):
        if not self.config_file.exists():
            self.config_file.parent.mkdir(exist_ok=True)
            detected_interface = self._detect_wireless_interface()
            default_config = {
                "ssid": "AndroidFlashHub",
                "password": "flashhub123",
                "interface": detected_interface,
                "auto_start": True
            }
            self.config_file.write_text(json.dumps(default_config, indent=2))
            print(f"Created hotspot config with detected interface: {detected_interface}")

    def _load_config(self):
        try:
            config = json.loads(self.config_file.read_text())
            # Auto-update interface if not set or invalid
            if not config.get("interface"):
                config["interface"] = self._detect_wireless_interface()
                self.config_file.write_text(json.dumps(config, indent=2))
            return config
        except:
            detected_interface = self._detect_wireless_interface()
            return {
                "ssid": "AndroidFlashHub",
                "password": "flashhub123",
                "interface": detected_interface,
                "auto_start": True
            }

    def get_status(self):
        try:
            config = self._load_config()
            expected_ssid = config.get("ssid", "AndroidFlashHub")
            expected_interface = config.get("interface", "wlan0")

            # Check if our configured SSID connection is active
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"],
                capture_output=True,
                text=True,
                timeout=5
            )

            active = False
            ssid = ""
            interface = ""

            # Look for WiFi connections in AP mode
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue

                parts = line.split(':')
                if len(parts) >= 3:
                    conn_name = parts[0]
                    conn_type = parts[1]
                    conn_device = parts[2]

                    # Check if it's a wifi connection
                    if conn_type in ['802-11-wireless', 'wifi']:
                        # Check if it matches our expected SSID or is a hotspot
                        if (conn_name == expected_ssid or
                            'hotspot' in conn_name.lower() or
                            'ap' in conn_name.lower()):
                            ssid = conn_name
                            interface = conn_device
                            active = True
                            break

            # Double-check by looking at device mode
            if interface:
                try:
                    iw_result = subprocess.run(
                        ["iw", "dev", interface, "info"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if "type AP" not in iw_result.stdout:
                        active = False
                except:
                    pass

            ip_address = ""
            if active and interface:
                try:
                    ip_result = subprocess.run(
                        ["ip", "addr", "show", interface],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
                    if ip_match:
                        ip_address = ip_match.group(1)
                except:
                    pass

            connected_devices = 0
            if active:
                try:
                    lease_files = [
                        "/var/lib/NetworkManager/dnsmasq-*.leases",
                        "/var/lib/misc/dnsmasq.leases"
                    ]
                    for lease_pattern in lease_files:
                        lease_result = subprocess.run(
                            ["bash", "-c", f"cat {lease_pattern} 2>/dev/null | wc -l"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if lease_result.returncode == 0:
                            connected_devices = int(lease_result.stdout.strip() or "0")
                            if connected_devices > 0:
                                break
                except:
                    pass

            if not ssid:
                ssid = expected_ssid
            if not interface:
                interface = expected_interface

            return {
                "active": active,
                "ssid": ssid,
                "interface": interface,
                "ip_address": ip_address,
                "connected_devices": connected_devices
            }

        except Exception as e:
            print(f"Error getting hotspot status: {e}")
            config = self._load_config()
            return {
                "active": False,
                "ssid": config.get("ssid", "AndroidFlashHub"),
                "interface": config.get("interface", "wlan0"),
                "ip_address": "",
                "connected_devices": 0
            }

    def start(self):
        try:
            config = self._load_config()
            ssid = config.get("ssid", "AndroidFlashHub")
            password = config.get("password", "flashhub123")
            interface = config.get("interface", "wlan0")

            # Check if nmcli is available
            check_result = subprocess.run(
                ["which", "nmcli"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if check_result.returncode != 0:
                return {"success": False, "error": "NetworkManager (nmcli) is not installed. Install with: sudo apt install network-manager"}

            # Check if interface exists
            iface_result = subprocess.run(
                ["ip", "link", "show", interface],
                capture_output=True,
                text=True,
                timeout=5
            )

            if iface_result.returncode != 0:
                # Try to find available wireless interfaces
                iface_list = subprocess.run(
                    ["nmcli", "device", "status"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return {"success": False, "error": f"Interface '{interface}' not found. Available interfaces:\n{iface_list.stdout}"}

            # Stop any existing hotspot first and clean up old connections
            old_connections = ["Hotspot", "Hotspot-1", "xLive", "xLive 1", ssid]
            for conn in old_connections:
                subprocess.run(
                    ["nmcli", "connection", "down", "id", conn],
                    capture_output=True,
                    timeout=5
                )
                subprocess.run(
                    ["nmcli", "connection", "delete", "id", conn],
                    capture_output=True,
                    timeout=5
                )

            # Create a new hotspot connection with proper SSID (try 5GHz first)
            result = subprocess.run(
                [
                    "nmcli", "connection", "add",
                    "type", "wifi",
                    "con-name", ssid,
                    "ifname", interface,
                    "ssid", ssid,
                    "mode", "ap",
                    "ipv4.method", "shared",
                    "802-11-wireless-security.key-mgmt", "wpa-psk",
                    "802-11-wireless-security.psk", password,
                    "802-11-wireless.band", "a",
                    "autoconnect", "no"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            create_error = None
            if result.returncode != 0:
                create_error = result.stderr or result.stdout
                # Connection might already exist, continue to activation
                pass

            # Activate the hotspot
            result = subprocess.run(
                ["nmcli", "connection", "up", "id", ssid],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {"success": True}
            else:
                # 5GHz failed, try with 2.4GHz as fallback
                activation_error = result.stderr or result.stdout

                # Delete the failed 5GHz connection
                subprocess.run(
                    ["nmcli", "connection", "delete", "id", ssid],
                    capture_output=True,
                    timeout=5
                )

                # Try creating with 2.4GHz
                result_24 = subprocess.run(
                    [
                        "nmcli", "connection", "add",
                        "type", "wifi",
                        "con-name", ssid,
                        "ifname", interface,
                        "ssid", ssid,
                        "mode", "ap",
                        "ipv4.method", "shared",
                        "802-11-wireless-security.key-mgmt", "wpa-psk",
                        "802-11-wireless-security.psk", password,
                        "802-11-wireless.band", "bg",
                        "autoconnect", "no"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result_24.returncode == 0:
                    # Try activating 2.4GHz
                    result_24_up = subprocess.run(
                        ["nmcli", "connection", "up", "id", ssid],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if result_24_up.returncode == 0:
                        return {"success": True, "message": "Hotspot started on 2.4GHz (5GHz not supported)"}

                # Both failed, return detailed error
                error_msg = f"Failed to start hotspot.\n\n5GHz Error: {activation_error}\n"
                if create_error:
                    error_msg += f"\nCreate Error: {create_error}"

                # Add helpful context to common errors
                if "rfkill" in error_msg.lower():
                    error_msg += "\n\nHint: WiFi may be blocked. Try: sudo rfkill unblock wifi"
                elif "not supported" in error_msg.lower():
                    error_msg += "\n\nHint: Your WiFi adapter may not support AP mode"
                elif "permission denied" in error_msg.lower():
                    error_msg += "\n\nHint: Run with sudo privileges"
                elif "already exists" in error_msg.lower():
                    error_msg += "\n\nHint: Connection already exists. Try stopping first, wait 5 seconds, then start again."

                return {"success": False, "error": error_msg}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out - NetworkManager may be unresponsive"}
        except FileNotFoundError as e:
            return {"success": False, "error": f"Required command not found: {e.filename}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def stop(self):
        try:
            status = self.get_status()
            if not status["active"]:
                return {"success": True, "message": "Hotspot already stopped"}

            config = self._load_config()
            ssid = config.get("ssid", "AndroidFlashHub")
            interface = status.get("interface", "wlan0")

            # Try stopping by connection name (configured SSID)
            result = subprocess.run(
                ["nmcli", "connection", "down", "id", ssid],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Fallback: try "Hotspot" name
            if result.returncode != 0:
                result = subprocess.run(
                    ["nmcli", "connection", "down", "id", "Hotspot"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

            # Last resort: disconnect the interface
            if result.returncode != 0:
                result = subprocess.run(
                    ["nmcli", "device", "disconnect", interface],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

            if result.returncode == 0:
                return {"success": True}
            else:
                return {"success": False, "error": result.stderr or "Unknown error"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_config(self):
        """Get current hotspot configuration"""
        return self._load_config()

    def update_config(self, new_config):
        """Update hotspot configuration"""
        try:
            current_config = self._load_config()
            current_config.update(new_config)
            self.config_file.write_text(json.dumps(current_config, indent=2))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_available_interfaces(self):
        """Get list of available wireless interfaces"""
        interfaces = []
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "DEVICE,TYPE", "device", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if ':wifi' in line or ':wireless' in line:
                    interface = line.split(':')[0]
                    if interface:
                        interfaces.append(interface)

            # Also check /sys/class/net
            net_path = Path("/sys/class/net")
            if net_path.exists():
                for iface in net_path.iterdir():
                    wireless_path = iface / "wireless"
                    if wireless_path.exists() and iface.name not in interfaces:
                        interfaces.append(iface.name)

            return interfaces if interfaces else ["wlan0"]

        except Exception as e:
            print(f"Error getting available interfaces: {e}")
            return ["wlan0"]

    def auto_start(self):
        config = self._load_config()
        if config.get("auto_start", True):
            status = self.get_status()
            if not status["active"]:
                print("Auto-starting WiFi hotspot...")
                result = self.start()
                if result["success"]:
                    print("WiFi hotspot started successfully")
                else:
                    print(f"Failed to start hotspot: {result.get('error')}")

    def get_connected_clients(self):
        """Get list of devices connected to the hotspot with their MAC addresses and IPs"""
        connected_clients = []
        try:
            # Try to read dnsmasq leases
            lease_files = [
                "/var/lib/NetworkManager/dnsmasq-*.leases",
                "/var/lib/misc/dnsmasq.leases"
            ]

            for lease_pattern in lease_files:
                result = subprocess.run(
                    ["bash", "-c", f"cat {lease_pattern} 2>/dev/null"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split()
                        if len(parts) >= 3:
                            # Format: timestamp mac_address ip_address hostname
                            connected_clients.append({
                                'mac_address': parts[1],
                                'ip_address': parts[2],
                                'hostname': parts[3] if len(parts) > 3 else ''
                            })
                    break

            return connected_clients
        except Exception as e:
            print(f"Error getting connected clients: {e}")
            return []
