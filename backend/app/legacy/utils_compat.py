from __future__ import annotations

import json
import os
import tempfile
import hashlib
import secrets
from typing import Tuple


def atomic_write_json(path: str, data):
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


_PBKDF2_ITER = 100_000


def hash_password(pw: str, salt: bytes | None = None) -> str:
    if not salt:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", (pw or "").encode("utf-8"), salt, _PBKDF2_ITER)
    return f"pbkdf2${_PBKDF2_ITER}${salt.hex()}${dk.hex()}"


def verify_password(stored: str, pw: str) -> Tuple[bool, bool]:
    if not stored:
        return False, False

    # 구형 평문 비번 호환 (admin 등) :contentReference[oaicite:6]{index=6}
    if not stored.startswith("pbkdf2$"):
        return (stored == pw), True

    try:
        _, it_s, salt_hex, hash_hex = stored.split("$", 3)
        it = int(it_s)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", (pw or "").encode("utf-8"), salt, it)
        return (dk.hex() == hash_hex), False
    except Exception:
        return False, False
