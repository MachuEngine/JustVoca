"use client";
import { useEffect, useState } from "react";
import { getStudents, sendNotice } from "../api"; //
// [추가] AuthGuard 임포트
import AuthGuard from "../components/AuthGuard";

export default function TeacherDash() {
  const [students, setStudents] = useState<any[]>([]);
  const [notice, setNotice] = useState({ title: "", content: "" });

  useEffect(() => { getStudents().then(setStudents); }, []);
  const [isScheduled, setIsScheduled] = useState(false); 
  const [scheduledDate, setScheduledDate] = useState<string | null>(null);
  
  const handleSend = async () => {
    if(!notice.title) return alert("제목을 입력하세요");
    await sendNotice({...notice, author: "teacher", scheduled_at: isScheduled ? scheduledDate : null});
    alert("발송 완료");
    setNotice({ title: "", content: "" });
  };

  return (
    // [보안 적용] 선생님 또는 관리자만 접근 가능
    <AuthGuard allowedRoles={['teacher', 'admin']}>
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">👨‍🏫 선생님 대시보드</h1>
        
        <div className="grid md:grid-cols-2 gap-6">
          <section>
            <h2 className="text-lg font-bold mb-4">학생 현황 ({students.length}명)</h2>
            <div className="space-y-3">
              {students.map(s => (
                <div key={s.uid} className="bg-white p-4 rounded-xl border shadow-sm flex justify-between items-center">
                  <div>
                    <p className="font-bold">{s.name}</p>
                    <p className="text-xs text-gray-500">진도율 {Math.round((s.learned/s.goal)*100)}%</p>
                  </div>
                  <span className="text-blue-600 font-bold">{s.learned}단어</span>
                </div>
              ))}
            </div>
          </section>

          <section className="bg-white p-6 rounded-2xl border shadow-sm h-fit">
            <h2 className="text-lg font-bold mb-4">📢 공지사항 작성</h2>
            <input 
              className="w-full border p-3 rounded-lg mb-3" 
              placeholder="제목" 
              value={notice.title} 
              onChange={e => setNotice({...notice, title: e.target.value})} 
            />
            <textarea 
              className="w-full border p-3 rounded-lg mb-4 h-32" 
              placeholder="내용을 입력하세요..." 
              value={notice.content} 
              onChange={e => setNotice({...notice, content: e.target.value})} 
            />
            <button onClick={handleSend} className="w-full bg-indigo-600 text-white py-3 rounded-lg font-bold hover:bg-indigo-700">
              공지 보내기
            </button>
          </section>
        </div>
      </div>
    </AuthGuard>
  );
}