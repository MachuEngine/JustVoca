"use client";

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChevronLeft, Mail, Phone, User, Globe, BarChart2, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import AuthGuard from '../../components/AuthGuard';
import { getStudentDetail, getStudentStats } from '../../api'; // stats API 추가 사용

export default function StudentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const uid = params.uid as string;

  const [student, setStudent] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        // 1. 학생 기본 정보
        const basicData = await getStudentDetail(uid);
        if (basicData?.info) setStudent(basicData);

        // 2. 학생 학습 통계 (상세 데이터)
        const statsData = await getStudentStats(uid);
        setStats(statsData);

      } catch (error) {
        console.error("정보 로드 실패:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [uid]);

  if (loading) return <div className="p-10 text-center font-bold text-gray-400">데이터를 불러오는 중...</div>;
  if (!student) return <div className="p-10 text-center">학생 정보를 찾을 수 없습니다.</div>;

  const { info, progress } = student;

  return (
    <AuthGuard allowedRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-gray-50 pb-20">
        {/* 헤더 */}
        <header className="h-16 flex items-center px-4 bg-white border-b border-gray-100 sticky top-0 z-10 shadow-sm">
          <button onClick={() => router.back()} className="p-2 -ml-2 hover:bg-gray-50 rounded-full transition-colors">
            <ChevronLeft className="text-gray-800" size={24} />
          </button>
          <h1 className="text-lg font-bold text-gray-900 ml-2">학생 상세 관리</h1>
        </header>

        <main className="p-6 space-y-6">
          
          {/* 1. 프로필 카드 */}
          <section className="bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center text-blue-500 border border-blue-100">
                <User size={30} />
              </div>
              <div>
                <h2 className="text-2xl font-black text-gray-900 leading-none mb-1">{info.name}</h2>
                <p className="text-sm font-bold text-gray-400">ID: {info.uid}</p>
              </div>
              <div className="ml-auto text-right">
                <span className="inline-block bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-black mb-1">
                  {progress.level}
                </span>
                <p className="text-xs text-gray-400 font-bold">진도율 {Math.min(100, progress.page * 10)}%</p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-2xl">
                <Globe size={18} className="text-gray-400 ml-1" />
                <div>
                  <p className="text-[10px] text-gray-400 font-bold uppercase">Nationality</p>
                  <p className="text-sm font-bold text-gray-800">{info.country}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-2xl">
                <Phone size={18} className="text-gray-400 ml-1" />
                <div>
                  <p className="text-[10px] text-gray-400 font-bold uppercase">Phone</p>
                  <p className="text-sm font-bold text-gray-800">{info.phone}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-2xl">
                <Mail size={18} className="text-gray-400 ml-1" />
                <div>
                  <p className="text-[10px] text-gray-400 font-bold uppercase">Email</p>
                  <p className="text-sm font-bold text-gray-800">{info.email}</p>
                </div>
              </div>
            </div>
          </section>

          {stats && (
            <>
              {/* 2. 학습 요약 통계 */}
              <section className="grid grid-cols-3 gap-3">
                <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm text-center">
                  <p className="text-[10px] font-bold text-gray-400 mb-1 uppercase">이번 주 학습</p>
                  <p className="text-xl font-black text-gray-900">{stats.weeklyLearned}<span className="text-xs font-normal text-gray-400 ml-0.5">단어</span></p>
                </div>
                <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm text-center">
                  <p className="text-[10px] font-bold text-gray-400 mb-1 uppercase">평균 정확도</p>
                  <p className="text-xl font-black text-blue-600">{stats.accuracy}%</p>
                </div>
                <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm text-center">
                  <p className="text-[10px] font-bold text-gray-400 mb-1 uppercase">연속 학습</p>
                  <p className="text-xl font-black text-orange-500">{stats.streak}<span className="text-xs font-normal text-gray-400 ml-0.5">일</span></p>
                </div>
              </section>

              {/* 3. 주간 학습 패턴 (그래프) */}
              <section className="bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm">
                <h3 className="text-md font-black text-gray-900 mb-6 flex items-center gap-2">
                  <BarChart2 size={18} className="text-blue-500" /> 주간 학습 패턴
                </h3>
                <div className="flex items-end justify-between h-32 gap-2 px-2">
                  {['월','화','수','목','금','토','일'].map((day, i) => (
                    <div key={day} className="flex-1 flex flex-col items-center gap-2">
                      <div className="w-full bg-gray-100 rounded-t-lg h-full flex items-end relative overflow-hidden">
                        <div 
                          style={{ height: `${stats.weeklyTrend[i]}%` }} 
                          className={`w-full rounded-t-lg transition-all duration-1000 ${stats.weeklyTrend[i] > 0 ? 'bg-blue-500' : 'bg-transparent'}`}
                        ></div>
                      </div>
                      <span className="text-[10px] font-bold text-gray-400">{day}</span>
                    </div>
                  ))}
                </div>
              </section>

              {/* 4. 최근 학습 로그 */}
              <section className="bg-white p-6 rounded-[2rem] border border-gray-100 shadow-sm">
                <h3 className="text-md font-black text-gray-900 mb-4 flex items-center gap-2">
                  <Clock size={18} className="text-green-500" /> 최근 학습 완료 기록
                </h3>
                <div className="space-y-3">
                  {stats.recentLogs && stats.recentLogs.length > 0 ? (
                    stats.recentLogs.map((log: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-10 rounded-full ${log.score >= 80 ? 'bg-green-500' : 'bg-orange-400'}`}></div>
                          <div>
                            <p className="font-bold text-gray-900 text-sm">{log.word}</p>
                            <p className="text-[10px] text-gray-400">{log.date}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`text-lg font-black ${log.score >= 80 ? 'text-green-600' : 'text-orange-500'}`}>
                            {log.score}
                          </span>
                          <span className="text-[10px] font-bold text-gray-400 ml-0.5">점</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-gray-400 text-sm">
                      아직 학습 기록이 없습니다.
                    </div>
                  )}
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}