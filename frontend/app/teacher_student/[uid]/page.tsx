"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type Student = {
  uid: string;
  name: string;
  email: string;
  phone: string;
  country: string;
  progress: any;
};

export default function TeacherStudentPage() {
  const router = useRouter();
  const params = useParams<{ uid: string }>();
  const uid = params?.uid;

  const [student, setStudent] = useState<Student | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    if (!uid) return;
    setErr(null);
    const res = await fetch(`${API}/api/teacher/students/${uid}`, {
      credentials: "include",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setErr(data?.detail ?? "불러오기 실패");
      return;
    }
    setStudent(data?.student ?? null);
  }

  async function resetPassword() {
    if (!uid) return;
    const ok = confirm("이 학생 비밀번호를 1111로 초기화할까요?");
    if (!ok) return;

    setBusy(true);
    try {
      const res = await fetch(`${API}/api/teacher/students/${uid}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ new_password: "1111" }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data?.detail ?? "초기화 실패");
        return;
      }
      alert("비밀번호를 1111로 초기화했습니다.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load();
  }, [uid]);

  return (
    <div style={{ maxWidth: 820, margin: "40px auto" }}>
      <button onClick={() => router.back()} style={{ marginBottom: 14 }}>
        ← 뒤로
      </button>

      <h2>학생 상세</h2>

      {err && <p style={{ color: "crimson" }}>{err}</p>}
      {!student ? (
        <p>불러오는 중...</p>
      ) : (
        <>
          <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 14 }}>
            <div style={{ fontSize: 18 }}>
              <b>{student.name || "(이름 없음)"}</b>{" "}
              <span style={{ opacity: 0.7 }}>({student.uid})</span>
            </div>
            <div style={{ marginTop: 8, fontSize: 13, opacity: 0.9 }}>
              국가: {student.country} · 이메일: {student.email || "-"} · 전화: {student.phone || "-"}
            </div>

            <div style={{ marginTop: 12 }}>
              <button onClick={resetPassword} disabled={busy}>
                비밀번호 1111로 초기화
              </button>
            </div>
          </div>

          <h3 style={{ marginTop: 22 }}>Progress (원본 그대로)</h3>
          <pre
            style={{
              background: "#111",
              color: "#eee",
              padding: 12,
              borderRadius: 12,
              overflowX: "auto",
              fontSize: 12,
            }}
          >
            {JSON.stringify(student.progress ?? {}, null, 2)}
          </pre>
        </>
      )}
    </div>
  );
}
