"use client";

import React, { useState, useEffect } from 'react';
import { ChevronRight, Zap, BookOpen, CheckCircle, RefreshCcw, Loader2 } from 'lucide-react';
import Link from 'next/link';
import AuthGuard from '../components/AuthGuard';
import { getStudentStats } from '../api';

export default function StatsPage() {
  const [viewMode, setViewMode] = useState<'weekly' | 'monthly'>('weekly');
  const [stats, setStats] = useState({
    weeklyLearned: 0,
    streak: 0,
    accuracy: 0,
    weeklyTrend: [0, 0, 0, 0, 0, 0, 0],
    monthlyTrend: [], // 백엔드에서 주는 배열 길이에 따라 동적 할당
    proficiency: [
        { label: "학습 완료", value: 0, color: "bg-[#20385F]" },
        { label: "복습 필요", value: 0, color: "bg-[#FF8C1A]" },
        { label: "다시 학습", value: 0, color: "bg-[#20385F]/30" },
    ],
    message: "데이터를 불러오는 중..."
  });
  const [loading, setLoading] = useState(true);

  // 1. 현재 모드에 따른 데이터 선택
  const isWeekly = viewMode === 'weekly';
  const displayTrend = isWeekly ? stats.weeklyTrend : stats.monthlyTrend;
  
  // 2. 레이블 생성 로직 (달력 기준 1일~말일 대응)
  const labels = isWeekly 
    ? ['월', '화', '수', '목', '금', '토', '일'] 
    : Array.from({ length: displayTrend.length }, (_, i) => `${i + 1}`);

  // 3. 실제 데이터가 모두 0인지 확인
  const hasNoData = displayTrend.length === 0 || displayTrend.every(val => val === 0);
  
  // 4. 그래프 막대 높이 계산용 최댓값
  const maxTrendValue = Math.max(...(displayTrend.length > 0 ? displayTrend : [0]), 1);

  useEffect(() => {
    async function fetchData() {
      const userId = localStorage.getItem('userId');
      if (!userId) return;
      try {
        const data = await getStudentStats(userId);
        if (data) setStats(data);
      } catch (error) {
        console.error("통계 로드 실패:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  return (
    <AuthGuard allowedRoles={['student']}>
      <div className="flex flex-col min-h-full bg-gray-50 pb-24">
        {/* 헤더 */}
        <header className="h-16 flex items-center px-6 border-b border-gray-100 bg-white sticky top-0 z-10">
          <h1 className="text-lg font-bold ml-2 text-[#20385F]">통계</h1>
        </header>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="animate-spin text-gray-400" />
          </div>
        ) : (
          <main className="p-5 space-y-6">
            
            {/* 1. 이번 주 요약 */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100 relative overflow-hidden">
              <h2 className="text-lg font-black text-[#20385F] mb-4">이번 주 요약</h2>
              <div className="space-y-4 z-10 relative">
                <div className="flex justify-between items-center border-b border-gray-50 pb-2">
                  <span className="text-gray-500 font-bold text-sm">학습한 단어</span>
                  <span className="text-xl font-black text-[#20385F]">{stats.weeklyLearned}개</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-50 pb-2">
                  <span className="text-gray-500 font-bold text-sm">연속 학습</span>
                  <span className="text-xl font-black text-[#FF8C1A]">{stats.streak}일</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-bold text-sm">발음 정확도</span>
                  <span className="text-xl font-black text-[#20385F]">{stats.accuracy}%</span>
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-gray-100">
                <p className="text-center text-[#20385F] font-black text-sm flex items-center justify-center gap-2">
                  <CheckCircle size={16} className="text-[#FF8C1A]" />
                  {stats.message}
                </p>
              </div>
              <div className="absolute top-0 right-0 w-32 h-32 bg-[#20385F]/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 opacity-60"></div>
            </section>

            {/* 2. 학습 추이 (달력 기준 연동) */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100 relative overflow-hidden">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-black text-[#20385F]">학습 추이</h2>
                <div className="bg-gray-100 p-1 rounded-full flex text-[10px] font-bold">
                  <button 
                    onClick={() => setViewMode('weekly')}
                    className={`${isWeekly ? 'bg-white text-[#20385F] shadow-sm' : 'text-gray-400'} px-3 py-1 rounded-full transition-all`}
                  >
                    주간
                  </button>
                  <button 
                    onClick={() => setViewMode('monthly')}
                    className={`${!isWeekly ? 'bg-white text-[#20385F] shadow-sm' : 'text-gray-400'} px-3 py-1 rounded-full transition-all`}
                  >
                    월간
                  </button>
                </div>
              </div>
              
              <div className="relative h-44">
                {hasNoData && (
                  <div className="absolute inset-0 z-30 flex items-center justify-center">
                    <p className="text-xs text-gray-400 font-bold bg-white/90 px-4 py-2 rounded-full border border-gray-100 shadow-sm">
                      이번 {isWeekly ? "주" : "달"} 기록이 없습니다.
                    </p>
                  </div>
                )}

                {/* ✅ 2열 레이아웃: (왼쪽) Y축 라벨 / (오른쪽) 차트 */}
                <div className={`relative z-10 h-full grid grid-cols-[28px,1fr] gap-1 ${hasNoData ? "opacity-20" : "opacity-100"}`}>
                  {/* (A) Y축 라벨 전용 */}
                  <div className="flex flex-col justify-between pb-6">
                    {[maxTrendValue, Math.round(maxTrendValue * 0.75), Math.round(maxTrendValue * 0.5), Math.round(maxTrendValue * 0.25), 0].map(
                      (v, idx) => (
                        <div key={idx} className="h-px flex items-center">
                          <span
                            className="
                              w-full text-right text-[10px] font-bold text-gray-300 leading-none
                              -translate-x-2
                            "
                          >
                            {v}
                          </span>
                        </div>
                      )
                    )}
                  </div>

                  {/* (B) 차트 전용 (그리드라인 + 막대) */}
                  <div className="relative">
                    {/* ✅ 그리드라인: 차트 영역에만 깔기 */}
                    <div className="pointer-events-none absolute inset-0 flex flex-col justify-between pb-6">
                      {[0, 1, 2, 3, 4].map((k) => (
                        <div key={k} className="h-px w-full bg-gray-100" />
                      ))}
                    </div>

                    {/* ✅ 막대 영역 */}
                    {isWeekly ? (
                      <div className="relative z-10 h-full flex items-end justify-between gap-3 pb-6 px-0">
                        {displayTrend.map((count, i) => {
                          const heightPercentage = (count / maxTrendValue) * 100;
                          return (
                            <div key={i} className="flex-1 h-full flex flex-col items-center">
                              <div className="w-full flex-1 bg-gray-100 rounded-t-lg flex items-end relative overflow-hidden">
                                <div
                                  style={{ height: `${heightPercentage}%` }}
                                  className="w-full rounded-t-lg transition-all duration-700 ease-out bg-[#20385F]"
                                />
                              </div>
                              <div className="h-6 flex items-center justify-center">
                                <span className="text-[9px] font-bold text-gray-400">{labels[i]}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div
                        className="relative z-10 h-full grid items-end gap-1 pb-6 px-0"
                        style={{ gridTemplateColumns: `repeat(${displayTrend.length}, minmax(0, 1fr))` }}
                      >
                        {displayTrend.map((count, i) => {
                          const heightPercentage = (count / maxTrendValue) * 100;
                          const dayNumber = i + 1;
                          const isFiveStep = dayNumber % 5 === 0 || dayNumber === 1;

                          return (
                            <div key={i} className="h-full flex flex-col items-center">
                              <div className="w-full flex-1 bg-gray-100 rounded-t-md flex items-end relative overflow-hidden">
                                <div
                                  style={{ height: `${heightPercentage}%` }}
                                  className="w-full rounded-t-md transition-all duration-700 ease-out bg-[#20385F]"
                                />
                              </div>
                              <div className="h-6 flex items-center justify-center">
                                <span className={`text-[9px] font-bold ${isFiveStep ? "text-[#20385F]" : "text-gray-300"}`}>
                                  {isFiveStep ? labels[i] : ""}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </section>

            {/* 3. 단어 숙련도 */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100">
              <h2 className="text-lg font-black text-[#20385F] mb-6">단어 숙련도</h2>
              <div className="flex items-center gap-6">
                <div className="relative w-32 h-32 flex-shrink-0">
                  <svg viewBox="0 0 36 36" className="w-full h-full rotate-[-90deg]">
                    <path className="text-gray-100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5" />
                    <path 
                      className="text-[#FF8C1A] transition-all duration-1000 ease-out" 
                      strokeDasharray={`${stats.accuracy}, 100`} 
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                      fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" 
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-black text-[#20385F]">{stats.accuracy}%</span>
                    <span className="text-[9px] font-bold text-gray-400 uppercase">TOTAL</span>
                  </div>
                </div>

                <div className="flex-1 space-y-3">
                  {stats.proficiency.map((item) => (
                    <div key={item.label} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-2.5 h-2.5 rounded-full ${item.color}`}></div>
                        <span className="text-xs font-bold text-gray-600">{item.label}</span>
                      </div>
                      <span className="text-sm font-black text-[#20385F]">{item.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* 4. 추천 행동 */}
            <section className="space-y-4">
              <h2 className="text-lg font-black text-[#20385F] px-2">추천 행동</h2>
              <div className="grid grid-cols-2 gap-3">
                <Link href="/study/vocabulary?mode=review" className="block">
                  <div className="bg-[#FF8C1A]/10 p-5 rounded-3xl border border-[#FF8C1A]/20 hover:bg-[#FF8C1A]/15 transition-colors active:scale-[0.98] h-full">
                    <div className="bg-white w-10 h-10 rounded-full flex items-center justify-center mb-3 shadow-sm text-[#FF8C1A]">
                      <RefreshCcw size={20} />
                    </div>
                    <p className="font-black text-[#20385F] mb-1">오늘 복습하기</p>
                    <p className="text-xs font-bold text-[#FF8C1A]/80">틀린 단어 다시 보기</p>
                  </div>
                </Link>
                <Link href="/study/vocabulary" className="block">
                  <div className="bg-[#20385F]/5 p-5 rounded-3xl border border-[#20385F]/10 hover:bg-[#20385F]/10 transition-colors active:scale-[0.98] h-full">
                    <div className="bg-white w-10 h-10 rounded-full flex items-center justify-center mb-3 shadow-sm text-[#20385F]">
                      <BookOpen size={20} />
                    </div>
                    <p className="font-black text-[#20385F] mb-1">오늘 단어 학습</p>
                    <p className="text-xs font-bold text-[#20385F]/70">새로운 단어 배우기</p>
                  </div>
                </Link>
              </div>
            </section>

          </main>
        )}
      </div>
    </AuthGuard>
  );
}