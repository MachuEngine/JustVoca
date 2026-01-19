const API_BASE_URL = "http://localhost:8000";

/**
 * [신규] 사용자의 현재 학습 진도(레벨) 가져오기
 */
export async function getUserProgress(userId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/study/current-progress?user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) throw new Error("진도 정보를 가져오지 못했습니다.");
    return await res.json();
  } catch (error) {
    console.error("getUserProgress Error:", error);
    return { level: "초급1", current_page: 1 };
  }
}

/**
 * [수정] 단어 목록 가져오기
 * 백엔드 라우터의 /study 접두사를 추가했습니다.
 */
export async function getWords(level: string = "초급1", userId: string = "test_user") {
  try {
    const encodedLevel = encodeURIComponent(level);
    const encodedUser = encodeURIComponent(userId);
    
    const res = await fetch(`${API_BASE_URL}/study/words?level=${encodedLevel}&user_id=${encodedUser}`);
    
    if (!res.ok) throw new Error("단어 데이터를 불러오지 못했습니다.");
    return await res.json();
  } catch (error) {
    console.error("getWords Error:", error);
    return [];
  }
}

/**
 * [수정] 공지사항 전송
 * 선생님 API 경로(/api/teacher)에 맞춰 수정했습니다.
 */
export async function sendNotice(data: any) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/teacher/notice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return await res.json();
  } catch (error) {
    console.error("sendNotice Error:", error);
    return null;
  }
}

/**
 * [수정] 학습 완료 처리 (진도 업데이트)
 * 백엔드 라우터의 /study 접두사를 추가했습니다.
 */
export async function completeStudy(level: string, userId: string) {
  try {
    const formData = new FormData();
    formData.append("level", level);
    formData.append("user_id", userId);

    const res = await fetch(`${API_BASE_URL}/study/complete`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error("진도 업데이트 실패");
    return await res.json();
  } catch (error) {
    console.error("completeStudy Error:", error);
    return null;
  }
}

/**
 * [유지] 학생 통계 가져오기
 * 이미 정확한 경로(/api/teacher/...)를 사용하고 있어 유지합니다.
 */
export async function getStudentStats(userId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/teacher/students/${encodeURIComponent(userId)}/stats`);
    const data = await res.json();
    return data.ok ? data.chart_data : [];
  } catch (error) {
    console.error("Stats Fetch Error:", error);
    return [];
  }
}

export const uploadRecord = async (formData: FormData) => {
  const response = await fetch('http://localhost:8000/speech/evaluate', {
    method: 'POST',
    body: formData,
  });
  return await response.json();
};