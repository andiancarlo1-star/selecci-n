import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8443'
export async function downloadAuthenticated(path) {
  const { data, headers } = await api.get(path, { responseType: 'blob' })
  const blobUrl = URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = (headers['content-disposition']?.match(/filename="?([^";]+)"?/i)?.[1]) || 'cv'
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
}

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
    }
    return Promise.reject(error)
  }
)

export default api
