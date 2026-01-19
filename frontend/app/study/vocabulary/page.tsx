"use client";

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Volume2, Mic, Square, BarChart, ChevronLeft, ChevronRight, RotateCcw,
  CheckCircle2, XCircle, Star, Trophy, ArrowRight, MessageCircle, X,
  Activity, Target, Sparkles, Loader2
} from 'lucide-react';
// [해결] 경로 오류 ts(2307) 수정: 실제 프로젝트의 api 파일 경로로 맞추세요.
import { uploadRecord } from '../../api'; 

export default function VocabularyStudyPage() {
  const router = useRouter();
  const USER_ID = "안종민"; 

  // 1. 상태 관리
  const [isFlipped, setIsFlipped] = useState(false);
  const [recordingStatus, setRecordingStatus] = useState<'idle' | 'recording' | 'done'>('idle');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showResultOverlay, setShowResultOverlay] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // SpeechPro 데이터 상태
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [overallScore, setOverallScore] = useState(0);

  // 녹음 관련 Ref 및 상태
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [recordBlob, setRecordBlob] = useState<Blob | null>(null);

  // 2. 학습 데이터
  const wordData = [
    { word: "안녕하세요", pronunciation: "[안녕하세요]", meaning: "인사", meaningEng: "Greeting", example: "안녕하세요.", audioKey: "Level1_1" },
    { word: "안녕", pronunciation: "[안녕]", meaning: "인사", meaningEng: "Hi", example: "안녕!", audioKey: "Level1_2" },
    { word: "감사합니다", pronunciation: "[감사합니다]", meaning: "감사", meaningEng: "Thank you", example: "도와주셔서 감사합니다.", audioKey: "Level1_3" },
  ];

  const currentWord = wordData[currentIndex];

  // 3. 기능 함수
  const playLocalAudio = (type: 'voca' | 'example', e: React.MouseEvent) => {
    e.stopPropagation();
    const levelFolder = currentWord.audioKey.split('_')[0].toLowerCase();
    const audioPath = `/assets/audio/${type}/${levelFolder}/${currentWord.audioKey}.wav`;
    const audio = new Audio(audioPath);
    audio.play().catch(() => console.error("오디오 재생 실패"));
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];
      mediaRecorderRef.current.ondataavailable = (e) => chunksRef.current.push(e.data);
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        setRecordBlob(blob);
        setRecordingStatus('done');
      };
      mediaRecorderRef.current.start();
      setRecordingStatus('recording');
    } catch (err) {
      alert("마이크 권한을 확인해주세요.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
  };

  // [수정] 결과 보기 버튼 클릭 시 API 호출 및 오버레이 활성화
  const handleShowResult = async () => {
    if (!recordBlob) return;
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('audio', recordBlob, 'record.wav');
      formData.append('word', currentWord.word);
      
      const response = await uploadRecord(formData);
      if (response.success) {
        setEvaluationResult(response.data.result);
        const sentence = response.data.result.quality.sentences.find((s: any) => s.text !== "!SIL");
        setOverallScore(Math.round(sentence?.score || 0));
        setShowResultOverlay(true);
      }
    } catch (error) {
      alert("AI 평가 중 오류가 발생했습니다.");
    } finally {
      setIsProcessing(false);
    }
  };

  const moveToWord = (direction: 'next' | 'prev') => {
    if (direction === 'next' && currentIndex < wordData.length - 1) setCurrentIndex(prev => prev + 1);
    else if (direction === 'prev' && currentIndex > 0) setCurrentIndex(prev => prev - 1);
    setIsFlipped(false);
    setRecordingStatus('idle');
    setRecordBlob(null);
    setEvaluationResult(null);
    setShowResultOverlay(false);
  };

  // 실시간 음절 데이터 추출
  const targetSentence = evaluationResult?.quality.sentences.find((s: any) => s.text !== "!SIL");
  const syllables = targetSentence?.words[0]?.syll || [];

  return (
    <div className="relative flex flex-col min-h-screen bg-gray-50 p-6 select-none overflow-hidden">
      
      {/* 상단 레이아웃 */}
      <div className="flex justify-between items-end mb-6 px-1">
        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <span className="text-[10px] font-black text-green-600 bg-green-50 px-2 py-1 rounded-md border border-green-100 uppercase">초급 1</span>
            <span className="text-[10px] font-black text-blue-600 bg-blue-50 px-2 py-1 rounded-md border border-blue-100 uppercase">TOPIK 1급</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className={`w-1.5 h-1.5 rounded-full ${isFlipped ? 'bg-blue-500' : 'bg-green-500'}`}></div>
            <span className="text-[11px] font-black text-gray-500 uppercase tracking-widest">
              {isFlipped ? "Practice Mode" : "Learning Mode"}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] font-black text-gray-300 font-mono mb-1">{String(currentIndex + 1).padStart(2, '0')} / {wordData.length}</div>
          <button onClick={() => setIsFlipped(!isFlipped)} className="flex items-center gap-1 text-[10px] font-black text-gray-400 border border-gray-200 px-2 py-1 rounded-lg bg-white shadow-sm active:bg-gray-100"><RotateCcw size={10} /> <span>회전</span></button>
        </div>
      </div>

      {/* 단어 카드 영역 */}
      <div className="flex-1 flex flex-col items-center justify-center mb-8">
        <div onClick={() => !isFlipped && setIsFlipped(true)} className="w-full aspect-[4/5] bg-white rounded-[3.5rem] shadow-2xl border border-gray-100 p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-500 relative overflow-hidden active:scale-[0.98]">
          {!isFlipped ? (
            <div className="flex flex-col items-center w-full animate-in fade-in duration-300">
              <h2 className="text-6xl font-black text-gray-900 mb-2">{currentWord.word}</h2>
              <p className="text-xl font-bold text-green-600 mb-10">{currentWord.pronunciation}</p>
              <div className="space-y-4 mb-12 px-4">
                <p className="text-gray-700 font-bold text-lg leading-relaxed">{currentWord.meaning}</p>
                <p className="text-gray-400 text-sm italic">{currentWord.meaningEng}</p>
              </div>
              <button onClick={(e) => playLocalAudio('voca', e)} className="flex items-center gap-3 px-10 py-5 bg-gray-900 text-white font-black rounded-2xl shadow-lg transition-all"><Volume2 size={24} /> <span>발음 듣기</span></button>
            </div>
          ) : (
            <div className="flex flex-col items-center w-full animate-in fade-in duration-300">
              <div className="w-full text-left mb-8 border-l-4 border-blue-500 pl-4">
                <h4 className="text-2xl font-black text-gray-900">{currentWord.word}</h4>
                <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1 opacity-60">Speak Now</p>
              </div>
              <h3 className="text-2xl font-black text-gray-900 leading-snug mb-12 text-left w-full break-keep px-2">
                {currentWord.example}
              </h3>
              <div className="grid grid-cols-1 w-full gap-4 px-2">
                <button onClick={(e) => playLocalAudio('example', e)} className="w-full h-16 bg-blue-50 text-blue-600 font-black rounded-2xl flex items-center justify-center gap-3 shadow-sm"><Volume2 size={24} /><span>문장 듣기</span></button>
                <div onClick={(e) => e.stopPropagation()}>
                  {recordingStatus === 'idle' && (
                    <button onClick={startRecording} className="w-full h-16 bg-gray-900 text-white font-black rounded-2xl flex items-center justify-center gap-3 shadow-lg active:scale-95 transition-all"><Mic size={24} /><span>문장 녹음</span></button>
                  )}
                  {recordingStatus === 'recording' && (
                    <button onClick={stopRecording} className="w-full h-16 bg-red-500 text-white font-black rounded-2xl flex items-center justify-center gap-3 animate-pulse shadow-lg"><Square size={24} fill="white" /><span>중지</span></button>
                  )}
                  {recordingStatus === 'done' && (
                    <button onClick={handleShowResult} disabled={isProcessing} className="w-full h-16 bg-green-600 text-white font-black rounded-2xl flex items-center justify-center gap-3 shadow-xl active:scale-95 transition-all">
                      {isProcessing ? <Loader2 className="animate-spin" /> : <BarChart size={24} />}
                      <span>{isProcessing ? "분석 중..." : "결과 보기"}</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 하단 네비게이션 */}
      <div className="flex gap-4 mb-4">
        <button disabled={currentIndex === 0} onClick={() => moveToWord('prev')} className="flex-1 h-16 bg-white border border-gray-100 rounded-3xl flex items-center justify-center gap-2 font-black text-gray-400 active:bg-gray-50 disabled:opacity-30 shadow-sm"><ChevronLeft size={20} /><span>이전</span></button>
        <button 
          disabled={currentIndex === wordData.length - 1 || recordingStatus !== 'done'} 
          onClick={() => moveToWord('next')} 
          className={`flex-1 h-16 border rounded-3xl flex items-center justify-center gap-2 font-black transition-all shadow-sm ${recordingStatus === 'done' ? 'bg-white border-green-200 text-green-600 active:bg-green-50' : 'bg-gray-100 border-gray-100 text-gray-300'}`}
        ><span>다음</span><ChevronRight size={20} /></button>
      </div>

      {/* --- [개선된 결과 상세 오버레이] --- */}
      {showResultOverlay && evaluationResult && (
        <div className="absolute inset-0 z-50 animate-in fade-in duration-300 overflow-hidden">
          <div className="absolute inset-0 bg-gray-900/60 backdrop-blur-md" onClick={() => setShowResultOverlay(false)}></div>
          
          <div className="absolute inset-x-0 bottom-0 top-12 bg-white rounded-t-[4.5rem] p-8 flex flex-col shadow-2xl animate-in slide-in-from-bottom duration-500 ease-out overflow-y-auto pb-12">
            <div className="flex justify-center mb-6"><div className="w-12 h-1.5 bg-gray-200 rounded-full"></div></div>
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-2xl font-black text-gray-900">발음 진단 리포트</h2>
              <button onClick={() => setShowResultOverlay(false)} className="p-3 bg-gray-50 rounded-2xl text-gray-400 active:scale-90 transition-all"><X size={24} /></button>
            </div>

            {/* 총점 원형 게이지 */}
            <div className="flex flex-col items-center mb-12">
              <div className="relative w-44 h-44 rounded-full border-[14px] border-green-500 flex items-center justify-center shadow-[0_20px_50px_rgba(34,197,94,0.2)] mb-6 bg-white">
                <div className="flex flex-col items-center">
                  <span className="text-6xl font-black text-gray-900">{overallScore}</span>
                  <span className="text-[11px] font-black text-gray-400 uppercase tracking-widest -mt-1">Score</span>
                </div>
                <Star className="absolute -top-2 -right-2 text-yellow-400 fill-yellow-400" size={32} />
              </div>
              <p className="text-2xl font-black text-gray-900 tracking-tight">훌륭해요, {USER_ID}님! 👏</p>
            </div>

            {/* 음절별 상세 피드백 (동적 데이터 바인딩) */}
            <div className="bg-gray-50 rounded-[3rem] p-8 mb-10 text-center border border-gray-100">
              <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-8 flex items-center justify-center gap-2">
                <Sparkles size={14} className="text-blue-500" /> Syllable Analysis
              </h3>
              <div className="flex flex-wrap gap-4 justify-center">
                {syllables.map((syll: any, idx: number) => (
                  <div key={idx} className="flex flex-col items-center gap-3">
                    <span className={`text-3xl font-black px-6 py-4 rounded-3xl shadow-sm border bg-white ${syll.score >= 80 ? 'text-green-600 border-green-100' : 'text-red-500 border-red-100'}`}>
                      {syll.text}
                    </span>
                    {syll.score >= 80 ? <CheckCircle2 size={20} className="text-green-500" /> : <XCircle size={20} className="text-red-400" />}
                    <span className="text-xs font-bold text-gray-400">{Math.round(syll.score)}점</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 상세 분석 지표 (공백 키 참조 수정 완료) */}
            <div className="grid grid-cols-1 gap-6 mb-10">
              {[
                { label: "정확도 (Accuracy)", score: overallScore, icon: <Target size={16} />, color: "bg-green-500" },
                { label: "유창성 (Fluency)", score: Math.min(100, Math.round(evaluationResult.fluency['speech rate'] * 20)), icon: <Activity size={16} />, color: "bg-blue-500" },
                { label: "명료도 (Clarity)", score: 95, icon: <Sparkles size={16} />, color: "bg-purple-500" }
              ].map((m, idx) => (
                <div key={idx} className="bg-white p-5 rounded-3xl border border-gray-100 shadow-sm">
                  <div className="flex justify-between items-center mb-3 px-1">
                    <div className="flex items-center gap-2 text-[11px] font-black text-gray-400 uppercase tracking-tighter">{m.icon}{m.label}</div>
                    <span className="text-sm font-black text-gray-900">{m.score}%</span>
                  </div>
                  <div className="w-full h-3 bg-gray-50 rounded-full overflow-hidden">
                    <div className={`h-full ${m.color} rounded-full transition-all duration-1000 delay-500`} style={{ width: `${m.score}%` }}></div>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-5 mb-6">
              <button onClick={() => { setShowResultOverlay(false); setRecordingStatus('idle'); }} className="h-20 bg-gray-50 text-gray-500 font-black rounded-[2rem] flex items-center justify-center gap-3 active:bg-gray-100 transition-all border border-gray-100 shadow-sm"><RotateCcw size={22} /><span>다시 녹음</span></button>
              <button onClick={() => moveToWord('next')} className="h-20 bg-green-500 text-gray-900 font-black rounded-[2rem] flex items-center justify-center gap-3 shadow-xl shadow-green-100 active:scale-95 transition-all"><span>다음 단어</span><ArrowRight size={22} /></button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}