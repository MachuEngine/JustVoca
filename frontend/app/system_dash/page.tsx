"use client";

import React, { useEffect, useState } from 'react';
import { ShieldCheck, UserCheck, Check, Clock } from 'lucide-react';
import AuthGuard from '../components/AuthGuard';
import { getPendingTeachers, approveTeacher } from '../api';

export default function AdminDash() {
  const [pendingTeachers, setPendingTeachers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // 대기 목록 불러오기
  const fetchPending = async () => {
    try {
      setLoading(true);
      const data = await getPendingTeachers();
      setPendingTeachers(data || []);
    } catch (error) {
      console.error("데이터 로드 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, []);

  // 승인 처리
  const handleApprove = async (uid: string, name: string) => {
    if (!confirm(`${name} 선생님을 승인하시겠습니까?`)) return;

    try {
      await approveTeacher(uid);
      alert("승인되었습니다.");
      // 목록 새로고침
      fetchPending(); 
    } catch (error) {
      alert("승인 처리에 실패했습니다.");
    }
  };

  return (
    <AuthGuard allowedRoles={['admin']}>
      <div className="min-h-screen bg-gray-50 pb-24">
        {/* 상단 헤더 */}
        <div className="bg-white px-6 py-8 border-b border-gray-100 shadow-sm">
          <h1 className="text-2xl font-black text-gray-900 mb-2 flex items-center gap-2">
             <ShieldCheck className="text-blue-600" /> 관리자 시스템
          </h1>
          <p className="text-gray-500 font-medium">선생님 가입 승인 및 시스템 관리</p>
        </div>

        <main className="p-6">
          {/* 대기 중인 선생님 목록 */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-black text-gray-900 flex items-center gap-2">
                <UserCheck size={20} className="text-orange-500" /> 
                승인 대기 목록
                <span className="bg-orange-100 text-orange-600 text-xs px-2 py-0.5 rounded-full">
                  {pendingTeachers.length}명
                </span>
              </h2>
            </div>

            {loading ? (
              <div className="text-center py-10 text-gray-400">데이터를 불러오는 중...</div>
            ) : pendingTeachers.length === 0 ? (
              <div className="bg-white rounded-2xl p-10 text-center border border-gray-100 shadow-sm">
                <Check className="mx-auto text-green-400 mb-3" size={40} />
                <p className="text-gray-900 font-bold mb-1">대기 중인 요청이 없습니다</p>
                <p className="text-xs text-gray-400">모든 선생님이 승인되었습니다.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingTeachers.map((teacher) => (
                  <div key={teacher.uid} className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm flex flex-col gap-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-black text-lg text-gray-900">{teacher.name}</span>
                          <span className="text-[10px] font-bold bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                            {teacher.uid}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500 flex flex-col gap-0.5">
                          <span>{teacher.email || "이메일 없음"}</span>
                          <span>{teacher.phone || "연락처 없음"}</span>
                          <span>{teacher.country || "국적 미기재"}</span>
                        </div>
                      </div>
                      <span className="text-xs font-bold text-orange-500 bg-orange-50 px-2 py-1 rounded-lg flex items-center gap-1">
                        <Clock size={12} /> 승인 대기
                      </span>
                    </div>
                    
                    <button 
                      onClick={() => handleApprove(teacher.uid, teacher.name)}
                      className="w-full py-3 bg-blue-600 text-white font-bold rounded-xl active:scale-[0.98] transition-all shadow-md flex items-center justify-center gap-2"
                    >
                      <Check size={18} /> 승인하기
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        </main>
      </div>
    </AuthGuard>
  );
}