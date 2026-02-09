"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { UserCircle, ChevronLeft } from "lucide-react";
import { getUserProfile, getUserProgress } from "../api";

export default function TopNavBar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [userRole, setUserRole] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState({
    nationalityEmoji: "🇰🇷",
    nationalityCode: "KR",
    learningLevel: "초급 1", // ✅ 현재 레벨(진행도 기준)
    topikLabel: "Topik I",
    teacherId: null as string | null,
  });

  const isTeacher = userRole === "teacher" || userRole === "admin";

  const getFlagEmojiOnly = (countryCode: string) => {
    if (!countryCode) return "🇰🇷";
    const codePoints = countryCode
      .toUpperCase()
      .split("")
      .map((char) => 127397 + char.charCodeAt(0));
    return String.fromCodePoint(...codePoints);
  };

  const fetchNavBarData = async () => {
    const userId =
      typeof window !== "undefined" ? localStorage.getItem("userId") : null;
    const role =
      typeof window !== "undefined" ? localStorage.getItem("userRole") : null;

    if (!userId) return;
    setUserRole(role);

    try {
      const profile = await getUserProfile(userId);

      let currentLevel = "초급 1";
      if (role !== "teacher" && role !== "admin") {
        const progress = await getUserProgress(userId);
        if (progress?.level) currentLevel = progress.level;
      }

      const countryCode = profile?.country || "KR";

      setUserInfo({
        nationalityEmoji: getFlagEmojiOnly(countryCode),
        nationalityCode: countryCode,
        learningLevel: currentLevel, // ✅ 기존 로직 유지
        topikLabel: "Topik I",
        teacherId: profile?.teacher_id || null,
      });
    } catch (error) {
      console.error("상단바 정보 로드 실패", error);
    }
  };

  useEffect(() => {
    fetchNavBarData();

    const handleProfileUpdate = () => fetchNavBarData();
    window.addEventListener("profileUpdated", handleProfileUpdate);
    return () => window.removeEventListener("profileUpdated", handleProfileUpdate);
  }, []);

  // ✅ 뒤로가기 동작: 진입 경로에 따라 fallback
  // 사용 방법(권장):
  // - 홈에서 들어올 때: /vocabulary_study?...&from=home
  // - 레벨선택에서 들어올 때: /vocabulary_study?...&from=level
  const handleBack = () => {
    const from = searchParams.get("from");

    // 1) 우선 back 시도
    // (히스토리 없는 direct 진입이면 fallback으로 이동)
    try {
      if (typeof window !== "undefined" && window.history.length > 1) {
        router.back();
        return;
      }
    } catch {}

    // 2) fallback
    if (from === "level") {
      router.push("/level_select"); // 🔁 너희 레벨 선택 페이지 경로로 바꿔줘
      return;
    }
    router.push("/student_home"); // 기본: 홈
  };

  // ✅ 학습/단어 관련 화면에서만 뒤로가기 노출하고 싶으면 조건
  const showBack =
    pathname?.includes("vocabulary") ||
    pathname?.includes("study") ||
    pathname?.includes("student");

  return (
    <nav className="sticky top-0 z-50 w-full bg-white">
      <div className="h-14 flex items-center justify-between px-4 border-b border-gray-100">

        {/* LEFT: Back + Level */}
        <div className="flex items-center gap-2 min-w-0">
          {showBack && (
            <button
              onClick={handleBack}
              className="p-2 -ml-2 rounded-full hover:bg-gray-50 active:scale-95 transition"
              aria-label="back"
            >
              <ChevronLeft size={22} className="text-gray-700" />
            </button>
          )}

          {!isTeacher && (
            <div className="text-sm font-bold text-gray-900 truncate">
              {userInfo.learningLevel}
              <span className="mx-1 text-gray-400">|</span>
              {userInfo.topikLabel}
            </div>
          )}

          {isTeacher && (
            <div className="text-sm font-bold text-gray-900">
              Teacher Mode
            </div>
          )}
        </div>

        {/* CENTER: 비움 (시안과 동일) */}
        <div className="flex-1" />

        {/* RIGHT: Profile */}
        <div className="flex items-center gap-2">
          {!isTeacher && (
            <div
              className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center"
              title={userInfo.nationalityCode}
            >
              <span className="text-lg">{userInfo.nationalityEmoji}</span>
            </div>
          )}

          <Link
            href="/profile"
            className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center active:scale-95 transition"
            aria-label="profile"
          >
            <UserCircle size={22} strokeWidth={1.5} className="text-gray-700" />
          </Link>
        </div>
      </div>
    </nav>
  );
}