# check_db.py
from sqlmodel import Session, select, create_engine
from app.models import StudyLog

# DB 연결
engine = create_engine("sqlite:///database.db")

def check_data():
    with Session(engine) as session:
        # 1. 저장된 모든 학습 로그 가져오기
        logs = session.exec(select(StudyLog)).all()
        
        print(f"\n--- [DB 데이터 점검] 총 {len(logs)}개 데이터 발견 ---")
        
        if not logs:
            print("❌ 데이터가 하나도 없습니다. 저장이 안 되고 있습니다.")
            return

        # 2. 데이터 내용 출력
        print(f"{'ID':<5} | {'User ID':<15} | {'단어':<10} | {'점수':<5} | {'날짜'}")
        print("-" * 60)
        for log in logs:
            created = log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "날짜없음"
            print(f"{log.id:<5} | {log.user_id:<15} | {log.word:<10} | {log.score:<5} | {created}")

if __name__ == "__main__":
    try:
        check_data()
    except Exception as e:
        print(f"DB 읽기 실패: {e}")
        print("Tip: app/models.py 등의 경로가 맞는지, 가상환경이 켜져 있는지 확인하세요.")