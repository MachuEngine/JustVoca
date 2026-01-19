from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

# ------------------------------------------------------------
# 경로 기준 (JustVoca 루트)
# ------------------------------------------------------------
# 이 파일 위치: backend/app/services/vocab_loader.py 라고 가정
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # -> JustVoca


def normalize_audio_url(p: str) -> str:
    """
    index json / 엑셀 / legacy dict에서 어떤 형태가 오든 최종은 /audio/... 로 통일.
    - FastAPI mount: app.mount("/audio", StaticFiles(directory=.../assets/audio))
    """
    if not p:
        return ""
    p = str(p).strip().replace("\\", "/")
    p = p.lstrip("/")

    # 이미 /audio 또는 audio 로 온 경우
    if p.startswith("audio/"):
        return "/" + p
    if p.startswith("audio"):
        # 'audio' 단독 방지
        return "/audio" + p[5:] if len(p) > 5 else "/audio"

    if p.startswith("assets/audio/"):
        return "/audio/" + p.split("assets/audio/", 1)[1]

    # 흔히 level1/foo.wav 형태로 저장된 경우
    return "/audio/" + p


def normalize_image_url(p: str) -> str:
    """
    이미지는 FastAPI에서 /images 로 mount한다고 가정.
    - mount 대상 폴더는 실제 존재하는 폴더로 잡음
    - legacy가 절대경로/상대경로/폴더명 포함 등으로 주는 케이스를 최대한 흡수
    """
    if not p:
        return ""
    p = str(p).strip().replace("\\", "/")
    p = p.lstrip("/")

    # 이미 images/ 로 온 경우
    if p.startswith("images/"):
        return "/" + p
    if p.startswith("data/media/images/"):
        return "/images/" + p.split("data/media/images/", 1)[1]
    if p.startswith("media/images/"):
        return "/images/" + p.split("media/images/", 1)[1]

    # 파일명만 오는 경우도 있으니 그대로 /images 밑으로
    return "/images/" + p


def _pick_example(w: Dict[str, Any]) -> str:
    # legacy에서 예문 키가 섞여 있을 수 있어 후보를 넓게 잡음
    for k in ("example", "sentence", "ex", "sample", "example_sentence", "exampleText"):
        v = w.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _pick_audio_voca(w: Dict[str, Any]) -> str:
    # 단어 발음 오디오 후보키
    for k in ("audio_voca", "audio_word", "audio", "voca_audio", "word_audio", "tts"):
        v = w.get(k)
        if isinstance(v, str) and v.strip():
            return normalize_audio_url(v)
    return ""


def _pick_audio_ex(w: Dict[str, Any]) -> str:
    # 예문 오디오 후보키
    for k in ("audio_ex", "audio_example", "example_audio", "sentence_audio", "ex_audio"):
        v = w.get(k)
        if isinstance(v, str) and v.strip():
            return normalize_audio_url(v)
    return ""


def _pick_image(w: Dict[str, Any]) -> str:
    # 이미지 후보키
    for k in ("image", "img", "image_path", "imageUrl", "picture"):
        v = w.get(k)
        if isinstance(v, str) and v.strip():
            return normalize_image_url(v)
    return ""


def _as_card(topic: str, w: Any) -> Dict[str, Any]:
    """
    Study API가 기대하는 최소 카드 형태로 변환.
    """
    if isinstance(w, dict):
        word = (w.get("word") or w.get("voca") or w.get("term") or "").strip()
        if not word:
            # key라도 있으면 word로 사용
            word = legacy_word_key(w)
        return {
            "topic": topic,
            "word": word,
            "example": _pick_example(w),
            "audio_voca": _pick_audio_voca(w),
            "audio_ex": _pick_audio_ex(w),
            "image": _pick_image(w),
            # legacy 원본도 필요하면 여기에 달아둘 수 있음(프론트에는 안 써도 됨)
            # "raw": w,
        }

    # dict가 아닌 케이스(문자열 등)
    s = str(w).strip()
    return {"topic": topic, "word": s, "example": "", "audio_voca": "", "audio_ex": "", "image": ""}


def get_topics() -> List[str]:
    return legacy_list_topics()


def get_items_by_topic(topic: str) -> List[Dict[str, Any]]:
    raw = legacy_get_topic_words(topic)
    items = [_as_card(topic, w) for w in raw]

    # word 비어있는 항목 제거
    items = [it for it in items if it.get("word")]
    return items
