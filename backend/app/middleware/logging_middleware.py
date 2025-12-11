from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.utils.log_storage import log_storage
import time

class APILoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        path = request.url.path
        method = request.method

        if path.startswith('/api/'):
            client_ip = request.client.host if request.client else 'unknown'

            log_storage.add_log(
                log_type='request',
                message=f'{method} {path}',
                details={
                    'method': method,
                    'path': path,
                    'client_ip': client_ip,
                    'query_params': str(request.query_params)
                }
            )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            if path.startswith('/api/') and path != '/api/logs/list':
                log_storage.add_log(
                    log_type='response',
                    message=f'{method} {path} - {response.status_code}',
                    details={
                        'method': method,
                        'path': path,
                        'status_code': response.status_code,
                        'process_time_ms': round(process_time * 1000, 2)
                    }
                )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            if path.startswith('/api/'):
                log_storage.add_log(
                    log_type='error',
                    message=f'{method} {path} - Error: {str(e)}',
                    details={
                        'method': method,
                        'path': path,
                        'error': str(e),
                        'process_time_ms': round(process_time * 1000, 2)
                    }
                )

            raise
