"use client";

import { usePathname } from "next/navigation";
import "./globals.css";
import TopNavBar from "./components/TopNavBar";
import BottomNavBar from "./components/BottomNavBar";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();

  // 상단/하단 메뉴를 숨길 경로 설정
  // '/'는 랜딩 화면, '/login'은 로그인 화면입니다.
  const hideNavigation = pathname === "/" || pathname === "/login";

  return (
    <html lang="ko">
      <body className="bg-gray-100 min-h-screen flex justify-center font-sans antialiased">
        {/* [모바일 앱 컨테이너] */}
        <div className="w-full max-w-[480px] min-h-screen bg-white shadow-2xl relative flex flex-col">
          
          {/* 네비게이션을 숨겨야 하는 경로가 아닐 때만 TopNavBar 표시 */}
          {!hideNavigation && <TopNavBar />}
          
          {/* 본문 영역 */}
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>

          {/* 네비게이션을 숨겨야 하는 경로가 아닐 때만 BottomNavBar 표시 */}
          {!hideNavigation && <BottomNavBar />}
          
        </div>
      </body>
    </html>
  );
}