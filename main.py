import flet as ft
import flet_audio as fta
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
    """엑셀 파일 로드"""
    global VOCAB_DB
    vocab_db = {}
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(current_dir, "data", "vocabulary.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"⚠️ 데이터 파일을 찾을 수 없습니다: {excel_path}")
        return {}

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
    """사용자 목록 로드"""
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
    """사용자 목록 저장"""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=4)
    except: pass

def register_user(uid, pw, name, role):
    """회원가입 처리"""
    users = load_users()
    if uid in users: return False, "이미 존재하는 아이디입니다."
    users[uid] = {"pw": pw, "name": name, "role": role}
    save_users(users)
    return True, "회원가입 완료! 로그인해주세요."

def authenticate_user(uid, pw):
    """로그인 인증"""
    users = load_users()
    if uid in users and users[uid]["pw"] == pw:
        u = users[uid]
        u["id"] = uid
        return True, u
    return False, None

# --- 학습 기록 관리 ---
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

# 초기 데이터 로드
VOCAB_DB = load_vocab_data()

# =============================================================================
# 2. 메인 앱 로직
# =============================================================================

def main(page: ft.Page):
    # 앱 설정
    page.title = "JustVoca"
    page.window_width = 390
    page.window_height = 844
    page.bgcolor = "#f4f7f6"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # 세션 (로그인 정보 및 학습 상태)
    session = {"user": None, "level": "", "study_words": [], "quiz_score": 0, "wrong_list": []}
    
    # 오디오 (에러 방지 처리)
    try:
        audio = fta.Audio(autoplay=True)
        page.overlay.append(audio)
    except: pass

    def play_tts(text):
        """TTS 재생"""
        try:
            audio.src = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q={text}&tl=ko"
            audio.update()
        except: pass

    def show_snack(msg):
        """하단 메시지 표시"""
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def go_to(route):
        """페이지 이동 헬퍼"""
        print(f"👉 이동 요청: {page.route} -> {route}") 
        page.go(route)

    # -------------------------------------------------------------------------
    # [View] 로그인 화면
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
                go_to("/student_home" if user["role"]=="student" else "/teacher_dash")
            else: show_snack("로그인 실패")

        def on_signup_click(e):
            print("👇 회원가입 버튼 클릭됨!")
            go_to("/signup")

        return ft.View("/login", [
            ft.Container(
                content=ft.Column([
                    ft.Text("JustVoca", size=32, weight="bold", color="#2c3e50"),
                    ft.Container(height=30),
                    id_f, pw_f,
                    ft.Container(height=20),
                    ft.ElevatedButton("로그인", on_click=on_login, width=280, height=50, 
                                      style=ft.ButtonStyle(bgcolor="#4a90e2", color="white")),
                    ft.Container(height=10),
                    ft.OutlinedButton("회원가입 하기", 
                                      on_click=on_signup_click, 
                                      width=280, height=50,
                                      style=ft.ButtonStyle(bgcolor="white", color="black"))
                ], alignment="center", horizontal_alignment="center"),
                padding=20, expand=True, bgcolor="white", alignment=ft.alignment.center
            )
        ])

    # -------------------------------------------------------------------------
    # [View] 회원가입 화면
    # -------------------------------------------------------------------------
    def view_signup():
        new_id = ft.TextField(label="아이디", width=280, bgcolor="white")
        new_pw = ft.TextField(label="비밀번호", password=True, width=280, bgcolor="white")
        new_name = ft.TextField(label="이름", width=280, bgcolor="white")
        role_grp = ft.RadioGroup(content=ft.Row([
            ft.Radio(value="student", label="학생"),
            ft.Radio(value="teacher", label="선생님")
        ]), value="student")

        def on_regist(e):
            if not (new_id.value and new_pw.value and new_name.value): return show_snack("모두 입력해주세요.")
            ok, msg = register_user(new_id.value, new_pw.value, new_name.value, role_grp.value)
            show_snack(msg)
            if ok: go_to("/login")

        return ft.View("/signup", [
            ft.AppBar(title=ft.Text("회원가입"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: go_to("/login"))),
            ft.Container(
                content=ft.Column([
                    ft.Text("계정 생성", size=24, weight="bold"),
                    ft.Container(height=20),
                    role_grp, new_id, new_pw, new_name,
                    ft.Container(height=20),
                    ft.ElevatedButton("가입 완료", on_click=on_regist, width=280, height=50, 
                                      style=ft.ButtonStyle(bgcolor="#2ecc71", color="white"))
                ], horizontal_alignment="center"),
                padding=20, expand=True, bgcolor="white", alignment=ft.alignment.center
            )
        ])

    # -------------------------------------------------------------------------
    # [View] 학생 홈
    # -------------------------------------------------------------------------
    def view_student_home():
        grid = ft.GridView(expand=True, max_extent=160, child_aspect_ratio=1.2, spacing=10)
        for lv in VOCAB_DB:
            grid.controls.append(ft.Container(
                content=ft.Column([
                    ft.Text(lv, size=18, weight="bold", color="#4a90e2"), 
                    ft.Text(f"{len(VOCAB_DB[lv])} 단어", size=12, color="grey")
                ], alignment="center"),
                bgcolor="white", border_radius=15, border=ft.border.all(1, "#eee"),
                on_click=lambda e, l=lv: [session.update({"level":l, "study_words":VOCAB_DB[l]}), go_to("/study")]
            ))
            
        return ft.View("/student_home", [
            ft.AppBar(title=ft.Text("학습 선택"), bgcolor="white", color="black", 
                      automatically_imply_leading=False,
                      actions=[ft.IconButton(ft.icons.LOGOUT, on_click=lambda _: go_to("/login"))]),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"반가워요, {session['user']['name']}님!", size=20, weight="bold"),
                    ft.Container(height=20),
                    grid
                ], horizontal_alignment="center"),
                padding=20, expand=True, bgcolor="#f4f7f6"
            )
        ])

    # -------------------------------------------------------------------------
    # [View] 학습 (Flashcard)
    # -------------------------------------------------------------------------
    def view_study():
        words = session["study_words"]
        total = min(10, len(words))
        idx = 0
        is_front = True
        
        card = ft.Container(
            width=320, height=450, bgcolor="white", border_radius=25, padding=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.with_opacity(0.1, "black")),
            alignment=ft.alignment.center, on_click=lambda e: flip()
        )
        prog = ft.ProgressBar(width=300, value=0, color="#4a90e2")
        
        def flip(): nonlocal is_front; is_front = not is_front; update()
        def next_w(e): nonlocal idx, is_front; idx += 1; is_front=True; update()
        
        def update():
            if idx >= total: return go_to("/quiz")
            prog.value = (idx + 1) / total
            w = words[idx]
            
            if is_front:
                card.content = ft.Column([
                    ft.Text(w["word"], size=48, weight="bold"),
                    ft.IconButton(ft.icons.VOLUME_UP, icon_size=40, on_click=lambda e: play_tts(w["word"])),
                    ft.Text("터치하여 뜻 확인", color="grey")
                ], alignment="center")
                card.bgcolor = "white"
            else:
                card.content = ft.Column([
                    ft.Row([ft.Text(w["word"], size=32), ft.IconButton(ft.icons.VOLUME_UP, on_click=lambda e: play_tts(w["word"]))], alignment="center"),
                    ft.Divider(),
                    ft.Text(w["mean"], size=20, color="#4a90e2"),
                    ft.Text(f"\"{w['ex']}\"", italic=True)
                ], alignment="center")
                card.bgcolor = "#fdfdfd"
            card.update()
            prog.update()
            
        update()
        return ft.View("/study", [
            ft.AppBar(title=ft.Text("학습"), bgcolor="white", color="black", leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: go_to("/student_home"))),
            ft.Column([
                ft.Container(height=10), prog, 
                ft.Container(height=20), card, 
                ft.Container(height=30), ft.ElevatedButton("다음 ▶", on_click=next_w, width=300, height=50)
            ], horizontal_alignment="center", expand=True)
        ])

    # -------------------------------------------------------------------------
    # [View] 퀴즈
    # -------------------------------------------------------------------------
    def view_quiz():
        study_list = session["study_words"][:10]
        quiz_list = random.sample(study_list, min(3, len(study_list)))
        q_idx, score = 0, 0
        wrong_words = []
        
        q_text = ft.Text(size=22, weight="bold", text_align="center")
        opts = ft.Column(spacing=15)

        def next_q():
            nonlocal q_idx
            if q_idx >= len(quiz_list):
                session.update({"quiz_score": score, "wrong_list": wrong_words})
                save_history(session["user"]["id"], session["user"]["name"], session["level"], score, len(quiz_list), wrong_words)
                return go_to("/result")
            
            tgt = quiz_list[q_idx]
            q_text.value = f"다음 설명에 맞는 단어는?\n\n\"{tgt['desc'] or tgt['mean']}\""
            
            others = [w for w in study_list if w!=tgt]
            choices = [tgt] + random.sample(others, min(3, len(others)))
            random.shuffle(choices)
            
            opts.controls.clear()
            for c in choices:
                opts.controls.append(ft.ElevatedButton(
                    c["word"], width=300, height=55,
                    on_click=lambda e, ans=(c==tgt), w=tgt['word']: check(ans, w)
                ))
            page.update()

        def check(ok, w):
            nonlocal score, q_idx
            if ok: score += 1; play_tts("정답"); show_snack("정답! ⭕")
            else: wrong_words.append(w); play_tts("오답"); show_snack("오답! ❌")
            q_idx += 1
            next_q()

        next_q()
        return ft.View("/quiz", [
            ft.AppBar(title=ft.Text("퀴즈"), bgcolor="white", color="black", automatically_imply_leading=False),
            ft.Container(content=ft.Column([q_text, ft.Container(height=30), opts], horizontal_alignment="center"), padding=20, expand=True)
        ])

    # -------------------------------------------------------------------------
    # [View] 결과 & 선생님 대시보드
    # -------------------------------------------------------------------------
    def view_result():
        wrongs = session["wrong_list"]
        return ft.View("/result", [
            ft.Container(content=ft.Column([
                ft.Text("🎉", size=80), ft.Text("학습 완료!", size=30, weight="bold"),
                ft.Text(f"점수: {session['quiz_score']}점", size=24, color="blue"),
                ft.Text(f"오답: {', '.join(wrongs)}" if wrongs else "완벽해요!", color="red" if wrongs else "green"),
                ft.Container(height=50),
                ft.ElevatedButton("홈으로", on_click=lambda _: go_to("/student_home"), width=280)
            ], alignment="center", horizontal_alignment="center"), expand=True, bgcolor="white", alignment=ft.alignment.center)
        ])
    
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
        
        return ft.View("/teacher_dash", [
            ft.AppBar(title=ft.Text("선생님 대시보드"), bgcolor="#34495e", color="white", actions=[ft.IconButton(ft.icons.LOGOUT, on_click=lambda _: go_to("/login"))]),
            ft.Container(content=ft.Column([
                ft.Text("학생 현황", size=20, weight="bold"),
                ft.DataTable(columns=[ft.DataColumn(ft.Text("이름")), ft.DataColumn(ft.Text("레벨")), ft.DataColumn(ft.Text("점수")), ft.DataColumn(ft.Text("오답"))], rows=rows)
            ], scroll="always"), padding=20, expand=True)
        ])

    # -------------------------------------------------------------------------
    # 라우팅 핸들러
    # -------------------------------------------------------------------------
    def route_change(route):
        print(f"🔄 URL 변경됨: {page.route}")
        page.views.clear()
        
        if page.route == "/login" or page.route == "/": page.views.append(view_login())
        elif page.route == "/signup": page.views.append(view_signup())
        elif page.route == "/student_home": page.views.append(view_student_home())
        elif page.route == "/study": page.views.append(view_study())
        elif page.route == "/quiz": page.views.append(view_quiz())
        elif page.route == "/result": page.views.append(view_result())
        elif page.route == "/teacher_dash": page.views.append(view_teacher_dash())
        
        page.update()

    page.on_route_change = route_change
    page.go("/login")

# =============================================================================
# [중요] WSL 환경 설정: 외부 접속 허용 (host='0.0.0.0')
# =============================================================================
if __name__ == "__main__":
    # IP 주소 자동 확인
    hostname = socket.gethostname()
    try:
        ip_addr = socket.gethostbyname(hostname)
    except:
        ip_addr = "127.0.0.1"
        
    print("\n" + "="*60)
    print("🚀 앱 서버가 실행되었습니다!")
    print(f"👉 윈도우에서 접속이 안되면 아래 주소들을 차례로 시도해보세요:")
    print(f"1. http://localhost:8080")
    print(f"2. http://{ip_addr}:8080")
    print("="*60 + "\n")
    
    # host='0.0.0.0'을 추가하여 모든 네트워크 인터페이스에서 접속 허용
    ft.app(target=main, port=8080, view=ft.AppView.WEB_BROWSER, host="0.0.0.0")