// app/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

// --- [인증 관련 API] ---

/**
 * 로그인 요청
 */
export async function login(id: string, password: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, password }),
      credentials: "include"
    });
    return await res.json();
  } catch (error) {
    console.error("login Error:", error);
    return { ok: false, detail: "로그인 서버 에러" };
  }
}

/**
 * 회원가입 요청 (사양서 국적 정보 포함)
 */
export async function signup(userData: any) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData),
      credentials: "include"
    });
    return await res.json();
  } catch (error) {
    console.error("signup Error:", error);
    return { ok: false, detail: "회원가입 서버 에러" };
  }
}

/**
 * 아이디 중복 확인
 */
export async function checkDuplicateId(id: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/check-id?id=${encodeURIComponent(id)}`);
    const data = await res.json();
    return data.available;
  } catch (error) {
    return false;
  }
}

// --- [학생 학습 관련 API] ---

/**
 * 단어 데이터 불러오기
 */
export async function getWords(level: string = "초급1", userId: string = "test_user") {
  try {
    const res = await fetch(
      `${API_BASE_URL}/study/words?level=${encodeURIComponent(level)}&user_id=${encodeURIComponent(userId)}`,
      { credentials: "include" }
    );
    if (!res.ok) throw new Error("단어 로드 실패");
    return await res.json();
  } catch (error) {
    console.error("getWords Error:", error);
    return [];
  }
}

/**
 * 학생 진도 정보 가져오기
 */
export async function getUserProgress(userId: string) {
  try {
    const res = await fetch(
      `${API_BASE_URL}/study/current-progress?user_id=${encodeURIComponent(userId)}`,
      { credentials: "include" }
    );
    if (!res.ok) throw new Error("진도 로드 실패");
    return await res.json();
  } catch (error) {
    return { level: "초급1", current_page: 1 };
  }
}

/**
 * 학습 완료 처리 (진도 업데이트)
 */
export async function completeStudy(level: string, userId: string) {
  try {
    const formData = new FormData();
    formData.append("level", level);
    formData.append("user_id", userId);
    const res = await fetch(`${API_BASE_URL}/study/complete`, {
      method: "POST",
      body: formData,
      credentials: "include"
    });
    return await res.json();
  } catch (error) {
    return null;
  }
}

/**
 * 발음 녹음 평가 요청
 */
export const uploadRecord = async (formData: FormData) => {
  const response = await fetch(`${API_BASE_URL}/speech/evaluate`, {
    method: 'POST',
    body: formData,
    credentials: "include"
  });
  return await response.json();
};

/**
 * 학생용 공지사항 목록 가져오기 (종소리 아이콘)
 */
export async function getStudentNotices() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/notice/list`, { credentials: "include" });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    return [];
  }
}

// --- [선생님/관리자 관련 API] ---

/**
 * 전체 학생 목록 가져오기 (대시보드 통계용)
 */
export async function getStudents() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/teacher/students`, { credentials: "include" });
    const data = await res.json();
    return data.items || [];
  } catch (error) {
    return [];
  }
}

/**
 * 공지사항 발송 이력 (로그) 가져오기
 */
export async function getNotices() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/notice/logs`, { credentials: "include" });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    return [];
  }
}

/**
 * 전체 공지 발송하기
 */
export async function sendNotice(data: any) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/notice/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      credentials: "include"
    });
    return await res.json();
  } catch (error) {
    return { status: "error" };
  }
}

/**
 * 학생 비밀번호 초기화 (사양서/상세페이지 기능)
 */
export async function resetStudentPassword(uid: string, newPassword: string = "1111") {
  try {
    const res = await fetch(`${API_BASE_URL}/api/teacher/students/${uid}/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_password: newPassword }),
      credentials: "include"
    });
    return res.ok;
  } catch (error) {
    return false;
  }
}

// --- [사용자 설정/프로필 관련 API] ---

export async function getUserProfile(userId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/user/${userId}/profile`, { credentials: "include" });
    if (!res.ok) throw new Error("프로필 로드 실패");
    return await res.json();
  } catch (error) {
    return { name: "사용자", role: "student", dailyGoal: 10, reviewWrong: true };
  }
}

export async function updateUserProfile(userId: string, data: any) {
  try {
    const res = await fetch(`${API_BASE_URL}/user/${userId}/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      credentials: "include"
    });
    return await res.json();
  } catch (error) {
    return { status: "error" };
  }
}

export async function updateStudySettings(userId: string, settings: any) {
  try {
    const res = await fetch(`${API_BASE_URL}/user/${userId}/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
      credentials: "include"
    });
    return await res.json();
  } catch (error) {
    return { status: "error" };
  }
}

export async function changePassword(userId: string, newPw: string) {
  try {
    const oldPw = prompt("현재 비밀번호를 입력해주세요:");
    if (!oldPw) return { status: "cancel" };
    const res = await fetch(`${API_BASE_URL}/user/${userId}/password`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
      credentials: "include"
    });
    return await res.json();
  } catch (error) {
    return { status: "error" };
  }
}

export async function withdrawUser(userId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/user/${userId}`, {
      method: "DELETE",
      credentials: "include"
    });
    return await res.json();
  } catch (error) {
    return { status: "error" };
  }
}