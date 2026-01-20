"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Layers, BarChart3, Settings } from "lucide-react";

export default function BottomNavBar() {
  const pathname = usePathname();
  const [userRole, setUserRole] = useState<string | null>(null);

  useEffect(() => {
    // 클라이언트 사이드에서만 로컬 스토리지 접근
    const role = localStorage.getItem('userRole');
    setUserRole(role);
  }, []);

  // 학생용 메뉴
  const studentMenuItems = [
    { name: "홈", href: "/student_home", icon: Home },
    { name: "레벨", href: "/levels", icon: Layers },
    { name: "통계", href: "/stats", icon: BarChart3 },
    { name: "설정", href: "/settings", icon: Settings },
  ];

  // 선생님용 메뉴 (홈 -> 선생님 대시보드 연결)
  const teacherMenuItems = [
    { name: "홈", href: "/teacher_dash", icon: Home },
    { name: "설정", href: "/settings", icon: Settings },
  ];

  // 역할에 따라 메뉴 결정
  const menuItems = (userRole === 'teacher' || userRole === 'admin') 
    ? teacherMenuItems 
    : studentMenuItems;

  return (
    <nav className="sticky bottom-0 w-full h-16 bg-white border-t border-gray-100 flex items-center justify-around px-2 z-50 flex-shrink-0">
      {menuItems.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.href;

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center justify-center w-full h-full gap-1 transition-colors ${
              isActive ? "text-green-600" : "text-gray-400 hover:text-gray-600"
            }`}
          >
            <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
            <span className="text-[11px] font-bold tracking-tighter">
              {item.name}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}