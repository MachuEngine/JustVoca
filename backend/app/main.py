# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from sqlmodel import Session, select
from app.core.database import create_db_and_tables, engine
from app.models import User

# [수정] 모든 라우터 임포트 확인 (notice 포함)
from app.api import auth, study, user, teacher, admin, speech, notice 
from app.core.config import settings

def create_default_users():
    with Session(engine) as session:
        if not session.get(User, "admin"):
            session.add(User(uid="admin", name="총괄 관리자", pw="1111", role="admin", progress={"settings": {"goal": 10, "review_wrong": True}}))
        if not session.get(User, "teacher"):
            session.add(User(uid="teacher", name="김선생님", pw="1111", role="teacher", progress={"settings": {"goal": 10, "review_wrong": True}}))
        if not session.get(User, "student"):
            session.add(User(uid="student", name="학생1", pw="1111", role="student", progress={"settings": {"goal": 10, "review_wrong": True}}))
        session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    create_default_users()
    yield

app = FastAPI(title="JustVoca API", lifespan=lifespan)

# [수정] 정적 파일 마운트 추가
# 1. 파일 업로드용 임시 폴더
os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.TEMP_UPLOAD_DIR), name="files")

# 2. [추가됨] 학습용 에셋(이미지/오디오) 폴더 마운트
# 실제 이미지가 저장된 폴더 경로를 지정해야 합니다. (예: backend/data/assets)
# settings.DATA_DIR이 'backend/data'를 가리킨다고 가정합니다.
assets_path = os.path.join(settings.DATA_DIR, "assets") 

# 폴더가 없으면 에러가 날 수 있으므로 체크 후 생성
os.makedirs(assets_path, exist_ok=True) 

app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# [수정] CORS 설정 강화: localhost와 127.0.0.1 모두 허용
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "JustVoca Backend is running!"}

# --- 라우터 등록 (경로 동기화) ---
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(study.router, prefix="/study", tags=["Study"])
app.include_router(user.router, prefix="/user", tags=["User"])
# [중요] teacher.py의 prefix와 중복되지 않도록 주의
app.include_router(teacher.router, prefix="/api/teacher", tags=["Teacher"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(speech.router, prefix="/speech", tags=["Speech"]) 
# [추가] 공지사항 라우터 등록
app.include_router(notice.router, prefix="/api/notice", tags=["Notice"])

os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.TEMP_UPLOAD_DIR), name="files")

@app.on_event("startup")
async def startup_event():
    print("✅ 서버가 시작되었습니다.")