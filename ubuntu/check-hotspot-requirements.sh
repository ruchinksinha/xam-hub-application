#!/bin/bash

echo "=== WiFi Hotspot Requirements Check ==="
echo ""

# Check NetworkManager
echo "1. Checking NetworkManager..."
if command -v nmcli &> /dev/null; then
    echo "   ✓ NetworkManager is installed"
    nmcli --version
else
    echo "   ✗ NetworkManager is NOT installed"
    echo "   Install with: sudo apt install network-manager"
fi
echo ""

# Check wireless interfaces
echo "2. Checking wireless interfaces..."
if command -v nmcli &> /dev/null; then
    echo "   Available network devices:"
    nmcli device status
else
    echo "   Cannot check - nmcli not available"
fi
echo ""

# Check if WiFi is blocked
echo "3. Checking rfkill status..."
if command -v rfkill &> /dev/null; then
    rfkill list
    if rfkill list | grep -q "Wireless.*blocked: yes"; then
        echo "   ⚠ WiFi is blocked!"
        echo "   Unblock with: sudo rfkill unblock wifi"
    else
        echo "   ✓ WiFi is not blocked"
    fi
else
    echo "   rfkill not installed"
fi
echo ""

# Check wireless capabilities
echo "4. Checking wireless capabilities..."
if command -v iw &> /dev/null; then
    for dev in /sys/class/net/*; do
        iface=$(basename "$dev")
        if [ -d "$dev/wireless" ]; then
            echo "   Interface: $iface"
            iw list | grep -A 10 "Supported interface modes" | head -11
        fi
    done
else
    echo "   iw not installed (optional)"
    echo "   Install with: sudo apt install iw"
fi
echo ""

# Check permissions
echo "5. Checking script execution..."
if [ "$EUID" -ne 0 ]; then
    echo "   ⚠ Not running as root"
    echo "   Note: Starting hotspot requires sudo privileges"
else
    echo "   ✓ Running with root privileges"
fi
echo ""

echo "=== Check Complete ==="
echo ""
echo "Common issues and solutions:"
echo "  - NetworkManager not installed: sudo apt install network-manager"
echo "  - WiFi blocked: sudo rfkill unblock wifi"
echo "  - No wireless interface: Check if WiFi adapter is connected"
echo "  - AP mode not supported: WiFi adapter doesn't support hotspot mode"
echo ""
