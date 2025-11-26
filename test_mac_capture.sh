#!/bin/bash

# Test MAC Address Capture Script
# Usage: ./test_mac_capture.sh <device_serial>

if [ -z "$1" ]; then
    echo "Usage: $0 <device_serial>"
    echo "Example: $0 ABC123456"
    exit 1
fi

SERIAL=$1

echo "=========================================="
echo "Testing MAC Address Capture for: $SERIAL"
echo "=========================================="
echo ""

echo "1. Testing: cat /sys/class/net/wlan0/address"
echo "Command: adb -s $SERIAL shell cat /sys/class/net/wlan0/address"
adb -s "$SERIAL" shell cat /sys/class/net/wlan0/address 2>&1
echo ""

echo "2. Testing: ip link show wlan0"
echo "Command: adb -s $SERIAL shell ip link show wlan0"
adb -s "$SERIAL" shell ip link show wlan0 2>&1
echo ""

echo "3. Testing: ifconfig wlan0"
echo "Command: adb -s $SERIAL shell ifconfig wlan0"
adb -s "$SERIAL" shell ifconfig wlan0 2>&1
echo ""

echo "4. Testing: getprop ro.boot.wifimacaddr"
echo "Command: adb -s $SERIAL shell getprop ro.boot.wifimacaddr"
adb -s "$SERIAL" shell getprop ro.boot.wifimacaddr 2>&1
echo ""

echo "5. Testing: settings get secure bluetooth_address"
echo "Command: adb -s $SERIAL shell settings get secure bluetooth_address"
adb -s "$SERIAL" shell settings get secure bluetooth_address 2>&1
echo ""

echo "=========================================="
echo "You can also test via API:"
echo "curl http://localhost/api/registered-devices/$SERIAL/wifi-mac"
echo "=========================================="
