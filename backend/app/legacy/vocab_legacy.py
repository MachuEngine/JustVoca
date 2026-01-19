from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from app.legacy.vocab_source import load_vocab_data  # type: ignore
except Exception:
    load_vocab_data = None  # type: ignore

_VOCAB_CACHE: Optional[Any] = None

def _fallback_load_vocab() -> Any:
    raise RuntimeError(
        "vocab loader import 실패: backend/app/legacy/vocab_source.py 가 없거나 "
        "load_vocab_data() 함수가 없습니다. "
        "기존 JustVoca vocab.py 내용을 vocab_source.py로 복사하세요."
    )

def get_vocab_cache(force_reload: bool = False) -> Any:
    global _VOCAB_CACHE
    if force_reload or _VOCAB_CACHE is None:
        if load_vocab_data is None:
            _VOCAB_CACHE = _fallback_load_vocab()
        else:
            _VOCAB_CACHE = load_vocab_data()
    return _VOCAB_CACHE

def _extract_topic_map(data: Any) -> Dict[str, List[Any]]:
    if isinstance(data, dict):
        if all(isinstance(v, list) for v in data.values()):
            return {str(k): v for k, v in data.items()}

        if "topics" in data and isinstance(data["topics"], dict):
            topics = data["topics"]
            if all(isinstance(v, list) for v in topics.values()):
                return {str(k): v for k, v in topics.items()}

        for k in ("levels", "level", "data"):
            if k in data and isinstance(data[k], dict):
                inner = data[k]
                if all(isinstance(v, list) for v in inner.values()):
                    return {str(tk): tv for tk, tv in inner.items()}

    if isinstance(data, list):
        return {"default": data}

    return {}

def list_topics() -> List[str]:
    data = get_vocab_cache()
    m = _extract_topic_map(data)
    return sorted(m.keys())

def get_topic_words(topic_key: str) -> List[Any]:
    data = get_vocab_cache()
    m = _extract_topic_map(data)
    return m.get(topic_key, [])

def word_key(w: Any) -> str:
    if isinstance(w, dict):
        return str(
            w.get("word")
            or w.get("voca")
            or w.get("term")
            or w.get("id")
            or w.get("key")
            or ""
        ).strip()
    return str(w).strip()

def normalize_topic_queue(topic_key: str, shuffle: bool = True) -> List[str]:
    import random
    words = get_topic_words(topic_key)
    keys = [word_key(w) for w in words if word_key(w)]
    if shuffle:
        random.shuffle(keys)
    return keys

def find_word_obj(topic_key: str, key: str) -> Any:
    words = get_topic_words(topic_key)
    for w in words:
        if word_key(w) == key:
            return w
    return {"word": key}
