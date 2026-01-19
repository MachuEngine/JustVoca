"use client";

import React from 'react';
import Link from 'next/link';
import { BarChart2, Home, Settings, TrendingUp, AlertCircle, ChevronRight } from 'lucide-react';

export default function StudentStats() {
  return (
    <div className="h-full flex flex-col bg-gray-50">
      
      {/* 헤더 */}
      <header className="h-16 flex items-center px-6 bg-white border-b border-gray-100">
        <h1 className="text-xl font-extrabold text-gray-900">학습 통계</h1>
      </header>

      <main className="flex-1 overflow-y-auto p-5 pb-24 space-y-6">
        
        {/* 1. 이번 주 요약 카드 */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-gray-500 font-bold mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-green-500" /> 이번 주 요약
          </h2>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-3 bg-gray-50 rounded-2xl">
              <div className="text-2xl font-black text-gray-900">84<span className="text-xs text-gray-400">개</span></div>
              <div className="text-[10px] text-gray-500 font-bold mt-1">학습 단어</div>
            </div>
            <div className="p-3 bg-gray-50 rounded-2xl">
              <div className="text-2xl font-black text-green-600">6<span className="text-xs text-gray-400">일</span></div>
              <div className="text-[10px] text-gray-500 font-bold mt-1">연속 학습</div>
            </div>
            <div className="p-3 bg-gray-50 rounded-2xl">
              <div className="text-2xl font-black text-blue-600">82<span className="text-xs text-gray-400">%</span></div>
              <div className="text-[10px] text-gray-500 font-bold mt-1">정확도</div>
            </div>
          </div>
          <div className="mt-4 bg-green-50 text-green-700 text-xs font-bold px-4 py-2 rounded-xl text-center">
            🎉 목표 달성까지 아주 조금 남았어요!
          </div>
        </div>

        {/* 2. 주간 그래프 (CSS로 간단 구현) */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <div className="flex justify-between items-end h-32 gap-3">
            {[40, 60, 30, 80, 100, 50, 70].map((h, i) => (
              <div key={i} className="flex-1 flex flex-col justify-end items-center gap-2 group">
                <div 
                  className={`w-full bg-gray-100 rounded-t-lg transition-all group-hover:bg-green-400 relative`} 
                  style={{ height: `${h}%` }}
                >
                  <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold text-gray-800 opacity-0 group-hover:opacity-100 transition-opacity">
                    {h}
                  </div>
                </div>
                <span className={`text-[10px] font-bold ${i === 4 ? 'text-black' : 'text-gray-300'}`}>
                  {['일','월','화','수','목','금','토'][i]}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 3. 약한 단어 (오답 노트) */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-gray-900 font-bold mb-4 flex justify-between items-center">
            <span>약한 단어 <span className="text-red-500 text-sm">5</span></span>
            <button className="text-xs text-gray-400 hover:text-gray-600">전체보기</button>
          </h2>
          <div className="space-y-3">
            {['복습', '필요', '다시', '학습', '어렵다'].map((word, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-red-50 rounded-xl">
                <div className="flex items-center gap-3">
                  <AlertCircle size={16} className="text-red-400" />
                  <span className="font-bold text-gray-800">{word}</span>
                </div>
                <button className="text-xs font-bold text-red-500 bg-white px-3 py-1.5 rounded-lg shadow-sm">
                  복습하기
                </button>
              </div>
            ))}
          </div>
        </div>

      </main>

      {/* 하단 탭바 (StudentHome과 동일) */}
      <nav className="absolute bottom-0 w-full bg-white border-t border-gray-100 h-20 flex justify-around items-center px-2 pb-2 rounded-t-3xl shadow-[0_-5px_20px_rgba(0,0,0,0.03)]">
        <Link href="/student_home">
          <button className="flex flex-col items-center gap-1 p-3 text-gray-400 hover:text-gray-600 transition-colors">
            <Home size={24} />
            <span className="text-[10px] font-medium">홈</span>
          </button>
        </Link>
        <button className="flex flex-col items-center gap-1 p-3 text-green-600">
          <BarChart2 size={24} strokeWidth={2.5} />
          <span className="text-[10px] font-bold">통계</span>
        </button>
        <button className="flex flex-col items-center gap-1 p-3 text-gray-400 hover:text-gray-600 transition-colors">
          <Settings size={24} />
          <span className="text-[10px] font-medium">설정</span>
        </button>
      </nav>
    </div>
  );
}