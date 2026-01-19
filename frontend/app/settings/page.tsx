"use client";

import React from 'react';
import { 
  User, 
  Mail, 
  Globe, 
  Lock, 
  LogOut, 
  ChevronRight, 
  BookOpen, 
  RotateCcw, 
  UserX 
} from 'lucide-react';

export default function SettingsPage() {
  // 사양서 기반 설정 데이터 [cite: 111-121]
  const settingsData = {
    accountType: "학습자", // [cite: 112]
    email: "john.smith@example.com", // [cite: 113]
    country: "미국 (USA)", // [cite: 114]
    dailyGoal: "10개", // 
  };

  return (
    <div className="flex flex-col min-h-full bg-gray-50 pb-10">
      {/* 1. 상단 헤더 */}
      <div className="bg-white px-6 py-6 border-b border-gray-100">
        <h1 className="text-2xl font-black text-gray-900">설정</h1> {/* [cite: 105, 108] */}
      </div>

      {/* 2. 계정 설정 섹션  */}
      <section className="mt-6 px-4">
        <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-3 ml-2">
          계정 설정 {/*  */}
        </h3>
        <div className="bg-white rounded-3xl overflow-hidden shadow-sm border border-gray-100">
          {/* 계정 유형 */}
          <div className="flex items-center justify-between p-4 border-b border-gray-50">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                <User size={20} />
              </div>
              <span className="font-bold text-gray-700">계정 유형</span>
            </div>
            <span className="text-sm font-bold text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
              {settingsData.accountType} {/* [cite: 112] */}
            </span>
          </div>

          {/* 이메일 (변경 가능)  */}
          <button className="w-full flex items-center justify-between p-4 border-b border-gray-50 active:bg-gray-50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-50 text-gray-500 rounded-xl">
                <Mail size={20} />
              </div>
              <div className="text-left">
                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-tight">Email</p>
                <p className="font-bold text-gray-700">{settingsData.email}</p> {/* [cite: 113] */}
              </div>
            </div>
            <ChevronRight size={18} className="text-gray-300" />
          </button>

          {/* 나라 (변경 가능) [cite: 114, 125] */}
          <button className="w-full flex items-center justify-between p-4 border-b border-gray-50 active:bg-gray-50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-50 text-gray-500 rounded-xl">
                <Globe size={20} />
              </div>
              <span className="font-bold text-gray-700">나라</span> {/* [cite: 114] */}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-500">{settingsData.country}</span>
              <ChevronRight size={18} className="text-gray-300" />
            </div>
          </button>

          {/* 비밀번호 변경 [cite: 117, 125] */}
          <button className="w-full flex items-center justify-between p-4 active:bg-gray-50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-50 text-gray-500 rounded-xl">
                <Lock size={20} />
              </div>
              <span className="font-bold text-gray-700">비밀번호 변경</span> {/* [cite: 117] */}
            </div>
            <ChevronRight size={18} className="text-gray-300" />
          </button>
        </div>
      </section>

      {/* 3. 학습 설정 섹션  */}
      <section className="mt-8 px-4">
        <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-3 ml-2">
          학습 설정 {/*  */}
        </h3>
        <div className="bg-white rounded-3xl overflow-hidden shadow-sm border border-gray-100">
          {/* 하루 학습량 */}
          <div className="flex items-center justify-between p-4 border-b border-gray-50">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 text-green-600 rounded-xl">
                <BookOpen size={20} />
              </div>
              <span className="font-bold text-gray-700">하루 학습량</span> {/*  */}
            </div>
            <select 
              className="bg-transparent font-bold text-green-600 outline-none text-right appearance-none cursor-pointer"
              defaultValue={settingsData.dailyGoal}
            >
              <option value="5개">5개</option>
              <option value="10개">10개</option>
              <option value="20개">20개</option>
              <option value="30개">30개</option>
            </select>
          </div>

          {/* 틀린 단어 다시보기 */}
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-50 text-orange-600 rounded-xl">
                <RotateCcw size={20} />
              </div>
              <span className="font-bold text-gray-700">틀린 단어 다시보기</span> {/*  */}
            </div>
            {/* 토글 스위치 예시 */}
            <div className="w-12 h-6 bg-green-500 rounded-full relative shadow-inner">
              <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm"></div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. 기타 액션 섹션 */}
      <section className="mt-8 px-4 space-y-3">
        {/* 로그아웃 */}
        <button className="w-full flex items-center gap-3 p-4 bg-white rounded-2xl border border-gray-100 text-gray-600 font-bold active:bg-gray-50 transition-colors">
          <LogOut size={20} />
          <span>로그아웃</span> {/*  */}
        </button>

        {/* 회원탈퇴 */}
        <button className="w-full flex items-center gap-3 p-4 bg-red-50 rounded-2xl border border-red-100 text-red-500 font-bold active:bg-red-100 transition-colors">
          <UserX size={20} />
          <span>회원탈퇴</span> {/*  */}
        </button>
      </section>
    </div>
  );
}