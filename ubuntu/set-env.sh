#!/bin/bash

echo "Setting environment variables for Android Device Flashing Application..."

export LINEAGE_OS_URL="https://example.com/path/to/lineageos.zip"

echo "Environment variables set:"
echo "LINEAGE_OS_URL=$LINEAGE_OS_URL"

echo ""
echo "============================================"
echo "To persist these environment variables:"
echo "============================================"
echo "1. Add them to your ~/.bashrc or ~/.profile:"
echo "   echo 'export LINEAGE_OS_URL=\"https://example.com/path/to/lineageos.zip\"' >> ~/.bashrc"
echo ""
echo "2. Or create a .env file in the project root:"
echo "   LINEAGE_OS_URL=https://example.com/path/to/lineageos.zip"
echo ""
echo "3. Then reload your shell:"
echo "   source ~/.bashrc"
echo ""
