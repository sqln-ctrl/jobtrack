import axios from 'axios'

export const api = axios.create({ baseURL: '/api/v1', withCredentials: true })

const readCsrf = () => {
  const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

// Double-submit CSRF: echo the readable cookie in a header on every state-changing request.
api.interceptors.request.use((config) => {
  if (!['get', 'head', 'options'].includes((config.method || 'get').toLowerCase())) {
    config.headers['X-CSRF-Token'] = readCsrf()
  }
  return config
})

export const errorMessage = (error, fallback = 'Something went wrong. Try again.') => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join('. ')
  return fallback
}
