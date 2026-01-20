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

from app.core.database import get_session
from app.models import StudyProgress, StudyLog, User

router = APIRouter()

# 엑셀 파일 경로 설정
CURRENT_FILE_PATH = os.path.abspath(__file__)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE_PATH)))
EXCEL_PATH = os.path.join(BACKEND_DIR, "data", "vocab", "vocabulary.xlsx")

class WordSchema(BaseModel):
    id: int
    level: str
    topic: str
    word: str
    meaning: str
    eng_meaning: str
    example: str
    audio_path: str # 오디오 정보 포함

# 기본 매핑 (고정 컬럼)
COLUMN_MAPPING = {
    "주제": "topic", 
    "단어": "word", 
    "분류": "meaning", 
    "CEFR Level": "eng_meaning", 
    "예문1": "example"
}

@router.get("/current-progress")
async def get_current_progress(user_id: str, db: Session = Depends(get_session)):
    statement = select(StudyProgress).where(StudyProgress.user_id == user_id).order_by(StudyProgress.updated_at.desc())
    progress = db.exec(statement).first()
    if not progress:
        return {"level": "초급1", "current_page": 1}
    return {"level": progress.level, "current_page": progress.current_page}

@router.get("/words", response_model=List[WordSchema])
async def get_words(
    level: str = "초급1", 
    user_id: Optional[str] = None, 
    db: Session = Depends(get_session)
):
    if not os.path.exists(EXCEL_PATH):
        return []

    try:
        current_page = 1
        if user_id:
            user = db.get(User, user_id)
            if not user:
                user = User(uid=user_id, name=user_id, role="student")
                db.add(user)
                db.commit()
            
            statement = select(StudyProgress).where(StudyProgress.user_id == user_id, StudyProgress.level == level)
            progress = db.exec(statement).first()
            if progress:
                current_page = progress.current_page

        xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")
        target_sheet = next((s for s in xls.sheet_names if s.replace(" ", "") == level.replace(" ", "")), None)
        
        if not target_sheet:
            target_sheet = random.choice(xls.sheet_names)
            
        df = pd.read_excel(xls, sheet_name=target_sheet)
        
        # --- [오디오 컬럼 유연한 매핑 로직 추가] ---
        actual_cols = df.columns.tolist()
        # "Audio_Voca" 또는 "파일 명"이라는 단어가 포함된 컬럼을 찾습니다.
        audio_col = next((c for c in actual_cols if "Audio_Voca" in str(c) or "파일 명" in str(c)), None)
        
        # 찾은 오디오 컬럼을 audio_path로 이름 변경
        temp_mapping = COLUMN_MAPPING.copy()
        if audio_col:
            temp_mapping[audio_col] = "audio_path"
            
        df = df.rename(columns=temp_mapping)

        # 필수 컬럼이 없을 경우 빈 값 생성
        required_fields = list(COLUMN_MAPPING.values()) + ["audio_path"]
        for col in required_fields:
            if col not in df.columns: df[col] = ""
        
        df = df.fillna("")

        start_idx = (current_page - 1) * 10
        if start_idx >= len(df): start_idx = 0 
        paged_df = df.iloc[start_idx : start_idx + 10].copy()
        
        if 'level' not in paged_df.columns: paged_df['level'] = target_sheet
        if 'topic' not in paged_df.columns: paged_df['topic'] = "General"

        data_list = paged_df.to_dict(orient="records")
        for idx, item in enumerate(data_list):
            item['id'] = start_idx + idx + 1
            item['word'] = str(item.get('word', ''))
            item['meaning'] = str(item.get('meaning', ''))
            item['eng_meaning'] = str(item.get('eng_meaning', ''))
            item['example'] = str(item.get('example', ''))
            item['audio_path'] = str(item.get('audio_path', '')) # 데이터를 문자열로 확실히 변환

        return data_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data Load Error: {str(e)}")

@router.post("/evaluate")
async def evaluate_pronunciation(
    file: UploadFile = File(...), 
    word: str = Form(...),
    user_id: str = Form(...), 
    db: Session = Depends(get_session)
):
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    score = random.randint(75, 100)
    feedback = "참 잘했어요!" if score > 85 else "조금만 더 힘내세요!"
    new_log = StudyLog(user_id=user_id, word=word, score=float(score), feedback=feedback)
    db.add(new_log)
    db.commit()

    return {"status": "success", "score": score, "feedback": feedback, "recognized_text": word}

@router.post("/complete")
async def complete_step(user_id: str = Form(...), level: str = Form(...), db: Session = Depends(get_session)):
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
    return {"status": "success", "next_page": progress.current_page if progress else 2}