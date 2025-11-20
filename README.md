# XAM Hub Application

Device Flashing Hub for managing and flashing Android devices.

## WiFi Connectivity Troubleshooting

### Why some devices can't see the WiFi hotspot

**IMPORTANT**: This system uses **2.4GHz band (802.11b/g)** for maximum compatibility.

1. **SSID Broadcasting**
   - The hotspot SSID is always broadcast (visible)
   - Default SSID: "AndroidFlashHub"
   - Change it in Admin Centre → Configure

2. **WiFi Band - 2.4GHz ONLY**
   - System is configured to use 2.4GHz (802.11b/g) band
   - This ensures compatibility with older devices
   - 5GHz is NOT supported (intentionally disabled)

3. **Common Reasons Devices Can't See It**
   - Device WiFi is turned off
   - Device is scanning 5GHz only (rare)
   - Signal range too weak
   - Hotspot is not started (check Admin Centre)

4. **WiFi Adapter AP Mode Support**
   - Not all WiFi adapters support Access Point (AP) mode
   - Check if your adapter supports AP mode:
     ```bash
     iw list | grep "Supported interface modes" -A 8
     ```
   - Look for "AP" in the output

5. **Driver Issues**
   - Some Linux drivers have limited hotspot support
   - Try updating drivers or using a different WiFi adapter

### Why connected devices show as disconnected

The system detects WiFi connectivity by matching devices in two ways:

1. **Automatic WiFi MAC/IP Capture**
   - When a registered device is connected via USB AND WiFi simultaneously
   - The system captures its MAC address and IP from DHCP leases
   - Next time it connects via WiFi only, it will be recognized

2. **Manual Process**
   - First time: Connect device via USB and register it
   - Ensure device is connected to the hotspot WiFi
   - Unplug USB cable
   - Device should now show as "WiFi Connected"

### Checking WiFi Clients

Go to **Admin Centre** to see:
- List of all devices connected to WiFi hotspot
- Their IP addresses and MAC addresses
- Compare with your registered devices

### Common Issues

1. **Mobile connected but not showing**
   - The mobile's MAC/IP needs to be captured first
   - Connect mobile via USB while on WiFi
   - System will auto-capture its WiFi info
   - Then it will work when WiFi-only

2. **Hotspot SSID different from configuration (shows "Hotspot" instead of "AndroidFlashHub")**
   - This happens when NetworkManager creates a default hotspot
   - **Solution**: Stop the hotspot in Admin Centre, wait 5 seconds, then start it again
   - The system will now use your configured SSID
   - Old connections are automatically deleted

3. **DHCP lease file not accessible**
   - Check permissions: `/var/lib/NetworkManager/dnsmasq-*.leases`
   - Run backend with appropriate permissions