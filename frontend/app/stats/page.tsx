"use client";

import React from 'react';
import { BarChart, PieChart, ArrowRight, Zap, Target, Flame } from 'lucide-react';

export default function StatsPage() {
  // 사양서 기반 통계 데이터 [cite: 130-133, 143]
  const statsSummary = {
    learnedWords: 84, // [cite: 131]
    streak: 6, // [cite: 132]
    accuracy: 82, // [cite: 133]
  };

  const proficiency = [
    { label: "완전 암기", value: 45, color: "bg-green-500" }, // 
    { label: "복습 필요", value: 35, color: "bg-orange-400" }, // 
    { label: "다시 학습", value: 20, color: "bg-red-400" }, // 
  ];

  return (
    <div className="flex flex-col min-h-full bg-gray-50 pb-10">
      {/* 상단 타이틀 */}
      <div className="bg-white px-6 py-6 border-b border-gray-100">
        <h1 className="text-2xl font-black text-gray-900">통계</h1>
      </div>

      {/* 1. 이번 주 요약 [cite: 130] */}
      <section className="p-4 grid grid-cols-3 gap-3">
        <div className="bg-white p-4 rounded-3xl shadow-sm border border-gray-100 text-center">
          <p className="text-[10px] font-bold text-gray-400 mb-1 uppercase">Words</p>
          <p className="text-xl font-black text-green-600">{statsSummary.learnedWords}</p>
        </div>
        <div className="bg-white p-4 rounded-3xl shadow-sm border border-gray-100 text-center">
          <p className="text-[10px] font-bold text-gray-400 mb-1 uppercase">Streak</p>
          <p className="text-xl font-black text-orange-500">{statsSummary.streak}일</p>
        </div>
        <div className="bg-white p-4 rounded-3xl shadow-sm border border-gray-100 text-center">
          <p className="text-[10px] font-bold text-gray-400 mb-1 uppercase">Acc.</p>
          <p className="text-xl font-black text-blue-600">{statsSummary.accuracy}%</p>
        </div>
      </section>

      {/* 2. 학습 추이 (막대 그래프) [cite: 135-137] */}
      <section className="px-4 mb-6">
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-black text-gray-800">학습 추이</h3>
            <div className="flex bg-gray-100 rounded-full p-1 scale-90">
              <button className="px-3 py-1 bg-white rounded-full text-xs font-bold shadow-sm">주간</button>
              <button className="px-3 py-1 text-xs font-bold text-gray-400">월간</button>
            </div>
          </div>
          {/* 가상 막대 그래프 */}
          <div className="flex items-end justify-between h-32 px-2 gap-2">
            {[40, 70, 50, 90, 60, 80, 30].map((h, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full bg-green-100 rounded-t-lg relative group">
                  <div style={{ height: `${h}%` }} className="bg-green-500 rounded-t-lg transition-all"></div>
                </div>
                <span className="text-[10px] font-bold text-gray-400">월화수목금토일"[i]</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. 단어 숙련도 (도넛 그래프) [cite: 138, 144] */}
      <section className="px-4 mb-6">
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
          <h3 className="font-black text-gray-800 mb-6">단어 숙련도</h3>
          <div className="flex items-center gap-8">
            {/* 가상 도넛 그래프 */}
            <div className="relative w-32 h-32 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-[12px] border-gray-100"></div>
              <div className="absolute inset-0 rounded-full border-[12px] border-green-500 border-l-transparent border-b-transparent rotate-45"></div>
              <div className="text-center">
                <p className="text-2xl font-black text-gray-800">82%</p>
                <p className="text-[9px] font-bold text-gray-400 uppercase tracking-tighter">Overall</p>
              </div>
            </div>
            {/* 범례  */}
            <div className="flex-1 space-y-3">
              {proficiency.map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                    <span className="text-xs font-bold text-gray-500">{item.label}</span>
                  </div>
                  <span className="text-xs font-black text-gray-800">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 4. 약한 단어 & 추천 행동 [cite: 145, 148] */}
      <section className="px-4 space-y-4">
        <button className="w-full flex items-center justify-between p-5 bg-orange-50 rounded-3xl border border-orange-100 active:scale-[0.98] transition-all">
          <div className="flex items-center gap-3">
            <Zap className="text-orange-500" />
            <span className="font-bold text-orange-700 underline decoration-2 underline-offset-4">헷갈리는 단어 5개 복습하기</span>
          </div>
          <ArrowRight className="text-orange-400" />
        </button>

        <div className="grid grid-cols-2 gap-3">
          <button className="p-4 bg-white rounded-3xl border border-gray-100 shadow-sm font-bold text-gray-700 text-sm active:bg-gray-50">
            오늘 복습하기
          </button>
          <button className="p-4 bg-white rounded-3xl border border-gray-100 shadow-sm font-bold text-gray-700 text-sm active:bg-gray-50">
            연습문제 풀기
          </button>
        </div>
      </section>
    </div>
  );
}