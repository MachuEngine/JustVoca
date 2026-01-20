# backend/app/models.py
from typing import Optional, Dict
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON

# 1. 유저 모델 (필드 추가됨)
class User(SQLModel, table=True):
    uid: str = Field(primary_key=True)
    name: str = "체험 사용자"
    pw: str
    role: str = "student" # student, teacher, admin
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    
    # [추가] 관리자 승인 로직을 위해 필요
    is_approved: bool = Field(default=True) 
    created_at: datetime = Field(default_factory=datetime.now)

    progress: Dict = Field(default={}, sa_type=JSON)

# 2. 학습 진도 모델
class StudyProgress(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    level: str
    current_page: int = 1
    updated_at: datetime = Field(default_factory=datetime.now)

# 3. 학습 로그 모델
class StudyLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    word: str
    score: float
    feedback: str
    created_at: datetime = Field(default_factory=datetime.now)

# 4. 단어 모델
class Word(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    level: str
    word: str
    pronunciation: str
    meaning: str
    meaning_en: str
    example: str
    audio_path: str

# 5. 공지사항 모델
class Notice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    author: str
    scheduled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)