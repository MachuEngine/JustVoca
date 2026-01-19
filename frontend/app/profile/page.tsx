"use client";

import React from 'react';
import { 
  Flame, 
  BookOpen, 
  Clock, 
  Target, 
  Trophy, 
  ChevronRight 
} from 'lucide-react';

export default function ProfilePage() {
  // 사양서 기반 데이터 (John Smith 예시)
  const profileData = {
    name: "John Smith", // [cite: 88]
    statusMsg: "오늘도 한 걸음", // [cite: 89]
    todayStatus: "오늘 학습 완료!", // [cite: 90]
    stats: {
      continuous: "7일 연속 학습", // [cite: 92]
      wordCount: "320단어 학습", // [cite: 93]
      totalTime: "총 4시간 학습", // [cite: 94]
    },
    topikLevel: "TOPIK II 레벨", // 
    nextGoal: "중급 단어 완주", // 
  };

  return (
    <div className="flex flex-col min-h-full bg-gray-50 p-6 pb-10">
      {/* 1. 상단 타이틀 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">내 프로필</h1> {/* [cite: 86] */}
      </div>

      {/* 2. 메인 프로필 카드 */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 mb-6 text-center">
        <div className="w-24 h-24 bg-green-100 rounded-full mx-auto mb-4 flex items-center justify-center border-4 border-green-50">
          {/* 캐릭터 이미지 또는 아이콘 자리 */}
          <span className="text-4xl">👨‍🎓</span>
        </div>
        <h2 className="text-xl font-black text-gray-900">{profileData.name}</h2>
        <p className="text-gray-500 font-medium text-sm mt-1">{profileData.statusMsg}</p>
        
        {/* 오늘 학습 상태 태그 */}
        <div className="inline-block mt-4 px-4 py-1.5 bg-green-600 text-white rounded-full text-xs font-bold shadow-md animate-bounce">
          {profileData.todayStatus}
        </div>
      </div>

      {/* 3. 성취 요약 섹션 (지금까지 이렇게 했어요) */}
      <div className="mb-6">
        <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-4 ml-1">
          지금까지 이렇게 했어요 {/* [cite: 91] */}
        </h3>
        <div className="grid grid-cols-1 gap-3">
          {/* 연속 학습 */}
          <div className="flex items-center p-4 bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center text-orange-600 mr-4">
              <Flame size={24} strokeWidth={2.5} />
            </div>
            <span className="font-bold text-gray-700">{profileData.stats.continuous}</span>
          </div>
          {/* 학습 단어 수 */}
          <div className="flex items-center p-4 bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600 mr-4">
              <BookOpen size={24} strokeWidth={2.5} />
            </div>
            <span className="font-bold text-gray-700">{profileData.stats.wordCount}</span>
          </div>
          {/* 총 학습 시간 */}
          <div className="flex items-center p-4 bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center text-purple-600 mr-4">
              <Clock size={24} strokeWidth={2.5} />
            </div>
            <span className="font-bold text-gray-700">{profileData.stats.totalTime}</span>
          </div>
        </div>
      </div>

      {/* 4. TOPIK 레벨 및 목표 */}
      <div className="space-y-3">
        {/* TOPIK 레벨 정보 */}
        <div className="p-5 bg-gradient-to-r from-blue-600 to-blue-500 rounded-2xl text-white shadow-lg flex justify-between items-center">
          <div>
            <p className="text-blue-100 text-xs font-bold mb-1 italic">Current Ability</p>
            <h4 className="text-lg font-black">{profileData.topikLevel}</h4> {/*  */}
          </div>
          <Trophy size={32} className="text-blue-200 opacity-50" />
        </div>

        {/* 다음 목표 */}
        <div className="p-5 bg-white rounded-2xl border border-gray-100 shadow-sm flex justify-between items-center">
          <div>
            <h4 className="text-xs font-black text-gray-400 uppercase tracking-wider mb-1">다음 목표</h4> {/* [cite: 96] */}
            <p className="text-gray-800 font-bold">{profileData.nextGoal}</p> {/*  */}
          </div>
          <button className="p-2 bg-gray-50 rounded-full text-gray-400">
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* 5. 확인 버튼 */}
      <button className="w-full h-16 bg-gray-900 text-white font-bold rounded-2xl text-lg hover:bg-black active:scale-[0.98] transition-all shadow-lg mt-8 flex-shrink-0">
        확인 {/* [cite: 103] */}
      </button>
    </div>
  );
}