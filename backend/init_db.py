# backend/init_db.py
from app.core.database import engine, Base
from app.models import User, Notice, StudyProgress, StudyLog

print("데이터베이스 테이블 생성 중...")
Base.metadata.create_all(bind=engine)
print("테이블 생성 완료!")

# 테스트용 유저 한 명 추가
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

db = SessionLocal()
if not db.query(User).filter(User.id == "테스트유저").first():
    test_user = User(id="테스트유저", name="테스트유저", role="student")
    db.add(test_user)
    db.commit()
    print("👤 테스트 유저 '테스트유저' 생성 완료!")
db.close()