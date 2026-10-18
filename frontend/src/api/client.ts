const API_BASE = '/api/v1';

export interface UserSession {
  token: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: 'ADMIN' | 'TEACHER' | 'STUDENT';
    is_active: boolean;
  };
}

class ApiError extends Error {
  statusCode: number;
  constructor(message: string, statusCode: number) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('srp_token');
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Do not set Content-Type if payload is FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      if (errorJson.error && errorJson.error.message) {
        errorDetail = errorJson.error.message;
      } else if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Ignore parse failure
    }
    throw new ApiError(errorDetail, response.status);
  }

  return response.json();
}

export const api = {
  // Authentication
  login: (email: string, password: string): Promise<UserSession> =>
    request<UserSession>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  getMe: () => request<UserSession['user']>('/auth/me'),

  // Academic Management
  getSessions: () => request<any[]>('/academic/sessions'),
  createSession: (data: any) =>
    request<any>('/academic/sessions', { method: 'POST', body: JSON.stringify(data) }),
  updateSessionStatus: (sessionId: string, status: string) =>
    request<any>(`/academic/sessions/${sessionId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  getCourses: () => request<any[]>('/academic/courses'),
  createCourse: (data: any) =>
    request<any>('/academic/courses', { method: 'POST', body: JSON.stringify(data) }),

  getDepartments: () => request<any[]>('/academic/departments'),
  getPrograms: (deptId?: string) =>
    request<any[]>(deptId ? `/academic/programs?department_id=${deptId}` : '/academic/programs'),

  // Teacher & Student Management
  createTeacher: (data: any) =>
    request<any>('/users-mgmt/teachers', { method: 'POST', body: JSON.stringify(data) }),
  createStudent: (data: any) =>
    request<any>('/users-mgmt/students', { method: 'POST', body: JSON.stringify(data) }),
  createAssignment: (data: any) =>
    request<any>('/users-mgmt/assignments', { method: 'POST', body: JSON.stringify(data) }),
  createEnrollment: (data: any) =>
    request<any>('/users-mgmt/enrollments', { method: 'POST', body: JSON.stringify(data) }),

  getTeacherAssignments: () => request<any[]>('/users-mgmt/teachers/me/assignments'),

  // CSV Imports
  getTemplateUrl: () => `${API_BASE}/imports/template`,
  uploadCsv: (sessionId: string, courseId: string, maxMarks: number, file: File) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('course_id', courseId);
    formData.append('max_marks', maxMarks.toString());
    formData.append('file', file);
    return request<any>('/imports/upload', {
      method: 'POST',
      body: formData,
    });
  },
  getBatch: (batchId: string) => request<any>(`/imports/batches/${batchId}`),
  approveBatch: (batchId: string) =>
    request<any>(`/imports/batches/${batchId}/approve`, { method: 'POST' }),
  rejectBatch: (batchId: string, rejectionReason: string) =>
    request<any>(`/imports/batches/${batchId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejection_reason: rejectionReason }),
    }),

  // Official Marks & Amendments
  getOfficialMarks: (sessionId: string, courseId?: string, studentId?: string) => {
    const params = new URLSearchParams({ session_id: sessionId });
    if (courseId) params.append('course_id', courseId);
    if (studentId) params.append('student_id', studentId);
    return request<any[]>(`/marks/official?${params.toString()}`);
  },
  amendOfficialMark: (markId: string, data: { new_marks_obtained: number; new_is_absent?: boolean; reason: string }) =>
    request<any>(`/marks/official/${markId}/amend`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getMarkAmendments: (markId: string) =>
    request<any[]>(`/marks/official/${markId}/amendments`),

  // Calculation & Publication
  calculateResults: (sessionId: string, allowPartial: boolean = false) =>
    request<any>(`/results/sessions/${sessionId}/calculate`, {
      method: 'POST',
      body: JSON.stringify({ allow_partial: allowPartial }),
    }),
  getSessionSummary: (sessionId: string) =>
    request<any>(`/results/sessions/${sessionId}/summary`),
  listSessionResults: (sessionId: string, resultStatus?: string, isWithheld?: boolean) => {
    const params = new URLSearchParams();
    if (resultStatus) params.append('result_status', resultStatus);
    if (isWithheld !== undefined) params.append('is_withheld', String(isWithheld));
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<any[]>(`/results/sessions/${sessionId}/students${qs}`);
  },
  withholdResult: (resultId: string, isWithheld: boolean, reason?: string) =>
    request<any>(`/results/${resultId}/withhold`, {
      method: 'PATCH',
      body: JSON.stringify({ is_withheld: isWithheld, reason }),
    }),
  publishSession: (sessionId: string) =>
    request<any>(`/results/sessions/${sessionId}/publish`, { method: 'POST' }),
  unpublishSession: (sessionId: string, reason: string) =>
    request<any>(`/results/sessions/${sessionId}/unpublish`, {
      method: 'POST',
      body: JSON.stringify({ is_withheld: false, reason }),
    }),

  // Student Results Portal
  getMyResults: () => request<any[]>('/results/my-results'),
  getMySessionResult: (sessionId: string) => request<any>(`/results/my-results/sessions/${sessionId}`),

  // Audit Logs
  getAuditLogs: (limit = 50, action?: string) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (action) params.append('action', action);
    return request<any[]>(`/audit/logs?${params.toString()}`);
  },
};
