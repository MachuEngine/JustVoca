"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Layers, BarChart3, Settings } from "lucide-react";

export default function BottomNavBar() {
  const pathname = usePathname();

  // [수정] 레벨 메뉴의 href를 /level_select에서 /levels로 변경
  const menuItems = [
    { 
      name: "홈", 
      href: "/student_home", 
      icon: Home 
    },
    { 
      name: "레벨", 
      href: "/levels", // [변경 포인트]
      icon: Layers 
    },
    { 
      name: "통계", 
      href: "/stats", 
      icon: BarChart3 
    },
    { 
      name: "설정", 
      href: "/settings", 
      icon: Settings 
    },
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