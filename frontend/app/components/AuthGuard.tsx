"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
  allowedRoles?: string[]; // 예: ['teacher', 'admin']
}

export default function AuthGuard({ children, allowedRoles }: AuthGuardProps) {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    // 1. 로컬 스토리지에서 정보 확인
    const userId = localStorage.getItem('userId');
    const userRole = localStorage.getItem('userRole');

    if (!userId) {
      // 2. 로그인 안 된 상태 -> 로그인 페이지로 강제 이동
      // alert("로그인이 필요한 서비스입니다."); // 필요 시 주석 해제
      router.replace('/login');
    } else if (allowedRoles && userRole && !allowedRoles.includes(userRole)) {
      // 3. 로그인 했으나 권한이 없는 경우 (예: 학생이 선생님 페이지 접근)
      alert("접근 권한이 없습니다.");
      router.replace('/');
    } else {
      // 4. 통과
      setIsAuthorized(true);
    }
  }, [router, allowedRoles]);

  // 검사 중일 때는 로딩 화면 표시 (깜빡임 방지)
  if (!isAuthorized) {
    return (
      <div className="h-screen flex items-center justify-center bg-white">
        <Loader2 className="animate-spin text-green-600" size={40} />
      </div>
    );
  }

  // 검사 통과 시 실제 페이지 내용 렌더링
  return <>{children}</>;
}