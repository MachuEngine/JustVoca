# src/storage.py
from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from src.constants import SYSTEM_FILE, USERS_FILE, HISTORY_FILE, DEFAULT_SYSTEM
from src.utils import atomic_write_json, log_write, hash_password, verify_password

def load_system() -> Dict[str, Any]:
    try:
        if not SYSTEM_FILE.exists():
            save_system(DEFAULT_SYSTEM)
            return dict(DEFAULT_SYSTEM)
        with SYSTEM_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f) or {}
        for k, v in DEFAULT_SYSTEM.items():
            if k not in data: data[k] = v
        return data
    except Exception as e:
        log_write(f"load_system error: {e}")
        return dict(DEFAULT_SYSTEM)

def save_system(sysdata: Dict[str, Any]) -> None:
    try:
        SYSTEM_FILE.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(SYSTEM_FILE, sysdata)
    except Exception as e:
        log_write(f"save_system error: {e}")

def update_user_approval(uid: str, approved: bool) -> bool:
    try:
        users = load_users()
        if uid in users:
            users[uid]["is_approved"] = approved
            save_users(users)
            return True
        return False
    except Exception as e:
        log_write(f"update_user_approval error: {e}")
        return False

def _default_users() -> Dict[str, Any]:
    return {
        "admin": {"pw": "1111", "name": "관리자", "role": "admin", "country": "KR", "is_approved": True, "progress": {}},
        "teacher": {"pw": hash_password("1111"), "name": "선생님", "role": "teacher", "country": "KR", "is_approved": True, "progress": {}},
        "student": {"pw": hash_password("1111"), "name": "학습자", "role": "student", "country": "KR", "is_approved": True, "progress": {}},
    }

def load_users() -> Dict[str, Any]:
    try:
        if not USERS_FILE.exists():
            users = _default_users()
            save_users(users)
            return users
        with USERS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f) or {}
        
        changed = False
        for uid, u in data.items():
            if not isinstance(u, dict): continue
            u["uid"] = uid
            u["id"] = uid
            
            if "role" not in u: u["role"] = "student"; changed = True
            if "country" not in u: u["country"] = "KR"; changed = True
            
            # [승인 로직] 선생님만 기본 False
            if "is_approved" not in u:
                u["is_approved"] = False if u["role"] == "teacher" else True
                changed = True
            
            if "progress" not in u:
                u["progress"] = {"settings": {"goal": 10, "ui_lang": "ko"}, "topics": {}}
                changed = True
            elif "settings" not in u["progress"]:
                u["progress"]["settings"] = {"goal": 10, "ui_lang": "ko"}
                changed = True
            
            # 비밀번호 해시 업그레이드 (기존 pw_hash가 있으면 적용)
            if "pw" not in u:
                if "pw_hash" in u:
                    u["pw"] = u["pw_hash"]
                else:
                    u["pw"] = hash_password("1111")
                changed = True

        if changed: save_users(data)
        return data
    except Exception as e:
        log_write(f"load_users error: {e}")
        return {}

def save_users(users_data: Dict[str, Any]) -> None:
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(USERS_FILE, users_data)
    except Exception as e: log_write(f"save_users error: {e}")

def register_user(uid, pw, name, email, phone, country, role, phone_verified):
    users = load_users()
    is_approved = False if role == "teacher" else True
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
        "progress": {}
    }
    save_users(users)
    return True, "회원가입이 완료되었습니다."

def authenticate_user(uid: str, pw: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """통합 인증 함수: 평문 비번과 해시 비번 모두 지원 (중복 제거됨)"""
    try:
        users = load_users()
        u = users.get(uid.strip())
        if not u: return False, None
        
        stored = u.get("pw", "")
        # 1. 평문 체크 (admin 등)
        if stored == pw: return True, u
        # 2. 해시 체크
        ok, _ = verify_password(stored, pw)
        if ok: return True, u
    except Exception as e:
        log_write(f"auth error: {e}")
        pass
    return False, None

def get_user(uid: str) -> Optional[Dict[str, Any]]:
    return load_users().get(uid)

def update_user(uid: str, new_user_obj: Dict[str, Any]) -> None:
    users = load_users()
    users[uid] = new_user_obj
    save_users(users)