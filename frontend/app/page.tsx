import Link from 'next/link';
import { BookOpen, ChevronDown } from 'lucide-react';
// 구글 폰트에서 'Outfit' 폰트 가져오기
import { Outfit } from 'next/font/google';

// 폰트 설정 (굵은 웨이트 위주로 로드)
const logoFont = Outfit({ 
  subsets: ['latin'],
  weight: ['700', '800'], // Bold, ExtraBold
  display: 'swap',
});

export default function LandingPage() {
  return (
    <Link href="/login" className="block group">
      {/* 배경: 상단 진함 -> 하단 연함 그라데이션 */}
      <div className="min-h-screen bg-gradient-to-b from-[#ACC2E5] to-[#F5F9FF] flex flex-col items-center justify-center p-6 relative cursor-pointer hover:from-[#FFFCF7] hover:to-[#FFFCF7] transition-all duration-500">
        
        {/* 중앙 로고 및 타이틀 영역 */}
        <div className="text-center space-y-8 animate-fade-in-up flex flex-col items-center">
          
          {/* 로고 자리 (JustVoca) */}
          <div className="relative">
              {/* 폰트 적용: logoFont.className 추가 */}
              <span className={`text-[#20385F] text-6xl md:text-8xl font-extrabold tracking-tighter ${logoFont.className}`}>
                JustVoca
              </span>
          </div>

          <div className="space-y-4">
            {/* 메인 타이틀 */}
            <h1 className="text-2xl md:text-3xl font-extrabold text-[#20385F] tracking-tight drop-shadow-sm">
              한국어 학습
            </h1>
            
            <div className="space-y-2">
              {/* 서브 타이틀 */}
              <p className="text-xl text-[#20385F] font-bold opacity-90">
                단어부터 발음, 진도 관리까지
              </p>
              {/* 설명 텍스트 */}
              <p className="text-sm text-[#3665B2] font-medium">
                쉽고 체계적인 맞춤형 커리큘럼
              </p>
            </div>
          </div>
        </div>

        {/* 하단 안내 문구 */}
        <div className="absolute bottom-12 text-center animate-pulse flex flex-col items-center gap-2">
          <p className="text-[#132138] text-md font-medium opacity-60">
            화면을 터치하여 시작하기
          </p>
        </div>

      </div>
    </Link>
  );
}