import axios from 'axios'

const rawBaseApiUrl = import.meta.env.VITE_API_URL || '/api/v1'
const baseApiUrl = rawBaseApiUrl.replace(/^http:\/\//i, 'https://')
const API_URL = baseApiUrl.endsWith('/api/v1') ? baseApiUrl : `${baseApiUrl}/api/v1`

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor do dodawania tokena
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor do obsługi błędów
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)



