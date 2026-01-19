"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
// 사양서의 메뉴 직관성을 위해 아이콘을 선정했습니다.
import { Home, Layers, BarChart3, Settings } from "lucide-react";

export default function BottomNavBar() {
  const pathname = usePathname();

  // 사양서 기준 하단 메뉴 구성 (홈 / 레벨 / 설정 / 통계) 
  // 
  const menuItems = [
    { 
      name: "홈", 
      href: "/student_home", 
      icon: Home 
    }, // [cite: 185]
    { 
      name: "레벨", 
      href: "/level_select", 
      icon: Layers 
    }, // 레벨 선택 
    { 
      name: "통계", 
      href: "/stats", 
      icon: BarChart3 
    }, // 
    { 
      name: "설정", 
      href: "/settings", 
      icon: Settings 
    }, // [cite: 187]
  ];

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
            {/* 아이콘 크기와 굵기 조절 */}
            <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
            {/* 사양서에 명시된 메뉴 명칭 [cite: 185-188] */}
            <span className="text-[11px] font-bold tracking-tighter">
              {item.name}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}