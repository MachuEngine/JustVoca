import flet as ft

# =============================================================================
# Flet 0.80+ 호환: 구버전 ft.icons.* 를 계속 쓰기 위한 alias
# =============================================================================
try:
    _ = ft.icons.ABC  # 존재하면 그대로 사용
except Exception:
    try:
        ft.icons = ft.Icons  # 없으면 ft.Icons를 old-style alias로 연결
    except Exception:
        pass

import pandas as pd
import random
import os
import json
import warnings
import tempfile
import hashlib
import secrets
from datetime import datetime
import math

warnings.filterwarnings("ignore")

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
VOCAB_DB = {}
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

# =============================================================================
# 유틸: 로깅/원자적 JSON 저장/비밀번호 해시
# =============================================================================
def log_write(msg: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass


def atomic_write_json(path: str, data):
    """
    JSON 저장 시 파일 깨짐 방지:
    임시파일에 먼저 쓰고 os.replace로 교체(원자적)
    """
    try:
        d = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(d, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=d)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except:
                pass
    except Exception as e:
        log_write(f"atomic_write_json error({path}): {e}")


# ---- password hashing (PBKDF2) ----
_PBKDF2_ITER = 120_000

def hash_password(pw: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", (pw or "").encode("utf-8"), salt, _PBKDF2_ITER)
    return f"pbkdf2${_PBKDF2_ITER}${salt.hex()}${dk.hex()}"


def verify_password(stored: str, pw: str) -> tuple[bool, bool]:
    """
    return (ok, needs_upgrade)
    - needs_upgrade: stored가 평문이어서 로그인 성공 후 해시로 바꿔야 하는 경우
    """
    stored = stored or ""
    pw = pw or ""
    if stored.startswith("pbkdf2$"):
        try:
            _, it_s, salt_hex, hash_hex = stored.split("$", 3)
            it = int(it_s)
            salt = bytes.fromhex(salt_hex)
            dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, it)
            ok = (dk.hex() == hash_hex)
            return ok, False
        except:
            return False, False
    else:
        # legacy plain-text
        return stored == pw, True


def load_system():
    if not os.path.exists(SYSTEM_FILE):
        save_system(DEFAULT_SYSTEM)
        return dict(DEFAULT_SYSTEM)
    try:
        with open(SYSTEM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for k, v in DEFAULT_SYSTEM.items():
            if k not in data:
                data[k] = v

        if "api" not in data:
            data["api"] = dict(DEFAULT_SYSTEM["api"])
        for k, v in DEFAULT_SYSTEM["api"].items():
            if k not in data["api"]:
                data["api"][k] = v

        save_system(data)
        return data
    except:
        save_system(DEFAULT_SYSTEM)
        return dict(DEFAULT_SYSTEM)


def save_system(sysdata):
    try:
        atomic_write_json(SYSTEM_FILE, sysdata)
    except Exception as e:
        log_write(f"save_system error: {e}")


def load_vocab_data():
    """엑셀 파일 로드: sheet_name == 토픽/레벨로 취급"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(current_dir, "data", "vocabulary.xlsx")
    os.makedirs(os.path.join(current_dir, "data"), exist_ok=True)

    if not os.path.exists(excel_path):
        dummy_data = []
        for i in range(1, 21):
            dummy_data.append(
                {
                    "word": f"테스트단어{i}",
                    "mean": "테스트 의미",
                    "ex": f"이것은 예문입니다 {i}",
                    "desc": "설명",
                    "pronunciation": f"[단어{i}]",
                    "image": "📝",
                }
            )
        return {"초급1": dummy_data, "초급2": dummy_data, "중급1": dummy_data}

    try:
        print(f"📂 엑셀 로딩 중... ({excel_path})")
        all_sheets = pd.read_excel(excel_path, sheet_name=None, engine="openpyxl")

        vocab_db = {}
        for sheet_name, df in all_sheets.items():
            df = df.fillna("")
            items = []

            for _, row in df.iterrows():
                cols = row.index.tolist()
                if "단어" not in cols and "word" not in cols:
                    continue

                word_item = {
                    "word": str(row.get("단어", row.get("word", ""))).strip(),
                    "mean": str(row.get("의미", row.get("뜻", row.get("mean", "")))).strip(),
                    "ex": str(row.get("예문", row.get("예문1", row.get("example", "")))).strip(),
                    "desc": str(row.get("설명", row.get("주제", row.get("desc", "")))).strip(),
                    "pronunciation": str(row.get("발음", row.get("pronunciation", ""))).strip(),
                    "image": str(row.get("이미지", row.get("image", "📖"))).strip(),
                }
                if not word_item["pronunciation"] and word_item["word"]:
                    word_item["pronunciation"] = f"[{word_item['word']}]"
                if word_item["word"]:
                    items.append(word_item)

            if items:
                vocab_db[sheet_name] = items
                print(f"✅ [{sheet_name}] 로드 완료 ({len(items)}개)")
        return vocab_db
    except Exception as e:
        print(f"❌ 엑셀 읽기 실패: {e}")
        log_write(f"excel read error: {e}")
        return {}


# --- 사용자 관리 ---
def load_users():
    if not os.path.exists(USERS_FILE):
        # 기본 계정도 해시로 저장(안전)
        default_users = {
            "admin": {
                "pw": hash_password("1111"),
                "name": "관리자",
                "role": "admin",
                "country": "KR",
                "progress": {},
            },
            "teacher": {
                "pw": hash_password("1111"),
                "name": "선생님",
                "role": "teacher",
                "country": "KR",
                "progress": {},
            },
            "student": {
                "pw": hash_password("1111"),
                "name": "학습자",
                "role": "student",
                "country": "KR",
                "progress": {},
            },
        }
        save_users(default_users)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 보정
        for uid, u in data.items():
            if "progress" not in u:
                u["progress"] = {}
            if "country" not in u:
                u["country"] = "KR"
            if "pw" not in u:
                u["pw"] = hash_password("1111")
            # [추가] 사양 반영 필드 보정
            if "email" not in u:
                u["email"] = ""
            if "phone" not in u:
                u["phone"] = ""
            if "phone_verified" not in u:
                u["phone_verified"] = False

        save_users(data)
        return data
    except:
        return {}


def save_users(users_data):
    try:
        atomic_write_json(USERS_FILE, users_data)
    except Exception as e:
        log_write(f"save_users error: {e}")


def register_user(uid, pw, name, email="", phone="", country="KR", role="student", phone_verified=False):
    users = load_users()
    uid = (uid or "").strip()

    if not uid:
        return False, "아이디를 입력해주세요."
    if uid in users:
        return False, "이미 존재하는 아이디입니다."

    users[uid] = {
        "pw": hash_password(pw),
        "name": name,
        "email": email or "",
        "phone": phone or "",
        "phone_verified": bool(phone_verified),
        "role": role,
        "country": country,
        "progress": {},
    }
    save_users(users)
    return True, "회원가입 완료! 로그인해주세요."


def authenticate_user(uid, pw):
    users = load_users()
    if uid in users:
        stored = users[uid].get("pw", "")
        ok, needs_upgrade = verify_password(stored, pw)
        if ok:
            # legacy plain-text -> hash upgrade
            if needs_upgrade:
                users[uid]["pw"] = hash_password(pw)
                save_users(users)

            u = users[uid]
            u["id"] = uid
            if "progress" not in u:
                u["progress"] = {}
            if "country" not in u:
                u["country"] = "KR"
            save_users(users)
            return True, u
    return False, None


def get_user(uid):
    users = load_users()
    return users.get(uid)


def update_user(uid, new_user_obj):
    users = load_users()
    users[uid] = new_user_obj
    save_users(users)


def ensure_progress(user):
    if "progress" not in user:
        user["progress"] = {}
    if "settings" not in user["progress"]:
        user["progress"]["settings"] = {}
    if "goal" not in user["progress"]["settings"]:
        sysdata = load_system()
        user["progress"]["settings"]["goal"] = int(sysdata.get("default_goal", 10))
    if "ui_lang" not in user["progress"]["settings"]:
        user["progress"]["settings"]["ui_lang"] = "ko"

    if "topics" not in user["progress"]:
        user["progress"]["topics"] = {}

    # 마지막 학습 자리 기억(토픽/인덱스)
    if "last_session" not in user["progress"]:
        user["progress"]["last_session"] = {"topic": "", "idx": 0}
    else:
        if "topic" not in user["progress"]["last_session"]:
            user["progress"]["last_session"]["topic"] = ""
        if "idx" not in user["progress"]["last_session"]:
            user["progress"]["last_session"]["idx"] = 0

    # 격려 화면(하루 1회) 플래그
    if "today_flags" not in user["progress"]:
        user["progress"]["today_flags"] = {}
    if "motivate_shown_date" not in user["progress"]["today_flags"]:
        user["progress"]["today_flags"]["motivate_shown_date"] = ""  # "YYYY-MM-DD"

    return user


def ensure_topic_progress(user, topic):
    user = ensure_progress(user)
    topics = user["progress"]["topics"]
    if topic not in topics:
        topics[topic] = {
            "learned": {},
            "stats": {"studied_count": 0, "avg_score": 0.0},
            "wrong_notes": [],
        }
    return user


def update_learned_word(user, topic, word_item, score):
    user = ensure_topic_progress(user, topic)
    t = user["progress"]["topics"][topic]
    learned = t["learned"]

    w = word_item["word"]
    learned[w] = {
        "mean": word_item.get("mean", ""),
        "last_score": int(score),
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    scores = [v.get("last_score", 0) for v in learned.values()]
    t["stats"]["studied_count"] = len(learned)
    t["stats"]["avg_score"] = round(sum(scores) / max(1, len(scores)), 2)
    return user


def update_last_seen_only(user, topic, word_item):
    """이미 learned에 있는 단어도 last_seen은 갱신(점수는 유지)."""
    user = ensure_topic_progress(user, topic)
    t = user["progress"]["topics"][topic]
    learned = t["learned"]
    w = word_item.get("word", "")
    if not w:
        return user
    if w in learned:
        learned[w]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return user


def add_wrong_note(user, topic, q, correct, user_answer):
    user = ensure_topic_progress(user, topic)
    t = user["progress"]["topics"][topic]
    t["wrong_notes"].append(
        {
            "q": q,
            "a": correct,
            "user": user_answer,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return user


def country_label(code: str) -> str:
    mp = {c: n for c, n in COUNTRY_OPTIONS}
    return mp.get(code or "", code or "KR")


VOCAB_DB = load_vocab_data()

# =============================================================================
# 2. 메인 앱 로직
# =============================================================================
def main(page: ft.Page):
    page.title = "한국어 학습 앱"
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # URL 끝에 # 붙는 문제(해시 라우팅) 줄이기: PATH 전략(가능한 버전에서만)
    try:
        page.route_url_strategy = "path"
    except:
        pass

    page.fonts = {
        "Pretendard": "https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"
    }
    page.theme = ft.Theme(font_family="Pretendard")

    sysdata = load_system()

    session = {
        "user": None,
        "topic": "",
        "study_words": [],
        "idx": 0,
        "goal": int(sysdata.get("default_goal", 10)),
        "mask_mode": "none",
        "test_queue": [],
        "test_idx": 0,
        "test_score": 0,
        "is_review": False,  # 복습 플로우 표시용
        "selected_student_id": None,  # teacher 상세 보기용

        # 발음(녹음/결과) 더미 상태
        "pron_state": {
            "recording": False,
            "recorded": False,
            "target_word": "",
            "target_example": "",
            "result_score": None,
            "result_comment": "",
            "detail": [],
        },
        # 오늘 학습 단어 목록
        "today_words": [],
    }

    # =============================================================================
    # (기초) UI 언어팩 구조
    # =============================================================================
    I18N = {
        "ko": {
            "app_title": "한국어 학습",
            "login": "로그인",
            "signup": "회원가입",
            "logout": "로그아웃",
            "save": "저장",
            "home": "홈",
            "level_select": "레벨 선택",
            "settings": "설정",
            "stats": "통계",
        },
        "en": {
            "app_title": "Korean Study",
            "login": "Login",
            "signup": "Sign up",
            "logout": "Logout",
            "save": "Save",
            "home": "Home",
            "level_select": "Levels",
            "settings": "Settings",
            "stats": "Stats",
        },
    }

    def t(key: str) -> str:
        u = session.get("user") or {}
        lang = (u.get("progress", {}).get("settings", {}) or {}).get("ui_lang", "ko")
        return I18N.get(lang, I18N["ko"]).get(key, I18N["ko"].get(key, key))

    # ------------------------------
    # TTS (Web Native)
    # ------------------------------
    def play_tts(text: str):
        try:
            tjson = json.dumps(text)
            page.run_javascript(
                f"""
            try {{
                if (!window.speechSynthesis) return;
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance({tjson});
                u.lang = "ko-KR"; u.rate = 1.0; u.volume = 1.0;
                window.speechSynthesis.speak(u);
            }} catch(e) {{}}
            """
            )
        except:
            pass

    # ------------------------------
    # Pronunciation 평가 (현재 더미)
    # ------------------------------
    def evaluate_pronunciation_dummy(text: str):
        score = random.randint(75, 100)
        if score >= 95:
            comment = "발음이 매우 정확하고 자연스럽습니다."
            tag = "excellent"
        elif score >= 88:
            comment = "전체적으로 좋습니다. 억양을 조금만 더 또렷하게 해보세요."
            tag = "good"
        elif score >= 80:
            comment = "의미 전달은 충분합니다. 받침/연음을 조금 더 신경써보세요."
            tag = "ok"
        else:
            comment = "천천히 또박또박 반복 연습이 필요합니다."
            tag = "need_practice"

        words = [w for w in (text or "").split() if w.strip()]
        detail = []
        for w in words[:12]:
            detail.append({"unit": w, "score": random.randint(max(60, score - 15), min(100, score + 10))})
        return score, comment, tag, detail

    COMMENT_DB = {
        "excellent": [
            "발음이 아주 안정적이에요. 지금 속도로 문장 길이를 조금씩 늘려보세요.",
            "억양이 자연스럽습니다. 오늘 발음은 특히 또렷했어요.",
        ],
        "good": [
            "전반적으로 좋습니다. 문장 끝 억양을 조금 더 또렷하게 해보세요.",
            "발음이 잘 들립니다. 받침이 있는 구간만 한 번 더 반복해보면 더 좋아져요.",
        ],
        "ok": [
            "의미 전달은 충분합니다. 연음이 생기는 구간을 천천히 끊어 연습해보세요.",
            "발음이 조금 흔들리는 부분이 있어요. 단어를 먼저 또박또박 말한 뒤 문장으로 이어보세요.",
        ],
        "need_practice": [
            "천천히 말해도 괜찮아요. 한 어절씩 끊어 연습한 뒤 다시 문장으로 이어보세요.",
            "받침 발음이 불안정합니다. 속도를 낮추고 반복 연습을 권장해요.",
        ],
    }

    def post_process_comment(tag: str, raw_comment: str) -> str:
        pool = COMMENT_DB.get(tag, [])
        if pool:
            return random.choice(pool)
        return raw_comment or "연습을 계속해보세요."

    def show_snack(msg, color="black"):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def go_to(route):
        page.go(route)

    # =============================================================================
    # Signup helpers (중복확인 / 전화 인증: 더미)
    # =============================================================================
    signup_state = {
        "id_checked": False,
        "id_ok": False,
        "sent_code": None,
        "phone_verified": False,
    }

    def check_id_available(uid: str):
        uid = (uid or "").strip()
        if not uid:
            return False, "아이디를 입력해주세요."
        users = load_users()
        if uid in users:
            return False, "이미 존재하는 아이디입니다."
        return True, "사용 가능한 아이디입니다."

    def send_phone_code_dummy(phone: str):
        # 더미: 6자리 코드 생성해서 session에 저장 (실서비스에서는 SMS API로 대체)
        phone = (phone or "").strip()
        if not phone:
            return False, "전화번호를 입력해주세요."
        code = "111111" # 프로토타입 임시 고정 
        #code = f"{random.randint(0, 999999):06d}"
        signup_state["sent_code"] = code
        signup_state["phone_verified"] = False
        # 개발 편의: 로그 남김(원하면 snack으로 코드 노출 가능)
        log_write(f"[dummy sms] phone={phone}, code={code}")
        return True, "인증번호를 전송했습니다. (더미: 111111)"

    def verify_phone_code_dummy(code_in: str):
        code_in = (code_in or "").strip()
        if not code_in:
            return False, "인증번호를 입력해주세요."
        if signup_state.get("sent_code") and code_in == signup_state["sent_code"]:
            signup_state["phone_verified"] = True
            return True, "전화번호 인증이 완료되었습니다."
        return False, "인증번호가 올바르지 않습니다."

    # =============================================================================
    # 공통 모바일 쉘
    # =============================================================================
    def mobile_shell(route: str, body: ft.Control, title: str = "", leading=None, actions=None):
        actions = actions or []
        topbar = None

        if title:
            left = leading if leading else ft.Container(width=40)
            right = ft.Row(actions, spacing=6) if actions else ft.Container(width=40)
            topbar = ft.Container(
                padding=ft.padding.only(left=16, right=16, top=14, bottom=10),
                content=ft.Row(
                    [
                        ft.Container(width=40, content=left),
                        ft.Text(title, size=16, weight="bold", color=COLOR_TEXT_MAIN),
                        ft.Container(width=40, content=right, alignment=ft.Alignment(1, 0)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        shell_content = ft.Column(
            expand=True,
            spacing=0,
            controls=[topbar, ft.Container(expand=True, content=body)] if topbar else [ft.Container(expand=True, content=body)],
        )

        return ft.View(
            route=route,
            bgcolor=COLOR_BG,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    padding=ft.padding.symmetric(vertical=24, horizontal=12),
                    content=ft.Container(
                        width=380,
                        bgcolor="white",
                        border_radius=STYLE_BORDER_RADIUS,
                        shadow=STYLE_CARD_SHADOW,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=shell_content,
                    ),
                )
            ],
        )

    def level_button(title: str, subtitle: str, on_click):
        return ft.Container(
            border_radius=18,
            bgcolor="#f8f9fa",
            padding=14,
            ink=True,
            on_click=on_click,
            border=ft.border.all(1, "#eef1f4"),
            content=ft.Column(
                [
                    ft.Text(title, size=15, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(height=2),
                    ft.Text(subtitle, size=11, color=COLOR_TEXT_DESC),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                border_radius=999,
                                bgcolor="#eef5ff",
                                content=ft.Text("학습하기", size=11, color=COLOR_PRIMARY, weight="bold"),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=0,
            ),
        )

    # =============================================================================
    # 학생용: 상단 정보 바(국가/레벨/토픽/프로필)
    # =============================================================================
    def student_info_bar():
        u = session.get("user")
        if not u:
            return ft.Container(height=0)

        country = country_label(u.get("country", "KR"))
        topic = session.get("topic") or "-"
        level = topic

        return ft.Container(
            padding=ft.padding.only(left=16, right=16, top=10, bottom=8),
            bgcolor="#ffffff",
            border=ft.border.only(bottom=ft.BorderSide(1, "#eef1f4")),
            content=ft.Row(
                [
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        bgcolor="#f8f9fa",
                        border_radius=999,
                        content=ft.Text(f"🌍 {country}", size=11, color=COLOR_TEXT_DESC),
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        bgcolor="#eef5ff",
                        border_radius=999,
                        content=ft.Text(f"📘 레벨: {level}", size=11, color=COLOR_PRIMARY, weight="bold"),
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        bgcolor="#fff9f0",
                        border_radius=999,
                        content=ft.Text(f"🏷 토픽: {topic}", size=11, color=COLOR_SECONDARY, weight="bold"),
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.icons.PERSON, icon_color=COLOR_TEXT_MAIN, on_click=lambda _: go_to("/profile")),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def student_bottom_nav(active: str = "home"):
        def nav_btn(icon, label, route, key):
            is_active = (active == key)
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                border_radius=14,
                bgcolor="#eef5ff" if is_active else "#ffffff",
                ink=True,
                on_click=lambda _: go_to(route),
                content=ft.Row(
                    [
                        ft.Text(icon, size=13),
                        ft.Text(label, size=11, color=COLOR_PRIMARY if is_active else COLOR_TEXT_DESC, weight="bold" if is_active else None),
                    ],
                    spacing=6,
                ),
            )

        return ft.Container(
            padding=ft.padding.only(left=12, right=12, bottom=12, top=10),
            bgcolor="#ffffff",
            border=ft.border.only(top=ft.BorderSide(1, "#eef1f4")),
            content=ft.Row(
                [
                    nav_btn("🏠", t("home"), "/student_home", "home"),
                    nav_btn("🗂", t("level_select"), "/level_select", "level"),
                    nav_btn("⚙️", t("settings"), "/settings", "settings"),
                    nav_btn("📊", t("stats"), "/stats", "stats"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

    # =============================================================================
    # View: Landing
    # =============================================================================
    def view_landing():
        body = ft.Container(
            padding=28,
            content=ft.Column(
                [
                    ft.Container(height=10),
                    ft.Container(
                        width=110,
                        height=110,
                        bgcolor="#f0f6ff",
                        border_radius=26,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("🇰🇷", size=56),
                    ),
                    ft.Container(height=18),
                    ft.Text("한국어 학습", size=28, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text(
                        "단어부터 발음, 진도 관리까지\n쉽고 체계적인 한국어 학습",
                        size=13,
                        color=COLOR_TEXT_DESC,
                        text_align="center",
                    ),
                    ft.Container(height=22),
                    ft.Container(
                        bgcolor="#f8f9fa",
                        border_radius=18,
                        padding=16,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Column(
                            [
                                ft.Row([ft.Text("📘", size=18), ft.Text("단계별 토픽 학습", weight="bold", size=13)], spacing=10),
                                ft.Text("토픽/레벨 기반 단어 DB로 학습", size=11, color=COLOR_TEXT_DESC),
                                ft.Divider(height=18),
                                ft.Row([ft.Text("🎧", size=18), ft.Text("웹 네이티브 TTS", weight="bold", size=13)], spacing=10),
                                ft.Text("단어/문장 듣기 + 연습 흐름", size=11, color=COLOR_TEXT_DESC),
                                ft.Divider(height=18),
                                ft.Row([ft.Text("📊", size=18), ft.Text("진도/오답/복습", weight="bold", size=13)], spacing=10),
                                ft.Text("누적 학습과 복습 대상 자동 추출", size=11, color=COLOR_TEXT_DESC),
                            ],
                            spacing=4,
                        ),
                    ),
                    ft.Container(height=22),
                    ft.ElevatedButton(
                        "학습 시작하기",
                        on_click=lambda _: go_to("/login"),
                        width=320,
                        height=48,
                        style=ft.ButtonStyle(
                            bgcolor=COLOR_PRIMARY,
                            color="white",
                            shape=ft.RoundedRectangleBorder(radius=14),
                        ),
                    ),
                    ft.Container(height=10),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        return mobile_shell("/", body, title="")

    # =============================================================================
    # View: Login 개선 적용(먹통 방지 + Enter 로그인)
    # =============================================================================
    def view_login():
        id_field = ft.TextField(
            label="아이디",
            width=320,
            border_radius=12,
            bgcolor="white",
            text_size=14,
            autofocus=True,
        )
        pw_field = ft.TextField(
            label="비밀번호",
            password=True,
            width=320,
            border_radius=12,
            bgcolor="white",
            text_size=14,
            can_reveal_password=True,
        )

        # (가능한 버전에서만) 모바일 키보드 액션
        try:
            id_field.text_input_action = ft.TextInputAction.NEXT
            pw_field.text_input_action = ft.TextInputAction.DONE
        except Exception:
            pass

        login_btn = ft.ElevatedButton(
            "로그인",
            width=320,
            height=48,
            style=ft.ButtonStyle(
                bgcolor=COLOR_PRIMARY,
                color="white",
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
        )

        def set_login_loading(loading: bool):
            login_btn.disabled = loading
            login_btn.text = "로그인 중..." if loading else "로그인"
            page.update()

        def on_login_click(e=None):
            try:
                if not id_field.value or not pw_field.value:
                    show_snack("아이디와 비밀번호를 입력해주세요.", COLOR_ACCENT)
                    return

                set_login_loading(True)

                ok, user = authenticate_user(id_field.value.strip(), pw_field.value)
                if ok:
                    user = ensure_progress(user)
                    session["user"] = user
                    session["goal"] = int(user["progress"]["settings"].get("goal", sysdata.get("default_goal", 10)))
                    session["is_review"] = False
                    update_user(user["id"], user)

                    show_snack(f"환영합니다, {user['name']}님!", COLOR_PRIMARY)
                    if user["role"] == "student":
                        go_to("/student_home")
                    elif user["role"] == "teacher":
                        go_to("/teacher_dash")
                    else:
                        go_to("/system_dash")
                else:
                    show_snack("로그인 정보가 올바르지 않습니다.", COLOR_ACCENT)

            except Exception as ex:
                log_write(f"login error: {repr(ex)}")
                show_snack("로그인 처리 중 오류가 발생했습니다. app.log를 확인하세요.", COLOR_ACCENT)
            finally:
                try:
                    set_login_loading(False)
                except Exception:
                    pass

        def id_submit(e):
            # 아이디 Enter -> 비번으로 포커스 이동
            try:
                pw_field.focus()
                page.update()
            except Exception:
                pass

        def pw_submit(e):
            # 비번 Enter -> 로그인
            on_login_click()

        id_field.on_submit = id_submit
        pw_field.on_submit = pw_submit
        login_btn.on_click = on_login_click

        body = ft.Container(
            padding=28,
            content=ft.Column(
                [
                    ft.Container(height=14),
                    ft.Text("로그인", size=24, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text("한국어 학습을 시작해보세요", size=12, color=COLOR_TEXT_DESC),
                    ft.Container(height=18),
                    id_field,
                    ft.Container(height=10),
                    pw_field,
                    ft.Container(height=18),
                    login_btn,
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.Text("아직 회원이 아니신가요?", size=11, color=COLOR_TEXT_DESC),
                            ft.TextButton(
                                "회원가입 하기",
                                on_click=lambda _: go_to("/signup"),
                                style=ft.ButtonStyle(
                                    color=COLOR_PRIMARY,
                                    overlay_color="#00000000",
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    ft.Container(height=10),
                    ft.Container(
                        bgcolor="#f8f9fa",
                        border_radius=14,
                        padding=12,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Text(
                            "테스트 계정: student/1111, teacher/1111, admin/1111",
                            size=10,
                            color="#95a5a6",
                        ),
                    ),
                    ft.Container(height=10),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        return mobile_shell("/login", body, title="한국어 학습")

    # =============================================================================
    # View: Signup (국적 필수)
    # =============================================================================
    def view_signup():
        # 입력 필드
        teacher_ck = ft.Checkbox(label="선생님", value=False)

        name_tf = ft.TextField(label="이름", width=320, border_radius=12, bgcolor="white")
        id_tf = ft.TextField(label="아이디", width=230, border_radius=12, bgcolor="white")
        email_tf = ft.TextField(label="이메일", width=320, border_radius=12, bgcolor="white", hint_text="example@email.com")

        pw_tf = ft.TextField(label="비밀번호", password=True, width=320, border_radius=12, bgcolor="white", can_reveal_password=True)
        pw2_tf = ft.TextField(label="비밀번호 확인", password=True, width=320, border_radius=12, bgcolor="white", can_reveal_password=True)

        phone_tf = ft.TextField(label="전화번호", width=230, border_radius=12, bgcolor="white", hint_text="01012345678")
        code_tf = ft.TextField(label="인증번호", width=230, border_radius=12, bgcolor="white", hint_text="6자리 숫자")

        country_dd = ft.Dropdown(
            label="국적",
            width=320,
            value="KR",
            options=[ft.dropdown.Option(code, name) for code, name in COUNTRY_OPTIONS],
        )

        # 상태 텍스트(사양상 알림용)
        id_status = ft.Text("", size=11, color=COLOR_TEXT_DESC)
        phone_status = ft.Text("", size=11, color=COLOR_TEXT_DESC)

        # 버튼
        btn_check_id = ft.ElevatedButton("중복확인", height=44)
        btn_send = ft.ElevatedButton("인증하기", height=44)
        btn_verify = ft.ElevatedButton("확인", height=44)

        signup_btn = ft.ElevatedButton(
            "회원가입",
            width=320,
            height=48,
            style=ft.ButtonStyle(
                bgcolor=COLOR_PRIMARY,
                color="white",
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
            disabled=True,  # 인증/중복확인 전에는 비활성
        )

        def refresh_signup_btn():
            # 아이디 중복확인 통과 + 전화 인증 완료 + 필수값 OK + pw 일치
            must_ok = (
                signup_state.get("id_ok") is True
                and signup_state.get("phone_verified") is True
                and bool(name_tf.value)
                and bool(id_tf.value)
                and bool(email_tf.value)
                and bool(pw_tf.value)
                and bool(pw2_tf.value)
                and (pw_tf.value == pw2_tf.value)
                and bool(country_dd.value)
                and bool(phone_tf.value)
            )
            signup_btn.disabled = not must_ok
            page.update()

        def on_check_id(e=None):
            ok, msg = check_id_available(id_tf.value)
            signup_state["id_checked"] = True
            signup_state["id_ok"] = ok
            id_status.value = msg
            id_status.color = COLOR_PRIMARY if ok else COLOR_ACCENT
            refresh_signup_btn()

        def on_send_code(e=None):
            ok, msg = send_phone_code_dummy(phone_tf.value)
            phone_status.value = msg
            phone_status.color = COLOR_PRIMARY if ok else COLOR_ACCENT
            refresh_signup_btn()
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)

        def on_verify_code(e=None):
            ok, msg = verify_phone_code_dummy(code_tf.value)
            phone_status.value = msg
            phone_status.color = COLOR_PRIMARY if ok else COLOR_ACCENT
            refresh_signup_btn()
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)

        def on_signup(e=None):
            # 최종 검증
            if pw_tf.value != pw2_tf.value:
                show_snack("비밀번호가 일치하지 않습니다.", COLOR_ACCENT)
                return
            if not signup_state.get("id_ok"):
                show_snack("아이디 중복확인을 해주세요.", COLOR_ACCENT)
                return
            if not signup_state.get("phone_verified"):
                show_snack("전화번호 인증을 완료해주세요.", COLOR_ACCENT)
                return

            role = "teacher" if teacher_ck.value else "student"
            ok, msg = register_user(
                uid=id_tf.value,
                pw=pw_tf.value,
                name=name_tf.value,
                email=email_tf.value,
                phone=phone_tf.value,
                country=country_dd.value,
                role=role,
                phone_verified=True,
            )
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)
            if ok:
                # 상태 초기화(선택)
                signup_state["id_checked"] = False
                signup_state["id_ok"] = False
                signup_state["sent_code"] = None
                signup_state["phone_verified"] = False
                go_to("/login")

        # 이벤트 연결
        btn_check_id.on_click = on_check_id
        btn_send.on_click = on_send_code
        btn_verify.on_click = on_verify_code
        signup_btn.on_click = on_signup

        # 입력 바뀔 때 가입 버튼 상태 갱신
        for tf in [name_tf, id_tf, email_tf, pw_tf, pw2_tf, phone_tf, code_tf]:
            tf.on_change = lambda e: refresh_signup_btn()
        country_dd.on_change = lambda e: refresh_signup_btn()
        teacher_ck.on_change = lambda e: refresh_signup_btn()

        body = ft.Container(
            expand=True,
            padding=24,
            content=ft.Column(
                [
                    ft.Text("회원가입", size=22, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text("한국어 학습을 시작해보세요", size=12, color=COLOR_TEXT_DESC),
                    ft.Container(height=8),
                    teacher_ck,
                    ft.Container(height=10),

                    name_tf,
                    ft.Container(height=10),

                    ft.Row([id_tf, btn_check_id], spacing=10),
                    id_status,
                    ft.Container(height=6),

                    email_tf,
                    ft.Container(height=10),

                    pw_tf,
                    ft.Container(height=10),
                    pw2_tf,
                    ft.Container(height=10),

                    ft.Row([phone_tf, btn_send], spacing=10),
                    ft.Container(height=6),
                    ft.Row([code_tf, btn_verify], spacing=10),
                    phone_status,
                    ft.Container(height=12),

                    country_dd,
                    ft.Container(height=18),

                    signup_btn,
                    ft.Container(height=10),

                    ft.Row(
                        [
                            ft.Text("이미 계정이 있으신가요?", size=11, color=COLOR_TEXT_DESC),
                            ft.TextButton("로그인", on_click=lambda _: go_to("/login")),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll="auto",
                expand=True,
            ),
        )

        return mobile_shell(
            "/signup",
            body,
            title="회원가입",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/login")),
        )


    # =============================================================================
    # View: Profile
    # =============================================================================
    def view_profile():
        u = session.get("user")
        if not u:
            return mobile_shell("/profile", ft.Text("로그인이 필요합니다."), title="프로필")

        u = get_user(u["id"]) or u
        u = ensure_progress(u)

        country_dd = ft.Dropdown(
            label="국적",
            width=320,
            value=u.get("country", "KR"),
            options=[ft.dropdown.Option(code, name) for code, name in COUNTRY_OPTIONS],
        )
        ui_lang_dd = ft.Dropdown(
            label="UI 언어(추후 다국어팩)",
            width=320,
            value=u["progress"]["settings"].get("ui_lang", "ko"),
            options=[ft.dropdown.Option(code, label) for code, label in UI_LANG_OPTIONS],
        )

        def save_profile(e=None):
            u["country"] = country_dd.value or "KR"
            u["progress"]["settings"]["ui_lang"] = ui_lang_dd.value or "ko"
            update_user(u["id"], u)
            session["user"] = u
            show_snack("프로필이 저장되었습니다.", COLOR_PRIMARY)

        def logout(e=None):
            session["user"] = None
            session["is_review"] = False
            show_snack("로그아웃 되었습니다.", COLOR_TEXT_MAIN)
            go_to("/login")

        body = ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Text("내 프로필", size=18, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(height=8),
                    ft.Container(
                        bgcolor="#f8f9fa",
                        border_radius=18,
                        padding=16,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Column(
                            [
                                ft.Text(f"이름: {u.get('name','')}", size=13, color=COLOR_TEXT_MAIN),
                                ft.Text(f"아이디: {u.get('id','')}", size=12, color=COLOR_TEXT_DESC),
                                ft.Text(f"권한: {u.get('role','')}", size=12, color=COLOR_TEXT_DESC),
                            ],
                            spacing=4,
                        ),
                    ),
                    ft.Container(height=12),
                    country_dd,
                    ft.Container(height=10),
                    ui_lang_dd,
                    ft.Container(height=14),
                    ft.ElevatedButton("저장", on_click=save_profile, bgcolor=COLOR_PRIMARY, color="white", width=320),
                    ft.Container(height=6),
                    ft.OutlinedButton("로그아웃", on_click=logout, width=320),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        return mobile_shell(
            "/profile",
            body,
            title="프로필",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")),
        )

    # =============================================================================
    # View: Settings (학생 설정)
    # =============================================================================
    def view_settings():
        u = session.get("user")
        if not u:
            return mobile_shell("/settings", ft.Text("로그인이 필요합니다."), title="설정")

        u = get_user(u["id"]) or u
        u = ensure_progress(u)

        goal_field = ft.TextField(
            label="오늘 목표(단어 수)",
            value=str(u["progress"]["settings"].get("goal", sysdata.get("default_goal", 10))),
            width=320,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=12,
        )

        review_thr = int(load_system().get("review_threshold", 85))
        info = ft.Text(f"복습 기준: {review_thr}점 미만(시스템 설정)", size=11, color=COLOR_TEXT_DESC)

        def save_settings(e=None):
            try:
                g = int(goal_field.value)
                g = max(1, min(100, g))
            except:
                g = int(sysdata.get("default_goal", 10))
            u["progress"]["settings"]["goal"] = g
            update_user(u["id"], u)
            session["goal"] = g
            session["user"] = u
            show_snack("설정이 저장되었습니다.", COLOR_PRIMARY)

        def logout(e=None):
            session["user"] = None
            session["is_review"] = False
            show_snack("로그아웃 되었습니다.", COLOR_TEXT_MAIN)
            go_to("/login")

        body = ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Text("설정", size=18, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(height=10),
                    goal_field,
                    ft.Container(height=8),
                    info,
                    ft.Container(height=14),
                    ft.ElevatedButton("저장", on_click=save_settings, bgcolor=COLOR_PRIMARY, color="white", width=320),
                    ft.Container(height=8),
                    ft.OutlinedButton("로그아웃", on_click=logout, width=320),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        shell_body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(expand=True, content=body),
                student_bottom_nav(active="settings"),
            ],
        )
        return mobile_shell(
            "/settings",
            shell_body,
            title="설정",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")),
        )

    # =============================================================================
    # View: Stats (학생 통계 + 오답/누적/복습 진입)
    # =============================================================================
    def view_stats():
        u = session.get("user")
        if not u:
            return mobile_shell("/stats", ft.Text("로그인이 필요합니다."), title="통계")

        u = get_user(u["id"]) or u
        u = ensure_progress(u)

        topics = u["progress"]["topics"]
        total_learned = sum(len(t.get("learned", {})) for t in topics.values())
        wrong_cnt = sum(len(t.get("wrong_notes", [])) for t in topics.values())
        avgs = [t.get("stats", {}).get("avg_score", 0) for t in topics.values() if t.get("learned")]
        avg_score = round(sum(avgs) / max(1, len(avgs)), 2) if avgs else 0.0

        cards = [
            ft.Container(
                expand=True,
                bgcolor="#f8f9fa",
                border_radius=18,
                padding=14,
                border=ft.border.all(1, "#eef1f4"),
                content=ft.Column(
                    [
                        ft.Text("누적 학습", size=11, color=COLOR_TEXT_DESC),
                        ft.Text(str(total_learned), size=22, weight="bold", color=COLOR_PRIMARY),
                    ],
                    spacing=2,
                ),
            ),
            ft.Container(
                expand=True,
                bgcolor="#f8f9fa",
                border_radius=18,
                padding=14,
                border=ft.border.all(1, "#eef1f4"),
                content=ft.Column(
                    [
                        ft.Text("평균 점수", size=11, color=COLOR_TEXT_DESC),
                        ft.Text(str(avg_score), size=22, weight="bold", color=COLOR_TEXT_MAIN),
                    ],
                    spacing=2,
                ),
            ),
            ft.Container(
                expand=True,
                bgcolor="#f8f9fa",
                border_radius=18,
                padding=14,
                border=ft.border.all(1, "#eef1f4"),
                content=ft.Column(
                    [
                        ft.Text("오답", size=11, color=COLOR_TEXT_DESC),
                        ft.Text(str(wrong_cnt), size=22, weight="bold", color=COLOR_ACCENT),
                    ],
                    spacing=2,
                ),
            ),
        ]

        topic_rows = []
        for tp in sorted(VOCAB_DB.keys()):
            tpdata = topics.get(tp, {})
            studied = len(tpdata.get("learned", {}))
            avg = tpdata.get("stats", {}).get("avg_score", 0.0)
            wcnt = len(tpdata.get("wrong_notes", []))
            topic_rows.append(
                ft.Container(
                    bgcolor="white",
                    border_radius=16,
                    padding=12,
                    border=ft.border.all(1, "#eef1f4"),
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(tp, size=13, weight="bold", color=COLOR_TEXT_MAIN),
                                    ft.Text(f"누적 {studied} · 평균 {avg} · 오답 {wcnt}", size=11, color=COLOR_TEXT_DESC),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.icons.CHEVRON_RIGHT, color="#bdc3c7"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ink=True,
                    on_click=lambda e, tpn=tp: (session.update({"topic": tpn}), go_to("/cumulative")),
                )
            )

        body = ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Row(cards, spacing=10),
                    ft.Container(height=14),
                    ft.Row(
                        [
                            ft.ElevatedButton("누적", on_click=lambda _: go_to("/cumulative"), bgcolor=COLOR_PRIMARY, color="white", expand=True),
                            ft.ElevatedButton("오답노트", on_click=lambda _: go_to("/wrong_notes"), bgcolor=COLOR_ACCENT, color="white", expand=True),
                        ],
                        spacing=10,
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton("복습", on_click=lambda _: go_to("/review"), bgcolor=COLOR_TEXT_MAIN, color="white", width=320),
                    ft.Container(height=14),
                    ft.Text("토픽별 보기", size=14, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(height=8),
                    ft.Column(topic_rows, spacing=10, scroll="auto"),
                ],
                spacing=0,
            ),
        )

        shell_body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(expand=True, content=body),
                student_bottom_nav(active="stats"),
            ],
        )
        return mobile_shell(
            "/stats",
            shell_body,
            title="통계",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")),
        )

    # =============================================================================
    # View: Student Home
    # =============================================================================
    def view_student_home():
        user = session["user"]
        user = ensure_progress(user)

        last = user["progress"].get("last_session", {"topic": "", "idx": 0})
        last_topic = last.get("topic") or ""
        last_idx = int(last.get("idx", 0) or 0)

        def continue_last(e=None):
            if not last_topic or last_topic not in VOCAB_DB:
                show_snack("이어서 학습할 기록이 없습니다.", COLOR_ACCENT)
                return
            start_study(last_topic, resume=True)

        topics = sorted(list(VOCAB_DB.keys()))

        def start_study(topic_name, resume=False):
            if topic_name not in VOCAB_DB:
                show_snack("아직 준비 중인 토픽입니다.", COLOR_ACCENT)
                return

            all_words = VOCAB_DB[topic_name]
            goal = int(user["progress"]["settings"].get("goal", session["goal"]))
            pick = all_words[:goal] if len(all_words) >= goal else all_words[:]

            session["today_words"] = pick[:]
            session["is_review"] = False

            if resume:
                idx = max(0, min(last_idx, max(0, len(pick) - 1)))
            else:
                idx = 0

            session.update({"topic": topic_name, "study_words": pick, "idx": idx})

            user2 = get_user(user["id"]) or user
            user2 = ensure_progress(user2)
            user2["progress"]["last_session"] = {"topic": topic_name, "idx": idx}
            update_user(user2["id"], user2)
            session["user"] = user2

            go_to("/study")

        user2 = get_user(user["id"]) or user
        user2 = ensure_progress(user2)
        topics_prog = user2["progress"]["topics"]
        total_learned = sum(len(t.get("learned", {})) for t in topics_prog.values())
        wrong_cnt = sum(len(t.get("wrong_notes", [])) for t in topics_prog.values())

        level_cards = []
        for tp in topics:
            tpdata = topics_prog.get(tp, {})
            studied = len(tpdata.get("learned", {}))
            avg = tpdata.get("stats", {}).get("avg_score", 0.0)
            level_cards.append(
                level_button(
                    tp,
                    f"누적 {studied}개 · 평균 {avg}",
                    on_click=lambda e, tpn=tp: start_study(tpn, resume=False),
                )
            )
        if not level_cards:
            level_cards = [ft.Text("엑셀 데이터가 없습니다.", color=COLOR_TEXT_DESC)]

        grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=175,
            child_aspect_ratio=1.10,
            spacing=12,
            run_spacing=12,
            controls=level_cards,
        )

        continue_btn = ft.Container(height=0)
        if last_topic and last_topic in VOCAB_DB:
            continue_btn = ft.Container(
                bgcolor="#eef5ff",
                border_radius=18,
                padding=14,
                border=ft.border.all(1, "#dbeafe"),
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("이어서 학습하기", size=12, weight="bold", color=COLOR_PRIMARY),
                                ft.Text(f"{last_topic} · {last_idx+1}번째 단어부터", size=11, color=COLOR_TEXT_DESC),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.ElevatedButton("계속", on_click=continue_last, bgcolor=COLOR_PRIMARY, color="white"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    padding=ft.padding.only(left=20, right=20, top=14, bottom=12),
                    content=ft.Column(
                        [
                            ft.Text(f"안녕하세요, {user['name']}님", size=18, weight="bold", color=COLOR_TEXT_MAIN),
                            ft.Text("오늘 공부할 레벨(토픽)을 선택하세요.", size=12, color=COLOR_TEXT_DESC),
                            ft.Container(height=12),
                            ft.Row(
                                [
                                    ft.Container(
                                        expand=True,
                                        bgcolor="#f8f9fa",
                                        border_radius=18,
                                        padding=14,
                                        border=ft.border.all(1, "#eef1f4"),
                                        content=ft.Column(
                                            [
                                                ft.Text("누적 학습", size=11, color=COLOR_TEXT_DESC),
                                                ft.Text(str(total_learned), size=20, weight="bold", color=COLOR_PRIMARY),
                                            ],
                                            spacing=2,
                                        ),
                                    ),
                                    ft.Container(
                                        expand=True,
                                        bgcolor="#f8f9fa",
                                        border_radius=18,
                                        padding=14,
                                        border=ft.border.all(1, "#eef1f4"),
                                        content=ft.Column(
                                            [
                                                ft.Text("오답", size=11, color=COLOR_TEXT_DESC),
                                                ft.Text(str(wrong_cnt), size=20, weight="bold", color=COLOR_ACCENT),
                                            ],
                                            spacing=2,
                                        ),
                                    ),
                                ],
                                spacing=10,
                            ),
                            ft.Container(height=12),
                            continue_btn,
                        ],
                        spacing=0,
                    ),
                ),
                ft.Container(
                    expand=True,
                    padding=ft.padding.only(left=20, right=20, top=6, bottom=6),
                    content=grid,
                ),
                student_bottom_nav(active="home"),
            ],
        )

        return mobile_shell(
            "/student_home",
            body,
            title="학습 홈",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/login")),
            actions=[],
        )

    # =============================================================================
    # View: Level Select
    # =============================================================================
    def view_level_select():
        user = session["user"]
        user = ensure_progress(user)

        topics = sorted(list(VOCAB_DB.keys()))

        def start_study(topic_name):
            if topic_name not in VOCAB_DB:
                show_snack("아직 준비 중인 토픽입니다.", COLOR_ACCENT)
                return
            all_words = VOCAB_DB[topic_name]
            goal = int(user["progress"]["settings"].get("goal", session["goal"]))
            pick = all_words[:goal] if len(all_words) >= goal else all_words[:]
            session["today_words"] = pick[:]
            session["is_review"] = False
            session.update({"topic": topic_name, "study_words": pick, "idx": 0})

            user2 = get_user(user["id"]) or user
            user2 = ensure_progress(user2)
            user2["progress"]["last_session"] = {"topic": topic_name, "idx": 0}
            update_user(user2["id"], user2)
            session["user"] = user2

            go_to("/study")

        user2 = get_user(user["id"]) or user
        user2 = ensure_progress(user2)
        topics_prog = user2["progress"]["topics"]

        level_cards = []
        for tp in topics:
            tpdata = topics_prog.get(tp, {})
            studied = len(tpdata.get("learned", {}))
            avg = tpdata.get("stats", {}).get("avg_score", 0.0)
            level_cards.append(level_button(tp, f"누적 {studied}개 · 평균 {avg}", on_click=lambda e, tpn=tp: start_study(tpn)))

        grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=175,
            child_aspect_ratio=1.10,
            spacing=12,
            run_spacing=12,
            controls=level_cards if level_cards else [ft.Text("데이터 없음")],
        )

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=ft.padding.only(left=20, right=20, top=14, bottom=10),
                    content=grid,
                ),
                student_bottom_nav(active="level"),
            ],
        )

        return mobile_shell(
            "/level_select",
            body,
            title="레벨 선택",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")),
        )

    # =============================================================================
    # View: Motivate (절반 지점 격려 화면)
    # =============================================================================
    def view_motivate():
        user = session.get("user")
        name = user.get("name", "") if user else ""
        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=24,
                    content=ft.Column(
                        [
                            ft.Container(height=10),
                            ft.Text("잘하고 있어요 🙌", size=22, weight="bold", color=COLOR_PRIMARY),
                            ft.Container(height=10),
                            ft.Text(f"{name}님, 오늘 목표의 절반을 채웠어요.\n조금만 더 힘내서 마무리해봐요!", size=13, color=COLOR_TEXT_DESC, text_align="center"),
                            ft.Container(height=18),
                            ft.ElevatedButton(
                                "이어서 학습하기",
                                on_click=lambda _: go_to("/study"),
                                bgcolor=COLOR_PRIMARY,
                                color="white",
                                width=320,
                                height=46,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ),
                student_bottom_nav(active="home"),
            ],
        )
        return mobile_shell(
            "/motivate",
            body,
            title="격려",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/study")),
        )

    # =============================================================================
    # View: Study
    # =============================================================================
    def view_study():
        words = session.get("study_words", [])
        topic = session.get("topic", "")
        if not words:
            body = ft.Container(
                padding=24,
                content=ft.Column(
                    [
                        ft.Text("학습할 데이터가 없습니다.", size=14, color=COLOR_TEXT_DESC),
                        ft.Container(height=10),
                        ft.ElevatedButton("홈으로", on_click=lambda _: go_to("/student_home"), bgcolor=COLOR_PRIMARY, color="white"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            return mobile_shell("/study", body, title="학습", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")))

        class StudyState:
            idx = session.get("idx", 0)
            is_front = True

        st = StudyState()
        total = len(words)

        status_text = ft.Text("", size=11, color="#95a5a6")

        def persist_position():
            user = get_user(session["user"]["id"]) or session["user"]
            user = ensure_progress(user)
            user["progress"]["last_session"] = {"topic": topic, "idx": st.idx}
            update_user(user["id"], user)
            session["user"] = user

        def mark_seen_default(word_item):
            user = get_user(session["user"]["id"]) or session["user"]
            user = ensure_progress(user)
            user = ensure_topic_progress(user, topic)
            tpdata = user["progress"]["topics"].get(topic, {})
            learned = tpdata.get("learned", {})

            if word_item["word"] not in learned:
                user = update_learned_word(user, topic, word_item, 90)
            else:
                user = update_last_seen_only(user, topic, word_item)

            update_user(user["id"], user)
            session["user"] = user

        def reset_pron_state_on_move():
            session["pron_state"]["recording"] = False
            session["pron_state"]["recorded"] = False
            status_text.value = ""

        def maybe_motivate(new_idx):
            user = get_user(session["user"]["id"]) or session["user"]
            user = ensure_progress(user)

            today = datetime.now().strftime("%Y-%m-%d")
            shown_date = user["progress"]["today_flags"].get("motivate_shown_date", "")

            half_idx = max(0, (total // 2) - 1)
            if (shown_date != today) and new_idx >= half_idx:
                user["progress"]["today_flags"]["motivate_shown_date"] = today
                update_user(user["id"], user)
                session["user"] = user
                go_to("/motivate")

        def change_card(delta):
            try:
                mark_seen_default(words[st.idx])
            except:
                pass

            new_idx = st.idx + delta
            if 0 <= new_idx < total:
                st.idx = new_idx
                session["idx"] = new_idx
                st.is_front = True
                reset_pron_state_on_move()
                persist_position()
                update_view()
                if delta > 0:
                    maybe_motivate(new_idx)
            elif new_idx >= total:
                persist_position()
                go_to("/review_start")

        def flip_card(e=None):
            st.is_front = not st.is_front
            update_view()

        def start_recording():
            session["pron_state"]["recording"] = True
            session["pron_state"]["recorded"] = False
            status_text.value = "🎙 문장 녹음 중... (더미)"
            page.update()

        def stop_recording():
            session["pron_state"]["recording"] = False
            session["pron_state"]["recorded"] = True
            status_text.value = "⏹ 녹음 종료 (더미). 결과 보기를 눌러주세요."
            page.update()

        def open_pron_result_for_current():
            w = words[st.idx]
            session["pron_state"]["target_word"] = w.get("word", "")
            session["pron_state"]["target_example"] = w.get("ex", "")
            session["pron_state"]["result_score"] = None
            session["pron_state"]["result_comment"] = ""
            session["pron_state"]["detail"] = []
            go_to("/pron_result")

        def eojeol_buttons(example: str):
            parts = [p for p in (example or "").split() if p.strip()]
            if not parts:
                return ft.Container(height=0)
            btns = []
            for p in parts[:12]:
                btns.append(ft.OutlinedButton(p, on_click=lambda e, t=p: play_tts(t), height=32))
            return ft.Row(
                controls=btns,
                wrap=True,
                spacing=6,
                run_spacing=8,
            )

        def render_card_content():
            w = words[st.idx]

            right_badges = []
            if session.get("is_review"):
                right_badges.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        bgcolor="#fff5f5",
                        border_radius=999,
                        content=ft.Text("복습중", size=11, color=COLOR_ACCENT, weight="bold"),
                    )
                )

            header = ft.Row(
                [
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        bgcolor="#f8f9fa",
                        border_radius=999,
                        content=ft.Text(f"{topic}", size=11, color=COLOR_TEXT_DESC),
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        bgcolor="#f8f9fa",
                        border_radius=999,
                        content=ft.Text(f"{st.idx + 1}/{total}", size=11, color=COLOR_TEXT_DESC),
                    ),
                    ft.Container(expand=True),
                    *right_badges,
                    ft.IconButton(icon=ft.icons.HOME, icon_color=COLOR_TEXT_MAIN, on_click=lambda _: go_to("/level_select")),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

            if st.is_front:
                return ft.Column(
                    [
                        header,
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Text(w.get("image", "📖"), size=54),
                            width=110,
                            height=110,
                            bgcolor="#f8f9fa",
                            border_radius=55,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Container(height=12),
                        ft.Text(w["word"], size=34, weight="bold", color=COLOR_TEXT_MAIN),
                        ft.Text(w.get("pronunciation", ""), size=14, color=COLOR_SECONDARY),
                        ft.Container(height=14),
                        ft.Container(
                            bgcolor="#fff9f0",
                            padding=14,
                            border_radius=14,
                            content=ft.Column(
                                [
                                    ft.Text(w.get("mean", ""), size=14, weight="bold", color=COLOR_TEXT_MAIN, text_align="center"),
                                    ft.Text(w.get("desc", ""), size=11, color="#8a7e6a", italic=True, text_align="center"),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                            ),
                        ),
                        ft.Container(height=10),
                        ft.Row(
                            [
                                ft.ElevatedButton("🔊 단어 듣기", on_click=lambda e: play_tts(w["word"]), expand=True, bgcolor=COLOR_PRIMARY, color="white"),
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=8),
                        ft.Row(
                            [
                                ft.OutlinedButton("뒷면 보기", on_click=lambda _: flip_card(), expand=True),
                                ft.ElevatedButton("다음 ▶", on_click=lambda e: change_card(1), expand=True, bgcolor=COLOR_TEXT_MAIN, color="white"),
                            ],
                            spacing=10,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            else:
                is_rec = bool(session["pron_state"].get("recording"))
                is_recorded = bool(session["pron_state"].get("recorded"))

                if not is_rec and not is_recorded:
                    rec_btn = ft.ElevatedButton("🎙 문장 녹음", on_click=lambda e: start_recording(), expand=True, bgcolor=COLOR_ACCENT, color="white")
                elif is_rec and not is_recorded:
                    rec_btn = ft.ElevatedButton("⏹ 중지", on_click=lambda e: stop_recording(), expand=True, bgcolor=COLOR_TEXT_MAIN, color="white")
                else:
                    rec_btn = ft.ElevatedButton("✅ 결과 보기", on_click=lambda e: open_pron_result_for_current(), expand=True, bgcolor=COLOR_EVAL, color="white")

                return ft.Column(
                    [
                        header,
                        ft.Container(
                            bgcolor="#eef5ff",
                            padding=14,
                            border_radius=16,
                            margin=ft.margin.symmetric(vertical=12),
                            border=ft.border.only(left=ft.BorderSide(5, COLOR_PRIMARY)),
                            content=ft.Column(
                                [
                                    ft.Text("[Example]", size=11, color=COLOR_PRIMARY, weight="bold"),
                                    ft.Text(w.get("ex", ""), size=14, color=COLOR_TEXT_MAIN),
                                    ft.Container(height=8),
                                    ft.Text("어절별 듣기", size=11, color=COLOR_TEXT_DESC),
                                    eojeol_buttons(w.get("ex", "")),
                                ],
                                spacing=6,
                            ),
                        ),
                        ft.Row(
                            [
                                ft.ElevatedButton("▶ 문장 듣기", on_click=lambda e: play_tts(w.get("ex", "")), expand=True, bgcolor=COLOR_PRIMARY, color="white"),
                                rec_btn,
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=8),
                        status_text,
                        ft.Container(expand=True),
                        ft.Row(
                            [
                                ft.OutlinedButton("앞면 보기", on_click=lambda _: flip_card(), expand=True),
                                ft.OutlinedButton("이전", on_click=lambda e: change_card(-1), expand=True),
                                ft.OutlinedButton("다음", on_click=lambda e: change_card(1), expand=True),
                            ],
                            spacing=10,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )

        card_container = ft.Container(
            content=render_card_content(),
            width=340,
            bgcolor=COLOR_CARD_BG,
            border_radius=24,
            padding=20,
            shadow=ft.BoxShadow(blur_radius=30, color="#14000000", offset=ft.Offset(0, 14)),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: flip_card(e),
        )

        def update_view():
            if card_container.page:
                card_container.content = render_card_content()
                card_container.update()

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Container(height=4),
                            card_container,
                            ft.Container(height=10),
                            ft.Text("카드를 터치하거나 버튼으로 앞/뒤를 전환하세요", color="#bdc3c7", size=11),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll="auto",
                        expand=True,
                    ),
                ),
                student_bottom_nav(active="home"),
            ],
        )

        return mobile_shell(
            "/study",
            body,
            title="단어 학습",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/level_select")),
        )

    # =============================================================================
    # View: Pronunciation Result
    # =============================================================================
    def view_pron_result():
        ps = session.get("pron_state", {})
        word = ps.get("target_word", "")
        ex = ps.get("target_example", "")
        recorded = bool(ps.get("recorded", False))

        score_text = ft.Text("", size=22, weight="bold", color=COLOR_EVAL)
        comment_text = ft.Text("", size=12, color=COLOR_TEXT_DESC, text_align="center")
        detail_col = ft.Column(scroll="auto", expand=True, spacing=6)

        result_box = ft.Container(
            visible=False,
            bgcolor="#f8f9fa",
            border_radius=18,
            padding=16,
            border=ft.border.all(1, "#eef1f4"),
            content=ft.Column(
                [
                    ft.Text("평가 결과", size=13, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(height=8),
                    ft.Row(
                        [
                            ft.Container(
                                width=88,
                                height=88,
                                border_radius=44,
                                border=ft.border.all(5, COLOR_EVAL),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    [score_text, ft.Text("점수", size=10, color="grey")],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=0,
                                ),
                            ),
                            ft.Container(expand=True),
                        ]
                    ),
                    ft.Container(height=6),
                    comment_text,
                    ft.Divider(height=18),
                    ft.Text("어절별 점수(더미)", size=11, color=COLOR_TEXT_DESC),
                    ft.Container(height=6),
                    ft.Container(content=detail_col, height=220),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        def run_ai_eval(e=None):
            if not recorded:
                show_snack("먼저 문장 녹음을 완료해 주세요. (현재는 더미)", COLOR_ACCENT)
                return

            score, raw_comment, tag, detail = evaluate_pronunciation_dummy(ex or word)
            comment = post_process_comment(tag, raw_comment)

            score_text.value = str(score)
            comment_text.value = comment

            detail_col.controls = []
            for d in detail:
                unit = d.get("unit", "")
                sc = int(d.get("score", 0))
                detail_col.controls.append(
                    ft.Container(
                        bgcolor="white",
                        border_radius=14,
                        padding=10,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Row(
                            [
                                ft.Text(unit, size=12, color=COLOR_TEXT_MAIN),
                                ft.Text(f"{sc}점", size=12, weight="bold", color=COLOR_EVAL if sc >= 85 else COLOR_ACCENT),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    )
                )

            result_box.visible = True
            page.update()

            # 학습 로그(해당 단어 점수 저장)
            try:
                topic = session.get("topic", "")
                wlist = session.get("study_words", [])
                found = None
                for it in wlist:
                    if it.get("word") == word:
                        found = it
                        break
                if found and topic:
                    user = get_user(session["user"]["id"]) or session["user"]
                    user = update_learned_word(user, topic, found, score)
                    update_user(user["id"], user)
                    session["user"] = user
            except Exception as ex2:
                log_write(f"persist pron score error: {ex2}")

        def back_to_study(e=None):
            session["pron_state"]["recording"] = False
            session["pron_state"]["recorded"] = False
            go_to("/study")

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Text("발음 녹음 결과", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                            ft.Container(height=10),
                            ft.Container(
                                bgcolor="white",
                                border_radius=18,
                                padding=14,
                                border=ft.border.all(1, "#eef1f4"),
                                content=ft.Column(
                                    [
                                        ft.Text(word, size=20, weight="bold", color=COLOR_TEXT_MAIN),
                                        ft.Text(ex, size=13, color=COLOR_TEXT_DESC),
                                        ft.Container(height=8),
                                        ft.Row(
                                            [
                                                ft.ElevatedButton("▶ 문장 듣기", on_click=lambda _: play_tts(ex), bgcolor=COLOR_PRIMARY, color="white", expand=True),
                                                ft.ElevatedButton("AI 평가", on_click=run_ai_eval, bgcolor=COLOR_ACCENT, color="white", expand=True),
                                            ],
                                            spacing=10,
                                        ),
                                        ft.Container(height=10),
                                        result_box,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                            ft.Container(height=12),
                            ft.ElevatedButton("학습 계속하기", on_click=back_to_study, bgcolor=COLOR_TEXT_MAIN, color="white", width=320),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                student_bottom_nav(active="home"),
            ],
        )

        return mobile_shell(
            "/pron_result",
            body,
            title="발음 결과",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/study")),
        )
    

    def make_test_queue(topic: str, today_words: list[dict], n_choices: int = 4) -> list[dict]:
        """
        사양서(p33~35)용 연습문제 생성:
        - 질문: 뜻(mean) 기반
        - 보기: 4개(정답 1 + 오답 3)
        - 오답은 누적해서 빨강 유지(리트라이 강제)
        """
        # distractor 풀: 같은 토픽 전체 단어 우선, 부족하면 오늘 단어
        topic_pool = VOCAB_DB.get(topic, []) or []
        pool_words = [it.get("word", "").strip() for it in topic_pool if it.get("word")]
        pool_words = [w for w in pool_words if w]

        today_pool = [it.get("word", "").strip() for it in (today_words or []) if it.get("word")]
        today_pool = [w for w in today_pool if w]

        qlist = []
        base = (today_words or [])[:]
        random.shuffle(base)

        for it in base:
            correct = (it.get("word", "") or "").strip()
            if not correct:
                continue

            prompt = (it.get("mean", "") or "").strip()
            if not prompt:
                # mean이 비어있으면 desc -> ex 순으로 fallback
                prompt = (it.get("desc", "") or "").strip() or (it.get("ex", "") or "").strip()
            if not prompt:
                prompt = "이 설명에 알맞은 단어는 무엇일까요?"

            # 오답 후보 수집
            candidates = [w for w in pool_words if w != correct]
            if len(candidates) < (n_choices - 1):
                candidates += [w for w in today_pool if w != correct and w not in candidates]

            # 그래도 부족하면(아주 작은 데이터셋) 가능한 범위에서만 구성
            random.shuffle(candidates)
            wrongs = candidates[: max(0, n_choices - 1)]
            choices = [correct] + wrongs
            # 보기 4개가 안되면 중복 없이 가능한 만큼만 사용(그래도 동작은 함)
            choices = list(dict.fromkeys(choices))
            random.shuffle(choices)

            qlist.append(
                {
                    "prompt": prompt,
                    "correct": correct,
                    "choices": choices,
                    # 상태값(사양서 동작)
                    "selected": None,          # 현재 선택
                    "wrong_set": set(),        # 누적 오답(빨강 유지)
                    "answered": False,         # 정답 처리 완료 여부
                    "just_correct": False,     # 직전 제출이 정답인지
                }
            )

        return qlist
    # =============================================================================
    # View: Review Start
    # =============================================================================
    def view_review_start():
        topic = session.get("topic", "")
        user = get_user(session["user"]["id"]) or session["user"]
        user = ensure_progress(user)

        thr = int(load_system().get("review_threshold", 85))

        today_words = session.get("today_words", []) or session.get("study_words", [])
        tpdata = user["progress"]["topics"].get(topic, {})
        learned = tpdata.get("learned", {})
        low_items = []
        for it in today_words:
            w = it.get("word", "")
            sc = learned.get(w, {}).get("last_score", 999)
            if sc < thr:
                low_items.append(it)

        low_cnt = len(low_items)

        def start_review_today(e=None):
            if low_cnt == 0:
                show_snack("복습 대상이 없습니다.", COLOR_PRIMARY)
                return
            session.update({"study_words": low_items, "idx": 0})
            session["is_review"] = True
            user2 = get_user(user["id"]) or user
            user2 = ensure_progress(user2)
            user2["progress"]["last_session"] = {"topic": topic, "idx": 0}
            update_user(user2["id"], user2)
            session["user"] = user2
            go_to("/study")

        def start_test(e=None):
            topic = session.get("topic", "")
            today_words = (session.get("today_words", []) or [])
            
            # 랜덤으로 3개 단어로 문제 생성
            random.shuffle(today_words)
            today_words = today_words[:3] 

            qlist = make_test_queue(topic, today_words, n_choices=4)

            session["test_queue"] = qlist
            session["test_idx"] = 0
            session["test_score"] = 0
            session["is_review"] = False
            go_to("/test?i=0")

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=24,
                    content=ft.Column(
                        [
                            ft.Container(height=6),
                            ft.Text("오늘 학습 수고했어요 💯", size=22, weight="bold", color=COLOR_PRIMARY),
                            ft.Container(height=10),
                            ft.Container(
                                bgcolor="#f8f9fa",
                                border_radius=20,
                                padding=18,
                                border=ft.border.all(1, "#eef1f4"),
                                content=ft.Column(
                                    [
                                        ft.Text(f"복습 기준: {thr}점 미만", size=12, color=COLOR_TEXT_DESC),
                                        ft.Text(f"오늘 학습 중 복습 대상: {low_cnt}개", size=14, weight="bold", color=COLOR_TEXT_MAIN),
                                        ft.Text("점수 미달 단어를 한 번 더 보고 넘어가면 더 좋아요.", size=12, color=COLOR_TEXT_DESC),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=6,
                                ),
                            ),
                            ft.Container(height=16),
                            ft.Row(
                                [
                                    ft.ElevatedButton("복습하기", on_click=start_review_today, expand=True, bgcolor=COLOR_ACCENT, color="white", disabled=(low_cnt == 0)),
                                    ft.ElevatedButton("테스트 시작", on_click=start_test, expand=True, bgcolor=COLOR_TEXT_MAIN, color="white"),
                                ],
                                spacing=10,
                            ),
                            ft.Container(height=10),
                            ft.OutlinedButton("홈으로", on_click=lambda _: go_to("/student_home"), width=320),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                student_bottom_nav(active="home"),
            ],
        )

        return mobile_shell(
            "/review_start",
            body,
            title="복습 안내",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/study")),
        )

    # =============================================================================
    # View: Test
    # =============================================================================
    def view_test():
        qlist = session.get("test_queue", [])
        if not qlist:
            body = ft.Container(
                padding=24,
                content=ft.Column(
                    [
                        ft.Text("테스트 데이터가 없습니다.", size=13, color=COLOR_TEXT_DESC),
                        ft.Container(height=10),
                        ft.ElevatedButton("홈", on_click=lambda _: go_to("/student_home"), bgcolor=COLOR_PRIMARY, color="white"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            return mobile_shell(
                "/test", body, title="연습문제",
                leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home"))
            )

        idx = int(session.get("test_idx", 0) or 0)
        idx = max(0, min(idx, len(qlist) - 1))
        q = qlist[idx]
        total = len(qlist)

        feedback = ft.Text("", size=12, weight="bold")

        # 옵션 컨테이너들을 참조로 들고 있다가 스타일을 직접 바꿔준다
        option_boxes: list[ft.Container] = []

        def _ensure_wrong_set():
            ws = q.get("wrong_set")
            if not isinstance(ws, set):
                ws = set()
                q["wrong_set"] = ws
            return ws

        def apply_styles(do_update: bool = True):
            selected = q.get("selected")
            answered = bool(q.get("answered"))
            correct = q.get("correct")
            wrong_set = _ensure_wrong_set()

            for box in option_boxes:
                word = box.data

                border_color = "#dfe6ee"
                bg = "white"
                txt_color = COLOR_TEXT_MAIN

                # 오답 누적(빨강 유지)
                if word in wrong_set:
                    border_color = COLOR_ACCENT
                    bg = "#fff5f5"
                    txt_color = COLOR_ACCENT

                # 정답 처리 후 정답만 초록
                if answered and word == correct:
                    border_color = COLOR_EVAL
                    bg = "#f0fdf4"
                    txt_color = COLOR_EVAL

                # 제출 전 선택 표시(파랑)
                if (not answered) and selected == word:
                    border_color = COLOR_PRIMARY
                    bg = "#eef5ff"
                    txt_color = COLOR_PRIMARY

                box.border = ft.border.all(2, border_color)
                box.bgcolor = bg
                if isinstance(box.content, ft.Text):
                    box.content.color = txt_color

                if do_update and box.page:
                    box.update()

        def pick(word: str):
            if q.get("answered"):
                return
            q["selected"] = word
            feedback.value = ""
            feedback.update()
            apply_styles()

        def save_wrong_once(user_ans: str, correct: str, prompt: str):
            user = get_user(session["user"]["id"]) or session["user"]
            user = add_wrong_note(user, session.get("topic", ""), prompt, correct, user_ans)
            update_user(user["id"], user)
            session["user"] = user

        def on_next(e=None):
            session["test_idx"] = idx + 1
            if session["test_idx"] >= total:
                go_to("/study_complete")
            else:
                go_to(f"/test?i={session['test_idx']}")


        def on_primary(e=None):
            if q.get("answered"):
                on_next()
            else:
                on_confirm()

        def on_confirm(e=None):
            if q.get("answered"):
                on_next()
                return

            selected = (q.get("selected") or "").strip()
            if not selected:
                show_snack("보기를 선택해주세요.", COLOR_ACCENT)
                return

            correct = (q.get("correct") or "").strip()
            prompt = (q.get("prompt") or "").strip()

            if selected == correct:
                q["answered"] = True
                session["test_score"] = int(session.get("test_score", 0) or 0) + 1

                feedback.value = "✨ 정답입니다!"
                feedback.color = COLOR_EVAL
                feedback.update()

                # 버튼을 “다음 문제”로 바꾸고 handler도 변경
                primary_btn.text = "다음 문제"
                primary_btn.on_click = on_next
                primary_btn.update()

                apply_styles()
            else:
                # 오답: 정답 공개 X, 오답만 빨강 누적 유지, 리트라이
                ws = _ensure_wrong_set()
                if selected not in ws:
                    ws.add(selected)
                    save_wrong_once(selected, correct, prompt)

                # 다시 풀도록 선택 해제(선택 파랑 제거)
                q["selected"] = None

                feedback.value = "오답입니다. 다시 풀어보세요."
                feedback.color = COLOR_ACCENT
                feedback.update()

                apply_styles()

        # 보기 만들기
        for w in (q.get("choices") or []):
            box = ft.Container(
                width=320,
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                border_radius=12,
                border=ft.border.all(2, "#dfe6ee"),
                bgcolor="white",
                ink=True,
                data=w,  # 옵션 단어 저장
                on_click=lambda e, ww=w: pick(ww),
                content=ft.Text(w, size=13, color=COLOR_TEXT_MAIN, weight="bold"),
            )
            option_boxes.append(box)

        # 하단 버튼(초기 상태 반영)
        is_answered = bool(q.get("answered"))
        primary_btn = ft.ElevatedButton(
            "다음 문제" if is_answered else "확인",
            on_click=on_primary,
            width=320,
            height=48,
            style=ft.ButtonStyle(
                bgcolor=COLOR_PRIMARY,
                color="white",
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
        )

        # 초기 스타일/피드백 세팅
        if is_answered:
            feedback.value = "✨ 정답입니다!"
            feedback.color = COLOR_EVAL

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Container(
                                bgcolor="#ffffff",
                                border_radius=20,
                                padding=18,
                                border=ft.border.all(1, "#eef1f4"),
                                content=ft.Column(
                                    [
                                        ft.Text(f"문제 {idx+1}/{total}", size=12, color=COLOR_PRIMARY, weight="bold"),
                                        ft.Container(height=8),
                                        ft.Container(
                                            bgcolor="#f8f9fa",
                                            border_radius=14,
                                            padding=14,
                                            content=ft.Column(
                                                [
                                                    ft.Text(f"“{q.get('prompt','')}”", size=13, color=COLOR_TEXT_MAIN),
                                                    ft.Container(height=6),
                                                    ft.Text("이 설명에 알맞은 단어는 무엇일까요?", size=12, color=COLOR_TEXT_DESC),
                                                ],
                                                spacing=0,
                                            ),
                                        ),
                                        ft.Container(height=12),
                                        ft.Column(option_boxes, spacing=10),
                                        ft.Container(height=10),
                                        feedback,
                                        ft.Container(height=18),
                                        primary_btn,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll="auto",
                        expand=True,
                    ),
                ),
                student_bottom_nav(active="home"),
            ],
        )

        apply_styles(do_update=False)  # 초기 렌더용(업데이트 호출 없이)

        return mobile_shell(
            "/test",
            body,
            title="연습문제",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")),
        )

    # =============================================================================
    # View: Study Complete
    # =============================================================================
    def view_study_complete():
        qlist = session.get("test_queue", [])
        total = len(qlist) if qlist else 0
        score = int(session.get("test_score", 0) or 0)

        # 사양서 예시: 3문제 중 2문제도 통과 → 기준을 2/3로 설정
        required = math.ceil((2 * max(1, total)) / 3)
        passed = (score >= required)

        def go_continue(e=None):
            # “이어서 학습하기”는 토픽 선택으로 연결(원하면 /study로 이어도 됨)
            go_to("/level_select")

        def go_done(e=None):
            # “오늘 학습 완료”
            go_to("/student_home")

        def retry_test(e=None):
            # 다시 풀기: 상태 초기화
            for q in (session.get("test_queue", []) or []):
                q["selected"] = None
                q["wrong_set"] = set()
                q["answered"] = False
                q["just_correct"] = False
            session["test_idx"] = 0
            session["test_score"] = 0
            go_to("/test")

        result_text = f"총 {total}문제 중 {score}문제를 맞혔습니다."

        buttons = []
        if passed:
            # p36: 통과 → 2개(둘 다 초록)
            buttons = [
                ft.ElevatedButton("이어서 학습하기", on_click=go_continue, width=320, height=48, bgcolor=COLOR_EVAL, color="white"),
                ft.ElevatedButton("오늘 학습 완료", on_click=go_done, width=320, height=48, bgcolor=COLOR_EVAL, color="white"),
            ]
        else:
            # p37: 미달 → 3개(파랑/주황/초록)
            buttons = [
                ft.ElevatedButton("이어서 학습하기", on_click=go_continue, width=320, height=48, bgcolor=COLOR_PRIMARY, color="white"),
                ft.ElevatedButton("다시 풀기", on_click=retry_test, width=320, height=48, bgcolor=COLOR_SECONDARY, color="white"),
                ft.ElevatedButton("오늘 학습 완료", on_click=go_done, width=320, height=48, bgcolor=COLOR_EVAL, color="white"),
            ]

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=24,
                    content=ft.Column(
                        [
                            ft.Container(height=10),
                            ft.Text("🎉", size=42),
                            ft.Container(height=6),
                            ft.Text("학습 결과", size=18, weight="bold", color=COLOR_TEXT_MAIN),
                            ft.Container(height=8),
                            ft.Text(result_text, size=12, color=COLOR_TEXT_DESC),
                            ft.Container(height=22),
                            ft.Column(buttons, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ),
                student_bottom_nav(active="home"),
            ],
        )

        return mobile_shell(
            "/study_complete",
            body,
            title="학습 결과",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")),
        )

    # =============================================================================
    # View: Cumulative
    # =============================================================================
    def view_cumulative():
        user = get_user(session["user"]["id"]) or session["user"]
        user = ensure_progress(user)

        topic_dd = ft.Dropdown(
            width=220,
            options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())],
            value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None),
        )

        mask_dd = ft.Dropdown(
            width=120,
            options=[
                ft.dropdown.Option("none", "가리기 없음"),
                ft.dropdown.Option("word", "단어 가리기"),
                ft.dropdown.Option("mean", "뜻 가리기"),
            ],
            value=session.get("mask_mode", "none"),
        )

        list_col = ft.Column(scroll="auto", expand=True)

        def render():
            session["mask_mode"] = mask_dd.value
            tp = topic_dd.value
            if not tp:
                list_col.controls = [ft.Text("토픽이 없습니다.")]
                page.update()
                return

            tpdata = user["progress"]["topics"].get(tp, {})
            learned = tpdata.get("learned", {})
            items = sorted(learned.items(), key=lambda x: x[1].get("last_seen", ""), reverse=True)

            controls = []
            for w, info in items:
                word_txt = "••••" if mask_dd.value == "word" else w
                mean_txt = "••••" if mask_dd.value == "mean" else info.get("mean", "")
                sc = info.get("last_score", 0)
                controls.append(
                    ft.Container(
                        bgcolor="white",
                        border_radius=16,
                        padding=12,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(word_txt, size=15, weight="bold", color=COLOR_TEXT_MAIN),
                                        ft.Text(mean_txt, size=11, color=COLOR_TEXT_DESC),
                                        ft.Text(info.get("last_seen", ""), size=10, color="#95a5a6"),
                                    ],
                                    expand=True,
                                    spacing=2,
                                ),
                                ft.Container(
                                    padding=8,
                                    border_radius=12,
                                    bgcolor="#f0fdf4" if sc >= 85 else "#fff5f5",
                                    content=ft.Text(f"{sc}점", weight="bold", color=COLOR_EVAL if sc >= 85 else COLOR_ACCENT),
                                ),
                            ]
                        ),
                    )
                )

            if not controls:
                controls = [ft.Text("아직 누적 학습 데이터가 없습니다.", color=COLOR_TEXT_DESC)]
            list_col.controls = controls
            page.update()

        topic_dd.on_change = lambda e: render()
        mask_dd.on_change = lambda e: render()
        render()

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Row([topic_dd, mask_dd], spacing=10),
                            ft.Container(height=10),
                            list_col,
                        ]
                    ),
                ),
                student_bottom_nav(active="stats"),
            ],
        )
        return mobile_shell(
            "/cumulative",
            body,
            title="누적 학습",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/stats")),
        )

    # =============================================================================
    # View: Wrong Notes
    # =============================================================================
    def view_wrong_notes():
        user = get_user(session["user"]["id"]) or session["user"]
        user = ensure_progress(user)

        topic_dd = ft.Dropdown(
            width=260,
            options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())],
            value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None),
        )
        col = ft.Column(scroll="auto", expand=True)

        def render():
            tp = topic_dd.value
            if not tp:
                col.controls = [ft.Text("토픽이 없습니다.")]
                page.update()
                return

            tpdata = user["progress"]["topics"].get(tp, {})
            wrongs = list(reversed(tpdata.get("wrong_notes", [])))
            controls = []

            for it in wrongs:
                controls.append(
                    ft.Container(
                        bgcolor="white",
                        border_radius=16,
                        padding=12,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Column(
                            [
                                ft.Text(f"문제: {it.get('q','')}", weight="bold", color=COLOR_TEXT_MAIN),
                                ft.Text(f"정답: {it.get('a','')}", color=COLOR_EVAL),
                                ft.Text(f"내 답: {it.get('user','')}", color=COLOR_ACCENT),
                                ft.Text(it.get("ts", ""), size=10, color="#95a5a6"),
                            ],
                            spacing=4,
                        ),
                    )
                )

            if not controls:
                controls = [ft.Text("오답노트가 비어 있습니다.", color=COLOR_TEXT_DESC)]
            col.controls = controls
            page.update()

        topic_dd.on_change = lambda e: render()
        render()

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Row([topic_dd], spacing=10),
                            ft.Container(height=10),
                            col,
                        ]
                    ),
                ),
                student_bottom_nav(active="stats"),
            ],
        )
        return mobile_shell(
            "/wrong_notes",
            body,
            title="오답노트",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/stats")),
        )

    # =============================================================================
    # View: Review
    # =============================================================================
    def view_review():
        user = get_user(session["user"]["id"]) or session["user"]
        user = ensure_progress(user)

        sysdata2 = load_system()
        thr = int(sysdata2.get("review_threshold", 85))

        topic_dd = ft.Dropdown(
            width=260,
            options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())],
            value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None),
        )
        col = ft.Column(scroll="auto", expand=True)

        def start_review(tp):
            tpdata = user["progress"]["topics"].get(tp, {})
            learned = tpdata.get("learned", {})
            items = []
            vocab = VOCAB_DB.get(tp, [])
            vocab_map = {it["word"]: it for it in vocab if it.get("word")}
            for w, info in learned.items():
                if info.get("last_score", 100) < thr and w in vocab_map:
                    items.append(vocab_map[w])
            if not items:
                show_snack("복습 대상 단어가 없습니다.", COLOR_PRIMARY)
                return
            session.update({"topic": tp, "study_words": items, "idx": 0})
            session["is_review"] = True
            go_to("/study")

        def render():
            tp = topic_dd.value
            if not tp:
                col.controls = [ft.Text("토픽이 없습니다.")]
                page.update()
                return
            tpdata = user["progress"]["topics"].get(tp, {})
            learned = tpdata.get("learned", {})
            low = [(w, info) for w, info in learned.items() if info.get("last_score", 100) < thr]
            low.sort(key=lambda x: x[1].get("last_score", 0))

            controls = [
                ft.Container(
                    bgcolor="#f8f9fa",
                    border_radius=16,
                    padding=12,
                    border=ft.border.all(1, "#eef1f4"),
                    content=ft.Row(
                        [
                            ft.Text(f"복습 기준: {thr}점 미만", color=COLOR_TEXT_DESC, size=12),
                            ft.ElevatedButton("복습 시작", on_click=lambda _: start_review(tp), bgcolor=COLOR_ACCENT, color="white"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                )
            ]
            for w, info in low[:200]:
                controls.append(
                    ft.Container(
                        bgcolor="white",
                        border_radius=16,
                        padding=12,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(w, weight="bold", color=COLOR_TEXT_MAIN),
                                        ft.Text(info.get("mean", ""), size=11, color=COLOR_TEXT_DESC),
                                    ],
                                    expand=True,
                                ),
                                ft.Text(f"{info.get('last_score',0)}점", color=COLOR_ACCENT, weight="bold"),
                            ]
                        ),
                    )
                )
            if len(controls) == 1:
                controls.append(ft.Text("복습 대상이 없습니다.", color=COLOR_TEXT_DESC))
            col.controls = controls
            page.update()

        topic_dd.on_change = lambda e: render()
        render()

        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column([ft.Row([topic_dd], spacing=10), ft.Container(height=10), col]),
                ),
                student_bottom_nav(active="stats"),
            ],
        )
        return mobile_shell(
            "/review",
            body,
            title="복습",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/stats")),
        )

    # =============================================================================
    # View: Teacher Dashboard stop_propagation 제거/우회(구조 개선)
    # =============================================================================
    def view_teacher_dash():
        users = load_users()
        rows = []
        for uid, u in users.items():
            if u.get("role") != "student":
                continue
            u = ensure_progress(u)
            goal = int(u["progress"]["settings"].get("goal", sysdata.get("default_goal", 10)))
            topics = u["progress"]["topics"]
            total_learned = sum(len(t.get("learned", {})) for t in topics.values())
            avgs = [t.get("stats", {}).get("avg_score", 0) for t in topics.values() if t.get("learned")]
            avg_score = round(sum(avgs) / max(1, len(avgs)), 2) if avgs else 0.0
            wrong_cnt = sum(len(t.get("wrong_notes", [])) for t in topics.values())
            ratio = int((min(total_learned, goal) / max(1, goal)) * 100) if goal else 0

            rows.append({"uid": uid, "name": u.get("name", uid), "goal": goal, "learned": total_learned, "ratio": ratio, "avg": avg_score, "wrong": wrong_cnt})

        rows.sort(key=lambda x: (-x["ratio"], -x["avg"], x["name"]))

        def open_student(uid: str):
            session["selected_student_id"] = uid
            go_to("/teacher_student")

        def reset_pw(uid: str):
            users2 = load_users()
            if uid not in users2:
                show_snack("학생을 찾을 수 없습니다.", COLOR_ACCENT)
                return
            users2[uid]["pw"] = hash_password("1111")
            save_users(users2)
            show_snack(f"{users2[uid].get('name', uid)} 비밀번호를 1111로 초기화했습니다.", COLOR_PRIMARY)

        cards = []
        for s in rows:
            # 카드 전체를 클릭 영역 + 오른쪽 아이콘은 독립 클릭(전파 차단 API 불필요)
            clickable = ft.Container(
                expand=True,
                ink=True,
                on_click=lambda e, uid=s["uid"]: open_student(uid),
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(s["name"], weight="bold", size=15, color=COLOR_TEXT_MAIN),
                                ft.Text(f"목표 {s['goal']} · 누적 {s['learned']}", size=11, color=COLOR_TEXT_DESC),
                                ft.Text(f"평균 {s['avg']} · 오답 {s['wrong']}", size=11, color=COLOR_TEXT_DESC),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Container(
                            padding=8,
                            border_radius=12,
                            bgcolor="#eef5ff",
                            content=ft.Text(f"{s['ratio']}%", weight="bold", color=COLOR_PRIMARY),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )

            card = ft.Container(
                bgcolor="white",
                padding=14,
                border_radius=16,
                border=ft.border.all(1, "#eef1f4"),
                content=ft.Row(
                    [
                        clickable,
                        ft.IconButton(
                            icon=ft.icons.RESTART_ALT,
                            tooltip="비밀번호 초기화(1111)",
                            on_click=lambda e, uid=s["uid"]: reset_pw(uid),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )
            cards.append(card)

        if not cards:
            cards = [ft.Text("학생 계정이 없습니다.", color=COLOR_TEXT_DESC)]

        body = ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                expand=True,
                                bgcolor=COLOR_PRIMARY,
                                padding=16,
                                border_radius=18,
                                content=ft.Column(
                                    [
                                        ft.Text("학생 수", color="white", size=11),
                                        ft.Text(str(len(rows)), size=22, weight="bold", color="white"),
                                    ],
                                    spacing=2,
                                ),
                            ),
                            ft.Container(
                                expand=True,
                                bgcolor="#f8f9fa",
                                padding=16,
                                border_radius=18,
                                border=ft.border.all(1, "#eef1f4"),
                                content=ft.Column(
                                    [
                                        ft.Text("관리 지표", color=COLOR_TEXT_DESC, size=11),
                                        ft.Text("진도/평균/오답", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                                    ],
                                    spacing=2,
                                ),
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Container(height=14),
                    ft.Text("학생 목록", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(height=8),
                    ft.Column(cards, spacing=10, scroll="auto"),
                ],
                spacing=0,
            ),
        )

        return mobile_shell(
            "/teacher_dash",
            body,
            title="선생님 대시보드",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/login")),
            actions=[ft.IconButton(icon=ft.icons.LOGOUT, on_click=lambda _: go_to("/login"))],
        )

    def view_teacher_student():
        uid = session.get("selected_student_id")
        if not uid:
            return mobile_shell("/teacher_student", ft.Text("학생 선택이 필요합니다."), title="학생 상세")

        u = get_user(uid)
        if not u:
            return mobile_shell("/teacher_student", ft.Text("학생 정보를 찾을 수 없습니다."), title="학생 상세")

        u = ensure_progress(u)
        topics = u["progress"]["topics"]
        total_learned = sum(len(t.get("learned", {})) for t in topics.values())
        wrong_cnt = sum(len(t.get("wrong_notes", [])) for t in topics.values())
        last = u["progress"].get("last_session", {"topic": "", "idx": 0})

        topic_cards = []
        for tp in sorted(VOCAB_DB.keys()):
            tpdata = topics.get(tp, {})
            studied = len(tpdata.get("learned", {}))
            avg = tpdata.get("stats", {}).get("avg_score", 0.0)
            wcnt = len(tpdata.get("wrong_notes", []))
            topic_cards.append(
                ft.Container(
                    bgcolor="white",
                    border_radius=16,
                    padding=12,
                    border=ft.border.all(1, "#eef1f4"),
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(tp, weight="bold", color=COLOR_TEXT_MAIN),
                                    ft.Text(f"누적 {studied} · 평균 {avg} · 오답 {wcnt}", size=11, color=COLOR_TEXT_DESC),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                        ]
                    ),
                )
            )

        def reset_pw():
            users2 = load_users()
            if uid not in users2:
                show_snack("학생을 찾을 수 없습니다.", COLOR_ACCENT)
                return
            users2[uid]["pw"] = hash_password("1111")
            save_users(users2)
            show_snack("비밀번호를 1111로 초기화했습니다.", COLOR_PRIMARY)

        body = ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Container(
                        bgcolor="#f8f9fa",
                        border_radius=18,
                        padding=16,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Column(
                            [
                                ft.Text(f"{u.get('name', uid)} ({uid})", size=18, weight="bold", color=COLOR_TEXT_MAIN),
                                ft.Text(f"국적: {country_label(u.get('country','KR'))}", size=12, color=COLOR_TEXT_DESC),
                                ft.Text(f"누적 학습: {total_learned} · 오답: {wrong_cnt}", size=12, color=COLOR_TEXT_DESC),
                                ft.Text(f"마지막 학습: {last.get('topic','')} / idx {int(last.get('idx',0))+1}", size=12, color=COLOR_TEXT_DESC),
                                ft.Container(height=10),
                                ft.Row(
                                    [
                                        ft.ElevatedButton("비밀번호 초기화(1111)", on_click=lambda e: reset_pw(), bgcolor=COLOR_ACCENT, color="white", expand=True),
                                        ft.OutlinedButton("목록", on_click=lambda e: go_to("/teacher_dash"), expand=True),
                                    ],
                                    spacing=10,
                                ),
                            ],
                            spacing=4,
                        ),
                    ),
                    ft.Container(height=12),
                    ft.Text("토픽별 현황", weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(height=8),
                    ft.Column(topic_cards, spacing=10, scroll="auto"),
                ],
                scroll="auto",
            ),
        )

        return mobile_shell(
            "/teacher_student",
            body,
            title="학생 상세",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/teacher_dash")),
        )

    # =============================================================================
    # View: System Dashboard (admin)
    # =============================================================================
    def view_system_dash():
        sysdata_local = load_system()

        default_goal_field = ft.TextField(
            label="기본 목표량(default_goal)",
            value=str(sysdata_local.get("default_goal", 10)),
            width=320,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=12,
        )
        review_thr_field = ft.TextField(
            label="복습 기준(review_threshold)",
            value=str(sysdata_local.get("review_threshold", 85)),
            width=320,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=12,
        )
        api_key_field = ft.TextField(
            label="OpenAI API Key(저장만)",
            value=str(sysdata_local.get("api", {}).get("openai_api_key", "")),
            width=320,
            password=True,
            can_reveal_password=True,
            bgcolor="white",
            border_radius=12,
        )
        stt_provider_field = ft.Dropdown(
            label="STT Provider",
            width=320,
            value=str(sysdata_local.get("api", {}).get("stt_provider", "none")),
            options=[ft.dropdown.Option("none"), ft.dropdown.Option("openai"), ft.dropdown.Option("google"), ft.dropdown.Option("aws")],
        )

        log_box = ft.TextField(
            label="최근 로그(읽기 전용)",
            value="",
            multiline=True,
            read_only=True,
            min_lines=10,
            max_lines=18,
            width=320,
            bgcolor="white",
            border_radius=12,
        )

        def refresh_log(e=None):
            try:
                if not os.path.exists(LOG_FILE):
                    log_box.value = "(로그 없음)"
                else:
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    log_box.value = "".join(lines[-200:]) if lines else "(로그 없음)"
            except Exception as ex:
                log_box.value = f"(로그 읽기 실패: {ex})"
            page.update()

        def save_admin_settings(e=None):
            try:
                dg = int(default_goal_field.value)
                dg = max(1, min(100, dg))
            except:
                dg = 10
            try:
                rt = int(review_thr_field.value)
                rt = max(0, min(100, rt))
            except:
                rt = 85

            sysdata_local["default_goal"] = dg
            sysdata_local["review_threshold"] = rt
            if "api" not in sysdata_local:
                sysdata_local["api"] = {}
            sysdata_local["api"]["openai_api_key"] = api_key_field.value or ""
            sysdata_local["api"]["stt_provider"] = stt_provider_field.value or "none"
            save_system(sysdata_local)

            session["goal"] = session["goal"] or dg
            show_snack("시스템 설정이 저장되었습니다.", COLOR_PRIMARY)
            log_write("admin saved system settings")

        refresh_log()

        body = ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Container(
                        bgcolor="#f8f9fa",
                        border_radius=18,
                        padding=16,
                        border=ft.border.all(1, "#eef1f4"),
                        content=ft.Column(
                            [
                                ft.Text("시스템 설정", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                                ft.Container(height=10),
                                default_goal_field,
                                ft.Container(height=10),
                                review_thr_field,
                                ft.Divider(height=18),
                                ft.Text("API 설정(저장만 / 기능 연결은 별도)", size=11, color=COLOR_TEXT_DESC),
                                ft.Container(height=8),
                                stt_provider_field,
                                ft.Container(height=10),
                                api_key_field,
                                ft.Container(height=12),
                                ft.ElevatedButton("저장", on_click=save_admin_settings, bgcolor=COLOR_PRIMARY, color="white", width=320),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    ft.Container(height=14),
                    ft.Text("로그", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(height=8),
                    ft.Row(
                        [ft.ElevatedButton("새로고침", on_click=refresh_log, bgcolor=COLOR_TEXT_MAIN, color="white")],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Container(height=8),
                    log_box,
                ],
                scroll="auto",
            ),
        )

        return mobile_shell(
            "/system_dash",
            body,
            title="시스템 대시보드",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/login")),
            actions=[ft.IconButton(icon=ft.icons.LOGOUT, on_click=lambda _: go_to("/login"))],
        )

    # =============================================================================
    # Routing
    # =============================================================================
    def route_change(e: ft.RouteChangeEvent):
        log_write(f"route_change: {page.route}")
        page.views.clear()

        r_full = page.route
        r = (r_full or "").split("?", 1)[0] 


        if r == "/":
            page.views.append(view_landing())
        elif r == "/login":
            page.views.append(view_login())
        elif r == "/signup":
            page.views.append(view_signup())

        elif r == "/student_home":
            page.views.append(view_student_home())
        elif r == "/level_select":
            page.views.append(view_level_select())
        elif r == "/settings":
            page.views.append(view_settings())
        elif r == "/stats":
            page.views.append(view_stats())
        elif r == "/profile":
            page.views.append(view_profile())

        elif r == "/study":
            page.views.append(view_study())
        elif r == "/motivate":
            page.views.append(view_motivate())
        elif r == "/pron_result":
            page.views.append(view_pron_result())
        elif r == "/review_start":
            page.views.append(view_review_start())

        elif r == "/test":
            page.views.append(view_test())
        elif r == "/study_complete":
            page.views.append(view_study_complete())

        elif r == "/cumulative":
            page.views.append(view_cumulative())
        elif r == "/wrong_notes":
            page.views.append(view_wrong_notes())
        elif r == "/review":
            page.views.append(view_review())

        elif r in ("/teacher_dash", "/teacher_dashboard"):
            page.views.append(view_teacher_dash())
        elif r == "/teacher_student":
            page.views.append(view_teacher_student())

        elif r in ("/system_dash", "/admin_dash", "/system_dashboard"):
            page.views.append(view_system_dash())

        else:
            page.views.append(view_login())

        page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/login")


# =============================================================================
# 실행
# =============================================================================
if __name__ == "__main__":
    os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
    print("🚀 Flet 앱 시작...")
    print("http://localhost:8100 에서 접속하세요.")

    # xdg-open 오류(헤드리스/서버 환경) 회피:
    # DISPLAY/WAYLAND가 없으면 WEB_BROWSER 대신 WEB_SERVER로 실행
    def _is_headless_linux() -> bool:
        if os.name != "posix":
            return False
        return (not os.environ.get("DISPLAY")) and (not os.environ.get("WAYLAND_DISPLAY"))

    try:
        if _is_headless_linux():
            try:
                view_mode = ft.AppView.WEB_SERVER
            except AttributeError:
                view_mode = "web_server"
        else:
            try:
                view_mode = ft.AppView.WEB_BROWSER
            except AttributeError:
                view_mode = "web_browser"
    except Exception:
        view_mode = "web_server"

    ft.app(target=main, port=8100, view=view_mode)
