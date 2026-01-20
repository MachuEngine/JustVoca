# backend/app/api/speech.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.speech_pro import speech_provider

router = APIRouter()

@router.post("/evaluate")
async def evaluate_speech(
    audio: UploadFile = File(...),
    # [수정] 프론트엔드 변경(key='text')에 맞춰 파라미터 이름 수정
    text: str = Form(...) 
):
    try:
        # 오디오 파일 읽기
        audio_bytes = await audio.read()
        
        # 엔진 호출 (SpeechProProvider)
        result = speech_provider.get_evaluation(text, audio_bytes)
        
        if not result["success"]:
             # 실패 시 상세 로그나 에러 메시지 반환 가능
             return {"success": False, "error": result.get("error")}
             
        return {"success": True, "data": result["data"]}

    except Exception as e:
        print(f"Error in speech evaluation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")