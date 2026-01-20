"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { UserCircle } from "lucide-react";
import { getUserProfile, getUserProgress } from "../api";

export default function TopNavBar() {
  const [userRole, setUserRole] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState({
    nationality: "🇰🇷 KR",
    learningLevel: "초급 1",
    topikLevel: "1급",
  });

  const getTopikLevel = (levelName: string) => {
    const normalized = levelName.replace(/\s/g, "");
    if (normalized.includes("초급1")) return "1급";
    if (normalized.includes("초급2")) return "2급";
    if (normalized.includes("중급1")) return "3급";
    if (normalized.includes("중급2")) return "4급";
    if (normalized.includes("고급1")) return "5급";
    if (normalized.includes("고급2")) return "6급";
    return "1급";
  };

  const getFlagEmoji = (countryCode: string) => {
    if (!countryCode) return "🇰🇷 KR";
    const codePoints = countryCode
      .toUpperCase()
      .split('')
      .map(char => 127397 + char.charCodeAt(0));
    return String.fromCodePoint(...codePoints) + " " + countryCode;
  };

  useEffect(() => {
    const userId = typeof window !== 'undefined' ? localStorage.getItem("userId") : null;
    const role = typeof window !== 'undefined' ? localStorage.getItem("userRole") : null;
    
    if (!userId) return;
    setUserRole(role);

    const fetchData = async () => {
      try {
        // 공통: 프로필 정보 (국적 등)
        const profile = await getUserProfile(userId);
        
        // 학생일 때만 진도 정보 가져오기
        let currentLevel = "초급 1";
        if (role !== 'teacher' && role !== 'admin') {
          const progress = await getUserProgress(userId);
          if (progress?.level) currentLevel = progress.level;
        }

        setUserInfo({
          nationality: profile?.country ? getFlagEmoji(profile.country) : "🇰🇷 KR",
          learningLevel: currentLevel,
          topikLevel: getTopikLevel(currentLevel),
        });
      } catch (error) {
        console.error("상단바 정보 로드 실패", error);
      }
    };

    fetchData();
  }, []);

  const isTeacher = userRole === 'teacher' || userRole === 'admin';

  return (
    <nav className="sticky top-0 z-50 w-full h-16 bg-white border-b border-gray-100 flex items-center justify-between px-4 flex-shrink-0">
      
      {/* 1. 좌측 영역: 선생님이면 숨김, 학생이면 학습 정보 표시 */}
      <div className="flex items-center gap-2">
        {!isTeacher && (
          <>
            <div className="flex items-center justify-center bg-gray-50 px-2 py-1 rounded-full border border-gray-200">
              <span className="text-xs font-bold text-gray-700">{userInfo.nationality}</span>
            </div>

            <div className="flex gap-1">
              <span className="bg-green-100 text-green-700 text-[10px] px-2 py-0.5 rounded font-semibold whitespace-nowrap">
                {userInfo.learningLevel}
              </span>
              <span className="bg-blue-100 text-blue-700 text-[10px] px-2 py-0.5 rounded font-semibold whitespace-nowrap">
                TOPIK {userInfo.topikLevel}
              </span>
            </div>
          </>
        )}
        {/* 선생님일 경우 좌측에 간단한 로고나 텍스트를 넣고 싶다면 여기에 추가 */}
        {isTeacher && (
           <span className="text-lg font-black text-gray-900">Teacher Mode</span>
        )}
      </div>

      {/* 2. 우측 프로필 버튼 (공통) */}
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
