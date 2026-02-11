"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Bell, 
  Moon, 
  ShieldCheck, 
  HelpCircle, 
  LogOut,
  Target,
  ChevronRight,
  Flame,
  Globe // 언어 아이콘
} from 'lucide-react';
import AuthGuard from '../components/AuthGuard';
import { getUserProfile } from '../api';
import { useTranslation } from 'react-i18next';

export default function SettingsPage() {
  const router = useRouter();
  const { t, i18n } = useTranslation();
  
  const [dailyGoal, setDailyGoal] = useState(10);
  const [showLangOptions, setShowLangOptions] = useState(false); // 언어 리스트 토글 상태

  const languages = [
    { code: 'ko', name: '한국어' },
    { code: 'en', name: 'English' },
    { code: 'vi', name: 'Tiếng Việt' },
    { code: 'zh', name: '中文' },
    { code: 'ja', name: '日本語' },
  ];

  useEffect(() => {
    const userId = localStorage.getItem('userId');
    if (userId) {
      getUserProfile(userId).then(data => {
        if (data) {
          setDailyGoal(data.dailyGoal || 10);
        }
      });
    }
  }, []);

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode);
    document.documentElement.lang = langCode;
    setShowLangOptions(false); // 선택 후 리스트 닫기
  };

  const handleLogout = () => {
    if (confirm(t('confirm_logout') || "로그아웃 하시겠습니까?")) {
      localStorage.removeItem('userId');
      localStorage.removeItem('userRole');
      router.replace('/login');
    }
  };

  const ComingSoonBadge = () => (
    <span className="bg-gray-100 text-gray-400 text-[10px] px-2 py-1 rounded-md font-bold ml-2">
      {t('coming_soon') || "준비중"}
    </span>
  );

  return (
    <AuthGuard>
      <div className="h-full flex flex-col bg-gray-50 pb-24">
        <header className="h-16 flex items-center px-6 border-b border-gray-100 bg-white sticky top-0 z-10">
          <h1 className="text-lg font-bold ml-2 text-gray-900">{t('settings_title')}</h1>
        </header>

        <main className="flex-1 p-6 space-y-8 overflow-y-auto">
          {/* Study Settings 섹션 */}


          {/* App Settings 섹션 */}
          <section>
            <h2 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 ml-1">App Settings</h2>
            <div className="bg-white rounded-3xl overflow-hidden border border-gray-100 shadow-sm">
              {/* 1. 알림 설정 (비활성) */}
              <div className="p-5 flex items-center justify-between border-b border-gray-50 opacity-60 cursor-not-allowed">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-50 text-blue-400 rounded-xl flex items-center justify-center">
                    <Bell size={20} />
                  </div>
                  <div className="flex items-center">
                    <span className="font-bold text-gray-900 text-sm">{t('notice')}</span>
                    <ComingSoonBadge />
                  </div>
                </div>
                <ChevronRight size={18} className="text-gray-200" />
              </div>

              {/* 2. 다크 모드 (비활성) */}
              <div className="p-5 flex items-center justify-between border-b border-gray-50 opacity-60 cursor-not-allowed">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-50 text-purple-400 rounded-xl flex items-center justify-center">
                    <Moon size={20} />
                  </div>
                  <div className="flex items-center">
                    <span className="font-bold text-gray-900 text-sm">다크 모드</span>
                    <ComingSoonBadge />
                  </div>
                </div>
                <ChevronRight size={18} className="text-gray-200" />
              </div>

              {/* ★ 3. 언어 설정 (활성 상태) ★ */}
              <div className="border-b border-gray-50">
                <button 
                  onClick={() => setShowLangOptions(!showLangOptions)}
                  className="w-full p-5 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-50 text-emerald-500 rounded-xl flex items-center justify-center">
                      <Globe size={20} />
                    </div>
                    <span className="font-bold text-gray-900 text-sm">{t('language_settings')}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg">
                      {languages.find(l => l.code === i18n.language)?.name || "한국어"}
                    </span>
                    <ChevronRight size={18} className={`text-gray-300 transition-transform ${showLangOptions ? 'rotate-90' : ''}`} />
                  </div>
                </button>

                {/* 클릭 시 나타나는 언어 리스트 */}
                {showLangOptions && (
                  <div className="bg-gray-50 px-5 py-3 grid grid-cols-1 gap-1 animate-in slide-in-from-top-2 duration-200">
                    {languages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => handleLanguageChange(lang.code)}
                        className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                          i18n.language === lang.code
                            ? "bg-white shadow-sm text-[#20385F] font-black"
                            : "text-gray-500 font-medium hover:bg-white/50"
                        }`}
                      >
                        <span className="text-sm">{lang.name}</span>
                        {i18n.language === lang.code && <div className="w-1.5 h-1.5 rounded-full bg-[#20385F]" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* 4. 개인정보 보호 (비활성) */}
              <div className="p-5 flex items-center justify-between border-b border-gray-50 opacity-60 cursor-not-allowed">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-50 text-green-400 rounded-xl flex items-center justify-center">
                    <ShieldCheck size={20} />
                  </div>
                  <div className="flex items-center">
                    <span className="font-bold text-gray-900 text-sm">개인정보 보호</span>
                    <ComingSoonBadge />
                  </div>
                </div>
                <ChevronRight size={18} className="text-gray-200" />
              </div>
            </div>
          </section>

          {/* 로그아웃 버튼 */}
          <button 
            onClick={handleLogout}
            className="w-full h-16 bg-white text-red-500 font-black rounded-3xl border border-red-100 shadow-sm flex items-center justify-center gap-2 hover:bg-red-50 active:scale-[0.98] transition-all"
          >
            <LogOut size={20} />
            <span>{t('logout')}</span>
          </button>
        </main>
      </div>
    </AuthGuard>
  );
}