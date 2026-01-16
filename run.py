# run.py (교체용)
import os
import sys
from pathlib import Path
import flet as ft

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui.app import main
from src.constants import ASSETS_DIR


def _is_headless_linux() -> bool:
    if os.name != "posix":
        return False
    return (not os.environ.get("DISPLAY")) and (not os.environ.get("WAYLAND_DISPLAY"))


def _appview(name: str):
    # ft.AppView에 name이 있으면 반환, 없으면 None
    try:
        return getattr(ft.AppView, name)
    except Exception:
        return None


def _pick_view():
    # 현재 설치된 Flet의 AppView 멤버를 기준으로 가장 적절한 걸 선택
    # 우선순위:
    # - headless: WEB_SERVER -> WEB_BROWSER -> (있으면) WEB -> FLET_APP
    # - non-headless: WEB_BROWSER -> WEB_SERVER -> WEB -> FLET_APP
    if _is_headless_linux():
        for n in ("WEB_SERVER", "WEB_BROWSER", "WEB", "FLET_APP"):
            v = _appview(n)
            if v is not None:
                return v
    else:
        for n in ("WEB_BROWSER", "WEB_SERVER", "WEB", "FLET_APP"):
            v = _appview(n)
            if v is not None:
                return v

    # 최후의 fallback: AppView 자체가 예상과 다를 때
    return None

if __name__ == "__main__":
    os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

    host = os.environ.get("FLET_HOST", "0.0.0.0")
    port = int(os.environ.get("FLET_PORT", "8101"))

    print("🚀 Flet 앱 시작...")
    print(f"http://localhost:{port} 에서 접속하세요.")

    view_mode = _pick_view()
    if view_mode is None:
        # 이 경우는 AppView가 특이하게 바뀐 케이스.
        # 일단 view 인자 없이 실행(기본값 사용)하게 처리.
        ft.app(main, host=host, port=port, assets_dir=str(ASSETS_DIR))
    else:
        ft.app(main, host=host, port=port, view=view_mode, assets_dir=str(ASSETS_DIR))