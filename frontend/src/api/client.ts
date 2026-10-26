export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');

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
  // System Health & Connectivity Diagnostics
  checkHealth: async () => {
    const start = performance.now();
    try {
      const res = await request<any>('/health');
      const latency = Math.round(performance.now() - start);
      return { ok: true, data: res, latency, apiBase: API_BASE };
    } catch (err: any) {
      const latency = Math.round(performance.now() - start);
      return { ok: false, error: err.message || 'Connection failed', latency, apiBase: API_BASE };
    }
  },
  // Authentication
  login: async (email: string, password: string): Promise<UserSession> => {
    const data = await request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    return {
      token: data.token || data.access_token,
      user: data.user || {
        id: String(data.user_id),
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        is_active: true,
      },
    };
  },

  getMe: () => request<UserSession['user']>('/auth/me'),

  // Authentication & System Setup
  getSetupStatus: () => request<{ needs_setup: boolean }>('/auth/setup-status'),
  bootstrapAdmin: (data: { email: string; password: string; full_name: string }) =>
    request<any>('/auth/bootstrap-admin', { method: 'POST', body: JSON.stringify(data) }),

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
  createDepartment: (data: { code: string; name: string }) =>
    request<any>('/academic/departments', { method: 'POST', body: JSON.stringify(data) }),

  getPrograms: (deptId?: string) =>
    request<any[]>(deptId ? `/academic/programs?department_id=${deptId}` : '/academic/programs'),
  createProgram: (data: { department_id: string; code: string; name: string; total_semesters: number }) =>
    request<any>('/academic/programs', { method: 'POST', body: JSON.stringify(data) }),

  // Teacher, Student & Enrollment Directory
  listTeachers: (departmentId?: string) =>
    request<any[]>(departmentId ? `/users-mgmt/teachers?department_id=${departmentId}` : '/users-mgmt/teachers'),
  createTeacher: (data: any) =>
    request<any>('/users-mgmt/teachers', { method: 'POST', body: JSON.stringify(data) }),

  listStudents: (programId?: string, semester?: number) => {
    const params = new URLSearchParams();
    if (programId) params.append('program_id', programId);
    if (semester) params.append('semester', semester.toString());
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<any[]>(`/users-mgmt/students${qs}`);
  },
  createStudent: (data: any) =>
    request<any>('/users-mgmt/students', { method: 'POST', body: JSON.stringify(data) }),

  listAssignments: (sessionId?: string, courseId?: string) => {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    if (courseId) params.append('course_id', courseId);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<any[]>(`/users-mgmt/assignments${qs}`);
  },
  createAssignment: (data: any) =>
    request<any>('/users-mgmt/assignments', { method: 'POST', body: JSON.stringify(data) }),

  listEnrollments: (sessionId?: string, courseId?: string) => {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    if (courseId) params.append('course_id', courseId);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<any[]>(`/users-mgmt/enrollments${qs}`);
  },
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
  listBatches: (sessionId?: string, courseId?: string) => {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    if (courseId) params.append('course_id', courseId);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<any[]>(`/imports/batches${qs}`);
  },
  getBatch: (batchId: string) => request<any>(`/imports/batches/${batchId}`),
  getBatchRows: (batchId: string, errorsOnly = false) =>
    request<any[]>(`/imports/batches/${batchId}/rows?errors_only=${errorsOnly}`),
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

  // Academic Updates & Deletions
  updateSession: (sessionId: string, data: any) =>
    request<any>(`/academic/sessions/${sessionId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteSession: (sessionId: string) =>
    request<any>(`/academic/sessions/${sessionId}`, { method: 'DELETE' }),
  updateCourse: (courseId: string, data: any) =>
    request<any>(`/academic/courses/${courseId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteCourse: (courseId: string) =>
    request<any>(`/academic/courses/${courseId}`, { method: 'DELETE' }),
  updateDepartment: (deptId: string, data: any) =>
    request<any>(`/academic/departments/${deptId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteDepartment: (deptId: string) =>
    request<any>(`/academic/departments/${deptId}`, { method: 'DELETE' }),
  updateProgram: (progId: string, data: any) =>
    request<any>(`/academic/programs/${progId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteProgram: (progId: string) =>
    request<any>(`/academic/programs/${progId}`, { method: 'DELETE' }),

  // Users Management Updates & Deletions
  updateTeacher: (teacherId: string, data: any) =>
    request<any>(`/users-mgmt/teachers/${teacherId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteTeacher: (teacherId: string) =>
    request<any>(`/users-mgmt/teachers/${teacherId}`, { method: 'DELETE' }),
  updateStudent: (studentId: string, data: any) =>
    request<any>(`/users-mgmt/students/${studentId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteStudent: (studentId: string) =>
    request<any>(`/users-mgmt/students/${studentId}`, { method: 'DELETE' }),
  deleteEnrollment: (enrollmentId: string) =>
    request<any>(`/users-mgmt/enrollments/${enrollmentId}`, { method: 'DELETE' }),
  deleteAssignment: (assignmentId: string) =>
    request<any>(`/users-mgmt/assignments/${assignmentId}`, { method: 'DELETE' }),

  // Database Administration ("Database Studio")
  getDbTables: () => request<any[]>('/database/tables'),
  getDbTableRows: (
    tableName: string,
    page = 1,
    limit = 25,
    search?: string,
    orderBy?: string,
    orderDir = 'asc'
  ) => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      order_dir: orderDir,
    });
    if (search && search.trim()) params.append('search', search.trim());
    if (orderBy && orderBy.trim()) params.append('order_by', orderBy.trim());
    return request<any>(`/database/tables/${encodeURIComponent(tableName)}/rows?${params.toString()}`);
  },
  insertDbRow: (tableName: string, data: Record<string, any>) =>
    request<any>(`/database/tables/${encodeURIComponent(tableName)}/rows`, {
      method: 'POST',
      body: JSON.stringify({ data }),
    }),
  updateDbRow: (tableName: string, rowId: string, data: Record<string, any>) =>
    request<any>(`/database/tables/${encodeURIComponent(tableName)}/rows/${encodeURIComponent(rowId)}`, {
      method: 'PUT',
      body: JSON.stringify({ data }),
    }),
  deleteDbRow: (tableName: string, rowId: string) =>
    request<any>(`/database/tables/${encodeURIComponent(tableName)}/rows/${encodeURIComponent(rowId)}`, {
      method: 'DELETE',
    }),
  executeDbQuery: (query: string, params?: Record<string, any>) =>
    request<any>('/database/query', {
      method: 'POST',
      body: JSON.stringify({ query, params }),
    }),
};
