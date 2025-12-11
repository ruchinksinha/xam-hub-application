#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "Starting Android Device Flashing Application..."

if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with LINEAGE_OS_URL variable"
    exit 1
fi

source .env

echo "Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

echo "Building frontend..."
npm run build

cd ..

echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ ! -f "venv/bin/pip" ]; then
        echo "Error: Failed to create virtual environment - pip not found"
        exit 1
    fi
    echo "Virtual environment created successfully"
fi

echo "Installing Python dependencies..."
venv/bin/pip install -r backend/requirements.txt

echo "Starting servers..."
echo "Main Hub Application: http://localhost"
echo "Exam Data Sync Server: http://localhost:8000"
echo "Press Ctrl+C to stop the servers"
echo ""

trap 'kill $(jobs -p) 2>/dev/null' EXIT

if [ "$EUID" -eq 0 ]; then
    venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 80 &
    venv/bin/python -m uvicorn backend.app.exam_data_server:app --host 0.0.0.0 --port 8000 &
else
    echo "Starting main hub on port 80 (requires sudo)..."
    sudo venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 80 &

    echo "Starting exam data sync server on port 8000..."
    venv/bin/python -m uvicorn backend.app.exam_data_server:app --host 0.0.0.0 --port 8000 &
fi

wait
