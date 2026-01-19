# backend/app/api/speech.py

from fastapi import APIRouter, UploadFile, File, Form
# 경로가 정확히 맞는지 확인 (app.core.speech_pro)
from app.core.speech_pro import speech_provider 

router = APIRouter()

@router.post("/evaluate")
async def evaluate_pronunciation(
    word: str = Form(...), 
    audio: UploadFile = File(...)
):
    audio_content = await audio.read()
    result = speech_provider.get_evaluation(word, audio_content)
    return result