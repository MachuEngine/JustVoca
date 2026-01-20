"use client";

import React from 'react';
import { BarChart, PieChart, ArrowRight, Zap, Target, Flame } from 'lucide-react'; //
// [추가] AuthGuard 임포트
import AuthGuard from '../components/AuthGuard';

export default function StatsPage() {
  const statsSummary = {
    learnedWords: 84,
    streak: 6,
    accuracy: 82,
  };

  const proficiency = [
    { label: "완전 암기", value: 45, color: "bg-green-500" },
    { label: "복습 필요", value: 35, color: "bg-orange-400" },
    { label: "다시 학습", value: 20, color: "bg-red-400" },
  ];

  return (
    // [보안 적용] 학생 전용
    <AuthGuard allowedRoles={['student']}>
      <div className="flex flex-col min-h-full bg-gray-50 pb-10">
        <div className="bg-white px-6 py-6 border-b border-gray-100">
          <h1 className="text-2xl font-black text-gray-900">통계</h1>
        </div>

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

        <section className="px-4 mb-6">
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-black text-gray-800">학습 추이</h3>
            </div>
            <div className="flex items-end justify-between h-32 px-2 gap-2">
              {[40, 70, 50, 90, 60, 80, 30].map((h, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full bg-green-100 rounded-t-lg relative group">
                    <div style={{ height: `${h}%` }} className="bg-green-500 rounded-t-lg transition-all"></div>
                  </div>
                  <span className="text-[10px] font-bold text-gray-400">{['월','화','수','목','금','토','일'][i]}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="px-4 mb-6">
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
            <h3 className="font-black text-gray-800 mb-6">단어 숙련도</h3>
            <div className="flex items-center gap-8">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-[12px] border-gray-100"></div>
                <div className="absolute inset-0 rounded-full border-[12px] border-green-500 border-l-transparent border-b-transparent rotate-45"></div>
                <div className="text-center">
                  <p className="text-2xl font-black text-gray-800">82%</p>
                  <p className="text-[9px] font-bold text-gray-400 uppercase tracking-tighter">Overall</p>
                </div>
              </div>
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

        <section className="px-4 space-y-4">
          <button className="w-full flex items-center justify-between p-5 bg-orange-50 rounded-3xl border border-orange-100 active:scale-[0.98] transition-all">
            <div className="flex items-center gap-3">
              <Zap className="text-orange-500" />
              <span className="font-bold text-orange-700 underline decoration-2 underline-offset-4">헷갈리는 단어 5개 복습하기</span>
            </div>
            <ArrowRight className="text-orange-400" />
          </button>
        </section>
      </div>
    </AuthGuard>
  );
}