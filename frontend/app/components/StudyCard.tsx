// app/components/StudyCard.tsx
"use client";

import { useState, useEffect } from "react";
import { Volume2 } from "lucide-react";
import { motion } from "framer-motion";

interface StudyCardProps {
  word: any;
  onPlayAudio?: () => void;
  autoPlay?: boolean;
}

export default function StudyCard({
  word,
  onPlayAudio,
  autoPlay = false,
}: StudyCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [imageError, setImageError] = useState(false);
  const imageUrl = word?.imageKey || "";

  // 발음 텍스트 포맷팅 (데이터가 있으면 대괄호 추가)
  const pronText = word?.pronunciation
    ? word.pronunciation.startsWith("[")
      ? word.pronunciation
      : `[${word.pronunciation}]`
    : "";

  useEffect(() => {
    setIsFlipped(false);
    setImageError(false);
    if (autoPlay) {
      const timer = setTimeout(() => playAudio(), 500);
      return () => clearTimeout(timer);
    }
  }, [word, autoPlay]);

  const playAudio = () => {
    if (onPlayAudio) onPlayAudio();
    else if (word?.audioKey) {
      const audio = new Audio(word.audioKey);
      audio.play().catch((e) => console.error("Audio play error:", e));
    }
  };

  if (!word)
    return <div className="w-full aspect-[3/4] bg-gray-100 rounded-[2.5rem]" />;

  return (
    <div
      className="relative w-full aspect-[3/4] perspective-1000 cursor-pointer group"
      onClick={() => setIsFlipped(!isFlipped)}
    >
      <motion.div
        className="w-full h-full relative preserve-3d transition-transform duration-500"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        style={{ transformStyle: "preserve-3d" }}
      >
        {/* ================= [앞면] ================= */}
        <div className="absolute inset-0 backface-hidden bg-white rounded-[2.5rem] shadow-xl border border-gray-100 p-5 flex flex-col items-center justify-between text-center pb-7">
          {/* 1. 이미지 영역 */}
          <div className="w-full flex justify-center mt-1">
            <div className="w-32 h-32 relative rounded-2xl overflow-hidden bg-gray-50 flex items-center justify-center shadow-inner">
              {imageUrl && !imageError ? (
                <img
                  key={imageUrl}
                  src={imageUrl}
                  alt={word.word}
                  className="w-full h-full object-cover"
                  onError={() => setImageError(true)}
                />
              ) : (
                <span className="text-6xl select-none opacity-20">📖</span>
              )}
            </div>
          </div>

          {/* 2. 텍스트 영역 */}
          <div className="flex-1 flex flex-col items-center justify-center w-full gap-1">
            {/* 단어 + [발음] (폰트 축소) */}
            <h2 className="text-2xl font-black text-gray-900 mb-2 break-keep flex items-baseline gap-2 flex-wrap justify-center leading-tight">
              {word.word}
              {pronText && (
                <span className="text-base font-normal text-gray-500 transform -translate-y-1">
                  {pronText}
                </span>
              )}
            </h2>

            {/* 한글 뜻 (축소) */}
            <p className="text-base font-bold text-gray-400 break-keep leading-snug">
              {word.meaning || ""}
            </p>

            {/* 영어 뜻 (축소) */}
            <p className="text-xs text-gray-200 font-medium">
              {word.meaningEng || ""}
            </p>
          </div>

          {/* 3. 하단 버튼 */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              playAudio();
            }}
            className="mb-1 px-6 py-3 bg-gray-900 text-white rounded-xl flex items-center gap-2 shadow-lg active:scale-95 transition-transform"
          >
            <Volume2 size={18} />
            <span className="font-bold text-xs">발음 듣기</span>
          </button>
        </div>

        {/* ================= [뒷면] ================= */}
        <div
          className="absolute inset-0 backface-hidden bg-white rounded-[2.5rem] shadow-xl border border-blue-100 p-7 flex flex-col items-center justify-center text-center bg-gradient-to-br from-blue-50 to-white"
          style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
        >
          <div className="w-full flex justify-center mb-5">
            <span className="px-3 py-1 bg-blue-100 text-blue-600 rounded-full text-[11px] font-bold tracking-wide">
              Example
            </span>
          </div>

          <div className="flex-1 flex items-center justify-center">
            <p className="text-lg font-medium text-gray-800 leading-relaxed break-keep">
              {word.example ? `"${word.example}"` : `"${word.word}"`}
            </p>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              playAudio();
            }}
            className="mt-5 w-12 h-12 flex items-center justify-center rounded-full bg-white border border-gray-200 shadow-sm text-gray-600 hover:text-blue-600 active:scale-90 transition-all"
          >
            <Volume2 size={18} />
          </button>
        </div>
      </motion.div>
    </div>
  );
}
