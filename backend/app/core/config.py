import os
from pathlib import Path

class Settings:
    BACKEND_ROOT = Path(__file__).resolve().parents[2]
    DATA_DIR = BACKEND_ROOT / "data"
    TEMP_UPLOAD_DIR = BACKEND_ROOT / "temp_uploads"
    USERS_FILE = DATA_DIR / "users.json"
    
    SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-jsv-2026")
    SESSION_COOKIE_NAME = "access_token"
    SESSION_TTL_SECONDS = 1209600

settings = Settings()

os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
USERS_FILE = settings.USERS_FILE