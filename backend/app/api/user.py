# backend/app/api/user.py
from fastapi import APIRouter, HTTPException, Depends
# [수정] load_notices 추가됨
from app.core.session import load_users, save_users, load_notices, hash_password, verify_password
from app.schemas import UserProfileUpdate, UserSettingsUpdate, UserPasswordUpdate
from datetime import datetime

router = APIRouter()

# --- [기존 기능] ---

@router.get("/{user_id}/stats")
async def get_stats(user_id: str):
    users = load_users()
    u = users.get(user_id)
    if not u: return {}
    
    prog = u.get("progress", {}).get("topics", {})
    total_learned = sum(len(t.get("learned", {})) for t in prog.values())
    
    # 차트 데이터 생성
    chart_data = [{"name": k, "score": v.get("stats", {}).get("avg_score", 0)} for k, v in prog.items()]
    
    return {
        "name": u["name"],
        "total_learned": total_learned,
        "chart_data": chart_data,
        "goal": u.get("progress", {}).get("settings", {}).get("goal", 10)
    }

@router.get("/{user_id}/notices")
async def get_notices(user_id: str):
    all_n = load_notices() # 이제 정상 동작합니다
    now = datetime.now().isoformat()
    # 예약 시간 지난 공지 필터링
    valid = [n for n in all_n if n.get("scheduled_at", "") <= now]
    return sorted(valid, key=lambda x: x["created_at"], reverse=True)


# --- [신규 추가 기능: 설정 화면용] ---

# 1. 사용자 프로필 및 설정 조회
@router.get("/{user_id}/profile")
async def get_profile(user_id: str):
    users = load_users()
    u = users.get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # settings가 없는 경우를 대비한 안전한 접근
    progress = u.get("progress", {})
    settings = progress.get("settings", {})
    
    return {
        "uid": u["uid"],
        "name": u["name"],
        "role": u.get("role", "student"),
        "email": u.get("email", ""),
        "phone": u.get("phone", ""),
        "country": u.get("country", ""),
        "dailyGoal": settings.get("goal", 10),
        "reviewWrong": settings.get("review_wrong", True)
    }

# 2. 프로필 정보 수정 (이메일, 전화번호, 국가)
@router.put("/{user_id}/profile")
async def update_profile(user_id: str, data: UserProfileUpdate):
    users = load_users()
    if user_id not in users:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    user = users[user_id]
    
    # 변경된 필드만 업데이트
    if data.email is not None: user["email"] = data.email
    if data.phone is not None: user["phone"] = data.phone
    if data.country is not None: user["country"] = data.country
    
    save_users(users)
    return {"status": "ok", "message": "프로필이 업데이트되었습니다."}

# 3. 학습 설정 수정 (목표량, 오답노트)
@router.put("/{user_id}/settings")
async def update_settings(user_id: str, data: UserSettingsUpdate):
    users = load_users()
    if user_id not in users:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    user = users[user_id]
    
    # progress 구조가 없으면 생성
    if "progress" not in user: user["progress"] = {}
    if "settings" not in user["progress"]: user["progress"]["settings"] = {}
    
    settings = user["progress"]["settings"]
    
    # 키값 매핑 (Frontend: camelCase -> Backend: snake_case/stored key)
    if data.dailyGoal is not None: settings["goal"] = data.dailyGoal
    if data.reviewWrong is not None: settings["review_wrong"] = data.reviewWrong
    
    save_users(users)
    return {"status": "ok", "message": "학습 설정이 저장되었습니다."}

# 4. 비밀번호 변경
@router.put("/{user_id}/password")
async def change_password(user_id: str, data: UserPasswordUpdate):
    users = load_users()
    if user_id not in users:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    user = users[user_id]
    stored_pw = user["pw"]
    
    # 기존 비밀번호 검증 (평문/해시 호환)
    valid = False
    if stored_pw == data.old_password:
        valid = True
    else:
        valid, _ = verify_password(stored_pw, data.old_password)
        
    if not valid:
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
    
    # 새 비밀번호 해시 적용 후 저장
    user["pw"] = hash_password(data.new_password)
    save_users(users)
    
    return {"status": "ok", "message": "비밀번호가 변경되었습니다."}

# 5. 회원 탈퇴
@router.delete("/{user_id}")
async def withdraw_user(user_id: str):
    users = load_users()
    if user_id not in users:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 사용자 삭제
    del users[user_id]
    save_users(users)
    
    return {"status": "ok", "message": "회원 탈퇴가 완료되었습니다."}