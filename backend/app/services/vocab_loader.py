import os
import pandas as pd
from typing import Dict, List, Any
from app.core.config import settings # 설정 파일 사용

def load_vocab_data() -> Dict[str, List[Dict[str, Any]]]:
    # settings.DATA_DIR을 사용하여 경로 안전성 확보
    vocab_path = settings.DATA_DIR / "vocab.xlsx"

    if not os.path.exists(vocab_path):
        # 파일 없을 시 테스트 데이터 반환
        return {
            "초급1": [{"word": "테스트", "mean": "Test", "예문1": "테스트입니다.", "correct": "테스트"}] 
        }

    try:
        df = pd.read_excel(vocab_path)
        result = {}
        # 'Topic' 컬럼이 없다면 전체를 '기본'으로 처리
        if "Topic" not in df.columns:
            result["기본"] = df.to_dict(orient="records")
        else:
            for topic, group in df.groupby("Topic"):
                result[topic] = group.to_dict(orient="records")
        return result
    except Exception as e:
        print(f"Error loading vocab: {e}")
        return {}