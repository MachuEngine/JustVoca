import hashlib
from typing import Tuple, Optional, Dict, Any
from fastapi import Request, HTTPException, status
from app.core.config import settings

# [변경 완료] JSON 파일 로드/저장 함수(load_users, save_users 등) 삭제됨
# 이제 모든 데이터 관리는 SQL DB(app.api.*)에서 직접 수행합니다.

# --- 세션/인증 헬퍼 함수 ---

def verify_session(token: str) -> Optional[Dict[str, Any]]:
    """
    세션 토큰 유효성 검사.
    현재는 토큰 문자열 자체가 uid인 단순 구조를 가정합니다.
    (JWT 도입 시 이곳에서 token decode 로직을 수행하면 됩니다.)
    
    Returns:
        세션 데이터 딕셔너리 (예: {"uid": "student"}) 또는 None
    """
    if not token:
        return None
    
    # 토큰이 존재하면 유효한 세션으로 간주하고 uid 반환
    return {"uid": token}

def hash_password(password: str) -> str:
    """비밀번호 해싱 (SHA-256)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_pw: str, input_pw: str) -> Tuple[bool, bool]:
    """
    저장된 비밀번호(stored_pw)와 입력된 비밀번호(input_pw)를 비교합니다.
    
    Returns:
        (일치 여부, 해시 업데이트 필요 여부)
    """
    # 1. 평문 비교 (기존 데이터 호환용: 예 - 초기 admin 계정 "1111")
    if stored_pw == input_pw:
        return True, True # 일치하지만, 보안을 위해 해시로 업데이트 권장
        
    # 2. 해시 비교 (정상적인 경우)
    if stored_pw == hash_password(input_pw):
        return True, False # 일치하고 해시 상태도 최신임
        
    return False, False