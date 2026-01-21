from fastapi import APIRouter, Depends, Request, HTTPException
from sqlmodel import Session, select, or_
from typing import List
from datetime import datetime
from app.core.database import get_session
from app.models import Notice, User
from app.core.config import settings
from app.core.session import verify_session

router = APIRouter()

# [내부 함수] 현재 로그인한 학생 정보 가져오기
def _get_current_student(request: Request, session: Session) -> User:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    sess = verify_session(token)
    if not sess:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
        
    user = session.get(User, sess["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
    return user

@router.get("/list", response_model=List[Notice])
def get_notice_list(request: Request, db: Session = Depends(get_session)):
    """
    [학생용] 공지사항 조회
    1. 학생의 담당 선생님(teacher_id)이 작성한 글만 조회
    2. 예약 발송(scheduled_at)인 경우, 현재 시간보다 과거인 것만 조회
    """
    # 1. 로그인한 학생 정보 조회
    student = _get_current_student(request, db)
    
    # 담당 선생님이 없으면 공지사항 없음
    if not student.teacher_id:
        return []

    now = datetime.now()

    # 2. 쿼리 작성 (선생님 필터링 + 예약 시간 체크)
    statement = (
        select(Notice)
        .where(Notice.teacher_id == student.teacher_id)  # 내 선생님의 글만
        .where(
            or_(
                Notice.scheduled_at == None,       # 예약 설정이 없거나 (즉시 발송)
                Notice.scheduled_at <= now         # 예약 시간이 현재보다 과거인 경우
            )
        )
        .order_by(Notice.created_at.desc())        # 최신순 정렬
    )
    
    return db.exec(statement).all()