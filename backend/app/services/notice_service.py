# backend/app/services/notice_service.py
from sqlalchemy.orm import Session
from ..models import Notice

def add_notice(db: Session, title: str, content: str, author: str, scheduled_at):
    new_notice = Notice(
        title=title,
        content=content,
        author=author,
        scheduled_at=scheduled_at
    )
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    return new_notice