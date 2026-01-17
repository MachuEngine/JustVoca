# src/vocab.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

from src.utils import log_write
from src.constants import DATA_DIR


def _build_dummy_vocab() -> Dict[str, List[Dict[str, Any]]]:
    dummy_data: List[Dict[str, Any]] = []
    for i in range(1, 21):
        ex1 = f"이것은 예문입니다 {i}"
        dummy_data.append(
            {
                "word": f"테스트단어{i}",
                "mean": "테스트 의미",
                # ✅ 예문1 고정 + 기존 ex 호환
                "예문1": ex1,
                "ex": ex1,
                "desc": "설명",
                "pronunciation": f"[테스트단어{i}]",
                "image": "📝",
                "audio_voca": "",
                "audio_ex": "",
            }
        )
    return {"초급1": dummy_data, "초급2": dummy_data, "중급1": dummy_data}


def _load_audio_map_by_id() -> Dict[str, Dict[str, str]]:
    """
    모든 JSON 파일을 스캔하여 '파일 ID(파일명)'를 기준으로 오디오 경로를 매핑합니다.
    예: "Level3_1" -> { "audio_voca": "/audio/.../Level3_1.wav", ... }

    이 방식은 단어(Text)가 중복되어도 파일명 ID가 고유하다면 충돌하지 않습니다.
    """
    audio_map: Dict[str, Dict[str, str]] = {}
    index_dir = DATA_DIR / "index"

    if not index_dir.exists():
        log_write(f"Index directory not found: {index_dir}")
        return audio_map

    for json_path in index_dir.glob("*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            items = data.get("items", [])
            for item in items:
                res = item.get("resources", {}) or {}

                voca_path = (res.get("audio_voca", {}) or {}).get("file", "") or ""
                ex_path = (res.get("audio_ex", {}) or {}).get("file", "") or ""

                target_path = voca_path if voca_path else ex_path

                if target_path:
                    file_id = Path(target_path).stem
                    audio_map[file_id] = {
                        "audio_voca": f"/{voca_path}" if voca_path else "",
                        "audio_ex": f"/{ex_path}" if ex_path else "",
                    }

        except Exception as e:
            log_write(f"json index load error ({json_path.name}): {e}")

    log_write(f"Total audio files mapped by ID: {len(audio_map)}")
    return audio_map


def _normalize_col_name(x: Any) -> str:
    """
    엑셀 컬럼명에 숨어있는 BOM/nbsp/공백 때문에 row.get('예문1') 실패하는 케이스 방지.
    """
    s = str(x)
    s = s.replace("\ufeff", "").replace("\xa0", " ").strip()
    return s


def load_vocab_data() -> Dict[str, List[Dict[str, Any]]]:
    audio_map_by_id = _load_audio_map_by_id()
    vocab_db: Dict[str, List[Dict[str, Any]]] = {}

    try:
        vocab_dir: Path = DATA_DIR / "vocab"
        vocab_dir.mkdir(parents=True, exist_ok=True)
        excel_path: Path = vocab_dir / "vocabulary.xlsx"

        if not excel_path.exists():
            return _build_dummy_vocab()

        log_write(f"excel loading: {excel_path}")
        all_sheets = pd.read_excel(excel_path, sheet_name=None, engine="openpyxl")

        for sheet_name, df in all_sheets.items():
            if df is None:
                continue

            sheet_str = str(sheet_name).strip()
            df = df.fillna("")

            # ✅ 컬럼명 정규화 (예문1 인식 실패 방지)
            df.columns = [_normalize_col_name(c) for c in df.columns]

            log_write(f"[DEBUG] sheet={sheet_str} columns={list(df.columns)}")
            log_write(f"[DEBUG] sheet={sheet_str} sample 예문1='{str(df.iloc[0].get('예문1',''))}'")


            items: List[Dict[str, Any]] = []

            # "파일 명(Image, Audio_Ex, Audio_Voca)" 같은 열 찾기
            file_id_col = None
            for col in df.columns:
                col_s = _normalize_col_name(col)
                if ("파일 명" in col_s) or ("Audio_Voca" in col_s):
                    file_id_col = col
                    break

            if not file_id_col:
                log_write(f"Warning: Could not find 'File Name' column in sheet '{sheet_str}'")

            # ✅ 예문은 오직 예문1만 사용 (고정)
            if "예문1" not in df.columns:
                log_write(f"[WARN] sheet '{sheet_str}' has no '예문1' column. columns={list(df.columns)}")

            for _, row in df.iterrows():
                cols = row.index.tolist()

                word_col = "단어" if "단어" in cols else ("word" if "word" in cols else None)
                if not word_col:
                    continue

                word = str(row.get(word_col, "")).strip()
                if not word:
                    continue

                mean = str(row.get("의미", row.get("뜻", row.get("mean", "")))).strip()

                # ✅ 예문1만 고정 (다른 컬럼 fallback 금지)
                ex1 = str(row.get("예문1", "")).strip()

                desc = str(row.get("설명", row.get("주제", row.get("desc", "")))).strip()
                pronunciation = str(row.get("발음", row.get("pronunciation", ""))).strip()
                image = str(row.get("이미지", row.get("image", "📖"))).strip()

                if not pronunciation:
                    pronunciation = f"[{word}]"

                audio_info = {"audio_voca": "", "audio_ex": ""}

                if file_id_col:
                    file_id_val = str(row.get(file_id_col, "")).strip()
                    if file_id_val:
                        found_audio = audio_map_by_id.get(file_id_val)
                        if found_audio:
                            audio_info = found_audio

                items.append(
                    {
                        "word": word,
                        "mean": mean,

                        # ✅ 둘 다 저장: 예문1 고정 + 기존 ex 호환
                        "예문1": ex1,
                        "ex": ex1,

                        "desc": desc,
                        "pronunciation": pronunciation,
                        "image": image,
                        "audio_voca": audio_info["audio_voca"],
                        "audio_ex": audio_info["audio_ex"],
                    }
                )

            if items:
                vocab_db[sheet_str] = items
                log_write(f"sheet loaded: {sheet_str} ({len(items)} items)")

        return vocab_db

    except Exception as e:
        log_write(f"excel read error: {e}")
        return {}
