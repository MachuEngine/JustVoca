# backend/app/api/notice.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.models import Notice
from typing import List

router = APIRouter()

@router.get("/list", response_model=List[Notice])
def get_notice_list(db: Session = Depends(get_session)):
    """[학생용] 전체 공지사항 목록을 최신순으로 가져옵니다."""
    statement = select(Notice).order_by(Notice.created_at.desc())
    return db.exec(statement).all()