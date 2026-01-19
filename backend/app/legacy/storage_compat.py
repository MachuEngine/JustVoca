from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from app.core.config import USERS_FILE
from app.legacy.utils_compat import atomic_write_json, hash_password, verify_password


def _default_users() -> Dict[str, Any]:
    # Flet 기본 유저: admin은 평문 "1111" :contentReference[oaicite:9]{index=9}
    return {
        "admin": {"pw": "1111", "name": "관리자", "role": "admin", "country": "KR", "is_approved": True, "progress": {}},
        "teacher": {"pw": hash_password("1111"), "name": "선생님", "role": "teacher", "country": "KR", "is_approved": True, "progress": {}},
        "student": {"pw": hash_password("1111"), "name": "학습자", "role": "student", "country": "KR", "is_approved": True, "progress": {}},
    }


def load_users() -> Dict[str, Any]:
    if not USERS_FILE.exists():
        users = _default_users()
        save_users(users)
        return users

    with USERS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f) or {}

    changed = False
    for uid, u in data.items():
        if not isinstance(u, dict):
            continue
        u["uid"] = uid
        u["id"] = uid

        if "role" not in u:
            u["role"] = "student"
            changed = True
        if "country" not in u:
            u["country"] = "KR"
            changed = True

        # teacher만 기본 승인 False :contentReference[oaicite:10]{index=10}
        if "is_approved" not in u:
            u["is_approved"] = False if u["role"] == "teacher" else True
            changed = True

        if "progress" not in u:
            u["progress"] = {"settings": {"goal": 10, "ui_lang": "ko"}, "topics": {}}
            changed = True
        elif "settings" not in u["progress"]:
            u["progress"]["settings"] = {"goal": 10, "ui_lang": "ko"}
            changed = True

        # pw 없으면 pw_hash 있으면 승계, 없으면 1111 해시 :contentReference[oaicite:11]{index=11}
        if "pw" not in u:
            if "pw_hash" in u:
                u["pw"] = u["pw_hash"]
            else:
                u["pw"] = hash_password("1111")
            changed = True

    if changed:
        save_users(data)
    return data


def save_users(users_data: Dict[str, Any]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(str(USERS_FILE), users_data)


def register_user(uid: str, pw: str, name: str, email: str, phone: str, country: str, role: str, phone_verified: bool):
    users = load_users()
    if uid in users:
        return False, "이미 존재하는 아이디입니다."

    is_approved = False if role == "teacher" else True  # :contentReference[oaicite:12]{index=12}
    users[uid] = {
        "uid": uid,
        "pw": hash_password(pw),
        "name": name,
        "email": email,
        "phone": phone,
        "country": country,
        "role": role,
        "is_approved": is_approved,
        "phone_verified": phone_verified,
        "created_at": datetime.now().isoformat(),
        "progress": {},
    }
    save_users(users)
    return True, "회원가입이 완료되었습니다."


def authenticate_user(uid: str, pw: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    users = load_users()
    u = users.get(uid.strip())
    if not u:
        return False, None

    stored = u.get("pw", "")
    # 1) 평문 체크(admin 등) :contentReference[oaicite:13]{index=13}
    if stored == pw:
        return True, u

    # 2) 해시 체크
    ok, _need_upgrade = verify_password(stored, pw)
    if ok:
        return True, u

    return False, None


def update_user(uid: str, new_user_obj: Dict[str, Any]) -> None:
    users = load_users()
    users[uid] = new_user_obj
    save_users(users)


def update_user_approval(uid: str, approved: bool) -> bool:
    users = load_users()
    if uid in users:
        users[uid]["is_approved"] = approved
        save_users(users)
        return True
    return False
