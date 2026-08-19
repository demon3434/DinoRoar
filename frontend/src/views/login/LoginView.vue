<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { showToast } from '@/utils/toast'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!username.value.trim() || !password.value.trim()) {
    errorMessage.value = '请输入账号名称与安全密码'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const formData = new FormData()
    formData.append('username', username.value.trim())
    formData.append('password', password.value.trim())

    const res: any = await apiClient.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    if (res.access_token) {
      localStorage.setItem('dinoroar_token', res.access_token)
      localStorage.setItem('token', res.access_token)
      // 获取当前用户完整身份
      const meRes: any = await apiClient.get('/api/auth/me')
      authStore.setAuth(res.access_token, meRes)

      if (meRes.theme) {
        themeStore.applyTheme(meRes.theme)
      }

      showToast('登录成功，欢迎进入树洞！', 'success')
      if (meRes.is_admin) {
        router.push('/admin/users')
      } else {
        window.location.href = '/dashboard'
      }
    }
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || '用户名或密码错误'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="blob blob-1" />
    <div class="blob blob-2" />

    <div class="container">
      <div class="login-card">
        <div class="logo-area">
          <h1 class="logo-text">DinoRoar</h1>
          <p class="logo-desc">🦖 恐龙风暴 · 私密树洞守护舱 🦕</p>
        </div>

        <form id="loginForm" @submit.prevent="handleLogin">
          <div class="input-group">
            <label class="input-label" for="username">账号名称</label>
            <input
              id="username"
              v-model="username"
              class="input-field"
              type="text"
              required
              placeholder="输入账号名称"
              autocomplete="username"
            />
          </div>
          <div class="input-group">
            <label class="input-label" for="password">安全密码</label>
            <input
              id="password"
              v-model="password"
              class="input-field"
              type="password"
              required
              placeholder="输入密码"
              autocomplete="current-password"
            />
          </div>
          <button class="login-btn" type="submit" :disabled="loading">
            {{ loading ? '正在验证...' : '进入树洞' }}
          </button>
        </form>

        <div v-if="errorMessage" class="error-msg">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%);
  color: #f8fafc;
  overflow: hidden;
  position: relative;
  font-family: 'Outfit', 'Noto Sans SC', sans-serif;
}

.blob {
  position: absolute;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
  border-radius: 50%;
  z-index: 0;
  filter: blur(50px);
}
.blob-1 {
  top: -10%;
  left: -10%;
}
.blob-2 {
  bottom: -10%;
  right: -10%;
}

.container {
  z-index: 10;
  width: 100%;
  max-width: 420px;
  padding: 20px;
}

.login-card {
  background: rgba(30, 27, 75, 0.45);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(168, 85, 247, 0.25);
  border-radius: 24px;
  padding: 40px 30px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  text-align: center;
  animation: fadeInUp 0.8s ease-out;
}

.logo-area {
  margin-bottom: 30px;
}

.logo-text {
  font-size: 2.2rem;
  font-weight: 800;
  background: linear-gradient(to right, #a855f7, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.logo-desc {
  font-size: 0.9rem;
  color: #94a3b8;
}

.input-group {
  margin-bottom: 20px;
  text-align: left;
}

.input-label {
  display: block;
  font-size: 0.85rem;
  color: #94a3b8;
  margin-bottom: 8px;
  font-weight: 600;
}

.input-field {
  width: 100%;
  padding: 14px 20px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #f8fafc;
  font-size: 1rem;
  transition: all 0.3s ease;
  outline: none;
  box-sizing: border-box;
}

.input-field:focus {
  border-color: #a855f7;
  box-shadow: 0 0 10px rgba(168, 85, 247, 0.3);
  background: rgba(15, 23, 42, 0.8);
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 15px;
  box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6);
}

.login-btn:active {
  transform: translateY(1px) scale(0.96);
  filter: brightness(0.9);
}

.error-msg {
  color: #ef4444;
  font-size: 0.85rem;
  margin-top: 15px;
  text-align: center;
  background: rgba(239, 68, 68, 0.15);
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
