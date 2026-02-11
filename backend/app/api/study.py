# backend/app/api/study.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
import shutil
import os
import pandas as pd
import json
from typing import List, Optional, Dict
import random
from datetime import datetime, timedelta
import unicodedata  # 한글 자소 분리 방지용
import math
import calendar  # 이번 달 말일 계산용

from app.core.database import get_session
from app.models import StudyProgress, StudyLog, User

router = APIRouter()

# --- [경로 설정] ---
CURRENT_FILE_PATH = os.path.abspath(__file__)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE_PATH)))
EXCEL_PATH = os.path.join(BACKEND_DIR, "data", "vocab", "vocabulary.xlsx")
JSON_DATA_DIR = os.path.abspath(os.path.join(BACKEND_DIR, "..", "data", "index"))

class WordSchema(BaseModel):
    id: int
    level: str
    topic: str
    word: str
    pronunciation: str # 발음 필드
    meaning: str
    eng_meaning: str
    example: str
    audio_path: str 
    audio_example_path: str  # 예문 오디오 경로 필드
    image_path: str  # 이미지 경로 필드

# 기본 매핑 (고정 컬럼)
COLUMN_MAPPING = {
    "주제": "topic", 
    "단어": "word", 
    "발음": "pronunciation", 
    "한글 뜻": "meaning",     
    "영어 뜻": "eng_meaning", 
    "예문1": "example"
}

# 레벨별 JSON 파일 매핑
LEVEL_JSON_MAP = {
    "초급1": "level1.json",
    "초급2": "level2.json",
    "중급1": "level3.json",
    "중급2": "level4.json",
    "고급1": "level5.json",
    "고급2": "level6.json",
}

def load_resource_map_by_id(level: str) -> Dict[str, Dict[str, str]]:
    """
    파일명(ID)을 키로 하여 리소스 경로를 반환합니다.
    (예: "Level1_1" -> {"image_path": "...", "audio_path": "..."})
    """
    json_filename = LEVEL_JSON_MAP.get(level, "level1.json")
    json_path = os.path.join(JSON_DATA_DIR, json_filename)
    
    id_resource_map = {}
    
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = data.get("items", [])
                for item in items:
                    resources = item.get("resources", {})
                    
                    # 1. 오디오 파일명에서 ID 추출 (예: "audio/voca/Level1_1.wav" -> "Level1_1")
                    aud_file_raw = resources.get("audio_voca", {}).get("file", "")
                    if not aud_file_raw: continue
                    
                    # 경로와 확장자를 제거하고 순수 파일명만 ID로 사용
                    file_id = os.path.splitext(os.path.basename(aud_file_raw))[0]
                    
                    # 2. 경로 보정
                    img_file = resources.get("image", {}).get("file", "")
                    aud_file = aud_file_raw
                    aud_ex_file = resources.get("audio_ex", {}).get("file", "")
                    
                    if img_file and not img_file.startswith("/"): img_file = f"/assets/{img_file}"
                    if aud_file and not aud_file.startswith("/"): aud_file = f"/assets/{aud_file}"
                    if aud_ex_file and not aud_ex_file.startswith("/"): aud_ex_file = f"/assets/{aud_ex_file}"
                        
                    id_resource_map[file_id] = {
                        "image_path": img_file,
                        "audio_path": aud_file,
                        "audio_example_path": aud_ex_file
                    }
        except Exception as e:
            print(f"[Warning] Failed to load JSON by ID: {e}")
            
    return id_resource_map

# [헬퍼] 문자열 정규화 (NFC: 'ㅎ'+'ㅏ' -> '하')
def normalize_text(text: str) -> str:
    if not text: return ""
    return unicodedata.normalize('NFC', str(text)).strip()

def load_resource_map(level: str) -> Dict[str, Dict[str, str]]:
    """
    해당 레벨의 JSON 파일을 읽어 { "단어": { "image": "...", "audio": "..." } } 형태의 맵을 반환합니다.
    (NFC 정규화 적용)
    """
    json_filename = LEVEL_JSON_MAP.get(level, "level1.json")
    json_path = os.path.join(JSON_DATA_DIR, json_filename)
    
    resource_map = {}
    
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = data.get("items", [])
                for item in items:
                    # 정규화 적용하여 키 저장
                    text_key = normalize_text(item.get("text", ""))
                    resources = item.get("resources", {})
                    
                    # 경로 추출 (JSON 구조: resources > image > file)
                    img_file = resources.get("image", {}).get("file", "")
                    aud_file = resources.get("audio_voca", {}).get("file", "")
                    aud_ex_file = resources.get("audio_ex", {}).get("file", "") # 예문 오디오 추출
                    
                    # 프론트엔드용 경로 보정 (/assets/ 추가)
                    if img_file and not img_file.startswith("/"):
                        img_file = f"/assets/{img_file}"
                    if aud_file and not aud_file.startswith("/"):
                        aud_file = f"/assets/{aud_file}"
                    if aud_ex_file and not aud_ex_file.startswith("/"):
                        aud_ex_file = f"/assets/{aud_ex_file}"
                        
                    resource_map[text_key] = {
                        "image_path": img_file,
                        "audio_path": aud_file,
                        "audio_example_path": aud_ex_file
                    }
        except Exception as e:
            print(f"[Warning] Failed to load JSON resources for {level}: {e}")
            
    return resource_map

@router.get("/current-progress")
async def get_current_progress(user_id: str, db: Session = Depends(get_session)):
    statement = select(StudyProgress).where(StudyProgress.user_id == user_id).order_by(StudyProgress.updated_at.desc())
    progress = db.exec(statement).first()
    if not progress:
        return {"level": "초급1", "current_page": 1}
    return {"level": progress.level, "current_page": progress.current_page}

@router.get("/words", response_model=List[WordSchema])
async def get_words(level: str = "초급1", user_id: Optional[str] = None, db: Session = Depends(get_session)):
    if not os.path.exists(EXCEL_PATH): return []

    try:
        current_page = 1
        if user_id:
            user = db.get(User, user_id)
            if not user:
                user = User(uid=user_id, name=user_id, role="student")
                db.add(user); db.commit()
            statement = select(StudyProgress).where(StudyProgress.user_id == user_id, StudyProgress.level == level)
            progress = db.exec(statement).first()
            if progress: current_page = progress.current_page

        xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")
        target_sheet = next((s for s in xls.sheet_names if s.replace(" ", "") == level.replace(" ", "")), None)
        if not target_sheet: target_sheet = random.choice(xls.sheet_names)
        
        df = pd.read_excel(xls, sheet_name=target_sheet)
        
        # 오디오 컬럼 처리
        actual_cols = df.columns.tolist()
        audio_col = next((c for c in actual_cols if "Audio_Voca" in str(c) or "파일 명" in str(c)), None)
        temp_mapping = COLUMN_MAPPING.copy()
        if audio_col: temp_mapping[audio_col] = "audio_path"
        df = df.rename(columns=temp_mapping)

        required_fields = list(COLUMN_MAPPING.values()) + ["audio_path"]
        for col in required_fields:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")

        start_idx = (current_page - 1) * 10
        if start_idx >= len(df): start_idx = 0 
        paged_df = df.iloc[start_idx : start_idx + 10].copy()
        
        if 'level' not in paged_df.columns: paged_df['level'] = target_sheet
        if 'topic' not in paged_df.columns: paged_df['topic'] = "General"

        # JSON 리소스 로드
        resource_map = load_resource_map_by_id(level) 
        data_list = []
        
        for idx, item in enumerate(paged_df.to_dict(orient="records")):
            # 2단계: 매칭 기준을 word_text에서 파일명(audio_path)으로 변경
            file_id = str(item.get('audio_path', '')).strip()
            
            # ID(파일명)를 키로 사용하여 JSON에서 가져온 리소스를 찾습니다.
            res = resource_map.get(file_id, {})
            
            # [안전장치] 만약 ID로 못 찾았을 경우에만 기존처럼 단어 텍스트로 시도
            if not res:
                word_text = normalize_text(item.get('word', ''))

            data_list.append({
                "id": start_idx + idx + 1,
                "level": level,
                "topic": item.get('topic', 'General'),
                "word": normalize_text(item.get('word', '')), # 엑셀의 단어
                "pronunciation": str(item.get('pronunciation', '')),
                "meaning": str(item.get('meaning', '')),
                "eng_meaning": str(item.get('eng_meaning', '')),
                "example": str(item.get('example', '')),
                # JSON에서 찾은 오디오/이미지 경로를 우선 사용하고, 없으면 엑셀 값 유지
                "audio_path": res.get("audio_path", str(item.get('audio_path', ''))),
                "audio_example_path": res.get("audio_example_path", ""), 
                "image_path": res.get("image_path", "")
            })
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
    # 1. 해당 레벨의 총 페이지 수 계산
    total_pages = 1
    if os.path.exists(EXCEL_PATH):
        try:
            xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")
            # 시트 찾기 (get_words와 동일한 로직)
            target_sheet = next((s for s in xls.sheet_names if s.replace(" ", "") == level.replace(" ", "")), None)
            if not target_sheet: 
                target_sheet = random.choice(xls.sheet_names)
            
            df = pd.read_excel(xls, sheet_name=target_sheet)
            # 10개씩 페이징 처리되므로 전체 페이지 수 계산 (올림 처리)
            total_pages = math.ceil(len(df) / 10)
        except Exception as e:
            print(f"Page calc error: {e}")
            pass

    # 2. 진도 업데이트 및 졸업 여부 판단
    statement = select(StudyProgress).where(StudyProgress.user_id == user_id, StudyProgress.level == level)
    progress = db.exec(statement).first()
    
    level_completed = False # 졸업 여부 플래그

    if progress:
        # 현재 보고 있는 페이지가 마지막 페이지(혹은 그 이상)라면 졸업
        if progress.current_page >= total_pages:
            level_completed = True
        
        progress.current_page += 1
        progress.updated_at = datetime.now()
        db.add(progress)
    else:
        new_progress = StudyProgress(user_id=user_id, level=level, current_page=2)
        db.add(new_progress)
        # 만약 단어가 10개 이하라면 1페이지가 곧 마지막이므로 바로 졸업 처리 가능
        if total_pages <= 1:
            level_completed = True

    # 레벨 완료 테스트 플래그 설정 (디버그용)
    # 설정 시 10개 단어 학습하면 바로 졸업 축하 화면 표시
    # level_completed = True

    db.commit()
    
    # level_completed 필드를 프론트로 전달
    return {
        "status": "success", 
        "next_page": progress.current_page if progress else 2,
        "level_completed": level_completed 
    }

@router.get("/review-words")
async def get_review_words(user_id: str, db: Session = Depends(get_session)):
    if not os.path.exists(EXCEL_PATH): return []

    # 1. 넉넉하게 최근/취약 기록 50개를 먼저 가져옵니다.
    statement = select(StudyLog).where(StudyLog.user_id == user_id).order_by(StudyLog.score.asc()).limit(50)
    all_logs = db.exec(statement).all()
    if not all_logs: return []

    # 2. 파이썬에서 단어 중복 제거 (이미 나온 단어는 건너뜀)
    unique_logs = []
    seen_words = set()
    for log in all_logs:
        if log.word not in seen_words:
            unique_logs.append(log)
            seen_words.add(log.word)
        if len(unique_logs) >= 10: # 최종적으로 10개만 선택
            break

    # 3. 엑셀 데이터 로드 및 매칭
    xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")
    all_df = pd.concat([pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names], ignore_index=True)
    all_df = all_df.rename(columns=COLUMN_MAPPING)
    
    actual_cols = all_df.columns.tolist()
    audio_col = next((c for c in actual_cols if "Audio_Voca" in str(c) or "파일 명" in str(c)), "audio_path")
    all_df = all_df.rename(columns={audio_col: "audio_path"})

    review_list = []
    json_cache = {}

    for log in unique_logs: # 중복 제거된 리스트 사용
        row = all_df[all_df['word'] == log.word].iloc[0] if any(all_df['word'] == log.word) else None
        
        if row is not None:
            file_id = str(row.get('audio_path', '')).strip()
            
            import re
            m = re.search(r'Level(\d+)', file_id, re.I)
            level_num = m.group(1) if m else "1"
            json_filename = f"level{level_num}.json"

            if json_filename not in json_cache:
                json_path = os.path.join(JSON_DATA_DIR, json_filename)
                json_cache[json_filename] = {}
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            for item in data.get("items", []):
                                res = item.get("resources", {})
                                aud_raw = res.get("audio_voca", {}).get("file", "")
                                if not aud_raw: continue
                                fid = os.path.splitext(os.path.basename(aud_raw))[0]
                                img = res.get("image", {}).get("file", "")
                                aud_ex = res.get("audio_ex", {}).get("file", "")
                                json_cache[json_filename][fid] = {
                                    "image_path": f"/assets/{img}" if img and not img.startswith("/") else img,
                                    "audio_path": f"/assets/{aud_raw}" if aud_raw and not aud_raw.startswith("/") else aud_raw,
                                    "audio_example_path": f"/assets/{aud_ex}" if aud_ex and not aud_ex.startswith("/") else aud_ex
                                }
                    except: pass

            res = json_cache[json_filename].get(file_id, {})

            review_list.append({
                "id": log.id,
                "level": str(row.get('level', f"Level{level_num}")),
                "topic": "전체 복습",
                "word": log.word,
                "pronunciation": str(row.get('pronunciation', '')),
                "meaning": str(row.get('meaning', '')),
                "eng_meaning": str(row.get('eng_meaning', '')),
                "example": str(row.get('example', '')),
                "audio_path": res.get("audio_path", ""),
                "audio_example_path": res.get("audio_example_path", ""),
                "image_path": res.get("image_path", "")
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

@router.get("/stats")
async def get_student_stats(user_id: str, db: Session = Depends(get_session)):
    """
    학생 학습 통계 (달력 기준: 이번 주 월~일 / 이번 달 1일~말일)
    """
    logs = db.exec(select(StudyLog).where(StudyLog.user_id == user_id).order_by(StudyLog.created_at.desc())).all()
    now = datetime.now()
    today_date = now.date()
    
    # 1. 이번 주 요약용 (상대적 최근 7일 학습 단어 수)
    seven_days_ago = now - timedelta(days=7)
    weekly_logs = [log for log in logs if log.created_at >= seven_days_ago]
    weekly_learned_count = len({log.word for log in weekly_logs})
    
    # 2. 정확도 및 Streak 계산
    avg_accuracy = 0
    if logs:
        avg_accuracy = int(sum(log.score for log in logs) / len(logs))
    
    streak = 0
    if logs:
        dates = sorted(list({log.created_at.date() for log in logs}), reverse=True)
        if dates and (today_date - dates[0]).days <= 1:
            streak = 1
            for i in range(len(dates) - 1):
                if (dates[i] - dates[i+1]).days == 1: streak += 1
                else: break

    # 3. [달력 기준] 주간 학습 추이 (이번 주 월요일 ~ 일요일)
    weekly_trend = [0] * 7
    # 월요일(0)을 기준으로 시작일 계산
    start_of_week = today_date - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # 4. [달력 기준] 월간 학습 추이 (이번 달 1일 ~ 말일)
    # 이번 달의 마지막 날짜 구하기
    _, last_day = calendar.monthrange(now.year, now.month)
    monthly_trend = [0] * last_day
    start_of_month = today_date.replace(day=1)

    for log in logs:
        log_date = log.created_at.date()
        
        # 주간 집계 (이번 주 범위 내)
        if start_of_week <= log_date <= end_of_week:
            day_idx = log_date.weekday() # 0(월) ~ 6(일)
            weekly_trend[day_idx] += 1
            
        # 월간 집계 (이번 달 범위 내)
        if start_of_month <= log_date <= today_date.replace(day=last_day):
            if log_date.month == now.month and log_date.year == now.year:
                day_idx = log_date.day - 1 # 1일은 0번 인덱스
                monthly_trend[day_idx] += 1

    # 그래프 정규화
    max_w = max(weekly_trend) if max(weekly_trend) > 0 else 1
    normalized_weekly = [int((v / max_w) * 100) for v in weekly_trend]
    
    max_m = max(monthly_trend) if max(monthly_trend) > 0 else 1
    normalized_monthly = [int((v / max_m) * 100) for v in monthly_trend]

    # 5. 숙련도 및 메시지
    total_count = len(logs) if logs else 1
    proficiency = [
        {"label": "학습 완료", "value": int((len([l for l in logs if l.score >= 90]) / total_count) * 100), "color": "bg-green-500"},
        {"label": "복습 필요", "value": int((len([l for l in logs if 70 <= l.score < 90]) / total_count) * 100), "color": "bg-orange-400"},
        {"label": "다시 학습", "value": int((len([l for l in logs if l.score < 70]) / total_count) * 100), "color": "bg-red-400"},
    ]
    message = "이번 주 목표 달성 중" if weekly_learned_count > 0 else "학습을 시작해보세요"

    return {
        "weeklyLearned": weekly_learned_count,
        "streak": streak,
        "accuracy": avg_accuracy,
        "weeklyTrend": normalized_weekly,
        "monthlyTrend": normalized_monthly,
        "proficiency": proficiency,
        "message": message
    }