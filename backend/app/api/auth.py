# backend/app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends, Response
from sqlmodel import Session
from pydantic import BaseModel  # [추가] 요청 데이터 정의를 위해 필요
from app.core.database import get_session
from app.models import User
from app.schemas import UserLogin, UserRegister
from app.core.session import hash_password, verify_password
from app.core.config import settings

router = APIRouter()

# [신규 추가] 아이디 중복 확인용 요청 모델
class IdCheckRequest(BaseModel):
    id: str

@router.post("/login")
async def login(
    response: Response,  # 쿠키 설정을 위해 Response 객체 주입
    data: UserLogin, 
    session: Session = Depends(get_session)
):
    print(f"[Login Attempt] ID: {data.id}")

    # 1. DB에서 사용자 조회
    user = session.get(User, data.id)
    
    if not user:
        raise HTTPException(status_code=401, detail="존재하지 않는 아이디입니다.")
    
    # 2. 비밀번호 검증
    is_valid_hash, _ = verify_password(user.pw, data.password)
    is_valid_plain = (user.pw == data.password)

    if not is_valid_hash and not is_valid_plain:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    # 3. 승인 대기 확인
    if user.role == "teacher" and not user.is_approved:
        raise HTTPException(status_code=403, detail="승인 대기 중인 계정입니다.")

    # [쿠키 설정]
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=user.uid,
        max_age=3600 * 24,  # 24시간
        path="/",           # 모든 경로 허용
        httponly=True,
        samesite="lax",
        secure=False        # 로컬(http) 환경이므로 False
    )

    print(f" -> 로그인 성공: {user.name} (Cookie Set for path=/)")
    return {"status": "ok", "user": user}

@router.post("/register")
async def register(data: UserRegister, session: Session = Depends(get_session)):
    if session.get(User, data.id):
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    
    # 선생님은 승인 대기, 학생은 자동 승인
    is_approved = False if data.role == "teacher" else True
    
    # [추가] 선생님 ID 유효성 검증 및 할당
    valid_teacher_id = None
    if data.role == "student" and data.teacher_id:
        teacher = session.get(User, data.teacher_id)
        if teacher and teacher.role == "teacher":
            valid_teacher_id = data.teacher_id
        else: raise HTTPException(status_code=400, detail="존재하지 않는 선생님 ID입니다.")

    new_user = User(
        uid=data.id,
        pw=hash_password(data.password),
        name=data.name,
        email=data.email,
        phone=data.phone,
        country=data.country,
        role=data.role,
        teacher_id=valid_teacher_id, # [저장]
        is_approved=is_approved,
        progress={"settings": {"goal": 10}, "topics": {}}
    )
    
    session.add(new_user)
    session.commit()
    
    return {"status": "ok"}

# [신규 추가] 아이디 중복 확인 엔드포인트
@router.post("/check-id")
async def check_id(data: IdCheckRequest, session: Session = Depends(get_session)):
    """
    아이디 중복 여부를 확인합니다.
    - user가 존재하면(검색됨) -> is_available: False (사용 불가)
    - user가 없으면(None) -> is_available: True (사용 가능)
    """
    user = session.get(User, data.id)
    return {"is_available": user is None}