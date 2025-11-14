from fastapi import APIRouter, HTTPException
from pathlib import Path
import os

router = APIRouter()

DOWNLOAD_DIR = Path("/tmp/lineage_downloads")

@router.get("/api/os/list")
async def list_os_images():
    try:
        if not DOWNLOAD_DIR.exists():
            return {"images": []}

        images = []
        for file_path in DOWNLOAD_DIR.iterdir():
            if file_path.is_file() and file_path.suffix == '.zip':
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

        if file_path.suffix != '.zip':
            raise HTTPException(status_code=400, detail="Invalid file type")

        if not str(file_path.resolve()).startswith(str(DOWNLOAD_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")

        os.remove(file_path)
        return {"success": True, "message": f"Deleted {filename}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
