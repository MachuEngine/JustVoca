import React from 'react';

const SpeechResultView = ({ evaluationData }) => {
  if (!evaluationData) return null;

  // 1. 전체 문장 데이터 추출 (!SIL 제외)
  const sentenceData = evaluationData.quality.sentences.find(s => s.text !== "!SIL");
  const overallScore = Math.round(sentenceData?.score || 0);
  
  // 2. 음절(Syllable) 목록 추출
  const syllables = sentenceData?.words[0]?.syll || [];

  // 3. 점수에 따른 색상 결정 함수
  const getScoreColor = (score) => {
    if (score >= 80) return "#4CAF50"; // 초록색 (우수)
    if (score >= 60) return "#FF9800"; // 주황색 (보통)
    return "#F44336"; // 빨간색 (노력 필요)
  };

  return (
    <div style={{ marginTop: '30px', padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '12px', border: '1px solid #eee' }}>
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: '0', color: '#333' }}>발음 평가 결과</h2>
        <div style={{ fontSize: '48px', fontWeight: 'bold', color: getScoreColor(overallScore) }}>
          {overallScore}<span style={{ fontSize: '20px' }}>점</span>
        </div>
      </div>

      {/* 글자별 상세 점수 표시 */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '15px', flexWrap: 'wrap' }}>
        {syllables.map((item, index) => (
          <div key={index} style={{ textAlign: 'center' }}>
            <div 
              style={{ 
                fontSize: '32px', 
                fontWeight: 'bold', 
                color: getScoreColor(item.score),
                padding: '10px',
                borderBottom: `4px solid ${getScoreColor(item.score)}`
              }}
            >
              {item.text}
            </div>
            <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
              {Math.round(item.score)}점
            </div>
          </div>
        ))}
      </div>

      {/* 유창성 정보 (추가 피드백) - 수정된 부분 */}
      <div style={{ marginTop: '25px', borderTop: '1px solid #ddd', paddingTop: '15px', fontSize: '14px', color: '#555' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          {/* 공백이 있는 키는 [' '] 형식을 사용해야 합니다 */}
          <span>말하기 속도: {evaluationData.fluency['speech rate'].toFixed(2)} syll/sec</span>
          <span>
            정확한 음절 수: {evaluationData.fluency['correct syllable count']} / {evaluationData.fluency['syllable count']}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SpeechResultView;