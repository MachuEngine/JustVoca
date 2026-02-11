"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Layers, BarChart3, Settings } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function BottomNavBar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const [userRole, setUserRole] = useState<string | null>(null);

  useEffect(() => {
    const role = localStorage.getItem('userRole');
    setUserRole(role);
  }, []);

  // 학생용 메뉴
  const studentMenuItems = [
    { name: t('nav_home'), href: "/student_home", icon: Home },
    { name: t('nav_level'), href: "/levels", icon: Layers },
    { name: t('nav_stats'), href: "/stats", icon: BarChart3 },
    { name: t('nav_settings'), href: "/settings", icon: Settings },
  ];

  // 선생님용 메뉴
  const teacherMenuItems = [
    { name: t('nav_home'), href: "/teacher_dash", icon: Home },
    { name: t('nav_settings'), href: "/settings", icon: Settings },
  ];

  // 관리자용 메뉴
  const adminMenuItems = [
    { name: t('nav_home'), href: "/system_dash", icon: Home },
    { name: t('nav_settings'), href: "/settings", icon: Settings },
  ];

  // 역할에 따라 메뉴 결정
  let menuItems = studentMenuItems;
  if (userRole === 'admin') {
    menuItems = adminMenuItems;
  } else if (userRole === 'teacher') {
    menuItems = teacherMenuItems;
  }

  return (
    <nav className="sticky bottom-0 w-full h-16 bg-white border-t border-gray-100 z-50 flex-shrink-0">
      <div className="flex items-center justify-around px-2 h-full max-w-screen-xl mx-auto w-full">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center w-full h-full gap-1 transition-colors ${
                isActive ? "text-[#20385F]" : "text-gray-400 hover:text-gray-600"
              }`}
            >
              <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-[11px] font-bold tracking-tighter">
                {item.name}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}