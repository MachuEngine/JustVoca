import Link from 'next/link';
import { BookOpen } from 'lucide-react'; // 아이콘 라이브러리

export default function LandingPage() {
  return (
    <Link href="/login" className="block">
      {/* 부모 layout.tsx의 min-h-screen과 충돌하지 않도록 
        컨테이너 높이를 h-[calc(100vh-64px)] 정도로 조절하거나, 
        전체 화면을 채우도록 설정합니다.
      */}
      <div className="min-h-[calc(100vh-64px)] bg-green-50 flex flex-col items-center justify-center p-6 relative cursor-pointer hover:bg-green-100 transition-colors">
        
        {/* 중앙 로고 및 타이틀 영역 */}
        <div className="text-center space-y-6 animate-fade-in-up">
          {/* 로고 자리 (KR) */}
          <div className="w-24 h-24 bg-green-600 rounded-full flex items-center justify-center mx-auto shadow-lg mb-8">
            <span className="text-white text-3xl font-bold">KR</span>
          </div>

          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
            한국어 학습
          </h1>
          
          <div className="space-y-2">
            <p className="text-lg text-gray-600 font-medium">
              단어부터 발음, 진도 관리까지
            </p>
            <p className="text-sm text-gray-500">
              쉽고 체계적인 한국어 학습
            </p>
          </div>
          
          {/* BookOpen 아이콘 활용 예시 (필요시 사용) */}
          <div className="flex justify-center pt-4">
            <BookOpen className="w-8 h-8 text-green-600 opacity-50" />
          </div>
        </div>

        {/* 하단 안내 문구 */}
        <div className="absolute bottom-10 text-center animate-pulse">
          <p className="text-gray-400 text-sm mb-2">
            화면을 터치하면 학습을 시작합니다
          </p>
          <div className="w-1 h-12 bg-gradient-to-b from-gray-300 to-transparent mx-auto rounded-full"></div>
        </div>

      </div>
    </Link>
  );
}