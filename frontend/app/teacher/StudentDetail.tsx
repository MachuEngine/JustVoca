"use client";

import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getStudentStats } from '../api';

export default function StudentScoreChart({ studentId }: { studentId: string }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    async function loadStats() {
      const stats = await getStudentStats(studentId);
      setData(stats);
    }
    loadStats();
  }, [studentId]);

  return (
    <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm mt-6">
      <h3 className="text-lg font-black text-gray-900 mb-6 flex items-center gap-2">
        📈 발음 점수 변화 추이
      </h3>
      
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 12, fill: '#9ca3af', fontWeight: 'bold' }} 
              dy={10}
            />
            <YAxis 
              domain={[0, 100]} 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 12, fill: '#9ca3af' }} 
            />
            <Tooltip 
              contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
              itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
            />
            <Line 
              type="monotone" 
              dataKey="score" 
              stroke="#10b981" 
              strokeWidth={4} 
              dot={{ r: 6, fill: '#10b981', strokeWidth: 2, stroke: '#fff' }}
              activeDot={{ r: 8, strokeWidth: 0 }}
              animationDuration={1500}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <p className="text-center text-xs text-gray-400 mt-4 font-medium">
        * 최근 7일간의 평균 점수를 나타냅니다.
      </p>
    </div>
  );
}