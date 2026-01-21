# app/speechpro_client.py
from __future__ import annotations

import base64
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ----------------------------------------------------------------------
# 엔진 주소
# ----------------------------------------------------------------------
ENGINE_URL = os.getenv("SPEECHPRO_ENGINE_URL", "http://112.220.79.222:33005/speechpro")


# ----------------------------------------------------------------------
# 유틸
# ----------------------------------------------------------------------
def normalize_spaces(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\u00A0\u2002\u2003\u2009\t\r\n]+", " ", text)
    return text.strip()


def _get_any(d: Dict[str, Any], *keys: str, default=None):
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d.get(k) is not None:
            return d.get(k)
    return default


def _engine_error_code(resp: Dict[str, Any]) -> int:
    if not isinstance(resp, dict):
        return 0
    code = _get_any(resp, "error code", "error_code", "errorCode", default=0)
    try:
        return int(code or 0)
    except Exception:
        return 0


def _make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.4,
        status_forcelist=(502, 503, 504),
        allowed_methods=frozenset(["POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=2, pool_maxsize=2)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


# ----------------------------------------------------------------------
# SpeechPro 호출
# ----------------------------------------------------------------------
def call_speechpro_evaluation_scorejson(text: str, wav_path: str) -> Dict[str, Any]:
    clean_text = normalize_spaces(text)
    if not clean_text:
        return {"success": False, "error": "텍스트가 비어 있습니다."}

    if not os.path.exists(wav_path):
        return {"success": False, "error": f"WAV 파일을 찾을 수 없습니다: {wav_path}"}

    req_id = "req_" + datetime.now().strftime("%H%M%S_%f")
    headers = {"Connection": "close"}

    s = _make_session()
    try:
        # 1) GTP
        r_gtp = s.post(
            f"{ENGINE_URL}/gtp",
            json={"id": req_id, "text": clean_text},
            timeout=(5, 30),
            headers=headers,
        )
        r_gtp.raise_for_status()
        gtp = r_gtp.json()

        if _engine_error_code(gtp) != 0:
            return {"success": False, "error": f"GTP 실패: {gtp}"}

        syll_ltrs = _get_any(gtp, "syll ltrs", "syll_ltrs")
        syll_phns = _get_any(gtp, "syll phns", "syll_phns")
        if not syll_ltrs or not syll_phns:
            return {"success": False, "error": f"GTP 응답에 syll 정보가 없습니다: {gtp}"}

        # 2) MODEL
        r_model = s.post(
            f"{ENGINE_URL}/model",
            json={
                "id": req_id,
                "text": clean_text,
                "syll ltrs": syll_ltrs,
                "syll phns": syll_phns,
            },
            timeout=(5, 30),
            headers=headers,
        )
        r_model.raise_for_status()
        model = r_model.json()

        if _engine_error_code(model) != 0:
            return {"success": False, "error": f"MODEL 실패: {model}"}

        fst = _get_any(model, "fst")
        if not fst:
            return {"success": False, "error": f"MODEL 응답에 fst가 없습니다: {model}"}

        model_syll_ltrs = _get_any(model, "syll ltrs", "syll_ltrs") or syll_ltrs
        model_syll_phns = _get_any(model, "syll phns", "syll_phns") or syll_phns

        # 3) SCOREJSON
        with open(wav_path, "rb") as f:
            wav_bytes = f.read()
        wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")

        score_payload: Dict[str, Any] = {
            "id": req_id,
            "text": clean_text,
            "syll ltrs": model_syll_ltrs,
            "syll phns": model_syll_phns,
            "fst": fst,
            "wav usr": wav_b64,
        }

        r_score = s.post(
            f"{ENGINE_URL}/scorejson",
            json=score_payload,
            timeout=(5, 60),
            headers=headers,
        )

        if r_score.status_code != 200:
            body = (r_score.text or "").strip()
            if len(body) > 800:
                body = body[:800] + "...(truncated)"
            return {
                "success": False,
                "error": f"SCOREJSON 실패: HTTP {r_score.status_code} - {body}",
            }

        score_data = r_score.json()

        if isinstance(score_data, dict) and isinstance(score_data.get("result"), str):
            try:
                score_data = json.loads(score_data["result"])
            except Exception:
                pass

        return {"success": True, "score_result": score_data}

    except Exception as e:
        return {"success": False, "error": f"엔진 통신 장애: {str(e)}"}
    finally:
        try:
            s.close()
        except Exception:
            pass


# ----------------------------------------------------------------------
# [수정됨] 점수 추출 로직 개선 함수
# ----------------------------------------------------------------------
def evaluate_pronunciation(text: str, wav_path: Path) -> Tuple[float, Dict[str, Any]]:
    result = call_speechpro_evaluation_scorejson(text=text, wav_path=str(wav_path))

    if not result.get("success"):
        return 0.0, {"error": result.get("error", "엔진 호출 실패")}

    raw = result.get("score_result", {}) or {}

    # 1. 중첩된 result 키 처리 (로그상 구조: raw['result']['quality']...)
    data = raw
    if "result" in raw and isinstance(raw["result"], dict):
        data = raw["result"]

    score = 0.0
    try:
        # 우선순위 1: 최상위 score (있다면)
        if data.get("score") is not None:
            score = float(data.get("score"))
        
        # 우선순위 2: quality -> score
        elif "quality" in data and isinstance(data["quality"], dict):
            q = data["quality"]
            if q.get("score") is not None:
                score = float(q.get("score"))
            
            # 우선순위 3: sentences 배열에서 !SIL이 아닌 실제 문장 점수 찾기
            # 로그에 따르면 !SIL은 점수가 높지만 실제 발음이 아님
            elif "sentences" in q and isinstance(q["sentences"], list):
                # !SIL이 아니고 점수가 있는 문장만 필터링
                valid_sentences = [
                    s for s in q["sentences"] 
                    if s.get("text") != "!SIL" and s.get("score") is not None
                ]
                
                if valid_sentences:
                    # 첫 번째 유효 문장의 점수 사용 (예: "안녕하세요": 78.8)
                    score = float(valid_sentences[0]["score"])
                    
    except Exception as e:
        print(f"[SpeechPro] 점수 추출 중 에러: {e}")
        score = 0.0

    return score, raw