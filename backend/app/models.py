from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .core.database import Base # 기존 Base 경로 유지

# 1. 사용자 테이블 (선생님/학생 공통)
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # 학번 또는 고유 ID
    name = Column(String, nullable=False)
    role = Column(String, default="student") # "student" 또는 "teacher"
    hashed_password = Column(String) # 로그인용 비밀번호
    
    # 관계 설정: 사용자가 삭제되면 관련 진도와 로그도 삭제됨
    progress = relationship("StudyProgress", back_populates="owner", cascade="all, delete-orphan")
    logs = relationship("StudyLog", back_populates="student", cascade="all, delete-orphan")

# 2. 학습 진도 테이블 (학생별/레벨별 현재 위치)
class StudyProgress(Base):
    __tablename__ = "study_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    level = Column(String) # 초급1, 초급2, 중급1 등 시트 이름과 매칭
    current_page = Column(Integer, default=1) # 현재 학습 중인 페이지(10개 단위)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    owner = relationship("User", back_populates="progress")

# 3. 학습 로그 테이블 (발음 평가 결과 기록)
class StudyLog(Base):
    __tablename__ = "study_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    word = Column(String)
    score = Column(Float)
    feedback = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    student = relationship("User", back_populates="logs")

# 4. 기존 공지사항 테이블 (유지)
class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    author = Column(String)
    scheduled_at = Column(DateTime)