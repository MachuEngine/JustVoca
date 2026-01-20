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
// [추가] AuthGuard 및 API 임포트
import AuthGuard from '../components/AuthGuard';
import { getUserProfile, updateStudySettings } from '../api';

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

  const handleGoalChange = async (newGoal: number) => {
    const userId = localStorage.getItem('userId');
    if (!userId) return;
    setDailyGoal(newGoal);
    await updateStudySettings(userId, { dailyGoal: newGoal });
  };

  const handleLogout = () => {
    if (confirm("로그아웃 하시겠습니까?")) {
      localStorage.removeItem('userId');
      localStorage.removeItem('userRole');
      router.replace('/login');
    }
  };

  return (
    // [보안 적용] 로그인한 모든 유저 접근 가능
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
            <div className="bg-white rounded-3xl overflow-hidden border border-gray-100 shadow-sm">
              <div className="p-5 border-b border-gray-50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-orange-50 text-orange-500 rounded-xl flex items-center justify-center">
                    <Target size={20} />
                  </div>
                  <div>
                    <p className="font-bold text-gray-900 text-sm">일일 학습 목표</p>
                    <p className="text-[10px] text-gray-400 font-medium">하루에 학습할 단어 개수</p>
                  </div>
                </div>
                <select 
                  value={dailyGoal}
                  onChange={(e) => handleGoalChange(Number(e.target.value))}
                  className="bg-gray-50 text-sm font-black text-gray-900 px-3 py-2 rounded-xl outline-none"
                >
                  <option value={5}>5개</option>
                  <option value={10}>10개</option>
                  <option value={20}>20개</option>
                  <option value={30}>30개</option>
                </select>
              </div>

              <div className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-red-50 text-red-500 rounded-xl flex items-center justify-center">
                    <Flame size={20} />
                  </div>
                  <div>
                    <p className="font-bold text-gray-900 text-sm">오답 자동 복습</p>
                    <p className="text-[10px] text-gray-400 font-medium">틀린 단어는 마지막에 다시 학습</p>
                  </div>
                </div>
                <button 
                  onClick={() => setReviewWrong(!reviewWrong)}
                  className={`w-12 h-6 rounded-full transition-colors relative ${reviewWrong ? 'bg-green-500' : 'bg-gray-200'}`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${reviewWrong ? 'right-1' : 'left-1'}`}></div>
                </button>
              </div>
            </div>
          </section>

          {/* 앱 설정 섹션 */}
          <section>
            <h2 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 ml-1">App Settings</h2>
            <div className="bg-white rounded-3xl overflow-hidden border border-gray-100 shadow-sm">
              {[
                { icon: Bell, label: "알림 설정", color: "text-blue-500", bg: "bg-blue-50" },
                { icon: Moon, label: "다크 모드", color: "text-purple-500", bg: "bg-purple-50" },
                { icon: ShieldCheck, label: "개인정보 보호", color: "text-green-500", bg: "bg-green-50" },
                { icon: HelpCircle, label: "고객 지원", color: "text-gray-500", bg: "bg-gray-50" }
              ].map((item, idx) => (
                <button 
                  key={idx}
                  className="w-full p-5 flex items-center justify-between hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${item.bg} ${item.color} rounded-xl flex items-center justify-center`}>
                      <item.icon size={20} />
                    </div>
                    <span className="font-bold text-gray-900 text-sm">{item.label}</span>
                  </div>
                  <ChevronRight size={18} className="text-gray-300" />
                </button>
              ))}
            </div>
          </section>

          {/* 로그아웃 버튼 */}
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