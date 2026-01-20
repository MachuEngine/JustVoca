# backend/app/api/study.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
import shutil
import os
import pandas as pd
from typing import List, Optional
import random
from datetime import datetime

# [수정] 프로젝트 설정에 맞게 get_session으로 변경
from app.core.database import get_session
from app.models import StudyProgress, StudyLog, User

router = APIRouter()

# 엑셀 파일 경로 설정
CURRENT_FILE_PATH = os.path.abspath(__file__)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE_PATH)))
EXCEL_PATH = os.path.join(BACKEND_DIR, "data", "vocab", "vocabulary.xlsx")

# 응답 스키마
class WordSchema(BaseModel):
    id: int
    level: str
    topic: str
    word: str
    meaning: str
    eng_meaning: str
    example: str

# 엑셀 컬럼 매핑
COLUMN_MAPPING = {"주제": "topic", "단어": "word", "분류": "meaning", "CEFR Level": "eng_meaning", "예문1": "example"}

@router.get("/current-progress")
async def get_current_progress(user_id: str, db: Session = Depends(get_session)):
    """
    사용자의 가장 최근 학습 레벨 정보를 가져옵니다.
    """
    # SQLModel 방식으로 쿼리 수정
    statement = select(StudyProgress).where(StudyProgress.user_id == user_id).order_by(StudyProgress.updated_at.desc())
    progress = db.exec(statement).first()

    if not progress:
        return {"level": "초급1", "current_page": 1}

    return {
        "level": progress.level,
        "current_page": progress.current_page
    }

@router.get("/words", response_model=List[WordSchema])
async def get_words(
    level: str = "초급1", 
    user_id: Optional[str] = None, 
    db: Session = Depends(get_session)
):
    print(f"\n--- [요청] 레벨: {level} | 유저: {user_id} ---")

    # 1. 엑셀 파일 존재 확인
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ 엑셀 파일 없음: {EXCEL_PATH}")
        # 파일이 없을 경우를 대비해 빈 리스트 반환 (500 에러 방지)
        return []

    try:
        current_page = 1
        
        # 2. 유저 및 진도 확인
        if user_id:
            user = db.get(User, user_id)
            if not user:
                # 유저가 없으면 자동 생성 (기존 로직 유지)
                user = User(uid=user_id, name=user_id, role="student")
                db.add(user)
                db.commit()
            
            # 해당 레벨의 진도 확인
            statement = select(StudyProgress).where(StudyProgress.user_id == user_id, StudyProgress.level == level)
            progress = db.exec(statement).first()
            
            if progress:
                current_page = progress.current_page

        # 3. 엑셀 파일 로드 (Pandas)
        xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")
        
        # 요청한 레벨(시트명) 찾기 (공백 무시 비교)
        target_sheet = next((s for s in xls.sheet_names if s.replace(" ", "") == level.replace(" ", "")), None)
        
        if not target_sheet:
            print(f"[WARN] '{level}' 시트가 없어 랜덤 시트를 선택합니다.")
            target_sheet = random.choice(xls.sheet_names)
            
        df = pd.read_excel(xls, sheet_name=target_sheet)
        df = df.rename(columns=COLUMN_MAPPING)

        # 필수 컬럼 채우기
        for col in COLUMN_MAPPING.values():
            if col not in df.columns: df[col] = ""
        df = df.fillna("")

        # 4. 페이징 처리 (10개씩)
        start_idx = (current_page - 1) * 10
        if start_idx >= len(df): 
            start_idx = 0 # 끝까지 갔으면 처음으로
            
        paged_df = df.iloc[start_idx : start_idx + 10].copy()
        
        if 'level' not in paged_df.columns:
            paged_df['level'] = target_sheet
        
        if 'topic' not in paged_df.columns:
            paged_df['topic'] = "General"

        # 5. 응답 데이터 생성
        data_list = paged_df.to_dict(orient="records")
        for idx, item in enumerate(data_list):
            item['id'] = start_idx + idx + 1
            # Pydantic 스키마에 맞게 문자열 변환
            item['word'] = str(item.get('word', ''))
            item['meaning'] = str(item.get('meaning', ''))
            item['eng_meaning'] = str(item.get('eng_meaning', ''))
            item['example'] = str(item.get('example', ''))

        print(f"✅ {len(data_list)}개 단어 추출 완료 (페이지: {current_page})")
        return data_list

    except Exception as e:
        print(f"🔥 백엔드 에러 발생: {str(e)}")
        # 디버깅을 위해 에러 로그 출력 후 빈 리스트 반환 or 500 에러
        raise HTTPException(status_code=500, detail=f"Data Load Error: {str(e)}")

@router.post("/evaluate")
async def evaluate_pronunciation(
    file: UploadFile = File(...), 
    word: str = Form(...),
    user_id: str = Form(...), 
    db: Session = Depends(get_session)
):
    # 파일 저장 디렉토리
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # [임시 로직] 실제 평가 엔진 연동 전 랜덤 점수
    # 추후 SpeechPro 엔진 연동 시 이 부분을 수정하면 됩니다.
    score = random.randint(75, 100)
    feedback = "참 잘했어요!" if score > 85 else "조금만 더 힘내세요!"

    # 학습 로그 DB 저장
    new_log = StudyLog(
        user_id=user_id,
        word=word,
        score=float(score),
        feedback=feedback
    )
    db.add(new_log)
    db.commit()

    return {
        "status": "success", 
        "score": score, 
        "feedback": feedback, 
        "recognized_text": word
    }

@router.post("/complete")
async def complete_step(
    user_id: str = Form(...),
    level: str = Form(...),
    db: Session = Depends(get_session)
):
    statement = select(StudyProgress).where(StudyProgress.user_id == user_id, StudyProgress.level == level)
    progress = db.exec(statement).first()

    if progress:
        progress.current_page += 1
        progress.updated_at = datetime.now()
        db.add(progress)
    else:
        new_progress = StudyProgress(user_id=user_id, level=level, current_page=2)
        db.add(new_progress)
    
    db.commit()
    
    next_page = progress.current_page if progress else 2
    return {"status": "success", "next_page": next_page}