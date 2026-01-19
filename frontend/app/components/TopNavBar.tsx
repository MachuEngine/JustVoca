"use client";

import React from "react";
import Link from "next/link"; // 페이지 이동을 위한 Link 컴포넌트 추가
import { UserCircle } from "lucide-react";

export default function TopNavBar() {
  // 나중에 API에서 가져올 실제 사용자 정보 예시
  const userInfo = {
    nationality: "🇰🇷 KR",
    learningLevel: "초급 1",
    topikLevel: "3급",
  };

  return (
    <nav className="sticky top-0 z-50 w-full h-16 bg-white border-b border-gray-100 flex items-center justify-between px-4 flex-shrink-0">
      
      {/* 1. 사용자 학습 정보 영역 */}
      <div className="flex items-center gap-2">
        <div className="flex items-center justify-center bg-gray-50 px-2 py-1 rounded-full border border-gray-200">
          <span className="text-xs font-bold text-gray-700">{userInfo.nationality}</span>
        </div>

        <div className="flex gap-1">
          <span className="bg-green-100 text-green-700 text-[10px] px-2 py-0.5 rounded font-semibold">
            {userInfo.learningLevel}
          </span>
          <span className="bg-blue-100 text-blue-700 text-[10px] px-2 py-0.5 rounded font-semibold">
            TOPIK {userInfo.topikLevel}
          </span>
        </div>
      </div>

      {/* 2. 우측 프로필 버튼 (누르면 /profile 페이지로 이동) */}
      <div className="flex items-center">
        <Link 
          href="/profile" 
          className="flex items-center gap-1 p-1 hover:bg-gray-50 rounded-full transition-colors text-gray-600 active:scale-95"
        >
          <UserCircle size={28} strokeWidth={1.5} />
        </Link>
      </div>

    </nav>
  );
}