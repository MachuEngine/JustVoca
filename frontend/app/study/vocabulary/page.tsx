"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Volume2,
  Mic,
  Square,
  BarChart,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Star,
  ArrowRight,
  X,
  Loader2,
  CheckCircle,
  Play,
} from "lucide-react";
import {
  uploadRecord,
  getWords,
  getReviewWords,
  getQuiz,
  completeStudy,
} from "../../api";
import AuthGuard from "../../components/AuthGuard";
import StudyCard from "../../components/StudyCard";
import confetti from "canvas-confetti";

const THEME_COLORS = {
  bg: "#F0F2F5",           // 전체 배경
  cardBg: "#FFFFFF",       // 카드 배경
  primary: "#20385F",      // ★ 메인 컬러 (네이비)
  secondary: "#E8EBF5",    // 보조 컬러 (연한 네이비)
  textMain: "#1A1A1A",     // 기본 검정 텍스트
  textSub: "#8F9BB3",      // 회색 텍스트
  accent: "#FFB02E",       // 강조(노랑)
  success: "#00C48C",      // 성공(초록)
};

export default function VocabularyStudyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const level = searchParams.get("level") || "초급1";
  const mode = searchParams.get("mode"); // 추가
  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("userId") || "student"
      : "student";

const getImageUrl = (path: string) => {
  if (!path) return "";
  return path; 
};

  // --- 상태 관리 ---
  const [phase, setPhase] = useState<
    "learning" | "review_intro" | "review" | "quiz_intro" | "quiz" | "complete"
  >("learning");

  const [isFlipped, setIsFlipped] = useState(false);
  const [recordingStatus, setRecordingStatus] = useState<
    "idle" | "recording" | "done"
  >("idle");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  const [wordData, setWordData] = useState<any[]>([]);
  const [reviewData, setReviewData] = useState<any[]>([]);
  const [quizData, setQuizData] = useState<any[]>([]);

  const [showEncouragement, setShowEncouragement] = useState(false);

  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isQuizCorrect, setIsQuizCorrect] = useState<boolean | null>(null);

  const [showResultOverlay, setShowResultOverlay] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [expandedWordIndex, setExpandedWordIndex] = useState<number | null>(
    null
  );
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [overallScore, setOverallScore] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [recordBlob, setRecordBlob] = useState<Blob | null>(null);

  const [imageError, setImageError] = useState(false); // 이미지 에러 상태

  const [isGraduated, setIsGraduated] = useState(false); // [추가] 졸업 여부 상태

  // --- 레벨 폴더 매핑 (로컬 오디오 경로 안정화) ---
  const levelDirMap: Record<string, string> = {
    초급1: "level1",
    초급2: "level2",
    중급1: "level3",
    중급2: "level4",
    고급: "level5",
  };
  const levelDir = levelDirMap[level] ?? "level1";

  // 백엔드 주소 (환경 변수로 관리하면 더 좋습니다)
  const API_BASE_URL = "http://localhost:8000"; // 또는 http://127.0.0.1:8000

  // --- 초기 데이터 로드 ---
  useEffect(() => {
    async function fetchInitialData() {
      try {
        setLoading(true);

        if (mode === "review") {
          // [전체 복습 모드] 통계 화면에서 온 경우
          const reviews = await getReviewWords(userId);
          const mapped = mapWordData(reviews);
          setReviewData(mapped);
          setPhase("review"); // 바로 복습 단계로 시작
          setCurrentIndex(0);
        } else {
          // [일반 학습 모드]
          const words = await getWords(level, userId);
          const mappedWords = mapWordData(words);
          setWordData(mappedWords);
        }

        // 퀴즈는 공통으로 로드
        try {
          const quizzes = await getQuiz(level);
          if (quizzes && quizzes.length > 0) setQuizData(quizzes);
        } catch (e) {
          console.error("퀴즈 로드 실패", e);
        }
      } catch (error) {
        console.error("데이터 로드 실패:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchInitialData();
  }, [level, userId, mode]); // mode를 의존성 배열에 추가

  // --- [추가] 화면 이탈 시 마이크 자동 종료 로직 ---
  useEffect(() => {
    return () => {
      // 1. 녹음 중이면 중단
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      
      // 2. 마이크 스트림 트랙들을 모두 종료 (브라우저 마이크 아이콘 제거)
      if (mediaRecorderRef.current && mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach((track) => {
          track.stop();
          console.log("마이크 트랙이 종료되었습니다.");
        });
      }
    };
  }, []);

const mapWordData = (list: any[]) => {
  if (!list || list.length === 0) return [];
  return list.map((w: any) => ({
    id: w.id,
    word: w.word,
    pronunciation: w.pronunciation || "",
    meaning: w.meaning,
    meaningEng: w.eng_meaning,
    example: w.example,
    audioKey: w.audio_path || "",               // 단어 오디오 경로
    audioExamplePath: w.audio_example_path || "", // 예문 오디오 경로 (새로 추가)
    imageKey: w.image_path || "",
  }));
};

  const currentList = phase === "review" ? reviewData : wordData;
  const currentWord = currentList[currentIndex];
  const currentQuiz = quizData[currentIndex];

  let totalSteps = wordData.length;
  if (phase === "review" || phase === "review_intro")
    totalSteps = reviewData.length;
  else if (phase === "quiz" || phase === "quiz_intro")
    totalSteps = quizData.length;

  // --- 상태 리셋 ---
  const resetCardState = () => {
    setIsFlipped(false);
    setImageError(false);
    setRecordingStatus("idle");
    setRecordBlob(null);
    setEvaluationResult(null);
    setShowResultOverlay(false);
    setExpandedWordIndex(null);
    setIsProcessing(false);
  };

  function parseLevelDirFromAudioKey(
    audioKey: string,
    fallbackLevelDir: string
  ) {
    const m = String(audioKey).match(/level\s*(\d+)/i);
    if (m && m[1]) return `level${m[1]}`;
    return fallbackLevelDir;
  }

function buildAudioPath(params: {
  audioKey: string;
}) {
  const { audioKey } = params;

  if (!audioKey) return "";

  // 백엔드에서 이미 /assets/... 로 시작하는 완성된 경로를 보내주므로
  // 별도의 조립 없이 그대로 반환합니다.
  if (audioKey.startsWith("/") || audioKey.startsWith("http")) {
    return audioKey;
  }

  // 혹시라도 순수 파일명만 올 경우를 대비한 안전장치 (필요 시 유지)
  return `/assets/audio/voca/${audioKey}.wav`;
}

  // --- 기능 함수 ---
const playLocalAudio = (type: "voca" | "example", e: React.MouseEvent) => {
  e.stopPropagation();
  if (!currentWord) return;

  // 1. 백엔드에서 준 경로 선택 (voca 또는 example)
  // [주의] 백엔드에서 audio_example_path를 추가했다면 해당 필드를 사용하세요.
  const audioPath = type === "voca" 
    ? currentWord.audioKey 
    : (currentWord.audioExamplePath || currentWord.audioKey);

  if (!audioPath) {
    console.warn(`${type} 오디오 경로가 없습니다.`);
    return;
  }

  // 2. 이미 완성된 경로(/assets/...)를 바로 사용
  const audio = new Audio(audioPath);
  audio.play().catch((err) => console.error("재생 실패:", audioPath, err));
};

const goToReview = () => {
  setPhase("review");
  setCurrentIndex(0);
};

const goToQuiz = () => {
  setPhase("quiz");
  setCurrentIndex(0);
  setSelectedOption(null);
  setIsQuizCorrect(null);
};

  const handleNext = async () => {
    if (phase === "learning") {
      // 중간 응원 메시지 로직 (생략 가능)
      if (currentIndex === 4 && !showEncouragement) {
        setShowEncouragement(true);
        resetCardState();
        return;
      }

      if (currentIndex < wordData.length - 1) {
        setCurrentIndex((prev) => prev + 1);
      } else {
        // 🟢 [수정 위치] 10개 학습이 끝났을 때
        // 현재 학습한 10개 단어를 복습 데이터로 복제합니다.

        // 🟢 [수정] 10개 학습 완료 시 점수가 70점 미만인 단어만 필터링
        const failedWords = wordData.filter(w => w.score !== undefined && w.score < 70);


        if (failedWords.length > 0) {
          setReviewData(failedWords);
          setPhase("review_intro");
          setCurrentIndex(0);
        } else {
          // 모든 단어가 70점 이상이면 복습을 건너뛰고 바로 퀴즈로 이동
          setPhase(quizData.length > 0 ? "quiz_intro" : "complete");
        }
      }
      resetCardState();
    } else if (phase === "review") {
      if (currentIndex < reviewData.length - 1) {
        setCurrentIndex((prev) => prev + 1);
      } else {
        if (quizData.length > 0) {
          setPhase("quiz_intro");
        } else {
          handleComplete();
        }
      }
      resetCardState();
    } else if (phase === "quiz") {
      if (currentIndex < quizData.length - 1) {
        setCurrentIndex((prev) => prev + 1);
        setSelectedOption(null);
        setIsQuizCorrect(null);
      } else {
        handleComplete();
      }
    }
  };

  const handleComplete = async () => {
    setPhase("complete");
    try {
      // API 호출
      const response: any = await completeStudy(level, userId);
      
      // [신규] 백엔드에서 졸업(마지막 페이지 완료) 신호를 줬는지 확인
      if (response && response.level_completed) {
        setIsGraduated(true);
        triggerConfetti(); // 폭죽 발사!
      } else {
        setIsGraduated(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // [신규] 폭죽 효과 함수
  const triggerConfetti = () => {
    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 999 };

    const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;

    const interval: any = setInterval(function () {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        return clearInterval(interval);
      }

      const particleCount = 50 * (timeLeft / duration);
      // 화면 양쪽에서 팡팡 터짐
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
    }, 250);
  };

  // --- 녹음 ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const preferredType = MediaRecorder.isTypeSupported(
        "audio/webm;codecs=opus"
      )
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "";

      mediaRecorderRef.current = preferredType
        ? new MediaRecorder(stream, { mimeType: preferredType })
        : new MediaRecorder(stream);

      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());

        if (chunksRef.current.length === 0) {
          alert("녹음된 데이터가 없습니다. 다시 시도해주세요.");
          setRecordingStatus("idle");
          return;
        }

        const mimeType =
          preferredType || mediaRecorderRef.current?.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: mimeType });

        // ✅ [추가] 너무 짧은 녹음 방지 (환경에 따라 숫자 조정)
        const MIN_SIZE = 12000; // webm/opus 기준 경험값. 너무 엄격하면 8000으로 낮춰도 됨.
        if (blob.size < MIN_SIZE) {
          alert("녹음이 너무 짧아요. 1초 이상 말해 주세요.");
          setRecordingStatus("idle");
          setRecordBlob(null);
          return;
        }
        setRecordBlob(blob);
        setRecordingStatus("done");
      };

      mediaRecorderRef.current.start();
      setRecordingStatus("recording");
    } catch (err) {
      alert("마이크 권한을 확인해주세요.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
  };

  // --- 결과 보기 ---
  const handleShowResult = async () => {
    if (!recordBlob || !currentWord) return;

    const targetText = currentWord.example || currentWord.word || "안녕하세요";

    setIsProcessing(true);
    try {
      const ext = recordBlob.type.includes("webm")
        ? "webm"
        : recordBlob.type.includes("ogg")
        ? "ogg"
        : recordBlob.type.includes("wav")
        ? "wav"
        : "webm";

      const file = new File([recordBlob], `record.${ext}`, {
        type: recordBlob.type,
      });

      console.log(
        "[UPLOAD] file.name=",
        file.name,
        "type=",
        file.type,
        "size=",
        file.size
      );

      const formData = new FormData();
      formData.append("audio", file);
      formData.append("text", targetText);
      formData.append("user_id", userId);
      formData.append("word", currentWord.word);

      console.log("[UPLOAD] fd audio =", formData.get("audio"));
      console.log("[UPLOAD] fd text  =", formData.get("text"));

      const response = await uploadRecord(formData);
      console.log("[UPLOAD] 6 response =", response);

      // 🟢 [수정 및 추가 부분 시작] ---------------------------------------------
      if (response?.success === false) {
        const errorMsg = String(response?.error || "");
        
        // 엔진 통신 장애(아무 말 안 함 등) 케이스 확인
        const isConnectionError = errorMsg.includes("Connection refused") || 
                                  errorMsg.includes("HTTPConnectionPool");

        if (isConnectionError) {
          // 시스템 에러가 아닌 친근한 안내로 대체
          alert("문장이 잘 들리지 않아요. 녹음 버튼을 눌러 다시 한번 읽어보세요.");
        } else {
          // 그 외 실제 분석 실패 메시지
          alert(response?.error || "분석이 어려워요. 문장을 다시 천천히 읽어보세요.");
        }

        // 상태 리셋 (버튼 활성화)
        setRecordingStatus("idle"); 
        setRecordBlob(null);
        setIsProcessing(false); 
        return;
      }
      // 🟢 [수정 및 추가 부분 끝] -----------------------------------------------

      console.log("[UPLOAD] response JSON =", JSON.stringify(response));

      const raw = response?.result ?? response ?? {};
      const candidate =
        raw && typeof raw === "object" && raw.result && typeof raw.result === "object"
          ? raw.result
          : raw;

      const resultData =
        candidate?.quality
          ? candidate
          : candidate?.score !== undefined
          ? candidate
          : candidate?.score_result
          ? candidate.score_result
          : candidate?.data
          ? candidate.data
          : candidate;

      console.log("[UPLOAD] raw =", raw);
      console.log("[UPLOAD] resultData(normalized) =", resultData);

      if (resultData) {
        setEvaluationResult(resultData);

        let finalScore = 0;

        if (typeof resultData.score === "number") {
          finalScore = resultData.score;
        } else if (resultData.quality?.score) {
          finalScore = resultData.quality.score;
        } else if (resultData.quality?.sentences) {
          const realSentence = resultData.quality.sentences.find(
            (s: any) => s.text && s.text !== "!SIL"
          );
          if (realSentence) {
            finalScore = realSentence.score;
          }
        }

        console.log("[DEBUG] 최종 결정된 점수:", finalScore);
        const roundedScore = Math.round(finalScore);
        setOverallScore(Math.round(finalScore));

        // 🟢 [추가] 현재 단어의 점수를 wordData 리스트에 기록합니다.
        setWordData(prev => prev.map((item, idx) => 
          idx === currentIndex ? { ...item, score: roundedScore } : item
        ));
        setShowResultOverlay(true);
      } else {
        console.error("서버 응답 데이터 구조 이상:", resultData);
        alert("평가 결과를 표시할 수 있는 데이터가 없습니다.");
        // 🟢 결과가 없을 때도 버튼 리셋 추가
        setRecordingStatus("idle");
        setRecordBlob(null);
      }
    } catch (error: any) {
      // 🟢 [수정] 네트워크 에러 등 발생 시 안내 문구 변경
      alert("소리가 인식되지 않았습니다. 녹음 버튼을 눌러 다시 읽어보세요.");
      setRecordingStatus("idle");
      setRecordBlob(null);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleQuizOption = (option: string) => {
    if (isQuizCorrect === true) return;
    setSelectedOption(option);
    const isCorrect = option === currentQuiz?.answer;
    setIsQuizCorrect(isCorrect);
  };

  // learning/review: 평가 결과 있어야 다음 가능(현재 로직 유지)
  // quiz: 정답이어야 다음 가능
  const isNextEnabled = () => {
    if (phase === "learning" || phase === "review") {
      return evaluationResult !== null;
    }
    if (phase === "quiz") return isQuizCorrect === true;
    return true;
  };

  // --- 렌더링 ---
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
        <Loader2 className="animate-spin text-[#FF8C1A] mb-4" size={40} />
        <p className="text-gray-500 font-bold">학습 데이터를 불러오는 중입니다...</p>
      </div>
    );
  }

  if (phase === "complete") {
    return (
      <AuthGuard allowedRoles={["student"]}>
        <div className="flex flex-col min-h-screen bg-white p-6 items-center justify-center text-center relative overflow-hidden">
          {/* 졸업 여부에 따라 다른 UI 표시 */}
          {isGraduated ? (
            // [졸업 축하 화면]
            <div className="animate-in zoom-in duration-700 flex flex-col items-center z-10">
              <div className="text-8xl mb-6 animate-bounce">🎓</div>
              <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 mb-4">
                축하합니다.
              </h1>
              <p className="text-xl text-gray-700 font-bold mb-8">
                <span className="text-blue-600">{level}</span> 레벨을<br />
                완벽하게 마스터하셨습니다.
              </p>
              <div className="bg-yellow-50 border-2 border-yellow-200 rounded-3xl p-6 mb-10 shadow-lg rotate-1 transform">
                <p className="text-sm font-bold text-yellow-700 uppercase tracking-widest mb-1">CERTIFICATE</p>
                <p className="text-gray-800 font-medium">
                   꾸준한 노력의 결실입니다.<br/>다음 레벨도 도전해보세요.
                </p>
              </div>
            </div>
          ) : (
            // ✅ [기존 일반 완료 화면]
            <div className="animate-in zoom-in duration-500 flex flex-col items-center z-10">
              <div className="w-24 h-24 bg-[#FF8C1A] rounded-full flex items-center justify-center mb-6">
                <CheckCircle className="w-12 h-12 text-white" />
              </div>
              <h2 className="text-3xl font-black text-gray-900 mb-2">학습 완료</h2>
              <p className="text-gray-500 mb-10">
                오늘도 목표를 달성하셨네요.
                <br />
                정말 고생 많으셨습니다.
              </p>
            </div>
          )}

          <button
            onClick={() => router.push("/student_home")}
            className={`w-full py-5 text-white rounded-2xl font-bold text-lg shadow-lg active:scale-95 transition-all z-20 ${
              isGraduated ? "bg-gradient-to-r from-[#20385F] to-purple-600 shadow-purple-200" : "bg-[#20385F]"
            }`}
          >
            홈으로 돌아가기
          </button>
          
          {/* 배경 장식 (졸업 시에만) */}
          {isGraduated && (
            <div className="absolute inset-0 bg-gradient-to-b from-blue-50/50 to-white pointer-events-none -z-0"></div>
          )}
        </div>
      </AuthGuard>
    );
  }

  if (phase === "review_intro") {
    return (
      <div
        className="flex flex-col min-h-screen items-center justify-center text-white animate-in fade-in"
        style={{ backgroundColor: THEME_COLORS.primary }}
        role="button"
        tabIndex={0}
        onClick={goToReview}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") goToReview();
        }}
      >
        <div className="text-6xl font-black mb-4 animate-bounce" style={{ color: THEME_COLORS.accent }}>
          ↺
        </div>
        <h2 className="text-3xl font-bold mb-2">복습을 시작합니다</h2>
        <p className="opacity-90">취약한 단어들을 다시 확인해보세요.</p>
        <p className="mt-8 text-sm font-black" style={{ color: THEME_COLORS.accent }}>
          화면을 터치하면 시작돼요
        </p>
      </div>
    );
  }

  if (phase === "quiz_intro") {
    return (
      <div
        className="flex flex-col min-h-screen items-center justify-center text-white p-6 animate-in fade-in"
        style={{ backgroundColor: THEME_COLORS.primary }}
        role="button"
        tabIndex={0}
        onClick={goToQuiz}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") goToQuiz();
        }}
      >
        <div className="w-24 h-24 rounded-full flex items-center justify-center mb-6"
            style={{ backgroundColor: `${THEME_COLORS.secondary}33` }}>
          <Star size={48} style={{ color: THEME_COLORS.accent }} />
        </div>
        <h2 className="text-3xl font-bold mb-4">연습 문제</h2>
        <p className="text-center opacity-90 mb-10 max-w-xs leading-relaxed">
          지금까지 배운 단어들을 문제를 풀며 확실하게 익혀보세요.
        </p>
        <p className="text-sm font-black" style={{ color: THEME_COLORS.accent }}>
          화면을 터치하면 시작돼요
        </p>
      </div>
    );
  }

  type PhoneItem = {
    symbol: string;
    score: number;
    text?: string;
  };

  function extractPhonesFromWord(wordObj: any): PhoneItem[] {
    const out: PhoneItem[] = [];
    const sylls = Array.isArray(wordObj?.syll) ? wordObj.syll : [];

    for (const s of sylls) {
      const phones = Array.isArray(s?.phones) ? s.phones : [];
      for (const p of phones) {
        if (!p?.symbol) continue;
        out.push({
          symbol: String(p.symbol),
          score: Math.round(Number(p.score ?? 0)),
          text: p.text ? String(p.text) : undefined,
        });
      }
    }
    return out;
  }

  const targetSentence = evaluationResult?.quality?.sentences?.find(
    (s: any) => s.text !== "!SIL"
  );
  const resultWords = (targetSentence?.words || []).filter(
    (w: any) => w?.text && w.text !== "!SIL"
  );

  return (
    <AuthGuard allowedRoles={["student"]}>
      <div
        className="relative flex flex-col h-[100dvh] px-0 pt-0 select-none overflow-hidden"
        style={{ backgroundColor: THEME_COLORS.bg }}
      >
        {showEncouragement && (
          <div
            className="absolute inset-0 z-[60] flex flex-col items-center justify-center backdrop-blur-sm text-white animate-in fade-in duration-300"
            style={{ backgroundColor: `${THEME_COLORS.primary}F2` }} // 약 95% 느낌
            role="button"
            tabIndex={0}
            onClick={() => {
              setShowEncouragement(false);
              setCurrentIndex((prev) => prev + 1);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                setShowEncouragement(false);
                setCurrentIndex((prev) => prev + 1);
              }
            }}
          >
            <div className="text-3xl font-black mb-2">절반이나 왔어요.</div>
            <p className="text-lg opacity-90">지금처럼만 하면 충분해요!</p>
            <p className="mt-6 text-sm font-black" style={{ color: THEME_COLORS.accent }}>
              화면을 터치하면 계속 진행돼요
            </p>
          </div>
        )}

        {/* 시안 진행바 */}
        <div className="px-4 mt-3 mb-3 flex items-center gap-3">
          <div className="flex-1 h-2 rounded-full bg-gray-200 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.round(((currentIndex + 1) / totalSteps) * 100)}%`,
                backgroundColor: THEME_COLORS.primary,
              }}
            />
          </div>
          <div className="text-xs font-bold text-gray-500">
            {currentIndex + 1}/{totalSteps}
          </div>
        </div>

        {/* --- [메인 콘텐츠 영역: 카드 + 버튼] --- */}
        {/* ✅ 카드 “더 크게”: max-w-md -> max-w-lg */}
        <div className="flex-1 min-h-0 w-full flex items-start justify-center px-4 pt-4 pb-[calc(env(safe-area-inset-bottom)+84px)]">
          <div className="w-full max-w-[340px]">
            <div className="w-full">
            {phase === "quiz" ? (
              <div className="w-full aspect-[3/4] bg-white rounded-[3.25rem] shadow-2xl border border-gray-100 p-7 flex flex-col items-center justify-center relative overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex-1 w-full flex flex-col justify-center">
                  <span className="text-center text-xs font-black text-blue-500 uppercase tracking-widest mb-4">
                    Quiz
                  </span>
                  <h3 className="text-xl font-black text-gray-900 text-center break-keep leading-relaxed mb-7">
                    "{currentQuiz?.question}"
                  </h3>
                  <div className="space-y-3 w-full">
                    {currentQuiz?.options?.map((option: string, idx: number) => {
                      let btnClass =
                        "w-full h-10 rounded-xl text-base font-bold border-2 transition-all shadow-sm ";

                      if (selectedOption === option) {
                        if (isQuizCorrect) {
                          btnClass += "bg-green-50 border-green-500 text-green-700";
                        } else {
                          btnClass += "bg-red-50 border-red-500 text-red-700";
                        }
                      } else {
                        btnClass +=
                          "bg-gray-50 border-transparent text-gray-600 hover:bg-white hover:border-blue-200";
                      }

                      return (
                        <button
                          key={idx}
                          onClick={() => handleQuizOption(option)}
                          className={btnClass}
                        >
                          {option}
                        </button>
                      );
                    })}
                  </div>
                  {selectedOption && isQuizCorrect === false && (
                    <p className="text-center text-red-500 font-bold mt-3 animate-pulse text-sm">
                      오답입니다. 다시 선택해보세요.
                    </p>
                  )}
                  {isQuizCorrect === true && (
                    <p className="text-center text-green-600 font-bold mt-3 animate-in zoom-in text-sm">
                      정답입니다.
                    </p>
                  )}

                {isQuizCorrect === true && (
                <button
                  onClick={handleNext}
                  className="mt-3 w-full h-12 rounded-xl font-black text-white shadow-lg active:scale-95 transition-all"
                  style={{ backgroundColor: THEME_COLORS.primary }}
                >
                  다음 문제
                </button>
              )}
                </div>
              </div>
            ) : (
              <div
                className="
                  relative w-full aspect-[4/6]
                  bg-white rounded-[28px]
                  shadow-[0_12px_28px_rgba(0,0,0,0.10)]
                  overflow-hidden
                "
                style={{ borderColor: THEME_COLORS.accent }}
                onClick={() => setIsFlipped((prev) => !prev)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") setIsFlipped((prev) => !prev);
                }}
              >
                {/* 회전 아이콘 */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsFlipped((prev) => !prev);
                  }}
                  className="absolute top-6 left-1/2 -translate-x-1/2 p-2 rounded-full hover:bg-gray-50 transition z-10"
                  style={{ color: THEME_COLORS.textSub }}
                  aria-label="flip"
                >
                  <RotateCcw size={18} />
                </button>

                {/* ✅ 고정 레이아웃 (사양서처럼) */}
                <div className="h-full px-6 pt-8 pb-6 flex flex-col">
                  {!isFlipped ? (
                    // =========================
                    // FRONT (단어/이미지)
                    // =========================
                    <>
                      <div className="flex items-center justify-center pt-2">
                        <div className="mt-10 w-[180px] h-[180px] flex items-center justify-center">
                          {currentWord?.imageKey && !imageError ? (
                            <img
                              src={getImageUrl(currentWord.imageKey)}
                              alt={currentWord.word}
                              className="w-full h-full object-contain"
                              onError={() => setImageError(true)}
                            />
                          ) : (
                            <div className="text-4xl opacity-10">🖼️</div>
                          )}
                        </div>
                      </div>

                      <div className="mt-2 text-center">
                        <div className="text-[34px] font-black text-gray-900 leading-tight">
                          {currentWord?.word}
                        </div>

                        {currentWord?.pronunciation && (
                          <div className="mt-1 text-[16px] font-bold text-orange-500">
                            [{currentWord.pronunciation}]
                          </div>
                        )}

                        <div className="mt-4 text-[13px] font-medium text-gray-700 leading-relaxed px-2">
                          {currentWord?.meaning}
                        </div>

                        {currentWord?.meaningEng && (
                          <div className="mt-2 text-[11px] text-gray-400 leading-relaxed px-2">
                            {currentWord.meaningEng}
                          </div>
                        )}
                      </div>

                      {/* ✅ 하단 고정 */}
                      <button
                        onClick={(e) => playLocalAudio("voca", e)}
                        className="mt-auto w-full h-12 rounded-xl font-black text-white flex items-center justify-center gap-2 transition-transform duration-100 active:scale-95 hover:brightness-110"
                        style={{ backgroundColor: THEME_COLORS.primary }}
                      >
                        <Volume2 size={20} />
                        발음 듣기
                      </button>
                    </>
                  ) : (
                    // =========================
                    // BACK (예문/녹음)
                    // =========================
                    <>
                      <div className="mt-10 text-center pt-3">
                        <div className="text-[34px] font-black text-gray-900">
                          {currentWord?.word}
                        </div>
                      </div>

                      <button
                        onClick={(e) => playLocalAudio("example", e)}
                        className="mt-14 flex items-center gap-2 text-orange-500 font-bold text-[13px] self-start transition-all duration-100 active:scale-95 hover:opacity-80 active:opacity-100"
                      >
                        <Volume2 size={16} />
                        예시 문장 듣기
                      </button>

                      {/* ✅ 예문 영역만 스크롤 */}
                      <div className="mt-2 text-[13px] text-gray-700 leading-relaxed overflow-auto flex-1 min-h-0 pr-1">
                        {currentWord?.example}
                      </div>

                      {/* ✅ 하단 액션 영역 고정 */}
                      <div className="mt-4 w-full" onClick={(e) => e.stopPropagation()}>
                        {recordingStatus === "idle" && (
                          <button
                            onClick={startRecording}
                            className="w-full h-12 rounded-xl font-black text-white flex items-center justify-center gap-2 transition-transform duration-100 active:scale-95 hover:brightness-110"
                            style={{ backgroundColor: THEME_COLORS.primary }}
                          >
                            <Mic size={18} />
                            문장 말하기
                          </button>
                        )}

                        {recordingStatus === "recording" && (
                          <button
                            onClick={stopRecording}
                            className="w-full h-12 rounded-xl font-black text-white flex items-center justify-center gap-2 bg-red-500 transition-transform duration-100 active:scale-95 hover:bg-red-600 shadow-md active:shadow-inner"
                          >
                            <Square size={18} fill="white" />
                            그만 말하기
                          </button>
                        )}

                        {recordingStatus === "done" && (
                          <button
                            onClick={handleShowResult}
                            disabled={isProcessing}
                            className="w-full h-12 rounded-xl font-black text-white flex items-center justify-center gap-2 transition-all duration-100 disabled:opacity-60 disabled:cursor-not-allowed enabled:active:scale-95 enabled:hover:brightness-110"
                            style={{ backgroundColor: THEME_COLORS.primary }}
                          >
                            {isProcessing ? <Loader2 className="animate-spin" size={18} /> : null}
                            {isProcessing ? "분석 중..." : "결과 보기"}
                          </button>
                        )}

                        <div className="mt-4 grid grid-cols-2 gap-3">
                          {/* 이전 버튼 */}
                          <button
                            disabled={currentIndex === 0}
                            onClick={() => {
                              setCurrentIndex((prev) => Math.max(0, prev - 1));
                              resetCardState();
                            }}
                            className="h-11 rounded-lg border border-gray-200 text-gray-600 font-bold transition-all duration-100 disabled:opacity-40 disabled:cursor-not-allowed enabled:hover:bg-gray-50 enabled:active:scale-95 enabled:active:bg-gray-100"
                          >
                            〈 이전
                          </button>

                          {/* 다음 버튼 */}
                          <button
                            onClick={handleNext}
                            disabled={!isNextEnabled()}
                            className="h-11 rounded-lg border border-gray-200 text-gray-600 font-bold transition-all duration-100 disabled:opacity-40 disabled:cursor-not-allowed enabled:hover:bg-gray-50 enabled:active:scale-95 enabled:active:bg-gray-100"
                          >
                            다음 〉
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
            </div>
          </div>
        </div>
        {/* 결과 상세 오버레이 */}
        {showResultOverlay && evaluationResult && (
          <div className="absolute inset-0 z-50 animate-in fade-in duration-300 overflow-hidden">
            {/* dim */}
            <div
              className="absolute inset-0 bg-gray-900/60 backdrop-blur-md"
              onClick={() => setShowResultOverlay(false)}
            />

            {/* ✅ 사양서 스타일: 한 화면에 모두 보이게(컴팩트) */}
            <div className="absolute inset-x-0 top-16 bottom-6 px-4 flex items-start justify-center">
              <div className="w-full max-w-[360px] bg-white rounded-[28px] shadow-2xl border border-gray-100 overflow-hidden flex flex-col">
                {/* Header */}
                <div className="px-5 pt-4 pb-3 flex items-center justify-between">
                  <div className="text-sm font-black text-gray-900">발음 녹음 결과</div>
                  <button
                    onClick={() => setShowResultOverlay(false)}
                    className="p-2 bg-gray-50 rounded-full text-gray-400 active:scale-90 transition-all"
                    aria-label="close"
                  >
                    <X size={18} />
                  </button>
                </div>

                {/* ✅ Total Score (컴팩트) */}
                <div className="px-5 pb-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full border-2 border-emerald-500 flex items-center justify-center">
                      <span className="text-base font-black text-emerald-600">
                        {overallScore}
                      </span>
                    </div>
                    <div className="leading-tight">
                      <div className="text-[11px] text-gray-400 font-bold">TOTAL SCORE</div>
                      <div className="text-sm font-black text-gray-900">발음 점수</div>
                    </div>
                  </div>
                </div>

                {/* ✅ 어절 리스트: 한 화면에 다 보이게 컴팩트(overflow 시에만 스크롤) */}
                <div className="px-5 pb-4 flex-1 min-h-0">
                  <div className="space-y-2 overflow-y-auto pr-1 max-h-full">
                    {resultWords.map((wordObj: any, idx: number) => {
                      const isExpanded = expandedWordIndex === idx;
                      const score = Math.round(wordObj.score);

                      let colorClass = "text-red-600 bg-red-50 border-red-100";
                      if (score >= 80) colorClass = "text-emerald-600 bg-emerald-50 border-emerald-100";
                      else if (score >= 60) colorClass = "text-orange-600 bg-orange-50 border-orange-100";

                      return (
                        <div
                          key={idx}
                          className="border border-gray-100 rounded-2xl overflow-hidden"
                        >
                          <button
                            type="button"
                            onClick={() => setExpandedWordIndex(isExpanded ? null : idx)}
                            className={`w-full px-4 py-3 flex items-center justify-between active:bg-gray-50 ${
                              isExpanded ? "bg-gray-50/60" : "bg-white"
                            }`}
                          >
                            <span className="text-sm font-black text-gray-900">
                              {wordObj.text}
                            </span>
                            <span className={`text-xs font-black px-2 py-1 rounded-full border ${colorClass}`}>
                              {score}점
                            </span>
                          </button>

                          {/* ✅ 음소별 점수: 클릭 시 유지 */}
                          {isExpanded && (
                            <div className="px-4 pb-3 pt-1 bg-gray-50/30">
                              <div className="flex flex-wrap gap-2 mt-2">
                                {extractPhonesFromWord(wordObj).map((ph, pIdx) => {
                                  const s = ph.score;
                                  const badge =
                                    s >= 80
                                      ? "text-emerald-600 bg-emerald-50 border-emerald-100"
                                      : s >= 60
                                      ? "text-orange-600 bg-orange-50 border-orange-100"
                                      : "text-red-600 bg-red-50 border-red-100";

                                  return (
                                    <div
                                      key={pIdx}
                                      className="flex items-center justify-between gap-2 bg-white border border-gray-100 rounded-xl px-3 py-2"
                                    >
                                      <span className="text-sm font-black text-gray-800">
                                        {ph.symbol}
                                      </span>
                                      <span className={`text-[11px] font-black px-2 py-1 rounded-full border ${badge}`}>
                                        {ph.score}점
                                      </span>
                                    </div>
                                  );
                                })}

                                {extractPhonesFromWord(wordObj).length === 0 && (
                                  <div className="text-xs text-gray-400 py-2">
                                    상세 음소 정보 없음
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* ✅ 하단 버튼: 다시 녹음 삭제 + 계속 학습하기 */}
                <div className="px-5 pb-5">
                  <button
                    onClick={() => {
                      setShowResultOverlay(false);
                      handleNext();
                    }}
                    className="w-full h-12 rounded-xl font-black text-white shadow-lg active:scale-95 transition-all"
                    style={{ backgroundColor: THEME_COLORS.primary }}
                  >
                    계속 학습하기
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
