# app/api/teacher.py
from fastapi import APIRouter, HTTPException, Request, Depends, Body
from sqlmodel import Session, select, func
from typing import List, Optional
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
        items.append({
            "uid": student.uid, "name": student.name, "country": student.country or "KR",
            "current_level": prog.level if prog else "미시작", "current_page": prog.current_page if prog else 1,
            "avg_score": round(float(avg_score), 1), "progress_rate": min(1.0, (prog.current_page * 10) / 100) if prog else 0.0,
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
    scheduled_at: Optional[str] = Body(None), # [수정] 예약 시간 필드 추가
    request: Request = None, 
    session: Session = Depends(get_session)
):
    teacher = _require_teacher(request, session)
    # [수정] Notice 모델 생성 시 예약 시간 포함
    new_notice = Notice(
        title=title, 
        content=content, 
        author=teacher.name,
        scheduled_at=scheduled_at
    )
    session.add(new_notice)
    session.commit()
    return {"status": "ok"}