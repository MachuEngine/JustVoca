import flet as ft
import pandas as pd
import random
import os
import json
import traceback
import warnings
import socket
from datetime import datetime

# 불필요한 경고 숨기기
warnings.filterwarnings("ignore")

# =============================================================================
# 1. 파일 경로 및 데이터 관리
# =============================================================================

VOCAB_DB = {}
HISTORY_FILE = "history.json"
USERS_FILE = "users.json"

def load_vocab_data():
    """엑셀 파일 로드 (실패 시 빈 딕셔너리 반환하여 멈춤 방지)"""
    global VOCAB_DB
    vocab_db = {}
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(current_dir, "data", "vocabulary.xlsx")
    
    # 폴더가 없으면 생성
    os.makedirs(os.path.join(current_dir, "data"), exist_ok=True)
    
    if not os.path.exists(excel_path):
        print(f"⚠️ [주의] 데이터 파일을 찾을 수 없습니다: {excel_path}")
        return {"기초단어": [{"word": "apple", "mean": "사과", "ex": "I eat apple", "desc": "과일"}]}

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
                    "mean": f"{row.get('분류', '')} · {row.get('주제', '')}", 
                    "ex": str(row.get("예문1", "")).strip(),
                    "desc": str(row.get("주제", "")).strip() 
                }
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
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(users_data):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=4)
        print("💾 사용자 데이터 저장 성공")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")

def register_user(uid, pw, name, role):
    users = load_users()
    if uid in users: return False, "이미 존재하는 아이디입니다."
    users[uid] = {"pw": pw, "name": name, "role": role}
    save_users(users)
    return True, "회원가입 완료! 로그인해주세요."

def authenticate_user(uid, pw):
    users = load_users()
    if uid in users and users[uid]["pw"] == pw:
        u = users[uid]
        u["id"] = uid
        return True, u
    return False, None

def save_history(user_id, name, level, score, total, wrongs):
    try:
        data = {}
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        if user_id not in data: data[user_id] = []
        data[user_id].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "name": name, "level": level, "score": score,
            "total": total, "wrong_words": wrongs
        })
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}

VOCAB_DB = load_vocab_data()

# =============================================================================
# 2. 메인 앱 로직
# =============================================================================

def main(page: ft.Page):
    page.title = "JustVoca"
    page.bgcolor = "#f4f7f6"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = "adaptive"

    session = {"user": None, "level": "", "study_words": [], "quiz_score": 0, "wrong_list": []}
    
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

    def show_snack(msg):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def go_to(route):
        page.go(route)

    # -------------------------------------------------------------------------
    # [View 1] 로그인
    # -------------------------------------------------------------------------
    def view_login():
        id_f = ft.TextField(label="아이디", width=280, bgcolor="white")
        pw_f = ft.TextField(label="비밀번호", password=True, width=280, bgcolor="white", can_reveal_password=True)
        
        def on_login(e):
            if not id_f.value or not pw_f.value: return show_snack("정보를 입력하세요.")
            ok, user = authenticate_user(id_f.value, pw_f.value)
            if ok:
                session["user"] = user
                show_snack(f"환영합니다 {user['name']}님!")
                if user["role"] == "student":
                    go_to("/student_home")
                else:
                    go_to("/teacher_dash")
            else: show_snack("로그인 실패")

        return ft.View(
            route="/login",
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("JustVoca", size=32, weight="bold", color="#2c3e50"),
                            ft.Container(height=30),
                            id_f, pw_f,
                            ft.Container(height=20),
                            ft.ElevatedButton("로그인", on_click=on_login, width=280, height=50, 
                                            style=ft.ButtonStyle(bgcolor="#4a90e2", color="white")),
                            ft.Container(height=10),
                            ft.OutlinedButton("회원가입 하기", on_click=lambda _: go_to("/signup"), 
                                            width=280, height=50)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.Alignment(0, 0),
                    expand=True
                )
            ],
            bgcolor="white",
            padding=20
        )

    # -------------------------------------------------------------------------
    # [View 2] 회원가입 (아이콘 수정됨)
    # -------------------------------------------------------------------------
    def view_signup():
        print("📌 회원가입 화면 진입")
        role_grp = ft.RadioGroup(content=ft.Row([
            ft.Radio(value="student", label="학생"),
            ft.Radio(value="teacher", label="선생님")
        ]), value="student")

        new_id = ft.TextField(label="아이디", width=280, bgcolor="white")
        new_pw = ft.TextField(label="비밀번호", password=True, width=280, bgcolor="white")
        new_name = ft.TextField(label="이름", width=280, bgcolor="white")

        async def on_regist(e):
            try:
                if not (new_id.value and new_pw.value and new_name.value): 
                    return show_snack("모두 입력해주세요.")
                
                print(f"📝 가입 시도: {new_id.value}")
                ok, msg = register_user(new_id.value, new_pw.value, new_name.value, role_grp.value)
                show_snack(msg)
                if ok: 
                    print("🚀 가입 성공! 이동")
                    go_to("/login")
            except Exception as err:
                print(f"❌ 가입 에러: {err}")
                traceback.print_exc()

        return ft.View(
            route="/signup",
            controls=[
                # [수정] ft.icons.ARROW_BACK 대신 "arrow_back" 문자열 사용
                ft.AppBar(title=ft.Text("회원가입"), leading=ft.IconButton(icon="arrow_back", on_click=lambda _: go_to("/login"))),
                ft.Container(
                    content=ft.Column([
                        ft.Text("계정 생성", size=24, weight="bold"),
                        ft.Container(height=20),
                        role_grp, new_id, new_pw, new_name,
                        ft.Container(height=20),
                        ft.ElevatedButton("가입 완료", on_click=on_regist, width=280, height=50, style=ft.ButtonStyle(bgcolor="#2ecc71", color="white"))
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20, expand=True, bgcolor="white", alignment=ft.Alignment(0, 0)
                )
            ],
            bgcolor="white"
        )

    # -------------------------------------------------------------------------
    # [View 3] 학생 홈 (아이콘 수정됨)
    # -------------------------------------------------------------------------
    def view_student_home():
        print("📌 학생 홈 진입")
        
        grid_items = []
        for lv in VOCAB_DB:
            def make_click_handler(level_name):
                return lambda e: [session.update({"level": level_name, "study_words": VOCAB_DB[level_name]}), go_to("/study")]

            grid_items.append(ft.Container(
                content=ft.Column([
                    ft.Text(lv, size=18, weight="bold", color="#4a90e2"), 
                    ft.Text(f"{len(VOCAB_DB[lv])} 단어", size=12, color="grey")
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="white", 
                border_radius=15, 
                border=ft.border.all(1, "#eee"),
                alignment=ft.Alignment(0, 0),
                on_click=make_click_handler(lv)
            ))

        grid = ft.GridView(
            runs_count=2,
            max_extent=160,
            child_aspect_ratio=1.2,
            spacing=10,
            run_spacing=10,
            controls=grid_items
        )

        return ft.View(
            route="/student_home",
            controls=[
                ft.AppBar(
                    title=ft.Text("학습 선택"), 
                    bgcolor="white", 
                    color="black", 
                    automatically_imply_leading=False,
                    # [수정] "logout" 문자열 사용
                    actions=[ft.IconButton(icon="logout", on_click=lambda _: go_to("/login"))]
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"반가워요, {session['user']['name']}님!", size=20, weight="bold"),
                        ft.Container(height=20),
                        ft.Container(content=grid, expand=True)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20, 
                    expand=True, 
                    bgcolor="#f4f7f6"
                )
            ]
        )

    # -------------------------------------------------------------------------
    # [View 4] 학습 화면 (아이콘 수정됨)
    # -------------------------------------------------------------------------
    def view_study():
        words = session.get("study_words", [])
        if not words: 
            return ft.View(route="/study", controls=[ft.Text("데이터가 없습니다.")])

        total = min(10, len(words))
        current_idx = [0] 
        is_front = [True]

        card_content = ft.Column(alignment=ft.MainAxisAlignment.CENTER)
        card = ft.Container(
            width=320, height=450, bgcolor="white", border_radius=25, padding=20,
            shadow=ft.BoxShadow(blur_radius=10, color="#1A000000"),
            alignment=ft.Alignment(0, 0),
            content=card_content
        )
        prog = ft.ProgressBar(width=300, value=0, color="#4a90e2")

        def render_card():
            idx = current_idx[0]
            if idx >= total: 
                go_to("/quiz")
                return

            w = words[idx]
            prog.value = (idx + 1) / total
            
            card_content.controls.clear()
            if is_front[0]:
                card.bgcolor = "white"
                card_content.controls = [
                    ft.Text(w["word"], size=48, weight="bold"),
                    # [수정] "volume_up" 문자열 사용
                    ft.IconButton(icon="volume_up", icon_size=40, on_click=lambda e: play_tts(w["word"])),
                    ft.Text("터치하여 뜻 확인", color="grey")
                ]
            else:
                card.bgcolor = "#fdfdfd"
                card_content.controls = [
                    # [수정] "volume_up" 문자열 사용
                    ft.Row([ft.Text(w["word"], size=32), ft.IconButton(icon="volume_up", on_click=lambda e: play_tts(w["word"]))], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(),
                    ft.Text(w["mean"], size=20, color="#4a90e2"),
                    ft.Text(f"\"{w['ex']}\"", italic=True)
                ]
            card.update()
            prog.update()

        def flip_card(e):
            is_front[0] = not is_front[0]
            render_card()

        def next_word(e):
            current_idx[0] += 1
            is_front[0] = True
            render_card()

        card.on_click = flip_card
        
        w_init = words[0]
        card_content.controls = [
             ft.Text(w_init["word"], size=48, weight="bold"),
             # [수정] "volume_up" 문자열 사용
             ft.IconButton(icon="volume_up", icon_size=40, on_click=lambda e: play_tts(w_init["word"])),
             ft.Text("터치하여 뜻 확인", color="grey")
        ]
        prog.value = 1/total

        return ft.View(
            route="/study", 
            controls=[
                # [수정] "arrow_back" 문자열 사용
                ft.AppBar(title=ft.Text("학습"), bgcolor="white", color="black", 
                          leading=ft.IconButton(icon="arrow_back", on_click=lambda _: go_to("/student_home"))),
                ft.Column([
                    ft.Container(height=10), prog, 
                    ft.Container(height=20), card, 
                    ft.Container(height=30), ft.ElevatedButton("다음 ▶", on_click=next_word, width=300, height=50)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            ]
        )

    # -------------------------------------------------------------------------
    # [View 5] 퀴즈
    # -------------------------------------------------------------------------
    def view_quiz():
        study_list = session["study_words"][:10]
        if len(study_list) < 4:
            quiz_list = study_list
        else:
            quiz_list = random.sample(study_list, min(3, len(study_list)))
            
        q_state = {"idx": 0, "score": 0, "wrong": []}
        
        q_text = ft.Text(size=22, weight="bold", text_align="center")
        opts = ft.Column(spacing=15)

        def load_question():
            if q_state["idx"] >= len(quiz_list):
                session.update({"quiz_score": q_state["score"], "wrong_list": q_state["wrong"]})
                save_history(session["user"]["id"], session["user"]["name"], session["level"], q_state["score"], len(quiz_list), q_state["wrong"])
                go_to("/result")
                return

            tgt = quiz_list[q_state["idx"]]
            q_text.value = f"다음 설명에 맞는 단어는?\n\n\"{tgt['desc'] or tgt['mean']}\""
            
            others = [w for w in study_list if w != tgt]
            choices = [tgt] + random.sample(others, min(3, len(others)))
            random.shuffle(choices)
            
            opts.controls.clear()
            for c in choices:
                def make_ans_handler(is_correct, word_obj):
                    return lambda e: check_answer(is_correct, word_obj)
                
                opts.controls.append(ft.ElevatedButton(
                    c["word"], width=300, height=55,
                    on_click=make_ans_handler(c == tgt, tgt['word'])
                ))
            page.update()

        def check_answer(is_correct, w_word):
            if is_correct:
                q_state["score"] += 1
                play_tts("정답")
                show_snack("정답! ⭕")
            else:
                q_state["wrong"].append(w_word)
                play_tts("오답")
                show_snack("오답! ❌")
            
            q_state["idx"] += 1
            load_question()

        load_question()

        return ft.View(
            route="/quiz", 
            controls=[
                ft.AppBar(title=ft.Text("퀴즈"), bgcolor="white", color="black", automatically_imply_leading=False),
                ft.Container(
                    content=ft.Column([q_text, ft.Container(height=30), opts], horizontal_alignment=ft.CrossAxisAlignment.CENTER), 
                    padding=20, expand=True
                )
            ]
        )

    # -------------------------------------------------------------------------
    # [View 6] 결과 & 선생님
    # -------------------------------------------------------------------------
    def view_result():
        wrongs = session.get("wrong_list", [])
        return ft.View(
            route="/result",
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("🎉", size=80), ft.Text("학습 완료!", size=30, weight="bold"),
                        ft.Text(f"점수: {session['quiz_score']}점", size=24, color="blue"),
                        ft.Text(f"오답: {', '.join(wrongs)}" if wrongs else "완벽해요!", color="red" if wrongs else "green"),
                        ft.Container(height=50),
                        ft.ElevatedButton("홈으로", on_click=lambda _: go_to("/student_home"), width=280)
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True, bgcolor="white", alignment=ft.Alignment(0, 0)
                )
            ]
        )

    def view_teacher_dash():
        hist = load_history()
        rows = []
        for uid, recs in hist.items():
            for r in recs:
                w_str = ", ".join(r['wrong_words']) if r['wrong_words'] else "-"
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(r['name'])), ft.DataCell(ft.Text(r['level'])),
                    ft.DataCell(ft.Text(f"{r['score']}")), ft.DataCell(ft.Text(w_str, color="red"))
                ]))
        
        return ft.View(
            route="/teacher_dash",
            controls=[
                # [수정] "logout" 문자열 사용
                ft.AppBar(title=ft.Text("선생님 대시보드"), bgcolor="#34495e", color="white", 
                          actions=[ft.IconButton(icon="logout", on_click=lambda _: go_to("/login"))]),
                ft.Container(
                    content=ft.Column([
                        ft.Text("학생 현황", size=20, weight="bold"),
                        ft.DataTable(columns=[ft.DataColumn(ft.Text("이름")), ft.DataColumn(ft.Text("레벨")), ft.DataColumn(ft.Text("점수")), ft.DataColumn(ft.Text("오답"))], rows=rows)
                    ], scroll="always"), 
                    padding=20, expand=True
                )
            ]
        )

    # -------------------------------------------------------------------------
    # 라우팅
    # -------------------------------------------------------------------------
    def route_change(e: ft.RouteChangeEvent):
        r = e.route
        print(f"🔄 URL 이동: {r}")
        
        if page.views and page.views[-1].route == r: return

        if r == "/login":
            page.views.clear()
        
        if r == "/login": page.views.append(view_login())
        elif r == "/signup": page.views.append(view_signup())
        elif r == "/student_home": page.views.append(view_student_home())
        elif r == "/study": page.views.append(view_study())
        elif r == "/quiz": page.views.append(view_quiz())
        elif r == "/result": page.views.append(view_result())
        elif r == "/teacher_dash": page.views.append(view_teacher_dash())
        
        page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.go("/login")

# =============================================================================
# 실행 (GPU 에러 방지 포함)
# =============================================================================
if __name__ == "__main__":
    import os
    
    # [중요] WSL 환경 GPU 충돌 방지
    os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1" 
    
    hostname = socket.gethostname()
    try: ip_addr = socket.gethostbyname(hostname)
    except: ip_addr = "127.0.0.1"
    
    print("\n" + "="*60)
    print("🚀 앱 서버 재가동 (아이콘 에러 완벽 수정됨)")
    print(f"👉 접속: http://localhost:8099")
    print("="*60 + "\n")
    
    ft.app(target=main, port=8099, host="0.0.0.0", view=ft.AppView.WEB_BROWSER)