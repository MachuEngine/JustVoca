# backend/app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models import User

router = APIRouter()

# 승인 대기 중인 선생님 목록 조회
@router.get("/pending_teachers")
async def get_pending(session: Session = Depends(get_session)):
    # SQL: SELECT * FROM user WHERE role='teacher' AND is_approved=False
    statement = select(User).where(User.role == "teacher", User.is_approved == False)
    pending_users = session.exec(statement).all()
    return pending_users

# 선생님 승인 처리
@router.post("/approve/{uid}")
async def approve(uid: str, session: Session = Depends(get_session)):
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    if user.role == "teacher":
        user.is_approved = True
        session.add(user)
        session.commit()
        
    return {"status": "ok"}

@router.get("/system_settings")
async def get_system_settings():
    # 시스템 설정은 아직 파일로 관리하거나 간단히 리턴해도 무방함
    return {"default_goal": 10}