"use client";

import React from 'react';
import Link from 'next/link';
import { Award } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function LevelSelectPage() {
  const { t } = useTranslation();

  const LEVELS = [
    { id: "초급1", titleKey: "level_beginner1", topik: "1", descKey: "level_beginner1_desc", color: "#20385F" },
    { id: "초급2", titleKey: "level_beginner2", topik: "2", descKey: "level_beginner2_desc", color: "#20385F" },
    { id: "중급1", titleKey: "level_intermediate1", topik: "3", descKey: "level_intermediate1_desc", color: "#20385F" },
    { id: "중급2", titleKey: "level_intermediate2", topik: "4", descKey: "level_intermediate2_desc", color: "#20385F" },
    { id: "고급1", titleKey: "level_advanced1", topik: "5", descKey: "level_advanced1_desc", color: "#20385F" },
    { id: "고급2", titleKey: "level_advanced2", topik: "6", descKey: "level_advanced2_desc", color: "#20385F" },
  ];

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 헤더 */}
      <header className="h-16 flex items-center px-6 border-b border-gray-100 bg-white sticky top-0 z-10">
        <h1 className="text-lg font-bold text-[#20385F]">{t('select_level')}</h1>
      </header>

      <main className="flex-1 p-6 overflow-y-auto pb-10">
        <div className="mb-6">
          <p className="text-sm font-medium text-[#20385F]/70">
            {t('select_level_desc')}
          </p>
        </div>

        {/* 레벨 카드 목록 */}
        <div className="flex flex-col gap-3">
          {LEVELS.map((lvl) => (
            <Link
              key={lvl.id}
              href={`/study/vocabulary?level=${encodeURIComponent(lvl.id)}`}
              className="block group"
            >
              <div
                // justify-center -> justify-start 로 변경하여 상단부터 정렬되게 함
                className="rounded-[2rem] border-2 transition-all duration-200 bg-white hover:shadow-md hover:scale-[1.01] active:scale-[0.99] px-6 py-5 flex flex-col justify-start min-h-[120px]" 
                style={{ borderColor: lvl.color }}
              >
                {/* 내부 flex 컨테이너에서도 justify-center 제거 */}
                <div className="flex flex-col gap-2 min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-black tracking-tight text-[#20385F] text-lg sm:text-xl">
                      {t(lvl.titleKey)}
                    </span>

                    <span className="bg-[#20385F]/5 font-bold rounded-full flex items-center gap-1 text-[#20385F] text-[10px] px-2.5 py-1 shrink-0">
                      <Award size={12} strokeWidth={3} /> TOPIK {lvl.topik}
                    </span>
                  </div>

                  <p className="text-[14px] font-bold opacity-70 text-[#20385F] break-keep leading-relaxed line-clamp-2">
                    {t(lvl.descKey)}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}