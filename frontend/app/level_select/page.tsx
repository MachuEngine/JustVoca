"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft, Award } from 'lucide-react';

export default function LevelSelectPage() {
  const router = useRouter();

  // 사양서 기반 레벨 구성 및 TOPIK 레벨 매칭 [cite: 157, 160, 161, 162, 163, 164, 165]
  const levels = [
    { id: "초급1", title: "초급 1", topik: "TOPIK 1급", color: "bg-green-50 text-green-700 border-green-100" },
    { id: "초급2", title: "초급 2", topik: "TOPIK 2급", color: "bg-green-50 text-green-700 border-green-100" },
    { id: "중급1", title: "중급 1", topik: "TOPIK 3급", color: "bg-blue-50 text-blue-700 border-blue-100" },
    { id: "중급2", title: "중급 2", topik: "TOPIK 4급", color: "bg-blue-50 text-blue-700 border-blue-100" },
    { id: "고급1", title: "고급 1", topik: "TOPIK 5급", color: "bg-purple-50 text-purple-700 border-purple-100" },
    { id: "고급2", title: "고급 2", topik: "TOPIK 6급", color: "bg-purple-50 text-purple-700 border-purple-100" },
  ];

  // 레벨 선택 시 해당 레벨의 단어 공부 화면으로 즉시 이동하는 핸들러
  const handleLevelSelect = (levelId: string) => {
    // 쿼리 파라미터를 통해 레벨 정보를 전달하며 이동합니다.
    router.push(`/study/vocabulary?level=${encodeURIComponent(levelId)}`);
  };

  return (
    <div className="flex flex-col min-h-full bg-white p-6">
      {/* 뒤로가기 헤더 */}
      <header className="h-14 flex items-center -ml-2 mb-4 flex-shrink-0">
        <button 
          onClick={() => router.back()} 
          className="p-2 rounded-full hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft size={28} className="text-gray-800" />
        </button>
      </header>

      <div className="flex-1">
        {/* 타이틀 영역 [cite: 153, 158] */}
        <div className="mb-10 text-center">
          <h1 className="text-2xl font-black text-gray-900 leading-tight">
            학습할 레벨을 <br />선택해 주세요
          </h1>
          <p className="text-gray-400 font-medium mt-2 text-sm uppercase tracking-widest">
            Level Selection
          </p>
        </div>

        {/* 레벨 선택 그리드 [cite: 160, 161, 162, 163, 164, 165] */}
        <div className="grid grid-cols-2 gap-4">
          {levels.map((level) => (
            <button
              key={level.id}
              onClick={() => handleLevelSelect(level.id)}
              className={`flex flex-col items-center justify-center p-6 rounded-3xl border-2 transition-all active:scale-[0.96] ${level.color}`}
            >
              <Award className="mb-3 opacity-40" size={32} />
              <span className="text-lg font-black">{level.title}</span>
              {/* 급수 밑에 토픽 레벨 추가 [cite: 157] */}
              <span className="text-[10px] font-bold mt-1 opacity-60 italic">
                {level.topik}
              </span>
            </button>
          ))}
        </div>

        {/* 안내 문구 영역 [cite: 155, 156] */}
        <div className="mt-12 p-6 bg-gray-50 rounded-3xl border border-dashed border-gray-200">
          <p className="text-xs font-bold text-gray-400 leading-relaxed text-center">
            최초 학습 시 레벨을 설정하면 <br />
            나중에 메뉴에서 언제든 변경할 수 있습니다. [cite: 155, 156]
          </p>
        </div>
      </div>
    </div>
  );
}