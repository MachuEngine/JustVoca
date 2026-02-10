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
    learningLevel: "초급 1",
    topikLabel: "Topik I",
    teacherId: null as string | null,
  });

  const isTeacher = userRole === "teacher" || userRole === "admin";

  const normalizeLevel = (level: string) => {
    const s = String(level || "").replace(/\s+/g, "");
    if (s === "고급") return "고급1";
    return s;
  };

  const topikLabelByLevel: Record<string, string> = {
    "초급1": "Topik1", "초급2": "Topik2", "중급1": "Topik3",
    "중급2": "Topik4", "고급1": "Topik5", "고급2": "Topik6",
  };

  const getTopikLabel = (level: string) => {
    const key = normalizeLevel(level);
    return topikLabelByLevel[key] ?? "Topik1";
  };

  const getFlagEmojiOnly = (countryCode: string) => {
    if (!countryCode) return "🇰🇷";
    const codePoints = countryCode
      .toUpperCase()
      .split("")
      .map((char) => 127397 + char.charCodeAt(0));
    return String.fromCodePoint(...codePoints);
  };

  const fetchNavBarData = async () => {
    const userId = typeof window !== "undefined" ? localStorage.getItem("userId") : null;
    const role = typeof window !== "undefined" ? localStorage.getItem("userRole") : null;

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
      const normalizedLevel = normalizeLevel(currentLevel);

      setUserInfo({
        nationalityEmoji: getFlagEmojiOnly(countryCode),
        nationalityCode: countryCode,
        learningLevel: currentLevel,
        topikLabel: getTopikLabel(normalizedLevel),
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

  const handleBack = () => {
    const from = searchParams.get("from");
    try {
      if (typeof window !== "undefined" && window.history.length > 1) {
        router.back();
        return;
      }
    } catch {}

    if (from === "level") {
      router.push("/level_select");
      return;
    }
    router.push("/student_home");
  };

  const showBack = pathname?.includes("vocabulary");

  return (
    <nav className="sticky top-0 z-50 w-full bg-white border-b border-gray-100">
      {/* 가이드 반영: max-w-screen-xl mx-auto 적용 */}
      <div className="h-14 flex items-center justify-between px-4 max-w-screen-xl mx-auto w-full">
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