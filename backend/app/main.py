from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# speech 라우터 추가 임포트
from app.api import auth, study, user, teacher, admin, speech 
from app.core.config import settings
import os

app = FastAPI(title="JustVoca API")

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
# [추가] SpeechPro 발음 평가 라우터
app.include_router(speech.router, prefix="/speech", tags=["Speech"]) 

# 4. 정적 파일 설정 (녹음 파일 등 저장소)
os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.TEMP_UPLOAD_DIR), name="files")

# 5. 서버 시작 시 경로 출력
@app.on_event("startup")
async def startup_event():
    print("✅ 서버가 시작되었습니다. 사용 가능한 경로 목록:")
    for route in app.routes:
        print(f"🔗 {route.path}")