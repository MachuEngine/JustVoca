"use client";

import React, { useState, useEffect } from 'react';
import { ChevronRight, Zap, BookOpen, CheckCircle, RefreshCcw, Loader2 } from 'lucide-react';
import Link from 'next/link';
import AuthGuard from '../components/AuthGuard';
import { getStudentStats } from '../api';

export default function StatsPage() {
  const [stats, setStats] = useState({
    weeklyLearned: 0,
    streak: 0,
    accuracy: 0,
    weeklyTrend: [0, 0, 0, 0, 0, 0, 0],
    proficiency: [
        { label: "학습 완료", value: 0, color: "bg-[#20385F]" },
        { label: "복습 필요", value: 0, color: "bg-[#FF8C1A]" },
        { label: "다시 학습", value: 0, color: "bg-[#20385F]/30" },
    ],
    message: "데이터를 불러오는 중..."
  });
  const [loading, setLoading] = useState(true);

  // 실제 데이터가 모두 0인지 확인
  const hasNoData = stats.weeklyTrend.every(val => val === 0);
  
  // 그래프 막대 높이 계산을 위한 기준값 (최소 1로 설정하여 0 나누기 방지)
  const maxTrendValue = Math.max(...stats.weeklyTrend, 1);

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

            {/* 2. 학습 추이 (실제 데이터 연동 완료) */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100 relative overflow-hidden">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-black text-[#20385F]">학습 추이</h2>
                <div className="bg-gray-100 p-1 rounded-full flex text-[10px] font-bold">
                  <button className="bg-white text-[#20385F] px-3 py-1 rounded-full shadow-sm">주간</button>
                  <button className="text-gray-400 px-3 py-1 cursor-default opacity-50">월간</button>
                </div>
              </div>
              
              <div className="relative h-40">
                {/* 데이터가 아예 없을 때만 안내 표시 */}
                {hasNoData && (
                  <div className="absolute inset-0 z-20 flex items-center justify-center">
                    <p className="text-xs text-gray-400 font-bold bg-white/90 px-4 py-2 rounded-full border border-gray-100 shadow-sm">
                      이번 주 학습 기록이 없습니다.
                    </p>
                  </div>
                )}

                <div className={`flex items-end justify-between h-32 gap-3 px-2 transition-all duration-500 ${hasNoData ? 'opacity-20' : 'opacity-100'}`}>
                  {['월','화','수','목','금','토','일'].map((day, i) => {
                    // 백엔드 데이터(stats.weeklyTrend) 기반 높이 계산
                    const count = stats.weeklyTrend[i] || 0;
                    const heightPercentage = (count / maxTrendValue) * 100;

                    return (
                      <div key={day} className="flex-1 flex flex-col items-center gap-2 h-full">
                        <div className="w-full bg-gray-100 rounded-t-lg h-full flex items-end relative overflow-hidden">
                          <div 
                            style={{ height: `${heightPercentage}%` }} 
                            className="w-full rounded-t-lg bg-[#20385F] transition-all duration-1000 ease-out"
                          >
                            {count > 0 && (
                              <span className="absolute top-1 left-1/2 -translate-x-1/2 text-[8px] font-black text-white">
                                {count}
                              </span>
                            )}
                          </div>
                        </div>
                        <span className="text-[10px] font-bold text-gray-500">{day}</span>
                      </div>
                    );
                  })}
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