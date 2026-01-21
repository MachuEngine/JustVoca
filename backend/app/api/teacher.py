# app/api/teacher.py
from fastapi import APIRouter, HTTPException, Request, Depends, Body
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime  # [추가] datetime 모듈 임포트 필수!
from app.core.database import get_session
from app.models import User, StudyProgress, StudyLog, Notice
from app.core.config import settings
from app.core.session import verify_session

router = APIRouter(tags=["teacher"])

def _require_teacher(request: Request, session: Session) -> User:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    if not token: raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    sess = verify_session(token)
    if not sess: raise HTTPException(status_code=401, detail="세션 만료")
    user = session.get(User, sess["uid"])
    if not user or user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="권한 없음")
    return user

@router.get("/students")
def list_students(request: Request, session: Session = Depends(get_session)):
    _require_teacher(request, session)
    students = session.exec(select(User).where(User.role == "student")).all()
    items = []
    for student in students:
        prog = session.exec(select(StudyProgress).where(StudyProgress.user_id == student.uid)).first()
        avg_score = session.exec(select(func.avg(StudyLog.score)).where(StudyLog.user_id == student.uid)).first() or 0.0
        
        # [수정] 진도율 계산 로직 통일
        # 학생 홈과 동일하게: ((현재페이지 - 1) / 전체10페이지) * 100
        # 페이지가 1이면(시작단계) 0%, 2이면 10% ...
        current_page = prog.current_page if prog else 1
        progress_rate = min(1.0, ((current_page - 1) * 10) / 100)

        items.append({
            "uid": student.uid, 
            "name": student.name, 
            "country": student.country or "KR",
            "current_level": prog.level if prog else "미시작", 
            "current_page": current_page,
            "avg_score": round(float(avg_score), 1), 
            "progress_rate": progress_rate, # 수정된 비율 적용
        })
    return {"ok": True, "items": items}

@router.get("/notices", response_model=List[Notice])
def list_teacher_notices(request: Request, session: Session = Depends(get_session)):
    _require_teacher(request, session)
    return session.exec(select(Notice).order_by(Notice.created_at.desc())).all()

@router.post("/notice")
async def send_notice(
    title: str = Body(...), 
    content: str = Body(...), 
    scheduled_at: Optional[str] = Body(None), 
    request: Request = None, 
    session: Session = Depends(get_session)
):
    teacher = _require_teacher(request, session)
    
    # [수정] 문자열로 들어온 날짜를 실제 datetime 객체로 변환
    dt_scheduled = None
    if scheduled_at:
        try:
            # 프론트엔드에서 보내는 'YYYY-MM-DDTHH:mm' 형식을 파싱
            dt_scheduled = datetime.fromisoformat(scheduled_at)
        except ValueError:
            # 날짜 형식이 올바르지 않으면 None으로 처리하거나 에러를 낼 수 있음
            pass 

    new_notice = Notice(
        title=title, 
        content=content, 
        author=teacher.name,
        scheduled_at=dt_scheduled # [수정] 변환된 datetime 객체를 저장
    )
    session.add(new_notice)
    session.commit()
    return {"status": "ok"}



@router.get("/student/{student_id}")
def get_student_detail(student_id: str, request: Request, session: Session = Depends(get_session)):
    """특정 학생의 상세 정보(연락처 포함) 조회"""
    # 1. 선생님 권한 확인
    _require_teacher(request, session)
    
    # 2. 학생 조회
    student = session.get(User, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
        
    # 3. 학습 진도 정보 조회 (옵션)
    prog = session.exec(select(StudyProgress).where(StudyProgress.user_id == student_id)).first()
    
    return {
        "status": "ok",
        "info": {
            "uid": student.uid,
            "name": student.name,
            "email": student.email or "-",      # 이메일 (없으면 -)
            "phone": student.phone or "-",      # 전화번호 (없으면 -)
            "country": student.country or "KR",
            "joined_at": student.created_at,    # 가입일 (User 모델에 있다면)
        },
        "progress": {
            "level": prog.level if prog else "미시작",
            "page": prog.current_page if prog else 0
        }
    }