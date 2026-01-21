# app/api/speech.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlmodel import Session
import os
import uuid
from pathlib import Path

# [추가] DB 관련 모듈 임포트
from app.core.database import get_session
from app.models import StudyLog

from app.audio_convert import convert_to_wav
from app.speechpro_client import evaluate_pronunciation

router = APIRouter()

TMP_DIR = Path("/tmp")

@router.post("/evaluate")
async def evaluate_speech(
    audio: UploadFile = File(...), 
    text: str = Form(...),
    # [추가] DB 저장을 위해 누가(user_id), 무엇을(word) 공부했는지 받습니다.
    user_id: str = Form(...),
    word: str = Form(...),
    session: Session = Depends(get_session)
):
    print(f"--- [진단] 요청 수신 시작: {text} (User: {user_id}) ---")
    print(f"[DEBUG] 요청 수신: 텍스트='{text}', 파일명='{audio.filename}'")

    temp_id = uuid.uuid4()
    temp_dir = "/tmp"  # WSL 환경이므로 /tmp 사용
    input_path = Path(f"{temp_dir}/up_{temp_id}{os.path.splitext(audio.filename)[1]}")
    wav_path: Path | None = None

    try:
        # 1) 업로드 저장 (기존 로직 유지)
        content = await audio.read()
        with open(input_path, "wb") as f:
            f.write(content)
        print(f"[DEBUG] 1. 파일 저장 완료: {input_path}")

        # 2) wav 변환 (기존 로직 유지)
        wav_path_str = convert_to_wav(input_path)
        print(f"[DEBUG] 2. 오디오 변환 완료: {wav_path_str}")

        if not wav_path_str:
            return {"success": False, "error": "오디오 변환 실패"}

        wav_path = Path(wav_path_str)

        # 3) 엔진 호출 (기존 로직 유지)
        print("[DEBUG] 3. 엔진 호출 시작 (GTP -> Model -> Score)...")
        score, full_result = evaluate_pronunciation(text, wav_path)
        print(f"[DEBUG] 4. 엔진 응답 수신 완료. 점수: {score}")

        # ✅ 엔진 통신/응답 에러면 success False (기존 로직 유지)
        if not full_result or (isinstance(full_result, dict) and full_result.get("error")):
            msg = (
                full_result.get("error")
                if isinstance(full_result, dict) and full_result.get("error")
                else "엔진 응답 없음"
            )
            return {"success": False, "error": msg}

        # 4) [신규 추가] 결과가 정상이면 DB에 학습 로그 저장
        # (기존 로직 흐름을 방해하지 않고, 마지막에 저장만 수행합니다)
        if score is not None:
            try:
                feedback_msg = "참 잘했어요!" if score >= 80 else "조금 더 연습해볼까요?"
                new_log = StudyLog(
                    user_id=user_id,
                    word=word,
                    score=float(score),
                    feedback=feedback_msg
                )
                session.add(new_log)
                session.commit()
                print(f"[DEBUG] 5. DB 저장 완료: {user_id} - {word} ({score}점)")
            except Exception as db_e:
                print(f"[Warning] DB 저장 실패 (평가는 정상 진행됨): {db_e}")
                # DB 저장이 실패해도 사용자는 평가 결과를 볼 수 있어야 하므로 pass

        # ✅ 정상일 때만 success True (기존 로직 유지)
        return {"success": True, "result": full_result, "score": score}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API Error] {e}")
        return {"success": False, "error": f"서버 내부 오류: {str(e)}"}
    finally:
        # 리소스 정리 (기존 로직 유지)
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