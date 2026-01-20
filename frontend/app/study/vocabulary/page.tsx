"use client";

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Volume2, Mic, Square, BarChart, ChevronLeft, ChevronRight, RotateCcw,
  Star, ArrowRight, X, ChevronDown, ChevronUp, Sparkles, Loader2, MessageSquareQuote
} from 'lucide-react';
import { uploadRecord } from '../../api'; 

export default function VocabularyStudyPage() {
  const router = useRouter();
  const USER_ID = "학습자"; 

  // 1. 상태 관리
  const [isFlipped, setIsFlipped] = useState(false);
  const [recordingStatus, setRecordingStatus] = useState<'idle' | 'recording' | 'done'>('idle');
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // 결과 오버레이 관련
  const [showResultOverlay, setShowResultOverlay] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [expandedWordIndex, setExpandedWordIndex] = useState<number | null>(null);
  
  // SpeechPro 데이터 상태
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [overallScore, setOverallScore] = useState(0);

  // 녹음 관련
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

  const handleShowResult = async () => {
    if (!recordBlob) return;
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('audio', recordBlob, 'record.wav');
      
      // [수정 포인트] 단어 대신 '예문'을 전송
      // 키 이름도 'word' -> 'text'로 변경하여 의미 명확화
      formData.append('text', currentWord.example); 
      
      const response = await uploadRecord(formData);
      if (response.success) {
        setEvaluationResult(response.data.result);
        const sentence = response.data.result.quality.sentences.find((s: any) => s.text !== "!SIL");
        setOverallScore(Math.round(sentence?.score || 0));
        setShowResultOverlay(true);
      }
    } catch (error) {
      console.error(error);
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
    setExpandedWordIndex(null);
  };

  const toggleWordDetail = (index: number) => {
    setExpandedWordIndex(expandedWordIndex === index ? null : index);
  };

  const targetSentence = evaluationResult?.quality.sentences.find((s: any) => s.text !== "!SIL");
  const words = targetSentence?.words || [];

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-blue-600 bg-blue-50 border-blue-100";
    if (score >= 60) return "text-green-600 bg-green-50 border-green-100";
    return "text-red-500 bg-red-50 border-red-100";
  };

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
        <div 
          onClick={() => setIsFlipped(prev => !prev)} 
          className="w-full aspect-[4/5] bg-white rounded-[3.5rem] shadow-2xl border border-gray-100 p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-500 relative overflow-hidden active:scale-[0.98]"
        >
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

      {/* --- 결과 상세 오버레이 --- */}
      {showResultOverlay && evaluationResult && (
        <div className="absolute inset-0 z-50 animate-in fade-in duration-300 overflow-hidden">
          <div className="absolute inset-0 bg-gray-900/60 backdrop-blur-md" onClick={() => setShowResultOverlay(false)}></div>
          
          <div className="absolute inset-x-0 bottom-0 top-20 bg-white rounded-t-[3rem] shadow-2xl animate-in slide-in-from-bottom duration-500 ease-out flex flex-col">
            
            <div className="px-8 pt-6 pb-4 flex justify-between items-center border-b border-gray-50">
              <h2 className="text-xl font-black text-gray-900">발음 진단 리포트</h2>
              <button onClick={() => setShowResultOverlay(false)} className="p-2 bg-gray-50 rounded-full text-gray-400 active:scale-90 transition-all"><X size={20} /></button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 pb-12">
              
              {/* 종합 점수 */}
              <div className="bg-gray-900 text-white rounded-[2.5rem] p-8 mb-8 relative overflow-hidden shadow-xl">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gray-800 rounded-full -mr-10 -mt-10 opacity-50"></div>
                <div className="relative z-10 flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 font-bold mb-1">Total Score</p>
                    <div className="text-5xl font-black tracking-tight">{overallScore}<span className="text-2xl text-gray-500 ml-1">점</span></div>
                  </div>
                  <div className="w-16 h-16 bg-gradient-to-tr from-green-400 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg transform rotate-3">
                    <Star className="text-white fill-white" size={32} />
                  </div>
                </div>
                <div className="mt-6 pt-6 border-t border-gray-800 flex items-start gap-3">
                  <MessageSquareQuote className="text-blue-400 shrink-0 mt-1" size={20} />
                  <div>
                    <p className="text-sm font-bold text-gray-300 leading-relaxed">
                      {overallScore >= 80 ? "아주 자연스러운 발음이에요! 억양이 한국인 같아요." : "전체적으로 좋지만, 받침 발음을 조금 더 신경 써보세요."}
                    </p>
                  </div>
                </div>
              </div>

              {/* 상세 분석 (어절 > 음절 > 음소) */}
              <div className="mb-6">
                <h3 className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Sparkles size={12} className="text-blue-500" /> 상세 분석 (단어를 눌러보세요)
                </h3>
                
                <div className="space-y-3">
                  {words.map((wordObj: any, idx: number) => {
                    const isExpanded = expandedWordIndex === idx;
                    const score = Math.round(wordObj.score);
                    const colorClass = getScoreColor(score);

                    return (
                      <div key={idx} className="bg-white border border-gray-100 rounded-3xl shadow-sm overflow-hidden transition-all duration-300">
                        {/* 어절 */}
                        <div 
                          onClick={() => toggleWordDetail(idx)}
                          className={`p-5 flex items-center justify-between cursor-pointer active:bg-gray-50 ${isExpanded ? 'bg-gray-50/50' : ''}`}
                        >
                          <div className="flex items-center gap-4">
                            <span className="text-lg font-black text-gray-800">{wordObj.text}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className={`text-sm font-black px-3 py-1 rounded-full border ${colorClass}`}>
                              {score}점
                            </span>
                            {isExpanded ? <ChevronUp size={18} className="text-gray-300" /> : <ChevronDown size={18} className="text-gray-300" />}
                          </div>
                        </div>

                        {/* 상세 내용 */}
                        {isExpanded && (
                          <div className="px-5 pb-5 pt-1 bg-gray-50/30 animate-in slide-in-from-top-2 duration-200">
                            <div className="flex flex-wrap gap-2 mt-2">
                              {wordObj.syll.map((syll: any, sIdx: number) => {
                                const phones = syll.phones || syll.phonemes || []; 

                                return (
                                  <div key={sIdx} className="flex-1 min-w-[70px] bg-white border border-gray-100 rounded-2xl p-3 flex flex-col items-center shadow-sm">
                                    <span className="text-sm font-bold text-gray-600 mb-1">{syll.text}</span>
                                    <span className={`text-xs font-black mb-2 ${syll.score >= 80 ? 'text-green-500' : 'text-orange-500'}`}>
                                      {Math.round(syll.score)}
                                    </span>
                                    
                                    {/* 음소 (Symbol 사용) */}
                                    {phones.length > 0 && (
                                      <div className="flex gap-1.5 pt-2 border-t border-gray-100 w-full justify-center">
                                        {phones.map((phone: any, pIdx: number) => {
                                          // JSON의 symbol 사용
                                          const displayChar = phone.symbol || phone.text || phone.label;
                                          
                                          return (
                                            <div key={pIdx} className="flex flex-col items-center">
                                              <span className="text-[10px] text-gray-500 mb-0.5 font-sans">{displayChar}</span>
                                              <span className={`text-[9px] font-bold ${phone.score >= 80 ? 'text-green-600' : 'text-orange-400'}`}>
                                                {Math.round(phone.score)}
                                              </span>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="p-6 pt-0 bg-white grid grid-cols-2 gap-4">
              <button 
                onClick={() => { setShowResultOverlay(false); setRecordingStatus('idle'); }} 
                className="h-16 bg-gray-100 text-gray-600 font-black rounded-2xl flex items-center justify-center gap-2 active:scale-95 transition-all"
              >
                <RotateCcw size={18} /> 다시 녹음
              </button>
              <button 
                onClick={() => moveToWord('next')} 
                className="h-16 bg-gray-900 text-white font-black rounded-2xl flex items-center justify-center gap-2 shadow-lg active:scale-95 transition-all"
              >
                다음 단어 <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}