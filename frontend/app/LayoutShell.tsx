// app/LayoutShell.tsx
"use client";

import { usePathname } from "next/navigation";
import TopNavBar from "./components/TopNavBar";
import BottomNavBar from "./components/BottomNavBar";

export default function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hideNavigation = pathname === "/" || pathname === "/login";

  return (
    // [수정] max-w-[480px]와 shadow-2xl을 제거하여 전체 화면을 유동적으로 활용합니다.
    <div className="w-full min-h-screen bg-white relative flex flex-col">
      {!hideNavigation && <TopNavBar />}

      {/* [수정] 큰 화면에서 콘텐츠가 너무 퍼지지 않게 중앙 정렬(mx-auto) 및 최대 너비(max-w-screen-xl)를 적용합니다. */}
      <main className="flex-1 overflow-y-auto w-full max-w-screen-xl mx-auto px-4 sm:px-6">
        {children}
      </main>

      {!hideNavigation && <BottomNavBar />}
    </div>
  );
}