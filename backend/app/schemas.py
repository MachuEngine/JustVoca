# backend/app/schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class UserLogin(BaseModel):
    id: str
    password: str

class UserRegister(BaseModel):
    id: str
    password: str
    name: str
    email: str
    phone: str
    country: str
    role: str = "student"
    # [추가] 회원가입 시 선생님 ID 입력 가능
    teacher_id: Optional[str] = None

class NoticeCreate(BaseModel):
    title: str
    content: str
    author: str
    scheduled_at: Optional[str] = None

class WrongNoteCreate(BaseModel):
    user_id: str
    topic: str
    question: str
    answer: str
    wrong_answer: str

class EvaluationResponse(BaseModel):
    score: int
    ai_feedback: str
    details: List[Dict[str, Any]]
    audio_url: str

# [수정] 프로필 수정 시 선생님 ID 변경 가능하도록 추가
class UserProfileUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    teacher_id: Optional[str] = None  # [추가됨]

# [신규] 학습 설정 수정 요청 데이터 (그대로 유지)
class UserSettingsUpdate(BaseModel):
    dailyGoal: Optional[int] = None
    reviewWrong: Optional[bool] = None

# [신규] 비밀번호 변경 요청 데이터 (그대로 유지)
class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str