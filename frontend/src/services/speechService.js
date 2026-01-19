/**
 * SpeechPro 발음 평가 API 호출 함수
 * @param {string} word - 학습 중인 단어
 * @param {Blob} audioBlob - 녹음된 오디오 데이터
 */
export const evaluateSpeech = async (word, audioBlob) => {
  const formData = new FormData();
  // 백엔드 Form(...) 및 File(...) 매개변수 명칭과 일치해야 함
  formData.append('word', word);
  formData.append('audio', audioBlob, 'recording.wav');

  try {
    const response = await fetch('http://localhost:8000/speech/evaluate', {
      method: 'POST',
      body: formData,
      // Note: FormData 전송 시 Content-Type 헤더는 브라우저가 자동으로 설정하게 둡니다.
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error("발음 평가 통신 오류:", error);
    return { success: false, error: "서버와 통신할 수 없습니다." };
  }
};