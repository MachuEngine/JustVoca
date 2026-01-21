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
        { label: "완전 암기", value: 0, color: "bg-green-500" },
        { label: "복습 필요", value: 0, color: "bg-orange-400" },
        { label: "다시 학습", value: 0, color: "bg-red-400" },
    ],
    message: "데이터를 불러오는 중..."
  });
  const [loading, setLoading] = useState(true);

  // [추가] 배경에 깔아둘 임시 그래프 데이터
  const dummyTrend = [40, 70, 45, 90, 65, 80, 30];
  // 실제 데이터가 모두 0이면 더미 데이터를 배경으로 사용
  const hasNoData = stats.weeklyTrend.every(val => val === 0);
  const trendDisplayData = hasNoData ? dummyTrend : stats.weeklyTrend;

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
        <div className="bg-white px-6 py-5 border-b border-gray-100 sticky top-0 z-10">
          <h1 className="text-xl font-black text-gray-900">통계</h1>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="animate-spin text-gray-400" />
          </div>
        ) : (
          <main className="p-5 space-y-6">
            
            {/* 1. 이번 주 요약 */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100 relative overflow-hidden">
              <h2 className="text-lg font-black text-gray-900 mb-4">이번 주 요약</h2>
              <div className="space-y-4 z-10 relative">
                <div className="flex justify-between items-center border-b border-gray-50 pb-2">
                  <span className="text-gray-500 font-bold text-sm">학습한 단어</span>
                  <span className="text-xl font-black text-gray-900">{stats.weeklyLearned}개</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-50 pb-2">
                  <span className="text-gray-500 font-bold text-sm">연속 학습</span>
                  <span className="text-xl font-black text-orange-500">{stats.streak}일</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-bold text-sm">발음 정확도</span>
                  <span className="text-xl font-black text-blue-600">{stats.accuracy}%</span>
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-gray-100">
                <p className="text-center text-green-600 font-black text-sm flex items-center justify-center gap-2">
                  <CheckCircle size={16} />
                  {stats.message}
                </p>
              </div>
              <div className="absolute top-0 right-0 w-32 h-32 bg-green-50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 opacity-50"></div>
            </section>

            {/* 2. 학습 추이 (준비중 오버레이 적용) */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100 relative overflow-hidden">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-black text-gray-900">학습 추이</h2>
                <div className="bg-gray-100 p-1 rounded-full flex text-[10px] font-bold opacity-50">
                  <button className="bg-white text-gray-900 px-3 py-1 rounded-full shadow-sm cursor-default">주간</button>
                  <button className="text-gray-400 px-3 py-1 cursor-default">월간</button>
                </div>
              </div>
              
              <div className="relative h-40"> {/* 높이 고정으로 안정감 부여 */}
                {/* [준비중 오버레이] - 블러 효과와 투명도 최적화 */}
                <div className="absolute inset-0 z-20 flex items-center justify-center">
                  {/* bg-white/30과 블러를 조합하여 유리 느낌 극대화 */}
                  <div className="absolute inset-0 bg-white/30 backdrop-blur-[2px] rounded-xl"></div>
                  
                  <div className="relative z-30 bg-white/95 px-6 py-3 rounded-2xl shadow-xl border border-gray-100 flex flex-col items-center gap-1.5 shadow-orange-100/50">
                    <div className="flex items-center gap-2">
                      <span className="flex h-2.5 w-2.5 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-orange-500"></span>
                      </span>
                      <span className="text-[15px] font-black text-gray-800 tracking-tight">통계 기능 준비 중</span>
                    </div>
                    <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Analysing Data Soon</p>
                  </div>
                </div>

                {/* [배경 그래프 영역] - 투명도를 20에서 60으로 높이고 색상을 진하게 변경 */}
                <div className="flex items-end justify-between h-32 gap-3 px-2 opacity-60 pointer-events-none">
                  {['월','화','수','목','금','토','일'].map((day, i) => (
                    <div key={day} className="flex-1 flex flex-col items-center gap-2 h-full">
                      {/* 막대기 배경을 조금 더 진한 회색(gray-200)으로 */}
                      <div className="w-full bg-gray-200 rounded-t-lg h-full flex items-end relative overflow-hidden">
                        <div 
                          style={{ height: `${trendDisplayData[i]}%` }} 
                          className="w-full rounded-t-lg bg-gray-400" // 막대 색상을 더 뚜렷하게
                        ></div>
                      </div>
                      {/* 요일 텍스트 색상을 더 진하게(gray-500) */}
                      <span className="text-[10px] font-bold text-gray-500">{day}</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* 3. 단어 숙련도 */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100">
              <h2 className="text-lg font-black text-gray-900 mb-6">단어 숙련도</h2>
              <div className="flex items-center gap-6">
                <div className="relative w-32 h-32 flex-shrink-0">
                  <svg viewBox="0 0 36 36" className="w-full h-full rotate-[-90deg]">
                    <path className="text-gray-100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5" />
                    <path 
                      className="text-green-500 transition-all duration-1000 ease-out" 
                      strokeDasharray={`${stats.accuracy}, 100`} 
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                      fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" 
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-black text-gray-900">{stats.accuracy}%</span>
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
                      <span className="text-sm font-black text-gray-900">{item.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* 4. 추천 행동 */}
            <section className="space-y-4">
              <h2 className="text-lg font-black text-gray-900 px-2">추천 행동</h2>
              <div className="grid grid-cols-2 gap-3">
                <Link href="/study/vocabulary?mode=review" className="block">
                  <div className="bg-orange-50 p-5 rounded-3xl border border-orange-100 hover:bg-orange-100 transition-colors active:scale-[0.98] h-full">
                    <div className="bg-white w-10 h-10 rounded-full flex items-center justify-center mb-3 shadow-sm text-orange-500">
                      <RefreshCcw size={20} />
                    </div>
                    <p className="font-black text-gray-900 mb-1">오늘 복습하기</p>
                    <p className="text-xs font-bold text-orange-600/80">틀린 단어 다시 보기</p>
                  </div>
                </Link>
                <Link href="/study/vocabulary" className="block">
                  <div className="bg-blue-50 p-5 rounded-3xl border border-blue-100 hover:bg-blue-100 transition-colors active:scale-[0.98] h-full">
                    <div className="bg-white w-10 h-10 rounded-full flex items-center justify-center mb-3 shadow-sm text-blue-500">
                      <BookOpen size={20} />
                    </div>
                    <p className="font-black text-gray-900 mb-1">오늘 단어 학습</p>
                    <p className="text-xs font-bold text-blue-600/80">새로운 단어 배우기</p>
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