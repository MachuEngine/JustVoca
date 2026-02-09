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
  
  // 이미 전체 주소(http)가 있으면 그대로 쓰고, 
  // 아니면 백엔드 주소 없이 경로(/assets/...)만 그대로 반환합니다.
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

  useEffect(() => {
    if (phase === "review_intro") {
      const timer = setTimeout(() => {
        setPhase("review");
        setCurrentIndex(0);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [phase]);

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

  const handleNext = async () => {
    if (phase === "learning") {
      // 중간 응원 메시지 로직 (생략 가능)
      if (currentIndex === 4 && !showEncouragement) {
        setShowEncouragement(true);
        setTimeout(() => {
          setShowEncouragement(false);
          setCurrentIndex((prev) => prev + 1);
        }, 1500);
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
          alert("문장이 잘 들리지 않아요. 녹음 버튼을 눌러 다시 한번 읽어보세요!");
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
        <Loader2 className="animate-spin text-green-500 mb-4" size={40} />
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
            // 🎉 [졸업 축하 화면]
            <div className="animate-in zoom-in duration-700 flex flex-col items-center z-10">
              <div className="text-8xl mb-6 animate-bounce">🎓</div>
              <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 mb-4">
                축하합니다!
              </h1>
              <p className="text-xl text-gray-700 font-bold mb-8">
                <span className="text-blue-600">{level}</span> 레벨을<br />
                완벽하게 마스터하셨습니다!
              </p>
              <div className="bg-yellow-50 border-2 border-yellow-200 rounded-3xl p-6 mb-10 shadow-lg rotate-1 transform">
                <p className="text-sm font-bold text-yellow-700 uppercase tracking-widest mb-1">CERTIFICATE</p>
                <p className="text-gray-800 font-medium">
                   꾸준한 노력의 결실입니다.<br/>다음 레벨도 도전해보세요! 🚀
                </p>
              </div>
            </div>
          ) : (
            // ✅ [기존 일반 완료 화면]
            <div className="animate-in zoom-in duration-500 flex flex-col items-center z-10">
              <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-6">
                <CheckCircle className="w-12 h-12 text-green-600" />
              </div>
              <h2 className="text-3xl font-black text-gray-900 mb-2">학습 완료!</h2>
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
              isGraduated ? "bg-gradient-to-r from-blue-500 to-purple-600 shadow-purple-200" : "bg-blue-500"
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
      <div className="flex flex-col min-h-screen bg-orange-500 items-center justify-center text-white animate-in fade-in">
        <div className="text-6xl font-black mb-4 animate-bounce">↺</div>
        <h2 className="text-3xl font-bold mb-2">복습을 시작합니다</h2>
        <p className="opacity-90">취약한 단어들을 다시 확인해보세요!</p>
        <div className="mt-8 flex gap-2">
          <span className="w-3 h-3 bg-white rounded-full animate-ping"></span>
          <span className="w-3 h-3 bg-white rounded-full animate-ping delay-100"></span>
          <span className="w-3 h-3 bg-white rounded-full animate-ping delay-200"></span>
        </div>
      </div>
    );
  }

  if (phase === "quiz_intro") {
    return (
      <div className="flex flex-col min-h-screen bg-blue-600 items-center justify-center text-white p-6 animate-in fade-in">
        <div className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center mb-6">
          <Star size={48} className="text-yellow-300 fill-yellow-300" />
        </div>
        <h2 className="text-3xl font-bold mb-4">연습 문제</h2>
        <p className="text-center opacity-90 mb-10 max-w-xs leading-relaxed">
          지금까지 배운 단어들을 문제를 풀며 확실하게 익혀보세요.
        </p>
        <button
          onClick={() => {
            setPhase("quiz");
            setCurrentIndex(0);
            setSelectedOption(null);
            setIsQuizCorrect(null);
          }}
          className="w-full max-w-xs py-5 bg-white text-blue-600 rounded-2xl font-black text-xl shadow-xl active:scale-95 transition-all flex items-center justify-center gap-2"
        >
          <Play size={24} fill="currentColor" /> 문제 풀기 시작
        </button>
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
      <div className="relative flex flex-col min-h-screen bg-gray-50 p-6 select-none overflow-hidden">
        {showEncouragement && (
          <div className="absolute inset-0 z-[60] flex flex-col items-center justify-center bg-blue-500/95 backdrop-blur-sm text-white animate-in fade-in duration-300">
            <div className="text-7xl mb-4 animate-bounce">🚀</div>
            <h2 className="text-3xl font-black mb-2">절반이나 왔어요!</h2>
            <p className="text-lg opacity-90">지금처럼만 하면 충분해요 👍</p>
          </div>
        )}

        {/* 상단바 */}
        <div className="flex justify-between items-end mb-6 px-1">
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <span className="text-[10px] font-black text-green-600 bg-green-50 px-2 py-1 rounded-md border border-green-100 uppercase">
                {level}
              </span>
              <span
                className={`text-[10px] font-black px-2 py-1 rounded-md border uppercase ${
                  phase.includes("review")
                    ? "text-orange-600 bg-orange-50 border-orange-100"
                    : "text-blue-600 bg-blue-50 border-blue-100"
                }`}
              >
                {phase.includes("learning")
                  ? "Learning"
                  : phase.includes("review")
                  ? "Review"
                  : "Quiz"}
              </span>
            </div>
            {phase !== "quiz" && (
              <div className="flex items-center gap-1.5">
                <div
                  className={`w-1.5 h-1.5 rounded-full ${
                    isFlipped ? "bg-blue-500" : "bg-green-500"
                  }`}
                ></div>
                <span className="text-[11px] font-black text-gray-500 uppercase tracking-widest">
                  {isFlipped ? "Practice Mode" : "Word Mode"}
                </span>
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="text-[10px] font-black text-gray-300 font-mono mb-1">
              {String(currentIndex + 1).padStart(2, "0")} / {totalSteps}
            </div>
            {phase !== "quiz" && (
              <button
                onClick={() => setIsFlipped(!isFlipped)}
                className="flex items-center gap-1 text-[10px] font-black text-gray-400 border border-gray-200 px-2 py-1 rounded-lg bg-white shadow-sm active:bg-gray-100"
              >
                <RotateCcw size={10} /> <span>회전</span>
              </button>
            )}
          </div>
        </div>

        {/* --- [메인 콘텐츠 영역: 카드 + 버튼] --- */}
        {/* ✅ 카드 “더 크게”: max-w-md -> max-w-lg */}
        <div className="flex-1 flex flex-col items-center justify-start w-full max-w-2xl mx-auto">
          {/* 1. 카드 영역 */}
          <div className="w-full mb-6">
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
                        "w-full py-4 rounded-xl text-base font-bold border-2 transition-all shadow-sm ";

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
                    <p className="text-center text-red-500 font-bold mt-4 animate-pulse text-sm">
                      오답입니다. 다시 선택해보세요!
                    </p>
                  )}
                  {isQuizCorrect === true && (
                    <p className="text-center text-green-600 font-bold mt-4 animate-in zoom-in text-sm">
                      정답입니다! 🎉
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div
                onClick={() => setIsFlipped((prev) => !prev)}
                // ✅ 더 커 보이게: aspect[3/4] + padding 축소(p-10->p-8)
                className="w-full aspect-[3/4] bg-white rounded-[3.25rem] shadow-2xl border border-gray-100 p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-500 relative overflow-hidden active:scale-[0.99]"
              >
                {!isFlipped ? (
                  <div className="flex flex-col items-center w-full animate-in fade-in duration-300">
                    {/* 이미지 영역 */}
                    <div className="flex-1 w-full flex items-center justify-center mb-2">
                      <div className="w-40 h-40 relative rounded-3xl overflow-hidden bg-gray-50 flex items-center justify-center shadow-inner border border-gray-100">
                        {currentWord?.imageKey && !imageError ? (
                          <img
                            key={currentWord.imageKey} // [중요] key 추가: URL이 바뀌면 이미지를 새로 그리기 위함
                            src={getImageUrl(currentWord.imageKey)}
                            alt={currentWord.word}
                            className="w-full h-full object-cover"
                            onError={() => setImageError(true)}
                          />
                        ) : (
                          <span className="text-6xl select-none opacity-20">📖</span>
                        )}
                      </div>
                    </div>

                    {/* ✅ 단어/발음 폰트 축소 */}
                    <div className="mb-5 w-full px-1">
                      <h2 className="text-2xl font-black text-gray-900 flex items-baseline justify-center gap-2 flex-wrap break-keep leading-tight">
                        {currentWord?.word}
                        {currentWord?.pronunciation && (
                          <span className="text-base font-medium text-gray-400 font-mono tracking-tight transform translate-y-[-2px]">
                            [{currentWord.pronunciation}]
                          </span>
                        )}
                      </h2>
                    </div>

                    {/* 뜻 영역 (폰트 축소) */}
                    <div className="w-full px-6 mb-7">
                      <div className="w-full bg-yellow-50 rounded-2xl p-1 border border-yellow-100 flex flex-col items-center shadow-sm">
                        <p className="text-gray-800 font-bold text-base leading-snug break-keep text-center">
                          {currentWord?.meaning}
                        </p>

                        {currentWord?.meaningEng && (
                          <div className="w-full h-px bg-yellow-200 my-3"></div>
                        )}

                        {currentWord?.meaningEng && (
                          <p className="text-gray-500 text-xs font-medium italic break-keep text-center">
                            {currentWord.meaningEng}
                          </p>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={(e) => playLocalAudio("voca", e)}
                      className={`flex items-center gap-3 px-10 py-5 text-white font-black rounded-2xl shadow-lg transition-all ${
                        !currentWord?.audioKey
                          ? "bg-gray-400 opacity-50"
                          : "bg-gray-900 active:scale-95"
                      }`}
                    >
                      <Volume2 size={22} /> <span className="text-sm">발음 듣기</span>
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center w-full animate-in fade-in duration-300">
                    <div className="w-full text-left mb-7 border-l-4 border-blue-500 pl-4">
                      <h4 className="text-xl font-black text-gray-900">
                        {currentWord?.word}
                      </h4>
                      <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1 opacity-60">
                        Speak Now
                      </p>
                    </div>

                    {/* ✅ 예문 폰트 축소 (text-2xl -> text-xl) */}
                    <h3 className="text-xl font-black text-gray-900 leading-snug mb-10 text-left w-full break-keep px-2">
                      {currentWord?.example}
                    </h3>

                    <div className="grid grid-cols-1 w-full gap-4 px-2">
                      <button
                        onClick={(e) => playLocalAudio("example", e)}
                        className={`w-full h-16 font-black rounded-2xl flex items-center justify-center gap-3 shadow-sm ${
                          !currentWord?.audioKey
                            ? "bg-gray-100 text-gray-400"
                            : "bg-blue-50 text-blue-600 active:bg-blue-100"
                        }`}
                      >
                        <Volume2 size={22} />
                        <span className="text-sm">문장 듣기</span>
                      </button>

                      <div onClick={(e) => e.stopPropagation()}>
                        {recordingStatus === "idle" && (
                          <button
                            onClick={startRecording}
                            className="w-full h-16 bg-gray-900 text-white font-black rounded-2xl flex items-center justify-center gap-3 shadow-lg active:scale-95 transition-all"
                          >
                            <Mic size={22} />
                            <span className="text-sm">문장 녹음</span>
                          </button>
                        )}
                        {recordingStatus === "recording" && (
                          <button
                            onClick={stopRecording}
                            className="w-full h-16 bg-red-500 text-white font-black rounded-2xl flex items-center justify-center gap-3 animate-pulse shadow-lg"
                          >
                            <Square size={22} fill="white" />
                            <span className="text-sm">중지</span>
                          </button>
                        )}
                        {recordingStatus === "done" && (
                          <button
                            onClick={handleShowResult}
                            disabled={isProcessing}
                            className={`w-full h-16 text-white font-black rounded-2xl flex items-center justify-center gap-3 shadow-xl active:scale-95 transition-all ${
                              evaluationResult ? "bg-blue-500" : "bg-green-600"
                            }`}
                          >
                            {isProcessing ? (
                              <Loader2 className="animate-spin" />
                            ) : (
                              <BarChart size={22} />
                            )}
                            <span className="text-sm">
                              {isProcessing
                                ? "분석 중..."
                                : evaluationResult
                                ? "결과 다시 보기"
                                : "결과 보기"}
                            </span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 2. 네비게이션 버튼 */}
          <div className="flex gap-4 w-full">
            <button
              disabled={currentIndex === 0}
              onClick={() => {
                setCurrentIndex((prev) => Math.max(0, prev - 1));
                resetCardState();
                if (phase === "quiz") {
                  setSelectedOption(null);
                  setIsQuizCorrect(null);
                }
              }}
              className="flex-1 h-16 bg-white border border-gray-100 rounded-3xl flex items-center justify-center gap-2 font-black text-gray-400 active:bg-gray-50 disabled:opacity-30 shadow-sm transition-all"
            >
              <ChevronLeft size={20} />
              <span>이전</span>
            </button>

            <button
              onClick={handleNext}
              disabled={!isNextEnabled()}
              className={`flex-1 h-16 border rounded-3xl flex items-center justify-center gap-2 font-black transition-all shadow-sm ${
                !isNextEnabled()
                  ? "bg-gray-100 text-gray-400 border-gray-100 cursor-not-allowed"
                  : phase === "quiz"
                  ? "bg-blue-500 text-white shadow-blue-200"
                  : "bg-white border-green-200 text-green-600 active:bg-green-50"
              }`}
            >
              <span>
                {phase === "quiz" && currentIndex >= quizData.length - 1
                  ? "결과 보기"
                  : "다음"}
              </span>
              <ChevronRight size={20} />
            </button>
          </div>
        </div>

        {/* 결과 상세 오버레이 */}
        {showResultOverlay && evaluationResult && (
          <div className="absolute inset-0 z-50 animate-in fade-in duration-300 overflow-hidden">
            <div
              className="absolute inset-0 bg-gray-900/60 backdrop-blur-md"
              onClick={() => setShowResultOverlay(false)}
            ></div>

            <div className="absolute inset-x-0 bottom-0 top-20 bg-white rounded-t-[3rem] shadow-2xl animate-in slide-in-from-bottom duration-500 ease-out flex flex-col">
              <div className="px-8 pt-6 pb-4 flex justify-between items-center border-b border-gray-50">
                <h2 className="text-xl font-black text-gray-900">발음 진단 리포트</h2>
                <button
                  onClick={() => setShowResultOverlay(false)}
                  className="p-2 bg-gray-50 rounded-full text-gray-400 active:scale-90 transition-all"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 pb-12">
                <div className="bg-gray-900 text-white rounded-[2.5rem] p-8 mb-8 relative overflow-hidden shadow-xl">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-gray-800 rounded-full -mr-10 -mt-10 opacity-50"></div>
                  <div className="relative z-10 flex items-center justify-between">
                    <div>
                      <p className="text-gray-400 font-bold mb-1">Total Score</p>
                      <div className="text-5xl font-black tracking-tight">
                        {overallScore}
                        <span className="text-2xl text-gray-500 ml-1">점</span>
                      </div>
                    </div>
                    <div className="w-16 h-16 bg-gradient-to-tr from-green-400 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg transform rotate-3">
                      <Star className="text-white fill-white" size={32} />
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  {resultWords.map((wordObj: any, idx: number) => {
                    const isExpanded = expandedWordIndex === idx;
                    const score = Math.round(wordObj.score);
                    let colorClass = "text-red-500 bg-red-50 border-red-100";
                    if (score >= 80)
                      colorClass = "text-blue-600 bg-blue-50 border-blue-100";
                    else if (score >= 60)
                      colorClass = "text-green-600 bg-green-50 border-green-100";

                    return (
                      <div
                        key={idx}
                        className="bg-white border border-gray-100 rounded-3xl shadow-sm overflow-hidden transition-all duration-300"
                      >
                        <div
                          onClick={() =>
                            setExpandedWordIndex(isExpanded ? null : idx)
                          }
                          className={`p-5 flex items-center justify-between cursor-pointer active:bg-gray-50 ${
                            isExpanded ? "bg-gray-50/50" : ""
                          }`}
                        >
                          <span className="text-lg font-black text-gray-800">
                            {wordObj.text}
                          </span>
                          <span
                            className={`text-sm font-black px-3 py-1 rounded-full border ${colorClass}`}
                          >
                            {score}점
                          </span>
                        </div>

                        {isExpanded && (
                          <div className="px-5 pb-5 pt-1 bg-gray-50/30 animate-in slide-in-from-top-2">
                            <div className="flex flex-wrap gap-2 mt-2">
                              {extractPhonesFromWord(wordObj).map((ph, pIdx) => {
                                const s = ph.score;
                                const badge =
                                  s >= 80
                                    ? "text-green-600 bg-green-50 border-green-100"
                                    : s >= 60
                                    ? "text-orange-600 bg-orange-50 border-orange-100"
                                    : "text-red-600 bg-red-50 border-red-100";

                                return (
                                  <div
                                    key={pIdx}
                                    className="flex items-center justify-between gap-2 min-w-[86px] bg-white border border-gray-100 rounded-2xl px-3 py-2"
                                  >
                                    <span className="text-base font-black text-gray-800">
                                      {ph.symbol}
                                    </span>
                                    <span
                                      className={`text-xs font-black px-2 py-1 rounded-full border ${badge}`}
                                    >
                                      {ph.score}점
                                    </span>
                                  </div>
                                );
                              })}

                              {extractPhonesFromWord(wordObj).length === 0 && (
                                <div className="text-xs text-gray-400 p-2">
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

              <div className="p-6 pt-0 bg-white grid grid-cols-2 gap-4">
                <button
                  onClick={() => {
                    setShowResultOverlay(false);
                    setRecordingStatus("idle");
                    setRecordBlob(null);
                    setEvaluationResult(null);
                    setOverallScore(0);
                  }}
                  className="h-16 bg-gray-100 text-gray-600 font-black rounded-2xl flex items-center justify-center gap-2 active:scale-95 transition-all"
                >
                  <RotateCcw size={18} /> 다시 녹음
                </button>
                <button
                  onClick={() => {
                    setShowResultOverlay(false);
                    handleNext();
                  }}
                  className="h-16 bg-gray-900 text-white font-black rounded-2xl flex items-center justify-center gap-2 shadow-lg active:scale-95 transition-all"
                >
                  다음 단어 <ArrowRight size={18} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
