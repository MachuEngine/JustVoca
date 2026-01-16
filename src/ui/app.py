# src/ui/app.py
import os
import json
import random
import asyncio
import math
import flet as ft
from datetime import datetime

# =============================================================================
# Flet 0.80+ 호환
# =============================================================================
try:
    _ = ft.icons.ABC
except Exception:
    try:
        ft.icons = ft.Icons
    except Exception:
        pass

# ------------------------------
# Local modules
# ------------------------------
from src.constants import *
from src.utils import log_write, hash_password
from src.vocab import load_vocab_data
from src.ui.components import build_ad_zone
from src.storage import (
    load_system,
    save_system,
    load_users,
    save_users,
    authenticate_user,
    update_user,
    get_user,
    register_user,
    update_user_approval,
    load_notices,
    add_notice,
    get_active_notices,
    mark_notice_read
)
from src.progress import (
    ensure_progress,
    ensure_topic_progress,
    update_learned_word,
    update_last_seen_only,
    add_wrong_note,
    country_label,
)

VOCAB_DB = load_vocab_data()

def main(page: ft.Page):
    page.title = "한국어 학습 앱"
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

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
        "is_review": False,
        "selected_student_id": None,
        "motivate_shown": False,
        "motivate_msg": "",
        "motivate_emoji": "",
        "pron_state": {
            "recording": False,
            "recorded": False,
            "target_word": "",
            "target_example": "",
            "result_score": None,
            "result_comment": "",
            "detail": [],
        },
        "today_words": [],
        "nav_token": 0,
    }

    MOTIVATE_MESSAGES = [
        "지금처럼만 하면 충분해요 ☺️",
        "충분히 잘하고 있어요! 지금처럼만 해요.",
        "여기까지 잘 왔어요! 계속 가볼까요?",
        "지금 흐름 좋아요. 이대로 이어가요.",
        "오늘도 잘하고 있어요.",
        "아주 안정적인 속도예요. 차근차근 가요.",
        "좋아요! 조금만 더 힘내면 목표 달성이에요!",
    ]
    MOTIVATE_EMOJIS = ["🙂", "🙌", "💪", "🌟", "✨", "👍", "💯"]

    I18N = {
        "ko": {"app_title": "한국어 학습", "login": "로그인", "signup": "회원가입", "home": "홈", "settings": "설정"},
        "en": {"app_title": "Korean Study", "login": "Login", "signup": "Sign up", "home": "Home", "settings": "Settings"},
    }

    def t(key: str) -> str:
        u = session.get("user") or {}
        lang = (u.get("progress", {}).get("settings", {}) or {}).get("ui_lang", "ko")
        return I18N.get(lang, I18N["ko"]).get(key, key)

    def play_tts(text: str):
        try:
            tjson = json.dumps(text)
            page.run_javascript(f"""
            try {{
                if (!window.speechSynthesis) return;
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance({tjson});
                u.lang = "ko-KR"; u.rate = 1.0; u.volume = 1.0;
                window.speechSynthesis.speak(u);
            }} catch(e) {{}}
            """)
        except:
            pass

    def evaluate_pronunciation_dummy(text: str):
        score = random.randint(75, 100)
        tag = "excellent" if score >= 95 else "good" if score >= 88 else "ok" if score >= 80 else "need_practice"
        comment = "발음이 매우 정확합니다." if score >= 95 else "좋습니다." if score >= 88 else "의미 전달은 충분합니다."
        words = [w for w in (text or "").split() if w.strip()]
        detail = [{"unit": w, "score": random.randint(max(60, score - 15), min(100, score + 10))} for w in words[:12]]
        return score, comment, tag, detail

    def post_process_comment(tag: str, raw_comment: str) -> str:
        return raw_comment

    def show_snack(msg, color="black"):
        print(f"SNACK: {msg}")  # [추가] 콘솔에 로그 출력 (화면에 안 뜰 경우 확인용)
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def go_to(route):
        page.go(route)

    def reset_pron_state():
        session["pron_state"] = {"recording": False, "recorded": False, "target_word": "", "target_example": "", "result_score": None, "result_comment": "", "detail": []}

    def reset_today_session(keep_user: bool = True):
        bump_nav_token()
        if not keep_user: session["user"] = None
        session.update({"topic": "", "study_words": [], "idx": 0, "today_words": [], "mask_mode": "none", "test_queue": [], "test_idx": 0, "test_score": 0, "is_review": False, "selected_student_id": None, "motivate_shown": False})
        reset_pron_state()

    def go_home():
        u = session.get("user")
        if not u:
            go_to("/login")
            return
        role = u.get("role", "student")
        if role == "student": go_to("/student_home")
        elif role == "teacher": go_to("/teacher_dash")
        else: go_to("/system_dash")

    def do_logout():
        reset_today_session(False)
        page.go("/login")

    def bump_nav_token() -> int:
        session["nav_token"] = int(session.get("nav_token", 0) or 0) + 1
        return session["nav_token"]

    def schedule_go(delay_sec: float, route: str, *, only_if_route: str | None = None, before_go=None):
        token = bump_nav_token()
        async def _job():
            try:
                await asyncio.sleep(max(0.0, float(delay_sec)))
                if token != session.get("nav_token"): return
                if only_if_route and ((page.route or "").split("?", 1)[0] != only_if_route): return
                if before_go: before_go()
                page.go(route)
            except: pass
        try: page.run_task(_job)
        except: pass

    # --- Signup Helpers ---
    signup_state = {"id_checked": False, "id_ok": False, "sent_code": None, "phone_verified": False}

    def check_id_available(uid: str):
        uid = (uid or "").strip()
        if not uid: return False, "아이디를 입력해주세요."
        users = load_users()
        if uid in users: return False, "이미 존재하는 아이디입니다."
        return True, "사용 가능한 아이디입니다."

    def send_phone_code_dummy(phone: str):
        phone = (phone or "").strip()
        if not phone: return False, "전화번호를 입력해주세요."
        signup_state.update({"sent_code": "111111", "phone_verified": False})
        return True, "인증번호를 전송했습니다. (더미: 111111)"

    def verify_phone_code_dummy(code_in: str):
        code_in = (code_in or "").strip()
        if not code_in: return False, "인증번호를 입력해주세요."
        if signup_state.get("sent_code") == code_in:
            signup_state["phone_verified"] = True
            return True, "전화번호 인증이 완료되었습니다."
        return False, "인증번호가 올바르지 않습니다."

    # =============================================================================
    # [수정] 모바일 쉘: 클릭 차단 문제 해결 (alignment 제거 -> right/bottom 배치)
    # =============================================================================
    def mobile_shell(route: str, body: ft.Control, title: str = "", leading=None, actions=None, bottom_nav: ft.Control = None, floating_action_button: ft.Control = None):
        actions = actions or []
        topbar = None
        if title:
            left = leading if leading else ft.Container(width=40)
            right = ft.Row(actions, spacing=6) if actions else ft.Container(width=40)
            topbar = ft.Container(
                padding=ft.padding.only(left=16, right=16, top=14, bottom=10),
                content=ft.Row([
                    ft.Container(width=40, content=left),
                    ft.Text(title, size=16, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Container(width=40, content=right, alignment=ft.Alignment(1, 0)),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

        controls_list = []
        if topbar:
            controls_list.append(topbar)
        
        # 본문은 확장(expand=True) -> 남은 공간 차지
        controls_list.append(ft.Container(content=body, expand=True))
        
        # 하단 메뉴 고정
        if bottom_nav:
            controls_list.append(bottom_nav)

        # 기본 레이아웃 (Column)
        base_layout = ft.Column(expand=True, spacing=0, controls=controls_list)

        # [수정] FAB가 있을 경우 Stack 사용
        if floating_action_button:
            # 하단 탭바 높이 고려
            bottom_padding = 90 if bottom_nav else 20
            
            final_content = ft.Stack(
                expand=True,
                controls=[
                    base_layout, # 배경 (기존 화면)
                    
                    # [핵심 수정] 
                    # 이전 코드: alignment=ft.Alignment(1,1) -> 화면 전체를 덮어서 클릭 방해
                    # 수정 코드: right, bottom 속성 사용 -> 해당 위치에만 배치되고 나머지 공간은 클릭 가능
                    ft.Container(
                        content=floating_action_button,
                        right=16,              # 오른쪽에서 16px 떨어짐
                        bottom=bottom_padding, # 바닥에서 계산된 만큼 떨어짐
                    )
                ]
            )
        else:
            final_content = base_layout

        return ft.View(
            route=route,
            bgcolor=COLOR_BG,
            controls=[
                ft.Container(
                    expand=True, alignment=ft.Alignment(0, 0), padding=ft.padding.symmetric(vertical=24, horizontal=12),
                    content=ft.Container(
                        width=380, bgcolor="white", border_radius=STYLE_BORDER_RADIUS, shadow=STYLE_CARD_SHADOW,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS, 
                        content=final_content
                    )
                )
            ]
        )

    def level_button(title: str, subtitle: str, on_click):
        return ft.Container(
            border_radius=18, bgcolor="#f8f9fa", padding=14, ink=True, on_click=on_click, border=ft.border.all(1, "#eef1f4"),
            content=ft.Column([
                ft.Text(title, size=15, weight="bold", color=COLOR_TEXT_MAIN), ft.Container(height=2),
                ft.Text(subtitle, size=11, color=COLOR_TEXT_DESC), ft.Container(height=10),
                ft.Row([ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), border_radius=999, bgcolor="#eef5ff", content=ft.Text("학습하기", size=11, color=COLOR_PRIMARY, weight="bold"))], alignment=ft.MainAxisAlignment.END)
            ], spacing=0)
        )

    def student_info_bar():
        u = session.get("user")
        if not u: return ft.Container(height=0)
        country = country_label(u.get("country", "KR"))
        topic = session.get("topic") or "-"
        level = topic
        return ft.Container(
            padding=ft.padding.only(left=16, right=16, top=10, bottom=8), bgcolor="#ffffff", border=ft.border.only(bottom=ft.BorderSide(1, "#eef1f4")),
            content=ft.Row([
                ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), bgcolor="#f8f9fa", border_radius=999, content=ft.Text(f"🌍 {country}", size=11, color=COLOR_TEXT_DESC)),
                ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), bgcolor="#eef5ff", border_radius=999, content=ft.Text(f"📘 레벨: {level}", size=11, color=COLOR_PRIMARY, weight="bold")),
                ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), bgcolor="#fff9f0", border_radius=999, content=ft.Text(f"🏷 토픽: {topic}", size=11, color=COLOR_SECONDARY, weight="bold")),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.icons.PERSON, icon_color=COLOR_TEXT_MAIN, on_click=lambda _: go_to("/profile"))
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def student_bottom_nav(active: str = "home"):
        def nav_btn(icon, label, route, key):
            is_active = (active == key)
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=8), border_radius=14,
                bgcolor="#eef5ff" if is_active else "#ffffff", ink=True, on_click=lambda _: go_to(route),
                content=ft.Row([ft.Text(icon, size=13), ft.Text(label, size=11, color=COLOR_PRIMARY if is_active else COLOR_TEXT_DESC, weight="bold" if is_active else None)], spacing=6)
            )
        return ft.Container(
            padding=ft.padding.only(left=12, right=12, bottom=12, top=10), bgcolor="#ffffff", border=ft.border.only(top=ft.BorderSide(1, "#eef1f4")),
            content=ft.Row([
                nav_btn("🏠", t("home"), "/student_home", "home"),
                nav_btn("🗂", t("level_select"), "/level_select", "level"),
                nav_btn("⚙️", t("settings"), "/settings", "settings"),
                nav_btn("📊", t("stats"), "/stats", "stats"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

    # =============================================================================
    # Views
    # =============================================================================
    def view_landing():
        def feature_card(icon_text: str, title: str, desc: str):
            return ft.Container(
                width=340,
                padding=ft.padding.symmetric(horizontal=16, vertical=14),
                bgcolor="#f4f6f8",
                border_radius=18,
                content=ft.Row(
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            bgcolor="white",
                            border_radius=14,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text(icon_text, size=20),
                        ),
                        ft.Column(
                            spacing=4,
                            expand=True,
                            controls=[
                                ft.Text(title, size=13, weight="bold", color=COLOR_TEXT_MAIN),
                                ft.Text(desc, size=11, color=COLOR_TEXT_DESC),
                            ],
                        ),
                    ],
                ),
            )

        content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            controls=[
                ft.Container(height=10),

                # 상단 KR 아이콘(이미지에 맞게: 텍스트 "KR"로)
                ft.Container(
                    width=120,
                    height=120,
                    bgcolor="#eef5ff",
                    border_radius=30,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text("KR", size=42, weight="bold", color=COLOR_TEXT_MAIN),
                ),

                ft.Container(height=18),

                ft.Text("한국어 학습", size=26, weight="bold", color=COLOR_TEXT_MAIN),

                ft.Container(height=6),

                ft.Text(
                    "단어부터 발음, 진도 관리까지\n쉽고 체계적인 한국어 학습",
                    size=12,
                    color=COLOR_TEXT_DESC,
                    text_align="center",
                ),

                ft.Container(height=22),

                feature_card(
                    "📘",
                    "체계적 단계별 단어 & 예문 학습",
                    "한국어 표준 교육 과정에 따른\n단계별 단어 학습",
                ),
                ft.Container(height=12),
                feature_card(
                    "🎧",
                    "발음 녹음 & 평가",
                    "특별한 발음평가 엔진으로\n보다 정확한 발음 진단",
                ),
                ft.Container(height=12),
                feature_card(
                    "📊",
                    "학습 진도 관리",
                    "학생별 맞춤 진도 및 평균점 관리",
                ),

                ft.Container(height=18),

                ft.Text(
                    "화면을 터치하면 학습을 시작합니다",
                    size=10,
                    color="#b0b7c3",
                ),

                ft.Container(height=10),
            ],
        )

        # 화면 전체 탭 시 로그인으로 이동
        tappable = ft.GestureDetector(
            on_tap=lambda _: go_to("/login"),
            content=ft.Container(
                padding=28,
                content=ft.Column(
                    expand=True,
                    scroll="auto",
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[content],
                ),
            ),
        )

        return mobile_shell("/", tappable, title="")

    def view_login():
        id_field = ft.TextField(label="아이디", width=320, border_radius=12, bgcolor="white", text_size=14, autofocus=True)
        pw_field = ft.TextField(label="비밀번호", password=True, width=320, border_radius=12, bgcolor="white", text_size=14, can_reveal_password=True)
        # [수정] 에러 텍스트
        error_text = ft.Text(value="", color=COLOR_ACCENT, size=12, weight="bold", text_align="center", visible=False)
        login_btn = ft.ElevatedButton(content=ft.Text("로그인", color="white", weight="bold"), width=320, height=48, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, shape=ft.RoundedRectangleBorder(radius=14)))

        def set_loading(is_loading):
            login_btn.disabled = is_loading
            login_btn.content = ft.ProgressRing(width=20, height=20, color="white") if is_loading else ft.Text("로그인", color="white", weight="bold")
            if is_loading: error_text.visible = False
            login_btn.update()
            error_text.update()

        def show_error(msg):
            error_text.value = f"⚠️ {msg}"
            error_text.visible = True
            error_text.update()
            set_loading(False)

        async def on_login_click(e=None):
            uid = (id_field.value or "").strip()
            pw = (pw_field.value or "")
            if not uid or not pw: return show_error("아이디와 비밀번호를 입력해주세요.")
            
            set_loading(True)
            await asyncio.sleep(0.1)

            try:
                ok, user = authenticate_user(uid, pw)
                if not ok: return show_error("아이디 또는 비밀번호가 틀렸습니다.")

                if user.get("role") == "teacher" and user.get("is_approved") is False:
                    return show_error("승인 대기 중입니다. 관리자에게 문의 해주세요")

                user = ensure_progress(user)
                user["id"] = user.get("uid")
                session["user"] = user
                show_snack(f"환영합니다, {user.get('name','')}님!", COLOR_PRIMARY)
                go_home()
            except Exception as ex:
                show_error(f"시스템 오류: {str(ex)}")

        async def id_submit(e): await pw_field.focus()
        async def pw_submit(e): await on_login_click()

        id_field.on_submit = id_submit
        pw_field.on_submit = pw_submit
        login_btn.on_click = on_login_click

        try:
            id_field.text_input_action = ft.TextInputAction.NEXT
            pw_field.text_input_action = ft.TextInputAction.DONE
        except: pass

        body = ft.Column(
            scroll="auto", horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=14), ft.Text("로그인", size=24, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Text("한국어 학습을 시작해보세요", size=12, color=COLOR_TEXT_DESC),
                ft.Container(height=18), id_field, ft.Container(height=10), pw_field,
                ft.Container(height=10), error_text, ft.Container(height=10), login_btn,
                ft.Container(height=12),
                ft.Row([ft.Text("아직 회원이 아니신가요?", size=11, color=COLOR_TEXT_DESC), ft.TextButton("회원가입 하기", on_click=lambda _: go_to("/signup"), style=ft.ButtonStyle(color=COLOR_PRIMARY, overlay_color="#00000000"))], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                ft.Container(height=10),
                ft.Container(bgcolor="#f8f9fa", border_radius=14, padding=12, border=ft.border.all(1, "#eef1f4"), content=ft.Text("테스트 계정: student/1111, teacher/1111, admin/1111", size=10, color="#95a5a6")),
                ft.Container(height=10),
            ]
        )
        return mobile_shell("/login", ft.Container(padding=28, content=body), title="한국어 학습")

    def view_signup():
        signup_state.update({"id_checked": False, "id_ok": False, "sent_code": None, "phone_verified": False})
        teacher_ck = ft.Checkbox(label="선생님", value=False)
        name_tf, id_tf, email_tf = ft.TextField(label="이름", width=320), ft.TextField(label="아이디", width=230), ft.TextField(label="이메일", width=320)
        pw_tf, pw2_tf = ft.TextField(label="비밀번호", password=True, width=320), ft.TextField(label="비밀번호 확인", password=True, width=320)
        phone_tf, code_tf = ft.TextField(label="전화번호", width=230), ft.TextField(label="인증번호", width=230)
        country_dd = ft.Dropdown(label="국적", width=320, value="KR", options=[ft.dropdown.Option(c, n) for c, n in COUNTRY_OPTIONS])

        id_status = ft.Text("", size=11, color=COLOR_TEXT_DESC)
        phone_status = ft.Text("", size=11, color=COLOR_TEXT_DESC)

        btn_check_id = ft.ElevatedButton("중복확인", height=44)
        btn_send = ft.ElevatedButton("인증하기", height=44)
        btn_verify = ft.ElevatedButton("확인", height=44)
        signup_btn = ft.ElevatedButton("회원가입", width=320, height=48, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color="white", shape=ft.RoundedRectangleBorder(radius=14)), disabled=True)

        def refresh_signup_btn():
            must_ok = (signup_state.get("id_ok") is True and signup_state.get("phone_verified") is True and bool(name_tf.value) and bool(id_tf.value) and bool(email_tf.value) and bool(pw_tf.value) and bool(pw2_tf.value) and (pw_tf.value == pw2_tf.value) and bool(country_dd.value) and bool(phone_tf.value))
            signup_btn.disabled = not must_ok
            page.update()

        def on_check_id(e=None):
            ok, msg = check_id_available(id_tf.value)
            signup_state.update({"id_checked": True, "id_ok": ok})
            id_status.value, id_status.color = msg, COLOR_PRIMARY if ok else COLOR_ACCENT
            refresh_signup_btn()

        def on_send_code(e=None):
            ok, msg = send_phone_code_dummy(phone_tf.value)
            phone_status.value, phone_status.color = msg, COLOR_PRIMARY if ok else COLOR_ACCENT
            refresh_signup_btn()
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)

        def on_verify_code(e=None):
            ok, msg = verify_phone_code_dummy(code_tf.value)
            phone_status.value, phone_status.color = msg, COLOR_PRIMARY if ok else COLOR_ACCENT
            refresh_signup_btn()
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)

        async def on_signup(e=None):
            if pw_tf.value != pw2_tf.value: return show_snack("비밀번호가 일치하지 않습니다.", COLOR_ACCENT)
            ok, msg = register_user(id_tf.value, pw_tf.value, name_tf.value, email_tf.value, phone_tf.value, country_dd.value, "teacher" if teacher_ck.value else "student", True)
            show_snack(msg, COLOR_PRIMARY if ok else COLOR_ACCENT)
            if ok:
                show_snack("회원가입 성공! 선생님 계정은 관리자 승인 후 로그인 가능합니다.", COLOR_PRIMARY)
                go_to("/login")

        btn_check_id.on_click = on_check_id
        btn_send.on_click = on_send_code
        btn_verify.on_click = on_verify_code
        signup_btn.on_click = on_signup

        for tf in [name_tf, id_tf, email_tf, pw_tf, pw2_tf, phone_tf, code_tf]: tf.on_change = lambda e: refresh_signup_btn()
        country_dd.on_change = lambda e: refresh_signup_btn()
        teacher_ck.on_change = lambda e: refresh_signup_btn()

        body = ft.Container(
            expand=True, padding=24,
            content=ft.Column([
                ft.Text("회원가입", size=22, weight="bold", color=COLOR_TEXT_MAIN), ft.Text("한국어 학습을 시작해보세요", size=12, color=COLOR_TEXT_DESC),
                ft.Container(height=8), teacher_ck, ft.Container(height=10), name_tf, ft.Container(height=10),
                ft.Row([id_tf, btn_check_id], spacing=10), id_status, ft.Container(height=6),
                email_tf, ft.Container(height=10), pw_tf, ft.Container(height=10), pw2_tf, ft.Container(height=10),
                ft.Row([phone_tf, btn_send], spacing=10), ft.Container(height=6), ft.Row([code_tf, btn_verify], spacing=10), phone_status, ft.Container(height=12),
                country_dd, ft.Container(height=18), signup_btn, ft.Container(height=10),
                ft.Row([ft.Text("이미 계정이 있으신가요?", size=11, color=COLOR_TEXT_DESC), ft.TextButton("로그인", on_click=lambda _: go_to("/login"))], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto", expand=True)
        )
        return mobile_shell("/signup", body, title="회원가입", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/login")))

    def view_profile():
        u = session.get("user")
        if not u: return mobile_shell("/profile", ft.Text("로그인이 필요합니다."), title="프로필")
        uid = u.get("id") or u.get("uid")
        u = ensure_progress(get_user(uid) or u)

        # 1. 통계 데이터 계산
        topics = u["progress"]["topics"]
        total_learned = sum(len(t.get("learned", {})) for t in topics.values())
        
        # [계산 로직]
        # 연속 학습일: 실제로는 접속 로그나 학습 이력을 분석해야 하나, 
        # 현재는 progress에 저장된 streak 값을 쓰거나 없으면 학습량 유무로 1일 표시
        streak_days = u["progress"].get("streak", 1 if total_learned > 0 else 0)
        
        # 총 학습 시간: 별도 로그가 없다면 '학습 단어 수 * 3분' 등으로 추정하여 표시
        # (DB에 total_time 필드가 있다면 그것을 사용)
        total_minutes = u["progress"].get("total_time", total_learned * 3)
        total_hours = total_minutes // 60
        
        # 현재 레벨 (마지막 학습 토픽)
        last_topic = u["progress"].get("last_session", {}).get("topic", "-")
        if not last_topic: last_topic = "학습 전"

        # 다음 목표 (현재 레벨에 따라 동적 표시)
        next_goal_text = "중급 단어 완주" if "초급" in last_topic else "고급 단어 완주"
        if "고급" in last_topic: next_goal_text = "마스터 과정 도전"

        # 2. UI 구성
        
        # (1) 프로필 헤더 (이름, 상태, 배지)
        profile_header = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Container(
                    width=90, height=90, bgcolor="#eef5ff", border_radius=45,
                    alignment=ft.Alignment(0,0),
                    content=ft.Text(u.get("name", "")[:1], size=36, weight="bold", color=COLOR_PRIMARY)
                ),
                ft.Container(height=8),
                ft.Text(u.get("name", ""), size=20, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Text("오늘도 한 걸음 성장하는 중! 🌱", size=12, color=COLOR_TEXT_DESC),
                ft.Container(height=10),
                # 오늘 단어를 학습했으면 배지 표시 (today_words가 있고 session에 완료 플래그가 있거나 할 때)
                # 여기서는 간단히 session에 단어가 로드되어 있으면 표시
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor="#fff9db", border_radius=20,
                    content=ft.Text("🔥 오늘 학습 완료!", size=11, weight="bold", color="#f59f00")
                ) if session.get("today_words") else ft.Container()
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # (2) 통계 카드 ("지금까지 이렇게 했어요")
        def _stat_box(val, label):
            return ft.Container(
                expand=True,
                padding=16, bgcolor="#f8f9fa", border_radius=16, border=ft.border.all(1, "#eef1f4"),
                content=ft.Column([
                    ft.Text(str(val), size=18, weight="bold", color=COLOR_PRIMARY),
                    ft.Text(label, size=11, color=COLOR_TEXT_DESC)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

        stats_row = ft.Row([
            _stat_box(f"{streak_days}일", "연속 학습"),
            _stat_box(f"{total_learned}단어", "총 학습"),
            _stat_box(f"{total_hours}시간", "총 시간"),
        ], spacing=10)

        stats_section = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("지금까지 이렇게 했어요", size=15, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                stats_row
            ])
        )

        # (3) 레벨/목표 카드
        level_card = ft.Container(
            padding=16, bgcolor="white", border_radius=16, border=ft.border.all(1, "#eef1f4"),
            content=ft.Row([
                ft.Container(
                    width=40, height=40, bgcolor="#fdf2f8", border_radius=12, alignment=ft.Alignment(0,0),
                    content=ft.Icon(ft.icons.FLAG, color=COLOR_SECONDARY, size=20)
                ),
                ft.Column([
                    ft.Text(f"현재: {last_topic}", size=14, weight="bold", color=COLOR_TEXT_MAIN),
                    ft.Text(f"다음 목표: {next_goal_text}", size=11, color=COLOR_TEXT_DESC)
                ], spacing=2)
            ], spacing=12)
        )

        level_section = ft.Container(
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Column([
                ft.Text("나의 목표", size=15, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                level_card
            ])
        )

        # 전체 조립
        body = ft.Column(
            scroll="auto",
            controls=[
                profile_header,
                ft.Divider(height=1, thickness=1, color="#f1f3f5"),
                stats_section,
                level_section,
                ft.Container(height=30),
            ]
        )

        # [설정 이동] 우측 상단 액션 버튼
        actions = [
            ft.IconButton(icon=ft.icons.SETTINGS, icon_color=COLOR_TEXT_MAIN, on_click=lambda _: go_to("/settings"))
        ]

        return mobile_shell(
            "/profile", 
            ft.Container(expand=True, content=body), 
            title="내 프로필", 
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_home()), 
            actions=actions,
            bottom_nav=student_bottom_nav("settings")
        )

    def view_settings():
        u = session.get("user")
        if not u: return mobile_shell("/settings", ft.Text("로그인이 필요합니다."), title="설정")
        uid = u.get("id") or u.get("uid")
        u = ensure_progress(get_user(uid) or u)

        # [필드 구성] 프로필 화면에서 옮겨온 국적/언어 설정 및 개인정보
        # 이름/아이디는 수정 불가(read_only)
        name_tf = ft.TextField(label="이름", value=u.get("name", ""), width=320, read_only=True, bgcolor="#f0f2f5")
        id_tf = ft.TextField(label="아이디", value=uid, width=320, read_only=True, bgcolor="#f0f2f5")
        
        email_tf = ft.TextField(label="이메일", value=u.get("email", ""), width=320)
        phone_tf = ft.TextField(label="전화번호", value=u.get("phone", ""), width=320)
        
        country_dd = ft.Dropdown(
            label="국적", width=320, value=u.get("country", "KR"), 
            options=[ft.dropdown.Option(code, name) for code, name in COUNTRY_OPTIONS], 
            border_radius=12
        )
        
        goal_field = ft.TextField(
            label="하루 목표(단어 수)", 
            value=str(u["progress"]["settings"].get("goal", sysdata.get("default_goal", 10))), 
            width=320, keyboard_type=ft.KeyboardType.NUMBER
        )
        
        ui_lang_dd = ft.Dropdown(
            label="UI 언어", width=320, value=u["progress"]["settings"].get("ui_lang", "ko"), 
            options=[ft.dropdown.Option(code, label) for code, label in UI_LANG_OPTIONS], 
            border_radius=12
        )

        def save_all(e):
            try:
                g = int(goal_field.value)
                g = max(1, min(100, g))
                
                # 정보 업데이트
                u["progress"]["settings"]["goal"] = g
                u["progress"]["settings"]["ui_lang"] = ui_lang_dd.value
                u["country"] = country_dd.value
                u["email"] = email_tf.value
                u["phone"] = phone_tf.value
                
                update_user(uid, u)
                session["goal"] = g
                session["user"] = u
                show_snack("설정이 저장되었습니다.", COLOR_PRIMARY)
            except Exception as err:
                show_snack(f"저장 오류: {err}", COLOR_ACCENT)

        body = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("계정 설정", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                ft.Column([name_tf, id_tf, email_tf, phone_tf, country_dd], spacing=10),
                
                ft.Container(height=24),
                ft.Text("학습 설정", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                ft.Column([goal_field, ui_lang_dd], spacing=10),
                
                ft.Container(height=24),
                ft.ElevatedButton("저장하기", on_click=save_all, width=320, height=48, bgcolor=COLOR_PRIMARY, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14))),
                ft.Container(height=10),
                ft.OutlinedButton("로그아웃", on_click=lambda _: do_logout(), width=320, height=48, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14))),
                ft.Container(height=40),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto")
        )

        return mobile_shell(
            "/settings", 
            ft.Container(expand=True, content=body), 
            title="설정", 
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_home()), 
            bottom_nav=student_bottom_nav("settings")
        )

    # [수정] 통계 화면: 차트 라이브러리 미지원 오류 해결 (막대/도넛 그래프 직접 구현)
    # [수정] 통계 화면: 0개 항목 렌더링 방지 (WASM 에러 해결) 및 동적 모서리 적용
    def view_stats():
        u = session.get("user")
        if not u: return mobile_shell("/stats", ft.Text("로그인이 필요합니다."), title="통계")
        uid = u.get("id") or u.get("uid")
        u = ensure_progress(get_user(uid) or u)

        # ------------------------------
        # 1. 데이터 집계
        # ------------------------------
        topics = u["progress"]["topics"]
        
        all_learned_words = []
        for t_name, t_data in topics.items():
            for w, info in t_data.get("learned", {}).items():
                all_learned_words.append({
                    "word": w,
                    "score": info.get("last_score", 0),
                    "last_seen": info.get("last_seen", "")
                })

        total_learned = len(all_learned_words)
        total_wrong = sum(len(t.get("wrong_notes", [])) for t in topics.values())
        
        # (1) 숙련도 데이터 계산
        count_perfect = sum(1 for w in all_learned_words if w["score"] >= 90)
        count_review = sum(1 for w in all_learned_words if 70 <= w["score"] < 90)
        count_relearn = sum(1 for w in all_learned_words if w["score"] < 70)
        
        # (2) 주간 학습 데이터 계산 (최근 7일)
        from datetime import datetime, timedelta
        today = datetime.now().date()
        daily_counts = { (today - timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in range(6, -1, -1) }
        
        for w in all_learned_words:
            ls = w.get("last_seen", "")
            if ls:
                try:
                    dt = ls.split(" ")[0]
                    if dt in daily_counts:
                        daily_counts[dt] += 1
                except: pass
        
        sorted_dates = sorted(daily_counts.keys())
        
        # ------------------------------
        # 2. UI 컴포넌트 생성
        # ------------------------------

        # [A] 숙련도 그래프 (WASM 에러 방지 로직 적용)
        # 데이터가 있는 항목만 필터링하여 리스트 생성
        chart_items = []
        if count_perfect > 0:
            chart_items.append({"label": "완전 암기", "count": count_perfect, "color": COLOR_EVAL})
        if count_review > 0:
            chart_items.append({"label": "복습 필요", "count": count_review, "color": COLOR_SECONDARY})
        if count_relearn > 0:
            chart_items.append({"label": "다시 학습", "count": count_relearn, "color": COLOR_ACCENT})

        bar_controls = []
        if total_learned == 0:
            # 데이터 없음: 회색 바 하나
            bar_controls.append(ft.Container(height=20, bgcolor="#f1f3f5", border_radius=6, expand=True))
        else:
            # 데이터 있음: 유효한 항목만 컨테이너로 생성
            for i, item in enumerate(chart_items):
                # 첫 번째 항목이면 왼쪽 모서리 둥글게
                radius_dict = {}
                if i == 0:
                    radius_dict["top_left"] = 6
                    radius_dict["bottom_left"] = 6
                # 마지막 항목이면 오른쪽 모서리 둥글게
                if i == len(chart_items) - 1:
                    radius_dict["top_right"] = 6
                    radius_dict["bottom_right"] = 6
                
                # 모서리 속성 적용
                b_radius = ft.border_radius.only(**radius_dict) if radius_dict else None
                
                bar_controls.append(
                    ft.Container(
                        expand=item["count"], # 개수를 비율로 사용
                        height=20, 
                        bgcolor=item["color"], 
                        border_radius=b_radius, 
                        tooltip=f"{item['label']}: {item['count']}개"
                    )
                )

        ratio_bar = ft.Row(bar_controls, spacing=0)

        proficiency_card = ft.Container(
            padding=20, bgcolor="white", border_radius=20, border=ft.border.all(1, "#eef1f4"),
            content=ft.Column([
                ft.Text("단어 숙련도 분석", size=15, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                ratio_bar,
                ft.Container(height=10),
                # 범례 (항상 표시)
                ft.Row([
                    ft.Row([ft.Container(width=8, height=8, bgcolor=COLOR_EVAL, border_radius=2), ft.Text(f"완전 암기 ({count_perfect})", size=11, color=COLOR_TEXT_DESC)], spacing=4),
                    ft.Row([ft.Container(width=8, height=8, bgcolor=COLOR_SECONDARY, border_radius=2), ft.Text(f"복습 필요 ({count_review})", size=11, color=COLOR_TEXT_DESC)], spacing=4),
                    ft.Row([ft.Container(width=8, height=8, bgcolor=COLOR_ACCENT, border_radius=2), ft.Text(f"다시 학습 ({count_relearn})", size=11, color=COLOR_TEXT_DESC)], spacing=4),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ])
        )

        # [B] 주간 학습 추이
        max_val = max(daily_counts.values()) if daily_counts and max(daily_counts.values()) > 0 else 1
        bar_height_base = 100 
        
        bars_ui = []
        for d_str in sorted_dates:
            val = daily_counts[d_str]
            h = (val / max_val) * bar_height_base
            if h < 2 and val > 0: h = 2 
            if h > bar_height_base: h = bar_height_base # 안전장치
            
            bars_ui.append(
                ft.Column([
                    ft.Container(height=bar_height_base - h),
                    ft.Container(
                        width=14, height=h, 
                        bgcolor=COLOR_PRIMARY if val > 0 else "#f1f3f5", 
                        border_radius=4,
                        tooltip=f"{d_str}: {val}단어"
                    ),
                    ft.Text(d_str[5:], size=10, color="#95a5a6") 
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
            
        trend_card = ft.Container(
            padding=20, bgcolor="white", border_radius=20, border=ft.border.all(1, "#eef1f4"),
            content=ft.Column([
                ft.Text("최근 7일 학습 추이", size=15, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                ft.Row(bars_ui, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.END)
            ])
        )

        # [C] 요약 통계
        def stat_mini_card(label, value, color):
            return ft.Container(
                expand=True, padding=12, bgcolor="#f8f9fa", border_radius=14, border=ft.border.all(1, "#eef1f4"),
                content=ft.Column([
                    ft.Text(label, size=11, color="#95a5a6"),
                    ft.Text(str(value), size=18, weight="bold", color=color)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        
        summary_row = ft.Row([
            stat_mini_card("총 학습", total_learned, COLOR_PRIMARY),
            stat_mini_card("오답 노트", total_wrong, COLOR_ACCENT),
            stat_mini_card("완전 암기", count_perfect, COLOR_EVAL),
        ], spacing=10)

        # [D] 하단 버튼
        action_buttons = ft.Row([
            ft.ElevatedButton("누적 단어장", on_click=lambda _: go_to("/cumulative"), bgcolor=COLOR_PRIMARY, color="white", expand=True, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))),
            ft.ElevatedButton("오답 노트", on_click=lambda _: go_to("/wrong_notes"), bgcolor=COLOR_ACCENT, color="white", expand=True, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))),
        ], spacing=10)
        
        review_btn = ft.ElevatedButton("취약 단어 복습하기", on_click=lambda _: go_to("/review"), bgcolor=COLOR_TEXT_MAIN, color="white", width=320, height=48, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))

        body = ft.Container(
            padding=20,
            content=ft.Column([
                summary_row,
                ft.Container(height=16),
                proficiency_card,
                ft.Container(height=16),
                trend_card,
                ft.Container(height=24),
                ft.Text("학습 관리", size=15, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                action_buttons,
                ft.Container(height=10),
                review_btn,
                ft.Container(height=30),
            ], scroll="auto")
        )

        return mobile_shell(
            "/stats", 
            body, 
            title="학습 통계", 
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_home()),
            bottom_nav=student_bottom_nav("stats")
        )

    def view_student_home():
        u_session = session.get("user")
        if not u_session: return mobile_shell("/student_home", ft.Text("로그인이 필요합니다."), title="학습 홈")
        
        uid = u_session.get("id") or u_session.get("uid")
        user = ensure_progress(get_user(uid) or u_session)
        session["user"] = user

        # [기존 로직] 레벨 순서 및 토픽 설정
        LEVEL_ORDER = ["초급1", "초급2", "중급1", "중급2", "고급"]
        db_keys = list(VOCAB_DB.keys())
        topics = sorted(db_keys, key=lambda x: LEVEL_ORDER.index(x) if x in LEVEL_ORDER else 999)

        last = user["progress"].get("last_session", {"topic": "", "idx": 0})
        last_topic = (last.get("topic") or "").strip()
        last_idx = int(last.get("idx", 0) or 0)

        current_topic = session.get("topic")
        if not current_topic or current_topic == "-" or current_topic not in VOCAB_DB:
            if last_topic and last_topic in VOCAB_DB:
                session["topic"] = last_topic
            elif topics:
                session["topic"] = topics[0]
        
        current_topic = session.get("topic")
        goal = int(user["progress"]["settings"].get("goal", 10))
        
        topics_prog = user["progress"]["topics"]
        total_learned = sum(len(t.get("learned", {})) for t in topics_prog.values())
        progress_value = min(total_learned / max(1, goal), 1.0)
        percent = int(progress_value * 100)

        active_notices = get_active_notices(uid)
        unread_count = len([n for n in active_notices if uid not in n.get("read_by", [])])
        noti_icon = ft.IconButton(ft.icons.NOTIFICATIONS_OUTLINED, tooltip="공지사항", on_click=lambda _: go_to("/notice_inbox"))
        actions = [ft.Stack([noti_icon, ft.Container(content=ft.CircleAvatar(bgcolor=COLOR_ACCENT, radius=4, content=ft.Container()), padding=ft.padding.only(left=24, top=8))])] if unread_count > 0 else [noti_icon]

        # [필수] 모듈 Import
        from datetime import datetime
        import calendar
        import random

        now_dt = datetime.now()
        
        # --- [기능] 미니 달력 위젯 (오른쪽) ---
        def build_mini_calendar():
            year, month = now_dt.year, now_dt.month
            try:
                cal = calendar.monthcalendar(year, month)
            except Exception as e:
                return ft.Text("Err")

            today_day = now_dt.day
            
            # 요일 헤더
            weeks_ui = [ft.Row([
                ft.Container(width=22, alignment=ft.Alignment(0,0), content=ft.Text(d, size=8, color=COLOR_TEXT_DESC)) 
                for d in ["일", "월", "화", "수", "목", "금", "토"]
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=1)]
            
            # 날짜 그리드
            for week in cal:
                days_row = []
                for day in week:
                    if day == 0:
                        days_row.append(ft.Container(width=22)) 
                    else:
                        is_today = (day == today_day)
                        
                        # [수정됨] 더미 출석 로직 제거 (실제 데이터 연동 전까지는 표시 안 함)
                        is_attended = False 
                        
                        bg_color = COLOR_PRIMARY if is_today else ("#eef5ff" if is_attended else "transparent")
                        txt_color = "white" if is_today else (COLOR_PRIMARY if is_attended else COLOR_TEXT_MAIN)
                        weight = "bold" if is_today else None
                        
                        day_container = ft.Container(
                            width=22, height=22, 
                            border_radius=11, 
                            bgcolor=bg_color,
                            alignment=ft.Alignment(0,0),
                            content=ft.Text(str(day), size=9, color=txt_color, weight=weight)
                        )
                        days_row.append(day_container)
                
                weeks_ui.append(ft.Row(days_row, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=1))

            return ft.Container(
                bgcolor="white", padding=10, border_radius=16, border=ft.border.all(1, "#eef1f4"),
                expand=True,
                content=ft.Column([
                    ft.Text(f"{month}월", weight="bold", size=11, color=COLOR_TEXT_MAIN),
                    ft.Column(weeks_ui, spacing=2)
                ], spacing=4)
            )

        # --- [기능] 프로필 이미지 위젯 (왼쪽) ---
        random_chars = ["🦁", "🐰", "🐻", "🐶", "🐱", "🦊", "🐨", "🐼"]
        user_char = random.choice(random_chars)
        
        profile_widget = ft.Container(
            width=90, height=120, 
            bgcolor="#fff9db", border_radius=16,
            alignment=ft.Alignment(0,0),
            content=ft.Column([
                ft.Text(user_char, size=36),
                ft.Text("Today", size=9, color="#f59f00", weight="bold"),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        )

        # --- [기능] 챗봇 버튼 ---
        chatbot_btn = ft.Container(
            width=110, height=48,
            bgcolor=COLOR_PRIMARY,
            border_radius=24,
            shadow=ft.BoxShadow(blur_radius=10, color="#4D000000", offset=ft.Offset(0, 4)),
            content=ft.Row([
                ft.Icon(ft.icons.SUPPORT_AGENT_ROUNDED, color="white", size=20),
                ft.Text("AI 튜터", color="white", size=13, weight="bold")
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            on_click=lambda _: show_snack("챗봇 기능은 준비 중입니다.", COLOR_PRIMARY),
            ink=True 
        )

        # [기존 기능] 학습 시작 함수들
        def start_study(topic_name: str, resume: bool = False):
            if topic_name not in VOCAB_DB: return show_snack("아직 준비 중인 토픽입니다.", COLOR_ACCENT)
            if resume and session.get("topic") == topic_name and session.get("study_words"):
                go_to("/study")
                return
            all_words = VOCAB_DB[topic_name] or []
            if not all_words: return show_snack("학습할 단어 데이터가 없습니다.", COLOR_ACCENT)
            learned_set = set(user["progress"]["topics"].get(topic_name, {}).get("learned", {}).keys())
            unlearned = [w for w in all_words if w["word"] not in learned_set]
            target_source = unlearned if unlearned else all_words
            pick = target_source[:goal]
            bump_nav_token()
            reset_pron_state()
            idx = 0
            session.update({
                "motivate_shown": False, "is_review": False, "test_queue": [], "today_words": pick,
                "review_queue": [], "topic": topic_name, "study_words": pick, "idx": idx
            })
            user["progress"]["last_session"] = {"topic": topic_name, "idx": idx}
            update_user(uid, user)
            go_to("/study")

        def start_today(e=None):
            target = current_topic if (current_topic and current_topic in VOCAB_DB) else (last_topic if last_topic else topics[0])
            start_study(target, resume=False)

        def on_ad_click(e):
             show_snack("광고 페이지로 이동합니다.", COLOR_PRIMARY)

        continue_btn = ft.Container(height=0)
        if last_topic and last_topic in VOCAB_DB:
            continue_btn = ft.Container(
                bgcolor="#eef5ff", border_radius=16, padding=10, border=ft.border.all(1, "#dbeafe"),
                content=ft.Row([
                    ft.Column([
                        ft.Text("이어서 학습하기", size=11, weight="bold", color=COLOR_PRIMARY), 
                        ft.Text(f"{last_topic} · {last_idx + 1}번부터", size=10, color=COLOR_TEXT_DESC)
                    ], expand=True, spacing=1),
                    ft.ElevatedButton("계속", on_click=lambda _: start_study(last_topic, True), bgcolor=COLOR_PRIMARY, color="white", height=30)
                ])
            )

        # 본문 구성
        content_body = ft.Column(
            spacing=0, 
            scroll="auto", # 스크롤 활성화
            expand=True,   # 스크롤 영역 확보
            controls=[
                student_info_bar(),
                ft.Container(
                    padding=16,
                    content=ft.Column([
                        
                        # 상단: 프로필 + 달력
                        ft.Row([
                            profile_widget,        
                            ft.Container(width=8), 
                            build_mini_calendar()   
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),

                        ft.Container(height=6), 
                        
                        # 오늘의 학습 카드 (Compact Mode)
                        ft.Container(
                            bgcolor="white", 
                            padding=12,  
                            border_radius=16, 
                            border=ft.border.all(1, "#eef1f4"),
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("오늘의 달성률", size=12, weight="bold"), 
                                    ft.Text(f"{percent}%", size=12, weight="bold", color=COLOR_PRIMARY)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                
                                ft.Container(height=4),
                                ft.ProgressBar(value=progress_value, color=COLOR_PRIMARY, bgcolor="#eeeeee", height=6, border_radius=3),
                                ft.Container(height=4),
                                ft.Text(f"목표 {goal}개 중 {total_learned}개 완료", size=10, color=COLOR_TEXT_DESC),
                                
                                ft.Container(height=10),
                                
                                ft.ElevatedButton(
                                    content=ft.Row([ft.Icon(ft.icons.PLAY_ARROW_ROUNDED, color="white", size=18), ft.Text("오늘의 학습 시작", size=13, weight="bold", color="white")], alignment=ft.MainAxisAlignment.CENTER),
                                    on_click=start_today, 
                                    bgcolor=COLOR_PRIMARY, color="white", 
                                    width=320, height=38, 
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
                                ),
                            ], spacing=0) 
                        ),
                        
                        ft.Container(height=6),
                        continue_btn,
                        
                        # 광고 영역
                        ft.Container(height=10), 
                        build_ad_zone(on_click=on_ad_click), 
                        ft.Container(height=100),
                        
                    ], spacing=6) 
                ),
            ]
        )

        return mobile_shell(
            "/student_home", 
            body=content_body, 
            title="Just Voca", 
            actions=actions, 
            bottom_nav=student_bottom_nav("home"),
            floating_action_button=chatbot_btn
        )
    
    def view_review_intro():
        # [사양] "3초 후 복습이 시작돼요..." 또는 [지금 시작] 버튼
        def start_review_now(e=None):
            go_to("/study") # 복습 모드로 설정된 상태로 study로 이동

        # 3초 후 자동 이동 타이머 (화면이 마운트된 후 실행 필요)
        # Flet View에서는 did_mount 등을 쓰기 어려우므로 버튼 유도 혹은 비동기 sleep 사용
        # 여기서는 심플하게 버튼 클릭을 유도하거나, schedule_go를 사용
        schedule_go(3.0, "/study")

        body = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            padding=40,
            content=ft.Column([
                ft.Icon(ft.icons.ACCESS_TIME_FILLED_ROUNDED, size=60, color=COLOR_PRIMARY),
                ft.Container(height=20),
                ft.Text("오늘 학습 기록을\n지킬 수 있어요!", size=20, weight="bold", text_align="center", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                ft.Text("점수가 부족한 단어를\n한 번 더 복습하고 넘어갈게요.", size=14, color=COLOR_TEXT_DESC, text_align="center"),
                ft.Container(height=40),
                ft.Text("3초 후 복습이 시작돼요...", size=12, color="#adb5bd"),
                ft.Container(height=20),
                ft.ElevatedButton("지금 시작", on_click=start_review_now, bgcolor=COLOR_PRIMARY, color="white", width=200)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
        )
        return mobile_shell("/review_intro", body, title="")
    
    def view_level_select():
        if not session.get("user"):
            return mobile_shell("/level_select", ft.Text("로그인이 필요합니다."), title="레벨 선택")

        u_session = session.get("user")
        uid = u_session.get("id") or u_session.get("uid")
        user = ensure_progress(get_user(uid) or u_session)

        # 이미지처럼 고정 레벨(있으면 활성, 없으면 비활성)
        LEVELS = ["초급1", "초급2", "중급1", "중급2", "고급"]

        def start_study(topic_name: str):
            if topic_name not in VOCAB_DB:
                return show_snack("아직 준비 중인 레벨입니다.", COLOR_ACCENT)

            all_words = VOCAB_DB[topic_name] or []
            if not all_words:
                return show_snack("학습할 단어 데이터가 없습니다.", COLOR_ACCENT)

            goal = int(user["progress"]["settings"].get("goal", session["goal"]))

            learned_set = set(user["progress"]["topics"].get(topic_name, {}).get("learned", {}).keys())
            unlearned = [w for w in all_words if w.get("word") and w["word"] not in learned_set]
            target_source = unlearned if unlearned else all_words
            pick = target_source[:goal]

            session["today_words"] = pick[:]
            bump_nav_token()
            reset_pron_state()
            session.update(
                {
                    "motivate_shown": False,
                    "is_review": False,
                    "test_queue": [],
                    "topic": topic_name,
                    "study_words": pick,
                    "idx": 0,
                }
            )

            user["progress"]["last_session"] = {"topic": topic_name, "idx": 0}
            update_user(uid, user)
            session["user"] = user
            go_to("/study")

        def level_btn(label: str, enabled: bool):
            # 이미지 느낌: 흰 배경 + 연한 보더 + 둥근 모서리 + 가운데 정렬
            bg = "white"
            border_color = "#e9ecef"
            txt_color = COLOR_TEXT_MAIN if enabled else "#c0c6cf"

            return ft.Container(
                height=54,
                border_radius=14,
                bgcolor=bg,
                border=ft.border.all(1, border_color),
                alignment=ft.Alignment(0, 0),
                ink=enabled,
                on_click=(lambda e, lv=label: start_study(lv)) if enabled else None,
                opacity=1.0 if enabled else 0.55,
                content=ft.Text(label, size=13, weight="bold", color=txt_color),
            )

        # 버튼 6개(2열) 구성
        # GridView 말고 Column+Row로 고정 배치하면 이미지처럼 안정적으로 나옵니다.
        rows = []
        for i in range(0, len(LEVELS), 2):
            left = LEVELS[i]
            right = LEVELS[i + 1] if i + 1 < len(LEVELS) else None

            rows.append(
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.Container(expand=True, content=level_btn(left, left in VOCAB_DB)),
                        ft.Container(expand=True, content=level_btn(right, right in VOCAB_DB)) if right else ft.Container(expand=True),
                    ],
                )
            )

        body = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            padding=ft.padding.only(left=24, right=24, top=28, bottom=16),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(height=6),
                    ft.Text("Pronunciation Master", size=16, weight="bold", color=COLOR_PRIMARY),
                    ft.Container(height=6),
                    ft.Text("학습할 레벨을 선택해 주세요", size=11, color=COLOR_TEXT_DESC),
                    ft.Container(height=20),
                    ft.Column(rows, spacing=12, width=340),
                    ft.Container(expand=True),
                ],
            ),
        )

        return mobile_shell(
            "/level_select",
            body,
            title="",  # 이미지처럼 상단바 타이틀 비움
            leading=None,
            bottom_nav=student_bottom_nav("level"),
        )

    def view_motivate():
        if not session.get("user"): return mobile_shell("/motivate", ft.Text("로그인이 필요합니다."), title="레벨 선택")
        msg = (session.get("motivate_msg") or "").strip() or "지금처럼만 하면 충분해요 ☺️"
        emo = (session.get("motivate_emoji") or "").strip() or "🙂"
        
        body = ft.Column(
            spacing=0,
            controls=[
                student_info_bar(),
                ft.Container(
                    expand=True, padding=24,
                    content=ft.Column([
                        ft.Container(height=18),
                        ft.Text(msg, size=14, color=COLOR_TEXT_MAIN, text_align="center"),
                        ft.Container(height=22),
                        ft.Container(width=300, height=180, border_radius=26, bgcolor="#ffffff", border=ft.border.all(1, "#dfe6ee"), alignment=ft.Alignment(0, 0), content=ft.Text(emo, size=64)),
                        ft.Container(expand=True),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
                )
            ]
        )
        schedule_go(0.8, "/study", only_if_route="/motivate")
        return mobile_shell("/motivate", body, title="학습 격려", leading=None, bottom_nav=student_bottom_nav("home"))

    def view_study():
        if not session.get("user"): return mobile_shell("/study", ft.Text("로그인이 필요합니다."), title="단어 학습")
        
        words = session.get("study_words", [])
        topic = session.get("topic", "")
        if not words: return mobile_shell("/study", ft.Container(content=ft.Text("학습할 데이터가 없습니다.")), title="학습")

        is_review = session.get("is_review", False)
        page_title = "단어 복습" if is_review else "오늘의 학습"

        class StudyState:
            idx = session.get("idx", 0)
            is_front = True

        st = StudyState()
        total = len(words)
        status_text = ft.Text("", size=11, color="#95a5a6")

        # [기능] 단어 학습 처리 (DB 저장)
        def mark_seen_default(word_item):
            u_session = session.get("user")
            uid = u_session.get("id") or u_session.get("uid")
            user = get_user(uid) or u_session
            user = ensure_progress(user)
            user = ensure_topic_progress(user, topic)
            tpdata = user["progress"]["topics"].get(topic, {})
            learned = tpdata.get("learned", {})
            
            # 처음 본 단어면 learned에 추가
            if word_item["word"] not in learned:
                user = update_learned_word(user, topic, word_item, 90)
            else:
                user = update_last_seen_only(user, topic, word_item)
                
            update_user(uid, user)
            session["user"] = user

        # [기능 1] 격려 화면 로직 (복구됨)
        def maybe_motivate(new_idx: int):
            # 복습 모드이거나 이미 보여줬으면 패스
            if is_review or session.get("motivate_shown", False): return
            if len(words) < 2: return
            
            # 절반 지점(예: 10개 중 5번째)에서 격려
            half_reach_idx = math.ceil(len(words) / 2) - 1
            if new_idx == half_reach_idx:
                session["motivate_shown"] = True
                if not session.get("motivate_msg"): session["motivate_msg"] = random.choice(MOTIVATE_MESSAGES)
                if not session.get("motivate_emoji"): session["motivate_emoji"] = random.choice(MOTIVATE_EMOJIS)
                go_to("/motivate")

        # [기능 2] 복습 큐 추가 (시뮬레이션 유지)
        def check_and_add_review(word_item):
            if is_review: return 
            if "review_queue" not in session: session["review_queue"] = []
            
            # (테스트용) 30% 확률로 복습 대상 추가 (2번 항목 요청대로 유지)
            import random
            if random.random() < 0.3:
                exists = any(w["word"] == word_item["word"] for w in session["review_queue"])
                if not exists: session["review_queue"].append(word_item)

        def persist_position():
            u_session = session.get("user")
            uid = u_session.get("id") or u_session.get("uid")
            user = get_user(uid) or u_session
            user = ensure_progress(user)
            if not is_review:
                user["progress"]["last_session"] = {"topic": topic, "idx": st.idx}
                update_user(uid, user)
            session["user"] = user

        def change_card(delta):
            # 1. 다음 카드로 넘어갈 때 처리 (delta > 0)
            if delta > 0:
                # 학습 완료 처리 (DB 저장)
                try: mark_seen_default(words[st.idx])
                except: pass
                
                # 복습 대상인지 체크 (시뮬레이션)
                try: check_and_add_review(words[st.idx])
                except: pass

                # [복구됨] 다음 인덱스 기준으로 격려 화면 체크
                maybe_motivate(st.idx + delta)

            new_idx = st.idx + delta
            if 0 <= new_idx < total:
                st.idx = new_idx
                session["idx"] = new_idx
                st.is_front = True
                status_text.value = ""
                persist_position()
                update_view()
            elif new_idx >= total:
                persist_position()
                
                # 학습 종료 후 분기 처리
                
                # 1. 이미 복습 모드였으면 -> 바로 테스트로
                if is_review:
                    go_to("/test_intro")
                    return

                # 2. 일반 학습이었으면 -> 복습할게 있는지 확인
                review_list = session.get("review_queue", [])
                if review_list:
                    # 복습 세션 설정
                    session["study_words"] = review_list
                    session["idx"] = 0
                    session["is_review"] = True
                    go_to("/review_intro") # 안내 화면으로 이동
                else:
                    # 복습할 게 없으면 바로 테스트
                    go_to("/test_intro")

        def flip_card(e=None):
            st.is_front = not st.is_front
            update_view()

        def start_recording():
            session["pron_state"]["recording"] = True
            session["pron_state"]["recorded"] = False
            status_text.value = "🎙 녹음 중... (더미)"
            page.update()

        def stop_recording():
            session["pron_state"]["recording"] = False
            session["pron_state"]["recorded"] = True
            status_text.value = "⏹ 녹음 종료."
            page.update()

        def open_pron_result_for_current():
            w = words[st.idx]
            session["pron_state"].update({"target_word": w.get("word", ""), "target_example": w.get("ex", ""), "result_score": None, "result_comment": "", "detail": []})
            go_to("/pron_result")

        def eojeol_buttons(example: str):
            parts = [p for p in (example or "").split() if p.strip()]
            if not parts: return ft.Container(height=0)
            return ft.Row(controls=[ft.OutlinedButton(p, on_click=lambda e, t=p: play_tts(t), height=32) for p in parts[:12]], wrap=True, spacing=6, run_spacing=8)

        def render_card_content():
            w = words[st.idx]
            right_badges = [ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), bgcolor="#fff5f5", border_radius=999, content=ft.Text("복습중", size=11, color=COLOR_ACCENT, weight="bold"))] if is_review else []
            
            header = ft.Row([
                ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), bgcolor="#f8f9fa", border_radius=999, content=ft.Text(f"{topic}", size=11, color=COLOR_TEXT_DESC)),
                ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), bgcolor="#f8f9fa", border_radius=999, content=ft.Text(f"{st.idx + 1}/{total}", size=11, color=COLOR_TEXT_DESC)),
                ft.Container(expand=True), *right_badges, ft.IconButton(icon=ft.icons.HOME, icon_color=COLOR_TEXT_MAIN, on_click=lambda _: go_to("/level_select"))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            if st.is_front:
                return ft.Column([
                    header, ft.Container(height=10),
                    ft.Container(content=ft.Text(w.get("image", "📖"), size=54), width=110, height=110, bgcolor="#f8f9fa", border_radius=55, alignment=ft.Alignment(0, 0)),
                    ft.Container(height=12), ft.Text(w["word"], size=34, weight="bold", color=COLOR_TEXT_MAIN), ft.Text(w.get("pronunciation", ""), size=14, color=COLOR_SECONDARY),
                    ft.Container(height=14),
                    ft.Container(bgcolor="#fff9f0", padding=14, border_radius=14, content=ft.Column([ft.Text(w.get("mean", ""), size=14, weight="bold", color=COLOR_TEXT_MAIN, text_align="center"), ft.Text(w.get("desc", ""), size=11, color="#8a7e6a", italic=True, text_align="center")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)),
                    ft.Container(height=10),
                    ft.ElevatedButton("🔊 단어 듣기", on_click=lambda e: play_tts(w["word"]), width=200, bgcolor=COLOR_PRIMARY, color="white"),
                    ft.Container(height=8),
                    ft.Row([ft.OutlinedButton("뒷면 보기", on_click=lambda _: flip_card(), expand=True), ft.ElevatedButton("다음 ▶", on_click=lambda e: change_card(1), expand=True, bgcolor=COLOR_TEXT_MAIN, color="white")], spacing=10)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            else:
                is_rec, is_recorded = bool(session["pron_state"].get("recording")), bool(session["pron_state"].get("recorded"))
                rec_btn = ft.ElevatedButton("⏹ 중지", on_click=lambda e: stop_recording(), expand=True, bgcolor=COLOR_TEXT_MAIN, color="white") if is_rec else (ft.ElevatedButton("✅ 결과 보기", on_click=lambda e: open_pron_result_for_current(), expand=True, bgcolor=COLOR_EVAL, color="white") if is_recorded else ft.ElevatedButton("🎙 문장 녹음", on_click=lambda e: start_recording(), expand=True, bgcolor=COLOR_ACCENT, color="white"))
                
                return ft.Column([
                    header,
                    ft.Container(bgcolor="#eef5ff", padding=14, border_radius=16, margin=ft.margin.symmetric(vertical=12), border=ft.border.only(left=ft.BorderSide(5, COLOR_PRIMARY)), content=ft.Column([ft.Text("[Example]", size=11, color=COLOR_PRIMARY, weight="bold"), ft.Text(w.get("ex", ""), size=14, color=COLOR_TEXT_MAIN), ft.Container(height=8), ft.Text("어절별 듣기", size=11, color=COLOR_TEXT_DESC), eojeol_buttons(w.get("ex", ""))], spacing=6)),
                    ft.Row([ft.ElevatedButton("▶ 문장 듣기", on_click=lambda e: play_tts(w.get("ex", "")), expand=True, bgcolor=COLOR_PRIMARY, color="white"), rec_btn], spacing=10),
                    ft.Container(height=8), status_text, ft.Container(expand=True),
                    ft.Row([ft.OutlinedButton("앞면 보기", on_click=lambda _: flip_card(), expand=True), ft.OutlinedButton("이전", on_click=lambda e: change_card(-1), expand=True), ft.OutlinedButton("다음", on_click=lambda e: change_card(1), expand=True)], spacing=10)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        card_container = ft.Container(content=render_card_content(), width=340, bgcolor=COLOR_CARD_BG, border_radius=24, padding=20, shadow=ft.BoxShadow(blur_radius=30, color="#14000000", offset=ft.Offset(0, 14)), alignment=ft.Alignment(0, 0), on_click=lambda e: flip_card(e))
        
        def update_view():
            if card_container.page:
                card_container.content = render_card_content()
                card_container.update()

        body = ft.Column(spacing=0, controls=[student_info_bar(), ft.Container(expand=True, padding=20, content=ft.Column([ft.Container(height=4), card_container, ft.Container(height=10), ft.Text("카드를 터치하거나 버튼으로 앞/뒤를 전환하세요", color="#bdc3c7", size=11)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto", expand=True))])
        
        return mobile_shell("/study", body, title=page_title, leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_home()), bottom_nav=student_bottom_nav("home"))

    def view_pron_result():
        if not session.get("user"): return mobile_shell("/pron_result", ft.Text("로그인이 필요합니다."), title="발음 결과")
        ps = session.get("pron_state", {})
        word, example_text, recorded = ps.get("target_word", ""), ps.get("target_example", ""), bool(ps.get("recorded", False))
        score_text, comment_text, detail_col = ft.Text("", size=22, weight="bold", color=COLOR_EVAL), ft.Text("", size=12, color=COLOR_TEXT_DESC, text_align="center"), ft.Column(scroll="auto", expand=True, spacing=6)
        result_box = ft.Container(visible=False, bgcolor="#f8f9fa", border_radius=18, padding=16, border=ft.border.all(1, "#eef1f4"), content=ft.Column([ft.Text("평가 결과", size=13, weight="bold", color=COLOR_TEXT_MAIN), ft.Container(height=8), ft.Row([ft.Container(width=88, height=88, border_radius=44, border=ft.border.all(5, COLOR_EVAL), alignment=ft.Alignment(0, 0), content=ft.Column([score_text, ft.Text("점수", size=10, color="grey")], alignment=ft.MainAxisAlignment.CENTER, spacing=0)), ft.Container(expand=True)]), ft.Container(height=6), comment_text, ft.Divider(height=18), ft.Text("어절별 점수(더미)", size=11, color=COLOR_TEXT_DESC), ft.Container(height=6), ft.Container(content=detail_col, height=220)], horizontal_alignment=ft.CrossAxisAlignment.CENTER))

        def run_ai_eval(e=None):
            if not recorded: return show_snack("먼저 문장 녹음을 완료해 주세요. (현재는 더미)", COLOR_ACCENT)
            score, raw_comment, tag, detail = evaluate_pronunciation_dummy(example_text or word)
            score_text.value, comment_text.value = str(score), post_process_comment(tag, raw_comment)
            detail_col.controls = [ft.Container(bgcolor="white", border_radius=14, padding=10, border=ft.border.all(1, "#eef1f4"), content=ft.Row([ft.Text(d.get("unit", ""), size=12, color=COLOR_TEXT_MAIN), ft.Text(f"{d.get('score', 0)}점", size=12, weight="bold", color=COLOR_EVAL if d.get('score', 0) >= 85 else COLOR_ACCENT)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)) for d in detail]
            result_box.visible = True
            page.update()
            
            try:
                topic, wlist = session.get("topic", ""), session.get("study_words", [])
                found = next((it for it in wlist if it.get("word") == word), None)
                if found and topic:
                    u_session = session.get("user")
                    uid = u_session.get("id") or u_session.get("uid")
                    user = update_learned_word(ensure_progress(get_user(uid) or u_session), topic, found, score)
                    update_user(uid, user)
                    session["user"] = user
            except Exception as err2: log_write(f"persist pron score error: {err2}")

        def back_to_study(e=None):
            session["pron_state"].update({"recording": False, "recorded": False})
            go_to("/study")

        body = ft.Column(spacing=0, controls=[student_info_bar(), ft.Container(expand=True, padding=20, content=ft.Column([ft.Text("발음 녹음 결과", size=16, weight="bold", color=COLOR_TEXT_MAIN), ft.Container(height=10), ft.Container(bgcolor="white", border_radius=18, padding=14, border=ft.border.all(1, "#eef1f4"), content=ft.Column([ft.Text(word, size=20, weight="bold", color=COLOR_TEXT_MAIN), ft.Text(example_text, size=13, color=COLOR_TEXT_DESC), ft.Container(height=8), ft.Row([ft.ElevatedButton("▶ 문장 듣기", on_click=lambda _: play_tts(example_text), bgcolor=COLOR_PRIMARY, color="white", expand=True), ft.ElevatedButton("AI 평가", on_click=run_ai_eval, bgcolor=COLOR_ACCENT, color="white", expand=True)], spacing=10), ft.Container(height=10), result_box], horizontal_alignment=ft.CrossAxisAlignment.CENTER)), ft.Container(height=12), ft.ElevatedButton("학습 계속하기", on_click=back_to_study, bgcolor=COLOR_TEXT_MAIN, color="white", width=320)], horizontal_alignment=ft.CrossAxisAlignment.CENTER))])
        return mobile_shell("/pron_result", body, title="발음 결과", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/study")), bottom_nav=student_bottom_nav("home"))

    def make_test_queue(topic: str, today_words: list[dict], n_choices: int = 4) -> list[dict]:
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
            if not correct: continue
            prompt = (it.get("mean", "") or "").strip() or (it.get("desc", "") or "").strip() or (it.get("ex", "") or "").strip() or "이 설명에 알맞은 단어는 무엇일까요?"
            
            candidates = [w for w in pool_words if w != correct]
            if len(candidates) < (n_choices - 1): candidates += [w for w in today_pool if w != correct and w not in candidates]
            random.shuffle(candidates)
            choices = [correct] + candidates[: max(0, n_choices - 1)]
            choices = list(dict.fromkeys(choices))
            random.shuffle(choices)
            qlist.append({"prompt": prompt, "correct": correct, "choices": choices, "selected": None, "wrong_set": set(), "answered": False, "just_correct": False})
        return qlist

    def view_review_start():
        if not session.get("user"): return mobile_shell("/review_start", ft.Text("로그인이 필요합니다."), title="복습 안내")
        topic = session.get("topic", "")
        u_session = session.get("user")
        uid = u_session.get("id") or u_session.get("uid")
        user = ensure_progress(get_user(uid) or u_session)
        thr = int(load_system().get("review_threshold", 85))

        today_words = session.get("today_words", []) or session.get("study_words", [])
        tpdata = user["progress"]["topics"].get(topic, {})
        learned = tpdata.get("learned", {})
        low_items = [it for it in today_words if learned.get(it.get("word", ""), {}).get("last_score", 999) < thr]
        low_cnt = len(low_items)

        auto_text = ft.Text("", size=12, color=COLOR_TEXT_DESC)
        auto_bar = ft.ProgressBar(width=320, value=0.0, visible=False)

        def start_auto_countdown_if_needed():
            if low_cnt <= 0:
                auto_text.value, auto_bar.visible = "복습 대상이 없습니다.", False
                return
            auto_bar.visible, auto_bar.value = True, 0.0
            total_sec, tick, token = 3.0, 0.1, bump_nav_token()

            async def _countdown():
                try:
                    remain = total_sec
                    while remain > 0:
                        if token != session.get("nav_token") or ((page.route or "").split("?", 1)[0] != "/review_start"): return
                        auto_text.value = f"{int(remain + 0.999)}초 후 복습이 자동 시작됩니다…"
                        auto_bar.value = 1.0 - (remain / total_sec)
                        page.update()
                        await asyncio.sleep(tick)
                        remain -= tick
                    if token != session.get("nav_token") or ((page.route or "").split("?", 1)[0] != "/review_start"): return
                    auto_text.value, auto_bar.value = "복습을 시작합니다…", 1.0
                    page.update()
                    _prepare_review_words()
                    page.go("/study")
                except Exception as err: log_write(f"auto countdown error: {repr(err)}")
            try: page.run_task(_countdown)
            except: pass

        def _prepare_review_words():
            session.update({"study_words": low_items, "idx": 0, "is_review": True})
            u_session = session.get("user")
            uid = u_session.get("id") or u_session.get("uid")
            user2 = ensure_progress(get_user(uid) or u_session)
            user2["progress"]["last_session"] = {"topic": topic, "idx": 0}
            update_user(uid, user2)
            session["user"] = user2

        def start_review_today(e=None, *, silent=False):
            if low_cnt == 0: return (not silent) and show_snack("복습 대상이 없습니다.", COLOR_PRIMARY)
            _prepare_review_words()
            go_to("/study")

        def start_test(e=None):
            bump_nav_token()
            go_to("/test_intro")

        start_auto_countdown_if_needed()

        body = ft.Column(spacing=0, controls=[
            student_info_bar(),
            ft.Container(expand=True, padding=24, content=ft.Column([
                ft.Container(height=6), ft.Text("오늘 학습 수고했어요 💯", size=22, weight="bold", color=COLOR_PRIMARY), ft.Container(height=10),
                ft.Container(bgcolor="#f8f9fa", border_radius=20, padding=18, border=ft.border.all(1, "#eef1f4"), content=ft.Column([ft.Text(f"복습 기준: {thr}점 미만", size=12, color=COLOR_TEXT_DESC), ft.Text(f"오늘 학습 중 복습 대상: {low_cnt}개", size=14, weight="bold", color=COLOR_TEXT_MAIN), ft.Text("점수 미달 단어를 한 번 더 보고 넘어가면 더 좋아요.", size=12, color=COLOR_TEXT_DESC)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)),
                ft.Container(height=16),
                ft.Row([ft.ElevatedButton("복습하기", on_click=start_review_today, expand=True, bgcolor=COLOR_ACCENT, color="white", disabled=(low_cnt == 0)), ft.ElevatedButton("테스트 시작", on_click=start_test, expand=True, bgcolor=COLOR_TEXT_MAIN, color="white")], spacing=10),
                auto_text, ft.Container(height=6), auto_bar, ft.Container(height=10), ft.OutlinedButton("홈으로", on_click=lambda _: go_home(), width=320)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        ])
        return mobile_shell("/review_start", body, title="복습 안내", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/study")), bottom_nav=student_bottom_nav("home"))

    def view_test_intro():
        if not session.get("user"): return mobile_shell("/test_intro", ft.Text("로그인이 필요합니다."), title="연습문제")
        topic = session.get("topic", "")
        today_words = session.get("today_words", []) or []
        u_session = session.get("user")
        uid = u_session.get("id") or u_session.get("uid")
        user = ensure_progress(get_user(uid) or u_session)
        thr = int(load_system().get("review_threshold", 85))
        tpdata = user["progress"]["topics"].get(topic, {})
        learned = tpdata.get("learned", {})
        low_items = [it for it in today_words if learned.get(it.get("word", ""), {}).get("last_score", 999) < thr]

        def start_test_now(e=None):
            combined, seen = [], set()
            for it in (today_words + low_items):
                w = (it.get("word", "") or "").strip()
                if w and w not in seen:
                    seen.add(w)
                    combined.append(it)
            
            # [수정] 전체 문제를 생성한 뒤 3개로 제한
            full_queue = make_test_queue(topic, combined, n_choices=4)
            final_queue = full_queue[:3]  # 최대 3문제만 출제
            
            session.update({"test_queue": final_queue, "test_idx": 0, "test_score": 0, "is_review": False})
            go_to("/test?i=0")

        def stamp_widget():
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "stamps/stamp_ok.png")
            return ft.Image(src="stamps/stamp_ok.png", width=120, height=120, fit=ft.ImageFit.CONTAIN) if os.path.exists(path) else ft.Text("💮", size=70)

        body = ft.Column(spacing=0, controls=[
            student_info_bar(),
            ft.Container(expand=True, padding=24, content=ft.Column([
                ft.Container(height=10), ft.Text("오늘 학습 완료!", size=22, weight="bold", color=COLOR_PRIMARY), ft.Container(height=10), ft.Text("✅ 연습문제를 풀어볼까요?", size=13, color=COLOR_TEXT_DESC),
                ft.Container(height=18), ft.Container(width=140, height=140, border_radius=26, bgcolor="#f8f9fa", alignment=ft.Alignment(0, 0), content=stamp_widget()),
                ft.Container(height=18), ft.ElevatedButton("시작하기", on_click=start_test_now, bgcolor=COLOR_TEXT_MAIN, color="white", width=320, height=48),
                ft.Container(height=10), ft.OutlinedButton("나중에", on_click=lambda _: go_home(), width=320)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER))
        ])
        return mobile_shell("/test_intro", body, title="연습문제", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/review_start")), bottom_nav=student_bottom_nav("home"))

    def view_test():
        if not session.get("user"): return mobile_shell("/test", ft.Text("로그인이 필요합니다."), title="연습문제")
        
        # 1. 큐에서 데이터 가져오기
        qlist = session.get("test_queue", [])
        if not qlist: return mobile_shell("/test", ft.Container(padding=24, content=ft.Column([ft.Text("테스트 데이터가 없습니다.", size=13, color=COLOR_TEXT_DESC), ft.Container(height=10), ft.ElevatedButton("홈", on_click=lambda _: go_home(), bgcolor=COLOR_PRIMARY, color="white")], horizontal_alignment=ft.CrossAxisAlignment.CENTER)), title="연습문제", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_home()))

        # 2. 현재 인덱스 및 문제 로드
        idx = max(0, min(int(session.get("test_idx", 0) or 0), len(qlist) - 1))
        q, total = qlist[idx], len(qlist)
        
        feedback = ft.Text("", size=14, weight="bold")
        option_boxes = []

        def _ensure_wrong_set():
            if not isinstance(q.get("wrong_set"), set): q["wrong_set"] = set()
            return q["wrong_set"]

        # [UI 업데이트] 선택 상태에 따라 보기 스타일 변경
        def apply_styles(do_update=True):
            selected, answered, correct, wrong_set = q.get("selected"), bool(q.get("answered")), q.get("correct"), _ensure_wrong_set()
            for box in option_boxes:
                word = box.data
                border_color, bg, txt_color = "#dfe6ee", "white", COLOR_TEXT_MAIN
                
                # 오답인 경우 (붉은색)
                if word in wrong_set: 
                    border_color, bg, txt_color = COLOR_ACCENT, "#fff5f5", COLOR_ACCENT
                
                # 정답인 경우 (초록색) - 문제 풀이가 끝난 후 정답 표시
                if answered and word == correct: 
                    border_color, bg, txt_color = COLOR_EVAL, "#f0fdf4", COLOR_EVAL
                
                # 현재 선택 중인 경우 (파란색)
                if (not answered) and selected == word: 
                    border_color, bg, txt_color = COLOR_PRIMARY, "#eef5ff", COLOR_PRIMARY
                
                box.border, box.bgcolor = ft.border.all(2, border_color), bg
                if isinstance(box.content, ft.Text): box.content.color = txt_color
                if do_update and box.page: box.update()

        # 보기 선택 핸들러
        def pick(word):
            if q.get("answered"): return # 이미 정답을 맞췄으면 선택 변경 불가
            q["selected"] = word
            feedback.value = ""
            feedback.update()
            apply_styles()

        def save_wrong_once(user_ans, correct, prompt):
            u_session = session.get("user")
            uid = u_session.get("id") or u_session.get("uid")
            user = add_wrong_note(ensure_progress(get_user(uid) or u_session), session.get("topic", ""), prompt, correct, user_ans)
            update_user(uid, user)
            session["user"] = user

        # [다음 문제 이동]
        def on_next(e=None):
            session["test_idx"] = idx + 1
            # 마지막 문제면 결과 페이지로, 아니면 다음 문제로
            go_to("/study_complete" if session["test_idx"] >= total else f"/test?i={session['test_idx']}")

        # [정답 확인] 버튼 핸들러
        def on_confirm(e=None):
            # 이미 정답 처리된 상태라면 바로 다음으로 이동
            if q.get("answered"): return on_next()
            
            selected = (q.get("selected") or "").strip()
            if not selected: return show_snack("보기를 선택해주세요.", COLOR_ACCENT)
            
            correct, prompt = (q.get("correct") or "").strip(), (q.get("prompt") or "").strip()

            if selected == correct:
                # 정답 처리
                q["answered"] = True
                session["test_score"] = int(session.get("test_score", 0) or 0) + 1
                feedback.value, feedback.color = "✨ 정답입니다!", COLOR_EVAL
                
                # [수정] 버튼 텍스트 및 스타일 변경 (content 사용)
                primary_btn.content.value = "다음 문제"
                primary_btn.on_click = on_next 
                # 스타일 업데이트 (새 ButtonStyle 할당)
                primary_btn.style = ft.ButtonStyle(bgcolor=COLOR_EVAL, color="white", shape=ft.RoundedRectangleBorder(radius=14))
            else:
                # 오답 처리
                ws = _ensure_wrong_set()
                if selected not in ws:
                    ws.add(selected)
                    save_wrong_once(selected, correct, prompt)
                q["selected"] = None
                feedback.value, feedback.color = "오답입니다. 다시 풀어보세요.", COLOR_ACCENT
            
            feedback.update()
            primary_btn.update()
            apply_styles()

        # 3. UI 구성 요소 생성
        for w in (q.get("choices") or []):
            option_boxes.append(
                ft.Container(
                    width=320, padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    border_radius=12, border=ft.border.all(2, "#dfe6ee"), bgcolor="white",
                    ink=True, data=w, on_click=lambda e, ww=w: pick(ww),
                    content=ft.Text(w, size=15, color=COLOR_TEXT_MAIN, weight="bold")
                )
            )

        # 초기 버튼 상태 설정
        is_answered = bool(q.get("answered"))
        btn_text = "다음 문제" if is_answered else "확인"
        btn_func = on_next if is_answered else on_confirm
        btn_color = COLOR_EVAL if is_answered else COLOR_PRIMARY

        # [수정] text=... 대신 content=ft.Text(...) 사용 (오류 해결 핵심)
        primary_btn = ft.ElevatedButton(
            content=ft.Text(btn_text, size=15, weight="bold", color="white"), 
            on_click=btn_func, 
            width=320, height=48, 
            style=ft.ButtonStyle(bgcolor=btn_color, color="white", shape=ft.RoundedRectangleBorder(radius=14))
        )
        
        if is_answered: 
            feedback.value, feedback.color = "✨ 정답입니다!", COLOR_EVAL

        body = ft.Column(spacing=0, controls=[
            student_info_bar(),
            ft.Container(
                expand=True, padding=20, 
                content=ft.Column([
                    ft.Container(
                        bgcolor="#ffffff", border_radius=20, padding=18, border=ft.border.all(1, "#eef1f4"),
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"문제 {idx+1}/{total}", size=14, color=COLOR_PRIMARY, weight="bold"),
                                ft.Container(expand=True)
                            ]),
                            ft.Container(height=12),
                            ft.Container(
                                bgcolor="#f8f9fa", border_radius=14, padding=20, width=320,
                                content=ft.Column([
                                    ft.Text(f"“{q.get('prompt','')}”", size=16, weight="bold", color=COLOR_TEXT_MAIN, text_align="center"),
                                    ft.Container(height=8),
                                    ft.Text("이 설명에 알맞은 단어는?", size=12, color=COLOR_TEXT_DESC)
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                            ),
                            ft.Container(height=20),
                            ft.Column(option_boxes, spacing=10),
                            ft.Container(height=16),
                            feedback,
                            ft.Container(height=16),
                            primary_btn
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto", expand=True)
            )
        ])
        
        apply_styles(False)
        return mobile_shell("/test", body, title="연습문제", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_home()), bottom_nav=student_bottom_nav("home"))
    
    def view_study_complete():
        if not session.get("user"): return mobile_shell("/study_complete", ft.Text("로그인이 필요합니다."), title="학습 결과")
        qlist, total, score = session.get("test_queue", []), len(session.get("test_queue", [])), int(session.get("test_score", 0) or 0)
        passed = (score >= math.ceil((2 * max(1, total)) / 3))

        def retry_test(e=None):
            for q in qlist: q.update({"selected": None, "wrong_set": set(), "answered": False, "just_correct": False})
            session.update({"test_idx": 0, "test_score": 0})
            go_to("/test")

        buttons = [ft.ElevatedButton("이어서 학습하기", on_click=lambda _: go_to("/level_select"), width=320, height=48, bgcolor=COLOR_EVAL if passed else COLOR_PRIMARY, color="white")]
        if not passed: buttons.append(ft.ElevatedButton("다시 풀기", on_click=retry_test, width=320, height=48, bgcolor=COLOR_SECONDARY, color="white"))
        buttons.append(ft.ElevatedButton("오늘 학습 완료", on_click=lambda _: go_to("/student_home"), width=320, height=48, bgcolor=COLOR_EVAL, color="white"))

        body = ft.Column(spacing=0, controls=[
            student_info_bar(),
            ft.Container(expand=True, padding=24, content=ft.Column([
                ft.Container(height=10), ft.Text("🎉", size=42), ft.Container(height=6), ft.Text("학습 결과", size=18, weight="bold", color=COLOR_TEXT_MAIN), ft.Container(height=8),
                ft.Text(f"총 {total}문제 중 {score}문제를 맞혔습니다.", size=12, color=COLOR_TEXT_DESC), ft.Container(height=22),
                ft.Column(buttons, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START))
        ])
        return mobile_shell("/study_complete", body, title="학습 결과", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_home()), bottom_nav=student_bottom_nav("home"))

    def view_cumulative():
        if not session.get("user"): return mobile_shell("/cumulative", ft.Text("로그인이 필요합니다."), title="누적 학습")
        u_session = session.get("user")
        uid = u_session.get("id") or u_session.get("uid")
        user = ensure_progress(get_user(uid) or u_session)

        topic_dd = ft.Dropdown(width=220, options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())], value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None))
        mask_dd = ft.Dropdown(width=120, options=[ft.dropdown.Option("none", "가리기 없음"), ft.dropdown.Option("word", "단어 가리기"), ft.dropdown.Option("mean", "뜻 가리기")], value=session.get("mask_mode", "none"))
        list_col = ft.Column(scroll="auto", expand=True)

        def render():
            session["mask_mode"] = mask_dd.value
            tp = topic_dd.value
            if not tp:
                list_col.controls = [ft.Text("토픽이 없습니다.")]
                page.update()
                return

            tpdata = user["progress"]["topics"].get(tp, {})
            items = sorted(tpdata.get("learned", {}).items(), key=lambda x: x[1].get("last_seen", ""), reverse=True)

            controls = []
            for w, info in items:
                word_txt = "••••" if mask_dd.value == "word" else w
                mean_txt = "••••" if mask_dd.value == "mean" else info.get("mean", "")
                sc = info.get("last_score", 0)
                controls.append(ft.Container(bgcolor="white", border_radius=16, padding=12, border=ft.border.all(1, "#eef1f4"), content=ft.Row([ft.Column([ft.Text(word_txt, size=15, weight="bold", color=COLOR_TEXT_MAIN), ft.Text(mean_txt, size=11, color=COLOR_TEXT_DESC), ft.Text(info.get("last_seen", ""), size=10, color="#95a5a6")], expand=True, spacing=2), ft.Container(padding=8, border_radius=12, bgcolor="#f0fdf4" if sc >= 85 else "#fff5f5", content=ft.Text(f"{sc}점", weight="bold", color=COLOR_EVAL if sc >= 85 else COLOR_ACCENT)) ])))
            
            list_col.controls = controls if controls else [ft.Text("아직 누적 학습 데이터가 없습니다.", color=COLOR_TEXT_DESC)]
            page.update()

        topic_dd.on_change = lambda e: render()
        mask_dd.on_change = lambda e: render()
        render()

        body = ft.Column(spacing=0, controls=[student_info_bar(), ft.Container(expand=True, padding=20, content=ft.Column([ft.Row([topic_dd, mask_dd], spacing=10), ft.Container(height=10), list_col]))])
        return mobile_shell("/cumulative", body, title="누적 학습", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/stats")), bottom_nav=student_bottom_nav("stats"))

    def view_wrong_notes():
        if not session.get("user"): return mobile_shell("/wrong_notes", ft.Text("로그인이 필요합니다."), title="오답노트")
        u_session = session.get("user")
        uid = u_session.get("id") or u_session.get("uid")
        user = ensure_progress(get_user(uid) or u_session)

        topic_dd = ft.Dropdown(width=260, options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())], value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None))
        col = ft.Column(scroll="auto", expand=True)

        def render():
            tp = topic_dd.value
            if not tp:
                col.controls = [ft.Text("토픽이 없습니다.")]
                page.update()
                return
            wrongs = list(reversed(user["progress"]["topics"].get(tp, {}).get("wrong_notes", [])))
            col.controls = [ft.Container(bgcolor="white", border_radius=16, padding=12, border=ft.border.all(1, "#eef1f4"), content=ft.Column([ft.Text(f"문제: {it.get('q','')}", weight="bold", color=COLOR_TEXT_MAIN), ft.Text(f"정답: {it.get('a','')}", color=COLOR_EVAL), ft.Text(f"내 답: {it.get('user','')}", color=COLOR_ACCENT), ft.Text(it.get("ts", ""), size=10, color="#95a5a6")], spacing=4)) for it in wrongs] if wrongs else [ft.Text("오답노트가 비어 있습니다.", color=COLOR_TEXT_DESC)]
            page.update()

        topic_dd.on_change = lambda e: render()
        render()
        body = ft.Column(spacing=0, controls=[student_info_bar(), ft.Container(expand=True, padding=20, content=ft.Column([ft.Row([topic_dd], spacing=10), ft.Container(height=10), col]))])
        return mobile_shell("/wrong_notes", body, title="오답노트", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/stats")), bottom_nav=student_bottom_nav("stats"))

    def view_review():
        if not session.get("user"): return mobile_shell("/review", ft.Text("로그인이 필요합니다."), title="복습")
        u_session = session.get("user")
        uid = u_session.get("id") or u_session.get("uid")
        user = ensure_progress(get_user(uid) or u_session)
        thr = int(load_system().get("review_threshold", 85))

        topic_dd = ft.Dropdown(width=260, options=[ft.dropdown.Option(t) for t in sorted(VOCAB_DB.keys())], value=session.get("topic") or (sorted(VOCAB_DB.keys())[0] if VOCAB_DB else None))
        col = ft.Column(scroll="auto", expand=True)

        def start_review(tp):
            learned = user["progress"]["topics"].get(tp, {}).get("learned", {})
            vocab_map = {it["word"]: it for it in VOCAB_DB.get(tp, []) if it.get("word")}
            items = [vocab_map[w] for w, info in learned.items() if info.get("last_score", 100) < thr and w in vocab_map]
            if not items: return show_snack("복습 대상 단어가 없습니다.", COLOR_PRIMARY)
            session.update({"topic": tp, "study_words": items, "idx": 0, "is_review": True})
            go_to("/study")

        def render():
            tp = topic_dd.value
            if not tp:
                col.controls = [ft.Text("토픽이 없습니다.")]
                page.update()
                return
            learned = user["progress"]["topics"].get(tp, {}).get("learned", {})
            low = sorted([(w, info) for w, info in learned.items() if info.get("last_score", 100) < thr], key=lambda x: x[1].get("last_score", 0))
            
            controls = [ft.Container(bgcolor="#f8f9fa", border_radius=16, padding=12, border=ft.border.all(1, "#eef1f4"), content=ft.Row([ft.Text(f"복습 기준: {thr}점 미만", color=COLOR_TEXT_DESC, size=12), ft.ElevatedButton("복습 시작", on_click=lambda _: start_review(tp), bgcolor=COLOR_ACCENT, color="white")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))]
            controls += [ft.Container(bgcolor="white", border_radius=16, padding=12, border=ft.border.all(1, "#eef1f4"), content=ft.Row([ft.Column([ft.Text(w, weight="bold", color=COLOR_TEXT_MAIN), ft.Text(info.get("mean", ""), size=11, color=COLOR_TEXT_DESC)], expand=True), ft.Text(f"{info.get('last_score',0)}점", color=COLOR_ACCENT, weight="bold")])) for w, info in low[:200]]
            if len(controls) == 1: controls.append(ft.Text("복습 대상이 없습니다.", color=COLOR_TEXT_DESC))
            col.controls = controls
            page.update()

        topic_dd.on_change = lambda e: render()
        render()
        body = ft.Column(spacing=0, controls=[student_info_bar(), ft.Container(expand=True, padding=20, content=ft.Column([ft.Row([topic_dd], spacing=10), ft.Container(height=10), col]))])
        return mobile_shell("/review", body, title="복습", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/stats")), bottom_nav=student_bottom_nav("stats"))

    def view_teacher_dash():
        # 1. 권한 체크
        u = session.get("user")
        if not u or u.get("role") != "teacher": 
            return mobile_shell("/teacher_dash", ft.Text("접근 권한이 없습니다."), title="선생님 대시보드")
        
        # 2. 학생 목록 데이터 준비
        users = load_users()
        rows = []
        for uid, s_user in users.items():
            if s_user.get("role") != "student": continue
            s_user = ensure_progress(s_user)
            
            goal = int(s_user["progress"]["settings"].get("goal", 10))
            topics = s_user["progress"]["topics"]
            
            total_learned = sum(len(t.get("learned", {})) for t in topics.values())
            avgs = [t.get("stats", {}).get("avg_score", 0) for t in topics.values() if t.get("learned")]
            avg_val = round(sum(avgs) / max(1, len(avgs)), 2) if avgs else 0.0
            w_cnt = sum(len(t.get("wrong_notes", [])) for t in topics.values())
            
            rows.append({
                "uid": uid, "name": s_user.get("name", uid), "goal": goal, 
                "learned": total_learned, 
                "ratio": int((min(total_learned, goal) / max(1, goal)) * 100) if goal else 0,
                "avg": avg_val, "wrong": w_cnt
            })
        rows.sort(key=lambda x: (-x["ratio"], -x["avg"], x["name"]))

        # 3. 학생 카드 리스트
        student_cards = []
        for s in rows:
            student_cards.append(
                ft.Container(
                    bgcolor="white", padding=14, border_radius=16, border=ft.border.all(1, "#eef1f4"), 
                    content=ft.Row([
                        ft.Container(
                            expand=True, ink=True, 
                            on_click=lambda e, u=s["uid"]: (session.update({"selected_student_id": u}), go_to("/teacher_student")),
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(s["name"], weight="bold", size=15, color=COLOR_TEXT_MAIN), 
                                    ft.Text(f"목표 {s['goal']} · 누적 {s['learned']}", size=11, color=COLOR_TEXT_DESC),
                                    ft.Text(f"평균 {s['avg']} · 오답 {s['wrong']}", size=11, color=COLOR_TEXT_DESC)
                                ], spacing=2, expand=True), 
                                ft.Container(padding=8, border_radius=12, bgcolor="#eef5ff", content=ft.Text(f"{s['ratio']}%", weight="bold", color=COLOR_PRIMARY))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    ])
                )
            )
        if not student_cards: student_cards = [ft.Container(padding=20, content=ft.Text("등록된 학생이 없습니다.", color=COLOR_TEXT_DESC))]

        # 4. 공지사항 입력 UI
        notice_title = ft.TextField(label="제목", width=280, height=40, text_size=13, content_padding=10)
        notice_content = ft.TextField(label="내용을 입력하세요", width=280, multiline=True, min_lines=3, text_size=13)
        
        is_scheduled = ft.Checkbox(label="예약 발송", value=False)
        date_btn = ft.ElevatedButton("날짜 선택", icon=ft.icons.CALENDAR_TODAY, visible=False)
        time_btn = ft.ElevatedButton("시간 선택", icon=ft.icons.ACCESS_TIME, visible=False)
        schedule_info = ft.Text("즉시 발송됩니다.", size=11, color=COLOR_TEXT_DESC)
        
        selected_dt = {"date": None, "time": None}

        def update_schedule_ui():
            if not is_scheduled.value:
                schedule_info.value = "즉시 발송됩니다."
                date_btn.visible = False
                time_btn.visible = False
            else:
                date_btn.visible = True
                time_btn.visible = True
                d_str = selected_dt["date"].strftime("%Y-%m-%d") if selected_dt["date"] else "날짜미정"
                t_str = selected_dt["time"].strftime("%H:%M") if selected_dt["time"] else "시간미정"
                schedule_info.value = f"발송 예정: {d_str} {t_str}"
            if page: page.update()

        def on_date_change(e):
            selected_dt["date"] = e.control.value
            update_schedule_ui()
        
        def on_time_change(e):
            selected_dt["time"] = e.control.value
            update_schedule_ui()

        # DatePicker, TimePicker 생성
        date_picker = ft.DatePicker(on_change=on_date_change)
        time_picker = ft.TimePicker(on_change=on_time_change)

        # [핵심 수정] 3중 안전장치가 적용된 열기 함수
        def open_picker_safe(picker):
            print(f"DEBUG: Trying to open picker {picker}") # 콘솔 디버깅용
            
            # 0. Overlay에 없으면 무조건 추가
            try:
                if picker not in page.overlay:
                    page.overlay.append(picker)
                    page.update()
            except: pass

            # 1. 최신 Flet 방식 (page.open)
            if hasattr(page, "open"):
                try:
                    page.open(picker)
                    return
                except Exception as e:
                    print(f"DEBUG: page.open failed: {e}")

            # 2. 구버전 Flet 방식 (pick_date/pick_time)
            try:
                if isinstance(picker, ft.DatePicker) and hasattr(picker, "pick_date"):
                    picker.pick_date()
                    return
                elif isinstance(picker, ft.TimePicker) and hasattr(picker, "pick_time"):
                    picker.pick_time()
                    return
            except Exception as e:
                print(f"DEBUG: pick_date/time failed: {e}")

            # 3. 강제 방식 (open 속성 직접 변경)
            try:
                picker.open = True
                picker.update()
                print("DEBUG: Force open=True executed")
            except Exception as e:
                print(f"DEBUG: Force open failed: {e}")
                show_snack(f"기능을 열 수 없습니다. 오류: {e}", COLOR_ACCENT)

        date_btn.on_click = lambda _: open_picker_safe(date_picker)
        time_btn.on_click = lambda _: open_picker_safe(time_picker)
        is_scheduled.on_change = lambda _: update_schedule_ui()

        # 5. 공지 로그
        log_col = ft.Column(spacing=6)

        def refresh_notice_log():
            try:
                # load_notices가 없으면 에러가 날 수 있음 (import 확인 필요)
                all_notices = load_notices()
                my_notices = sorted(all_notices, key=lambda x: x["created_at"], reverse=True)[:5]
                
                items = []
                for n in my_notices:
                    t_str = n["created_at"][:16].replace("T", " ")
                    sch = n.get("scheduled_at", "")
                    now_iso = datetime.now().isoformat()
                    status_text = "예약중" if sch > now_iso else "발송됨"
                    status_color = COLOR_ACCENT if status_text == "예약중" else COLOR_PRIMARY
                    
                    items.append(
                        ft.Container(
                            padding=10, bgcolor="#f8f9fa", border_radius=8,
                            content=ft.Row([
                                ft.Column([ft.Text(f"[{status_text}] {n['title']}", size=12, weight="bold", color=status_color), ft.Text(f"작성: {t_str}", size=10, color="#95a5a6")], expand=True),
                                ft.Text(f"읽음 {len(n.get('read_by',[]))}", size=10, color=COLOR_PRIMARY)
                            ])
                        )
                    )
                log_col.controls = items if items else [ft.Text("발송 이력이 없습니다.", size=11, color="#95a5a6")]
                if page: page.update()
            except Exception as e:
                print(f"DEBUG: Log refresh failed: {e}")

        # 6. 공지 보내기 버튼 동작
        def send_notice_action(e):
            print("DEBUG: Send button clicked") # 클릭 확인용
            
            # 입력값 검증
            if not notice_title.value or not notice_content.value:
                show_snack("제목과 내용을 모두 입력해주세요.", COLOR_ACCENT)
                return
            
            # 예약값 검증
            scheduled_at_iso = None
            if is_scheduled.value:
                if not selected_dt["date"] or not selected_dt["time"]:
                    show_snack("예약 날짜와 시간을 선택해주세요.", COLOR_ACCENT)
                    return
                dt = datetime.combine(selected_dt["date"], selected_dt["time"])
                scheduled_at_iso = dt.isoformat()
            
            # 저장 및 초기화
            try:
                add_notice(notice_title.value, notice_content.value, u.get("id"), scheduled_at_iso)
                show_snack("공지가 등록되었습니다.", COLOR_PRIMARY)
                
                notice_title.value = ""
                notice_content.value = ""
                is_scheduled.value = False
                selected_dt["date"] = None
                selected_dt["time"] = None
                update_schedule_ui()
                refresh_notice_log()
            except Exception as err:
                print(f"DEBUG: Save failed: {err}")
                show_snack(f"저장 실패: {err}", COLOR_ACCENT)

        refresh_notice_log()

        # 7. 화면 구성
        main_content = ft.Column(
            scroll="auto", expand=True,
            controls=[
                ft.Row([
                    ft.Container(expand=True, bgcolor=COLOR_PRIMARY, padding=16, border_radius=18, content=ft.Column([ft.Text("학생 수", color="white", size=11), ft.Text(str(len(rows)), size=22, weight="bold", color="white")], spacing=2)),
                    ft.Container(expand=True, bgcolor="#f8f9fa", padding=16, border_radius=18, border=ft.border.all(1, "#eef1f4"), content=ft.Column([ft.Text("관리 지표", color=COLOR_TEXT_DESC, size=11), ft.Text("진도/평균/오답", size=16, weight="bold", color=COLOR_TEXT_MAIN)], spacing=2))
                ], spacing=10),
                ft.Container(height=20),
                ft.Text("학생 목록", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=8),
                ft.Column(student_cards, spacing=10),
                ft.Container(height=30),
                ft.Divider(height=1, color="#eef1f4"),
                ft.Container(height=20),
                ft.Text("공지사항 발송", size=16, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=10),
                ft.Container(
                    bgcolor="white", padding=16, border_radius=16, border=ft.border.all(1, "#eef1f4"),
                    content=ft.Column([
                        notice_title, notice_content,
                        ft.Row([is_scheduled, schedule_info], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([date_btn, time_btn], spacing=10),
                        ft.Container(height=10),
                        ft.ElevatedButton("공지 보내기", on_click=send_notice_action, width=320, bgcolor=COLOR_PRIMARY, color="white")
                    ])
                ),
                ft.Container(height=20),
                ft.Text("최근 발송 이력", size=14, weight="bold", color=COLOR_TEXT_MAIN),
                ft.Container(height=8),
                log_col,
                ft.Container(height=40),
            ]
        )

        return mobile_shell(
            "/teacher_dash", 
            ft.Container(padding=20, content=main_content, expand=True),
            title="선생님 대시보드", 
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: do_logout()), 
            actions=[ft.IconButton(icon=ft.icons.LOGOUT, on_click=lambda _: do_logout())]
        )
    
    def view_teacher_student():
        me = session.get("user")
        if not me or me.get("role") not in ("teacher", "admin"): return mobile_shell("/teacher_student", ft.Text("접근 권한이 없습니다."), title="학생 상세")
        uid = session.get("selected_student_id")
        u = ensure_progress(get_user(uid)) if uid else None
        if not u: return mobile_shell("/teacher_student", ft.Text("학생 정보를 찾을 수 없습니다."), title="학생 상세")

        topics = u["progress"]["topics"]
        last = u["progress"].get("last_session", {"topic": "", "idx": 0})
        topic_cards = []
        for tp in sorted(VOCAB_DB.keys()):
            tpdata = topics.get(tp, {})
            studied, avg, wcnt = len(tpdata.get("learned", {})), tpdata.get("stats", {}).get("avg_score", 0.0), len(tpdata.get("wrong_notes", []))
            topic_cards.append(ft.Container(bgcolor="white", border_radius=16, padding=12, border=ft.border.all(1, "#eef1f4"), content=ft.Row([ft.Column([ft.Text(tp, weight="bold", color=COLOR_TEXT_MAIN), ft.Text(f"누적 {studied} · 평균 {avg} · 오답 {wcnt}", size=11, color=COLOR_TEXT_DESC)], expand=True, spacing=2)])))

        def reset_pw():
            users2 = load_users()
            if uid in users2:
                users2[uid]["pw"] = hash_password("1111")
                save_users(users2)
                show_snack("비밀번호를 1111로 초기화했습니다.", COLOR_PRIMARY)

        body = ft.Container(padding=20, content=ft.Column([ft.Container(bgcolor="#f8f9fa", border_radius=18, padding=16, border=ft.border.all(1, "#eef1f4"), content=ft.Column([ft.Text(f"{u.get('name', uid)} ({uid})", size=18, weight="bold", color=COLOR_TEXT_MAIN), ft.Text(f"국적: {country_label(u.get('country','KR'))}", size=12, color=COLOR_TEXT_DESC), ft.Text(f"누적 학습: {sum(len(t.get('learned', {})) for t in topics.values())} · 오답: {sum(len(t.get('wrong_notes', [])) for t in topics.values())}", size=12, color=COLOR_TEXT_DESC), ft.Text(f"마지막 학습: {last.get('topic','')} / idx {int(last.get('idx',0))+1}", size=12, color=COLOR_TEXT_DESC), ft.Container(height=10), ft.Row([ft.ElevatedButton("비밀번호 초기화(1111)", on_click=lambda e: reset_pw(), bgcolor=COLOR_ACCENT, color="white", expand=True), ft.OutlinedButton("목록", on_click=lambda e: go_to("/teacher_dash"), expand=True)], spacing=10)], spacing=4)), ft.Container(height=12), ft.Text("토픽별 현황", weight="bold", color=COLOR_TEXT_MAIN), ft.Container(height=8), ft.Column(topic_cards, spacing=10, scroll="auto")], scroll="auto"))
        return mobile_shell("/teacher_student", body, title="학생 상세", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: go_to("/teacher_dash")))
    
    # =============================================================================
    # [추가] 학생용 공지사항 수신함 뷰
    # =============================================================================
    def view_notice_inbox():
        u_session = session.get("user")
        if not u_session: return mobile_shell("/notice_inbox", ft.Text("로그인이 필요합니다."), title="공지사항")
        
        uid = u_session.get("id") or u_session.get("uid")
        notices = get_active_notices(uid)
        
        notice_list = ft.Column(spacing=10, scroll="auto", expand=True)
        
        if not notices:
            notice_list.controls = [
                ft.Container(
                    padding=40, alignment=ft.Alignment(0, 0),
                    content=ft.Column([
                        ft.Icon(ft.icons.MAIL_OUTLINE, size=40, color="#bdc3c7"),
                        ft.Text("도착한 공지사항이 없습니다.", color="#95a5a6")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ]
        else:
            for n in notices:
                is_read = uid in n.get("read_by", [])
                card_bg = "white" if is_read else "#eef5ff"
                icon_color = "#bdc3c7" if is_read else COLOR_PRIMARY
                
                # [수정] 클릭 시 세션에 ID 저장 후 상세 페이지로 이동
                def on_click_notice(e, nid=n["id"]):
                    session["selected_notice_id"] = nid
                    go_to("/notice_detail")

                notice_list.controls.append(
                    ft.Container(
                        bgcolor=card_bg, border_radius=12, padding=14,
                        border=ft.border.all(1, "#eef1f4"),
                        ink=True,  # [추가] 클릭 시 물결 효과 (터치감 향상)
                        on_click=on_click_notice,
                        content=ft.Row([
                            ft.Icon(ft.icons.MARK_EMAIL_UNREAD if not is_read else ft.icons.MAIL_OUTLINE, color=icon_color),
                            ft.Column([
                                ft.Text(n.get("title", ""), weight="bold", color=COLOR_TEXT_MAIN),
                                ft.Text(n.get("created_at", "")[:16].replace("T", " "), size=11, color=COLOR_TEXT_DESC)
                            ], expand=True, spacing=2),
                            ft.Icon(ft.icons.CHEVRON_RIGHT, size=16, color="#bdc3c7")
                        ])
                    )
                )

        body = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("받은 메시지함", size=18, weight="bold"),
                ft.Container(height=10),
                notice_list
            ])
        )
        return mobile_shell("/notice_inbox", ft.Container(expand=True, content=body), title="공지사항", leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: go_home()))

    def view_notice_detail():
        u_session = session.get("user")
        if not u_session: return mobile_shell("/notice_detail", ft.Text("로그인이 필요합니다."), title="공지 상세")
        
        nid = session.get("selected_notice_id")
        if not nid: return mobile_shell("/notice_detail", ft.Text("공지 정보를 찾을 수 없습니다."), title="오류")
        
        notices = load_notices()
        target = next((n for n in notices if n["id"] == nid), None)
        
        if not target:
             return mobile_shell("/notice_detail", ft.Text("삭제되었거나 존재하지 않는 공지입니다."), title="오류", leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: go_to("/notice_inbox")))
        
        uid = u_session.get("id") or u_session.get("uid")
        mark_notice_read(nid, uid)
        
        body = ft.Container(
            padding=24,
            content=ft.Column([
                # 제목
                ft.Text(target.get("title", ""), size=20, weight="bold", color=COLOR_TEXT_MAIN),
                
                ft.Container(height=8),
                
                # 작성 시간
                ft.Row([
                    ft.Icon(ft.icons.ACCESS_TIME, size=14, color=COLOR_TEXT_DESC),
                    ft.Text(f"보낸 시간: {target.get('created_at', '')[:16].replace('T', ' ')}", size=12, color=COLOR_TEXT_DESC)
                ], spacing=4),
                
                ft.Divider(height=30, color="#eef1f4"),
                
                # [수정] 본문 내용 (height 속성 제거)
                ft.Container(
                    content=ft.Text(
                        target.get("content", ""), 
                        size=15, 
                        color=COLOR_TEXT_MAIN,
                        # height=1.6 제거 (이것 때문에 텍스트가 안 보였습니다)
                    ),
                    expand=True, 
                )
            ], scroll="auto")
        )
        
        return mobile_shell("/notice_detail", ft.Container(expand=True, content=body), title="공지 상세", leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: go_to("/notice_inbox")))
    
    def view_system_dash():
        u = session.get("user")
        if not u or u.get("role") != "admin": return mobile_shell("/system_dash", ft.Text("접근 권한이 없습니다."), title="시스템 대시보드")
        sysdata_local = load_system()
        default_goal_field = ft.TextField(label="기본 목표량", value=str(sysdata_local.get("default_goal", 10)), width=320)
        review_thr_field = ft.TextField(label="복습 기준", value=str(sysdata_local.get("review_threshold", 85)), width=320)
        api_key_field = ft.TextField(label="API Key", value=str(sysdata_local.get("api", {}).get("openai_api_key", "")), width=320, password=True, can_reveal_password=True)
        stt_provider_field = ft.Dropdown(label="STT", width=320, value=str(sysdata_local.get("api", {}).get("stt_provider", "none")), options=[ft.dropdown.Option("none"), ft.dropdown.Option("openai"), ft.dropdown.Option("google")])
        log_box = ft.TextField(label="로그", value="", multiline=True, read_only=True, min_lines=5, max_lines=10, width=320)
        approval_list_col = ft.Column(spacing=10)

        def load_pending_teachers():
            pending_rows = []
            for uid, u in load_users().items():
                if u.get("role") == "teacher" and not u.get("is_approved", False):
                    pending_rows.append(ft.Container(bgcolor="white", padding=12, border_radius=12, border=ft.border.all(1, "#eef1f4"), content=ft.Row([ft.Column([ft.Text(f"{u.get('name')} ({uid})", weight="bold"), ft.Text(f"ID: {uid} | 국적: {u.get('country')}", size=11, color=COLOR_TEXT_DESC)], expand=True), ft.ElevatedButton("승인", bgcolor=COLOR_PRIMARY, color="white", on_click=lambda e, t=uid: (update_user_approval(t, True), show_snack(f"{t} 승인됨", COLOR_PRIMARY), load_pending_teachers()))])))
            approval_list_col.controls = pending_rows if pending_rows else [ft.Text("대기 중인 선생님 없음", size=12, color=COLOR_TEXT_DESC)]
            if page: page.update()

        load_pending_teachers()
        
        def save_admin_settings(e):
            sysdata_local.update({"default_goal": int(default_goal_field.value), "review_threshold": int(review_thr_field.value), "api": {"openai_api_key": api_key_field.value, "stt_provider": stt_provider_field.value}})
            save_system(sysdata_local)
            session["goal"] = int(default_goal_field.value)
            show_snack("저장되었습니다.", COLOR_PRIMARY)

        def refresh_log(e=None):
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8") as f: log_box.value = "".join(f.readlines()[-50:])
            page.update()

        refresh_log()

        body = ft.Container(padding=20, content=ft.Column([ft.Text("시스템 설정", size=16, weight="bold"), ft.Container(height=10), default_goal_field, review_thr_field, stt_provider_field, api_key_field, ft.ElevatedButton("저장", on_click=save_admin_settings, width=320), ft.Container(height=20), ft.Text("선생님 승인 관리", size=16, weight="bold"), ft.Container(height=8), approval_list_col, ft.Container(height=20), ft.Text("로그", size=16, weight="bold"), ft.ElevatedButton("새로고침", on_click=refresh_log), log_box], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"))
        return mobile_shell("/system_dash", body, title="시스템 대시보드", leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: do_logout()), actions=[ft.IconButton(icon=ft.icons.LOGOUT, on_click=lambda _: do_logout())])

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        r_full = page.route
        r = (r_full or "").split("?", 1)[0]
        
        # 쿼리 파라미터 파싱
        qi = None
        try:
            if "?" in r_full:
                q = r_full.split("?", 1)[1]
                for part in q.split("&"):
                    if part.startswith("i="):
                        qi = part.split("=")[1]
        except: pass

        if r == "/": page.views.append(view_landing())
        elif r == "/login": page.views.append(view_login())
        elif r == "/signup": page.views.append(view_signup())
        elif r == "/student_home": page.views.append(view_student_home())
        elif r == "/level_select": page.views.append(view_level_select())
        elif r == "/settings": page.views.append(view_settings())
        elif r == "/stats": page.views.append(view_stats())
        elif r == "/profile": page.views.append(view_profile())
        elif r == "/study": page.views.append(view_study())
        elif r == "/motivate": page.views.append(view_motivate())
        elif r == "/pron_result": page.views.append(view_pron_result())
        
        # [추가된 부분] 복습 안내 화면 라우팅
        elif r == "/review_intro": page.views.append(view_review_intro())
        
        elif r == "/review_start": page.views.append(view_review_start())
        elif r == "/test_intro": page.views.append(view_test_intro())
        elif r == "/test":
            if qi: 
                try: session["test_idx"] = max(0, int(qi))
                except: pass
            page.views.append(view_test())
        elif r == "/study_complete": page.views.append(view_study_complete())
        elif r == "/cumulative": page.views.append(view_cumulative())
        elif r == "/wrong_notes": page.views.append(view_wrong_notes())
        elif r == "/review": page.views.append(view_review())
        elif r == "/notice_inbox": page.views.append(view_notice_inbox())
        elif r == "/notice_detail": page.views.append(view_notice_detail())
        elif r in ("/teacher_dash", "/teacher_dashboard"): page.views.append(view_teacher_dash())
        elif r == "/teacher_student": page.views.append(view_teacher_student())
        elif r in ("/system_dash", "/admin_dash", "/system_dashboard"): page.views.append(view_system_dash())
        else: page.views.append(view_login())
        
        page.update()
    
    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/login")