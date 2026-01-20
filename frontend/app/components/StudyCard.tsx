// frontend/app/components/StudyCard.tsx
"use client";
import type { ReactNode } from "react";

export function StudyCard({
  word,
  example,
  isFront,
  onFlip,
  onPrev,
  onNext,
  canPrev,
  canNext,
  rightButton,
}: {
  word: string;
  example: string;
  isFront: boolean;
  onFlip: () => void;
  onPrev: () => void;
  onNext: () => void;
  canPrev: boolean;
  canNext: boolean;
  rightButton: ReactNode;
}) {
  return (
    <div
      onClick={onFlip} // [수정 1] 클릭 이벤트를 최상위 컨테이너로 이동 (여백 클릭 시 동작)
      style={{
        width: 340,
        borderRadius: 22,
        background: "white",
        padding: 16,
        boxShadow: "0 10px 28px rgba(0,0,0,0.12)",
        cursor: "pointer", // 클릭 가능함을 보여주는 커서
        position: "relative",
      }}
    >
      {/* 텍스트 표시 영역 (회색 박스) */}
      <div
        style={{
          height: 220,
          borderRadius: 18,
          background: "#f6f8ff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 14,
          textAlign: "center",
          fontWeight: 900,
          fontSize: isFront ? 34 : 18,
          // 내부 onClick 제거 (부모 div의 이벤트가 동작함)
        }}
      >
        {isFront ? word : example}
      </div>

      <div style={{ height: 14 }} />

      {/* 이전/다음 버튼 영역 */}
      <div style={{ display: "flex", gap: 10 }}>
        <button
          onClick={(e) => {
            e.stopPropagation(); // [수정 2] 버튼 클릭 시 카드 뒤집힘 방지
            onPrev();
          }}
          disabled={!canPrev}
          style={{
            flex: 1,
            height: 44,
            borderRadius: 14,
            cursor: canPrev ? "pointer" : "default", // 비활성화 시 커서 처리
            opacity: canPrev ? 1 : 0.5, // 비활성화 시 시각적 처리 (선택사항)
          }}
        >
          이전
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation(); // [수정 2] 버튼 클릭 시 카드 뒤집힘 방지
            onNext();
          }}
          disabled={!canNext}
          style={{
            flex: 1,
            height: 44,
            borderRadius: 14,
            cursor: canNext ? "pointer" : "default",
            opacity: canNext ? 1 : 0.5,
          }}
        >
          다음
        </button>
      </div>

      <div style={{ height: 12 }} />

      {/* 우측 하단 버튼 (녹음/듣기 등) 영역 */}
      <div
        onClick={(e) => e.stopPropagation()} // [수정 3] 기능 버튼 영역 클릭 시 카드 뒤집힘 방지
        style={{ display: "flex", justifyContent: "center" }}
      >
        {rightButton}
      </div>
    </div>
  );
}