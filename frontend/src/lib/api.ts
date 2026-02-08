import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'https://api.mommode.ai'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

type ApiPayload = Record<string, unknown>
type QueryParams = Record<string, string | number | boolean | undefined>

// Auth
export const signup = (payload: ApiPayload) => api.post('/auth/signup', payload)
export const login = (payload: ApiPayload) => api.post('/auth/login', payload)
export const logout = () => api.post('/auth/logout')

// Doctors
export const getDoctorProfile = () => api.get('/doctors/me')

// Calendar
export const getCalendarAuthUrl = () => api.get('/calendar/auth-url')
export const postCalendarCallback = (payload: ApiPayload) => api.post('/calendar/callback', payload)
export const getCalendarStatus = () => api.get('/calendar/status')
export const disconnectCalendar = () => api.post('/calendar/disconnect')
export const getCalendarAvailability = (params?: QueryParams) =>
  api.get('/calendar/availability', { params })

// Patients
export const getPatients = (params?: QueryParams) => api.get('/patients', { params })
export const createPatient = (payload: ApiPayload) => api.post('/patients', payload)
export const getPatient = (id: string) => api.get(`/patients/${id}`)
export const updatePatient = (id: string, payload: ApiPayload) => api.put(`/patients/${id}`, payload)
export const deletePatient = (id: string) => api.delete(`/patients/${id}`)

// Appointments
export const getAppointments = (params?: QueryParams) => api.get('/appointments', { params })
export const getUpcomingAppointments = (params?: QueryParams) =>
  api.get('/appointments/upcoming', { params })
export const createAppointment = (payload: ApiPayload) => api.post('/appointments', payload)
export const updateAppointment = (id: string, payload: ApiPayload) =>
  api.put(`/appointments/${id}`, payload)
export const deleteAppointment = (id: string) => api.delete(`/appointments/${id}`)
export const confirmAppointment = (id: string) => api.post(`/appointments/${id}/confirm`)

// Calls
export const getCalls = (params?: QueryParams) => api.get('/calls', { params })
export const getScheduledCalls = (params?: QueryParams) => api.get('/calls/scheduled', { params })
export const getCall = (id: string) => api.get(`/calls/${id}`)
export const createManualCall = (payload: ApiPayload) => api.post('/calls/manual', payload)

// Dashboard
export const getDashboardStats = () => api.get('/dashboard/stats')
export const getDashboardActivity = () => api.get('/dashboard/activity')

// Settings
export const getSettings = () => api.get('/settings')
export const updateSettings = (payload: ApiPayload) => api.put('/settings', payload)
