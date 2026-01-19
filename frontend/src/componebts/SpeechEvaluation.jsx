import React, { useState, useRef } from 'react';
import { evaluateSpeech } from '../services/speechService';

const SpeechEvaluation = ({ currentWord }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  // 녹음 시작
  const startRecording = async () => {
    setResult(null);
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.current = new MediaRecorder(stream);
    
    mediaRecorder.current.ondataavailable = (event) => {
      audioChunks.current.push(event.data);
    };

    mediaRecorder.current.onstop = async () => {
      const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
      audioChunks.current = [];
      await handleEvaluation(audioBlob);
    };

    mediaRecorder.current.start();
    setIsRecording(true);
  };

  // 녹음 중지
  const stopRecording = () => {
    mediaRecorder.current.stop();
    setIsRecording(false);
  };

  // 백엔드 전송 및 결과 처리
  const handleEvaluation = async (blob) => {
    setLoading(true);
    const response = await evaluateSpeech(currentWord, blob);
    
    if (response.success) {
      setResult(response.data); // SpeechPro의 score 데이터 포함
    } else {
      alert(response.error || "평가에 실패했습니다.");
    }
    setLoading(false);
  };

  return (
    <div className="speech-eval-container" style={{ padding: '20px', textAlign: 'center' }}>
      <h3>대상 단어: <strong>{currentWord}</strong></h3>
      
      <div style={{ margin: '20px 0' }}>
        {!isRecording ? (
          <button onClick={startRecording} disabled={loading}>🎤 녹음 시작</button>
        ) : (
          <button onClick={stopRecording} style={{ backgroundColor: 'red', color: 'white' }}>
            ⏹️ 녹음 중지 (분석 시작)
          </button>
        )}
      </div>

      {loading && <p>AI가 발음을 분석 중입니다...</p>}

      {result && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd' }}>
          <h4>평가 결과</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff' }}>
            점수: {result.score}점
          </p>
          <p>상세 피드백: {result.score > 80 ? "훌륭한 발음입니다!" : "조금 더 연습해 보세요."}</p>
        </div>
      )}
    </div>
  );
};

export default SpeechEvaluation;


const handleEvaluation = async (blob) => {
  setLoading(true);
  const response = await evaluateSpeech(currentWord, blob);
  
  if (response.success) {
    // 백엔드에서 준 'data' 안의 'result'를 상태에 저장합니다.
    setResult(response.data.result);
  } else {
    alert(response.error || "평가에 실패했습니다.");
  }
  setLoading(false);
};

return (
  <div>
    {/* 녹음 버튼 로직 */}
    <button onClick={isRecording ? stopRecording : startRecording}>
      {isRecording ? "녹음 중지" : "녹음 시작"}
    </button>

    {/* 결과 뷰 컴포넌트 호출 */}
    {result && <SpeechResultView evaluationData={result} />}
  </div>
);