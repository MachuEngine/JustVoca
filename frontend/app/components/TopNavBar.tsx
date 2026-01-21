"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { UserCircle, GraduationCap } from "lucide-react";
import { getUserProfile, getUserProgress } from "../api";

export default function TopNavBar() {
  const [userRole, setUserRole] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState({
    nationality: "🇰🇷 KR",
    learningLevel: "초급 1",
    topikLevel: "1급",
    teacherId: null as string | null,
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

  // [수정] 데이터 로드 로직을 함수로 분리
  const fetchNavBarData = async () => {
    const userId = typeof window !== 'undefined' ? localStorage.getItem("userId") : null;
    const role = typeof window !== 'undefined' ? localStorage.getItem("userRole") : null;
    
    if (!userId) return;
    setUserRole(role);

    try {
      const profile = await getUserProfile(userId);
      
      let currentLevel = "초급 1";
      if (role !== 'teacher' && role !== 'admin') {
        const progress = await getUserProgress(userId);
        if (progress?.level) currentLevel = progress.level;
      }

      setUserInfo({
        nationality: profile?.country ? getFlagEmoji(profile.country) : "🇰🇷 KR",
        learningLevel: currentLevel,
        topikLevel: getTopikLevel(currentLevel),
        teacherId: profile?.teacher_id || null, 
      });
    } catch (error) {
      console.error("상단바 정보 로드 실패", error);
    }
  };

  useEffect(() => {
    // 1. 처음 켜질 때 로드
    fetchNavBarData();

    // 2. [추가] 프로필이 업데이트되었다는 신호를 받으면 다시 로드
    const handleProfileUpdate = () => {
      fetchNavBarData();
    };
    window.addEventListener("profileUpdated", handleProfileUpdate);

    // 뒷정리 (이벤트 제거)
    return () => {
      window.removeEventListener("profileUpdated", handleProfileUpdate);
    };
  }, []);

  const isTeacher = userRole === 'teacher' || userRole === 'admin';

  return (
    <nav className="sticky top-0 z-50 w-full h-16 bg-white border-b border-gray-100 flex items-center justify-between px-4 flex-shrink-0">
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide py-1">
        {!isTeacher && (
          <>
            <div className="flex items-center justify-center bg-gray-50 px-2 py-1 rounded-full border border-gray-200 flex-shrink-0">
              <span className="text-xs font-bold text-gray-700">{userInfo.nationality}</span>
            </div>

            <div className="flex gap-1 flex-shrink-0">
              <span className="bg-green-100 text-green-700 text-[10px] px-2 py-0.5 rounded font-semibold whitespace-nowrap flex items-center">
                {userInfo.learningLevel}
              </span>
              <span className="bg-blue-100 text-blue-700 text-[10px] px-2 py-0.5 rounded font-semibold whitespace-nowrap flex items-center">
                TOPIK {userInfo.topikLevel}
              </span>
            </div>

            {userInfo.teacherId && (
              <div className="flex items-center gap-1 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-100 flex-shrink-0 animate-in fade-in zoom-in">
                <GraduationCap size={10} className="text-purple-500" />
                <span className="text-[10px] font-bold text-purple-600 whitespace-nowrap">
                  T: {userInfo.teacherId}
                </span>
              </div>
            )}
          </>
        )}
        
        {isTeacher && (
           <span className="text-lg font-black text-gray-900">Teacher Mode</span>
        )}
      </div>

      <div className="flex items-center flex-shrink-0">
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