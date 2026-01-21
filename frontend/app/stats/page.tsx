"use client";

import React, { useState, useEffect } from 'react';
import { ChevronRight, Zap, BookOpen, CheckCircle, RefreshCcw, Loader2 } from 'lucide-react';
import Link from 'next/link';
import AuthGuard from '../components/AuthGuard';
import { getStudentStats } from '../api'; // 2단계에서 만든 함수 임포트

export default function StatsPage() {
  // 통계 데이터 상태 관리 (초기값은 0으로 설정)
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

  // 화면이 켜질 때 백엔드에서 데이터 가져오기
  useEffect(() => {
    async function fetchData() {
      const userId = localStorage.getItem('userId');
      if (!userId) return;
      try {
        const data = await getStudentStats(userId);
        setStats(data);
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
            
            {/* 1. 이번 주 요약 (사양서: 이번 주 요약) */}
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
              
              {/* 배경 데코레이션 (흐릿한 원) */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-green-50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 opacity-50"></div>
            </section>

            {/* 2. 학습 추이 (사양서: 학습 추이 막대 그래프) */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-black text-gray-900">학습 추이</h2>
                {/* 주간/월간 토글 버튼 (모양만 구현) */}
                <div className="bg-gray-100 p-1 rounded-full flex text-[10px] font-bold">
                  <button className="bg-white text-gray-900 px-3 py-1 rounded-full shadow-sm">주간</button>
                  <button className="text-gray-400 px-3 py-1">월간</button>
                </div>
              </div>
              
              <div className="flex items-end justify-between h-32 gap-3 px-2">
                {['월','화','수','목','금','토','일'].map((day, i) => (
                  <div key={day} className="flex-1 flex flex-col items-center gap-2">
                    {/* 막대 그래프 */}
                    <div className="w-full bg-gray-100 rounded-t-lg h-full flex items-end relative overflow-hidden">
                      <div 
                        style={{ height: `${stats.weeklyTrend[i]}%` }} 
                        className={`w-full rounded-t-lg transition-all duration-1000 ${stats.weeklyTrend[i] > 0 ? 'bg-green-500' : 'bg-transparent'}`}
                      ></div>
                    </div>
                    <span className="text-[10px] font-bold text-gray-400">{day}</span>
                  </div>
                ))}
              </div>
            </section>

            {/* 3. 단어 숙련도 (사양서: 도넛 차트 및 분포) */}
            <section className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100">
              <h2 className="text-lg font-black text-gray-900 mb-6">단어 숙련도</h2>
              <div className="flex items-center gap-6">
                {/* 도넛 그래프 (SVG 활용) */}
                <div className="relative w-32 h-32 flex-shrink-0">
                  <svg viewBox="0 0 36 36" className="w-full h-full rotate-[-90deg]">
                    {/* 회색 배경 원 */}
                    <path className="text-gray-100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5" />
                    {/* 초록색 데이터 원 */}
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

                {/* 숙련도 범례 */}
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

            {/* 4. 추천 행동 (사양서: 약한 단어 & 추천 행동 버튼) */}
            <section className="space-y-4">
              <div className="flex items-center justify-between px-2">
                <h2 className="text-lg font-black text-gray-900">추천 행동</h2>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                {/* 복습하기 버튼 */}
                <Link href="/study/vocabulary?mode=review" className="block h-full">
                  <div className="bg-orange-50 p-5 rounded-3xl border border-orange-100 hover:bg-orange-100 transition-colors active:scale-[0.98] h-full flex flex-col justify-between cursor-pointer">
                    <div className="bg-white w-10 h-10 rounded-full flex items-center justify-center mb-3 shadow-sm text-orange-500">
                      <RefreshCcw size={20} />
                    </div>
                    <div>
                      <p className="font-black text-gray-900 mb-1">오늘 복습하기</p>
                      <p className="text-xs font-bold text-orange-600/80">틀린 단어 다시 보기</p>
                    </div>
                  </div>
                </Link>

                {/* 새 학습 버튼 */}
                <Link href="/study/vocabulary" className="block h-full">
                  <div className="bg-blue-50 p-5 rounded-3xl border border-blue-100 hover:bg-blue-100 transition-colors active:scale-[0.98] h-full flex flex-col justify-between cursor-pointer">
                    <div className="bg-white w-10 h-10 rounded-full flex items-center justify-center mb-3 shadow-sm text-blue-500">
                      <BookOpen size={20} />
                    </div>
                    <div>
                      <p className="font-black text-gray-900 mb-1">오늘 단어 학습</p>
                      <p className="text-xs font-bold text-blue-600/80">새로운 단어 배우기</p>
                    </div>
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