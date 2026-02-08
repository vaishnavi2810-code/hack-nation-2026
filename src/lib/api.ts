import axios from 'axios'

export const api = axios.create({
  baseURL: 'https://api.mommode.ai',
  timeout: 10000,
})

export const getClinicOverview = () => api.get('/clinic/overview')
export const getAppointments = () => api.get('/appointments')
export const getPatients = () => api.get('/patients')
export const getCallHistory = () => api.get('/calls')
