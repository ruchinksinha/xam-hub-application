from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.app.api.devices import router as devices_router

app = FastAPI()

app.include_router(devices_router)

frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
