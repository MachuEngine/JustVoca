import flet as ft
import random

# src/constants.py
from pathlib import Path
from src.constants import DUMMY_ADS

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
