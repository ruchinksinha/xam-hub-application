# XAM Hub Application

Device Flashing Hub for managing and flashing Android devices.

## Quick Start

### Setup and Run

```bash
./start.sh
```

### Access the Application

- **Main Hub Application**: http://localhost (port 80)
- **Exam Data Sync Server**: http://localhost:8000

## Environment Variables

Configure these variables in the `.env` file:

### Backend Configuration

- **APK_FILE_PATH**: Path to the APK file for publishing to devices
  - Example: `/path/to/your/app.apk`
  - Used by the "Publish App" feature to install apps on connected devices

- **NODEAPP_SOURCE_URL**: URL to download NodeApp.apk
  - Example: `https://example.com/NodeApp.apk`
  - Used by the OS Status page to download the NodeApp APK file
  - Leave empty if not using the download feature

### Frontend Configuration

- **VITE_API_URL**: API base URL (optional)
  - Default: `http://localhost`
  - Override if running the backend on a different host/port

## Architecture

The application runs two separate FastAPI servers:

- **Main Hub Server (Port 80)**:
  - Serves frontend application
  - Device management APIs
  - OS image management APIs
  - Registered devices APIs
  - Admin centre APIs
  - System logs APIs

- **Exam Data Sync Server (Port 8000)**:
  - Exam session data API
  - Question actions API
  - Snapshot actions API
  - Final submissions API
  - Receives data from mobile devices during exams

## WiFi Connectivity Troubleshooting

### Why some devices can't see the WiFi hotspot

**IMPORTANT**: This system uses **5GHz band (802.11a)** for better performance.

1. **SSID Broadcasting**
   - The hotspot SSID is always broadcast (visible)
   - Default SSID: "AndroidFlashHub"
   - Change it in Admin Centre → Configure

2. **WiFi Band - 5GHz**
   - System is configured to use 5GHz (802.11a) band
   - Better performance and less interference
   - Note: Older devices may only support 2.4GHz and won't see this network

3. **Common Reasons Devices Can't See It**
   - Device only supports 2.4GHz (common on older devices)
   - Device WiFi is turned off
   - Device is scanning 2.4GHz only
   - Signal range too weak (5GHz has shorter range than 2.4GHz)
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