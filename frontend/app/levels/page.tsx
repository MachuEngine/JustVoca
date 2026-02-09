"use client";

import React from 'react';
import Link from 'next/link';
import { ChevronLeft, BookOpen, Award } from 'lucide-react';

// [수정] 레벨과 토픽 매칭 데이터 정의 (색상만 변경)
export const LEVELS = [
  {
    id: "초급1",
    title: "초급 1",
    topik: "1급",
    desc: "기초 자음/모음과 인사말 배우기",
    color: "#20385F",
  },
  {
    id: "초급2",
    title: "초급 2",
    topik: "2급",
    desc: "일상 생활 표현과 기본 문법",
    color: "#20385F",
  },
  {
    id: "중급1",
    title: "중급 1",
    topik: "3급",
    desc: "복잡한 문장 만들기와 감정 표현",
    color: "#20385F",
  },
  {
    id: "중급2",
    title: "중급 2",
    topik: "4급",
    desc: "비즈니스 한국어와 사회 이슈",
    color: "#20385F",
  },
  {
    id: "고급1",
    title: "고급 1",
    topik: "5급",
    desc: "전문적인 토론과 뉴스 청취",
    color: "#20385F",
  },
  {
    id: "고급2",
    title: "고급 2",
    topik: "6급",
    desc: "학문적 연구와 관용구 심화",
    color: "#20385F",
  },
];

export default function LevelSelectPage() {
  return (
    <div className="h-full flex flex-col bg-white">
      <header className="h-16 flex items-center px-6 border-b border-gray-100 bg-white sticky top-0 z-10">
        <h1 className="text-lg font-bold ml-2 text-[#20385F]">과정 선택</h1>
      </header>

      <main className="flex-1 p-6 overflow-y-auto pb-10">
        <div className="mb-6">
          <p className="text-sm font-medium text-[#20385F]/70">
            학습할 단계를 선택하세요.
          </p>
        </div>

        {/* [수정] 항상 2열 + 모바일에서 깨짐 방지 */}
        <div className="grid grid-cols-2 gap-4">
          {LEVELS.map((lvl) => (
            <Link
              key={lvl.id}
              href={`/study/vocabulary?level=${encodeURIComponent(lvl.id)}`}
              className="block group"
            >
              <div
                className="rounded-3xl border-2 transition-all duration-200 bg-white hover:shadow-md hover:scale-[1.02] active:scale-[0.98] p-4 sm:p-6"
                style={{ borderColor: lvl.color }}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {/* [수정] 제목 한 줄 유지 + 모바일 폰트 약간 축소 */}
                    <span className="font-black tracking-tight text-[#20385F] text-base sm:text-xl whitespace-nowrap">
                      {lvl.title}
                    </span>

                    {/* [수정] 뱃지 축소 + 한 줄 유지 */}
                    <span className="bg-white/80 font-bold rounded-full flex items-center gap-1 shadow-sm text-[#20385F] whitespace-nowrap text-[9px] sm:text-[10px] px-1.5 sm:px-2 py-0.5">
                      <Award size={10} /> TOPIK {lvl.topik}
                    </span>
                  </div>
                </div>

                {/* [수정] 설명은 2줄까지만 + 한글 깨짐 방지 */}
                <p className="text-sm font-bold opacity-80 text-[#20385F] break-keep line-clamp-2">
                  {lvl.desc}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
