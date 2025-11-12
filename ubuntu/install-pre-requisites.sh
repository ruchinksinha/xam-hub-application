#!/bin/bash

set -e

echo "Installing system prerequisites for Android Device Flashing Application..."

echo "Updating package lists..."
sudo apt-get update

echo "Installing Python 3.11 and pip..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip

echo "Installing Node.js and npm..."
sudo apt-get install -y curl
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "Installing Android Debug Bridge (ADB) and Fastboot..."
sudo apt-get install -y android-tools-adb android-tools-fastboot

echo "Installing build essentials..."
sudo apt-get install -y build-essential

echo "Installing USB utilities..."
sudo apt-get install -y usbutils

echo "Installing wget for downloading files..."
sudo apt-get install -y wget

echo "Installing unzip..."
sudo apt-get install -y unzip

echo "Setting up ADB udev rules for device permissions..."
sudo tee /etc/udev/rules.d/51-android.rules > /dev/null <<EOF
# Google Nexus devices
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"
# Samsung devices
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"
# HTC devices
SUBSYSTEM=="usb", ATTR{idVendor}=="0bb4", MODE="0666", GROUP="plugdev"
# LG devices
SUBSYSTEM=="usb", ATTR{idVendor}=="1004", MODE="0666", GROUP="plugdev"
# Motorola devices
SUBSYSTEM=="usb", ATTR{idVendor}=="22b8", MODE="0666", GROUP="plugdev"
# OnePlus devices
SUBSYSTEM=="usb", ATTR{idVendor}=="2a70", MODE="0666", GROUP="plugdev"
# Xiaomi devices
SUBSYSTEM=="usb", ATTR{idVendor}=="2717", MODE="0666", GROUP="plugdev"
# Generic Android devices
SUBSYSTEM=="usb", ATTR{idVendor}=="0502", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0b05", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="413c", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0489", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="091e", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"
EOF

echo "Setting udev rules permissions..."
sudo chmod a+r /etc/udev/rules.d/51-android.rules

echo "Adding current user to plugdev group..."
sudo usermod -aG plugdev $USER

echo "Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Creating application directories..."
mkdir -p ~/android-flash-app
cd ~/android-flash-app

echo "Creating Python virtual environment..."
python3.11 -m venv venv

echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip

echo "Verifying installations..."
echo "Python version:"
python3.11 --version
echo "Node version:"
node --version
echo "npm version:"
npm --version
echo "ADB version:"
adb version

echo ""
echo "============================================"
echo "Installation completed successfully!"
echo "============================================"
echo ""
echo "IMPORTANT NEXT STEPS:"
echo "1. Run 'source ubuntu/set-env.sh' to set environment variables"
echo "2. Log out and log back in for group changes to take effect"
echo "3. Connect your Android device and run 'adb devices' to verify connection"
echo ""
