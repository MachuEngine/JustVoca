import React, { useState } from 'react';

const PronunciationResultOverlay = ({ evaluationData, onClose }) => {
  const [showDetail, setShowDetail] = useState(false);

  if (!evaluationData) return null;

  // 1. 데이터 추출 (사양서 기반 파싱)
  const sentenceData = evaluationData.quality.sentences.find(s => s.text !== "!SIL");
  const overallScore = Math.round(sentenceData?.score || 0); [cite, 228, 247]
  const syllables = sentenceData?.words[0]?.syll || [];

  const getScoreColor = (score) => {
    if (score >= 80) return "#4CAF50"; // 초록 (우수)
    if (score >= 60) return "#FF9800"; // 주황 (보통)
    return "#F44336"; // 빨강 (노력)
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.container}>
        {/* 상단: 종합 정확도 [cite: 247] */}
        <div style={styles.header}>
          <div style={styles.scoreCircle}>
            <span style={styles.scoreNumber}>{overallScore}</span>
            <span style={styles.scoreLabel}>정확도</span> [cite: 247]
          </div>
        </div>

        {/* 중단: 어절/음절별 점수 리스트  */}
        <div style={styles.resultList}>
          {syllables.map((item, index) => (
            <div key={index} style={styles.resultItem}>
              <div style={styles.syllableInfo}>
                <span style={styles.typeLabel}>음절</span> [cite: 254]
                <span style={styles.syllableText}>{item.text}</span>
              </div>
              <div style={{ color: getScoreColor(item.score), fontWeight: 'bold' }}>
                {Math.round(item.score)}점 [cite: 242]
                <button 
                  onClick={() => setShowDetail(!showDetail)} 
                  style={styles.detailBtn}
                >
                  상세{showDetail ? '▲' : '▼'} [cite: 255]
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* 하단: 유창성 정보 (image_ec94c7.png 에러 수정됨) */}
        <div style={styles.fluencyBox}>
          <span>말하기 속도: {evaluationData.fluency['speech rate'].toFixed(2)}</span>
          <span>정확도: {evaluationData.fluency['correct syllable count']}/{evaluationData.fluency['syllable count']}</span>
        </div>

        {/* 최하단: 학습 계속하기 버튼  */}
        <button onClick={onClose} style={styles.continueBtn}>
          학습 계속하기 [cite: 264]
        </button>
      </div>
    </div>
  );
};

const styles = {
  overlay: { position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 },
  container: { width: '90%', maxWidth: '400px', backgroundColor: 'white', borderRadius: '20px', padding: '25px', textAlign: 'center' },
  header: { marginBottom: '20px' },
  scoreCircle: { width: '100px', height: '100px', borderRadius: '50%', border: '5px solid #4CAF50', display: 'inline-flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' },
  scoreNumber: { fontSize: '32px', fontWeight: 'bold' },
  scoreLabel: { fontSize: '14px', color: '#666' },
  resultList: { textAlign: 'left', marginBottom: '20px', maxHeight: '300px', overflowY: 'auto' },
  resultItem: { display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #eee' },
  syllableInfo: { display: 'flex', alignItems: 'center', gap: '10px' },
  typeLabel: { fontSize: '12px', color: '#999', backgroundColor: '#f0f0f0', padding: '2px 6px', borderRadius: '4px' },
  syllableText: { fontSize: '18px', fontWeight: 'bold' },
  detailBtn: { background: 'none', border: 'none', color: '#666', cursor: 'pointer', marginLeft: '5px' },
  fluencyBox: { fontSize: '12px', color: '#888', display: 'flex', justifyContent: 'space-between', marginBottom: '20px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '8px' },
  continueBtn: { width: '100%', padding: '15px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '10px', fontSize: '18px', fontWeight: 'bold', cursor: 'pointer' }
};

export default PronunciationResultOverlay;