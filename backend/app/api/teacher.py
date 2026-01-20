from fastapi import APIRouter, HTTPException, Request, Body, Depends
from sqlmodel import Session, select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# [중요] DB 설정 임포트 (get_db 아님)
from app.core.database import get_session
# [중요] DB 모델 임포트
from app.models import User, StudyProgress, StudyLog, Notice
from app.core.config import settings
from app.core.session import verify_session, hash_password

router = APIRouter(prefix="/api/teacher", tags=["teacher"])

# --- [1. 권한 체크 함수 (DB 기반)] ---
def _require_teacher(request: Request, session: Session) -> User:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
    sess = verify_session(token)
    if not sess:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
    
    uid = sess["uid"]
    
    # [수정] JSON 파일 대신 DB에서 유저 확인
    user = session.get(User, uid)
    
    if not user:
        raise HTTPException(status_code=401, detail="사용자 정보를 찾을 수 없습니다.")
    if user.role != "teacher" and user.role != "admin": # 관리자도 허용
        raise HTTPException(status_code=403, detail="교사 권한이 필요합니다.")
        
    return user

# --- [2. 학생 목록 조회] ---
@router.get("/students")
def list_students(request: Request, session: Session = Depends(get_session)):
    # 권한 체크
    _require_teacher(request, session)

    # 1. 학생 역할인 유저만 DB에서 조회
    statement = select(User).where(User.role == "student")
    students = session.exec(statement).all()

    items = []
    for student in students:
        # 2. 진도 정보 조회 (StudyProgress)
        prog_stmt = select(StudyProgress).where(StudyProgress.user_id == student.uid)
        prog = session.exec(prog_stmt).first()
        
        # 3. 평균 점수 계산 (StudyLog)
        # SQL: SELECT AVG(score) FROM studylog WHERE user_id = ...
        avg_score_val = session.exec(
            select(func.avg(StudyLog.score)).where(StudyLog.user_id == student.uid)
        ).first()
        avg_score = avg_score_val if avg_score_val else 0.0

        # 목표 설정 가져오기 (JSON 필드 파싱)
        settings_data = student.progress.get("settings", {}) if student.progress else {}
        goal = int(settings_data.get("goal", 10))

        items.append({
            "uid": student.uid,
            "name": student.name,
            "country": student.country or "KR",
            "current_level": prog.level if prog else "미시작",
            "current_page": prog.current_page if prog else 1,
            "avg_score": round(float(avg_score), 1),
            "goal": goal,
            # 진도율 계산 (단순 페이지 기준 예시)
            "progress_rate": min(1.0, (prog.current_page * 10) / 100) if prog else 0.0,
        })

    return {"ok": True, "items": items}

# --- [3. 학생 상세 조회] ---
@router.get("/students/{student_uid}")
def get_student(student_uid: str, request: Request, session: Session = Depends(get_session)):
    _require_teacher(request, session)
    
    # DB에서 학생 조회
    student = session.get(User, student_uid)
    if not student or student.role != "student":
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")

    # 최근 학습 로그 20개
    log_stmt = select(StudyLog).where(StudyLog.user_id == student_uid).order_by(StudyLog.created_at.desc()).limit(20)
    logs = session.exec(log_stmt).all()
    
    # 진도 상세 정보
    prog_stmt = select(StudyProgress).where(StudyProgress.user_id == student_uid)
    progs = session.exec(prog_stmt).all()
    prog_list = [{"level": p.level, "page": p.current_page} for p in progs]

    return {
        "ok": True,
        "student": {
            "uid": student.uid,
            "name": student.name,
            "email": student.email or "",
            "phone": student.phone or "",
            "country": student.country or "KR",
            "db_progress": prog_list,
            "recent_logs": logs
        }
    }

# --- [4. 비밀번호 초기화] ---
class ResetPwIn(BaseModel):
    new_password: str = "1111"

@router.post("/students/{student_uid}/reset-password")
def reset_student_password(student_uid: str, payload: ResetPwIn, request: Request, session: Session = Depends(get_session)):
    _require_teacher(request, session)
    
    student = session.get(User, student_uid)
    if not student or student.role != "student":
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")

    # DB 업데이트 (update_user 함수 제거 -> session 사용)
    # 실제로는 해시 함수 사용 권장: student.pw = hash_password(payload.new_password)
    student.pw = payload.new_password 
    session.add(student)
    session.commit()
    session.refresh(student)
    
    return {"ok": True, "uid": student_uid, "new_password": payload.new_password}

# --- [5. 공지사항 전송 (DB 저장)] ---
class NoticeCreate(BaseModel):
    title: str
    content: str
    author: str
    scheduled_at: Optional[datetime] = None

@router.post("/notice")
async def send_notice(
    notice_in: NoticeCreate, 
    request: Request, 
    session: Session = Depends(get_session)
):
    # 선생님 확인
    teacher = _require_teacher(request, session)
    
    # DB에 공지사항 저장 (add_notice 서비스 제거 -> 직접 DB 저장)
    new_notice = Notice(
        title=notice_in.title,
        content=notice_in.content,
        author=teacher.name, # 현재 로그인한 선생님 이름 사용
        scheduled_at=notice_in.scheduled_at
    )
    session.add(new_notice)
    session.commit()
    
    return {"status": "ok", "message": "공지사항이 등록되었습니다."}