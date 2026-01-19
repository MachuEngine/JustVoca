"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ChevronLeft, Volume2, Mic, RotateCcw, ChevronRight, Square, Loader2 } from 'lucide-react';
// [수정] completeStudy 함수 추가 임포트
import { uploadRecord, getWords, completeStudy } from '../api'; 

export default function StudyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const level = searchParams.get('level') || "초급1";

  // [추가] 임시 유저 ID (나중에 로그인 정보에서 가져오도록 연동 가능)
  const USER_ID = "안종민"; 

  // 상태 관리
  const [words, setWords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordBlob, setRecordBlob] = useState<Blob | null>(null);
  const [score, setScore] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // [로직] 초기 데이터 로드 (user_id를 함께 전달하여 진도에 맞는 단어 10개 로드)
  useEffect(() => {
    async function fetchData() {
      try {
        // [수정] USER_ID를 인자로 전달
        const data = await getWords(level, USER_ID); 
        if (data && data.length > 0) {
          setWords(data);
        } else {
          alert(`'${level}' 과정에 해당하는 학습 데이터가 없거나 모든 학습을 마쳤습니다.`);
          router.back();
        }
      } catch (error) {
        console.error("데이터 로드 실패:", error);
        alert("서버 연결에 실패했습니다.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [level]);

  // 오디오 재생 함수 (TTS) - 기존 유지
  const playAudio = (text: string, e: React.MouseEvent) => {
    e.stopPropagation(); 
    if (!text) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ko-KR'; 
    utterance.rate = 0.9; 
    window.speechSynthesis.speak(utterance);
  };

  // 로딩 화면 - 기존 유지
  if (loading) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-gray-50">
        <Loader2 className="animate-spin text-green-500 mb-2" size={40} />
        <p className="text-gray-500 font-bold">오늘의 단어를 준비 중입니다...</p>
      </div>
    );
  }

  if (words.length === 0) return null;

  const currentWord = words[currentIndex];
  const progress = ((currentIndex + 1) / words.length) * 100;

  // 녹음 시작 - 기존 유지
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordBlob(blob);
      };
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error(err);
      alert("마이크 사용 권한을 허용해주세요.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // [수정] 평가 제출 시 user_id를 포함하여 DB 로그에 기록되도록 함
  const handleSubmit = async () => {
    if (!recordBlob) return;
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', recordBlob, 'recording.webm');
      formData.append('word', currentWord.word);
      formData.append('user_id', USER_ID); // 👈 백엔드 로그 저장용 ID 추가
      
      const result = await uploadRecord(formData);
      setScore(result.score);
      setFeedback(result.feedback);
    } catch (error) {
      console.error(error);
      alert("평가 중 오류가 발생했습니다.");
    } finally {
      setIsProcessing(false);
    }
  };

  // [수정] 10개 단어 학습 완료 시 백엔드에 진도 업데이트 요청
  const handleNext = async () => {
    if (currentIndex < words.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setIsFlipped(false);
      setRecordBlob(null);
      setScore(null);
      setFeedback(null);
    } else {
      // 10개 학습 완료 시점
      try {
        // [추가] 백엔드 DB의 current_page를 +1 시킴
        await completeStudy(level, USER_ID);
        alert("오늘의 학습을 모두 완료했습니다! 고생하셨습니다 🎉");
      } catch (error) {
        console.error("진도 업데이트 실패:", error);
      } finally {
        router.push('/student_home');
      }
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 relative">
      <header className="h-16 flex items-center justify-between px-4 bg-white border-b border-gray-100">
        <button onClick={() => router.back()} className="p-2 -ml-2 rounded-full hover:bg-gray-100">
          <ChevronLeft className="text-gray-800" />
        </button>
        <div className="flex-1 mx-6">
          <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
        <span className="text-xs font-bold text-gray-400 w-8 text-right">
          {currentIndex + 1}/{words.length}
        </span>
      </header>

      <main className="flex-1 p-6 flex flex-col items-center justify-center relative perspective-1000">
        <div className="w-full max-w-sm aspect-[4/5] relative">
          
          {/* [앞면] */}
          <div 
            onClick={() => !isFlipped && setIsFlipped(true)}
            className={`
              absolute inset-0 w-full h-full bg-white rounded-3xl shadow-xl border border-gray-100 p-8 
              flex flex-col items-center justify-center text-center transition-all duration-500 backface-hidden cursor-pointer
              ${isFlipped ? 'opacity-0 pointer-events-none translate-y-4' : 'opacity-100 translate-y-0'}
            `}
          >
            <span className="absolute top-6 left-6 text-xs font-bold text-gray-400 bg-gray-100 px-2 py-1 rounded">
              {currentWord.level}
            </span>
            <span className="text-xs text-green-600 font-bold mb-8 bg-green-50 px-3 py-1 rounded-full animate-pulse">
              터치해서 뒤집기
            </span>
            <h1 className="text-5xl font-black text-gray-900 mb-6">{currentWord.word}</h1>
            <p className="text-xl text-gray-700 font-bold mb-2 break-keep">{currentWord.meaning}</p>
            <p className="text-sm text-gray-400">{currentWord.eng_meaning}</p>
            <button 
              onClick={(e) => playAudio(currentWord.word, e)}
              className="mt-12 p-4 bg-gray-50 rounded-full text-gray-600 hover:bg-gray-200 transition-colors shadow-sm active:scale-95"
            >
              <Volume2 size={28} />
            </button>
          </div>

          {/* [뒷면] */}
          <div 
             className={`
              absolute inset-0 w-full h-full bg-white rounded-3xl shadow-xl border border-gray-100 p-6 
              flex flex-col items-center justify-between transition-all duration-500 backface-hidden
              ${isFlipped ? 'opacity-100 translate-y-0' : 'opacity-0 pointer-events-none -translate-y-4'}
            `}
          >
            <div className="text-center mt-2 w-full">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">{currentWord.word}</h2>
              <div className="bg-gray-50 p-5 rounded-2xl w-full">
                <p className="text-gray-800 font-medium leading-relaxed break-keep text-sm">"{currentWord.example}"</p>
                <button 
                  onClick={(e) => playAudio(currentWord.example, e)}
                  className="mt-3 flex items-center justify-center gap-1 text-xs text-gray-500 w-full hover:text-blue-500"
                >
                  <Volume2 size={12} /> 예문 듣기
                </button>
              </div>
            </div>

            <div className="flex-1 flex flex-col items-center justify-center w-full py-4">
              {score !== null ? (
                <div className="text-center animate-fade-in-up">
                  <div className="relative w-28 h-28 mx-auto mb-4">
                     <svg className="w-full h-full" viewBox="0 0 36 36">
                        <path className="text-gray-100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
                        <path className="text-green-500 drop-shadow-md" strokeDasharray={`${score}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
                     </svg>
                     <div className="absolute inset-0 flex items-center justify-center flex-col">
                        <span className="text-3xl font-black text-gray-900">{score}</span>
                        <span className="text-[10px] text-gray-400">점</span>
                     </div>
                  </div>
                  <p className="text-gray-800 font-bold mb-1 px-4 text-sm">{feedback}</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-6">
                   {!recordBlob ? (
                     <button 
                      onClick={isRecording ? stopRecording : startRecording}
                      className={`w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-xl border-4 border-white ${isRecording ? 'bg-red-500 animate-pulse ring-4 ring-red-100' : 'bg-green-500 hover:bg-green-600 ring-4 ring-green-100'}`}
                    >
                      {isRecording ? <Square size={28} fill="white" className="text-white" /> : <Mic size={32} className="text-white" />}
                    </button>
                   ) : (
                     <div className="flex gap-3 animate-fade-in-up">
                        <button onClick={() => { setRecordBlob(null); }} className="w-14 h-14 bg-gray-100 rounded-full text-gray-600 flex items-center justify-center hover:bg-gray-200 transition-colors"><RotateCcw size={20} /></button>
                        <button onClick={handleSubmit} disabled={isProcessing} className="h-14 px-8 bg-black text-white rounded-full font-bold shadow-lg hover:bg-gray-800 disabled:opacity-50 flex items-center gap-2 transition-all active:scale-95">
                          {isProcessing ? '분석 중...' : '발음 평가하기'}
                        </button>
                     </div>
                   )}
                   <p className="text-sm text-gray-400 font-medium">{isRecording ? "듣고 있어요..." : recordBlob ? "녹음 완료!" : "마이크를 눌러 따라 읽어보세요"}</p>
                </div>
              )}
            </div>

            <div className="w-full flex justify-between items-center pt-4 border-t border-gray-50">
              <button onClick={() => { setIsFlipped(false); setRecordBlob(null); setScore(null); }} className="text-xs text-gray-400 font-bold hover:text-gray-600 px-2 py-2">다시 공부하기</button>
              {score !== null && (
                <button onClick={handleNext} className="flex items-center gap-1 text-green-600 font-bold hover:text-green-700 bg-green-50 px-4 py-2 rounded-lg transition-colors">다음 단어 <ChevronRight size={16} /></button>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}