from fastapi import APIRouter, HTTPException
from backend.utils.log_storage import log_storage

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("/list")
async def get_logs(limit: int = 100, log_type: str = None):
    try:
        logs = log_storage.get_logs(limit=limit, log_type=log_type)
        return {
            "logs": logs,
            "total_count": log_storage.get_log_count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
async def clear_logs():
    try:
        log_storage.clear_logs()
        return {"message": "Logs cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_log_stats():
    try:
        all_logs = log_storage.get_logs(limit=1000)

        stats = {
            'total': len(all_logs),
            'by_type': {},
            'by_method': {},
            'recent_errors': []
        }

        for log in all_logs:
            log_type = log.get('type', 'unknown')
            stats['by_type'][log_type] = stats['by_type'].get(log_type, 0) + 1

            if 'details' in log and 'method' in log['details']:
                method = log['details']['method']
                stats['by_method'][method] = stats['by_method'].get(method, 0) + 1

            if log_type == 'error':
                stats['recent_errors'].append(log)

        stats['recent_errors'] = stats['recent_errors'][-10:]

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
