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
      style={{
        width: 340,
        borderRadius: 22,
        background: "white",
        padding: 16,
        boxShadow: "0 10px 28px rgba(0,0,0,0.12)",
      }}
    >
      <div
        onClick={onFlip}
        style={{
          height: 220,
          borderRadius: 18,
          background: "#f6f8ff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          padding: 14,
          textAlign: "center",
          fontWeight: 900,
          fontSize: isFront ? 34 : 18,
        }}
      >
        {isFront ? word : example}
      </div>

      <div style={{ height: 14 }} />

      <div style={{ display: "flex", gap: 10 }}>
        <button
          onClick={onPrev}
          disabled={!canPrev}
          style={{ flex: 1, height: 44, borderRadius: 14 }}
        >
          이전
        </button>

        <button
          onClick={onNext}
          disabled={!canNext}
          style={{ flex: 1, height: 44, borderRadius: 14 }}
        >
          다음
        </button>
      </div>

      <div style={{ height: 12 }} />

      <div style={{ display: "flex", justifyContent: "center" }}>
        {rightButton}
      </div>
    </div>
  );
}
