"use client";

import { usePathname } from "next/navigation";
import TopNavBar from "./components/TopNavBar";
import BottomNavBar from "./components/BottomNavBar";

export default function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hideNavigation = pathname === "/" || pathname === "/login";

  return (
    <div className="w-full max-w-[480px] min-h-screen bg-white shadow-2xl relative flex flex-col">
      {!hideNavigation && <TopNavBar />}

      <main className="flex-1 overflow-y-auto">{children}</main>

      {!hideNavigation && <BottomNavBar />}
    </div>
  );
}
