# backend/app/api/user.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.models import User
from app.schemas import UserProfileUpdate, UserSettingsUpdate, UserPasswordUpdate

router = APIRouter()

# 1. 프로필 조회 (보안 강화: 자동 생성 로직 삭제)
@router.get("/{user_id}/profile")
async def get_profile(user_id: str, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    
    # [수정] 사용자가 없으면 404 에러 발생 (자동 생성 금지)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    progress = user.progress if user.progress else {}
    settings = progress.get("settings", {})
    
    return {
        "uid": user.uid,
        "name": user.name,
        "role": user.role,
        "email": user.email or "",
        "phone": user.phone or "",
        "country": user.country or "",
        "dailyGoal": settings.get("goal", 10),
        "reviewWrong": settings.get("review_wrong", True)
    }

# ... (나머지 함수들은 그대로 유지) ...
@router.put("/{user_id}/profile")
async def update_profile(user_id: str, data: UserProfileUpdate, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.email is not None: user.email = data.email
    if data.phone is not None: user.phone = data.phone
    if data.country is not None: user.country = data.country
    session.add(user)
    session.commit()
    return {"status": "ok", "message": "Updated"}

@router.put("/{user_id}/settings")
async def update_settings(user_id: str, data: UserSettingsUpdate, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    current_progress = dict(user.progress) if user.progress else {}
    if "settings" not in current_progress:
        current_progress["settings"] = {}
    if data.dailyGoal is not None:
        current_progress["settings"]["goal"] = data.dailyGoal
    if data.reviewWrong is not None:
        current_progress["settings"]["review_wrong"] = data.reviewWrong
    user.progress = current_progress
    session.add(user)
    session.commit()
    return {"status": "ok", "message": "Settings saved"}

@router.put("/{user_id}/password")
async def change_password(user_id: str, data: UserPasswordUpdate, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.pw != data.old_password:
        raise HTTPException(status_code=400, detail="Wrong password")
    user.pw = data.new_password
    session.add(user)
    session.commit()
    return {"status": "ok", "message": "Password changed"}

@router.delete("/{user_id}")
async def withdraw_user(user_id: str, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if user:
        session.delete(user)
        session.commit()
    return {"status": "ok", "message": "User deleted"}