from fastapi import APIRouter, HTTPException
from pathlib import Path
import os
import aiohttp
import asyncio
from config.settings import settings

router = APIRouter()

DOWNLOAD_DIR = Path("/tmp/lineage_downloads")

download_progress = {}

@router.get("/api/os/list")
async def list_os_images():
    try:
        if not DOWNLOAD_DIR.exists():
            return {"images": []}

        images = []
        for file_path in DOWNLOAD_DIR.iterdir():
            if file_path.is_file() and file_path.suffix in ['.zip', '.img']:
                stat = file_path.stat()
                images.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })

        images.sort(key=lambda x: x['modified'], reverse=True)
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/os/delete/{filename}")
async def delete_os_image(filename: str):
    try:
        file_path = DOWNLOAD_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")

        if file_path.suffix not in ['.zip', '.img']:
            raise HTTPException(status_code=400, detail="Invalid file type")

        if not str(file_path.resolve()).startswith(str(DOWNLOAD_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")

        os.remove(file_path)
        return {"success": True, "message": f"Deleted {filename}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def download_file_background(url: str, filename: str):
    """Background task to download file with progress tracking"""
    try:
        DOWNLOAD_DIR.mkdir(exist_ok=True)
        file_path = DOWNLOAD_DIR / filename

        download_progress[filename] = {
            'status': 'downloading',
            'progress': 0,
            'downloaded': 0,
            'total': 0,
            'error': None
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download: HTTP {response.status}")

                total_size = int(response.headers.get('content-length', 0))
                download_progress[filename]['total'] = total_size

                downloaded = 0
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        download_progress[filename]['downloaded'] = downloaded

                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            download_progress[filename]['progress'] = progress

        download_progress[filename]['status'] = 'completed'
        download_progress[filename]['progress'] = 100

    except Exception as e:
        download_progress[filename]['status'] = 'error'
        download_progress[filename]['error'] = str(e)
        if file_path.exists():
            os.remove(file_path)

@router.post("/api/os/download")
async def start_download():
    """Start downloading the OS image from LINEAGE_OS_URL"""
    try:
        os_url = settings.LINEAGE_OS_URL
        if not os_url:
            raise HTTPException(status_code=400, detail="LINEAGE_OS_URL not configured")

        filename = os_url.split('/')[-1]
        if not filename.endswith(('.zip', '.img')):
            filename = f"lineageos_{filename}.zip"

        file_path = DOWNLOAD_DIR / filename

        if filename in download_progress and download_progress[filename]['status'] == 'downloading':
            raise HTTPException(status_code=400, detail="Download already in progress")

        if file_path.exists():
            return {
                "success": True,
                "message": "File already exists",
                "filename": filename,
                "already_exists": True
            }

        asyncio.create_task(download_file_background(os_url, filename))

        return {
            "success": True,
            "message": "Download started",
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/os/download/progress")
async def get_download_progress():
    """Get download progress for all active downloads"""
    return {"downloads": download_progress}
