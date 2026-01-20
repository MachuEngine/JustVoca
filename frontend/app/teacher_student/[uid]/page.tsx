"use client";

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChevronLeft, Mail, Phone, User, Globe } from 'lucide-react'; // 아이콘 추가
import AuthGuard from '../../components/AuthGuard';
import { getStudentDetail } from '../../api'; // API 함수 임포트

export default function StudentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const uid = params.uid as string;

  const [student, setStudent] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await getStudentDetail(uid);
        if (data && data.info) {
          setStudent(data);
        }
      } catch (error) {
        console.error("학생 정보 로드 실패:", error);
        alert("학생 정보를 불러오지 못했습니다.");
        router.back();
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [uid, router]);

  if (loading) return <div className="p-10 text-center">로딩 중...</div>;
  if (!student) return null;

  const { info, progress } = student;

  return (
    <AuthGuard allowedRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-gray-50 pb-20">
        {/* 헤더 */}
        <header className="h-16 flex items-center px-4 bg-white border-b border-gray-100 sticky top-0 z-10">
          <button onClick={() => router.back()} className="p-2 -ml-2 hover:bg-gray-50 rounded-full">
            <ChevronLeft className="text-gray-800" size={24} />
          </button>
          <h1 className="text-lg font-bold text-gray-900 ml-2">{info.name} 학생 상세</h1>
        </header>

        <main className="p-6 space-y-6">
          
          {/* 1. 기본 정보 카드 (요청하신 부분) */}
          <section className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
                <User size={32} className="text-gray-400" />
              </div>
              <div>
                <h2 className="text-2xl font-black text-gray-900">{info.name}</h2>
                <p className="text-sm font-bold text-gray-400">ID: {info.uid}</p>
              </div>
              <div className="ml-auto">
                <span className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-black">
                  {progress.level} 과정
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <Globe size={18} className="text-gray-500" />
                <div>
                  <p className="text-[10px] text-gray-400 font-bold uppercase">국적</p>
                  <p className="text-sm font-bold text-gray-800">{info.country}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <Phone size={18} className="text-gray-500" />
                <div>
                  <p className="text-[10px] text-gray-400 font-bold uppercase">전화번호</p>
                  <p className="text-sm font-bold text-gray-800">{info.phone}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <Mail size={18} className="text-gray-500" />
                <div>
                  <p className="text-[10px] text-gray-400 font-bold uppercase">이메일</p>
                  <p className="text-sm font-bold text-gray-800">{info.email}</p>
                </div>
              </div>
            </div>
          </section>

          {/* 이후 기존의 학습 통계 차트나 상세 정보를 배치 */}
          {/* <StudentScoreChart ... /> 등을 여기에 추가 */}
          
        </main>
      </div>
    </AuthGuard>
  );
}