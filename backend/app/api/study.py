# backend/app/api/study.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
import shutil
import os
import pandas as pd
from typing import List, Optional
import random
from datetime import datetime, timedelta

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


# app/api/study.py (기존 코드 하단에 추가)

@router.get("/review-words")
async def get_review_words(user_id: str, db: Session = Depends(get_session)):
    """
    [복습 기능]
    최근 학습 로그 중 점수가 낮은 순서대로 최대 5개 단어를 가져옵니다.
    """
    # 1. 사용자의 학습 로그 조회 (점수 낮은 순)
    statement = select(StudyLog).where(StudyLog.user_id == user_id).order_by(StudyLog.score.asc()).limit(5)
    logs = db.exec(statement).all()
    
    if not logs:
        return []

    # 2. 로그 기반으로 단어 리스트 반환 (프론트엔드 Word 타입에 맞춤)
    review_list = []
    for log in logs:
        review_list.append({
            "id": log.id,
            "word": log.word,
            "meaning": "", # 로그에는 뜻이 없으므로 빈값 혹은 DB 구조 변경 필요 (여기선 빈값 처리)
            "eng_meaning": "",
            "example": "",
            "audio_path": "",
            "level": "",
            "topic": "Review"
        })
    return review_list

@router.get("/quiz")
async def get_quiz(level: str = "초급1"):
    """
    [퀴즈 기능]
    해당 레벨의 엑셀 데이터에서 랜덤하게 3문제를 생성합니다.
    """
    if not os.path.exists(EXCEL_PATH):
        return []

    try:
        # 1. 엑셀 로드
        xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")
        target_sheet = next((s for s in xls.sheet_names if s.replace(" ", "") == level.replace(" ", "")), None)
        if not target_sheet:
            target_sheet = xls.sheet_names[0]
            
        df = pd.read_excel(xls, sheet_name=target_sheet).fillna("")
        
        # 컬럼 매핑 (단어, 의미 찾기)
        df = df.rename(columns=COLUMN_MAPPING)
        
        # 데이터가 적으면 전체 사용, 많으면 3개 샘플링
        sample_size = min(3, len(df))
        quiz_samples = df.sample(n=sample_size).to_dict(orient="records")
        
        quizzes = []
        for i, item in enumerate(quiz_samples):
            correct_word = str(item.get('word', ''))
            description = str(item.get('meaning', item.get('뜻', '')))
            
            # 오답 보기 3개 생성 (정답이 아닌 것 중에서 랜덤 샘플링)
            distractors = df[df['word'] != correct_word]['word'].sample(n=3).tolist()
            options = distractors + [correct_word]
            random.shuffle(options)
            
            quizzes.append({
                "id": i + 1,
                "question": description, # 예: "가깝게 오래 사귄 사람"
                "answer": correct_word,  # 예: "친구"
                "options": options       # ["친구", "학교", "공부", "운동"]
            })
            
        return quizzes

    except Exception as e:
        print(f"Quiz generation error: {e}")
        return []


# [신규 추가] 통계 API 엔드포인트
@router.get("/stats")
async def get_student_stats(user_id: str, db: Session = Depends(get_session)):
    """
    학생 개인 학습 통계 조회 (사양서 기반)
    """
    # 1. 학생의 모든 학습 로그 조회 (최신순)
    logs = db.exec(select(StudyLog).where(StudyLog.user_id == user_id).order_by(StudyLog.created_at.desc())).all()
    
    # 2. 이번 주(최근 7일) 학습한 단어 수 계산
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    
    # 최근 7일 내의 로그만 필터링
    weekly_logs = [log for log in logs if log.created_at >= seven_days_ago]
    # 중복 단어를 제외하고 개수 세기 (set 이용)
    weekly_learned_count = len({log.word for log in weekly_logs})
    
    # 3. 전체 평균 정확도 계산
    avg_accuracy = 0
    if logs:
        total_score = sum(log.score for log in logs)
        avg_accuracy = int(total_score / len(logs))
    
    # 4. 연속 학습일(Streak) 계산
    streak = 0
    if logs:
        # 로그에서 날짜만 추출하여 중복 제거 후 내림차순 정렬
        dates = sorted(list({log.created_at.date() for log in logs}), reverse=True)
        today = now.date()
        
        # 가장 최근 학습일이 오늘이거나 어제여야 연속 학습으로 인정
        if dates and (today - dates[0]).days <= 1:
            streak = 1
            # 과거 날짜들을 비교하며 연속 여부 확인
            for i in range(len(dates) - 1):
                if (dates[i] - dates[i+1]).days == 1:
                    streak += 1
                else:
                    break
    
    # 5. 주간 학습 추이 (월~일)
    # 0:월요일, ... 6:일요일
    weekly_trend = [0] * 7
    
    # 이번 주의 시작일(월요일) 구하기
    start_of_week = now.date() - timedelta(days=now.weekday())
    
    for log in logs:
        log_date = log.created_at.date()
        # 로그 날짜가 이번 주(월~일) 범위에 포함되는지 확인
        if start_of_week <= log_date <= (start_of_week + timedelta(days=6)):
            day_idx = log_date.weekday() # 0(월) ~ 6(일)
            weekly_trend[day_idx] += 1
            
    # 그래프 표현을 위해 가장 많이 학습한 날을 100%로 잡고 정규화
    max_val = max(weekly_trend) if max(weekly_trend) > 0 else 1
    normalized_trend = [int((val / max_val) * 100) for val in weekly_trend]

    # 6. 숙련도 (점수 구간별 분포)
    total_count = len(logs) if logs else 1
    high_count = len([l for l in logs if l.score >= 90])      # 90점 이상: 완전 암기
    mid_count = len([l for l in logs if 70 <= l.score < 90])  # 70~89점: 복습 필요
    low_count = len([l for l in logs if l.score < 70])        # 70점 미만: 다시 학습
    
    proficiency = [
        {"label": "완전 암기", "value": int((high_count / total_count) * 100), "color": "bg-green-500"},
        {"label": "복습 필요", "value": int((mid_count / total_count) * 100), "color": "bg-orange-400"},
        {"label": "다시 학습", "value": int((low_count / total_count) * 100), "color": "bg-red-400"},
    ]

    # 응원 메시지 설정
    message = "이번 주 목표 달성 중! 🔥" if weekly_learned_count > 0 else "학습을 시작해보세요! 💪"

    return {
        "weeklyLearned": weekly_learned_count,
        "streak": streak,
        "accuracy": avg_accuracy,
        "weeklyTrend": normalized_trend,
        "proficiency": proficiency,
        "message": message
    }