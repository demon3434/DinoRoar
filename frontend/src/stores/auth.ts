import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('dinoroar_token'))
  const user = ref<UserInfo | null>(
    localStorage.getItem('dinoroar_user') 
      ? JSON.parse(localStorage.getItem('dinoroar_user')!) 
      : null
  )

  const isAuthenticated = computed(() => !!token.value)

  function setAuth(newToken: string, userInfo?: UserInfo) {
    token.value = newToken
    localStorage.setItem('dinoroar_token', newToken)
    if (userInfo) {
      user.value = userInfo
      localStorage.setItem('dinoroar_user', JSON.stringify(userInfo))
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('dinoroar_token')
    localStorage.removeItem('dinoroar_user')
  }

  return {
    token,
    user,
    isAuthenticated,
    setAuth,
    logout
  }
})
