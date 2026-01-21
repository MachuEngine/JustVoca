"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Play, MessageCircle, Loader2, ChevronRight, Bell } from 'lucide-react';
import AuthGuard from '../components/AuthGuard';
// [수정] getStudentStats 추가 임포트
import { getUserProfile, getUserProgress, getStudentNotices, getStudentStats } from '../api';

export default function StudentHomePage() {
  const router = useRouter();
  const [userName, setUserName] = useState("학습자"); 
  const [progress, setProgress] = useState(0); 
  const [userLevel, setUserLevel] = useState("초급 1");
  const [isNavigating, setIsNavigating] = useState(false);
  const [notices, setNotices] = useState<any[]>([]);
  
  // [추가] 주간 출석 데이터 상태 (월~일)
  const [weeklyAttendance, setWeeklyAttendance] = useState<number[]>([0,0,0,0,0,0,0]);

  useEffect(() => {
    const storedUserId = localStorage.getItem('userId');
    if (!storedUserId) return;

    const fetchData = async () => {
      try {
        // 1. 프로필
        const profile = await getUserProfile(storedUserId);
        if (profile?.name) setUserName(profile.name);

        // 2. 진도율 (페이지 단위)
        const progressData = await getUserProgress(storedUserId);
        if (progressData) {
          setUserLevel(progressData.level || "초급 1");
          // 1페이지(0%) ~ 11페이지(100%) 기준 계산
          const current = progressData.current_page || 1;
          const calc = Math.min(100, Math.round(((current - 1) / 10) * 100));
          setProgress(calc);
        }

        // 3. 공지사항
        const noticeData = await getStudentNotices();
        setNotices(noticeData || []);

        // 4. [추가] 통계 API를 호출하여 "실제 출석(학습) 여부" 가져오기
        const statsData = await getStudentStats(storedUserId);
        if (statsData && statsData.weeklyTrend) {
          setWeeklyAttendance(statsData.weeklyTrend); // [0, 1, 0...] 형태의 학습 빈도 배열
        }

      } catch (error) {
        console.error("데이터 로드 실패:", error);
      }
    };
    fetchData();
  }, []);

  const handleStartLearning = () => {
    setIsNavigating(true);
    router.push(`/study/vocabulary?level=${encodeURIComponent(userLevel)}`);
  };

  // 이번 주 날짜 계산 (월요일 시작 ~ 일요일 끝)
  const today = new Date();
  const currentDay = today.getDay(); // 0(일) ~ 6(토)
  // 한국식 달력(월~일) 순서로 정렬하기 위한 로직
  // getDay(): 일(0), 월(1), 화(2), 수(3), 목(4), 금(5), 토(6)
  // 배열 인덱스: 월(0), 화(1), 수(2), 목(3), 금(4), 토(5), 일(6)
  
  // 오늘 날짜 기준으로 이번 주의 월요일 날짜 구하기
  const mondayOffset = currentDay === 0 ? -6 : 1 - currentDay; 
  const mondayDate = new Date(today);
  mondayDate.setDate(today.getDate() + mondayOffset);

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(mondayDate);
    d.setDate(mondayDate.getDate() + i);
    return d;
  });

  return (
    <AuthGuard allowedRoles={['student']}>
      <div className="flex flex-col min-h-full bg-white relative pb-24">
        
        {/* 1. 인사말 및 공지 알림 */}
        <div className="px-6 pt-8 mb-4 flex justify-between items-start">
          <div>
            <p className="text-sm text-gray-400 font-bold mb-1 uppercase">Welcome</p>
            <h2 className="text-2xl font-black text-gray-900 leading-tight">
              안녕하세요, <br />
              <span className="text-green-600">{userName}</span> 님! 👋
            </h2>
          </div>
          <button 
            onClick={() => router.push('/notices')}
            className="relative p-3 bg-gray-50 rounded-2xl border border-gray-100 active:scale-90 transition-transform"
          >
            <Bell size={24} className="text-gray-700" />
            {notices.length > 0 && (
              <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-red-500 border-2 border-white rounded-full"></span>
            )}
          </button>
        </div>

        {/* 최신 공지 배너 */}
        {notices.length > 0 && (
          <section className="px-6 mb-6">
            <div 
              onClick={() => router.push('/notices')}
              className="bg-indigo-50 p-4 rounded-2xl border border-indigo-100 flex items-center justify-between group active:scale-[0.98] transition-all cursor-pointer"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="bg-indigo-500 text-white text-[8px] font-black px-1.5 py-0.5 rounded uppercase">Notice</span>
                </div>
                <p className="text-sm font-bold text-indigo-900 line-clamp-1">{notices[0].title}</p>
              </div>
              <ChevronRight size={18} className="text-indigo-300 group-hover:translate-x-1 transition-transform" />
            </div>
          </section>
        )}

        {/* 2. 주간 출석 체크 (실제 데이터 연동) */}
        <section className="px-6 mb-8">
          <div className="bg-gray-50 rounded-3xl p-5 border border-gray-100">
            <div className="flex justify-between items-center mb-5 px-1">
              <h3 className="font-black text-gray-800 text-sm">
                {today.getFullYear()}년 {today.getMonth() + 1}월
              </h3>
              <span className="text-[10px] font-bold text-gray-300 uppercase tracking-widest">weekly calendar</span>
            </div>
            <div className="flex justify-between items-center">
              {weekDays.map((date, idx) => {
                // weeklyAttendance[0] = 월요일 학습량, ... [6] = 일요일
                // idx 0 = 월요일 ... idx 6 = 일요일
                const count = weeklyAttendance[idx] || 0;
                const isAttended = count > 0;
                const isToday = date.getDate() === today.getDate();
                
                // 날짜 표시 (일, 월, 화...)
                const dayName = ['일','월','화','수','목','금','토'][date.getDay()];

                return (
                  <div key={idx} className="flex flex-col items-center gap-2">
                    <span className={`text-[10px] font-black ${isToday ? 'text-green-600' : 'text-gray-400'}`}>{dayName}</span>
                    <div className={`
                      w-9 h-9 flex items-center justify-center rounded-full text-xs font-black transition-all relative
                      ${isAttended 
                        ? 'bg-green-500 text-white shadow-md shadow-green-200' // 출석함 (진한 초록)
                        : isToday 
                          ? 'bg-white border-2 border-green-500 text-green-600' // 오늘인데 아직 안함 (테두리)
                          : 'bg-gray-200 text-gray-400 opacity-50' // 결석/미래 (회색)
                      }
                    `}>
                      {/* 오늘 날짜 강조 효과 */}
                      {isToday && !isAttended && (
                        <div className="absolute inset-0 border-2 border-green-500 rounded-full animate-ping opacity-20"></div>
                      )}
                      {date.getDate()}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* 3. 학습 카드 */}
        <section className="px-6 mb-8">
          <div className="bg-white rounded-[2.5rem] p-8 shadow-xl border border-gray-50 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-green-50 rounded-bl-full -mr-10 -mt-10"></div>
            <div className="relative z-10">
              <div className="flex justify-between items-start mb-6">
                <span className="bg-green-100 text-green-700 text-[10px] font-black px-3 py-1 rounded-full uppercase">{userLevel}</span>
                <div className="text-right">
                  <span className="text-3xl font-black text-gray-900">{progress}%</span>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Achievement</p>
                </div>
              </div>
              <h4 className="text-xl font-black text-gray-900 mb-2">오늘의 단어 학습 시작</h4>
              <div className="w-full h-3 bg-gray-100 rounded-full mb-8 overflow-hidden">
                <div className="h-full bg-green-500 rounded-full transition-all duration-1000 ease-out" style={{ width: `${progress}%` }}></div>
              </div>
              <button onClick={handleStartLearning} disabled={isNavigating} className="w-full h-16 bg-gray-900 text-white font-black rounded-2xl text-lg flex items-center justify-center gap-3 active:scale-[0.97] transition-all shadow-lg disabled:opacity-70">
                {isNavigating ? <Loader2 size={20} className="animate-spin" /> : <><Play size={20} fill="currentColor" /><span>학습 시작</span></>}
              </button>
            </div>
          </div>
        </section>

        {/* 4. 광고 배너 */}
        <div className="px-6 mb-6">
          <a href="https://mediazen.ngrok.app/" target="_blank" rel="noopener noreferrer" className="block w-full max-w-xl mx-auto relative h-24 rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 group active:scale-[0.98]">
            <Image src="/assets/images/student_home_banner_onui.png" alt="오누이 한국어 광고" fill style={{ objectFit: 'cover' }} className="group-hover:scale-105 transition-transform duration-700" priority />
            <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent"></div>
            <div className="absolute inset-0 px-5 flex items-center justify-between">
              <div className="flex flex-col gap-0.5">
                <span className="bg-blue-500/90 text-white text-[9px] font-black px-1.5 py-0.5 rounded w-fit uppercase tracking-wider mb-1">AD</span>
                <h3 className="text-white font-black text-lg leading-tight drop-shadow-md">오누이 한국어</h3>
                <p className="text-white/80 text-[10px] font-medium drop-shadow-sm">재미있는 한국어 학습의 시작! 🚀</p>
              </div>
              <div className="bg-white/90 backdrop-blur-sm text-gray-900 text-[11px] font-black px-3 py-2 rounded-xl flex items-center gap-1 shadow-sm group-hover:bg-white transition-colors">바로가기 <ChevronRight size={12} strokeWidth={3} /></div>
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
    </AuthGuard>
  );
}