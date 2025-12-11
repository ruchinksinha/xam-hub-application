from datetime import datetime
from typing import List, Dict
from collections import deque
import threading

class LogStorage:
    def __init__(self, max_logs: int = 1000):
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self.lock = threading.Lock()

    def add_log(self, log_type: str, message: str, details: dict = None):
        with self.lock:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': log_type,
                'message': message,
                'details': details or {}
            }
            self.logs.append(log_entry)

    def get_logs(self, limit: int = 100, log_type: str = None) -> List[Dict]:
        with self.lock:
            logs_list = list(self.logs)

            if log_type:
                logs_list = [log for log in logs_list if log['type'] == log_type]

            return logs_list[-limit:]

    def clear_logs(self):
        with self.lock:
            self.logs.clear()

    def get_log_count(self) -> int:
        with self.lock:
            return len(self.logs)

log_storage = LogStorage(max_logs=1000)
