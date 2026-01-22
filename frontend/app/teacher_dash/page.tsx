"use client";

import React, { useState, useEffect } from 'react';
import { 
  Calendar, Send, ChevronLeft, Clock, Users, 
  BarChart, CheckCircle, GraduationCap, Search, RotateCcw, List, Lock
} from 'lucide-react'; 
import Link from 'next/link';
import AuthGuard from '../components/AuthGuard';
import { getStudents, sendNotice, getNotices } from '../api'; 

export default function TeacherDash() {
  // --- 상태 관리 ---
  const [students, setStudents] = useState<any[]>([]);
  const [noticeLogs, setNoticeLogs] = useState<any[]>([]); 
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduledDate, setScheduledDate] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // --- 데이터 로드 ---
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // 1. 학생 데이터 가져오기
      const response = await getStudents();
      
      // [수정 핵심] 백엔드가 { ok: true, items: [...] } 형태로 주므로 items만 꺼내야 함
      if (response && response.items) {
        setStudents(response.items);
      } else if (Array.isArray(response)) {
        // 혹시 백엔드가 배열로 줄 경우를 대비한 방어 코드
        setStudents(response);
      } else {
        setStudents([]);
      }
      
      // 2. 공지 이력 가져오기
      const logs = await getNotices();
      setNoticeLogs(logs || []);
      
    } catch (error) {
      console.error("데이터 로드 실패:", error);
    }
  };

  // --- 공지 발송 ---
  const handleSend = async () => {
    if (!title || !content) {
      alert("제목과 내용을 입력해주세요.");
      return;
    }
    try {
      const response = await sendNotice({
        title, content, author: "Teacher",
        scheduled_at: isScheduled ? scheduledDate : null
      });
      if (response?.status === "ok") {
        alert("📢 공지사항 발송 완료!");
        setTitle(''); setContent(''); 
        fetchData(); // 로그 새로고침
      }
    } catch (error) {
      alert("전송 실패");
    }
  };

  // [추가] 진도 평균 계산 로직
  const averageProgress = students.length > 0
    ? Math.round(
        students.reduce((acc, curr) => acc + (curr.progress_rate || 0), 0) / students.length * 100
      )
    : 0;

  // [추가] 준비중 배지 컴포넌트
  const ComingSoonBadge = () => (
    <span className="absolute top-4 right-4 bg-white/80 backdrop-blur-sm text-gray-400 text-[10px] font-bold px-2 py-1 rounded-full border border-gray-100 flex items-center gap-1">
      <Lock size={8} /> 준비중
    </span>
  );

  return (
    <AuthGuard allowedRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-gray-50 pb-20">
        {/* 1. 상단 통계 카드 영역 */}
        <div className="bg-white px-6 py-8 border-b border-gray-100 shadow-sm">
          <h1 className="text-2xl font-black text-gray-900 mb-6 flex items-center gap-2">
             <BarChart className="text-blue-600" /> 학습 통계
          </h1>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            
            {/* [1] 전체 학생 (실제 데이터) */}
            <div className="bg-blue-50 p-5 rounded-3xl border border-blue-100">
              <Users className="text-blue-500 mb-2" size={20} />
              <p className="text-2xl font-black text-blue-900">{students.length}</p>
              <p className="text-[10px] font-bold text-blue-400 uppercase">전체 학생</p>
            </div>

            {/* [2] 진도 평균 (실제 데이터 적용됨) */}
            <div className="bg-green-50 p-5 rounded-3xl border border-green-100">
              <CheckCircle className="text-green-500 mb-2" size={20} />
              {/* 계산된 평균값 사용 */}
              <p className="text-2xl font-black text-green-900">{averageProgress}%</p>
              <p className="text-[10px] font-bold text-green-400 uppercase">진도 평균</p>
            </div>

            {/* [3] 시험 평균 (준비중 표시) */}
            <div className="bg-purple-50/40 p-5 rounded-3xl border border-purple-50 relative">
              <ComingSoonBadge />
              <GraduationCap className="text-purple-300 mb-2" size={20} />
              <p className="text-2xl font-black text-purple-900/30 blur-[2px] select-none">82</p>
              <p className="text-[10px] font-bold text-purple-400/70 uppercase">시험 평균</p>
            </div>

            {/* [4] 과제 제출 (준비중 표시) */}
            <div className="bg-orange-50/40 p-5 rounded-3xl border border-orange-50 relative">
              <ComingSoonBadge />
              <RotateCcw className="text-orange-300 mb-2" size={20} />
              <p className="text-2xl font-black text-orange-900/30 blur-[2px] select-none">12</p>
              <p className="text-[10px] font-bold text-orange-400/70 uppercase">과제 제출</p>
            </div>

          </div>
        </div>

        <main className="p-6 space-y-8">
          {/* 2. 학생 목록 및 검색 */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-black text-gray-900">학생 관리</h2>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                <input 
                  type="text" placeholder="이름/이메일 검색"
                  className="pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-3">
              {/* 이제 students가 확실히 배열이므로 .filter 사용 가능 */}
              {Array.isArray(students) && students.filter(s => s.name && s.name.includes(searchTerm)).map((student) => (
                <Link key={student.uid} href={`/teacher_student/${student.uid}`}>
                  <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm flex justify-between items-center hover:shadow-md transition-all active:scale-[0.99] mb-3">
                    <div>
                      <p className="font-bold text-gray-900">{student.name}</p>
                      <p className="text-xs text-gray-400">
                        {student.current_level} · 진도 {Math.round(student.progress_rate * 100)}%
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-24 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className="bg-blue-500 h-full transition-all duration-500" 
                          style={{ width: `${Math.min(100, student.progress_rate * 100)}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-black text-blue-600">
                        {Math.round(student.progress_rate * 100)}%
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
              
              {/* 학생이 없을 경우 안내 메시지 */}
              {students.length === 0 && (
                 <div className="text-center py-10 text-gray-400 text-sm">
                   등록된 학생이 없습니다.
                 </div>
              )}
            </div>
          </section>

          {/* 3. 공지사항 작성 */}
          <section className="bg-white p-6 rounded-[2.5rem] shadow-xl border border-gray-50">
            <h2 className="text-lg font-black text-gray-900 mb-6 flex items-center gap-2">
              <Send size={20} className="text-blue-600" /> 전체 공지 발송
            </h2>
            <div className="flex bg-gray-100 p-1 rounded-xl mb-6">
              <button onClick={() => setIsScheduled(false)} className={`flex-1 py-2 text-sm font-bold rounded-lg z-10 ${!isScheduled ? 'bg-white shadow-sm text-gray-900' : 'text-gray-400'}`}>즉시 발송</button>
              <button onClick={() => setIsScheduled(true)} className={`flex-1 py-2 text-sm font-bold rounded-lg z-10 ${isScheduled ? 'bg-white shadow-sm text-gray-900' : 'text-gray-400'}`}>예약 발송</button>
            </div>

            {isScheduled && (
              <div className="mb-6 animate-in slide-in-from-top-2">
                <label className="text-xs font-bold text-gray-500 mb-2 block flex items-center gap-1"><Clock size={14} /> 발송 시간 예약</label>
                <input type="datetime-local" className="w-full bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-sm font-bold text-blue-900" value={scheduledDate} onChange={(e) => setScheduledDate(e.target.value)} />
              </div>
            )}

            <input type="text" placeholder="공지 제목" className="w-full text-lg font-bold border-b-2 border-gray-100 py-3 mb-4 outline-none focus:border-blue-500 bg-transparent" value={title} onChange={(e) => setTitle(e.target.value)} />
            <textarea placeholder="공지 내용을 입력하세요" className="w-full h-32 bg-gray-50 rounded-2xl p-4 text-sm outline-none focus:ring-2 focus:ring-blue-100 mb-6" value={content} onChange={(e) => setContent(e.target.value)} />
            
            <button onClick={handleSend} className="w-full bg-gray-900 text-white font-black py-4 rounded-2xl flex items-center justify-center gap-2 shadow-lg active:scale-95 transition-all">
               <Send size={18} /> 발송하기
            </button>
          </section>

          {/* 4. 공지 발송 로그 */}
          <section>
            <h2 className="text-lg font-black text-gray-900 mb-4 flex items-center gap-2">
              <List size={20} className="text-gray-400" /> 공지 발송 로그
            </h2>
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm divide-y divide-gray-50">
              {noticeLogs.length > 0 ? noticeLogs.map((log: any, idx: number) => (
                <div key={idx} className="p-4">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] font-black text-blue-500 uppercase">{log.scheduled_at ? '예약' : '즉시'}</span>
                    <span className="text-[10px] text-gray-400">{new Date(log.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-sm font-bold text-gray-800 mb-1">{log.title}</p>
                  <p className="text-xs text-gray-500 line-clamp-1">{log.content}</p>
                </div>
              )) : (
                <p className="p-10 text-center text-gray-300 text-sm font-bold">발송된 공지가 없습니다.</p>
              )}
            </div>
          </section>
        </main>
      </div>
    </AuthGuard>
  );
}