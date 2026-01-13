import flet as ft
import pandas as pd
import random
import os
import json
import warnings
from datetime import datetime

# 불필요한 경고 숨기기
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

# 스타일 정의
STYLE_BORDER_RADIUS = 28
# 그림자: ft.colors 사용 대신 HEX 문자열 사용 (호환성 확보)
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

def load_vocab_data():
    """엑셀 파일 로드"""
    global VOCAB_DB
    vocab_db = {}
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(current_dir, "data", "vocabulary.xlsx")
    os.makedirs(os.path.join(current_dir, "data"), exist_ok=True)
    
    if not os.path.exists(excel_path):
        dummy_data = []
        for i in range(1, 11):
            dummy_data.append({
                "word": f"테스트단어{i}", "mean": "테스트 의미", "ex": f"이것은 예문입니다 {i}", 
                "desc": "설명", "pronunciation": f"[단어{i}]", "image": "📝"
            })
        return {"초급1": dummy_data, "초급2": dummy_data, "중급1": dummy_data}

    try:
        print(f"📂 엑셀 로딩 중... ({excel_path})")
        all_sheets = pd.read_excel(excel_path, sheet_name=None, engine='openpyxl')
        
        for sheet_name, df in all_sheets.items():
            df = df.fillna("")
            items = []
            for _, row in df.iterrows():
                if "단어" not in row: continue
                
                word_item = {
                    "word": str(row.get("단어", "")).strip(),
                    "mean": str(row.get("의미", row.get("뜻", ""))).strip(),
                    "ex": str(row.get("예문", row.get("예문1", ""))).strip(),
                    "desc": str(row.get("설명", row.get("주제", ""))).strip(),
                    "pronunciation": str(row.get("발음", "")).strip(),
                    "image": str(row.get("이미지", "📖")).strip()
                }
                if not word_item["pronunciation"]:
                    word_item["pronunciation"] = f"[{word_item['word']}]"
                
                items.append(word_item)
            
            if items:
                vocab_db[sheet_name] = items
                print(f"✅ [{sheet_name}] 로드 완료 ({len(items)}개)")
        return vocab_db
    except Exception as e:
        print(f"❌ 엑셀 읽기 실패: {e}")
        return {}

# --- 사용자 관리 ---
def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {"admin": {"pw": "1111", "name": "관리자", "role": "admin"}}
        save_users(default_users)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_users(users_data):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=4)
    except Exception as e: print(f"❌ 저장 실패: {e}")

def register_user(uid, pw, name, role):
    users = load_users()
    if uid in users: return False, "이미 존재하는 아이디입니다."
    users[uid] = {"pw": pw, "name": name, "role": role, "progress": {}}
    save_users(users)
    return True, "회원가입 완료! 로그인해주세요."

def authenticate_user(uid, pw):
    users = load_users()
    if uid == "student" and pw == "1111":
        return True, {"id": "student", "name": "학습자", "role": "student", "progress": {}}
    if uid == "teacher" and pw == "1111":
        return True, {"id": "teacher", "name": "선생님", "role": "teacher"}
        
    if uid in users and users[uid]["pw"] == pw:
        u = users[uid]
        u["id"] = uid
        if "progress" not in u: u["progress"] = {}
        save_users(users)
        return True, u
    return False, None

VOCAB_DB = load_vocab_data()

# =============================================================================
# 2. 메인 앱 로직
# =============================================================================

def main(page: ft.Page):
    page.title = "한국어 학습 앱"
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    #page.scroll = "adaptive"
    
    page.fonts = {
        "Pretendard": "https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"
    }
    page.theme = ft.Theme(font_family="Pretendard")

    session = {"user": None, "level": "", "study_words": [], "idx": 0}

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
        except: pass

    def show_snack(msg, color="black"):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def go_to(route):
        page.go(route)

    # --- View 1: 랜딩 페이지 ---
    def view_landing():
        return ft.View(
            route="/",
            controls=[
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER, # 수직 중앙 정렬 추가
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
                                            alignment=ft.Alignment(0, 0), # 수정됨
                                            margin=ft.margin.only(bottom=20)
                                        ),
                                        ft.Text("한국어 학습", size=30, weight="bold", color=COLOR_TEXT_MAIN),
                                        ft.Text("단어부터 발음, 진도 관리까지\n쉽고 체계적인 한국어 학습", 
                                                size=15, color=COLOR_TEXT_DESC, text_align="center"),
                                        ft.Container(height=25),
                                        ft.Column(
                                            spacing=14,
                                            controls=[
                                                feature_item("📘", "체계적 단계별 학습", "표준 교육과정 기반"),
                                                feature_item("🎧", "발음 녹음 & 평가", "정확한 발음 진단"),
                                                feature_item("📊", "학습 진도 관리", "맞춤형 진도 체크"),
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
                                            on_click=lambda _: page.go("/login") # 직접 이동 권장
                                        )
                                    ]
                                )
                            )
                        ]
                    ),
                    alignment=ft.Alignment(0, 0), # 수정됨
                    expand=True # 매우 중요: 화면 전체를 채워야 보입니다.
                )
            ],
            bgcolor=COLOR_BG,
            vertical_alignment=ft.MainAxisAlignment.CENTER, # View 자체 정렬
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

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

    # --- View 2: 로그인 ---
    def view_login():
        id_field = ft.TextField(label="아이디", width=280, border_radius=12, bgcolor="white", text_size=14)
        pw_field = ft.TextField(label="비밀번호", password=True, width=280, border_radius=12, bgcolor="white", text_size=14, can_reveal_password=True)
        
        role_group = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="student", label="학생"),
                ft.Radio(value="teacher", label="선생님"),
                ft.Radio(value="admin", label="관리자"),
            ], alignment=ft.MainAxisAlignment.CENTER),
            value="student"
        )

        def on_login_click(e):
            if not id_field.value or not pw_field.value:
                return show_snack("아이디와 비밀번호를 입력해주세요.", COLOR_ACCENT)
            
            ok, user = authenticate_user(id_field.value, pw_field.value)
            if ok:
                session["user"] = user
                show_snack(f"환영합니다, {user['name']}님!", COLOR_PRIMARY)
                if user["role"] == "student":
                    go_to("/student_home")
                else:
                    go_to("/teacher_dash")
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
                                role_group,
                                ft.Container(height=10),
                                id_field,
                                ft.Container(height=10),
                                pw_field,
                                ft.Container(height=20),
                                ft.ElevatedButton(
                                    "로그인", 
                                    on_click=on_login_click, 
                                    width=280, height=50,
                                    style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="white", shape=ft.RoundedRectangleBorder(radius=14))
                                ),
                                ft.Container(height=15),
                                ft.Row([
                                    ft.Text("아직 회원이 아니신가요?", size=12, color=COLOR_TEXT_DESC),
                                    ft.Text("회원가입 하기", size=12, color=COLOR_PRIMARY, weight="bold", 
                                            spans=[ft.TextSpan(on_click=lambda _: go_to("/signup"))])
                                ], alignment=ft.MainAxisAlignment.CENTER)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER)
                )
            ],
            bgcolor=COLOR_BG
        )

    # --- View 3: 학생 홈 ---
    def view_student_home():
        def make_level_btn(level_name):
            return ft.Container(
                content=ft.Column([
                    ft.Text(level_name, size=16, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text("학습하기", size=12, color=COLOR_PRIMARY)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COLOR_CARD_BG,
                border_radius=15,
                border=ft.border.all(2, "#eee"),
                padding=10,
                on_click=lambda e: start_study(level_name),
                ink=True,
                alignment=ft.Alignment(0, 0)
            )

        def start_study(level_name):
            if level_name not in VOCAB_DB:
                show_snack("아직 준비 중인 레벨입니다.")
                return
            
            all_words = VOCAB_DB[level_name]
            session.update({
                "level": level_name,
                "study_words": all_words[:10],
                "idx": 0
            })
            go_to("/study")

        level_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=160,
            child_aspect_ratio=1.3,
            spacing=15,
            run_spacing=15,
            controls=[make_level_btn(lv) for lv in ["초급1", "초급2", "중급1", "중급2", "고급1", "고급2"]]
        )

        return ft.View(
            route="/student_home",
            controls=[
                ft.AppBar(
                    title=ft.Text("학습 레벨 선택", color=COLOR_TEXT_MAIN, weight="bold"),
                    bgcolor=COLOR_BG,
                    elevation=0,
                    actions=[
                        ft.IconButton(icon="logout", icon_color=COLOR_TEXT_DESC, on_click=lambda _: go_to("/login"))
                    ],
                    automatically_imply_leading=False
                ),
                ft.Container(
                    padding=20,
                    expand=True,
                    content=ft.Column([
                        ft.Text(f"반가워요, {session['user']['name']}님!", size=20, weight="bold", color=COLOR_PRIMARY),
                        ft.Text("오늘 공부할 단계를 선택해주세요.", size=14, color=COLOR_TEXT_DESC),
                        ft.Container(height=20),
                        ft.Container(content=level_grid, expand=True)
                    ])
                )
            ],
            bgcolor=COLOR_BG
        )

    # --- View 4: 학습 화면 (Flashcard + Overlay) ---
    def view_study():
        # 1. 기초 데이터 및 상태 준비
        words = session.get("study_words", [])
        if not words: 
            return ft.View(route="/study", controls=[ft.Text("데이터 없음")])

        class StudyState:
            idx = session.get("idx", 0)
            is_front = True
        
        st = StudyState()
        total = len(words)

        # 2. UI 갱신 관련 함수 정의 (컨트롤 생성보다 먼저 정의해야 함)
        def render_card_content():
            """현재 인덱스와 상태에 맞는 카드 내부 UI를 생성하여 반환"""
            w = words[st.idx]
            if st.is_front:
                # 카드 앞면
                return ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text("◀", color=COLOR_PRIMARY),
                            on_click=lambda _: go_to("/student_home"),
                            padding=5, border_radius=5, bgcolor="#f0f4f8"
                        ),
                        ft.Text(f"{session.get('level')} ({st.idx+1}/{total})", size=12, color="grey")
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
                            ft.Text(w["mean"], size=16, weight="bold", color=COLOR_TEXT_MAIN, text_align="center"),
                            ft.Text(w["desc"], size=12, color="#8a7e6a", italic=True, text_align="center")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton("🔊 발음 듣기", on_click=lambda e: play_tts(w["word"]), width=280, bgcolor=COLOR_PRIMARY, color="white")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            else:
                # 카드 뒷면 (예문)
                return ft.Column([
                    ft.Text(w["word"], size=28, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(
                        bgcolor="#eef5ff", padding=15, border_radius=15, margin=ft.margin.symmetric(vertical=20),
                        border=ft.border.only(left=ft.BorderSide(5, COLOR_PRIMARY)),
                        content=ft.Column([
                            ft.Text("[Example]", size=12, color=COLOR_PRIMARY, weight="bold"),
                            ft.Text(w["ex"], size=16, color=COLOR_TEXT_MAIN)
                        ])
                    ),
                    ft.Row([
                        ft.ElevatedButton("▶ 문장 듣기", on_click=lambda e: play_tts(w["ex"]), expand=True, bgcolor=COLOR_PRIMARY, color="white"),
                        ft.ElevatedButton("🎙 문장 녹음", on_click=lambda e: open_overlay(), expand=True, bgcolor=COLOR_ACCENT, color="white")
                    ], spacing=10),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.OutlinedButton("이전", on_click=lambda e: change_card(-1), expand=True),
                        ft.OutlinedButton("다음", on_click=lambda e: change_card(1), expand=True)
                    ], spacing=10)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        def update_view():
            """카드의 내용만 교체하고 화면 업데이트"""
            if card_container.page: # 페이지에 로드된 상태인지 확인
                card_container.content = render_card_content()
                card_container.update()

        def flip_card(e):
            st.is_front = not st.is_front
            update_view()

        def change_card(delta):
            new_idx = st.idx + delta
            if 0 <= new_idx < total:
                st.idx = new_idx
                session["idx"] = new_idx
                st.is_front = True
                update_view()
            elif new_idx >= total:
                show_snack("학습이 완료되었습니다! 🎉", COLOR_EVAL)
                go_to("/student_home")

        def open_overlay():
            w = words[st.idx]
            overlay_content.controls = [
                ft.Container(
                    bgcolor="#f8f9fa", padding=10, border_radius=10, margin=ft.margin.only(bottom=5),
                    content=ft.Row([
                        ft.Text(w["ex"], size=14, weight="bold"),
                        ft.Text("92점", color=COLOR_EVAL, weight="bold")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            ]
            for char in w["word"]:
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
            overlay_container.visible = True
            page.update()

        def close_overlay():
            overlay_container.visible = False
            page.update()

        # 3. UI 컨트롤 생성 (함수들이 정의된 후 생성)
        overlay_content = ft.Column(scroll="auto", expand=True)
        overlay_container = ft.Container(
            visible=False,
            bgcolor="#4D000000",
            alignment=ft.Alignment(0, 0),
            expand=True,
            content=ft.Container(
                width=330, height=550,
                bgcolor="white",
                border_radius=25,
                padding=20,
                shadow=ft.BoxShadow(blur_radius=20, color="black"),
                content=ft.Column([
                    ft.Text("상세 발음 평가", size=18, weight="bold"),
                    ft.Divider(),
                    ft.Container(
                        width=80, height=80, border_radius=40,
                        border=ft.border.all(4, COLOR_EVAL),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column([
                            ft.Text("92", size=24, weight="bold", color=COLOR_EVAL),
                            ft.Text("정확도", size=10, color="grey")
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=0)
                    ),
                    ft.Container(content=overlay_content, expand=True),
                    ft.ElevatedButton("학습 계속하기", on_click=lambda e: close_overlay(), width=300, bgcolor=COLOR_TEXT_MAIN, color="white")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )

        card_container = ft.Container(
            content=render_card_content(), # 초기 내용을 함수 호출로 미리 설정
            width=340, height=520,
            bgcolor=COLOR_CARD_BG,
            border_radius=25,
            padding=25,
            shadow=STYLE_CARD_SHADOW,
            alignment=ft.Alignment(0, 0),
            animate=ft.Animation(400, "easeOut"),
            on_click=lambda e: flip_card(e) if st.is_front else None
        )

        # 4. View 객체 반환 (마지막에 update_view() 호출 금지)
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
                             ft.Text("카드를 터치하여 뒤집으세요", color="#bdc3c7", size=12, visible=True)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    overlay_container
                ], expand=True)
            ],
            bgcolor=COLOR_BG
        )

    # --- View 5: 선생님 대시보드 ---
    def view_teacher_dash():
        students = [
            {"name": "김철수", "prog": 80, "score": 90, "issue": False},
            {"name": "이영희", "prog": 45, "score": 70, "issue": True},
            {"name": "박민수", "prog": 95, "score": 100, "issue": False},
        ]

        def make_student_card(s):
            return ft.Container(
                bgcolor="white", padding=15, border_radius=15, margin=ft.margin.only(bottom=10),
                border=ft.border.all(1, "#eee"),
                content=ft.Row([
                    ft.Column([
                        ft.Text(s["name"], weight="bold", size=16),
                        ft.Text(f"진도율: {s['prog']}%", size=12, color="grey")
                    ]),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(f"{s['score']}점", color=COLOR_EVAL if s['score']>=80 else COLOR_ACCENT, weight="bold"),
                            bgcolor="#f0fdf4" if s['score']>=80 else "#fff5f5",
                            padding=8, border_radius=8
                        ),
                        ft.IconButton(ft.icons.CHEVRON_RIGHT, icon_color="grey")
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

        return ft.View(
            route="/teacher_dash",
            controls=[
                ft.AppBar(
                    title=ft.Text("선생님 대시보드"), bgcolor="white", color="black",
                    actions=[ft.IconButton(icon="logout", on_click=lambda _: go_to("/login"))]
                ),
                ft.Container(
                    padding=20, scroll="auto", expand=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                expand=True, bgcolor=COLOR_PRIMARY, padding=20, border_radius=20,
                                content=ft.Column([
                                    ft.Text("총 학생 수", color="white"),
                                    ft.Text(str(len(students)), size=24, weight="bold", color="white")
                                ])
                            ),
                            ft.Container(
                                expand=True, bgcolor="#fff", padding=20, border_radius=20,
                                content=ft.Column([
                                    ft.Text("관리 필요", color=COLOR_ACCENT),
                                    ft.Text("1명", size=24, weight="bold", color=COLOR_ACCENT)
                                ])
                            )
                        ], spacing=10),
                        ft.Container(height=20),
                        ft.Text("학생 목록", size=18, weight="bold"),
                        ft.Container(height=10),
                        ft.Column([make_student_card(s) for s in students])
                    ])
                )
            ],
            bgcolor=COLOR_BG
        )
    
    # --- View 6: 회원가입 ---
    def view_signup():
        new_id = ft.TextField(label="아이디", width=280)
        new_pw = ft.TextField(label="비밀번호", password=True, width=280)
        new_name = ft.TextField(label="이름", width=280)
        
        def on_regist(e):
            if not (new_id.value and new_pw.value and new_name.value): return
            ok, msg = register_user(new_id.value, new_pw.value, new_name.value, "student")
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)
            if ok: go_to("/login")

        return ft.View(
            route="/signup",
            controls=[
                ft.AppBar(title=ft.Text("회원가입"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: go_to("/login"))),
                ft.Container(
                    alignment=ft.Alignment(0, 0), padding=20,
                    content=ft.Column([
                        new_id, new_pw, new_name,
                        ft.ElevatedButton("가입하기", on_click=on_regist, width=280, bgcolor=COLOR_PRIMARY, color="white")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ], bgcolor="white"
        )

    # --- 라우팅 관리 ---
    def route_change(e: ft.RouteChangeEvent):
        print(f"🔄 이동 중: {page.route}") # 로그 확인용
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
        elif page.route == "/teacher_dash":
            page.views.append(view_teacher_dash())
        
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
    
    # [수정됨] 버전 호환성을 위해 ft.WEB_BROWSER 대신 ft.AppView.WEB_BROWSER 사용
    # 최신 버전에서는 Enum을 사용하는 것이 원칙입니다.
    try:
        # 최신 버전 (권장)
        view_mode = ft.AppView.WEB_BROWSER
    except AttributeError:
        # 혹시 모를 구버전 호환 (문자열 fallback)
        view_mode = "web_browser"

    ft.app(target=main, port=8099, view=view_mode)