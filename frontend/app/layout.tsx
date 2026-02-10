// app/layout.tsx
import "./globals.css";
import LayoutShell from "./LayoutShell";
import Chatbot from "./components/Chatbot";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      {/* [수정] bg-gray-100 대신 bg-white를 사용하고, justify-center를 제거하여 유동적인 배치를 허용합니다. */}
      <body className="bg-white min-h-screen font-sans antialiased">
        <LayoutShell>{children}</LayoutShell>

        <Chatbot />
      </body>
    </html>
  );
}