from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import shutil
import os
import pandas as pd
from typing import List, Optional
import random

from app.core.database import get_db
from app.models import StudyProgress, StudyLog, User

router = APIRouter()

CURRENT_FILE_PATH = os.path.abspath(__file__)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE_PATH))))
EXCEL_PATH = os.path.join(BACKEND_DIR, "data", "vocab", "vocabulary.xlsx")

class WordSchema(BaseModel):
    id: int
    level: str
    topic: str
    word: str
    meaning: str
    eng_meaning: str
    example: str

COLUMN_MAPPING = {"주제": "topic", "단어": "word", "분류": "meaning", "CEFR Level": "eng_meaning", "예문1": "example"}

@router.get("/current-progress")
async def get_current_progress(user_id: str, db: Session = Depends(get_db)):
    """
    사용자의 가장 최근 학습 레벨 정보를 가져옵니다.
    """
    # 마지막으로 업데이트된 진도 정보를 가져옴
    progress = db.query(StudyProgress).filter(
        StudyProgress.user_id == user_id
    ).order_by(StudyProgress.updated_at.desc()).first()

    if not progress:
        # 진도 정보가 없는 신규 유저라면 기본값으로 '초급1' 반환
        return {"level": "초급1", "current_page": 1}

    return {
        "level": progress.level,
        "current_page": progress.current_page
    }

@router.get("/words", response_model=List[WordSchema])
async def get_words(
    level: str = "초급1", 
    user_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    print(f"\n--- [요청] 레벨: {level} | 유저: {user_id} ---")

    if not os.path.exists(EXCEL_PATH):
        print(f"❌ 엑셀 파일 없음: {EXCEL_PATH}")
        return []

    try:
        current_page = 1
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(id=user_id, name=user_id, role="student")
                db.add(user)
                db.commit()
            
            progress = db.query(StudyProgress).filter(
                StudyProgress.user_id == user_id, 
                StudyProgress.level == level
            ).first()
            if progress:
                current_page = progress.current_page

        xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")
        target_sheet = next((s for s in xls.sheet_names if s.replace(" ", "") == level.replace(" ", "")), None)
        
        if not target_sheet:
            target_sheet = random.choice(xls.sheet_names)
            
        df = pd.read_excel(xls, sheet_name=target_sheet)
        df = df.rename(columns=COLUMN_MAPPING)

        for col in COLUMN_MAPPING.values():
            if col not in df.columns: df[col] = ""
        df = df.fillna("")

        start_idx = (current_page - 1) * 10
        if start_idx >= len(df): 
            start_idx = 0
            
        paged_df = df.iloc[start_idx : start_idx + 10].copy()
        if 'level' not in paged_df.columns:
            paged_df['level'] = target_sheet

        data_list = paged_df.to_dict(orient="records")
        for idx, item in enumerate(data_list):
            item['id'] = start_idx + idx + 1

        print(f"✅ {len(data_list)}개 단어 추출 완료 (시작 인덱스: {start_idx})")
        return data_list

    except Exception as e:
        print(f"🔥 백엔드 에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate")
async def evaluate_pronunciation(
    file: UploadFile = File(...), 
    word: str = Form(...),
    user_id: str = Form(...), 
    db: Session = Depends(get_db)
):
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    with open(f"{upload_dir}/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    score = random.randint(75, 100)
    feedback = "참 잘했어요!" if score > 85 else "조금만 더 힘내세요!"

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
    db: Session = Depends(get_db)
):
    progress = db.query(StudyProgress).filter(
        StudyProgress.user_id == user_id, 
        StudyProgress.level == level
    ).first()

    if progress:
        progress.current_page += 1
    else:
        new_progress = StudyProgress(user_id=user_id, level=level, current_page=2)
        db.add(new_progress)
    
    db.commit()
    return {"status": "success", "next_page": progress.current_page if progress else 2}