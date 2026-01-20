"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, Bell, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import AuthGuard from "../components/AuthGuard";
import { getStudentNotices } from "../api";

interface Notice {
  id: number;
  title: string;
  content: string;
  created_at: string;
  author?: string;
}

export default function NoticesPage() {
  const router = useRouter();
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  
  // 어떤 공지사항이 펼쳐져 있는지 관리 (ID 저장)
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    async function fetchNotices() {
      try {
        const data = await getStudentNotices();
        // 최신순 정렬 (ID 기준 내림차순 또는 날짜 기준)
        const sorted = Array.isArray(data) 
          ? data.sort((a: Notice, b: Notice) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()) 
          : [];
        setNotices(sorted);
      } catch (error) {
        console.error("공지사항 로드 실패:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchNotices();
  }, []);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
    } catch {
      return "-";
    }
  };

  return (
    <AuthGuard allowedRoles={["student"]}>
      <div className="flex flex-col min-h-full bg-white pb-20">
        {/* 헤더 */}
        <header className="h-14 flex items-center px-4 sticky top-0 bg-white/90 backdrop-blur-md z-10 border-b border-gray-100">
          <button 
            onClick={() => router.back()} 
            className="p-2 -ml-2 hover:bg-gray-50 rounded-full transition-colors active:scale-95"
          >
            <ChevronLeft size={24} className="text-gray-800" />
          </button>
          <h1 className="text-lg font-bold text-gray-900 ml-2">공지사항</h1>
        </header>

        <main className="flex-1 p-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <Loader2 className="animate-spin mb-2" size={32} />
              <p className="text-xs font-bold">공지사항을 불러오는 중...</p>
            </div>
          ) : notices.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-300">
              <Bell size={48} className="mb-4 opacity-20" />
              <p className="text-sm font-bold">등록된 공지사항이 없습니다.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {notices.map((notice) => {
                const isExpanded = expandedId === notice.id;
                
                return (
                  <div 
                    key={notice.id} 
                    className={`bg-white rounded-2xl border transition-all duration-300 overflow-hidden ${
                      isExpanded 
                        ? "border-indigo-100 shadow-md ring-1 ring-indigo-50" 
                        : "border-gray-100 shadow-sm active:scale-[0.99]"
                    }`}
                  >
                    <button 
                      onClick={() => toggleExpand(notice.id)}
                      className="w-full text-left p-5 flex justify-between items-start gap-4"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="bg-indigo-50 text-indigo-600 text-[10px] font-black px-2 py-0.5 rounded uppercase tracking-wider">
                            Notice
                          </span>
                          <span className="text-[10px] font-medium text-gray-400">
                            {formatDate(notice.created_at)}
                          </span>
                        </div>
                        <h3 className={`font-bold text-gray-900 leading-snug ${isExpanded ? "text-lg" : "text-base line-clamp-1"}`}>
                          {notice.title}
                        </h3>
                      </div>
                      <div className={`mt-1 text-gray-400 transition-transform duration-300 ${isExpanded ? "rotate-180" : ""}`}>
                        <ChevronDown size={20} />
                      </div>
                    </button>

                    {/* 펼쳐지는 내용 영역 */}
                    <div 
                      className={`overflow-hidden transition-all duration-300 ease-in-out ${
                        isExpanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
                      }`}
                    >
                      <div className="px-5 pb-5 pt-0">
                        <div className="w-full h-px bg-gray-50 mb-4"></div>
                        <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                          {notice.content}
                        </p>
                        {notice.author && (
                          <p className="text-right text-[10px] font-bold text-gray-300 mt-4">
                            From. {notice.author}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}