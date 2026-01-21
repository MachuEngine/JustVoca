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

export default function VocabularyStudyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const level = searchParams.get("level") || "초급1";
  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("userId") || "student"
      : "student";

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

  // --- 레벨 폴더 매핑 (로컬 오디오 경로 안정화) ---
  const levelDirMap: Record<string, string> = {
    초급1: "level1",
    초급2: "level2",
    중급1: "level3",
    중급2: "level4",
    고급: "level5",
  };
  const levelDir = levelDirMap[level] ?? "level1";

  // --- 초기 데이터 로드 ---
  useEffect(() => {
    async function fetchInitialData() {
      try {
        setLoading(true);

        const words = await getWords(level, userId);
        const mappedWords = mapWordData(words);
        setWordData(mappedWords);

        try {
          const reviews = await getReviewWords(userId);
          if (reviews && reviews.length > 0) {
            setReviewData(mapWordData(reviews));
          } else {
            setReviewData(mappedWords.slice(0, 5));
          }
        } catch (e) {
          setReviewData(mappedWords.slice(0, 5));
        }

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
    // searchParams는 객체라 dep에 넣으면 불필요 렌더링이 잦을 수 있어 level/userId로 충분
  }, [level, userId]);

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
      pronunciation: w.pronunciation || `[${w.word}]`,
      meaning: w.meaning,
      meaningEng: w.meaning_en || "Meaning",
      example: w.example || w.word,
      audioKey: w.audio_path || "",
    }));
  };

  const currentList = phase === "review" ? reviewData : wordData;
  const currentWord = currentList[currentIndex];
  const currentQuiz = quizData[currentIndex];

  let totalSteps = wordData.length;
  if (phase === "review" || phase === "review_intro") totalSteps = reviewData.length;
  else if (phase === "quiz" || phase === "quiz_intro") totalSteps = quizData.length;

  // --- 상태 리셋 ---
  const resetCardState = () => {
    setIsFlipped(false);
    setRecordingStatus("idle");
    setRecordBlob(null);
    setEvaluationResult(null);
    setShowResultOverlay(false);
    setExpandedWordIndex(null);
    setIsProcessing(false);
  };

  function parseLevelDirFromAudioKey(audioKey: string, fallbackLevelDir: string) {
    // 예: "Level6_1" / "level6_1" / "LEVEL6_1" -> "level6"
    const m = String(audioKey).match(/level\s*(\d+)/i);
    if (m && m[1]) return `level${m[1]}`;
    return fallbackLevelDir;
  }

  function buildAudioPath(params: {
    type: "voca" | "example";
    audioKey: string;
    fallbackLevelDir: string;
  }) {
    const { type, audioKey, fallbackLevelDir } = params;

    if (!audioKey) return "";
    if (audioKey.startsWith("http")) return audioKey;

    const dir = parseLevelDirFromAudioKey(audioKey, fallbackLevelDir);
    return `/assets/audio/${type}/${dir}/${audioKey}.wav`;
  }


  // --- 기능 함수 ---
  const playLocalAudio = (type: "voca" | "example", e: React.MouseEvent) => {
    e.stopPropagation();
    if (!currentWord || !currentWord.audioKey) return;

    const audioPath = buildAudioPath({
      type,
      audioKey: currentWord.audioKey,
      fallbackLevelDir: levelDir, // 기존 레벨 매핑은 fallback으로만 사용
    });

    if (!audioPath) return;

    const audio = new Audio(audioPath);
    audio.play().catch(() => console.error("오디오 재생 실패:", audioPath));
  };

  const handleNext = async () => {
    if (phase === "learning") {
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
        setPhase("review_intro");
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
      await completeStudy(level, userId);
    } catch (e) {
      console.error(e);
    }
  };

  // --- 녹음 ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const preferredType = MediaRecorder.isTypeSupported(
        "audio/webm;codecs=opus"
      )
        ? "audio/webm;codecs=opus"
        : (MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "");

      mediaRecorderRef.current = preferredType
        ? new MediaRecorder(stream, { mimeType: preferredType })
        : new MediaRecorder(stream);

      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        // 마이크 트랙 중지(점유 해제)
        stream.getTracks().forEach((track) => track.stop());

        if (chunksRef.current.length === 0) {
          alert("녹음된 데이터가 없습니다. 다시 시도해주세요.");
          setRecordingStatus("idle");
          return;
        }

        const mimeType =
          preferredType || mediaRecorderRef.current?.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: mimeType });
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
      const ext =
      recordBlob.type.includes("webm") ? "webm" :
      recordBlob.type.includes("ogg") ? "ogg" :
      recordBlob.type.includes("wav") ? "wav" : "webm";

      const file = new File([recordBlob], `record.${ext}`, { type: recordBlob.type });

      console.log("[UPLOAD] file.name=", file.name, "type=", file.type, "size=", file.size);

      const formData = new FormData();
      formData.append("audio", file);
      formData.append("text", targetText);
      // [추가] 누가 학습했는지 userId 전송
      formData.append("user_id", userId); 
      // [추가] 어떤 단어인지 word 전송 (로그 저장용)
      formData.append("word", currentWord.word);

      console.log("[UPLOAD] fd audio =", formData.get("audio"));
      console.log("[UPLOAD] fd text  =", formData.get("text"));

      const response = await uploadRecord(formData);
      console.log("[UPLOAD] 6 response =", response);

      if (response?.success === false) {
        alert(`에러 발생: ${response.error || "알 수 없는 오류"}`);
        return;
      }

      console.log("[UPLOAD] response JSON =", JSON.stringify(response));

      const raw = response?.result ?? response ?? {};

      // 1) raw.result가 객체이고 그 안에 quality/score가 있으면 그게 진짜 본체일 가능성이 큼
      const candidate =
        (raw && typeof raw === "object" && raw.result && typeof raw.result === "object") ? raw.result : raw;

      const resultData =
        candidate?.quality ? candidate :
        candidate?.score !== undefined ? candidate :
        candidate?.score_result ? candidate.score_result :
        candidate?.data ? candidate.data :
        candidate;

      console.log("[UPLOAD] raw =", raw);
      console.log("[UPLOAD] resultData(normalized) =", resultData);

      if (resultData) {
        setEvaluationResult(resultData);

        let finalScore = 0;

        // 1. 최상위 score가 있다면 그것이 정답 (로그의 맨 마지막 "score": 73.186)
        if (typeof resultData.score === 'number') {
          finalScore = resultData.score;
        } 
        // 2. quality.score 확인
        else if (resultData.quality?.score) {
          finalScore = resultData.quality.score;
        }
        // 3. sentences 배열에서 !SIL이 아닌 실제 문장 찾기 (안전장치)
        else if (resultData.quality?.sentences) {
           const realSentence = resultData.quality.sentences.find(
             (s: any) => s.text && s.text !== "!SIL"
           );
           if (realSentence) {
             finalScore = realSentence.score;
           }
        }

        console.log("[DEBUG] 최종 결정된 점수:", finalScore); // 73.186 예상

        setOverallScore(Math.round(finalScore));
        setShowResultOverlay(true);
      } else {
        console.error("서버 응답 데이터 구조 이상:", resultData);
        alert("평가 결과를 표시할 수 있는 데이터가 없습니다.");
      }
    } catch (error: any) {
      alert("서버와 통신할 수 없습니다.");
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

  // ✅ 다음 버튼 활성화 조건 수정:
  // - learning/review: 앞면(단어 모드)은 자유롭게 다음 가능, 뒷면(연습 모드)은 결과 있어야 다음 가능
  // - quiz: 정답이어야 다음 가능
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
        <div className="flex flex-col min-h-screen bg-white p-6 items-center justify-center text-center">
          <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-6 animate-in zoom-in duration-500">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
          <h2 className="text-3xl font-black text-gray-900 mb-2">학습 완료!</h2>
          <p className="text-gray-500 mb-10">
            오늘도 목표를 달성하셨네요.
            <br />
            정말 고생 많으셨습니다.
          </p>
          <button
            onClick={() => router.push("/student_home")}
            className="w-full py-5 bg-blue-500 text-white rounded-2xl font-bold text-lg shadow-lg active:scale-95 transition-all"
          >
            홈으로 돌아가기
          </button>
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
        <div className="flex-1 flex flex-col items-center justify-start w-full max-w-md mx-auto">
          {/* 1. 카드 영역 */}
          <div className="w-full mb-6">
            {phase === "quiz" ? (
              <div className="w-full aspect-[4/5] bg-white rounded-[3.5rem] shadow-2xl border border-gray-100 p-8 flex flex-col items-center justify-center relative overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex-1 w-full flex flex-col justify-center">
                  <span className="text-center text-xs font-black text-blue-500 uppercase tracking-widest mb-4">
                    Quiz
                  </span>
                  <h3 className="text-2xl font-black text-gray-900 text-center break-keep leading-relaxed mb-8">
                    "{currentQuiz?.question}"
                  </h3>
                  <div className="space-y-3 w-full">
                    {currentQuiz?.options?.map((option: string, idx: number) => {
                      let btnClass =
                        "w-full py-4 rounded-xl text-lg font-bold border-2 transition-all shadow-sm ";

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
                    <p className="text-center text-red-500 font-bold mt-4 animate-pulse">
                      오답입니다. 다시 선택해보세요!
                    </p>
                  )}
                  {isQuizCorrect === true && (
                    <p className="text-center text-green-600 font-bold mt-4 animate-in zoom-in">
                      정답입니다! 🎉
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div
                onClick={() => setIsFlipped((prev) => !prev)}
                className="w-full aspect-[4/5] bg-white rounded-[3.5rem] shadow-2xl border border-gray-100 p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-500 relative overflow-hidden active:scale-[0.99]"
              >
                {!isFlipped ? (
                  <div className="flex flex-col items-center w-full animate-in fade-in duration-300">
                    <h2 className="text-6xl font-black text-gray-900 mb-2">
                      {currentWord?.word}
                    </h2>
                    <p className="text-xl font-bold text-green-600 mb-10">
                      {currentWord?.pronunciation}
                    </p>
                    <div className="space-y-4 mb-12 px-4">
                      <p className="text-gray-700 font-bold text-lg leading-relaxed">
                        {currentWord?.meaning}
                      </p>
                      <p className="text-gray-400 text-sm italic">
                        {currentWord?.meaningEng}
                      </p>
                    </div>
                    <button
                      onClick={(e) => playLocalAudio("voca", e)}
                      className={`flex items-center gap-3 px-10 py-5 text-white font-black rounded-2xl shadow-lg transition-all ${
                        !currentWord?.audioKey
                          ? "bg-gray-400 opacity-50"
                          : "bg-gray-900 active:scale-95"
                      }`}
                    >
                      <Volume2 size={24} /> <span>발음 듣기</span>
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center w-full animate-in fade-in duration-300">
                    <div className="w-full text-left mb-8 border-l-4 border-blue-500 pl-4">
                      <h4 className="text-2xl font-black text-gray-900">
                        {currentWord?.word}
                      </h4>
                      <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1 opacity-60">
                        Speak Now
                      </p>
                    </div>
                    <h3 className="text-2xl font-black text-gray-900 leading-snug mb-12 text-left w-full break-keep px-2">
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
                        <Volume2 size={24} />
                        <span>문장 듣기</span>
                      </button>

                      <div onClick={(e) => e.stopPropagation()}>
                        {recordingStatus === "idle" && (
                          <button
                            onClick={startRecording}
                            className="w-full h-16 bg-gray-900 text-white font-black rounded-2xl flex items-center justify-center gap-3 shadow-lg active:scale-95 transition-all"
                          >
                            <Mic size={24} />
                            <span>문장 녹음</span>
                          </button>
                        )}
                        {recordingStatus === "recording" && (
                          <button
                            onClick={stopRecording}
                            className="w-full h-16 bg-red-500 text-white font-black rounded-2xl flex items-center justify-center gap-3 animate-pulse shadow-lg"
                          >
                            <Square size={24} fill="white" />
                            <span>중지</span>
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
                              <BarChart size={24} />
                            )}
                            <span>
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
                // ✅ 이전 이동 시 상태 리셋
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
              className={`flex-1 h-16 border rounded-3xl flex items-center justify-center gap-2 font-black transition-all shadow-sm
                ${
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
                <h2 className="text-xl font-black text-gray-900">
                  발음 진단 리포트
                </h2>
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
                    if (score >= 80) colorClass = "text-blue-600 bg-blue-50 border-blue-100";
                    else if (score >= 60) colorClass = "text-green-600 bg-green-50 border-green-100";

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
                                <div className="text-xs text-gray-400 p-2">상세 음소 정보 없음</div>
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
