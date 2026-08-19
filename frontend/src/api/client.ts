import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { showToast } from '@/utils/toast'

const apiClient = axios.create({
  baseURL: '',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request Interceptor: Attach Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('dinoroar_token') || localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response Interceptor: Global Error Handling & Toast
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const status = error.response?.status
    const dataDetail = error.response?.data?.detail
    let message = error.response?.data?.message || error.message || '网络请求失败，请稍后重试'

    if (typeof dataDetail === 'string') {
      message = dataDetail
    } else if (Array.isArray(dataDetail) && dataDetail.length > 0) {
      message = dataDetail.map((d: any) => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg || ''}`).join('; ')
    } else if (dataDetail && typeof dataDetail === 'object') {
      message = dataDetail.msg || JSON.stringify(dataDetail)
    }

    if (status === 401) {
      localStorage.removeItem('dinoroar_token')
      localStorage.removeItem('token')
      localStorage.removeItem('dinoroar_user')
      if (!window.location.pathname.includes('/login')) {
        showToast('登录状态已失效，请重新登录', 'warning')
        window.location.href = '/login'
      }
    } else {
      showToast(message, 'error')
    }

    return Promise.reject(error)
  }
)

export default apiClient
