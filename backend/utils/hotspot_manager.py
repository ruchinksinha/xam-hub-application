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
        import os

        aps = []

        # Discover Wi-Fi interfaces
        iw = subprocess.run(
            ["iw", "dev"],
            capture_output=True,
            text=True
        )

        current_iface = None
        iface_info = {}

        for line in iw.stdout.splitlines():
            line = line.strip()

            if line.startswith("Interface"):
                current_iface = line.split()[1]
                iface_info[current_iface] = {
                    "interface": current_iface,
                    "ssid": "",
                    "active": False,
                    "ip_address": "",
                    "connected_devices": 0
                }

            elif current_iface and line.startswith("type"):
                if "AP" in line:
                    iface_info[current_iface]["active"] = True

            elif current_iface and line.startswith("ssid"):
                iface_info[current_iface]["ssid"] = line.split(None, 1)[1]

        # For each AP interface, get IP and client count
        for iface, info in iface_info.items():
            if not info["active"]:
                continue

            # IP address
            ip = subprocess.run(
                ["ip", "addr", "show", iface],
                capture_output=True,
                text=True
            )
            m = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip.stdout)
            if m:
                info["ip_address"] = m.group(1)

            # Get real-time connected client count using iw station dump
            try:
                iw_result = subprocess.run(
                    ["iw", "dev", iface, "station", "dump"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if iw_result.returncode == 0:
                    # Count number of "Station" lines which represent active connections
                    connected_count = iw_result.stdout.count('Station ')
                    info["connected_devices"] = connected_count
                else:
                    # Fallback to dnsmasq leases if iw fails
                    with open("/var/lib/misc/dnsmasq.leases") as f:
                        info["connected_devices"] = len(f.readlines())
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Error counting connected devices on {iface}: {e}")

            aps.append(info)

        return {
            "active": len(aps) > 0,
            "aps": aps
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

            # Delete all AP-related connections to avoid duplicates
            cleanup_result = subprocess.run(
                ["bash", "-c",
                 "nmcli -t -f NAME,TYPE connection show | "
                 "grep -E 'wifi|802-11-wireless' | "
                 "awk -F: '{print $1}' | "
                 "xargs -r -I {} nmcli connection delete '{}' 2>/dev/null"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            print(f"Cleanup result: {cleanup_result.stdout}")

            # Create a new hotspot connection with 2.4GHz band on channel 1
            # Try with full configuration first
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
                    "802-11-wireless-security.proto", "rsn",
                    "802-11-wireless-security.group", "ccmp",
                    "802-11-wireless-security.pairwise", "ccmp",
                    "802-11-wireless.band", "bg",
                    "802-11-wireless.channel", "1",
                    "autoconnect", "no"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            create_error = None
            if result.returncode != 0:
                create_error = result.stderr or result.stdout
                print(f"Create error: {create_error}")

                # If creation failed, maybe connection already exists, continue to activation
                pass
            else:
                print(f"Connection created successfully")

                # Try to set htmode after creation (some systems need this as a separate step)
                try:
                    htmode_result = subprocess.run(
                        ["nmcli", "connection", "modify", ssid, "802-11-wireless.htmode", "HT40"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if htmode_result.returncode != 0:
                        print(f"HT40 mode not supported, continuing with default: {htmode_result.stderr}")
                except:
                    print("Could not set HT40 mode, continuing with default")

            # Activate the hotspot
            print(f"Activating connection: {ssid}")
            result = subprocess.run(
                ["nmcli", "connection", "up", "id", ssid],
                capture_output=True,
                text=True,
                timeout=10
            )

            print(f"Activation returncode: {result.returncode}")
            print(f"Activation stdout: {result.stdout}")
            print(f"Activation stderr: {result.stderr}")

            if result.returncode == 0:
                print("Hotspot started successfully")
                return {"success": True, "message": "Hotspot started on 2.4GHz channel 1"}
            else:
                activation_error = result.stderr or result.stdout
                error_msg = f"Failed to start hotspot.\n\nActivation Error: {activation_error}"

                if create_error:
                    error_msg += f"\n\nConnection Create Error: {create_error}"

                # Add helpful context to common errors
                if "rfkill" in error_msg.lower():
                    error_msg += "\n\nHint: WiFi may be blocked. Try: sudo rfkill unblock wifi"
                elif "not supported" in error_msg.lower():
                    error_msg += "\n\nHint: Your WiFi adapter may not support AP mode"
                elif "permission denied" in error_msg.lower():
                    error_msg += "\n\nHint: Run with sudo privileges"
                elif "already exists" in error_msg.lower():
                    error_msg += "\n\nHint: Connection already exists. Try stopping first, wait 5 seconds, then start again."
                elif "secrets were required" in error_msg.lower():
                    error_msg += "\n\nHint: Password/security configuration issue"

                print(f"Error starting hotspot: {error_msg}")
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

            # Stop all active AP interfaces
            config = self._load_config()
            stopped_any = False

            for ap in status.get("aps", []):
                interface = ap.get("interface")
                if not interface:
                    continue

                # Stop hostapd for this interface
                try:
                    result = subprocess.run(
                        ["pkill", "-f", f"hostapd.*{interface}"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    # Also try to down the interface
                    subprocess.run(
                        ["ip", "link", "set", interface, "down"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    stopped_any = True
                except Exception as e:
                    print(f"Error stopping AP on {interface}: {e}")

            if stopped_any:
                return {"success": True, "message": "Hotspot stopped"}
            else:
                return {"success": False, "error": "No hotspot interfaces found to stop"}

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
        """Get list of devices currently connected to the hotspot in real-time"""
        connected_clients = []
        try:
            status = self.get_status()
            if not status["active"]:
                return []

            # Iterate through all active AP interfaces
            for ap in status.get("aps", []):
                interface = ap.get("interface")
                if not interface:
                    continue

                # Step 1: Get actively connected WiFi stations using iw
                iw_result = subprocess.run(
                    ["iw", "dev", interface, "station", "dump"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if iw_result.returncode != 0:
                    # Fallback to ARP table if iw fails
                    connected_clients.extend(self._get_clients_from_arp(interface))
                    continue

                # Parse iw station dump output
                active_mac_addresses = []
                current_mac = None

                for line in iw_result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('Station '):
                        # Extract MAC address: "Station aa:bb:cc:dd:ee:ff (on wlan0)"
                        parts = line.split()
                        if len(parts) >= 2:
                            current_mac = parts[1].lower()
                            active_mac_addresses.append(current_mac)

                if not active_mac_addresses:
                    continue

                # Step 2: Get IP addresses from DHCP leases for active MACs only
                lease_files = [
                    "/var/lib/NetworkManager/dnsmasq-*.leases",
                    "/var/lib/misc/dnsmasq.leases"
                ]

                dhcp_map = {}
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
                                mac = parts[1].lower()
                                dhcp_map[mac] = {
                                    'ip_address': parts[2],
                                    'hostname': parts[3] if len(parts) > 3 else ''
                                }
                        break

                # Step 3: Combine active MACs with DHCP info
                for mac in active_mac_addresses:
                    dhcp_info = dhcp_map.get(mac, {})
                    connected_clients.append({
                        'mac_address': mac,
                        'ip_address': dhcp_info.get('ip_address', 'N/A'),
                        'hostname': dhcp_info.get('hostname', '')
                    })

            return connected_clients

        except Exception as e:
            print(f"Error getting connected clients: {e}")
            return []

    def _get_clients_from_arp(self, interface):
        """Fallback method: Get connected clients from ARP table"""
        connected_clients = []
        try:
            # Get ARP entries that are REACHABLE or STALE on the interface
            arp_result = subprocess.run(
                ["ip", "neigh", "show", "dev", interface],
                capture_output=True,
                text=True,
                timeout=5
            )

            if arp_result.returncode != 0:
                return []

            for line in arp_result.stdout.split('\n'):
                if not line.strip():
                    continue

                # Parse: "192.168.1.2 lladdr aa:bb:cc:dd:ee:ff REACHABLE"
                parts = line.split()
                if len(parts) >= 5 and parts[2] == 'lladdr':
                    state = parts[4] if len(parts) > 4 else ''
                    # Only include REACHABLE devices (actively connected)
                    if state in ['REACHABLE', 'DELAY', 'PROBE']:
                        ip_address = parts[0]
                        mac_address = parts[3].lower()

                        # Try to get hostname
                        hostname = ''
                        try:
                            hostname_result = subprocess.run(
                                ["bash", "-c", f"grep {mac_address} /var/lib/NetworkManager/dnsmasq-*.leases 2>/dev/null | awk '{{print $4}}'"],
                                capture_output=True,
                                text=True,
                                timeout=2
                            )
                            if hostname_result.returncode == 0:
                                hostname = hostname_result.stdout.strip()
                        except:
                            pass

                        connected_clients.append({
                            'mac_address': mac_address,
                            'ip_address': ip_address,
                            'hostname': hostname
                        })

            return connected_clients

        except Exception as e:
            print(f"Error getting clients from ARP: {e}")
            return []
