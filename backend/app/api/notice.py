# 1. Django 방식(Notice.objects.create)은 삭제하세요.
# 2. FastAPI/SQLAlchemy 방식은 아래와 같습니다.

from sqlalchemy.orm import Session
from app.models import Notice

def add_notice(db: Session, title, content, author, scheduled_at):
    # 객체를 생성합니다.
    new_notice = Notice(
        title=title,
        content=content,
        author=author,
        scheduled_at=scheduled_at
    )
    db.add(new_notice)    # DB에 추가
    db.commit()           # 저장 확정
    db.refresh(new_notice) # 생성된 ID 등 정보 동기화
    return new_notice