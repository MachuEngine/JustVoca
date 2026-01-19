// frontend/app/components/PronOverlay.tsx
"use client";

export function PronOverlay({
  open,
  onClose,
  score,
  details,
  error,
}: {
  open: boolean;
  onClose: () => void;
  score?: number | null;
  details?: any;
  error?: string | null;
}) {
  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.55)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 18,
        zIndex: 9999,
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "min(520px, 100%)",
          background: "white",
          borderRadius: 18,
          padding: 16,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <div style={{ fontWeight: 900 }}>발음 평가 결과</div>
          <button onClick={onClose}>닫기</button>
        </div>

        {error ? (
          <div style={{ marginTop: 12, color: "#b00020", fontWeight: 700 }}>
            {error}
          </div>
        ) : (
          <>
            <div style={{ marginTop: 12, fontSize: 18, fontWeight: 900 }}>
              점수: {typeof score === "number" ? score.toFixed(1) : "-"}
            </div>

            <div style={{ marginTop: 12, fontSize: 12, opacity: 0.8 }}>
              details/raw 구조는 SpeechPro 응답에 맞춰 커스터마이즈하면 됨
            </div>

            <pre
              style={{
                marginTop: 10,
                maxHeight: 260,
                overflow: "auto",
                background: "#f5f5f5",
                padding: 10,
                borderRadius: 10,
                fontSize: 12,
              }}
            >
              {JSON.stringify(details ?? {}, null, 2)}
            </pre>
          </>
        )}
      </div>
    </div>
  );
}
