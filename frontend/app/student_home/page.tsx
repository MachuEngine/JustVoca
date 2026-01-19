"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { 
  Play, 
  MessageCircle,
  Loader2,
  // [추가] 광고 배너 화살표 아이콘
  ChevronRight
} from 'lucide-react';

export default function StudentHomePage() {
  const router = useRouter();
  const userName = "안종민"; 

  const [progress, setProgress] = useState(0); // 사양서 초기 달성률 0%
  const [userLevel, setUserLevel] = useState("초급 1");
  const [isNavigating, setIsNavigating] = useState(false);

  const handleStartLearning = async () => {
    setIsNavigating(true);
    // const data = await getUserProgress(USER_ID);
    setTimeout(() => {
      router.push(`/study/vocabulary`);
    }, 500);
  };

  const today = new Date();
  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - d.getDay() + i); 
    return d;
  });

  return (
    <div className="flex flex-col min-h-full bg-white relative pb-24">
      
      {/* 1. 인사말 및 공지함 */}
      <div className="px-6 pt-8 mb-6 flex justify-between items-start">
        <div>
          <p className="text-sm text-gray-400 font-bold mb-1 uppercase">Welcome</p>
          <h2 className="text-2xl font-black text-gray-900 leading-tight">
            안녕하세요, <br />
            <span className="text-green-600">{userName}</span> 님! 👋
          </h2>
        </div>
      </div>

      {/* 2. 주간 출석 체크 */}
      <section className="px-6 mb-8">
        <div className="bg-gray-50 rounded-3xl p-5 border border-gray-100">
          <div className="flex justify-between items-center mb-5 px-1">
            <h3 className="font-black text-gray-800 text-sm">2026년 1월</h3>
            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-widest">Attendance</span>
          </div>
          
          <div className="flex justify-between items-center">
            {weekDays.map((date, idx) => {
              const isToday = date.getDate() === today.getDate();
              const isPast = date < today && !isToday;
              
              return (
                <div key={idx} className="flex flex-col items-center gap-2">
                  <span className="text-[10px] text-gray-400 font-black">
                    {['일','월','화','수','목','금','토'][date.getDay()]}
                  </span>
                  <div className={`
                    w-9 h-9 flex items-center justify-center rounded-full text-xs font-black transition-all relative
                    ${isToday 
                      ? 'text-green-600 bg-white border-2 border-green-600 shadow-sm' 
                      : isPast 
                        ? 'bg-green-100 text-green-700 opacity-60' 
                        : 'bg-transparent text-gray-300'
                    }
                  `}>
                    {isToday && (
                        <div className="absolute inset-0 border-2 border-green-600 rounded-full animate-ping opacity-20"></div>
                    )}
                    {date.getDate()}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 3. 학습 카드 및 달성률 */}
      <section className="px-6 mb-8">
        <div className="bg-white rounded-[2.5rem] p-8 shadow-xl border border-gray-50 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-green-50 rounded-bl-full -mr-10 -mt-10"></div>
          
          <div className="relative z-10">
            <div className="flex justify-between items-start mb-6">
              <span className="bg-green-100 text-green-700 text-[10px] font-black px-3 py-1 rounded-full uppercase">
                {userLevel}
              </span>
              <div className="text-right">
                <span className="text-3xl font-black text-gray-900">{progress}%</span>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Achievement</p>
              </div>
            </div>

            <h4 className="text-xl font-black text-gray-900 mb-2">오늘의 단어 학습 시작</h4>
            <div className="w-full h-3 bg-gray-100 rounded-full mb-8 overflow-hidden">
              <div 
                className="h-full bg-green-500 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <button 
              onClick={handleStartLearning}
              disabled={isNavigating}
              className="w-full h-16 bg-gray-900 text-white font-black rounded-2xl text-lg flex items-center justify-center gap-3 active:scale-[0.97] transition-all shadow-lg disabled:opacity-70"
            >
              {isNavigating ? <Loader2 size={20} className="animate-spin" /> : <><Play size={20} fill="currentColor" /><span>학습 시작</span></>}
            </button>
          </div>
        </div>
      </section>

      {/* 4. 광고 배너 */}
      <div className="px-6 mb-6">
        <a 
          href="https://mediazen.ngrok.app/" 
          target="_blank" 
          rel="noopener noreferrer"
          // h-28에서 h-24로 높이를 줄여 전체적인 부피감을 감소시켰습니다.
          // max-w-md와 mx-auto를 추가해 가로 폭이 너무 넓어지지 않게 조절 가능합니다.
          className="block w-full max-w-xl mx-auto relative h-24 rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 group active:scale-[0.98]"
        >
          {/* 배경 이미지 */}
          <Image
            src="/assets/images/student_home_banner_onui.png" 
            alt="오누이 한국어 광고"
            fill
            style={{ objectFit: 'cover' }} // 이미지 비율을 유지하며 영역을 채움
            className="group-hover:scale-105 transition-transform duration-700" 
            priority
          />
          
          {/* 그라데이션 오버레이 - 높이가 낮아진 만큼 더 얇게 조정 */}
          <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent"></div>

          {/* 콘텐츠 레이어 */}
          <div className="absolute inset-0 px-5 flex items-center justify-between">
            <div className="flex flex-col gap-0.5">
              <span className="bg-blue-500/90 text-white text-[9px] font-black px-1.5 py-0.5 rounded w-fit uppercase tracking-wider mb-1">
                AD
              </span>
              <h3 className="text-white font-black text-lg leading-tight drop-shadow-md">
                오누이 한국어
              </h3>
              <p className="text-white/80 text-[10px] font-medium drop-shadow-sm">
                재미있는 한국어 학습의 시작! 🚀
              </p>
            </div>

            {/* 바로가기 버튼 - 더 작고 심플하게 수정 */}
            <div className="bg-white/90 backdrop-blur-sm text-gray-900 text-[11px] font-black px-3 py-2 rounded-xl flex items-center gap-1 shadow-sm group-hover:bg-white transition-colors">
              바로가기 <ChevronRight size={12} strokeWidth={3} />
            </div>
          </div>
        </a>
      </div>

      {/* 5. 플로팅 챗봇 */}
      <div className="fixed bottom-24 right-6 z-[60]">
        <button className="w-14 h-14 bg-gray-900 text-white rounded-full shadow-2xl flex items-center justify-center hover:scale-110 active:scale-95 transition-transform">
          <MessageCircle size={24} fill="currentColor" />
        </button>
      </div>

    </div>
  );
}