import flet as ft

# =============================================================================
# ✅ Flet 0.80+ 호환: 구버전 ft.icons.* 를 계속 쓰기 위한 alias
# - 0.80.1에서는 아이콘 상수가 ft.Icons 로 이동한 케이스가 많아서,
#   ft.icons 가 비어있으면 ft.Icons 를 ft.icons 로 붙여줌
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
from datetime import datetime

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


def log_write(msg: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass


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
        with open(SYSTEM_FILE, "w", encoding="utf-8") as f:
            json.dump(sysdata, f, ensure_ascii=False, indent=2)
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
        default_users = {
            "admin": {
                "pw": "1111",
                "name": "관리자",
                "role": "admin",
                "country": "KR",
                "progress": {},
            },
            "teacher": {
                "pw": "1111",
                "name": "선생님",
                "role": "teacher",
                "country": "KR",
                "progress": {},
            },
            "student": {
                "pw": "1111",
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
        save_users(data)
        return data
    except:
        return {}


def save_users(users_data):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_write(f"save_users error: {e}")


def register_user(uid, pw, name, country="KR", role="student"):
    users = load_users()
    if uid in users:
        return False, "이미 존재하는 아이디입니다."
    users[uid] = {"pw": pw, "name": name, "role": role, "country": country, "progress": {}}
    save_users(users)
    return True, "회원가입 완료! 로그인해주세요."


def authenticate_user(uid, pw):
    users = load_users()
    if uid in users and users[uid]["pw"] == pw:
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

    # 격려 화면(오늘 1회만 띄우기) 플래그
    if "today_flags" not in user["progress"]:
        user["progress"]["today_flags"] = {}
    if "motivate_shown" not in user["progress"]["today_flags"]:
        user["progress"]["today_flags"]["motivate_shown"] = False

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

    # ✅ URL 끝에 # 붙는 문제(해시 라우팅) 줄이기: PATH 전략(가능한 버전에서만)
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

    # ------------------------------
    # TTS (Web Native)
    # ------------------------------
    def play_tts(text: str):
        try:
            t = json.dumps(text)
            page.run_javascript(
                f"""
            try {{
                if (!window.speechSynthesis) return;
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance({t});
                u.lang = "ko-KR"; u.rate = 1.0; u.volume = 1.0;
                window.speechSynthesis.speak(u);
            }} catch(e) {{}}
            """
            )
        except:
            pass

    # ------------------------------
    # Pronunciation 평가 (현재 더미)
    # - 사양서: "AI 평가 버튼"을 눌러야 결과가 뜨게
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

        # 상세(어절/음절) 더미: text를 공백 기준 어절로 쪼개고 점수
        words = [w for w in (text or "").split() if w.strip()]
        detail = []
        for w in words[:12]:
            detail.append({"unit": w, "score": random.randint(max(60, score - 15), min(100, score + 10))})
        return score, comment, tag, detail

    # 코멘트 “DB 템플릿 느낌” (추후: 이벤트 분류(tag) 기반으로 실제 문구 DB 연결)
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
        # 사양서 의도: “생성형 그대로” 느낌을 줄이기 위해 후처리/템플릿화
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

    def pill(icon: str, text: str, on_click=None):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=999,
            bgcolor="#f3f6fb",
            ink=True,
            on_click=on_click,
            content=ft.Row(
                [
                    ft.Text(icon, size=14),
                    ft.Text(text, size=12, color=COLOR_TEXT_DESC),
                ],
                spacing=6,
            ),
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
        # 레벨/토픽단계는 현재 "시트명"을 레벨로 쓰는 구조라 동일하게 표시
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
        # 사양서: 하단 메뉴 = 홈 / 레벨 선택 / 설정 / 통계
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
                    nav_btn("🏠", "홈", "/student_home", "home"),
                    nav_btn("🗂", "레벨 선택", "/level_select", "level"),
                    nav_btn("⚙️", "설정", "/settings", "settings"),
                    nav_btn("📊", "통계", "/stats", "stats"),
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
    # View: Login
    # =============================================================================
    def view_login():
        id_field = ft.TextField(label="아이디", width=320, border_radius=12, bgcolor="white", text_size=14)
        pw_field = ft.TextField(
            label="비밀번호",
            password=True,
            width=320,
            border_radius=12,
            bgcolor="white",
            text_size=14,
            can_reveal_password=True,
        )

        def on_login_click(e):
            if not id_field.value or not pw_field.value:
                return show_snack("아이디와 비밀번호를 입력해주세요.", COLOR_ACCENT)

            ok, user = authenticate_user(id_field.value, pw_field.value)
            if ok:
                user = ensure_progress(user)
                session["user"] = user
                session["goal"] = int(user["progress"]["settings"].get("goal", sysdata.get("default_goal", 10)))
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
                    ft.ElevatedButton(
                        "로그인",
                        on_click=on_login_click,
                        width=320,
                        height=48,
                        style=ft.ButtonStyle(
                            bgcolor=COLOR_PRIMARY,
                            color="white",
                            shape=ft.RoundedRectangleBorder(radius=14),
                        ),
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.Text("아직 회원이 아니신가요?", size=11, color=COLOR_TEXT_DESC),
                            ft.Text(
                                "회원가입 하기",
                                size=11,
                                color=COLOR_PRIMARY,
                                weight="bold",
                                spans=[ft.TextSpan(on_click=lambda _: go_to("/signup"))],
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
        new_id = ft.TextField(label="아이디", width=320, border_radius=12, bgcolor="white")
        new_pw = ft.TextField(label="비밀번호", password=True, width=320, border_radius=12, bgcolor="white", can_reveal_password=True)
        new_name = ft.TextField(label="이름", width=320, border_radius=12, bgcolor="white")

        country_dd = ft.Dropdown(
            label="국적",
            width=320,
            value="KR",
            options=[ft.dropdown.Option(code, name) for code, name in COUNTRY_OPTIONS],
        )

        def on_regist(e):
            if not (new_id.value and new_pw.value and new_name.value and country_dd.value):
                return show_snack("모든 항목을 입력해주세요.", COLOR_ACCENT)
            ok, msg = register_user(new_id.value, new_pw.value, new_name.value, country_dd.value, "student")
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)
            if ok:
                go_to("/login")

        body = ft.Container(
            padding=24,
            content=ft.Column(
                [
                    ft.Text("회원가입", size=22, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text("학습자 계정을 생성합니다.", size=12, color=COLOR_TEXT_DESC),
                    ft.Container(height=16),
                    new_id,
                    ft.Container(height=10),
                    new_pw,
                    ft.Container(height=10),
                    new_name,
                    ft.Container(height=10),
                    country_dd,
                    ft.Container(height=18),
                    ft.ElevatedButton(
                        "가입하기",
                        on_click=on_regist,
                        width=320,
                        height=48,
                        style=ft.ButtonStyle(
                            bgcolor=COLOR_PRIMARY,
                            color="white",
                            shape=ft.RoundedRectangleBorder(radius=14),
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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

        # 토픽별 리스트
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

        # 이어서 학습
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

            session["today_words"] = pick[:]  # 오늘 학습 대상
            if resume:
                idx = max(0, min(last_idx, max(0, len(pick) - 1)))
            else:
                idx = 0
                # 새 학습 시작할 때 오늘 격려 플래그 초기화(원하면 날짜 기반으로 바꾸면 됨)
                user["progress"]["today_flags"]["motivate_shown"] = False
                update_user(user["id"], user)
                session["user"] = user

            session.update({"topic": topic_name, "study_words": pick, "idx": idx})
            # 자리 저장
            user2 = get_user(user["id"]) or user
            user2 = ensure_progress(user2)
            user2["progress"]["last_session"] = {"topic": topic_name, "idx": idx}
            update_user(user2["id"], user2)
            session["user"] = user2

            go_to("/study")

        # 상단 요약
        user2 = get_user(user["id"]) or user
        user2 = ensure_progress(user2)
        topics_prog = user2["progress"]["topics"]
        total_learned = sum(len(t.get("learned", {})) for t in topics_prog.values())
        wrong_cnt = sum(len(t.get("wrong_notes", [])) for t in topics_prog.values())

        # 토픽 카드들
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

        # 이어서 버튼 (기록 있을 때만)
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
    # View: Level Select (사양서 하단 메뉴용 별도 라우트)
    # =============================================================================
    def view_level_select():
        # 사실상 홈의 토픽 그리드만 보여주는 화면
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
            session.update({"topic": topic_name, "study_words": pick, "idx": 0})

            # 자리 저장
            user2 = get_user(user["id"]) or user
            user2 = ensure_progress(user2)
            user2["progress"]["last_session"] = {"topic": topic_name, "idx": 0}
            user2["progress"]["today_flags"]["motivate_shown"] = False
            update_user(user2["id"], user2)
            session["user"] = user2

            go_to("/study")

        # 카드
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

        # 카드 아래 “상태” 메시지
        status_text = ft.Text("", size=11, color="#95a5a6")

        def persist_position():
            user = get_user(session["user"]["id"]) or session["user"]
            user = ensure_progress(user)
            user["progress"]["last_session"] = {"topic": topic, "idx": st.idx}
            update_user(user["id"], user)
            session["user"] = user

        def mark_seen_default(word_item):
            # 학습 결과 로그/자리 기억: 발음평가를 안 해도 일단 “봤음”으로 기록(기본 점수 90)
            user = get_user(session["user"]["id"]) or session["user"]
            user = ensure_progress(user)
            tpdata = user["progress"]["topics"].get(topic, {})
            learned = tpdata.get("learned", {})
            if word_item["word"] not in learned:
                user = update_learned_word(user, topic, word_item, 90)
                update_user(user["id"], user)
                session["user"] = user

        def maybe_motivate(new_idx):
            user = get_user(session["user"]["id"]) or session["user"]
            user = ensure_progress(user)
            shown = bool(user["progress"]["today_flags"].get("motivate_shown", False))
            half_idx = max(0, (total // 2) - 1)  # 예: 10개면 4(=5번째 도달 직전) -> 다음으로 넘어가면 절반 완료 느낌
            if (not shown) and new_idx >= half_idx:
                user["progress"]["today_flags"]["motivate_shown"] = True
                update_user(user["id"], user)
                session["user"] = user
                go_to("/motivate")

        def change_card(delta):
            # 현재 단어 “봤음” 처리
            try:
                mark_seen_default(words[st.idx])
            except:
                pass

            new_idx = st.idx + delta
            if 0 <= new_idx < total:
                st.idx = new_idx
                session["idx"] = new_idx
                st.is_front = True
                persist_position()
                update_view()
                if delta > 0:
                    maybe_motivate(new_idx)
            elif new_idx >= total:
                # 오늘 학습 끝 → 복습 시작 화면
                persist_position()
                go_to("/review_start")

        def prepare_test_queue():
            q = []
            for w in words:
                q.append({"type": "meaning", "word": w["word"], "correct": w.get("mean", ""), "example": w.get("ex", "")})
            random.shuffle(q)
            session["test_queue"] = q
            session["test_idx"] = 0
            session["test_score"] = 0

        def flip_card(e=None):
            st.is_front = not st.is_front
            update_view()

        def start_recording():
            # 실제 녹음은 추후 API/JS(MediaRecorder)로 붙일 자리
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
                wrap=True,          # ✅ 이게 Wrap 역할
                spacing=6,          # 가로 간격
                run_spacing=8,      # 줄(런) 간격
            )

        def render_card_content():
            w = words[st.idx]
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

                # 녹음 버튼 라벨/액션
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
            #height=520,
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
                        scroll="auto",     # ✅ 추가
                        expand=True,       # ✅ 추가 (스크롤 동작 안정)
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
    # View: Pronunciation Result (AI 평가 버튼 눌러야 결과)
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
            # 사양: 버튼 누르기 전에는 결과를 즉시 보여주지 않음
            if not recorded:
                show_snack("먼저 문장 녹음을 완료해 주세요. (현재는 더미)", COLOR_ACCENT)
                return

            score, raw_comment, tag, detail = evaluate_pronunciation_dummy(ex or word)
            comment = post_process_comment(tag, raw_comment)

            # 화면 반영
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
            # 녹음/결과 상태는 다음 단어에 영향을 주지 않게 초기화
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

    # =============================================================================
    # View: Review Start (학습 끝 -> 복습 유도)
    # =============================================================================
    def view_review_start():
        topic = session.get("topic", "")
        user = get_user(session["user"]["id"]) or session["user"]
        user = ensure_progress(user)

        thr = int(load_system().get("review_threshold", 85))

        # 오늘 학습 단어 중 점수 미달 찾기
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
            # 자리 저장(복습도 동일 플로우로)
            user2 = get_user(user["id"]) or user
            user2 = ensure_progress(user2)
            user2["progress"]["last_session"] = {"topic": topic, "idx": 0}
            update_user(user2["id"], user2)
            session["user"] = user2
            go_to("/study")

        def start_test(e=None):
            # 테스트 큐 준비 후 이동
            q = []
            for w in (session.get("today_words", []) or []):
                q.append({"type": "meaning", "word": w["word"], "correct": w.get("mean", ""), "example": w.get("ex", "")})
            random.shuffle(q)
            session["test_queue"] = q
            session["test_idx"] = 0
            session["test_score"] = 0
            go_to("/test")

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
                            ft.Text("오늘 학습 수고했어요 🎉", size=22, weight="bold", color=COLOR_PRIMARY),
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
            return mobile_shell("/test", body, title="테스트", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")))

        idx = session.get("test_idx", 0)
        idx = max(0, min(idx, len(qlist) - 1))
        q = qlist[idx]
        topic = session.get("topic", "")
        total = len(qlist)

        answer = ft.TextField(label="정답을 입력하세요", width=320, bgcolor="white", border_radius=12)

        def submit(e):
            user_ans = (answer.value or "").strip()
            correct = (q.get("correct") or "").strip()
            ok = correct != "" and (user_ans == correct or (user_ans in correct) or (correct in user_ans))

            if ok:
                session["test_score"] += 1
                show_snack("정답!", COLOR_EVAL)
            else:
                show_snack("오답! 오답노트에 저장되었습니다.", COLOR_ACCENT)
                user = get_user(session["user"]["id"]) or session["user"]
                user = add_wrong_note(user, topic, q["word"], correct, user_ans)
                update_user(user["id"], user)
                session["user"] = user

            session["test_idx"] = idx + 1
            if session["test_idx"] >= total:
                go_to("/study_complete")
            else:
                go_to("/test")

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
                                        ft.Text(f"[{idx+1}/{total}] 뜻을 입력하세요", size=12, color=COLOR_TEXT_DESC),
                                        ft.Text(q["word"], size=28, weight="bold", color=COLOR_TEXT_MAIN),
                                        ft.Container(height=10),
                                        ft.Row(
                                            [
                                                ft.ElevatedButton("🔊 단어 듣기", on_click=lambda _: play_tts(q["word"]), bgcolor=COLOR_PRIMARY, color="white", expand=True),
                                            ]
                                        ),
                                        ft.Container(height=12),
                                        answer,
                                        ft.Container(height=10),
                                        ft.ElevatedButton("제출", on_click=submit, width=320, bgcolor=COLOR_TEXT_MAIN, color="white"),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                student_bottom_nav(active="home"),
            ],
        )

        return mobile_shell(
            "/test",
            body,
            title="테스트",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home")),
        )

    # =============================================================================
    # View: Study Complete
    # =============================================================================
    def view_study_complete():
        qlist = session.get("test_queue", [])
        total = len(qlist) if qlist else 0
        score = session.get("test_score", 0)
        ratio = int((score / max(1, total)) * 100)

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
                            ft.Text("학습 완료 🎉", size=22, weight="bold", color=COLOR_PRIMARY),
                            ft.Container(height=8),
                            ft.Container(
                                bgcolor="#f8f9fa",
                                border_radius=20,
                                padding=18,
                                border=ft.border.all(1, "#eef1f4"),
                                content=ft.Column(
                                    [
                                        ft.Text("테스트 결과", size=12, color=COLOR_TEXT_DESC),
                                        ft.Text(f"{score}/{total} ({ratio}%)", size=20, weight="bold", color=COLOR_TEXT_MAIN),
                                        ft.Container(height=8),
                                        ft.Text("오답은 오답노트에서 확인할 수 있습니다.", size=12, color=COLOR_TEXT_DESC),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                            ft.Container(height=16),
                            ft.Row(
                                [
                                    ft.ElevatedButton("오답노트", on_click=lambda _: go_to("/wrong_notes"), expand=True, bgcolor=COLOR_ACCENT, color="white"),
                                    ft.ElevatedButton("홈", on_click=lambda _: go_to("/student_home"), expand=True, bgcolor=COLOR_TEXT_MAIN, color="white"),
                                ],
                                spacing=10,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                student_bottom_nav(active="home"),
            ],
        )

        return mobile_shell(
            "/study_complete",
            body,
            title="완료",
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
    # View: Teacher Dashboard
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

            rows.append({"name": u.get("name", uid), "goal": goal, "learned": total_learned, "ratio": ratio, "avg": avg_score, "wrong": wrong_cnt})

        rows.sort(key=lambda x: (-x["ratio"], -x["avg"], x["name"]))

        cards = []
        for s in rows:
            cards.append(
                ft.Container(
                    bgcolor="white",
                    padding=14,
                    border_radius=16,
                    border=ft.border.all(1, "#eef1f4"),
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(s["name"], weight="bold", size=15, color=COLOR_TEXT_MAIN),
                                    ft.Text(f"목표 {s['goal']} · 누적 {s['learned']}", size=11, color=COLOR_TEXT_DESC),
                                    ft.Text(f"평균 {s['avg']} · 오답 {s['wrong']}", size=11, color=COLOR_TEXT_DESC),
                                ],
                                spacing=2,
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
            )

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

        r = page.route

        # 메인
        if r == "/":
            page.views.append(view_landing())
        elif r == "/login":
            page.views.append(view_login())
        elif r == "/signup":
            page.views.append(view_signup())

        # 학생(사양 반영)
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

        # 학습 플로우
        elif r == "/study":
            page.views.append(view_study())
        elif r == "/motivate":
            page.views.append(view_motivate())
        elif r == "/pron_result":
            page.views.append(view_pron_result())
        elif r == "/review_start":
            page.views.append(view_review_start())

        # 테스트/결과
        elif r == "/test":
            page.views.append(view_test())
        elif r == "/study_complete":
            page.views.append(view_study_complete())

        # 기존 기능(통계에서 접근)
        elif r == "/cumulative":
            page.views.append(view_cumulative())
        elif r == "/wrong_notes":
            page.views.append(view_wrong_notes())
        elif r == "/review":
            page.views.append(view_review())

        # 선생님/관리자
        elif r in ("/teacher_dash", "/teacher_dashboard"):
            page.views.append(view_teacher_dash())
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
    try:
        view_mode = ft.AppView.WEB_BROWSER
    except AttributeError:
        view_mode = "web_browser"

    ft.app(target=main, port=8100, view=view_mode)
