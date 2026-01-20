from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

# [추가] DB 및 모델 관련 임포트
from sqlmodel import Session, select
from app.core.database import create_db_and_tables, engine
from app.models import User

# 라우터 임포트
from app.api import auth, study, user, teacher, admin, speech 
from app.core.config import settings

# --- [핵심] 기본 계정 3개 자동 생성 함수 ---
def create_default_users():
    with Session(engine) as session:
        print("[INFO] 기본 계정 점검 중...")
        
        # 1. Admin (관리자)
        if not session.get(User, "admin"):
            print(" -> 'admin' 계정 생성됨")
            # 비밀번호는 실제 서비스에선 해싱 권장 (현재는 테스트용 1111)
            session.add(User(
                uid="admin", name="총괄 관리자", pw="1111", role="admin",
                progress={"settings": {"goal": 10, "review_wrong": True}}
            ))
        
        # 2. Teacher (선생님)
        if not session.get(User, "teacher"):
            print(" -> 'teacher' 계정 생성됨")
            session.add(User(
                uid="teacher", name="김선생님", pw="1111", role="teacher",
                progress={"settings": {"goal": 10, "review_wrong": True}}
            ))
            
        # 3. Student (학생)
        if not session.get(User, "student"):
            print(" -> 'student' 계정 생성됨")
            session.add(User(
                uid="student", name="학생1", pw="1111", role="student",
                progress={"settings": {"goal": 10, "review_wrong": True}}
            ))
            
        session.commit()

# 수명 주기(Lifespan) 설정: 서버 시작 시 실행될 작업들
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. DB 테이블 생성 (database.db 파일이 없으면 생성)
    create_db_and_tables()
    # 2. 기본 계정 3개 확인 및 생성
    create_default_users()
    yield

# [수정] lifespan과 title 설정을 한 번에 적용 (중복 선언 제거)
app = FastAPI(title="JustVoca API", lifespan=lifespan)

# 1. CORS 설정 (프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 서버 상태 확인용 루트 경로
@app.get("/")
async def root():
    return {"status": "ok", "message": "JustVoca Backend is running!"}

# 3. 라우터 등록
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(study.router, prefix="/study", tags=["Study"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(teacher.router, prefix="/api/teacher", tags=["Teacher"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(speech.router, prefix="/speech", tags=["Speech"]) 

# 4. 정적 파일 설정 (녹음 파일 등 저장소)
os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.TEMP_UPLOAD_DIR), name="files")

# 5. 서버 시작 시 경로 출력 (보조용)
@app.on_event("startup")
async def startup_event():
    print("✅ 서버가 시작되었습니다. 사용 가능한 경로 목록:")
    for route in app.routes:
        print(f"🔗 {route.path}")