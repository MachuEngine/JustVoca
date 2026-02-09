from fastapi import APIRouter, Depends, Request, HTTPException
from sqlmodel import Session, select, or_, SQLModel, Field
from typing import List, Optional
from datetime import datetime
from app.core.database import get_session
from app.models import Notice, User
from app.core.config import settings
from app.core.session import verify_session

router = APIRouter()

# [신규] 읽음 상태를 저장할 모델 (DB 테이블)
class NoticeRead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    notice_id: int
    user_id: str
    read_at: datetime = Field(default_factory=datetime.now)

# [신규] API 응답용 모델 (기존 Notice + read 필드)
class NoticeResponse(SQLModel):
    id: int
    title: str
    content: str
    created_at: datetime
    author: str
    scheduled_at: Optional[datetime] = None
    teacher_id: str
    read: bool = False  # 읽음 여부 추가

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

@router.get("/list", response_model=List[NoticeResponse])
def get_notice_list(request: Request, db: Session = Depends(get_session)):
    """
    [학생용] 공지사항 조회
    1. 학생의 담당 선생님(teacher_id)이 작성한 글만 조회
    2. 예약 발송(scheduled_at)인 경우, 현재 시간보다 과거인 것만 조회
    """
    student = _get_current_student(request, db)
    
    if not student.teacher_id:
        return []

    now = datetime.now()

    # 1. 공지사항 목록 조회
    statement = (
        select(Notice)
        .where(Notice.teacher_id == student.teacher_id)
        .where(or_(Notice.scheduled_at == None, Notice.scheduled_at <= now))
        .order_by(Notice.created_at.desc())
    )
    notices = db.exec(statement).all()

    # 2. 내가 읽은 공지사항 ID 조회
    read_statement = select(NoticeRead.notice_id).where(NoticeRead.user_id == student.uid)
    read_ids = db.exec(read_statement).all()
    read_ids_set = set(read_ids)

    # 3. 결과 합치기 (읽음 여부 표시)
    result = []
    for n in notices:
        result.append(NoticeResponse(
            **n.dict(),
            read=(n.id in read_ids_set) # 읽은 목록에 있으면 True
        ))
    
    return result


# [신규] 공지사항 읽음 처리 API
@router.post("/{notice_id}/read")
def mark_notice_read(notice_id: int, request: Request, db: Session = Depends(get_session)):
    student = _get_current_student(request, db)
    
    # 이미 읽었는지 확인
    statement = select(NoticeRead).where(
        NoticeRead.notice_id == notice_id,
        NoticeRead.user_id == student.uid
    )
    existing = db.exec(statement).first()
    
    if not existing:
        new_read = NoticeRead(notice_id=notice_id, user_id=student.uid)
        db.add(new_read)
        db.commit()
        
    return {"status": "success"}