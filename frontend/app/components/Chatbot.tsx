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

  // 1. 초기 설정 (위치 계산 및 로그인 체크)
  useEffect(() => {
    // 클라이언트 사이드에서만 실행
    if (typeof window !== "undefined") {
      // 초기 위치: 우측 하단
      setPosition({
        x: window.innerWidth - 80, // 오른쪽에서 80px
        y: window.innerHeight - 130, // 바닥에서 120px
      });
    }

    // 로그인한 학생일 때만 챗봇 표시
    const storedId = localStorage.getItem("userId");
    const role = localStorage.getItem("userRole");
    if (storedId && role === "student") {
      setUserId(storedId);
      setShowButton(true);
    }
  }, []);

  // 2. 화면 리사이즈 시 버튼이 화면 밖으로 나가지 않게 조정
  useEffect(() => {
    const handleResize = () => {
      setPosition((prev) => ({
        x: Math.min(prev.x, window.innerWidth - 70),
        y: Math.min(prev.y, window.innerHeight - 70),
      }));
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // 3. 메시지 추가될 때마다 스크롤 아래로
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
    
    // 드래그 중 텍스트 선택 방지 등 포인터 캡처
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging.current) return;

    let newX = e.clientX - offset.current.x;
    let newY = e.clientY - offset.current.y;

    // 화면 밖으로 나가지 않게 제한 (Boundary Check)
    const maxX = window.innerWidth - 70; 
    const maxY = window.innerHeight - 70;

    newX = Math.max(10, Math.min(newX, maxX));
    newY = Math.max(10, Math.min(newY, maxY));

    setPosition({ x: newX, y: newY });
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    isDragging.current = false;
    e.currentTarget.releasePointerCapture(e.pointerId);

    // 드래그 거리가 짧으면(5px 미만) "클릭"으로 간주하고 채팅창 열기
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

  // 렌더링 조건 체크
  if (!showButton || !isVisiblePath) return null;

  return (
    <div className="z-[9999]">
      {/* 1. 채팅창 영역 (고정 위치) */}
      <div
        className={`fixed bottom-24 right-4 sm:right-6 pointer-events-auto bg-white 
          w-[calc(100vw-2rem)] sm:w-96
          rounded-3xl shadow-2xl border border-gray-100 overflow-hidden 
          transition-all duration-300 origin-bottom-right mb-4 
          ${isOpen ? "scale-100 opacity-100 z-[10000]" : "scale-90 opacity-0 h-0 w-0 overflow-hidden"}`}
        style={{ maxHeight: "60vh" }}
      >
        {/* 헤더 */}
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

        {/* 메시지 리스트 */}
        <div 
          ref={scrollRef}
          className="h-64 sm:h-80 overflow-y-auto p-4 bg-gray-50 flex flex-col gap-3"
        >
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-2 max-w-[85%] ${
                msg.role === "user" ? "self-end flex-row-reverse" : "self-start"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === "user" ? "bg-gray-200" : "bg-indigo-100"
                }`}
              >
                {msg.role === "user" ? <User size={16} className="text-gray-500" /> : <Bot size={16} className="text-indigo-600" />}
              </div>
              <div
                className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm break-words ${
                  msg.role === "user"
                    ? "bg-[#20385F] text-white rounded-tr-none"
                    : "bg-white text-gray-800 border border-gray-100 rounded-tl-none"
                }`}
              >
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

        {/* 입력창 */}
        <div className="p-3 bg-white border-t border-gray-100 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="궁금한 점을 물어보세요."
            // [중요] text-base 적용으로 모바일 확대 방지
            className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="bg-[#20385F] text-white p-2.5 rounded-xl hover:bg-[#1a2d4d] active:scale-95 transition-all disabled:opacity-50 disabled:active:scale-100"
          >
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
            left: `${position.x}px`,
            top: `${position.y}px`,
            touchAction: "none", // 드래그 시 모바일 스크롤 방지
          }}
          className="fixed z-[9999] w-14 h-14 bg-[#FF8C1A] text-white
                    rounded-full shadow-[0_4px_20px_rgba(32,56,95,0.4)]
                    flex items-center justify-center
                    hover:scale-110 active:scale-95
                    transition-transform cursor-move animate-in fade-in zoom-in duration-300"
        >
          <div className="relative pointer-events-none"> {/* 내부 요소는 드래그 이벤트 간섭 방지 */}
            {/* 아이콘 */}
            <MessageCircle size={40} />

            {/* 아이콘 안 텍스트 */}
            <span
              className="absolute inset-0 flex items-center justify-center
                        text-[20px] font-bold leading-none"
            >
              ...
            </span>
          </div>
        </button>
      )}
    </div>
  );
}