import json
import os
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# FastAPI 관련 임포트 (verify_session을 위해 필수)
from fastapi import Request, HTTPException, status

# 설정 파일 가져오기
from app.core.config import settings

# --- 데이터 파일 경로 설정 ---
# config.py에 정의된 경로를 우선 사용합니다.
USERS_FILE = os.path.join(settings.DATA_DIR, "users.json")
NOTICES_FILE = os.path.join(settings.DATA_DIR, "notices.json")
SYSTEM_FILE = os.path.join(settings.DATA_DIR, "system.json")

# 데이터 디렉토리가 없으면 생성
os.makedirs(settings.DATA_DIR, exist_ok=True)


# --- [핵심 추가] 세션 검증 함수 (에러 해결용) ---
def verify_session(request: Request) -> str:
    """
    사용자의 요청(Request) 쿠키에서 세션 토큰이 있는지 확인합니다.
    teacher.py 등 관리자 기능에서 이 함수를 호출하여 로그인을 체크합니다.
    """
    # 쿠키에서 토큰 가져오기 (config.py에 설정된 이름 사용)
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다. (세션 만료 또는 미로그인)"
        )
    
    # 여기서 추가로 토큰 유효성을 검사할 수 있습니다 (예: 사용자 목록에 있는지 확인)
    # users = load_users()
    # if token not in users: raise HTTPException(...)
    
    return token


# --- 헬퍼 함수 (JSON 입출력) ---
def _load_json(path: str, default: Any = None) -> Any:
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def _save_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_pw: str, input_pw: str) -> Tuple[bool, bool]:
    # 기존 평문 비밀번호 호환 지원
    if stored_pw == input_pw:
        return True, False # (일치함, 해시 필요함)
    if stored_pw == hash_password(input_pw):
        return True, True  # (일치함, 이미 해시됨)
    return False, False


# --- 사용자 관리 ---
def load_users() -> Dict[str, Any]:
    return _load_json(USERS_FILE, {})

def save_users(users: Dict[str, Any]):
    _save_json(USERS_FILE, users)

def get_user_progress(user_id: str):
    users = load_users()
    return users.get(user_id, {}).get("progress", {})

def update_user_progress(user_id: str, topic: str, word: str, score: int, status: str = "learned"):
    users = load_users()
    if user_id not in users: return
    
    # 구조 초기화
    prog = users[user_id].setdefault("progress", {})
    topics = prog.setdefault("topics", {})
    t_data = topics.setdefault(topic, {"learned": {}, "wrong_notes": [], "stats": {}})
    
    # 단어 학습 상태 업데이트
    t_data["learned"][word] = {"score": score, "status": status, "date": datetime.now().isoformat()}
    
    # 평균 점수 재계산
    scores = [v["score"] for v in t_data["learned"].values()]
    t_data["stats"]["avg_score"] = sum(scores) // len(scores) if scores else 0
    
    save_users(users)

def add_wrong_note(user_id: str, topic: str, question: str, answer: str, wrong_answer: str):
    users = load_users()
    if user_id not in users: return
    
    prog = users[user_id].setdefault("progress", {})
    t_data = prog.setdefault("topics", {}).setdefault(topic, {"learned": {}, "wrong_notes": [], "stats": {}})
    
    # 오답 노트 추가
    t_data["wrong_notes"].append({
        "question": question,
        "answer": answer,
        "wrong_answer": wrong_answer,
        "date": datetime.now().isoformat()
    })
    save_users(users)


# --- 공지사항 및 시스템 ---
def load_notices() -> List[Dict[str, Any]]:
    return _load_json(NOTICES_FILE, [])

def add_notice(title: str, content: str, author: str, scheduled_at: str = None):
    notices = load_notices()
    # ID 생성 로직 (기존 개수 + 1)
    new_id = str(len(notices) + 1)
    
    new_notice = {
        "id": new_id,
        "title": title,
        "content": content,
        "author": author,
        "created_at": datetime.now().isoformat(),
        "scheduled_at": scheduled_at or datetime.now().isoformat()
    }
    
    notices.append(new_notice)
    _save_json(NOTICES_FILE, notices)
    return new_notice # 생성된 공지사항 반환

def load_system() -> Dict[str, Any]:
    return _load_json(SYSTEM_FILE, {"default_goal": 10})

def save_system(data: Dict[str, Any]):
    _save_json(SYSTEM_FILE, data)