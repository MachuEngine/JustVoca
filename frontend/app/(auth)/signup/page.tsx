"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  ChevronLeft, 
  User, 
  Mail, 
  Lock, 
  Globe, 
  CheckSquare, 
  Square, 
  UserCheck, 
  BadgeCheck 
} from 'lucide-react';

export default function SignupPage() {
  const router = useRouter();
  const [isTeacher, setIsTeacher] = useState(false); // 선생님 여부 체크 [cite: 36]
  
  // 중복확인 관련 상태 관리
  const [userId, setUserId] = useState("");
  const [isIdChecked, setIsIdChecked] = useState(false); // 중복확인 버튼 클릭 여부
  const [isIdAvailable, setIsIdAvailable] = useState<boolean | null>(null); // 아이디 사용 가능 여부

  // 아이디 중복확인 함수 (모의 로직) 
  const handleIdCheck = () => {
    if (!userId.trim()) {
      alert("아이디를 입력해주세요.");
      return;
    }

    // 예시: 'admin'이나 'test'는 중복된 것으로 가정
    const duplicateIds = ["admin", "test", "user1"];
    
    if (duplicateIds.includes(userId)) {
      setIsIdAvailable(false);
    } else {
      setIsIdAvailable(true);
    }
    setIsIdChecked(true);
  };

  return (
    <div className="h-full flex flex-col bg-white p-6 overflow-y-auto">
      {/* 1. 상단 뒤로가기 [cite: 195] */}
      <header className="h-14 flex items-center -ml-2 mb-4 flex-shrink-0">
        <Link href="/login" className="p-2 rounded-full hover:bg-gray-100 transition-colors">
          <ChevronLeft size={28} className="text-gray-800" />
        </Link>
      </header>

      <div className="flex-1 pb-10">
        <div className="mb-8">
          <h1 className="text-3xl font-black text-gray-900 mb-3 leading-tight">
            회원가입 {/* [cite: 34] */}
          </h1>
          <p className="text-gray-500 font-medium">
            한국어 학습을 시작해보세요 {/* [cite: 35] */}
          </p>
        </div>

        <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
          {/* 2. 선생님/관리자 체크박스 [cite: 36] */}
          <div 
            onClick={() => setIsTeacher(!isTeacher)}
            className="flex items-center gap-2 cursor-pointer mb-2 w-fit px-1"
          >
            {isTeacher 
              ? <CheckSquare className="text-green-600" size={22} /> 
              : <Square className="text-gray-300" size={22} />
            }
            <span className={`text-sm font-bold transition-colors ${isTeacher ? 'text-green-600' : 'text-gray-400'}`}>
              선생님으로 가입하기
            </span>
          </div>

          <div className="space-y-4">
            {/* 이름 입력 [cite: 37] */}
            <div className="relative">
              <UserCheck className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="text" 
                placeholder="이름" 
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 transition-all font-bold text-gray-800"
              />
            </div>

            {/* 아이디 입력 및 중복확인 [cite: 39, 41] */}
            <div className="space-y-2">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                  <input 
                    type="text" 
                    placeholder="아이디" 
                    value={userId}
                    onChange={(e) => {
                      setUserId(e.target.value);
                      setIsIdChecked(false); // 입력값이 바뀌면 다시 중복확인 하도록 초기화
                    }}
                    className={`w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none transition-all font-bold text-gray-800 ${
                      isIdChecked ? (isIdAvailable ? 'ring-2 ring-green-500' : 'ring-2 ring-red-500') : 'focus:ring-2 focus:ring-green-500'
                    }`}
                  />
                </div>
                <button 
                  type="button"
                  onClick={handleIdCheck}
                  className={`px-4 font-bold rounded-2xl text-sm transition-colors ${
                    isIdChecked && isIdAvailable 
                    ? "bg-green-600 text-white" 
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  중복확인 {/*  */}
                </button>
              </div>
              {/* 중복확인 결과 메시지 */}
              {isIdChecked && (
                <p className={`text-xs ml-4 font-bold ${isIdAvailable ? 'text-green-600' : 'text-red-500'}`}>
                  {isIdAvailable ? "사용 가능한 아이디입니다." : "이미 사용 중인 아이디입니다."}
                </p>
              )}
            </div>

            {/* 이메일 입력 [cite: 42] */}
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="email" 
                placeholder="이메일 (example@email.com)" 
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 transition-all font-bold text-gray-800"
              />
            </div>

            {/* 국적 정보 [cite: 56] */}
            <div className="relative">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <select className="w-full h-16 pl-12 pr-10 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 font-bold text-gray-800 appearance-none">
                <option value="">국적을 선택해주세요</option>
                <option value="US">미국 (USA)</option>
                <option value="VN">베트남 (Vietnam)</option>
                <option value="JP">일본 (Japan)</option>
                <option value="CN">중국 (China)</option>
              </select>
            </div>

            {/* 비밀번호 [cite: 44] 및 확인 [cite: 45] */}
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="password" 
                placeholder="비밀번호" 
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 transition-all font-bold text-gray-800"
              />
            </div>

            <div className="relative">
              <BadgeCheck className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="password" 
                placeholder="비밀번호 확인" 
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 transition-all font-bold text-gray-800"
              />
            </div>
          </div>

          {/* 가입 완료 버튼 [cite: 51] */}
          <button className="w-full h-16 bg-gray-900 text-white font-bold rounded-2xl text-lg hover:bg-black active:scale-[0.98] transition-all shadow-lg mt-6">
            회원가입
          </button>
        </form>

        <div className="mt-8 text-center pb-8">
          <p className="text-gray-400 text-sm font-medium">
            이미 계정이 있으신가요?{" "}
            <Link href="/login" className="text-green-600 font-black hover:underline ml-1">
              로그인 {/* [cite: 52] */}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}