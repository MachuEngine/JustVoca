"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { User, Lock, ChevronLeft, CheckSquare, Square } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [isTeacher, setIsTeacher] = useState(false); // 선생님 여부 체크

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // 로그인 로직 (나중에 API 연결)
    if (isTeacher) {
      router.push('/teacher_dash'); // 선생님이면 대시보드로 이동
    } else {
      router.push('/student_home'); // 학생이면 홈으로 이동
    }
  };

  return (
    <div className="h-full flex flex-col bg-white p-6">
      {/* 1. 상단 뒤로가기 버튼 */}
      <header className="h-14 flex items-center -ml-2 mb-4">
        <Link href="/" className="p-2 rounded-full hover:bg-gray-100 transition-colors">
          <ChevronLeft size={28} className="text-gray-800" />
        </Link>
      </header>

      <div className="flex-1 flex flex-col justify-center pb-20">
        {/* 2. 타이틀 영역 */}
        <div className="mb-10">
          <h1 className="text-3xl font-black text-gray-900 mb-3 leading-tight">
            환영합니다! 👋
          </h1>
          <p className="text-gray-500 font-medium">
            {isTeacher ? '선생님, 오늘 수업도 파이팅하세요!' : '한국어 학습을 시작해보세요.'}
          </p>
        </div>

        {/* 3. 로그인 폼 */}
        <form onSubmit={handleLogin} className="space-y-5">
          {/* 선생님/관리자 체크박스 */}
          <div 
            onClick={() => setIsTeacher(!isTeacher)}
            className="flex items-center gap-2 cursor-pointer mb-2 w-fit px-1"
          >
            {isTeacher 
              ? <CheckSquare className="text-green-600" size={22} /> 
              : <Square className="text-gray-300" size={22} />
            }
            <span className={`text-sm font-bold transition-colors ${isTeacher ? 'text-green-600' : 'text-gray-400'}`}>
              선생님/관리자 로그인
            </span>
          </div>

          <div className="space-y-4">
            {/* 아이디 입력창 */}
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="text" 
                placeholder="아이디" 
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 transition-all font-bold text-gray-800 border border-transparent"
              />
            </div>
            {/* 비밀번호 입력창 */}
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="password" 
                placeholder="비밀번호" 
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 transition-all font-bold text-gray-800 border border-transparent"
              />
            </div>
          </div>

          {/* 로그인 버튼 */}
          <button className="w-full h-16 bg-gray-900 text-white font-bold rounded-2xl text-lg hover:bg-black active:scale-[0.98] transition-all shadow-lg mt-8">
            로그인
          </button>
        </form>

        {/* 4. 하단 회원가입 유도 링크 */}
        <div className="mt-12 text-center">
          <Link href="/signup" className="text-green-600 font-bold hover:underline text-sm tracking-tight">
            아직 회원이 아니신가요? 회원가입 하러가기
          </Link>
        </div>
      </div>
    </div>
  );
}