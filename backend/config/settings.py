import os
from functools import lru_cache

class Settings:
    def __init__(self):
        self.lineage_os_url = os.getenv('LINEAGE_OS_URL', '')

@lru_cache()
def get_settings():
    return Settings()
