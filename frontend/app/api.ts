// frontend/app/api.ts
const getBaseUrl = () => {
  if (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }
  return "http://localhost:8000";
};
const API_BASE_URL = getBaseUrl();

export const api = {
  get: async (endpoint: string) => {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, { credentials: "include" });
    if (!res.ok) throw new Error(`GET 실패: ${res.status}`);
    return await res.json();
  },
  post: async (endpoint: string, body: any) => {
    const isFormData = body instanceof FormData;
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      body: isFormData ? body : JSON.stringify(body),
      headers: isFormData ? {} : { "Content-Type": "application/json" },
      credentials: "include",
    });
    if (!res.ok) throw new Error(`POST 실패: ${res.status}`);
    return await res.json();
  },
  put: async (endpoint: string, body: any) => {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "include"
    });
    if (!res.ok) throw new Error(`PUT 실패: ${res.status}`);
    return await res.json();
  }
};

// --- 기능 함수 ---

// 인증 및 사용자 관련
export const login = (id: string, pw: string) => api.post("/auth/login", { id, password: pw });
export const signup = (data: any) => api.post("/auth/register", data);
export const checkIdDuplicate = (id: string) => api.post("/auth/check-id", { id });

// 프로필 및 설정 관련 (추가 및 수정)
export const getUserProfile = (uid: string) => api.get(`/user/${uid}/profile`);
export const updateUserProfile = (uid: string, profileData: any) => 
  api.put(`/user/${uid}/profile`, profileData);
export const updateStudySettings = (uid: string, settingsData: any) => 
  api.put(`/user/${uid}/settings`, settingsData);

// 학습 관련
export const getWords = (lv: string, uid: string) => api.get(`/study/words?level=${lv}&user_id=${uid}`);
export const getReviewWords = (uid: string) => api.get(`/study/review-words?user_id=${uid}`);
export const getQuiz = (lv: string) => api.get(`/study/quiz?level=${lv}`);
export const getUserProgress = (uid: string) => api.get(`/study/current-progress?user_id=${uid}`);
export const uploadRecord = (fd: FormData) => api.post("/speech/evaluate", fd);
export const completeStudy = (lv: string, uid: string) => {
  const fd = new FormData(); 
  fd.append("level", lv); 
  fd.append("user_id", uid);
  return api.post("/study/complete", fd);
};

// 선생님 및 공지사항 관련 (수정 완료)
export const getStudents = () => api.get("/api/teacher/students");
export const getNotices = () => api.get("/api/teacher/notices");
export const getStudentNotices = () => api.get("/api/notice/list");

// sendNotice: 객체 형태로 인자를 받으며 scheduled_at을 포함합니다.
export const sendNotice = (data: { 
  title: string; 
  content: string; 
  author: string; 
  scheduled_at: string | null 
}) => api.post("/api/teacher/notice", data);

// [추가] 선생님용: 특정 학생 상세 정보 가져오기
export const getStudentDetail = (uid: string) => api.get(`/api/teacher/student/${uid}`);