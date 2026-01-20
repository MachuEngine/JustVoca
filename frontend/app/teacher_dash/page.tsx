"use client";

import React, { useState } from 'react';
import { sendNotice } from '../api'; 
import { Calendar, Send, ChevronLeft, Clock } from 'lucide-react'; 
import Link from 'next/link';
// [추가] 방금 만든 AuthGuard 임포트
import AuthGuard from '../components/AuthGuard';

export default function TeacherDash() {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduledDate, setScheduledDate] = useState('');

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
      if (response?.status === "ok" || response?.id) {
        alert("공지사항 발송 완료");
        setTitle(''); setContent(''); setScheduledDate('');
      }
    } catch (error) {
      console.error(error); alert("전송 실패");
    }
  };

  return (
    // [핵심] AuthGuard로 감싸서 'teacher' 권한이 있는 사람만 접근 허용
    <AuthGuard allowedRoles={['teacher', 'admin']}>
      <div className="h-full flex flex-col bg-white">
        
        {/* 1. 상단 헤더 (앱바) */}
        <header className="h-14 flex items-center px-4 sticky top-0 bg-white z-10 border-b border-gray-100">
          <Link href="/" className="p-2 -ml-2 hover:bg-gray-50 rounded-full transition-colors">
            <ChevronLeft size={24} className="text-gray-800" />
          </Link>
          <h1 className="text-lg font-bold text-gray-900 ml-2">공지사항 작성</h1>
        </header>

        {/* 2. 메인 컨텐츠 영역 */}
        <main className="flex-1 p-5 overflow-y-auto pb-24">
          
          {/* 발송 타입 토글 */}
          <div className="flex bg-gray-100 p-1 rounded-xl mb-8 relative">
            <div 
              className={`absolute top-1 bottom-1 w-[calc(50%-4px)] bg-white rounded-lg shadow-sm transition-all duration-300 ease-out ${isScheduled ? 'left-[calc(50%+2px)]' : 'left-1'}`}
            ></div>
            
            <button
              onClick={() => setIsScheduled(false)}
              className={`flex-1 py-2.5 text-sm font-bold rounded-lg z-10 transition-colors ${!isScheduled ? 'text-gray-900' : 'text-gray-400'}`}
            >
              즉시 발송
            </button>
            <button
              onClick={() => setIsScheduled(true)}
              className={`flex-1 py-2.5 text-sm font-bold rounded-lg z-10 transition-colors ${isScheduled ? 'text-gray-900' : 'text-gray-400'}`}
            >
              예약 발송
            </button>
          </div>

          {/* 예약 시간 설정 */}
          <div className={`overflow-hidden transition-all duration-300 ${isScheduled ? 'max-h-24 opacity-100 mb-6' : 'max-h-0 opacity-0'}`}>
            <label className="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1">
              <Clock size={14} /> 발송 시간 설정
            </label>
            <div className="flex items-center bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
              <input
                type="datetime-local"
                className="bg-transparent w-full text-sm font-bold text-blue-900 outline-none"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
              />
            </div>
          </div>

          {/* 제목 입력 */}
          <div className="mb-8 group">
            <label className="block text-xs font-bold text-gray-400 mb-1 group-focus-within:text-blue-500 transition-colors">
              제목
            </label>
            <input
              type="text"
              placeholder="공지 제목을 입력하세요"
              className="w-full text-xl font-bold placeholder-gray-300 border-b-2 border-gray-100 py-2 focus:border-blue-500 outline-none transition-all bg-transparent"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* 내용 입력 */}
          <div className="flex flex-col h-64">
             <label className="block text-xs font-bold text-gray-400 mb-2">내용</label>
            <textarea
              placeholder="학생들에게 전달할 내용을 작성해주세요."
              className="flex-1 w-full text-base leading-relaxed placeholder-gray-300 outline-none resize-none bg-gray-50 rounded-2xl p-5 focus:ring-2 focus:ring-blue-100 transition-all"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
          </div>
        </main>

        {/* 3. 하단 고정 버튼 */}
        <div className="absolute bottom-0 left-0 w-full p-4 bg-white/90 backdrop-blur-sm border-t border-gray-50">
          <button
            onClick={handleSend}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 active:scale-[0.98] transition-all text-white font-bold py-4 rounded-2xl text-lg flex items-center justify-center gap-2 shadow-xl shadow-blue-200"
          >
            <Send size={20} className="text-blue-100" />
            <span>공지 발송하기</span>
          </button>
        </div>
      </div>
    </AuthGuard>
  );
}