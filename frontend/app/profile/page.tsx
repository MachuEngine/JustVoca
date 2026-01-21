"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ChevronLeft, Camera, User, Mail, Phone, Globe, 
  CheckCircle2, GraduationCap
} from 'lucide-react';
import AuthGuard from '../components/AuthGuard';
import { getUserProfile, updateUserProfile } from '../api';

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState({
    name: "",
    email: "",
    phone: "",
    country: "",
    role: "",
    teacher_id: "" 
  });
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    const userId = localStorage.getItem('userId');
    if (userId) {
      getUserProfile(userId).then(data => {
        if (data) {
          setProfile({
            ...data,
            teacher_id: data.teacher_id || "" 
          });
        }
      });
    }
  }, []);

  const handleSave = async () => {
    const userId = localStorage.getItem('userId');
    if (!userId) return;

    setIsSaving(true);
    try {
      await updateUserProfile(userId, {
        email: profile.email,
        phone: profile.phone,
        country: profile.country,
        teacher_id: profile.teacher_id 
      });
      
      // 상단바 업데이트 신호
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event("profileUpdated"));
      }

      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 2000);
    } catch (error: any) {
      // [수정 포인트] 에러 로그를 상황에 따라 다르게 출력
      
      let errorMessage = "저장에 실패했습니다. 잠시 후 다시 시도해주세요.";
      const status = error.response?.status;

      // 1. 에러 메시지 추출
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }

      // 2. 400번대(입력 실수)는 경고(warn)로, 그 외(서버 오류)는 에러(error)로 로그 출력
      if (status && status >= 400 && status < 500) {
        console.warn(`[유효성 검사 실패] ${errorMessage}`); // 노란색 로그
      } else {
        console.error("Profile save error:", error); // 빨간색 로그
      }
      
      // 3. 사용자에게 알림 띄우기
      alert(`⚠️ ${errorMessage}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <AuthGuard>
      <div className="flex flex-col min-h-full bg-white pb-24">
        <header className="h-14 flex items-center justify-between px-4 sticky top-0 bg-white/80 backdrop-blur-md z-10">
          <button onClick={() => router.back()} className="p-2 -ml-2 hover:bg-gray-100 rounded-full transition-colors">
            <ChevronLeft size={24} className="text-gray-800" />
          </button>
          <h1 className="text-lg font-bold text-gray-900">프로필 편집</h1>
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="text-green-600 font-bold px-2 disabled:opacity-50"
          >
            {isSaving ? "저장 중..." : "완료"}
          </button>
        </header>

        <main className="flex-1 px-6 pt-6">
          <div className="flex flex-col items-center mb-10">
            <div className="relative group">
              <div className="w-28 h-28 bg-green-50 rounded-full flex items-center justify-center border-4 border-white shadow-xl overflow-hidden">
                <User size={50} className="text-green-200" />
              </div>
              <button className="absolute bottom-0 right-0 bg-gray-900 text-white p-2 rounded-full shadow-lg hover:scale-110 active:scale-95 transition-transform">
                <Camera size={18} />
              </button>
            </div>
            <p className="mt-4 text-xl font-black text-gray-900">{profile.name}</p>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-widest bg-gray-100 px-3 py-1 rounded-full mt-2">
              {profile.role || "LEARNER"}
            </span>
          </div>

          <div className="space-y-6">
            <div className="space-y-1.5">
              <label className="text-xs font-black text-gray-400 ml-1 uppercase">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300" size={18} />
                <input 
                  type="email" 
                  value={profile.email}
                  onChange={(e) => setProfile({...profile, email: e.target.value})}
                  className="w-full h-14 pl-12 pr-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-green-500 outline-none font-bold text-gray-800 transition-all"
                  placeholder="이메일을 입력하세요"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-black text-gray-400 ml-1 uppercase">Phone Number</label>
              <div className="relative">
                <Phone className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300" size={18} />
                <input 
                  type="tel" 
                  value={profile.phone}
                  onChange={(e) => setProfile({...profile, phone: e.target.value})}
                  className="w-full h-14 pl-12 pr-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-green-500 outline-none font-bold text-gray-800 transition-all"
                  placeholder="전화번호를 입력하세요"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-black text-gray-400 ml-1 uppercase">Country</label>
              <div className="relative">
                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300" size={18} />
                <select 
                  value={profile.country}
                  onChange={(e) => setProfile({...profile, country: e.target.value})}
                  className="w-full h-14 pl-12 pr-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-green-500 outline-none font-bold text-gray-800 appearance-none transition-all"
                >
                  <option value="KR">South Korea (대한민국)</option>
                  <option value="US">United States</option>
                  <option value="VN">Vietnam</option>
                  <option value="CN">China</option>
                  <option value="JP">Japan</option>
                </select>
              </div>
            </div>

            {profile.role === 'student' && (
              <div className="space-y-1.5">
                <label className="text-xs font-black text-blue-500 ml-1 uppercase">My Teacher</label>
                <div className="relative">
                  <GraduationCap className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-300" size={18} />
                  <input 
                    type="text" 
                    value={profile.teacher_id}
                    onChange={(e) => setProfile({...profile, teacher_id: e.target.value})}
                    className="w-full h-14 pl-12 pr-4 bg-blue-50 border border-blue-100 rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none font-bold text-gray-800 transition-all placeholder:text-blue-200"
                    placeholder="선생님 ID를 입력하세요"
                  />
                </div>
                <p className="text-[10px] text-gray-400 ml-2">* 담당 선생님 ID를 입력하면 선생님과 연결됩니다.</p>
              </div>
            )}
          </div>

          {showSuccess && (
            <div className="fixed bottom-10 left-1/2 -translate-x-1/2 bg-gray-900 text-white px-6 py-3 rounded-2xl shadow-2xl flex items-center gap-2 animate-bounce z-50">
              <CheckCircle2 size={18} className="text-green-400" />
              <span className="font-bold text-sm">성공적으로 저장되었습니다!</span>
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}