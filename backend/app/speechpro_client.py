from __future__ import annotations

import os
import json
import requests
from pathlib import Path
from typing import Any, Dict, Tuple
from datetime import datetime

# 엔진 URL 설정
ENGINE_URL = "http://112.220.79.222:33005/speechpro"

def log_write(msg: str):
    """간단한 콘솔 로깅"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def call_speechpro_evaluation(text: str, audio_path: str) -> dict:
    """
    SpeechPro 엔진에 직접 요청 (src/utils.py 로직 이식)
    """
    if not os.path.exists(audio_path):
        return {"success": False, "error": "오디오 파일을 찾을 수 없습니다."}

    try:
        req_id = "req_" + datetime.now().strftime("%H%M%S")
        log_write(f"[SpeechPro] 평가 요청: {text} (파일: {os.path.basename(audio_path)})")

        # [1단계] GTP
        try:
            resp_gtp = requests.post(f"{ENGINE_URL}/gtp", json={"id": req_id, "text": text}, timeout=5)
            resp_gtp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"엔진 연결 실패(GTP): {e}"}
            
        gtp_data = resp_gtp.json()
        if gtp_data.get("error code", 0) != 0:
             return {"success": False, "error": f"GTP 에러: {gtp_data}"}
        
        # [2단계] Model
        model_payload = {
            "id": req_id, "text": text,
            "syll ltrs": gtp_data.get("syll ltrs"),
            "syll phns": gtp_data.get("syll phns")
        }
        resp_model = requests.post(f"{ENGINE_URL}/model", json=model_payload, timeout=5)
        if resp_model.status_code != 200:
            return {"success": False, "error": f"Model 에러: {resp_model.text}"}
        model_data = resp_model.json()
        
        # [3단계] Score
        config_dict = {
            "id": req_id, "text": text,
            "syll ltrs": model_data.get("syll ltrs"),
            "syll phns": model_data.get("syll phns"), "fst": model_data.get("fst")
        }
        
        with open(audio_path, "rb") as f:
            files = {"wav_usr": (os.path.basename(audio_path), f, "audio/wav")}
            data = {"config": json.dumps(config_dict)}
            resp_score = requests.post(f"{ENGINE_URL}/scorefile", files=files, data=data, timeout=15)
            
        if resp_score.status_code == 200:
            result = resp_score.json()
            if isinstance(result.get("result"), str): # 이중 인코딩 처리
                try: result = json.loads(result["result"])
                except: pass
            
            score = result.get('score', 0)
            log_write(f"[SpeechPro] 평가 성공! 점수: {score}")
            return {"success": True, "score": result}
        else:
            return {"success": False, "error": f"채점 실패 ({resp_score.status_code}): {resp_score.text}"}

    except Exception as e:
        log_write(f"[SpeechPro Exception] {str(e)}")
        return {"success": False, "error": f"통신 오류: {str(e)}"}

# API에서 호출하는 래퍼 함수
def evaluate_pronunciation(text: str, wav_path: Path) -> Tuple[float, Dict[str, Any]]:
    result = call_speechpro_evaluation(text=text, audio_path=str(wav_path))

    if not result.get("success"):
        return 0.0, {"error": result.get("error")}

    raw_score = result.get("score", {})
    if isinstance(raw_score, dict):
        final_score = float(raw_score.get("score", 0.0))
        return final_score, raw_score
    
    return 0.0, {}