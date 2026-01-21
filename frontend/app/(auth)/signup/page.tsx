"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  ChevronLeft, User, Mail, Lock, Globe, CheckSquare, Square, 
  UserCheck, BadgeCheck, Phone, Loader2, GraduationCap 
} from 'lucide-react';
// [중요] api.ts에서 함수 불러오기
import { checkIdDuplicate, signup } from '../../api';

export default function SignupPage() {
  const router = useRouter();
  
  // 1. 입력값 상태 관리 (teacherId 추가됨)
  const [formData, setFormData] = useState({
    name: "",
    id: "",
    email: "",
    password: "",
    confirmPassword: "",
    phone: "",
    country: "",
    role: "student", // 기본값
    teacherId: ""    // [추가] 선생님 ID
  });

  // 2. UI 상태 관리
  const [isTeacher, setIsTeacher] = useState(false);
  const [isIdChecked, setIsIdChecked] = useState(false);
  const [isIdAvailable, setIsIdAvailable] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // 입력값 변경 핸들러
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // 아이디를 고치면 중복확인을 다시 해야 함 -> 상태 초기화
    if (name === "id") {
      setIsIdChecked(false);
      setIsIdAvailable(null);
    }
  };

  // 선생님 <-> 학생 전환
  const toggleRole = () => {
    const newIsTeacher = !isTeacher;
    setIsTeacher(newIsTeacher);
    // 선생님으로 전환하면 teacherId 초기화 (선생님은 선생님 ID 필요 없음)
    setFormData(prev => ({ 
      ...prev, 
      role: newIsTeacher ? "teacher" : "student",
      teacherId: "" 
    }));
  };

  // 실제 백엔드 API로 중복 확인
  const handleIdCheck = async () => {
    if (!formData.id.trim()) {
      alert("아이디를 입력해주세요.");
      return;
    }

    try {
      const res = await checkIdDuplicate(formData.id);
      setIsIdAvailable(res.is_available);
      setIsIdChecked(true);
      
      if (!res.is_available) {
        alert("이미 사용 중인 아이디입니다.");
      } else {
        alert("사용 가능한 아이디입니다.");
      }
    } catch (error) {
      console.error("중복 확인 에러:", error);
      alert("중복 확인 중 서버 오류가 발생했습니다.");
    }
  };

  // 실제 백엔드 API로 회원가입 요청
  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    // 필수 입력값 검사
    if (!formData.name || !formData.id || !formData.password || !formData.email || !formData.phone || !formData.country) {
      alert("필수 정보를 모두 입력해주세요.");
      return;
    }
    
    // 중복 확인 여부 검사
    if (!isIdChecked || !isIdAvailable) {
      alert("아이디 중복 확인을 해주세요.");
      return;
    }

    // 비밀번호 일치 검사
    if (formData.password !== formData.confirmPassword) {
      alert("비밀번호가 일치하지 않습니다.");
      return;
    }

    setIsLoading(true);

    try {
      // 전송할 데이터 정리 (confirmPassword 제외, teacherId는 스네이크케이스로 변환 등 백엔드 스펙에 맞춤)
      const submitData = {
        id: formData.id,
        password: formData.password,
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        country: formData.country,
        role: formData.role,
        // teacherId가 있을 때만 보냄 (키 이름은 백엔드 스키마 teacher_id에 맞춤)
        teacher_id: formData.teacherId || undefined 
      };
      
      const res = await signup(submitData);

      if (res.status === "ok") {
        alert("회원가입이 완료되었습니다! 로그인해주세요.");
        router.push("/login");
      }
    } catch (error: any) {
      console.error("회원가입 실패:", error);
      alert("회원가입에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white p-6 overflow-y-auto">
      <header className="h-14 flex items-center -ml-2 mb-4 flex-shrink-0">
        <Link href="/login" className="p-2 rounded-full hover:bg-gray-100 transition-colors">
          <ChevronLeft size={28} className="text-gray-800" />
        </Link>
      </header>

      <div className="flex-1 pb-10">
        <div className="mb-8">
          <h1 className="text-3xl font-black text-gray-900 mb-3 leading-tight">회원가입</h1>
          <p className="text-gray-500 font-medium">한국어 학습을 시작해보세요</p>
        </div>

        <form className="space-y-5" onSubmit={handleSignup}>
          {/* 역할 선택 */}
          <div onClick={toggleRole} className="flex items-center gap-2 cursor-pointer mb-2 w-fit px-1">
            {isTeacher 
              ? <CheckSquare className="text-green-600" size={22} /> 
              : <Square className="text-gray-300" size={22} />
            }
            <span className={`text-sm font-bold transition-colors ${isTeacher ? 'text-green-600' : 'text-gray-400'}`}>
              선생님으로 가입하기
            </span>
          </div>

          <div className="space-y-4">
            {/* 이름 */}
            <div className="relative">
              <UserCheck className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="text" name="name" placeholder="이름" 
                value={formData.name} onChange={handleChange}
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 font-bold text-gray-800"
              />
            </div>

            {/* 아이디 & 중복확인 */}
            <div className="space-y-2">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                  <input 
                    type="text" name="id" placeholder="아이디" 
                    value={formData.id} onChange={handleChange}
                    className={`w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none font-bold text-gray-800 transition-all ${
                      isIdChecked 
                        ? (isIdAvailable ? 'ring-2 ring-green-500 bg-green-50' : 'ring-2 ring-red-500 bg-red-50') 
                        : 'focus:ring-2 focus:ring-green-500'
                    }`}
                  />
                </div>
                <button 
                  type="button" onClick={handleIdCheck}
                  className={`px-4 font-bold rounded-2xl text-sm transition-colors whitespace-nowrap ${
                    isIdChecked && isIdAvailable 
                    ? "bg-green-600 text-white" 
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  중복확인
                </button>
              </div>
              {isIdChecked && (
                <p className={`text-xs ml-4 font-bold ${isIdAvailable ? 'text-green-600' : 'text-red-500'}`}>
                  {isIdAvailable ? "사용 가능한 아이디입니다." : "이미 사용 중인 아이디입니다."}
                </p>
              )}
            </div>

            {/* 이메일 */}
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="email" name="email" placeholder="이메일" 
                value={formData.email} onChange={handleChange}
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 font-bold text-gray-800"
              />
            </div>

            {/* 전화번호 */}
            <div className="relative">
              <Phone className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="tel" name="phone" placeholder="전화번호" 
                value={formData.phone} onChange={handleChange}
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 font-bold text-gray-800"
              />
            </div>

            {/* 국적 */}
            <div className="relative">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <select 
                name="country" value={formData.country} onChange={handleChange}
                className="w-full h-16 pl-12 pr-10 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 font-bold text-gray-800 appearance-none"
              >
                <option value="">국적을 선택해주세요</option>
                <option value="KR">한국 (Korea)</option>
                <option value="US">미국 (USA)</option>
                <option value="VN">베트남 (Vietnam)</option>
                <option value="JP">일본 (Japan)</option>
                <option value="CN">중국 (China)</option>
              </select>
            </div>

            {/* [신규 추가] 선생님 ID 입력 (학생일 때만 보임) */}
            {!isTeacher && (
              <div className="relative animate-in fade-in slide-in-from-top-2">
                <GraduationCap className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                <input 
                  type="text" name="teacherId" placeholder="선생님 ID (선택 사항)" 
                  value={formData.teacherId} onChange={handleChange}
                  className="w-full h-16 pl-12 pr-4 bg-blue-50 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-bold text-gray-800 placeholder:text-gray-400"
                />
              </div>
            )}

            {/* 비밀번호 */}
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="password" name="password" placeholder="비밀번호" 
                value={formData.password} onChange={handleChange}
                className="w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-green-500 font-bold text-gray-800"
              />
            </div>

            {/* 비밀번호 확인 */}
            <div className="relative">
              <BadgeCheck className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="password" name="confirmPassword" placeholder="비밀번호 확인" 
                value={formData.confirmPassword} onChange={handleChange}
                className={`w-full h-16 pl-12 pr-4 bg-gray-50 rounded-2xl outline-none font-bold text-gray-800 transition-all ${
                  formData.confirmPassword && formData.password !== formData.confirmPassword
                    ? "ring-2 ring-red-500 bg-red-50"
                    : "focus:ring-2 focus:ring-green-500"
                }`}
              />
            </div>
          </div>

          {/* 가입 완료 버튼 */}
          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full h-16 bg-gray-900 text-white font-bold rounded-2xl text-lg hover:bg-black active:scale-[0.98] transition-all shadow-lg mt-6 flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="animate-spin" />}
            회원가입
          </button>
        </form>

        <div className="mt-8 text-center pb-8">
          <p className="text-gray-400 text-sm font-medium">
            이미 계정이 있으신가요?{" "}
            <Link href="/login" className="text-green-600 font-black hover:underline ml-1">
              로그인
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}