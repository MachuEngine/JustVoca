# JustVoca

외국인 학습자를 위한 **AI 기반 한국어 발음 교정 및 단어 학습 플랫폼**입니다. 
사용자의 음성을 녹음하여 특허받은 발음 평가 엔진(SpeechPro)으로 정밀 진단하며, 학습 → 복습 → 퀴즈로 이어지는 체계적인 파이프라인과 직관적인 통계 대시보드를 제공합니다.

---

## 기술 스택 (Tech Stack)

### Frontend
* **Framework:** Next.js 14 (App Router)
* **Language:** TypeScript
* **Styling:** Tailwind CSS
* **Animation:** Framer Motion (3D 카드 플립 등)
* **i18n:** i18next (5개 국어 다국어 지원)
* **HTTP Client:** Axios

### Backend
* **Framework:** FastAPI (Python 3.12 권장)
* **ORM & Database:** SQLModel (SQLite)
* **Data Processing:** Pandas, openpyxl (단어장 엑셀 파싱)
* **Audio Processing:** FFmpeg (16kHz Mono WAV 변환)
* **AI & External:** SpeechPro (발음 평가 엔진), OpenAI API (챗봇 Justy)

---

## 프로젝트 구조 (Project Structure)
```text
JustVoca_Project/
├── frontend/             # Next.js 프론트엔드 폴더
│   ├── app/              # App 라우터 및 페이지
│   ├── src/components/   # 공통 컴포넌트
│   └── package.json      # 프론트엔드 의존성
└── backend/              # FastAPI 백엔드 폴더
    ├── api/              # 라우터 엔드포인트
    ├── core/             # DB, 설정, SpeechPro 엔진 연동 로직
    ├── data/             # vocabulary.xlsx 및 JSON 리소스 데이터
    └── requirements.txt  # 파이썬 의존성
```

---

## 로컬 개발 환경 세팅 (Getting Started)

### 0. 사전 요구 사항 (Prerequisites)
* **Node.js** (v18.17 이상 권장)
* **Python** (v3.10 이상 권장)
* **FFmpeg**: 사용자 음성 파일 변환을 위해 시스템에 반드시 설치되어 있어야 합니다.
  * Mac: `brew install ffmpeg`
  * Ubuntu: `sudo apt-get install ffmpeg`
  * Windows: FFmpeg 공식 홈페이지에서 다운로드 후 환경 변수(PATH)에 추가

### 1. Backend 환경 세팅
파이썬 가상환경(venv) 생성을 권장합니다.

```bash
# 백엔드 폴더로 이동
cd backend

# 패키지 설치
pip install -r requirements.txt

# FastAPI 서버 실행 (기본 포트: 8000)
uvicorn app.main:app --reload
```

### 2. Frontend 환경 세팅

```bash
# 프론트엔드 폴더로 이동
cd frontend

# 패키지 설치
npm install

# Next.js 개발 서버 실행 (기본 포트: 3000)
npm run dev
```
이제 브라우저에서 `http://localhost:3000`으로 접속하여 화면을 확인할 수 있습니다.

---

## 환경 변수
(./backend/.env)

```env
# OpenAI API Key (챗봇 Justy 및 문장 교정용)
OPENAI_API_KEY="sk-openai-api-key-here"
```