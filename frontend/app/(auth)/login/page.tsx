"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { User, Lock, ChevronLeft, CheckSquare, Square, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [isTeacher, setIsTeacher] = useState(false);
  const [id, setId] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!id || !password) {
      alert("아이디와 비밀번호를 입력해주세요.");
      return;
    }

    setIsLoading(true);

    try {
      // 1. 백엔드 API 호출 (진짜 로그인 검증)
      // [수정] credentials: "include" 옵션을 추가하여 서버가 주는 쿠키를 저장하도록 설정합니다.
      const res = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, password }),
        credentials: "include" // <--- [핵심 수정] 이 줄이 있어야 쿠키가 저장됩니다!
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.detail || "로그인에 실패했습니다.");
        setIsLoading(false);
        return;
      }

      // 2. 로그인 성공 시 처리
      // 받은 유저 정보를 로컬 스토리지에 저장 (나중에 프로필 조회 등에 사용)
      localStorage.setItem('userId', data.user.uid);
      localStorage.setItem('userRole', data.user.role);
      
      // 역할에 따라 페이지 이동
      if (data.user.role === 'teacher' || data.user.role === 'admin') {
         router.push('/teacher_dash');
      } else {
         router.push('/student_home');
      }

    } catch (error) {
      console.error("로그인 에러:", error);
      alert("서버와 통신 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white p-6">
      <header className="h-14 flex items-center -ml-2 mb-4">
        <Link href="/" className="p-2 rounded-full hover:bg-gray-100 transition-colors">
          <ChevronLeft size={28} className="text-gray-800" />
        </Link>
      </header>

      <div className="flex-1 flex flex-col justify-center pb-20">
        <div className="mb-10">
          <h1 className="text-3xl font-black text-gray-900 mb-3 leading-tight">
            환영합니다! 👋
          </h1>
          <p className="text-gray-500 font-medium">
            {isTeacher ? '선생님, 오늘 수업도 파이팅하세요!' : '한국어 학습을 시작해보세요.'}
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
          {/* 역할 선택 (단순 UI용 상태 변경) */}
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
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="text" 
                placeholder="아이디" 
                value={id}
                onChange={(e) => setId(e.target.value)}
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 transition-all font-bold text-gray-800 border border-transparent"
              />
            </div>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="password" 
                placeholder="비밀번호" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 transition-all font-bold text-gray-800 border border-transparent"
              />
            </div>
          </div>

          <button 
            disabled={isLoading}
            className="w-full h-16 bg-gray-900 text-white font-bold rounded-2xl text-lg hover:bg-black active:scale-[0.98] transition-all shadow-lg mt-8 flex items-center justify-center"
          >
            {isLoading ? <Loader2 className="animate-spin" /> : "로그인"}
          </button>
        </form>

        <div className="mt-12 text-center">
          <Link href="/signup" className="text-green-600 font-bold hover:underline text-sm tracking-tight">
            아직 회원이 아니신가요? 회원가입 하러가기
          </Link>
        </div>
      </div>
    </div>
  );
}