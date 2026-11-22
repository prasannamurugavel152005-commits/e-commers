import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL?.trim() || '/api',
})

export const authStorage = {
  save({ access, refresh }) {
    localStorage.setItem('pexo_access', access)
    localStorage.setItem('pexo_refresh', refresh)
  },
  clear() {
    localStorage.removeItem('pexo_access')
    localStorage.removeItem('pexo_refresh')
  },
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('pexo_access')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config
    const refresh = localStorage.getItem('pexo_refresh')
    const isAuthRequest = ['/accounts/login/', '/accounts/register/', '/accounts/refresh/']
      .some((path) => request?.url?.includes(path))

    if (
      error.response?.status !== 401 ||
      !request ||
      request._retry ||
      !refresh ||
      isAuthRequest
    ) {
      return Promise.reject(error)
    }

    request._retry = true
    try {
      const { data } = await api.post('/accounts/refresh/', { refresh })
      localStorage.setItem('pexo_access', data.access)
      request.headers.Authorization = `Bearer ${data.access}`
      return api(request)
    } catch (refreshError) {
      authStorage.clear()
      window.dispatchEvent(new Event('pexo:session-expired'))
      return Promise.reject(refreshError)
    }
  },
)

export default api
