from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Body, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.session import verify_session
from app.legacy.storage_compat import load_users, update_user
from app.legacy.utils_compat import hash_password
from app.services.notice_service import add_notice

from sqlalchemy import func, cast, Date

# DB 연동을 위한 임포트 추가
from app.core.database import get_db
from app.models import StudyProgress, StudyLog

router = APIRouter(prefix="/api/teacher", tags=["teacher"])

def _require_teacher(request: Request) -> str:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    sess = verify_session(token) if token else None
    if not sess:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    uid = sess["uid"]
    users = load_users()
    u = users.get(uid)
    if not u:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
    if u.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="교사 권한이 필요합니다.")
    if not u.get("is_approved", False):
        raise HTTPException(status_code=403, detail="승인 후 이용할 수 있습니다.")
    return uid

@router.get("/students")
def list_students(request: Request, db: Session = Depends(get_db)):
    _require_teacher(request)
    users = load_users()

    items = []
    for uid, u in users.items():
        if not isinstance(u, dict) or u.get("role") != "student":
            continue

        # [개선] 새 DB에서 이 학생의 실시간 진도 및 평균 점수 가져오기
        # 1. 현재 진행중인 레벨과 페이지 확인
        prog = db.query(StudyProgress).filter(StudyProgress.user_id == uid).first()
        
        # 2. 전체 발음 평가 평균 점수 계산
        avg_score = db.query(func.avg(StudyLog.score)).filter(StudyLog.user_id == uid).scalar() or 0.0

        # 레거시 데이터 유지
        legacy_prog = (u.get("progress") or {})
        legacy_settings = (legacy_prog.get("settings") or {})
        goal = int(legacy_settings.get("goal", 10) or 10)

        items.append({
            "uid": uid,
            "name": u.get("name", ""),
            "country": u.get("country", "KR"),
            "current_level": prog.level if prog else "미시작",
            "current_page": prog.current_page if prog else 1,
            "avg_score": round(float(avg_score), 1),
            "goal": goal,
            "progress_rate": min(1.0, (prog.current_page * 10) / goal) if prog and goal > 0 else 0.0,
        })

    return {"ok": True, "items": items}

@router.get("/students/{student_uid}")
def get_student(student_uid: str, request: Request, db: Session = Depends(get_db)):
    _require_teacher(request)
    users = load_users()
    u = users.get(student_uid)
    if not u or u.get("role") != "student":
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")

    # [개선] 이 학생의 상세 학습 로그(최근 20개) 함께 반환
    logs = db.query(StudyLog).filter(StudyLog.user_id == student_uid).order_by(StudyLog.created_at.desc()).limit(20).all()
    
    # DB 진도 정보
    prog_db = db.query(StudyProgress).filter(StudyProgress.user_id == student_uid).all()
    prog_list = [{"level": p.level, "page": p.current_page} for p in prog_db]

    return {
        "ok": True,
        "student": {
            "uid": student_uid,
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "phone": u.get("phone", ""),
            "country": u.get("country", "KR"),
            "legacy_progress": u.get("progress") or {}, # 기존 데이터 보존
            "db_progress": prog_list,
            "recent_logs": logs
        }
    }

class ResetPwIn(BaseModel):
    new_password: str = "1111"

@router.post("/students/{student_uid}/reset-password")
def reset_student_password(student_uid: str, payload: ResetPwIn, request: Request):
    _require_teacher(request)
    users = load_users()
    u = users.get(student_uid)
    if not u or u.get("role") != "student":
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")

    u["pw"] = hash_password(payload.new_password)
    update_user(student_uid, u)
    return {"ok": True, "uid": student_uid, "new_password": payload.new_password}

@router.post("/notice")
async def send_notice(title: str = Body(...), content: str = Body(...), author: str = Body(...), scheduled_at: str = Body(None)):
    add_notice(title, content, author, scheduled_at)
    return {"status": "ok"}