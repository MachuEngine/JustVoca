# backend/app/api/user.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.models import User
from app.schemas import UserProfileUpdate, UserSettingsUpdate, UserPasswordUpdate

router = APIRouter()

# 1. 프로필 조회
@router.get("/{user_id}/profile")
async def get_profile(user_id: str, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    
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
        # [핵심 수정] 저장된 선생님 ID를 반환해야 프론트엔드가 알 수 있습니다.
        "teacher_id": user.teacher_id or "", 
        "dailyGoal": settings.get("goal", 10),
        "reviewWrong": settings.get("review_wrong", True)
    }

# 2. 프로필 수정
@router.put("/{user_id}/profile")
async def update_profile(
    user_id: str, 
    data: UserProfileUpdate, 
    session: Session = Depends(get_session)
):
    # 1. 유저 조회
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. 기존 프로필 정보 업데이트
    if data.email is not None: user.email = data.email
    if data.phone is not None: user.phone = data.phone
    if data.country is not None: user.country = data.country
    
    # 3. 선생님 ID 연결 로직
    if data.teacher_id is not None:
        if data.teacher_id == "": 
            # 빈 문자열이면 연결 해제
            user.teacher_id = None
        else:
            # 선생님 ID가 유효한지 검증
            teacher = session.get(User, data.teacher_id)
            if teacher and teacher.role == "teacher":
                user.teacher_id = data.teacher_id
            else:
                # 존재하지 않거나 학생 계정인 경우 에러 처리
                raise HTTPException(status_code=400, detail="존재하지 않는 선생님 ID입니다.")

    # 4. 저장
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {"status": "ok", "message": "Updated", "user": user}

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
