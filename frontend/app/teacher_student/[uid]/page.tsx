"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation"; //
// [추가] AuthGuard 임포트
import AuthGuard from "../../components/AuthGuard";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type Student = {
  uid: string; name: string; email: string; phone: string; country: string; progress: any;
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
    const res = await fetch(`${API}/api/teacher/students/${uid}`, { credentials: "include" });
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
      if (!res.ok) { alert("초기화 실패"); return; }
      alert("비밀번호를 1111로 초기화했습니다.");
    } finally { setBusy(false); }
  }

  useEffect(() => { load(); }, [uid]);

  return (
    // [보안 적용] 선생님 또는 관리자만 접근 가능
    <AuthGuard allowedRoles={['teacher', 'admin']}>
      <div style={{ maxWidth: 820, margin: "40px auto" }} className="p-6">
        <button onClick={() => router.back()} className="mb-4 px-4 py-2 bg-gray-100 rounded-lg">← 뒤로</button>
        <h2 className="text-2xl font-bold mb-6">학생 상세 정보</h2>
        {err && <p className="text-red-500 mb-4">{err}</p>}
        {!student ? (
          <p>불러오는 중...</p>
        ) : (
          <>
            <div className="border border-gray-200 rounded-2xl p-6 bg-white shadow-sm mb-6">
              <div className="text-xl font-bold mb-2">{student.name || "(이름 없음)"} <span className="text-gray-400 text-sm font-normal">({student.uid})</span></div>
              <div className="text-gray-600 text-sm">국가: {student.country} · 이메일: {student.email || "-"} · 전화: {student.phone || "-"}</div>
              <div className="mt-6">
                <button onClick={resetPassword} disabled={busy} className="bg-red-50 text-red-600 px-4 py-2 rounded-xl font-bold hover:bg-red-100 disabled:opacity-50">
                  비밀번호 1111로 초기화
                </button>
              </div>
            </div>
            <h3 className="text-lg font-bold mb-4">학습 진도 (상세 데이터)</h3>
            <pre className="bg-gray-900 text-gray-100 p-6 rounded-2xl overflow-x-auto text-xs">{JSON.stringify(student.progress ?? {}, null, 2)}</pre>
          </>
        )}
      </div>
    </AuthGuard>
  );
}