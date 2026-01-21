# app/api/teacher.py
from fastapi import APIRouter, HTTPException, Request, Depends, Body
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
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
    # 1. 현재 로그인한 선생님 정보 가져오기
    teacher = _require_teacher(request, session)
    
    # 2. [수정됨] 해당 선생님이 담당하는 학생만 조회 (User.teacher_id == teacher.uid)
    #    (관리자인 경우 모든 학생을 볼 수도 있겠지만, 여기선 엄격하게 자기 학생만 봅니다)
    query = select(User).where(User.role == "student")
    
    # 만약 선생님이 'admin' 권한이 아니라 일반 'teacher'라면, 본인 학생만 필터링
    if teacher.role == "teacher":
        query = query.where(User.teacher_id == teacher.uid)
        
    students = session.exec(query).all()

    items = []
    for student in students:
        prog = session.exec(select(StudyProgress).where(StudyProgress.user_id == student.uid)).first()
        avg_score = session.exec(select(func.avg(StudyLog.score)).where(StudyLog.user_id == student.uid)).first() or 0.0
        
        current_page = prog.current_page if prog else 1
        progress_rate = min(1.0, ((current_page - 1) * 10) / 100)

        items.append({
            "uid": student.uid, 
            "name": student.name, 
            "country": student.country or "KR",
            "current_level": prog.level if prog else "미시작", 
            "current_page": current_page,
            "avg_score": round(float(avg_score), 1), 
            "progress_rate": progress_rate,
        })
    return {"ok": True, "items": items}

@router.get("/notices", response_model=List[Notice])
def list_teacher_notices(request: Request, session: Session = Depends(get_session)):
    _require_teacher(request, session)
    # 공지사항도 추후엔 '내 반 공지'만 보이게 할 수 있으나, 일단 전체 공지로 둡니다.
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
    
    dt_scheduled = None
    if scheduled_at:
        try:
            dt_scheduled = datetime.fromisoformat(scheduled_at)
        except ValueError:
            pass 

    new_notice = Notice(
        title=title, 
        content=content, 
        author=teacher.name,
        scheduled_at=dt_scheduled
    )
    session.add(new_notice)
    session.commit()
    return {"status": "ok"}

@router.get("/student/{student_id}")
def get_student_detail(student_id: str, request: Request, session: Session = Depends(get_session)):
    teacher = _require_teacher(request, session)
    
    # [수정] 상세 조회 시에도 내 학생인지 검증하는 것이 안전함
    student = session.get(User, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    
    # 일반 선생님은 자기 학생만 볼 수 있음
    if teacher.role == "teacher" and student.teacher_id != teacher.uid:
        raise HTTPException(status_code=403, detail="담당 학생이 아닙니다.")
        
    prog = session.exec(select(StudyProgress).where(StudyProgress.user_id == student_id)).first()
    
    return {
        "status": "ok",
        "info": {
            "uid": student.uid,
            "name": student.name,
            "email": student.email or "-",
            "phone": student.phone or "-",
            "country": student.country or "KR",
            "joined_at": student.created_at,
        },
        "progress": {
            "level": prog.level if prog else "미시작",
            "page": prog.current_page if prog else 0
        }
    }