# app/api/speech.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import uuid
from pathlib import Path

from app.audio_convert import convert_to_wav
from app.speechpro_client import evaluate_pronunciation

router = APIRouter()

TMP_DIR = Path("/tmp")


@router.post("/evaluate")
async def evaluate_speech(audio: UploadFile = File(...), text: str = Form(...)):
    print(f"--- [진단] 요청 수신 시작: {text} ---")
    print(f"[DEBUG] 요청 수신: 텍스트='{text}', 파일명='{audio.filename}'")

    temp_id = uuid.uuid4()
    temp_dir = "/tmp"  # WSL 환경이므로 /tmp 사용
    input_path = Path(f"{temp_dir}/up_{temp_id}{os.path.splitext(audio.filename)[1]}")
    wav_path: Path | None = None

    try:
        # 1) 업로드 저장
        content = await audio.read()
        with open(input_path, "wb") as f:
            f.write(content)
        print(f"[DEBUG] 1. 파일 저장 완료: {input_path}")

        # 2) wav 변환
        wav_path_str = convert_to_wav(input_path)
        print(f"[DEBUG] 2. 오디오 변환 완료: {wav_path_str}")

        if not wav_path_str:
            return {"success": False, "error": "오디오 변환 실패"}

        wav_path = Path(wav_path_str)

        # 3) 엔진 호출
        print("[DEBUG] 3. 엔진 호출 시작 (GTP -> Model -> Score)...")
        score, full_result = evaluate_pronunciation(text, wav_path)
        print(f"[DEBUG] 4. 엔진 응답 수신 완료. 점수: {score}")

        # ✅ 엔진 통신/응답 에러면 success False
        if not full_result or (isinstance(full_result, dict) and full_result.get("error")):
            msg = (
                full_result.get("error")
                if isinstance(full_result, dict) and full_result.get("error")
                else "엔진 응답 없음"
            )
            return {"success": False, "error": msg}

        # ✅ 정상일 때만 success True
        return {"success": True, "result": full_result, "score": score}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API Error] {e}")
        return {"success": False, "error": f"서버 내부 오류: {str(e)}"}
    finally:
        # 리소스 정리
        try:
            if input_path.exists():
                input_path.unlink()
        except Exception:
            pass
        try:
            if wav_path and wav_path.exists():
                wav_path.unlink()
        except Exception:
            pass
