from __future__ import annotations

from datetime import datetime

from src.constants import COUNTRY_OPTIONS

def ensure_progress(user: dict) -> dict:
    """
    user dict에 progress 기본 구조를 보장
    """
    if user is None:
        user = {}
    if "progress" not in user or not isinstance(user["progress"], dict):
        user["progress"] = {}
    if "topics" not in user["progress"] or not isinstance(user["progress"]["topics"], dict):
        user["progress"]["topics"] = {}
    return user


def ensure_topic_progress(user, topic):
    user = ensure_progress(user)
    topics = user["progress"]["topics"]
    if topic not in topics:
        topics[topic] = {
            "learned": {},
            "stats": {"studied_count": 0, "avg_score": 0.0},
            "wrong_notes": [],
        }
    return user


def update_learned_word(user, topic, word_item, score):
    user = ensure_topic_progress(user, topic)
    t = user["progress"]["topics"][topic]
    learned = t["learned"]

    w = word_item["word"]
    learned[w] = {
        "mean": word_item.get("mean", ""),
        "last_score": int(score),
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    scores = [v.get("last_score", 0) for v in learned.values()]
    t["stats"]["studied_count"] = len(learned)
    t["stats"]["avg_score"] = round(sum(scores) / max(1, len(scores)), 2)
    return user


def update_last_seen_only(user, topic, word_item):
    """이미 learned에 있는 단어도 last_seen은 갱신(점수는 유지)."""
    user = ensure_topic_progress(user, topic)
    t = user["progress"]["topics"][topic]
    learned = t["learned"]
    w = word_item.get("word", "")
    if not w:
        return user
    if w in learned:
        learned[w]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return user


def add_wrong_note(user, topic, q, correct, user_answer):
    user = ensure_topic_progress(user, topic)
    t = user["progress"]["topics"][topic]
    t["wrong_notes"].append(
        {
            "q": q,
            "a": correct,
            "user": user_answer,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return user


def country_label(code: str) -> str:
    mp = {c: n for c, n in COUNTRY_OPTIONS}
    return mp.get(code or "", code or "KR")


