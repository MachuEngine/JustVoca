# backend/init_db.py
from app.core.database import engine, Base
from app.models import User, Notice, StudyProgress, StudyLog

print("🚀 데이터베이스 테이블 생성 중...")
Base.metadata.create_all(bind=engine)
print("✅ 테이블 생성 완료!")

# 테스트용 유저 한 명 추가 (선택 사항)
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

db = SessionLocal()
if not db.query(User).filter(User.id == "안종민").first():
    test_user = User(id="안종민", name="안종민", role="student")
    db.add(test_user)
    db.commit()
    print("👤 테스트 유저 '안종민' 생성 완료!")
db.close()