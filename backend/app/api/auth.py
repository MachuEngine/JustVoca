# backend/app/api/auth.py
from fastapi import APIRouter, HTTPException, Body
from app.core.session import load_users, save_users, hash_password, verify_password
from app.schemas import UserLogin, UserRegister
from datetime import datetime

router = APIRouter()

@router.post("/login")
async def login(data: UserLogin):
    users = load_users()
    user = users.get(data.id)
    if not user:
        raise HTTPException(status_code=401, detail="아이디가 존재하지 않습니다.")
    
    # 평문/해시 비밀번호 모두 지원 (Flet 호환)
    if user["pw"] != data.password:
        valid, _ = verify_password(user["pw"], data.password)
        if not valid:
             raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    if user.get("role") == "teacher" and not user.get("is_approved"):
        raise HTTPException(status_code=403, detail="승인 대기 중인 계정입니다.")

    return {"status": "ok", "user": user}

@router.post("/register")
async def register(data: UserRegister):
    users = load_users()
    if data.id in users:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    
    users[data.id] = {
        "uid": data.id,
        "pw": hash_password(data.password),
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "country": data.country,
        "role": data.role,
        "is_approved": False if data.role == "teacher" else True,
        "created_at": datetime.now().isoformat(),
        "progress": {"settings": {"goal": 10}, "topics": {}}
    }
    save_users(users)
    return {"status": "ok"}