// app/api.ts

const API_BASE_URL = "http://localhost:8000";

// --- [기존 함수들 유지] ---
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

export async function getWords(level: string = "초급1", userId: string = "test_user") {
  try {
    const res = await fetch(`${API_BASE_URL}/study/words?level=${encodeURIComponent(level)}&user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) throw new Error("단어 데이터를 불러오지 못했습니다.");
    return await res.json();
  } catch (error) {
    console.error("getWords Error:", error);
    return [];
  }
}

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
  const response = await fetch(`${API_BASE_URL}/speech/evaluate`, {
    method: 'POST',
    body: formData,
  });
  return await response.json();
};


// --- [설정 페이지(SettingsPage)를 위한 신규 함수 추가] ---

// 1. 프로필 정보 가져오기
export async function getUserProfile(userId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/user/${userId}/profile`);
    if (!res.ok) throw new Error("프로필 로드 실패");
    return await res.json();
  } catch (error) {
    console.error("getUserProfile Error:", error);
    // 에러 시 화면 깨짐 방지를 위한 기본값 반환
    return {
      uid: userId,
      name: "사용자",
      role: "student",
      email: "student@example.com",
      phone: "010-0000-0000",
      country: "South Korea",
      dailyGoal: 10,
      reviewWrong: true
    };
  }
}

// 2. 프로필 정보 수정 (이메일, 전화번호, 나라)
export async function updateUserProfile(userId: string, data: { email?: string; phone?: string; country?: string }) {
  try {
    const res = await fetch(`${API_BASE_URL}/user/${userId}/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return await res.json();
  } catch (error) {
    console.error("updateUserProfile Error:", error);
    return { status: "error" };
  }
}

// 3. 학습 설정 수정 (목표량, 오답노트 설정)
export async function updateStudySettings(userId: string, settings: { dailyGoal?: number; reviewWrong?: boolean }) {
  try {
    const res = await fetch(`${API_BASE_URL}/user/${userId}/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    return await res.json();
  } catch (error) {
    console.error("updateStudySettings Error:", error);
    return { status: "error" };
  }
}

// 4. 비밀번호 변경
export async function changePassword(userId: string, newPw: string) {
  try {
    // 실제로는 '현재 비밀번호' 확인이 필요하지만, 여기서는 단순화하여 처리
    const oldPw = prompt("현재 비밀번호를 입력해주세요 (확인용):");
    if (!oldPw) return { status: "cancel" };

    const res = await fetch(`${API_BASE_URL}/user/${userId}/password`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
    });
    return await res.json();
  } catch (error) {
    console.error("changePassword Error:", error);
    return { status: "error" };
  }
}

// 5. 회원 탈퇴
export async function withdrawUser(userId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/user/${userId}`, {
      method: "DELETE",
    });
    return await res.json();
  } catch (error) {
    console.error("withdrawUser Error:", error);
    return { status: "error" };
  }
}

export async function getStudents() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/teacher/students`);
    if (!res.ok) throw new Error("학생 목록 로드 실패");
    const data = await res.json();
    // 백엔드 리턴 구조({ok: true, items: [...]})에 맞춰 items 반환
    return data.ok ? data.items : [];
  } catch (error) {
    console.error("getStudents Error:", error);
    return [];
  }
}