from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.utils.log_storage import log_storage
import time
import json

class APILoggingMiddleware(BaseHTTPMiddleware):
    def _should_log(self, path: str) -> bool:
        return path.startswith('/api/exam-data/')

    async def _extract_device_id_from_body(self, body: bytes) -> str:
        try:
            if body:
                data = json.loads(body.decode('utf-8'))

                if 'deviceId' in data:
                    return data['deviceId']
                elif 'actions' in data and len(data['actions']) > 0:
                    return data['actions'][0].get('deviceId', 'N/A')
                elif 'snapshots' in data and len(data['snapshots']) > 0:
                    return data['snapshots'][0].get('deviceId', 'N/A')

            return 'N/A'
        except:
            return 'N/A'

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        path = request.url.path
        method = request.method
        device_id = 'N/A'

        if self._should_log(path):
            client_ip = request.client.host if request.client else 'unknown'
            server_port = request.url.port or 8000

            body = await request.body()
            device_id = self._extract_device_id_from_body(body)

            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

            log_storage.add_log(
                log_type='request',
                message=f'{method} {path} from Device {device_id}',
                details={
                    'method': method,
                    'path': path,
                    'device_id': device_id,
                    'client_ip': client_ip,
                    'server_port': server_port,
                    'query_params': str(request.query_params)
                }
            )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            if self._should_log(path):
                server_port = request.url.port or 8000
                log_storage.add_log(
                    log_type='response',
                    message=f'{method} {path} - {response.status_code} from Device {device_id}',
                    details={
                        'method': method,
                        'path': path,
                        'device_id': device_id,
                        'server_port': server_port,
                        'status_code': response.status_code,
                        'process_time_ms': round(process_time * 1000, 2)
                    }
                )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            if self._should_log(path):
                server_port = request.url.port or 8000
                log_storage.add_log(
                    log_type='error',
                    message=f'{method} {path} - Error: {str(e)} from Device {device_id}',
                    details={
                        'method': method,
                        'path': path,
                        'device_id': device_id,
                        'server_port': server_port,
                        'error': str(e),
                        'process_time_ms': round(process_time * 1000, 2)
                    }
                )

            raise
