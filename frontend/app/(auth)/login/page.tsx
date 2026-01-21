"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { User, Lock, ChevronLeft, Loader2 } from 'lucide-react';
// api.ts에서 login 함수 임포트 (fetch 대신 사용 권장)
import { login } from '../../api';

export default function LoginPage() {
  const router = useRouter();
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
      // 1. 백엔드 API 호출 (api.ts의 login 함수 사용)
      const data = await login(id, password);

      // 2. 로그인 성공 시 처리
      localStorage.setItem('userId', data.user.uid);
      localStorage.setItem('userRole', data.user.role);
      
      // 3. 역할별 페이지 자동 이동
      if (data.user.role === 'admin') {
         router.push('/system_dash');   // 관리자
      } else if (data.user.role === 'teacher') {
         router.push('/teacher_dash');  // 선생님
      } else {
         router.push('/student_home');  // 학생
      }

    } catch (error: any) {
      console.error("로그인 에러:", error);
      // api.ts에서 파싱해준 에러 메시지 표시
      const msg = error.response?.data?.detail || "로그인에 실패했습니다.";
      alert(msg);
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
            로그인하여 학습을 시작해보세요.
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
          {/* 체크박스 영역이 삭제되었습니다 */}

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