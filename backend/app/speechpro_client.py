# speechpro_client.py
# SpeechPro 엔진 연동 (GTP -> Model -> ScoreJSON)
# - 기존 scorefile(multipart) 방식 대신 scorejson(JSON + base64 wav usr) 방식으로 안정화
# - evaluate_pronunciation(text, wav_path: Path) -> (score: float, full_result: dict) 형태 유지

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
    # NBSP 등 다양한 공백/개행을 일반 공백으로 치환
    text = re.sub(r"[\u00A0\u2002\u2003\u2009\t\r\n]+", " ", text)
    return text.strip()


def _get_any(d: Dict[str, Any], *keys: str, default=None):
    """공백키/언더바키 등 혼용 대응"""
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d.get(k) is not None:
            return d.get(k)
    return default


def _engine_error_code(resp: Dict[str, Any]) -> int:
    """엔진이 error code / error_code 등을 섞어서 주는 경우 대응"""
    if not isinstance(resp, dict):
        return 0
    code = _get_any(resp, "error code", "error_code", "errorCode", default=0)
    try:
        return int(code or 0)
    except Exception:
        return 0


def _make_session() -> requests.Session:
    """
    재시도/연결 관리 세션
    - IncompleteRead/일시적 네트워크 장애에 대비해 retry 적용
    """
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
# SpeechPro 호출 (scorejson 방식)
# ----------------------------------------------------------------------
def call_speechpro_evaluation_scorejson(text: str, wav_path: str) -> Dict[str, Any]:
    """
    1) /gtp
    2) /model
    3) /scorejson  (JSON + base64 wav usr)
    """
    clean_text = normalize_spaces(text)
    if not clean_text:
        return {"success": False, "error": "텍스트가 비어 있습니다."}

    if not os.path.exists(wav_path):
        return {"success": False, "error": f"WAV 파일을 찾을 수 없습니다: {wav_path}"}

    req_id = "req_" + datetime.now().strftime("%H%M%S_%f")
    headers = {"Connection": "close"}  # keep-alive로 인한 간헐 끊김 회피

    s = _make_session()
    try:
        # --- 1) GTP ---
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

        # --- 2) MODEL ---
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

        # ✅ 엔진에 따라 MODEL 응답에는 syll 정보가 없을 수 있음 (fst만 내려줌)
        #    이 경우 GTP에서 받은 syll 값을 그대로 사용
        model_syll_ltrs = _get_any(model, "syll ltrs", "syll_ltrs") or syll_ltrs
        model_syll_phns = _get_any(model, "syll phns", "syll_phns") or syll_phns


        # --- 3) SCOREJSON (base64 wav usr) ---
        with open(wav_path, "rb") as f:
            wav_bytes = f.read()

        wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")

        # ✅ scorejson은 최상위 payload로 전송 (config wrapper 제거)
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

        # ✅ 400일 때 본문을 같이 보면 바로 원인 확정 가능
        if r_score.status_code != 200:
            body = (r_score.text or "").strip()
            if len(body) > 800:
                body = body[:800] + "...(truncated)"
            return {
                "success": False,
                "error": f"SCOREJSON 실패: HTTP {r_score.status_code} - {body}",
            }

        score_data = r_score.json()

        # scorejson 결과가 {"result": "...json string..."} 형태일 수 있어 파싱 보정
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
# 외부에서 사용하는 함수 (speech.py에서 import)
# ----------------------------------------------------------------------
def evaluate_pronunciation(text: str, wav_path: Path) -> Tuple[float, Dict[str, Any]]:
    """
    FastAPI에서 호출:
      score, full_result = evaluate_pronunciation(text, wav_path)

    반환:
      (점수, 엔진 원본 결과 dict)
    실패 시:
      (0.0, {"error": "..."} )
    """
    result = call_speechpro_evaluation_scorejson(text=text, wav_path=str(wav_path))

    if not result.get("success"):
        return 0.0, {"error": result.get("error", "엔진 호출 실패")}

    raw = result.get("score_result", {}) or {}

    # 점수 후보들 안전 추출
    score = 0.0
    try:
        if isinstance(raw, dict):
            if raw.get("score") is not None:
                score = float(raw.get("score") or 0.0)
            elif "quality" in raw and isinstance(raw["quality"], dict):
                q = raw["quality"]
                if q.get("score") is not None:
                    score = float(q.get("score") or 0.0)
                else:
                    sent0 = q.get("sentences", [{}])[0] if isinstance(q.get("sentences"), list) else {}
                    if isinstance(sent0, dict) and sent0.get("score") is not None:
                        score = float(sent0.get("score") or 0.0)
    except Exception:
        score = 0.0

    return score, raw
