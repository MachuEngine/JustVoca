// app/components/Chatbot.tsx
"use client";

import React, { useState, useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { MessageCircle, X, Send, Loader2, User, Bot } from "lucide-react";
import { sendChatMessage } from "../api";

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ role: "user" | "bot"; text: string }[]>([
    { role: "bot", text: "안녕하세요! 무엇을 도와드릴까요?" },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [showButton, setShowButton] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null); // role 상태 추가

  // --- [드래그 관련 상태] ---
  const [position, setPosition] = useState({ x: 0, y: 0 }); // 버튼 위치
  const isDragging = useRef(false); // 드래그 중인지 판별
  const dragStartPos = useRef({ x: 0, y: 0 }); // 드래그 시작 좌표 (클릭 구분용)
  const offset = useRef({ x: 0, y: 0 }); // 마우스와 버튼의 오차 보정
  const buttonRef = useRef<HTMLButtonElement>(null); // 버튼 요소 참조

  const scrollRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();

  // 챗봇을 표시할 경로 목록 정의
  const allowedPaths = ["/student_home", "/levels", "/stats", "/settings"];
  const isVisiblePath = allowedPaths.some((path) => pathname?.startsWith(path));

  // 1. 초기 설정 (로그인 체크)
  useEffect(() => {
    // 로그인한 학생일 때만 챗봇 표시
    const storedId = localStorage.getItem("userId");
    const role = localStorage.getItem("userRole");

    // role이 'student'인 경우에만 버튼을 보여주도록 설정
    if (storedId && role === "student") {
      setUserId(storedId);
      setUserRole(role);
      setShowButton(true);
    } else {
      // 관리자(admin)이거나 로그인 정보가 없으면 버튼을 숨김
      setShowButton(false);
    }
  }, []);

  // 2. 메시지 추가될 때마다 스크롤 아래로
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  // --- [드래그 핸들러 함수들] ---
  const handlePointerDown = (e: React.PointerEvent) => {
    if (isOpen) return;

    isDragging.current = true;
    dragStartPos.current = { x: e.clientX, y: e.clientY };

    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      offset.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    }
    
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging.current) return;

    let newX = e.clientX - offset.current.x;
    let newY = e.clientY - offset.current.y;

    // 화면 경계 제한
    const maxX = window.innerWidth - 70; 
    const maxY = window.innerHeight - 70;

    newX = Math.max(10, Math.min(newX, maxX));
    newY = Math.max(10, Math.min(newY, maxY));

    setPosition({ x: newX, y: newY });
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    isDragging.current = false;
    e.currentTarget.releasePointerCapture(e.pointerId);

    const dist = Math.hypot(
      e.clientX - dragStartPos.current.x,
      e.clientY - dragStartPos.current.y
    );

    if (dist < 5) {
      setIsOpen(true);
    }
  };

  // --- [채팅 로직] ---
  const handleSend = async () => {
    if (!input.trim() || !userId) return;

    const userMsg = input.trim();
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await sendChatMessage(userMsg, userId);
      setMessages((prev) => [...prev, { role: "bot", text: res.response }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "죄송해요, 잠시 문제가 생겼어요. 다시 시도해주세요." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!showButton || !isVisiblePath || userRole !== "student") {
    return null;
  }

  return (
    <div className="z-[9999]">
      {/* 1. 채팅창 영역 */}
      <div
        className={`fixed bottom-24 right-4 sm:right-6 pointer-events-auto bg-white 
          w-[calc(100vw-2rem)] sm:w-96
          rounded-3xl shadow-2xl border border-gray-100 overflow-hidden 
          transition-all duration-300 origin-bottom-right mb-4 
          ${isOpen ? "scale-100 opacity-100 z-[10000]" : "scale-90 opacity-0 h-0 w-0 overflow-hidden"}`}
        style={{ maxHeight: "60vh" }}
      >
        <div className="bg-[#20385F] p-4 flex justify-between items-center text-white">
          <div className="flex items-center gap-2">
            <div className="bg-white/20 p-1.5 rounded-full">
              <Bot size={20} />
            </div>
            <span className="font-bold text-sm">저스티</span>
          </div>
          <button onClick={() => setIsOpen(false)} className="hover:bg-white/20 p-1 rounded-full transition">
            <X size={18} />
          </button>
        </div>

        <div ref={scrollRef} className="h-64 sm:h-80 overflow-y-auto p-4 bg-gray-50 flex flex-col gap-3">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-2 max-w-[85%] ${msg.role === "user" ? "self-end flex-row-reverse" : "self-start"}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === "user" ? "bg-gray-200" : "bg-indigo-100"}`}>
                {msg.role === "user" ? <User size={16} className="text-gray-500" /> : <Bot size={16} className="text-indigo-600" />}
              </div>
              <div className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm break-words ${msg.role === "user" ? "bg-[#20385F] text-white rounded-tr-none" : "bg-white text-gray-800 border border-gray-100 rounded-tl-none"}`}>
                {msg.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="self-start flex gap-2">
               <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center"><Bot size={16} className="text-indigo-600"/></div>
               <div className="bg-white px-4 py-3 rounded-2xl rounded-tl-none border border-gray-100 shadow-sm">
                 <Loader2 size={16} className="animate-spin text-gray-400" />
               </div>
            </div>
          )}
        </div>

        <div className="p-3 bg-white border-t border-gray-100 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="궁금한 점을 물어보세요."
            className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
          />
          <button onClick={handleSend} disabled={!input.trim() || isLoading} className="bg-[#20385F] text-white p-2.5 rounded-xl hover:bg-[#1a2d4d] active:scale-95 transition-all disabled:opacity-50">
            <Send size={18} />
          </button>
        </div>
      </div>

      {/* 2. 드래그 가능한 플로팅 버튼 */}
      {!isOpen && (
        <button
          ref={buttonRef}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          style={{
            // 드래그 중일 때만 JS 계산 좌표 적용, 아닐 때는 클래스로 위치 고정
            left: isDragging.current ? `${position.x}px` : undefined,
            top: isDragging.current ? `${position.y}px` : undefined,
            touchAction: "none",
          }}
          className={`fixed z-[9999] w-14 h-14 bg-[#FF8C1A] text-white rounded-full shadow-xl 
                    flex items-center justify-center hover:scale-110 active:scale-95 transition-transform 
                    cursor-move animate-in fade-in zoom-in duration-300
                    ${!isDragging.current ? "right-6 bottom-24" : ""}`} // 드래그 중이 아닐 때만 우측 하단 고정
        >
          <div className="relative pointer-events-none">
            <MessageCircle size={40} />
            <span className="absolute inset-0 flex items-center justify-center text-[20px] font-bold leading-none">...</span>
          </div>
        </button>
      )}
    </div>
  );
}