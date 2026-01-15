import os, json, tempfile, hashlib, secrets
from datetime import datetime

from src.constants import LOG_FILE

# =============================================================================
def log_write(msg: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass


def atomic_write_json(path: str, data):
    """
    JSON 저장 시 파일 깨짐 방지:
    임시파일에 먼저 쓰고 os.replace로 교체(원자적)
    """
    try:
        d = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(d, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=d)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except:
                pass
    except Exception as e:
        log_write(f"atomic_write_json error({path}): {e}")


# ---- password hashing (PBKDF2) ----
_PBKDF2_ITER = 120_000

def hash_password(pw: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", (pw or "").encode("utf-8"), salt, _PBKDF2_ITER)
    return f"pbkdf2${_PBKDF2_ITER}${salt.hex()}${dk.hex()}"


def verify_password(stored: str, pw: str) -> tuple[bool, bool]:
    """
    return (ok, needs_upgrade)
    - needs_upgrade: stored가 평문이어서 로그인 성공 후 해시로 바꿔야 하는 경우
    """
    stored = stored or ""
    pw = pw or ""
    if stored.startswith("pbkdf2$"):
        try:
            _, it_s, salt_hex, hash_hex = stored.split("$", 3)
            it = int(it_s)
            salt = bytes.fromhex(salt_hex)
            dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, it)
            ok = (dk.hex() == hash_hex)
            return ok, False
        except:
            return False, False
    else:
        # legacy plain-text
        return stored == pw, True


