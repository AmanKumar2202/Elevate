import axios from 'axios'

// All API calls go through /api — Vite proxy forwards to http://localhost:8000
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect to /login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ─── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post<{
      access_token: string
      token_type: string
      user: User
    }>('/auth/login', { email, password }),
}

// ─── Users ─────────────────────────────────────────────────────────────────────
export const usersApi = {
  getMe: () => api.get<User>('/users/me'),
  getMyReports: () => api.get<DirectReport[]>('/users/my-reports'),
}

// ─── Feedback ──────────────────────────────────────────────────────────────────
export const feedbackApi = {
  getParameters: () => api.get<FeedbackParameter[]>('/feedback/parameters'),
  getCycles: () => api.get<Cycle[]>('/feedback/cycles'),
  getCurrentCycle: () => api.get<Cycle>('/feedback/cycles/current'),
  getMySubmissions: (cycleId: number) =>
    api.get<SubmissionStatus[]>(`/feedback/my-submissions?cycle_id=${cycleId}`),
  submitFeedback: (payload: SubmitFeedbackPayload) =>
    api.post<{ id: number; status: string }>('/feedback/submit', payload),
  getReceived: () => api.get<ReceivedFeedback[]>('/feedback/received'),
  getTrends: () => api.get<ParameterTrend[]>('/feedback/trends'),
}

// ─── HR ────────────────────────────────────────────────────────────────────────
export const hrApi = {
  getCycles: () => api.get<Cycle[]>('/hr/cycles'),
  getPending: (cycleId: number) =>
    api.get<ManagerPendingReport[]>(`/hr/pending?cycle_id=${cycleId}`),
}

// ─── Types ─────────────────────────────────────────────────────────────────────
export interface User {
  id: number
  name: string
  email: string
  role: 'EMPLOYEE' | 'HR'
  company_id: number
  company_name: string
  manager_id: number | null
  title: string | null
  has_reports?: boolean
}

export interface DirectReport {
  id: number
  name: string
  email: string
  title: string | null
}

export interface FeedbackParameter {
  id: number
  name: string
  description: string | null
}

export interface Cycle {
  id: number
  month: number
  year: number
}

export interface ScoreIn {
  parameter_id: number
  score: number
  comment: string
}

export interface SubmitFeedbackPayload {
  cycle_id: number
  given_to_id: number
  scores: ScoreIn[]
  status: 'DRAFT' | 'SUBMITTED'
}

export interface ScoreOut {
  parameter_id: number
  parameter_name: string
  score: number
  comment: string
}

export interface SubmissionStatus {
  feedback_id: number | null
  employee: DirectReport
  status: 'SUBMITTED' | 'DRAFT' | 'PENDING'
  submitted_at: string | null
  scores: ScoreIn[]
}

export interface ReceivedFeedback {
  cycle_id: number
  month: number
  year: number
  status: string
  given_by_name: string
  scores: ScoreOut[]
}

export interface MonthlyScore {
  month: number
  year: number
  score: number
}

export interface ParameterTrend {
  parameter_id: number
  parameter_name: string
  monthly_scores: MonthlyScore[]
}

export interface ManagerPendingReport {
  manager: DirectReport
  total_reports: number
  submitted_count: number
  pending_employees: DirectReport[]
}

export const MONTH_NAMES = [
  '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]
