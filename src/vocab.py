# src/vocab.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

from src.utils import log_write
from src.constants import DATA_DIR

# (참고) 지금 파일에서는 MEDIA_INDEX_FILE을 선언만 하고 사용하지 않으니
# 필요한 곳에서만 import/사용하도록 두거나, 여기서 계속 유지해도 됨.
MEDIA_INDEX_FILE = DATA_DIR / "index" / "media_index.json"


def _build_dummy_vocab() -> Dict[str, List[Dict[str, Any]]]:
    dummy_data: List[Dict[str, Any]] = []
    for i in range(1, 21):
        dummy_data.append(
            {
                "word": f"테스트단어{i}",
                "mean": "테스트 의미",
                "ex": f"이것은 예문입니다 {i}",
                "desc": "설명",
                "pronunciation": f"[테스트단어{i}]",
                "image": "📝",
            }
        )
    return {"초급1": dummy_data, "초급2": dummy_data, "중급1": dummy_data}


def load_vocab_data() -> Dict[str, List[Dict[str, Any]]]:
    """
    엑셀 파일 로드: sheet_name == 토픽/레벨로 취급

    - 위치 고정: {DATA_DIR}/vocab/vocabulary.xlsx
    - src 구조로 옮겨도 실행 위치(cwd)에 상관없이 항상 동일 파일을 읽음
    """
    try:
        vocab_dir: Path = DATA_DIR / "vocab"
        vocab_dir.mkdir(parents=True, exist_ok=True)

        excel_path: Path = vocab_dir / "vocabulary.xlsx"

        if not excel_path.exists():
            return _build_dummy_vocab()

        log_write(f"excel loading: {excel_path}")
        all_sheets = pd.read_excel(excel_path, sheet_name=None, engine="openpyxl")

        vocab_db: Dict[str, List[Dict[str, Any]]] = {}

        for sheet_name, df in all_sheets.items():
            if df is None:
                continue

            df = df.fillna("")
            items: List[Dict[str, Any]] = []

            for _, row in df.iterrows():
                cols = row.index.tolist()
                if "단어" not in cols and "word" not in cols:
                    continue

                word = str(row.get("단어", row.get("word", ""))).strip()
                if not word:
                    continue

                mean = str(row.get("의미", row.get("뜻", row.get("mean", "")))).strip()
                ex = str(row.get("예문", row.get("예문1", row.get("example", "")))).strip()
                desc = str(row.get("설명", row.get("주제", row.get("desc", "")))).strip()
                pronunciation = str(row.get("발음", row.get("pronunciation", ""))).strip()
                image = str(row.get("이미지", row.get("image", "📖"))).strip()

                if not pronunciation:
                    pronunciation = f"[{word}]"

                items.append(
                    {
                        "word": word,
                        "mean": mean,
                        "ex": ex,
                        "desc": desc,
                        "pronunciation": pronunciation,
                        "image": image,
                    }
                )

            if items:
                vocab_db[str(sheet_name)] = items
                log_write(f"sheet loaded: {sheet_name} ({len(items)} items)")

        return vocab_db

    except Exception as e:
        log_write(f"excel read error: {e}")
        return {}
