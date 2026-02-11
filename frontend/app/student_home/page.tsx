"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Play, Loader2, ChevronRight, Bell } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import AuthGuard from '../components/AuthGuard';
import { getUserProfile, getUserProgress, getStudentNotices, getStudentStats } from '../api';

export default function StudentHomePage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [userName, setUserName] = useState(""); 
  const [progress, setProgress] = useState(0); 
  const [userLevel, setUserLevel] = useState("level_beginner1"); 
  const [isNavigating, setIsNavigating] = useState(false);
  const [notices, setNotices] = useState<any[]>([]);
  const [weeklyAttendance, setWeeklyAttendance] = useState<number[]>([0,0,0,0,0,0,0]);

  useEffect(() => {
    const storedUserId = localStorage.getItem('userId');
    if (!storedUserId) return;

    const fetchData = async () => {
      try {
        // 1. 프로필 조회
        const profile = await getUserProfile(storedUserId);
        if (profile?.name) setUserName(profile.name);

        // 2. 진도율 및 레벨 매핑 (고급 1, 2 포함)
        const progressData = await getUserProgress(storedUserId);
        if (progressData) {
          const levelMap: { [key: string]: string } = {
            "초급 1": "level_beginner1",
            "초급 2": "level_beginner2",
            "중급 1": "level_intermediate1",
            "중급 2": "level_intermediate2",
            "고급 1": "level_advanced1",
            "고급 2": "level_advanced2",
          };
          setUserLevel(levelMap[progressData.level] || "level_beginner1");

          const current = progressData.current_page || 1;
          const calc = Math.min(100, Math.round(((current - 1) / 10) * 100));
          setProgress(calc);
        }

        // 3. 공지사항 조회
        const noticeData = await getStudentNotices();
        setNotices(noticeData || []);

        // 4. 주간 통계 조회
        const statsData = await getStudentStats(storedUserId);
        if (statsData && statsData.weeklyTrend) {
          setWeeklyAttendance(statsData.weeklyTrend);
        }

      } catch (error) {
        console.error("데이터 로드 실패:", error);
      }
    };
    fetchData();

    const handleFocus = () => fetchData();
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  const hasUnread = Array.isArray(notices) && notices.some((n: any) => !n.read);

  const handleStartLearning = () => {
    setIsNavigating(true);
    // 학습 페이지 이동 시 번역된 레벨 텍스트 전달
    router.push(`/study/vocabulary?level=${encodeURIComponent(t(userLevel))}`);
  };

  // 주간 캘린더 날짜 계산 로직
  const today = new Date();
  const currentDay = today.getDay();
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
        
        {/* 1. 상단 헤더 및 인사말 */}
        <div className="px-6 pt-8 mb-4 flex justify-between items-start">
          <div>
            <p className="text-md text-gray-400">
              {/* "안녕하세요," 부분 분리 (welcome_back 키 활용) */}
              {t('welcome_back', { name: '' }).split(',')[0]},
            </p>
            <h2 className="text-md font-bold text-[#20385F]">
              {t('welcome_back', { name: userName || t('nav_profile') })}
            </h2>
          </div>
          <button 
            onClick={() => router.push('/notices')}
            className="relative p-3 bg-gray-50 rounded-2xl border border-gray-100 active:scale-90 transition-transform"
          >
            <Bell size={24} className="text-[#20385F]" />
            {hasUnread && (
              <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-red-500 border-2 border-white rounded-full"></span>
            )}
          </button>
        </div>

        {/* 최신 공지 배너 */}
        {notices.length > 0 && (
          <section className="px-6 mb-6">
            <div 
              onClick={() => router.push('/notices')}
              className="bg-[#20385F]/5 p-4 rounded-2xl border border-[#20385F]/15 flex items-center justify-between group active:scale-[0.98] transition-all cursor-pointer"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="bg-[#20385F] text-white text-[8px] font-black px-1.5 py-0.5 rounded uppercase">{t('notice')}</span>
                </div>
                <p className="text-sm font-bold text-[#20385F] line-clamp-1">{notices[0].title}</p>
              </div>
              <ChevronRight size={18} className="text-[#20385F]/40 group-hover:translate-x-1 transition-transform" />
            </div>
          </section>
        )}

        {/* 2. 주간 출석 체크 (다국어 날짜 적용) */}
        <section className="px-6 mb-8">
          <div className="bg-gray-50 rounded-3xl p-5 border border-gray-100">
            <div className="flex justify-between items-center mb-5 px-1">
              <h3 className="font-black text-gray-800 text-sm">
                {today.getFullYear()}{t('year')} {today.getMonth() + 1}{t('month')}
              </h3>
              <span className="text-[10px] font-bold text-gray-300 uppercase tracking-widest">{t('weekly_progress')}</span>
            </div>
            <div className="flex justify-between items-center">
              {weekDays.map((date, idx) => {
                const count = weeklyAttendance[idx] || 0;
                const isAttended = count > 0;
                const isToday = date.getDate() === today.getDate();
                
                // 요일 다국어 키 배열
                const dayKeys = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
                const dayName = t(dayKeys[date.getDay()]);

                return (
                  <div key={idx} className="flex flex-col items-center gap-2">
                    <span className={`text-[10px] font-black ${isToday ? 'text-[#FF8C1A]' : 'text-gray-400'}`}>{dayName}</span>
                    <div className={`
                      w-9 h-9 flex items-center justify-center rounded-full text-xs font-black transition-all relative
                      ${isAttended 
                        ? 'bg-[#20385F] text-white shadow-md shadow-[#20385F]/30' 
                        : isToday 
                          ? 'bg-white border-2 border-[#FF8C1A] text-[#FF8C1A]' 
                          : 'bg-gray-200 text-gray-400 opacity-50' 
                      }
                    `}>
                      {isToday && !isAttended && (
                        <div className="absolute inset-0 border-2 border-[#FF8C1A] rounded-full animate-ping opacity-20"></div>
                      )}
                      {date.getDate()}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* 3. 학습 카드 (번역된 레벨 및 문구 적용) */}
        <section className="px-6 mb-8">
          <div className="bg-white rounded-[2.0rem] p-6 shadow-xl border border-gray-50 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#20385F]/5 rounded-bl-full -mr-10 -mt-10"></div>
            <div className="relative z-10">
              <div className="flex justify-between items-start mb-1">
                <span className="text-[13px] font-black px-3 py-1 rounded-full uppercase text-[#20385F]">{t(userLevel)}</span>
                <div className="text-right">
                  <span className="text-2xl font-black text-gray-900">{progress}%</span>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">{t('achievement_rate')}</p>
                </div>
              </div>
              <h4 className="text-lg font-black text-gray-900 mb-2">{t('daily_goal')}</h4>
              <div className="w-full h-2 bg-gray-100 rounded-full mb-4 overflow-hidden">
                <div className="h-full bg-[#FF8C1A] rounded-full transition-all duration-1000 ease-out" style={{ width: `${progress}%` }}></div>
              </div>
              <button 
                onClick={handleStartLearning} 
                disabled={isNavigating} 
                className="w-full h-12 bg-[#20385F] text-white font-black rounded-2xl text-lg flex items-center justify-center gap-3 active:scale-[0.97] transition-all shadow-lg disabled:opacity-70"
              >
                {isNavigating ? <Loader2 size={20} className="animate-spin" /> : <><Play size={20} fill="currentColor" /><span>{t('start_study_btn')}</span></>}
              </button>
            </div>
          </div>
        </section>

        {/* 4. 광고 배너 (내부 문구 다국어화) */}
        <div className="px-6 mb-6">
          <a href="https://mediazen.ngrok.app/" target="_blank" rel="noopener noreferrer" className="block w-full max-w-xl mx-auto relative h-24 rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 group active:scale-[0.98]">
            <Image src="/assets/images/student_home_banner_onui.png" alt="Ad Banner" fill style={{ objectFit: 'cover' }} className="group-hover:scale-105 transition-transform duration-700" priority />
            <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent"></div>
            <div className="absolute inset-0 px-5 flex items-center justify-between">
              <div className="flex flex-col gap-0.5">
                <span className="bg-[#FF8C1A]/90 text-white text-[9px] font-black px-1.5 py-0.5 rounded w-fit uppercase tracking-wider mb-1">AD</span>
                <h3 className="text-white font-black text-lg leading-tight drop-shadow-md">오누이 한국어</h3>
                <p className="text-white/80 text-[10px] font-medium drop-shadow-sm">Learning Korean is fun</p>
              </div>
              <div className="bg-white/90 backdrop-blur-sm text-gray-900 text-[11px] font-black px-3 py-2 rounded-xl flex items-center gap-1 shadow-sm group-hover:bg-white transition-colors">
                {t('next_step')} <ChevronRight size={12} strokeWidth={3} />
              </div>
            </div>
          </a>
        </div>
      </div>
    </AuthGuard>
  );
}