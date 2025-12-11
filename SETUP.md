# Setup Guide

## Architecture

The application runs two separate FastAPI servers:

1. **Main Hub Server (Port 80)**
   - Serves frontend application and all main APIs
   - Device management, OS images, registered devices, admin, logs

2. **Exam Data Sync Server (Port 8000)**
   - Dedicated server for receiving exam data from mobile devices
   - Handles exam sessions, question actions, snapshots, and submissions

## Installation Steps

### 1. Start the Application

Run the start script:

```bash
./start.sh
```

This will:
- Install frontend dependencies
- Build the frontend
- Setup Python virtual environment
- Install backend dependencies
- Start both servers (port 80 and 8000)

## Access the Application

- **Main Hub Application**: http://localhost
- **Exam Data Sync Server**: http://localhost:8000
- **Health Check (Main)**: http://localhost/api/health
- **Health Check (Exam Data)**: http://localhost:8000/health

## Stopping the Application

Press `Ctrl+C` in the terminal - both servers will stop automatically.

## Development Mode

To run in development mode with hot reload:

```bash
# Terminal 1 - Main Hub Server
source venv/bin/activate
sudo venv/bin/python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 80

# Terminal 2 - Exam Data Sync Server
source venv/bin/activate
python -m uvicorn backend.app.exam_data_server:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 - Frontend Dev Server (optional)
cd frontend
npm run dev
```

Frontend dev server will run on http://localhost:5173

## Exam Data API Endpoints

The exam data sync server (port 8000) provides these endpoints:

- `GET /api/exam-data/status` - Server status check
- `POST /api/exam-data/exam-sessions` - Receive exam session data
- `POST /api/exam-data/question-actions` - Receive question action data
- `POST /api/exam-data/snapshot-actions` - Receive snapshot data
- `POST /api/exam-data/final-submissions` - Receive final submission data

## Mobile Device Configuration

Configure mobile devices to send exam data to:
```
http://<server-ip>:8000/api/exam-data/
```

## Troubleshooting

### Check if servers are running

```bash
# Main hub
curl http://localhost/api/health

# Exam data sync
curl http://localhost:8000/health
```

### Check server logs

Both servers output logs to the terminal. Check for errors or issues.

### Port 80 requires sudo

The main hub server runs on port 80 which requires root privileges. The start script handles this automatically.

### Port already in use

If port 80 or 8000 is already in use:

```bash
# Check what's using the ports
sudo lsof -i :80
sudo lsof -i :8000

# Kill the process if needed
sudo kill -9 <PID>
```
