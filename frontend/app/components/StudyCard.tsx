// app/components/StudyCard.tsx
"use client";

import { useState, useEffect } from "react";
import { Volume2, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";

// 단어 데이터 타입 정의
interface Word {
  id: number;
  word: string;
  meaning: string;
  eng_meaning: string;
  example: string;
  audio_path: string;
  level: string;
  topic: string;
}

// 컴포넌트 Props 정의
interface StudyCardProps {
  word: Word;
  onPlayAudio?: () => void;
  autoPlay?: boolean;
}

// [핵심 수정] export default로 변경하여 import 에러 방지
export default function StudyCard({ word, onPlayAudio, autoPlay = false }: StudyCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);

  // 단어가 변경될 때마다 앞면으로 초기화
  useEffect(() => {
    setIsFlipped(false);
    if (autoPlay) {
      const timer = setTimeout(() => {
        playAudio();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [word, autoPlay]);

  const playAudio = () => {
    if (onPlayAudio) {
      onPlayAudio();
    } else if (word?.audio_path) {
      try {
        const audioSrc = word.audio_path.startsWith("http")
          ? word.audio_path
          : `/assets/audio/${word.audio_path}`;
        const audio = new Audio(audioSrc);
        audio.play().catch((e) => console.log("Audio play failed", e));
      } catch (e) {
        console.error("Audio error", e);
      }
    }
  };

  // 데이터가 없을 경우 에러 방지용 빈 박스 렌더링
  if (!word) return <div className="w-full aspect-[4/5] bg-gray-100 rounded-[2.5rem]" />;

  return (
    <div
      className="relative w-full aspect-[4/5] perspective-1000 cursor-pointer group"
      onClick={() => setIsFlipped(!isFlipped)}
    >
      <motion.div
        className="w-full h-full relative preserve-3d transition-transform duration-500"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ duration: 0.6, type: "spring", stiffness: 260, damping: 20 }}
        style={{ transformStyle: "preserve-3d" }}
      >
        {/* --- [앞면] 단어 --- */}
        <div
          className="absolute inset-0 backface-hidden bg-white rounded-[2.5rem] shadow-xl border border-gray-100 p-8 flex flex-col items-center justify-center text-center"
          style={{ backfaceVisibility: "hidden" }}
        >
          <div className="flex-1 flex flex-col items-center justify-center">
            <h2 className="text-5xl font-black text-gray-900 mb-6 break-keep">
              {word.word}
            </h2>
            <div className="space-y-2">
              <p className="text-2xl font-bold text-gray-700 break-keep leading-snug">
                {word.meaning}
              </p>
              <p className="text-lg text-gray-400 font-medium">
                {word.eng_meaning}
              </p>
            </div>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              playAudio();
            }}
            className="mb-4 px-8 py-4 bg-gray-900 text-white rounded-2xl flex items-center gap-2 shadow-lg active:scale-95 transition-transform hover:bg-gray-800"
          >
            <Volume2 size={24} />
            <span className="font-bold">발음 듣기</span>
          </button>

          <div className="text-gray-300 text-sm font-medium flex items-center gap-1">
            <RefreshCw size={12} />
            터치하여 뒤집기
          </div>
        </div>

        {/* --- [뒷면] 예문 --- */}
        <div
          className="absolute inset-0 backface-hidden bg-white rounded-[2.5rem] shadow-xl border border-blue-100 p-8 flex flex-col items-center justify-center text-center bg-gradient-to-br from-blue-50 to-white"
          style={{
            backfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
          }}
        >
          <div className="w-full text-left border-l-4 border-blue-500 pl-4 mb-8">
            <span className="text-xs font-black text-blue-500 uppercase tracking-widest">
              Example
            </span>
            <h3 className="text-xl font-bold text-gray-900 mt-1">{word.word}</h3>
          </div>

          <div className="flex-1 flex items-center justify-center">
            <p className="text-xl font-medium text-gray-800 leading-relaxed break-keep px-2">
              "{word.example}"
            </p>
          </div>

          <div className="w-full mt-8">
            <button
              onClick={(e) => {
                e.stopPropagation();
                playAudio();
              }}
              className="w-full py-4 bg-white border border-blue-200 text-blue-600 rounded-2xl font-bold flex items-center justify-center gap-2 shadow-sm active:bg-blue-50"
            >
              <Volume2 size={20} />
              듣기
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}