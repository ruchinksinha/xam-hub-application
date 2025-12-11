from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.app.api.devices import router as devices_router
from backend.app.api.os_images import router as os_images_router
from backend.app.api.registered_devices import router as registered_devices_router
from backend.app.api.admin import router as admin_router
from backend.app.api.logs import router as logs_router
from backend.app.api.exam_data import router as exam_data_router
from backend.app.middleware.logging_middleware import APILoggingMiddleware
from backend.utils.hotspot_manager import HotspotManager

app = FastAPI()

app.add_middleware(APILoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices_router)
app.include_router(os_images_router)
app.include_router(registered_devices_router)
app.include_router(admin_router)
app.include_router(logs_router)
app.include_router(exam_data_router)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
