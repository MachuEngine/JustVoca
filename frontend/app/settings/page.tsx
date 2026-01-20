"use client";

import React, { useState, useEffect } from 'react';
import { 
  User, Mail, Globe, Lock, LogOut, ChevronRight, 
  BookOpen, RotateCcw, UserX, Phone 
} from 'lucide-react';
import { useRouter } from 'next/navigation';
// 위에서 정의한 api 함수들을 임포트 (경로 확인 필요)
import { 
  getUserProfile, 
  updateUserProfile, 
  updateStudySettings, 
  changePassword, 
  withdrawUser 
} from '../api';

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  // 사용자 상태 관리
  const [user, setUser] = useState({
    uid: "",
    name: "",
    accountType: "학습자", // [cite: 1295]
    email: "",             // [cite: 1296]
    country: "",           // [cite: 1297]
    phone: "",             // [cite: 1298]
    dailyGoal: 10,         // [cite: 1302]
    reviewWrong: true      // [cite: 1303]
  });

  // 초기 데이터 로드
  useEffect(() => {
    // 로그인 시 저장한 ID 가져오기 (없으면 테스트용 ID)
    const storedUserId = localStorage.getItem("userId") || "test_user";
    
    async function init() {
      const profile = await getUserProfile(storedUserId);
      if (profile) {
        setUser({
          uid: storedUserId,
          name: profile.name,
          accountType: profile.role,
          email: profile.email,
          country: profile.country,
          phone: profile.phone,
          dailyGoal: profile.dailyGoal,
          reviewWrong: profile.reviewWrong
        });
      }
      setLoading(false);
    }
    init();
  }, []);

  // --- [버튼 동작 핸들러 구현] ---

  // 1. 정보 수정 핸들러 (이메일, 전화번호, 나라)
  const handleEditInfo = async (field: 'email' | 'phone' | 'country', label: string) => {
    const currentValue = user[field];
    // 간단한 입력을 위해 prompt 사용 (추후 모달로 고도화 가능)
    const newValue = window.prompt(`새로운 ${label}을(를) 입력하세요:`, currentValue);

    if (newValue && newValue !== currentValue) {
      // 1) API 호출 (Mock)
      await updateUserProfile(user.uid, { [field]: newValue });
      
      // 2) UI 상태 업데이트
      setUser(prev => ({ ...prev, [field]: newValue }));
      alert(`${label} 정보가 변경되었습니다.`);
    }
  };

  // 2. 비밀번호 변경 [cite: 1300]
  const handlePasswordChange = async () => {
    const newPw = window.prompt("변경할 비밀번호를 입력하세요:");
    if (newPw) {
      const confirmPw = window.prompt("비밀번호 확인:");
      if (newPw === confirmPw) {
        await changePassword(user.uid, newPw);
        alert("비밀번호가 변경되었습니다. 다시 로그인해주세요.");
        handleLogout(); // 비밀번호 변경 후 로그아웃 처리
      } else {
        alert("비밀번호가 일치하지 않습니다.");
      }
    }
  };

  // 3. 하루 학습량 변경 [cite: 1302]
  const handleGoalChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newGoal = Number(e.target.value);
    await updateStudySettings(user.uid, { dailyGoal: newGoal });
    setUser(prev => ({ ...prev, dailyGoal: newGoal }));
  };

  // 4. 틀린 단어 다시보기 토글 [cite: 1303]
  const toggleReview = async () => {
    const newValue = !user.reviewWrong;
    await updateStudySettings(user.uid, { reviewWrong: newValue });
    setUser(prev => ({ ...prev, reviewWrong: newValue }));
  };

  // 5. 로그아웃 [cite: 1299]
  const handleLogout = () => {
    if (window.confirm("로그아웃 하시겠습니까?")) {
      localStorage.removeItem("userId");
      // 쿠키 삭제 (세션 쿠키)
      document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      alert("로그아웃 되었습니다.");
      router.push('/login');
    }
  };

  // 6. 회원 탈퇴 [cite: 1304]
  const handleWithdrawal = async () => {
    if (window.confirm("정말로 탈퇴하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")) {
      await withdrawUser(user.uid);
      localStorage.clear();
      alert("탈퇴가 완료되었습니다.");
      router.push('/');
    }
  };

  if (loading) return <div className="p-10 text-center font-bold text-gray-500">로딩 중...</div>;

  return (
    <div className="flex flex-col min-h-full bg-gray-50 pb-24">
      {/* 헤더 */}
      <div className="bg-white px-6 py-6 border-b border-gray-100 sticky top-0 z-10 flex items-center">
        <button onClick={() => router.back()} className="mr-4">
          <ChevronRight className="rotate-180 text-gray-400" />
        </button>
        <h1 className="text-xl font-black text-gray-900">설정</h1>
      </div>

      {/* 계정 설정 섹션 */}
      <section className="mt-6 px-4">
        <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-3 ml-2">
          프로필 관리
        </h3>
        <div className="bg-white rounded-3xl overflow-hidden shadow-sm border border-gray-100">
          
          {/* 계정 유형 (수정 불가) */}
          <div className="flex items-center justify-between p-4 border-b border-gray-50">
            <div className="flex items-center gap-3 text-gray-700">
              <User size={20} className="text-blue-500" />
              <span className="font-bold">계정 유형</span>
            </div>
            <span className="text-xs font-black text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
              {user.accountType}
            </span>
          </div>

          {/* 이메일 변경 */}
          <button 
            onClick={() => handleEditInfo('email', '이메일')}
            className="w-full flex items-center justify-between p-4 border-b border-gray-50 active:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3 text-gray-700">
              <Mail size={20} className="text-gray-400" />
              <div className="text-left">
                <p className="text-[10px] text-gray-400 font-bold uppercase">Email</p>
                <p className="font-bold">{user.email}</p>
              </div>
            </div>
            <ChevronRight size={18} className="text-gray-300" />
          </button>

          {/* 나라 변경 */}
          <button 
            onClick={() => handleEditInfo('country', '나라')}
            className="w-full flex items-center justify-between p-4 border-b border-gray-50 active:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3 text-gray-700">
              <Globe size={20} className="text-gray-400" />
              <span className="font-bold">나라</span>
            </div>
            <div className="flex items-center gap-2 text-gray-500">
              <span className="text-sm font-medium">{user.country}</span>
              <ChevronRight size={18} className="text-gray-300" />
            </div>
          </button>

          {/* 전화번호 변경 */}
          <button 
            onClick={() => handleEditInfo('phone', '전화번호')}
            className="w-full flex items-center justify-between p-4 border-b border-gray-50 active:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3 text-gray-700">
              <Phone size={20} className="text-gray-400" />
              <span className="font-bold">전화번호</span>
            </div>
            <div className="flex items-center gap-2 text-gray-500">
              <span className="text-sm font-medium">{user.phone}</span>
              <ChevronRight size={18} className="text-gray-300" />
            </div>
          </button>

          {/* 비밀번호 변경 */}
          <button 
            onClick={handlePasswordChange}
            className="w-full flex items-center justify-between p-4 active:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3 text-gray-700">
              <Lock size={20} className="text-gray-400" />
              <span className="font-bold">비밀번호 변경</span>
            </div>
            <ChevronRight size={18} className="text-gray-300" />
          </button>
        </div>

        {/* 로그아웃 버튼 */}
        <button 
          onClick={handleLogout}
          className="w-full mt-3 flex items-center justify-center gap-2 p-4 bg-white rounded-2xl border border-gray-100 text-gray-600 font-bold active:bg-gray-50 transition-colors"
        >
          <LogOut size={20} />
          <span>로그아웃</span>
        </button>
      </section>

      {/* 학습 설정 섹션 */}
      <section className="mt-8 px-4">
        <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-3 ml-2">
          학습 설정
        </h3>
        <div className="bg-white rounded-3xl overflow-hidden shadow-sm border border-gray-100">
          
          {/* 하루 학습량 */}
          <div className="flex items-center justify-between p-4 border-b border-gray-50">
            <div className="flex items-center gap-3 text-gray-700">
              <BookOpen size={20} className="text-green-500" />
              <span className="font-bold">하루 학습량</span>
            </div>
            <select 
              value={user.dailyGoal}
              onChange={handleGoalChange}
              className="bg-transparent font-black text-green-600 outline-none text-right appearance-none cursor-pointer"
            >
              <option value={5}>5개</option>
              <option value={10}>10개</option>
              <option value={20}>20개</option>
              <option value={30}>30개</option>
            </select>
          </div>

          {/* 틀린 단어 다시보기 */}
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3 text-gray-700">
              <RotateCcw size={20} className="text-orange-500" />
              <span className="font-bold">틀린 단어 다시보기</span>
            </div>
            <button 
              onClick={toggleReview}
              className={`w-12 h-6 rounded-full relative transition-colors duration-200 ${
                user.reviewWrong ? 'bg-green-500' : 'bg-gray-200'
              }`}
            >
              <div 
                className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-all duration-200 ${
                  user.reviewWrong ? 'right-1' : 'left-1'
                }`} 
              />
            </button>
          </div>
        </div>

        {/* 회원탈퇴 버튼 */}
        <button 
          onClick={handleWithdrawal}
          className="w-full mt-4 flex items-center justify-center gap-2 p-4 bg-red-50 rounded-2xl border border-red-100 text-red-500 font-bold active:bg-red-100 transition-colors"
        >
          <UserX size={20} />
          <span>회원탈퇴</span>
        </button>
      </section>
    </div>
  );
}