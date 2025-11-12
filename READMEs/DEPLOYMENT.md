# Deployment Guide

## Prerequisites Installation

After cloning the repository, run the prerequisite installation script:

```bash
cd android-flash-app
chmod +x ubuntu/install-pre-requisites.sh
sudo ./ubuntu/install-pre-requisites.sh
```

This will install:
- Python 3.11
- Node.js 18
- ADB and Fastboot
- Required system packages
- USB device permissions

## Environment Configuration

1. Update the `.env` file in the project root with your Lineage OS URL:

```bash
nano .env
```

Update the value:
```
LINEAGE_OS_URL=https://your-actual-url.com/path/to/lineageos.zip
```

2. Optionally, run the environment setup script:

```bash
source ubuntu/set-env.sh
```

## Starting the Application

Run the start script:

```bash
chmod +x start.sh
sudo ./start.sh
```

The script will:
1. Install frontend dependencies
2. Build the frontend
3. Set up Python virtual environment
4. Install Python dependencies
5. Start the backend server

## Accessing the Application

Once started, access the application at:

```
http://localhost
```

Or from another machine on the same network:

```
http://<server-ip-address>
```

## Connecting Android Devices

1. Enable USB debugging on your Android device
2. Connect the device via USB
3. Accept the debugging authorization on the device
4. The device should appear in the application automatically

## Verify Device Connection

To manually verify devices are detected:

```bash
adb devices
```

## Stopping the Application

Press `Ctrl+C` in the terminal where the application is running.

## Running on System Startup (Optional)

To run the application automatically on system startup, create a systemd service:

```bash
sudo nano /etc/systemd/system/android-flash.service
```

Add the following content:

```ini
[Unit]
Description=Android Device Flashing Application
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/android-flash-app
ExecStart=/path/to/android-flash-app/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable android-flash.service
sudo systemctl start android-flash.service
```

Check service status:

```bash
sudo systemctl status android-flash.service
```

## Troubleshooting

### Port 80 Permission Denied

If you get permission errors on port 80, either:

1. Run with sudo: `sudo ./start.sh`
2. Or use a different port by modifying `start.sh` (e.g., port 8000)

### Devices Not Detected

1. Check USB connection: `lsusb`
2. Check ADB devices: `adb devices`
3. Ensure device has USB debugging enabled
4. Check udev rules are applied: `sudo udevadm control --reload-rules`
5. Log out and log back in for group permissions to take effect

### Frontend Not Loading

1. Ensure frontend was built: `cd frontend && npm run build`
2. Check that `frontend/dist` directory exists
3. Restart the application
