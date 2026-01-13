import flet as ft
import pandas as pd
import random
import os
import json
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

# =============================================================================
# 0. 디자인 상수
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
    offset=ft.Offset(0, 18)
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
    "default_goal": 10,              # 목표 학습량 기본값
    "review_threshold": 85,          # 발음/유창성 점수 기준(이하 복습)
    "api": {
        "openai_api_key": "",
        "stt_provider": "none"
    }
}

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
        # 보정
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
    """엑셀 파일 로드: sheet_name == 토픽/레벨 로 취급"""
    vocab_db = {}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(current_dir, "data", "vocabulary.xlsx")
    os.makedirs(os.path.join(current_dir, "data"), exist_ok=True)

    if not os.path.exists(excel_path):
        dummy_data = []
        for i in range(1, 21):
            dummy_data.append({
                "word": f"테스트단어{i}",
                "mean": "테스트 의미",
                "ex": f"이것은 예문입니다 {i}",
                "desc": "설명",
                "pronunciation": f"[단어{i}]",
                "image": "📝"
            })
        return {"초급1": dummy_data, "초급2": dummy_data, "중급1": dummy_data}

    try:
        print(f"📂 엑셀 로딩 중... ({excel_path})")
        all_sheets = pd.read_excel(excel_path, sheet_name=None, engine="openpyxl")

        for sheet_name, df in all_sheets.items():
            df = df.fillna("")
            items = []

            # 컬럼 표준화 (단어/의미/예문/설명/발음/이미지)
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
                    "image": str(row.get("이미지", row.get("image", "📖"))).strip()
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
            "admin": {"pw": "1111", "name": "관리자", "role": "admin", "progress": {}},
            "teacher": {"pw": "1111", "name": "선생님", "role": "teacher", "progress": {}},
            "student": {"pw": "1111", "name": "학습자", "role": "student", "progress": {}},
        }
        save_users(default_users)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for uid, u in data.items():
            if "progress" not in u:
                u["progress"] = {}
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

def register_user(uid, pw, name, role="student"):
    users = load_users()
    if uid in users:
        return False, "이미 존재하는 아이디입니다."
    users[uid] = {"pw": pw, "name": name, "role": role, "progress": {}}
    save_users(users)
    return True, "회원가입 완료! 로그인해주세요."

def authenticate_user(uid, pw):
    users = load_users()
    if uid in users and users[uid]["pw"] == pw:
        u = users[uid]
        u["id"] = uid
        if "progress" not in u:
            u["progress"] = {}
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
    if "topics" not in user["progress"]:
        user["progress"]["topics"] = {}
    return user

def ensure_topic_progress(user, topic):
    user = ensure_progress(user)
    topics = user["progress"]["topics"]
    if topic not in topics:
        topics[topic] = {
            "learned": {},
            "stats": {"studied_count": 0, "avg_score": 0.0},
            "wrong_notes": []
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
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    scores = [v.get("last_score", 0) for v in learned.values()]
    t["stats"]["studied_count"] = len(learned)
    t["stats"]["avg_score"] = round(sum(scores) / max(1, len(scores)), 2)
    return user

def add_wrong_note(user, topic, q, correct, user_answer):
    user = ensure_topic_progress(user, topic)
    t = user["progress"]["topics"][topic]
    t["wrong_notes"].append({
        "q": q, "a": correct, "user": user_answer,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return user

VOCAB_DB = load_vocab_data()

# =============================================================================
# 2. 메인 앱 로직
# =============================================================================
def main(page: ft.Page):
    page.title = "한국어 학습 앱"
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

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
        "test_score": 0
    }

    # ------------------------------
    # TTS (Web Native)
    # ------------------------------
    def play_tts(text: str):
        try:
            t = json.dumps(text)
            page.run_javascript(f"""
            try {{
                if (!window.speechSynthesis) return;
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance({t});
                u.lang = "ko-KR"; u.rate = 1.0; u.volume = 1.0;
                window.speechSynthesis.speak(u);
            }} catch(e) {{}}
            """)
        except:
            pass

    # ------------------------------
    # Pronunciation / Fluency 평가 (현재 더미)
    # ------------------------------
    def evaluate_pronunciation_dummy(text: str):
        score = random.randint(75, 100)
        if score >= 95:
            comment = "발음이 매우 정확하고 자연스럽습니다."
        elif score >= 88:
            comment = "전체적으로 좋습니다. 억양을 조금만 더 또렷하게 해보세요."
        elif score >= 80:
            comment = "의미 전달은 충분합니다. 받침/연음을 조금 더 신경써보세요."
        else:
            comment = "천천히 또박또박 반복 연습이 필요합니다."
        return score, comment

    def show_snack(msg, color="black"):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def go_to(route):
        page.go(route)

    def feature_item(icon, title, subtitle):
        return ft.Container(
            bgcolor="#f8f9fa", border_radius=20, padding=16,
            content=ft.Row([
                ft.Container(
                    content=ft.Text(icon, size=22),
                    width=44, height=44, bgcolor="white", border_radius=14,
                    alignment=ft.Alignment(0, 0),
                    shadow=ft.BoxShadow(blur_radius=15, color="#14000000")
                ),
                ft.Column([
                    ft.Text(title, size=14, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text(subtitle, size=12, color=COLOR_TEXT_DESC)
                ], spacing=2)
            ])
        )

    # =============================================================================
    # View: Landing
    # =============================================================================
    def view_landing():
        return ft.View(
            route="/",
            controls=[
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=360,
                                bgcolor=COLOR_CARD_BG,
                                border_radius=STYLE_BORDER_RADIUS,
                                padding=35,
                                shadow=STYLE_CARD_SHADOW,
                                content=ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(
                                            content=ft.Text("🇰🇷", size=60),
                                            bgcolor="#f0f6ff",
                                            width=120, height=120, border_radius=30,
                                            alignment=ft.Alignment(0, 0),
                                            margin=ft.margin.only(bottom=20)
                                        ),
                                        ft.Text("한국어 학습", size=30, weight="bold", color=COLOR_TEXT_MAIN),
                                        ft.Text("단어부터 발음, 진도 관리까지\n쉽고 체계적인 한국어 학습",
                                                size=15, color=COLOR_TEXT_DESC, text_align="center"),
                                        ft.Container(height=25),
                                        ft.Column(
                                            spacing=14,
                                            controls=[
                                                feature_item("📘", "체계적 단계별 학습", "토픽/레벨 기반 단어 DB"),
                                                feature_item("🎧", "발음 듣기 & 녹음", "웹 네이티브 TTS 기반"),
                                                feature_item("📊", "진도/오답/복습", "누적 학습 + 오답노트"),
                                            ]
                                        ),
                                        ft.Container(height=30),
                                        ft.ElevatedButton(
                                            "학습 시작하기",
                                            style=ft.ButtonStyle(
                                                bgcolor=COLOR_PRIMARY,
                                                color="white",
                                                padding=20,
                                                shape=ft.RoundedRectangleBorder(radius=15)
                                            ),
                                            width=280,
                                            on_click=lambda _: page.go("/login")
                                        )
                                    ]
                                )
                            )
                        ]
                    ),
                    alignment=ft.Alignment(0, 0),
                    expand=True
                )
            ],
            bgcolor=COLOR_BG,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    # =============================================================================
    # View: Login
    # =============================================================================
    def view_login():
        id_field = ft.TextField(label="아이디", width=280, border_radius=12, bgcolor="white", text_size=14)
        pw_field = ft.TextField(
            label="비밀번호", password=True, width=280, border_radius=12,
            bgcolor="white", text_size=14, can_reveal_password=True
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
                    go_to("/admin_dash")
            else:
                show_snack("로그인 정보가 올바르지 않습니다.", COLOR_ACCENT)

        return ft.View(
            route="/login",
            controls=[
                ft.Container(
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    content=ft.Column([
                        ft.Container(
                            width=360,
                            bgcolor=COLOR_CARD_BG,
                            border_radius=STYLE_BORDER_RADIUS,
                            padding=35,
                            shadow=STYLE_CARD_SHADOW,
                            content=ft.Column([
                                ft.Text("로그인", size=28, weight="bold", color=COLOR_TEXT_MAIN),
                                ft.Text("한국어 학습을 시작해보세요", size=14, color=COLOR_TEXT_DESC),
                                ft.Container(height=20),
                                id_field,
                                ft.Container(height=10),
                                pw_field,
                                ft.Container(height=20),
                                ft.ElevatedButton(
                                    "로그인",
                                    on_click=on_login_click,
                                    width=280, height=50,
                                    style=ft.ButtonStyle(
                                        bgcolor=COLOR_PRIMARY,
                                        color="white",
                                        shape=ft.RoundedRectangleBorder(radius=14)
                                    )
                                ),
                                ft.Container(height=15),
                                ft.Row([
                                    ft.Text("아직 회원이 아니신가요?", size=12, color=COLOR_TEXT_DESC),
                                    ft.Text("회원가입 하기", size=12, color=COLOR_PRIMARY, weight="bold",
                                            spans=[ft.TextSpan(on_click=lambda _: go_to("/signup"))])
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Container(height=10),
                                ft.Text("테스트 계정: student/1111, teacher/1111, admin/1111",
                                        size=11, color="#95a5a6")
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER)
                )
            ],
            bgcolor=COLOR_BG
        )

    # =============================================================================
    # View: Signup
    # =============================================================================
    def view_signup():
        new_id = ft.TextField(label="아이디", width=280)
        new_pw = ft.TextField(label="비밀번호", password=True, width=280, can_reveal_password=True)
        new_name = ft.TextField(label="이름", width=280)

        def on_regist(e):
            if not (new_id.value and new_pw.value and new_name.value):
                return show_snack("모든 항목을 입력해주세요.", COLOR_ACCENT)
            ok, msg = register_user(new_id.value, new_pw.value, new_name.value, "student")
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)
            if ok:
                go_to("/login")

        return ft.View(
            route="/signup",
            controls=[
                ft.AppBar(
                    title=ft.Text("회원가입"),
                    # ✅ 아이콘 enum 제거: 문자열로 통일
                    leading=ft.IconButton(icon="arrow_back", on_click=lambda _: go_to("/login"))
                ),
                ft.Container(
                    alignment=ft.Alignment(0, 0),
                    padding=20,
                    content=ft.Column([
                        new_id, new_pw, new_name,
                        ft.Container(height=10),
                        ft.ElevatedButton("가입하기", on_click=on_regist, width=280,
                                          bgcolor=COLOR_PRIMARY, color="white")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ],
            bgcolor="white"
        )

    # =============================================================================
    # View: Student Home
    # =============================================================================
    def view_student_home():
        user = session["user"]
        user = ensure_progress(user)
        goal_field = ft.TextField(
            label="오늘 목표량(단어 수)",
            value=str(session["goal"]),
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=12
        )

        def save_goal(e=None):
            try:
                g = int(goal_field.value)
                g = max(1, min(100, g))
            except:
                g = int(sysdata.get("default_goal", 10))
            session["goal"] = g
            user["progress"]["settings"]["goal"] = g
            update_user(user["id"], user)
            show_snack(f"목표량이 {g}개로 저장되었습니다.", COLOR_PRIMARY)

        topics = sorted(list(VOCAB_DB.keys()))

        def make_topic_btn(topic_name):
            user2 = get_user(user["id"]) or user
            user2 = ensure_progress(user2)
            tp = user2["progress"]["topics"].get(topic_name, {})
            studied = len(tp.get("learned", {}))
            avg = tp.get("stats", {}).get("avg_score", 0.0)

            return ft.Container(
                content=ft.Column([
                    ft.Text(topic_name, size=16, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text(f"누적 학습: {studied}개", size=12, color=COLOR_TEXT_DESC),
                    ft.Text(f"평균 점수: {avg}", size=12, color=COLOR_TEXT_DESC),
                    ft.Container(height=6),
                    ft.Text("학습하기", size=12, color=COLOR_PRIMARY)
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLOR_CARD_BG,
                border_radius=15,
                border=ft.border.all(2, "#eee"),
                padding=12,
                on_click=lambda e: start_study(topic_name),
                ink=True,
                alignment=ft.Alignment(0, 0)
            )

        def start_study(topic_name):
            if topic_name not in VOCAB_DB:
                show_snack("아직 준비 중인 토픽입니다.", COLOR_ACCENT)
                return

            all_words = VOCAB_DB[topic_name]
            goal = session["goal"]
            pick = all_words[:goal] if len(all_words) >= goal else all_words[:]

            session.update({
                "topic": topic_name,
                "study_words": pick,
                "idx": 0
            })
            go_to("/study")

        topic_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=170,
            child_aspect_ratio=1.25,
            spacing=15,
            run_spacing=15,
            controls=[make_topic_btn(tp) for tp in topics] if topics else [ft.Text("엑셀 데이터가 없습니다.")]
        )

        return ft.View(
            route="/student_home",
            controls=[
                ft.AppBar(
                    title=ft.Text("학습 홈", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG,
                    elevation=0,
                    # ✅ 아이콘 enum 제거: 문자열로 통일
                    actions=[
                        ft.IconButton(icon="format_list_bulleted", tooltip="누적 학습", icon_color=COLOR_TEXT_DESC,
                                      on_click=lambda _: go_to("/cumulative")),
                        ft.IconButton(icon="bookmark", tooltip="오답노트", icon_color=COLOR_TEXT_DESC,
                                      on_click=lambda _: go_to("/wrong_notes")),
                        ft.IconButton(icon="replay", tooltip="복습", icon_color=COLOR_TEXT_DESC,
                                      on_click=lambda _: go_to("/review")),
                        ft.IconButton(icon="logout", tooltip="로그아웃", icon_color=COLOR_TEXT_DESC,
                                      on_click=lambda _: go_to("/login")),
                    ],
                    automatically_imply_leading=False
                ),
                ft.Container(
                    padding=20,
                    expand=True,
                    content=ft.Column([
                        ft.Text(f"반가워요, {user['name']}님!", size=20, weight="bold", color=COLOR_PRIMARY),
                        ft.Text("오늘 공부할 토픽(레벨)을 선택해주세요.", size=14, color=COLOR_TEXT_DESC),
                        ft.Container(height=10),
                        ft.Row([
                            goal_field,
                            ft.ElevatedButton("저장", on_click=save_goal,
                                              bgcolor=COLOR_PRIMARY, color="white")
                        ], alignment=ft.MainAxisAlignment.START, spacing=10),
                        ft.Container(height=15),
                        ft.Container(content=topic_grid, expand=True)
                    ])
                )
            ],
            bgcolor=COLOR_BG
        )

    # =============================================================================
    # View: Study
    # =============================================================================
    def view_study():
        words = session.get("study_words", [])
        topic = session.get("topic", "")
        if not words:
            return ft.View(route="/study", controls=[ft.Text("데이터 없음")], bgcolor=COLOR_BG)

        class StudyState:
            idx = session.get("idx", 0)
            is_front = True

        st = StudyState()
        total = len(words)

        overlay_content = ft.Column(scroll="auto", expand=True)
        overlay_container = ft.Container(visible=False)

        score_label = ft.Text("0", size=24, weight="bold", color=COLOR_EVAL)
        comment_label = ft.Text("", size=12, color=COLOR_TEXT_DESC, text_align="center")

        def open_overlay_for_word(word_item, score, comment):
            overlay_content.controls = [
                ft.Container(
                    bgcolor="#f8f9fa", padding=10, border_radius=10, margin=ft.margin.only(bottom=8),
                    content=ft.Row([
                        ft.Text(word_item.get("word", ""), size=14, weight="bold"),
                        ft.Text(f"{score}점", color=COLOR_EVAL if score >= 85 else COLOR_ACCENT, weight="bold")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ),
                ft.Text(comment, size=12, color=COLOR_TEXT_DESC),
                ft.Divider()
            ]
            for char in word_item.get("word", ""):
                overlay_content.controls.append(
                    ft.Container(
                        padding=10,
                        content=ft.Row([
                            ft.Text(f"음절 '{char}'", size=12),
                            ft.Text(f"{random.randint(80, 100)}점", size=12, color=COLOR_EVAL)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        border=ft.border.only(bottom=ft.BorderSide(1, "#eee"))
                    )
                )

            score_label.value = str(score)
            comment_label.value = comment
            overlay_container.visible = True
            page.update()

        def close_overlay(e=None):
            overlay_container.visible = False
            page.update()

        def persist_study_result(word_item, score):
            user = get_user(session["user"]["id"]) or session["user"]
            user = update_learned_word(user, topic, word_item, score)
            update_user(user["id"], user)
            session["user"] = user

        def render_card_content():
            w = words[st.idx]
            if st.is_front:
                return ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text("◀", color=COLOR_PRIMARY),
                            on_click=lambda _: go_to("/student_home"),
                            padding=5, border_radius=5, bgcolor="#f0f4f8"
                        ),
                        ft.Text(f"{topic} ({st.idx+1}/{total})", size=12, color="grey")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Container(height=30),
                    ft.Container(
                        content=ft.Text(w.get("image", "📖"), size=60),
                        width=120, height=120, bgcolor="#f8f9fa", border_radius=60,
                        alignment=ft.Alignment(0, 0)
                    ),
                    ft.Text(w["word"], size=36, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text(w.get("pronunciation", ""), size=16, color=COLOR_SECONDARY),

                    ft.Container(
                        bgcolor="#fff9f0", padding=15, border_radius=12, margin=ft.margin.only(top=20),
                        content=ft.Column([
                            ft.Text(w.get("mean", ""), size=16, weight="bold",
                                    color=COLOR_TEXT_MAIN, text_align="center"),
                            ft.Text(w.get("desc", ""), size=12, color="#8a7e6a",
                                    italic=True, text_align="center")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.ElevatedButton("🔊 발음 듣기", on_click=lambda e: play_tts(w["word"]),
                                          expand=True, bgcolor=COLOR_PRIMARY, color="white"),
                        ft.ElevatedButton("다음 ▶", on_click=lambda e: change_card(1),
                                          expand=True, bgcolor=COLOR_TEXT_MAIN, color="white"),
                    ], spacing=10)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            else:
                return ft.Column([
                    ft.Text(w["word"], size=28, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(
                        bgcolor="#eef5ff", padding=15, border_radius=15, margin=ft.margin.symmetric(vertical=20),
                        border=ft.border.only(left=ft.BorderSide(5, COLOR_PRIMARY)),
                        content=ft.Column([
                            ft.Text("[Example]", size=12, color=COLOR_PRIMARY, weight="bold"),
                            ft.Text(w.get("ex", ""), size=16, color=COLOR_TEXT_MAIN)
                        ])
                    ),
                    ft.Row([
                        ft.ElevatedButton("▶ 문장 듣기", on_click=lambda e: play_tts(w.get("ex", "")),
                                          expand=True, bgcolor=COLOR_PRIMARY, color="white"),
                        ft.ElevatedButton("🎙 발음 평가", on_click=lambda e: do_pron_eval(),
                                          expand=True, bgcolor=COLOR_ACCENT, color="white")
                    ], spacing=10),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.OutlinedButton("이전", on_click=lambda e: change_card(-1), expand=True),
                        ft.OutlinedButton("다음", on_click=lambda e: change_card(1), expand=True)
                    ], spacing=10)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        def update_view():
            if card_container.page:
                card_container.content = render_card_content()
                card_container.update()

        def flip_card(e):
            st.is_front = not st.is_front
            update_view()

        def do_pron_eval():
            w = words[st.idx]
            score, comment = evaluate_pronunciation_dummy(w["word"])
            persist_study_result(w, score)
            open_overlay_for_word(w, score, comment)

        def change_card(delta):
            new_idx = st.idx + delta
            if 0 <= new_idx < total:
                st.idx = new_idx
                session["idx"] = new_idx
                st.is_front = True
                update_view()
            elif new_idx >= total:
                show_snack("목표량 학습 완료! 테스트로 이동합니다. 📝", COLOR_EVAL)
                prepare_test_queue()
                go_to("/test")

        def prepare_test_queue():
            q = []
            for w in words:
                q.append({
                    "type": "meaning",
                    "word": w["word"],
                    "correct": w.get("mean", ""),
                    "example": w.get("ex", "")
                })
            random.shuffle(q)
            session["test_queue"] = q
            session["test_idx"] = 0
            session["test_score"] = 0

        overlay_container = ft.Container(
            visible=False,
            bgcolor="#4D000000",
            alignment=ft.Alignment(0, 0),
            expand=True,
            content=ft.Container(
                width=330, height=560,
                bgcolor="white",
                border_radius=25,
                padding=20,
                shadow=ft.BoxShadow(blur_radius=20, color="black"),
                content=ft.Column([
                    ft.Text("발음/유창성 평가", size=18, weight="bold"),
                    ft.Divider(),
                    ft.Container(
                        width=90, height=90, border_radius=45,
                        border=ft.border.all(5, COLOR_EVAL),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column([
                            score_label,
                            ft.Text("점수", size=10, color="grey")
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=0)
                    ),
                    ft.Container(height=8),
                    comment_label,
                    ft.Container(height=8),
                    ft.Container(content=overlay_content, expand=True),
                    ft.Row([
                        ft.ElevatedButton("닫기", on_click=close_overlay,
                                          expand=True, bgcolor=COLOR_TEXT_MAIN, color="white"),
                    ], spacing=10)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )

        card_container = ft.Container(
            content=render_card_content(),
            width=340, height=520,
            bgcolor=COLOR_CARD_BG,
            border_radius=25,
            padding=25,
            shadow=STYLE_CARD_SHADOW,
            alignment=ft.Alignment(0, 0),
            animate=ft.Animation(400, "easeOut"),
            on_click=lambda e: flip_card(e)
        )

        return ft.View(
            route="/study",
            controls=[
                ft.Stack([
                    ft.Container(
                        padding=20,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                        content=ft.Column([
                            ft.Container(height=20),
                            card_container,
                            ft.Text("카드를 터치하여 앞/뒤를 전환하세요", color="#bdc3c7", size=12, visible=True)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    overlay_container
                ], expand=True)
            ],
            bgcolor=COLOR_BG
        )

    # =============================================================================
    # View: Test
    # =============================================================================
    def view_test():
        qlist = session.get("test_queue", [])
        if not qlist:
            return ft.View(
                route="/test",
                controls=[ft.Text("테스트 데이터가 없습니다."),
                          ft.ElevatedButton("홈", on_click=lambda _: go_to("/student_home"))],
                bgcolor=COLOR_BG
            )

        idx = session.get("test_idx", 0)
        idx = max(0, min(idx, len(qlist)-1))
        q = qlist[idx]
        topic = session.get("topic", "")
        total = len(qlist)

        answer = ft.TextField(label="정답을 입력하세요", width=320, bgcolor="white", border_radius=12)
        prompt_text = ft.Text(f"[{idx+1}/{total}] 뜻을 입력하세요: {q['word']}",
                              size=16, weight="bold", color=COLOR_TEXT_MAIN)

        def submit(e):
            user_ans = (answer.value or "").strip()
            correct = (q.get("correct") or "").strip()
            ok = (correct != "" and (user_ans == correct or (user_ans in correct) or (correct in user_ans)))
            if ok:
                session["test_score"] += 1
                show_snack("정답!", COLOR_EVAL)
            else:
                show_snack("오답! 오답노트에 저장되었습니다.", COLOR_ACCENT)
                user = get_user(session["user"]["id"]) or session["user"]
                user = add_wrong_note(user, topic, q['word'], correct, user_ans)
                update_user(user["id"], user)
                session["user"] = user

            session["test_idx"] = idx + 1
            if session["test_idx"] >= total:
                go_to("/test_result")
            else:
                go_to("/test")

        return ft.View(
            route="/test",
            controls=[
                ft.AppBar(
                    title=ft.Text("테스트", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG,
                    elevation=0,
                    # ✅ 문자열 아이콘
                    leading=ft.IconButton(icon="arrow_back", on_click=lambda _: go_to("/student_home"))
                ),
                ft.Container(
                    padding=20,
                    expand=True,
                    content=ft.Column([
                        ft.Container(
                            bgcolor="white", border_radius=20, padding=20,
                            shadow=STYLE_CARD_SHADOW,
                            content=ft.Column([
                                prompt_text,
                                ft.Container(height=10),
                                ft.Text("🔊 듣기(단어 TTS)", size=12, color=COLOR_TEXT_DESC),
                                ft.ElevatedButton("재생", on_click=lambda _: play_tts(q["word"]),
                                                  bgcolor=COLOR_PRIMARY, color="white"),
                                ft.Container(height=10),
                                answer,
                                ft.Container(height=10),
                                ft.ElevatedButton("제출", on_click=submit, width=320,
                                                  bgcolor=COLOR_TEXT_MAIN, color="white")
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ],
            bgcolor=COLOR_BG
        )

    def view_test_result():
        qlist = session.get("test_queue", [])
        total = len(qlist) if qlist else 0
        score = session.get("test_score", 0)
        ratio = int((score / max(1, total)) * 100)

        return ft.View(
            route="/test_result",
            controls=[
                ft.AppBar(
                    title=ft.Text("테스트 결과", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG, elevation=0,
                    # ✅ 문자열 아이콘
                    leading=ft.IconButton(icon="arrow_back", on_click=lambda _: go_to("/student_home"))
                ),
                ft.Container(
                    padding=20, expand=True,
                    content=ft.Column([
                        ft.Container(
                            width=360,
                            bgcolor="white",
                            border_radius=20,
                            padding=25,
                            shadow=STYLE_CARD_SHADOW,
                            content=ft.Column([
                                ft.Text("수고하셨습니다! 🎉", size=22, weight="bold", color=COLOR_PRIMARY),
                                ft.Container(height=10),
                                ft.Text(f"점수: {score}/{total} ({ratio}%)", size=18, weight="bold",
                                        color=COLOR_TEXT_MAIN),
                                ft.Container(height=10),
                                ft.Text("오답은 오답노트에서 확인할 수 있습니다.", size=13, color=COLOR_TEXT_DESC),
                                ft.Container(height=20),
                                ft.Row([
                                    ft.ElevatedButton("오답노트", on_click=lambda _: go_to("/wrong_notes"),
                                                      expand=True, bgcolor=COLOR_ACCENT, color="white"),
                                    ft.ElevatedButton("홈", on_click=lambda _: go_to("/student_home"),
                                                      expand=True, bgcolor=COLOR_TEXT_MAIN, color="white")
                                ], spacing=10)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ],
            bgcolor=COLOR_BG
        )

    # =============================================================================
    # View: Cumulative
    # =============================================================================
    def view_cumulative():
        user = get_user(session["user"]["id"]) or session["user"]
        user = ensure_progress(user)

        topic_dd = ft.Dropdown(
            width=240,
            options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())],
            value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None)
        )

        mask_dd = ft.Dropdown(
            width=140,
            options=[
                ft.dropdown.Option("none", "가리기 없음"),
                ft.dropdown.Option("word", "단어 가리기"),
                ft.dropdown.Option("mean", "뜻 가리기"),
            ],
            value=session.get("mask_mode", "none")
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
                        bgcolor="white", border_radius=14, padding=12,
                        border=ft.border.all(1, "#eee"),
                        content=ft.Row([
                            ft.Column([
                                ft.Text(word_txt, size=16, weight="bold", color=COLOR_TEXT_MAIN),
                                ft.Text(mean_txt, size=12, color=COLOR_TEXT_DESC),
                                ft.Text(info.get("last_seen", ""), size=10, color="#95a5a6")
                            ], expand=True),
                            ft.Container(
                                padding=8, border_radius=10,
                                bgcolor="#f0fdf4" if sc >= 85 else "#fff5f5",
                                content=ft.Text(f"{sc}점", weight="bold",
                                                color=COLOR_EVAL if sc >= 85 else COLOR_ACCENT)
                            )
                        ])
                    )
                )

            if not controls:
                controls = [ft.Text("아직 누적 학습 데이터가 없습니다.", color=COLOR_TEXT_DESC)]
            list_col.controls = controls
            page.update()

        topic_dd.on_change = lambda e: render()
        mask_dd.on_change = lambda e: render()
        render()

        return ft.View(
            route="/cumulative",
            controls=[
                ft.AppBar(
                    title=ft.Text("누적 학습", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG, elevation=0,
                    # ✅ 문자열 아이콘
                    leading=ft.IconButton(icon="arrow_back", on_click=lambda _: go_to("/student_home"))
                ),
                ft.Container(
                    padding=20, expand=True,
                    content=ft.Column([
                        ft.Row([topic_dd, mask_dd], spacing=10),
                        ft.Container(height=10),
                        list_col
                    ])
                )
            ],
            bgcolor=COLOR_BG
        )

    # =============================================================================
    # View: Wrong Notes
    # =============================================================================
    def view_wrong_notes():
        user = get_user(session["user"]["id"]) or session["user"]
        user = ensure_progress(user)

        topic_dd = ft.Dropdown(
            width=240,
            options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())],
            value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None)
        )
        col = ft.Column(scroll="auto", expand=True)

        def render():
            tp = topic_dd.value
            if not tp:
                col.controls = [ft.Text("토픽이 없습니다.")]
                page.update()
                return

            tpdata = user["progress"]["topics"].get(tp, {})
            wrongs = tpdata.get("wrong_notes", [])
            wrongs = list(reversed(wrongs))
            controls = []

            for it in wrongs:
                controls.append(
                    ft.Container(
                        bgcolor="white", border_radius=14, padding=12,
                        border=ft.border.all(1, "#eee"),
                        content=ft.Column([
                            ft.Text(f"문제: {it.get('q','')}", weight="bold", color=COLOR_TEXT_MAIN),
                            ft.Text(f"정답: {it.get('a','')}", color=COLOR_EVAL),
                            ft.Text(f"내 답: {it.get('user','')}", color=COLOR_ACCENT),
                            ft.Text(it.get("ts", ""), size=10, color="#95a5a6")
                        ], spacing=4)
                    )
                )

            if not controls:
                controls = [ft.Text("오답노트가 비어 있습니다.", color=COLOR_TEXT_DESC)]
            col.controls = controls
            page.update()

        topic_dd.on_change = lambda e: render()
        render()

        return ft.View(
            route="/wrong_notes",
            controls=[
                ft.AppBar(
                    title=ft.Text("오답노트", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG, elevation=0,
                    # ✅ 문자열 아이콘
                    leading=ft.IconButton(icon="arrow_back", on_click=lambda _: go_to("/student_home"))
                ),
                ft.Container(
                    padding=20, expand=True,
                    content=ft.Column([
                        ft.Row([topic_dd], spacing=10),
                        ft.Container(height=10),
                        col
                    ])
                )
            ],
            bgcolor=COLOR_BG
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
            width=240,
            options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())],
            value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None)
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
                    bgcolor="white", border_radius=14, padding=12,
                    content=ft.Row([
                        ft.Text(f"복습 기준: {thr}점 미만", color=COLOR_TEXT_DESC),
                        ft.ElevatedButton("복습 시작", on_click=lambda _: start_review(tp),
                                          bgcolor=COLOR_ACCENT, color="white")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            ]
            for w, info in low[:200]:
                controls.append(
                    ft.Container(
                        bgcolor="white", border_radius=14, padding=12,
                        border=ft.border.all(1, "#eee"),
                        content=ft.Row([
                            ft.Column([
                                ft.Text(w, weight="bold", color=COLOR_TEXT_MAIN),
                                ft.Text(info.get("mean", ""), size=12, color=COLOR_TEXT_DESC)
                            ], expand=True),
                            ft.Text(f"{info.get('last_score',0)}점", color=COLOR_ACCENT, weight="bold")
                        ])
                    )
                )
            if len(controls) == 1:
                controls.append(ft.Text("복습 대상이 없습니다.", color=COLOR_TEXT_DESC))
            col.controls = controls
            page.update()

        topic_dd.on_change = lambda e: render()
        render()

        return ft.View(
            route="/review",
            controls=[
                ft.AppBar(
                    title=ft.Text("복습", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG, elevation=0,
                    # ✅ 문자열 아이콘
                    leading=ft.IconButton(icon="arrow_back", on_click=lambda _: go_to("/student_home"))
                ),
                ft.Container(
                    padding=20, expand=True,
                    content=ft.Column([
                        ft.Row([topic_dd], spacing=10),
                        ft.Container(height=10),
                        col
                    ])
                )
            ],
            bgcolor=COLOR_BG
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

            rows.append({
                "name": u.get("name", uid),
                "goal": goal,
                "learned": total_learned,
                "ratio": ratio,
                "avg": avg_score,
                "wrong": wrong_cnt
            })

        rows.sort(key=lambda x: (-x["ratio"], -x["avg"], x["name"]))

        cards = []
        for s in rows:
            cards.append(
                ft.Container(
                    bgcolor="white", padding=15, border_radius=15, margin=ft.margin.only(bottom=10),
                    border=ft.border.all(1, "#eee"),
                    content=ft.Row([
                        ft.Column([
                            ft.Text(s["name"], weight="bold", size=16),
                            ft.Text(f"목표: {s['goal']}개 | 누적: {s['learned']}개", size=12, color="grey"),
                            ft.Text(f"평균 점수: {s['avg']} | 오답: {s['wrong']}", size=12, color="grey"),
                        ]),
                        ft.Container(
                            padding=8, border_radius=10,
                            bgcolor="#eef5ff",
                            content=ft.Text(f"{s['ratio']}%", weight="bold", color=COLOR_PRIMARY)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            )

        if not cards:
            cards = [ft.Text("학생 계정이 없습니다.", color=COLOR_TEXT_DESC)]

        return ft.View(
            route="/teacher_dash",
            controls=[
                ft.AppBar(
                    title=ft.Text("선생님 대시보드", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG, elevation=0,
                    # ✅ 문자열 아이콘
                    actions=[ft.IconButton(icon="logout", on_click=lambda _: go_to("/login"))],
                    automatically_imply_leading=False
                ),
                ft.Container(
                    padding=20, scroll="auto", expand=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                expand=True, bgcolor=COLOR_PRIMARY, padding=20, border_radius=20,
                                content=ft.Column([
                                    ft.Text("학생 수", color="white"),
                                    ft.Text(str(len(rows)), size=24, weight="bold", color="white")
                                ])
                            ),
                            ft.Container(
                                expand=True, bgcolor="white", padding=20, border_radius=20,
                                content=ft.Column([
                                    ft.Text("관리 지표", color=COLOR_TEXT_DESC),
                                    ft.Text("진도/평균/오답", size=18, weight="bold", color=COLOR_TEXT_MAIN)
                                ])
                            )
                        ], spacing=10),
                        ft.Container(height=20),
                        ft.Text("학생 목록", size=18, weight="bold"),
                        ft.Container(height=10),
                        ft.Column(cards)
                    ])
                )
            ],
            bgcolor=COLOR_BG
        )

    # =============================================================================
    # View: Admin Dashboard
    # =============================================================================
    def view_admin_dash():
        sysdata_local = load_system()

        default_goal_field = ft.TextField(
            label="기본 목표량(default_goal)",
            value=str(sysdata_local.get("default_goal", 10)),
            width=260,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=12
        )
        review_thr_field = ft.TextField(
            label="복습 기준(review_threshold)",
            value=str(sysdata_local.get("review_threshold", 85)),
            width=260,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=12
        )
        api_key_field = ft.TextField(
            label="OpenAI API Key(저장만)",
            value=str(sysdata_local.get("api", {}).get("openai_api_key", "")),
            width=320,
            password=True,
            can_reveal_password=True,
            bgcolor="white",
            border_radius=12
        )
        stt_provider_field = ft.Dropdown(
            label="STT Provider",
            width=200,
            value=str(sysdata_local.get("api", {}).get("stt_provider", "none")),
            options=[
                ft.dropdown.Option("none"),
                ft.dropdown.Option("openai"),
                ft.dropdown.Option("google"),
                ft.dropdown.Option("aws"),
            ]
        )

        log_box = ft.TextField(
            label="최근 로그(읽기 전용)",
            value="",
            multiline=True,
            read_only=True,
            min_lines=10,
            max_lines=18,
            width=360,
            bgcolor="white",
            border_radius=12
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

        return ft.View(
            route="/admin_dash",
            controls=[
                ft.AppBar(
                    title=ft.Text("관리자", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG, elevation=0,
                    # ✅ 문자열 아이콘
                    actions=[ft.IconButton(icon="logout", on_click=lambda _: go_to("/login"))],
                    automatically_imply_leading=False
                ),
                ft.Container(
                    padding=20, scroll="auto", expand=True,
                    content=ft.Column([
                        ft.Text("시스템 설정", size=18, weight="bold", color=COLOR_TEXT_MAIN),
                        ft.Container(height=10),
                        ft.Container(
                            bgcolor="white", border_radius=20, padding=15,
                            content=ft.Column([
                                default_goal_field,
                                review_thr_field,
                                ft.Divider(),
                                ft.Text("API 설정(저장만 / 기능 연결은 별도)", size=12, color=COLOR_TEXT_DESC),
                                stt_provider_field,
                                api_key_field,
                                ft.Container(height=10),
                                ft.ElevatedButton("저장", on_click=save_admin_settings,
                                                  bgcolor=COLOR_PRIMARY, color="white", width=200)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        ),
                        ft.Container(height=20),
                        ft.Text("로그", size=18, weight="bold", color=COLOR_TEXT_MAIN),
                        ft.Row([
                            ft.ElevatedButton("새로고침", on_click=refresh_log,
                                              bgcolor=COLOR_TEXT_MAIN, color="white")
                        ]),
                        log_box
                    ])
                )
            ],
            bgcolor=COLOR_BG
        )

    # =============================================================================
    # Routing
    # =============================================================================
    def route_change(e: ft.RouteChangeEvent):
        log_write(f"route_change: {page.route}")
        page.views.clear()

        if page.route == "/":
            page.views.append(view_landing())
        elif page.route == "/login":
            page.views.append(view_login())
        elif page.route == "/signup":
            page.views.append(view_signup())
        elif page.route == "/student_home":
            page.views.append(view_student_home())
        elif page.route == "/study":
            page.views.append(view_study())
        elif page.route == "/test":
            page.views.append(view_test())
        elif page.route == "/test_result":
            page.views.append(view_test_result())
        elif page.route == "/cumulative":
            page.views.append(view_cumulative())
        elif page.route == "/wrong_notes":
            page.views.append(view_wrong_notes())
        elif page.route == "/review":
            page.views.append(view_review())
        elif page.route == "/teacher_dash":
            page.views.append(view_teacher_dash())
        elif page.route == "/admin_dash":
            page.views.append(view_admin_dash())
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
    print("http://localhost:8099 에서 접속하세요.")
    try:
        view_mode = ft.AppView.WEB_BROWSER
    except AttributeError:
        view_mode = "web_browser"
    ft.app(target=main, port=8099, view=view_mode)
