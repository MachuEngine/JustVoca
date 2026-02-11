"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { UserCircle, ChevronLeft } from "lucide-react";
import { useTranslation } from "react-i18next";
import { getUserProfile, getUserProgress } from "../api";

export default function TopNavBar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { t } = useTranslation();

  const [userRole, setUserRole] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState({
    nationalityEmoji: "🇰🇷",
    nationalityCode: "KR",
    learningLevelKey: "level_beginner1",
    topikLabel: "Topik1",
    teacherId: null as string | null,
  });

  const isTeacher = userRole === "teacher";
  const isAdmin = userRole === "admin";

  // 정규화 및 매핑 로직
  const getLevelKeyAndTopik = (level: string) => {
    const s = String(level || "").replace(/\s+/g, "");
    const mapping: Record<string, { key: string; topik: string }> = {
      "초급1": { key: "level_beginner1", topik: "Topik1" },
      "초급2": { key: "level_beginner2", topik: "Topik2" },
      "중급1": { key: "level_intermediate1", topik: "Topik3" },
      "중급2": { key: "level_intermediate2", topik: "Topik4" },
      "고급1": { key: "level_advanced1", topik: "Topik5" },
      "고급": { key: "level_advanced1", topik: "Topik5" },
      "고급2": { key: "level_advanced2", topik: "Topik6" },
    };
    return mapping[s] ?? { key: "level_beginner1", topik: "Topik1" };
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
      const { key, topik } = getLevelKeyAndTopik(currentLevel);

      setUserInfo({
        nationalityEmoji: getFlagEmojiOnly(countryCode),
        nationalityCode: countryCode,
        learningLevelKey: key,
        topikLabel: topik, // Topik + 숫자 형태 저장
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

          {!isTeacher && !isAdmin && (
            <div className="text-sm font-bold text-gray-900 truncate">
              {/* 레벨 명칭만 번역 적용 */}
              {t(userInfo.learningLevelKey)}
              <span className="mx-1 text-gray-400">|</span>
              {/* Topik은 기존처럼 고정 라벨 사용 */}
              {userInfo.topikLabel}
            </div>
          )}

          {isTeacher && (
            <div className="text-sm font-bold text-[#20385F]">
              {t('teacher_mode')}
            </div>
          )}

          {isAdmin && (
            <div className="text-sm font-bold text-red-600">
              {t('admin_mode')}
            </div>
          )}
        </div>

        <div className="flex-1" />

        {/* RIGHT: Profile */}
        <div className="flex items-center gap-2">
          {!isTeacher && !isAdmin && (
            <div
              className="w-9 h-9 rounded-full bg-gray-50 flex items-center justify-center border border-gray-100"
              title={userInfo.nationalityCode}
            >
              <span className="text-lg">{userInfo.nationalityEmoji}</span>
            </div>
          )}

          <Link
            href="/profile"
            className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center active:scale-95 transition hover:bg-gray-200"
            aria-label="profile"
          >
            <UserCircle size={22} strokeWidth={1.5} className="text-gray-700" />
          </Link>
        </div>
      </div>
    </nav>
  );
}