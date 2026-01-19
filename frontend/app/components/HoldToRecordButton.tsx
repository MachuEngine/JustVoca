// frontend/app/components/HoldToRecordButton.tsx
"use client";

import { useRef, useState } from "react";

export function HoldToRecordButton({
  disabled,
  onRecorded,
}: {
  disabled?: boolean;
  onRecorded: (blob: Blob) => void;
}) {
  const recRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const [recording, setRecording] = useState(false);

  const start = async () => {
    if (disabled || recording) return;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    chunksRef.current = [];

    const rec = new MediaRecorder(stream);
    recRef.current = rec;

    rec.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
    };

    rec.onstop = () => {
      const blob = new Blob(chunksRef.current, {
        type: rec.mimeType || "audio/webm",
      });
      // stop tracks
      stream.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      recRef.current = null;
      chunksRef.current = [];
      onRecorded(blob);
    };

    rec.start();
    setRecording(true);
  };

  const stop = () => {
    if (!recRef.current) return;
    try {
      recRef.current.stop();
    } finally {
      setRecording(false);
    }
  };

  return (
    <button
      disabled={!!disabled}
      onPointerDown={(e) => {
        e.preventDefault();
        start();
      }}
      onPointerUp={(e) => {
        e.preventDefault();
        stop();
      }}
      onPointerLeave={() => {
        if (recording) stop();
      }}
      style={{
        width: 320,
        height: 56,
        borderRadius: 14,
        fontWeight: 800,
        fontSize: 16,
      }}
    >
      {recording ? "🎙️ 말하는 중…" : "🎤 누르고 말하세요"}
    </button>
  );
}
