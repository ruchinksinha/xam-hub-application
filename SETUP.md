# Setup Guide

## Architecture

The application now runs with separated frontend and backend:

- **Backend API**: Port 8000 (Python/FastAPI)
- **Frontend**: Port 80 (Nginx serving static files)
- **API Proxy**: Nginx proxies `/api/*` requests to backend on port 8000

## Installation Steps

### 1. Setup Nginx

Run the nginx setup script:

```bash
./setup-nginx.sh
```

This will:
- Install nginx if not present
- Configure nginx to serve frontend on port 80
- Setup API proxying to backend on port 8000

### 2. Start the Backend

Run the start script to build frontend and start backend:

```bash
./start.sh
```

This will:
- Install frontend dependencies
- Build the frontend
- Setup Python virtual environment
- Install backend dependencies
- Start the backend API server on port 8000

## Access the Application

- **Frontend**: http://localhost
- **API**: http://localhost/api/* (proxied to port 8000)
- **Direct API Access**: http://localhost:8000/api/* (for testing)

## Stopping the Application

1. Stop the backend: Press `Ctrl+C` in the terminal running `start.sh`
2. Nginx runs as a service and doesn't need to be stopped

## Development Mode

To run in development mode with hot reload:

```bash
# Terminal 1 - Backend
source venv/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Frontend dev server will run on http://localhost:5173

## Troubleshooting

### Check nginx status
```bash
sudo systemctl status nginx
```

### Check nginx logs
```bash
sudo tail -f /var/log/nginx/error.log
```

### Test nginx configuration
```bash
sudo nginx -t
```

### Reload nginx after changes
```bash
sudo systemctl reload nginx
```

### Check if backend is running
```bash
curl http://localhost:8000/api/health
```
