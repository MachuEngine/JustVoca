# src/storage.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple, Optional

from src.constants import SYSTEM_FILE, USERS_FILE, HISTORY_FILE, DEFAULT_SYSTEM
from src.utils import atomic_write_json, log_write, hash_password, verify_password


# =============================================================================
# System
# =============================================================================
def load_system() -> Dict[str, Any]:
    """
    system.json 로드 + DEFAULT_SYSTEM 기준 보정
    """
    try:
        if not SYSTEM_FILE.exists():
            save_system(DEFAULT_SYSTEM)
            return dict(DEFAULT_SYSTEM)

        with SYSTEM_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f) or {}

        # 상위 키 보정
        for k, v in DEFAULT_SYSTEM.items():
            if k not in data:
                data[k] = v

        # "api" 서브키 보정
        if "api" not in data or not isinstance(data["api"], dict):
            data["api"] = dict(DEFAULT_SYSTEM.get("api", {}))

        for k, v in (DEFAULT_SYSTEM.get("api", {}) or {}).items():
            if k not in data["api"]:
                data["api"][k] = v

        save_system(data)
        return data

    except Exception as e:
        log_write(f"load_system error: {e}")
        save_system(DEFAULT_SYSTEM)
        return dict(DEFAULT_SYSTEM)


def save_system(sysdata: Dict[str, Any]) -> None:
    try:
        SYSTEM_FILE.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(SYSTEM_FILE, sysdata)
    except Exception as e:
        log_write(f"save_system error: {e}")


# =============================================================================
# Users
# =============================================================================
def _default_users() -> Dict[str, Any]:
    """
    기본 계정 (비번은 해시로 저장)
    """
    return {
        "admin": {
            "pw": hash_password("1111"),
            "name": "관리자",
            "role": "admin",
            "country": "KR",
            "email": "",
            "phone": "",
            "phone_verified": False,
            "progress": {},
        },
        "teacher": {
            "pw": hash_password("1111"),
            "name": "선생님",
            "role": "teacher",
            "country": "KR",
            "email": "",
            "phone": "",
            "phone_verified": False,
            "progress": {},
        },
        "student": {
            "pw": hash_password("1111"),
            "name": "학습자",
            "role": "student",
            "country": "KR",
            "email": "",
            "phone": "",
            "phone_verified": False,
            "progress": {},
        },
    }


def load_users() -> Dict[str, Any]:
    """
    users.json 로드 + 필드 보정 + 필요 시 해시 업그레이드
    """
    try:
        if not USERS_FILE.exists():
            users = _default_users()
            save_users(users)
            return users

        with USERS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f) or {}

        changed = False

        # 보정
        for uid, u in data.items():
            if not isinstance(u, dict):
                data[uid] = {}
                u = data[uid]
                changed = True

            if "progress" not in u or not isinstance(u["progress"], dict):
                u["progress"] = {}
                changed = True
            if "country" not in u:
                u["country"] = "KR"
                changed = True

            # 비밀번호 필드 통일: "pw"
            # (예전 필드가 있을 수 있어 보정)
            if "pw" not in u:
                # 혹시 pw_hash 같은 게 들어있으면 흡수
                if "pw_hash" in u and u["pw_hash"]:
                    u["pw"] = u["pw_hash"]
                else:
                    u["pw"] = hash_password("1111")
                changed = True

            # 사양 반영 필드 보정
            if "email" not in u:
                u["email"] = ""
                changed = True
            if "phone" not in u:
                u["phone"] = ""
                changed = True
            if "phone_verified" not in u:
                u["phone_verified"] = False
                changed = True
            if "role" not in u:
                u["role"] = "student"
                changed = True
            if "name" not in u:
                u["name"] = uid
                changed = True

            # verify_password가 legacy(평문) -> hash 업그레이드를 지원하는 설계라면
            # load 시점에 강제 업그레이드는 하지 않고, authenticate 시 업그레이드하는 게 안전함.
            # (여기서는 값만 통일)

        if changed:
            save_users(data)

        return data

    except Exception as e:
        log_write(f"load_users error: {e}")
        return {}


def save_users(users_data: Dict[str, Any]) -> None:
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(USERS_FILE, users_data)
    except Exception as e:
        log_write(f"save_users error: {e}")


def register_user(
    uid: str,
    pw: str,
    name: str,
    email: str = "",
    phone: str = "",
    country: str = "KR",
    role: str = "student",
    phone_verified: bool = False,
) -> Tuple[bool, str]:
    users = load_users()
    uid = (uid or "").strip()

    if not uid:
        return False, "아이디를 입력해주세요."
    if uid in users:
        return False, "이미 존재하는 아이디입니다."
    if not (pw or "").strip():
        return False, "비밀번호를 입력해주세요."
    if not (name or "").strip():
        return False, "이름을 입력해주세요."

    users[uid] = {
        "pw": hash_password(pw),
        "name": name.strip(),
        "email": (email or "").strip(),
        "phone": (phone or "").strip(),
        "phone_verified": bool(phone_verified),
        "role": role,
        "country": country,
        "progress": {},
    }
    save_users(users)
    return True, "회원가입 완료! 로그인해주세요."


def authenticate_user(uid: str, pw: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    return (ok: bool, user: dict|None)
    - pw는 입력 비밀번호
    - 저장 비밀번호는 users[uid]["pw"] (hash 또는 legacy 평문일 수 있음)
    - verify_password는 (stored, input) -> (ok, needs_upgrade) 형태를 기대
    """
    users = load_users()
    uid = (uid or "").strip()
    if not uid or uid not in users:
        return False, None

    u = users[uid]
    stored = u.get("pw", "")

    try:
        ok, needs_upgrade = verify_password(stored, pw)
    except Exception as e:
        log_write(f"verify_password error: {e}")
        return False, None

    if not ok:
        return False, None

    # legacy plain-text -> hash upgrade
    if needs_upgrade:
        u["pw"] = hash_password(pw)
        users[uid] = u
        save_users(users)

    # 사용자 dict 보정 + id 주입
    u["id"] = uid
    if "progress" not in u or not isinstance(u["progress"], dict):
        u["progress"] = {}
    if "country" not in u:
        u["country"] = "KR"

    # 로그인 성공 시 보정값 저장(선택: 상태 유지 목적)
    users[uid] = u
    save_users(users)

    return True, u


def get_user(uid: str) -> Optional[Dict[str, Any]]:
    users = load_users()
    return users.get(uid)


def update_user(uid: str, new_user_obj: Dict[str, Any]) -> None:
    users = load_users()
    users[uid] = new_user_obj
    save_users(users)


# =============================================================================
# History
# =============================================================================
def load_history() -> List[Any]:
    """
    history.json 로드 (없으면 빈 리스트 반환)
    """
    try:
        if not HISTORY_FILE.exists():
            return []
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        log_write(f"load_history error: {e}")
        return []


def save_history(history_data: List[Any]) -> None:
    """
    history.json 저장
    """
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(HISTORY_FILE, history_data)
    except Exception as e:
        log_write(f"save_history error: {e}")


# =============================================================================
# Progress (user object 보정)
# =============================================================================
def ensure_progress(user: Dict[str, Any]) -> Dict[str, Any]:
    if "progress" not in user or not isinstance(user["progress"], dict):
        user["progress"] = {}

    if "settings" not in user["progress"] or not isinstance(user["progress"]["settings"], dict):
        user["progress"]["settings"] = {}

    if "goal" not in user["progress"]["settings"]:
        sysdata = load_system()
        user["progress"]["settings"]["goal"] = int(sysdata.get("default_goal", 10))

    if "ui_lang" not in user["progress"]["settings"]:
        user["progress"]["settings"]["ui_lang"] = "ko"

    if "topics" not in user["progress"] or not isinstance(user["progress"]["topics"], dict):
        user["progress"]["topics"] = {}

    # 마지막 학습 자리 기억(토픽/인덱스)
    if "last_session" not in user["progress"] or not isinstance(user["progress"]["last_session"], dict):
        user["progress"]["last_session"] = {"topic": "", "idx": 0}
    else:
        user["progress"]["last_session"].setdefault("topic", "")
        user["progress"]["last_session"].setdefault("idx", 0)

    # 격려 화면(하루 1회) 플래그
    if "today_flags" not in user["progress"] or not isinstance(user["progress"]["today_flags"], dict):
        user["progress"]["today_flags"] = {}
    user["progress"]["today_flags"].setdefault("motivate_shown_date", "")  # "YYYY-MM-DD"

    return user
