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
            server_port = request.url.port or 8000

            log_storage.add_log(
                log_type='request',
                message=f'{method} {path} (port {server_port})',
                details={
                    'method': method,
                    'path': path,
                    'client_ip': client_ip,
                    'server_port': server_port,
                    'query_params': str(request.query_params)
                }
            )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            if path.startswith('/api/') and path != '/api/logs/list':
                server_port = request.url.port or 8000
                log_storage.add_log(
                    log_type='response',
                    message=f'{method} {path} - {response.status_code} (port {server_port})',
                    details={
                        'method': method,
                        'path': path,
                        'server_port': server_port,
                        'status_code': response.status_code,
                        'process_time_ms': round(process_time * 1000, 2)
                    }
                )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            if path.startswith('/api/'):
                server_port = request.url.port or 8000
                log_storage.add_log(
                    log_type='error',
                    message=f'{method} {path} - Error: {str(e)} (port {server_port})',
                    details={
                        'method': method,
                        'path': path,
                        'server_port': server_port,
                        'error': str(e),
                        'process_time_ms': round(process_time * 1000, 2)
                    }
                )

            raise
