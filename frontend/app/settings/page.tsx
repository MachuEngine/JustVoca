"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ChevronLeft, 
  Bell, 
  Moon, 
  ShieldCheck, 
  HelpCircle, 
  LogOut,
  Target,
  ChevronRight,
  Flame
} from 'lucide-react';
import AuthGuard from '../components/AuthGuard';
import { getUserProfile } from '../api';

export default function SettingsPage() {
  const router = useRouter();
  const [dailyGoal, setDailyGoal] = useState(10);
  const [reviewWrong, setReviewWrong] = useState(true);

  useEffect(() => {
    const userId = localStorage.getItem('userId');
    if (userId) {
      getUserProfile(userId).then(data => {
        if (data) {
          setDailyGoal(data.dailyGoal || 10);
          setReviewWrong(data.reviewWrong !== false);
        }
      });
    }
  }, []);

  // 로그아웃 함수만 유지
  const handleLogout = () => {
    if (confirm("로그아웃 하시겠습니까?")) {
      localStorage.removeItem('userId');
      localStorage.removeItem('userRole');
      router.replace('/login');
    }
  };

  // 준비중 알림을 위한 헬퍼 컴포넌트
  const ComingSoonBadge = () => (
    <span className="bg-gray-100 text-gray-400 text-[10px] px-2 py-1 rounded-md font-bold ml-2">
      준비중
    </span>
  );

  return (
    <AuthGuard>
      <div className="h-full flex flex-col bg-gray-50 pb-24">
        {/* 헤더 */}
        <header className="h-16 flex items-center px-6 bg-white border-b border-gray-100 sticky top-0 z-10">
          <button onClick={() => router.back()} className="p-2 -ml-3 hover:bg-gray-100 rounded-full transition-colors">
            <ChevronLeft size={24} className="text-gray-800" />
          </button>
          <h1 className="text-xl font-black text-gray-900 ml-2">설정</h1>
        </header>

        <main className="flex-1 p-6 space-y-8 overflow-y-auto">
          {/* 학습 설정 섹션 */}
          <section>
            <h2 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 ml-1">Study Settings</h2>
            <div className="bg-white rounded-3xl overflow-hidden border border-gray-100 shadow-sm opacity-60">
              {/* 일일 목표 - 비활성화 */}
              <div className="p-5 border-b border-gray-50 flex items-center justify-between cursor-not-allowed">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-orange-50 text-orange-400 rounded-xl flex items-center justify-center">
                    <Target size={20} />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <p className="font-bold text-gray-900 text-sm">일일 학습 목표</p>
                      <ComingSoonBadge />
                    </div>
                    <p className="text-[10px] text-gray-400 font-medium">하루에 학습할 단어 개수</p>
                  </div>
                </div>
                <div className="bg-gray-50 text-sm font-black text-gray-400 px-3 py-2 rounded-xl">
                  {dailyGoal}개
                </div>
              </div>

              {/* 오답 복습 - 비활성화 */}
              <div className="p-5 flex items-center justify-between cursor-not-allowed">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-red-50 text-red-400 rounded-xl flex items-center justify-center">
                    <Flame size={20} />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <p className="font-bold text-gray-900 text-sm">오답 자동 복습</p>
                      <ComingSoonBadge />
                    </div>
                    <p className="text-[10px] text-gray-400 font-medium">틀린 단어는 마지막에 다시 학습</p>
                  </div>
                </div>
                <div className="w-12 h-6 rounded-full bg-gray-200 relative">
                  <div className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-all"></div>
                </div>
              </div>
            </div>
          </section>

          {/* 앱 설정 섹션 */}
          <section>
            <h2 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 ml-1">App Settings</h2>
            <div className="bg-white rounded-3xl overflow-hidden border border-gray-100 shadow-sm opacity-60">
              {[
                { icon: Bell, label: "알림 설정", color: "text-blue-400", bg: "bg-blue-50" },
                { icon: Moon, label: "다크 모드", color: "text-purple-400", bg: "bg-purple-50" },
                { icon: ShieldCheck, label: "개인정보 보호", color: "text-green-400", bg: "bg-green-50" },
                { icon: HelpCircle, label: "고객 지원", color: "text-gray-400", bg: "bg-gray-50" }
              ].map((item, idx) => (
                <div 
                  key={idx}
                  className="w-full p-5 flex items-center justify-between border-b border-gray-50 last:border-0 cursor-not-allowed"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${item.bg} ${item.color} rounded-xl flex items-center justify-center`}>
                      <item.icon size={20} />
                    </div>
                    <div className="flex items-center">
                      <span className="font-bold text-gray-900 text-sm">{item.label}</span>
                      <ComingSoonBadge />
                    </div>
                  </div>
                  <ChevronRight size={18} className="text-gray-200" />
                </div>
              ))}
            </div>
          </section>

          {/* 로그아웃 버튼 - 활성 상태 유지 */}
          <button 
            onClick={handleLogout}
            className="w-full h-16 bg-white text-red-500 font-black rounded-3xl border border-red-100 shadow-sm flex items-center justify-center gap-2 hover:bg-red-50 active:scale-[0.98] transition-all"
          >
            <LogOut size={20} />
            <span>로그아웃</span>
          </button>

          <div className="text-center">
            <p className="text-[10px] font-bold text-gray-300 uppercase tracking-widest">Version 1.0.0 (Beta)</p>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}