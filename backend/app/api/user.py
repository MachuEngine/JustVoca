# backend/app/api/user.py
from fastapi import APIRouter
from app.core.session import load_users, load_notices, save_users
from datetime import datetime

router = APIRouter()

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
    all_n = load_notices()
    now = datetime.now().isoformat()
    # 예약 시간 지난 공지 필터링
    valid = [n for n in all_n if n.get("scheduled_at", "") <= now]
    return sorted(valid, key=lambda x: x["created_at"], reverse=True)