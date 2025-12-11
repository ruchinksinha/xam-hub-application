#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Setting up nginx for Android Device Flashing Application..."

if ! command -v nginx &> /dev/null; then
    echo "nginx not found. Installing nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

echo "Copying nginx configuration..."
sudo cp "$PROJECT_DIR/nginx.conf" /etc/nginx/sites-available/xam-hub

if [ -f "/etc/nginx/sites-enabled/default" ]; then
    echo "Removing default nginx site..."
    sudo rm /etc/nginx/sites-enabled/default
fi

if [ ! -L "/etc/nginx/sites-enabled/xam-hub" ]; then
    echo "Enabling xam-hub site..."
    sudo ln -s /etc/nginx/sites-available/xam-hub /etc/nginx/sites-enabled/
fi

echo "Updating nginx configuration with correct project path..."
sudo sed -i "s|/tmp/cc-agent/60128089/project|$PROJECT_DIR|g" /etc/nginx/sites-available/xam-hub

echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Reloading nginx..."
    sudo systemctl reload nginx
    echo ""
    echo "Nginx setup complete!"
    echo "Frontend will be accessible at: http://localhost"
    echo "API will be accessible at: http://localhost/api/*"
    echo ""
else
    echo "Error: nginx configuration test failed!"
    exit 1
fi
