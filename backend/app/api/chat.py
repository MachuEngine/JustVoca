# backend/app/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from app.core.config import settings
from app.core.prompts import get_system_prompt
import os
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter()
client = OpenAI(api_key=API_KEY)

# 요청 데이터 구조 확장 (history 필드 추가)
class ChatRequest(BaseModel):
    message: str
    user_id: str
    mode: str = "free_talk"  # 기본값: 일반 대화 (옵션: correction, quiz)
    user_level: str = "Beginner" # 나중에 DB에서 가져올 수도 있음 (Beginner, Intermediate)
    topic: str = "" # 퀴즈나 특정 주제 대화 시 사용
    # 이전 대화 내역을 받을 리스트 (role과 content를 가진 딕셔너리 리스트)
    history: List[Dict[str, str]] = [] 

@router.post("/message")
async def chat_with_ai(request: ChatRequest):
    try:
        # 1. 프롬프트 생성 (동적으로 조립)
        system_content = get_system_prompt(
            mode=request.mode, 
            user_level=request.user_level,
            topic=request.topic
        )

        # 2. OpenAI에 보낼 메시지 구성
        # 순서: [시스템 프롬프트] -> [이전 대화 내역(최대 10개)] -> [현재 사용자 질문]
        messages = [{"role": "system", "content": system_content}]
        
        # 히스토리 추가 (OpenAI 형식에 맞게 들어옴)
        messages.extend(request.history)

        # 현재 질문 추가
        messages.append({"role": "user", "content": request.message})

        # 3. OpenAI 호출
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # 예산이 된다면 gpt-4o-mini
            messages=messages,
            temperature=0.7, # 창의성 조절 (0.7: 적당함, 0.2: 사실적)
        )
        
        answer = response.choices[0].message.content
        return {"response": answer}

    except Exception as e:
        print(f"OpenAI Error: {e}")
        raise HTTPException(status_code=500, detail=f"챗봇 오류: {str(e)}")