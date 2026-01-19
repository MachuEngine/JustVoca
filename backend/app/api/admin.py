# backend/app/api/admin.py
from fastapi import APIRouter
from app.core.session import load_users, save_users, load_system, save_system
# 수정 포인트: settings 객체를 가져옵니다.
from app.core.config import settings 

router = APIRouter()

@router.get("/pending_teachers")
async def get_pending():
    users = load_users()
    # 승인되지 않은 선생님 목록을 반환합니다.
    return [u for u in users.values() if u.get("role") == "teacher" and not u.get("is_approved")]

@router.post("/approve/{uid}")
async def approve(uid: str):
    users = load_users()
    if uid in users:
        users[uid]["is_approved"] = True
        save_users(users)
    return {"status": "ok"}

@router.get("/system_settings")
async def get_system_settings():
    # 이제 필요한 경우 settings.SESSION_COOKIE_NAME 처럼 접근 가능합니다.
    return load_system()