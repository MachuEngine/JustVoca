import flet as ft
import random

# src/constants.py
from pathlib import Path

# src/constants.py 파일 위치: project_root/src/constants.py
# project_root = src의 부모
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"

SYSTEM_FILE = DATA_DIR / "system.json"
USERS_FILE = DATA_DIR / "users.json"
HISTORY_FILE = DATA_DIR / "history.json"


DUMMY_ADS = [
    {
        "title": "📌 광고: 오누이 한국어",
        "desc": "한국에 거주를 원하는 외국인들을 위한 한국어 교육 솔루션",
        "cta": "자세히 보기",
    }
]
def build_ad_zone(on_click=None) -> ft.Control:
    """
    홈 화면용 광고 영역(임시 더미).
    - 랜덤 1개 선택
    - 눌렀을 때 동작은 on_click으로 주입 가능
    """
    ad = random.choice(DUMMY_ADS)

    return ft.Container(
        padding=14,
        border_radius=18,
        bgcolor="#ffffff",
        border=ft.border.all(1, "#dfe6ee"),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text(ad["title"], size=14, weight="w700"),
                ft.Text(ad["desc"], size=12, color="#56606a"),
                ft.Container(height=6),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=999,
                    bgcolor="#f2f4f7",
                    content=ft.Text(ad["cta"], size=12),
                ),
            ],
        ),
        on_click=on_click,
    )


# =============================================================================
