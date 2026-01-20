"use client";

import React from 'react';
import Link from 'next/link';
import { ChevronLeft, BookOpen } from 'lucide-react';

const LEVELS = [
  { id: "초급1", title: "초급 1", desc: "기초 자음/모음과 인사말 배우기", color: "bg-green-100 text-green-700 border-green-200" },
  { id: "초급2", title: "초급 2", desc: "일상 생활 표현과 기본 문법", color: "bg-green-50 text-green-600 border-green-100" },
  { id: "중급1", title: "중급 1", desc: "복잡한 문장 만들기와 감정 표현", color: "bg-blue-100 text-blue-700 border-blue-200" },
  { id: "중급2", title: "중급 2", desc: "비즈니스 한국어와 사회 이슈", color: "bg-blue-50 text-blue-600 border-blue-100" },
  { id: "고급1", title: "고급 1", desc: "전문적인 토론과 뉴스 청취", color: "bg-purple-100 text-purple-700 border-purple-200" },
  { id: "고급2", title: "고급 2", desc: "학문적 연구와 관용구 심화", color: "bg-purple-50 text-purple-600 border-purple-100" },
];

export default function LevelSelectPage() {
  return (
    <div className="h-full flex flex-col bg-white">
      <header className="h-16 flex items-center px-4 border-b border-gray-100 bg-white sticky top-0 z-10">
        <Link href="/student_home" className="p-2 -ml-2 rounded-full hover:bg-gray-50">
          <ChevronLeft className="text-gray-800" size={24} />
        </Link>
        <h1 className="text-lg font-bold ml-2 text-gray-900">과정 선택</h1>
      </header>

      <main className="flex-1 p-6 overflow-y-auto pb-10">
        <div className="mb-6">
          <h2 className="text-2xl font-black text-gray-900 mb-2 leading-tight">오늘 학습할<br/>단계를 선택해주세요</h2>
          <p className="text-gray-500 font-medium text-sm">하루 10개씩, 꾸준함이 실력이 됩니다! 🔥</p>
        </div>

        <div className="space-y-4">
          {LEVELS.map((lvl) => (
            <Link 
              key={lvl.id} 
              href={`/study/vocabulary?level=${encodeURIComponent(lvl.id)}`}
              className="block group"
            >
              <div className={`p-6 rounded-3xl border-2 transition-all duration-200 ${lvl.color} bg-opacity-60 hover:bg-opacity-100 hover:shadow-md hover:scale-[1.02] active:scale-[0.98]`}>
                <div className="flex justify-between items-start mb-2">
                  <span className="font-black text-xl tracking-tight flex items-center gap-2">{lvl.title}</span>
                  <div className="bg-white/50 p-1.5 rounded-full">
                    <BookOpen size={18} fill="currentColor" className="opacity-70" />
                  </div>
                </div>
                <p className="text-sm font-bold opacity-80">{lvl.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}