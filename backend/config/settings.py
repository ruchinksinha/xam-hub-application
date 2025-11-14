import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    def __init__(self):
        self.LINEAGE_OS_URL = os.getenv('LINEAGE_OS_URL', '')

@lru_cache()
def get_settings():
    return Settings()

# Create a global instance
settings = get_settings()
