# backend/app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.core.database import get_session  # [필수] SQL 세션 가져오기
from app.models import User                # [필수] User 테이블 가져오기
from app.schemas import UserLogin, UserRegister
from app.core.session import hash_password, verify_password

router = APIRouter()

@router.post("/login")
async def login(data: UserLogin, session: Session = Depends(get_session)):
    print(f"[Login Attempt] ID: {data.id}")

    # 1. DB에서 사용자 조회 (load_users 아님!)
    user = session.get(User, data.id)
    
    if not user:
        raise HTTPException(status_code=401, detail="존재하지 않는 아이디입니다.")
    
    # 2. 비밀번호 검증 (평문 & 해시 모두 지원)
    # verify_password: 해시된 값 비교
    # user.pw == data.password: 초기 데이터(1111 등)용 평문 비교
    is_valid_hash, _ = verify_password(user.pw, data.password)
    is_valid_plain = (user.pw == data.password)

    if not is_valid_hash and not is_valid_plain:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    # 3. 승인 대기 확인
    if user.role == "teacher" and not user.is_approved:
        raise HTTPException(status_code=403, detail="승인 대기 중인 계정입니다.")

    print(f" -> 로그인 성공: {user.name}")
    return {"status": "ok", "user": user}

@router.post("/register")
async def register(data: UserRegister, session: Session = Depends(get_session)):
    # 1. 중복 확인
    if session.get(User, data.id):
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    
    # 2. 선생님은 승인 대기(False), 학생은 자동 승인(True)
    is_approved = False if data.role == "teacher" else True
    
    # 3. DB에 저장
    new_user = User(
        uid=data.id,
        pw=hash_password(data.password),
        name=data.name,
        email=data.email,
        phone=data.phone,
        country=data.country,
        role=data.role,
        is_approved=is_approved,
        progress={"settings": {"goal": 10}, "topics": {}}
    )
    
    session.add(new_user)
    session.commit()
    
    return {"status": "ok"}