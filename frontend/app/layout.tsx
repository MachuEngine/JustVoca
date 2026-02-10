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
      <body className="bg-gray-100 min-h-screen flex justify-center font-sans antialiased">
        <LayoutShell>{children}</LayoutShell>

        <Chatbot />
      </body>
    </html>
  );
}
