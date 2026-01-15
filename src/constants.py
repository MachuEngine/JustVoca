from __future__ import annotations
import flet as ft
from pathlib import Path


# =============================================================================
# 0. 디자인 상수 (모바일 카드 프레임)
# =============================================================================
COLOR_BG = "#f4f7f6"
COLOR_CARD_BG = "#ffffff"
COLOR_PRIMARY = "#4a90e2"
COLOR_SECONDARY = "#f39c12"
COLOR_ACCENT = "#e74c3c"
COLOR_EVAL = "#27ae60"
COLOR_TEXT_MAIN = "#2c3e50"
COLOR_TEXT_DESC = "#5d6d7e"

STYLE_BORDER_RADIUS = 28
STYLE_CARD_SHADOW = ft.BoxShadow(
    blur_radius=45,
    color="#14000000",
    offset=ft.Offset(0, 18),
)

# =============================================================================
# 1. 파일 경로 및 데이터 관리
# =============================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
VOCAB_DB = {}
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
HISTORY_FILE = "history.json"
USERS_FILE = "users.json"
SYSTEM_FILE = "system.json"
LOG_FILE = "app.log"

DEFAULT_SYSTEM = {
    "default_goal": 10,
    "review_threshold": 85,
    "api": {
        "openai_api_key": "",
        "stt_provider": "none",
    },
}

COUNTRY_OPTIONS = [
    ("KR", "대한민국"),
    ("MN", "몽골"),
    ("UZ", "우즈베키스탄"),
    ("VN", "베트남"),
    ("CN", "중국"),
    ("JP", "일본"),
    ("ETC", "기타"),
]

UI_LANG_OPTIONS = [
    ("ko", "한국어"),
    ("en", "English"),
    # 추후 확장
]

# =========================
# 임시 광고(더미) 데이터
# =========================

