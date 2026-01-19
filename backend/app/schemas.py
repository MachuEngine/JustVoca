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