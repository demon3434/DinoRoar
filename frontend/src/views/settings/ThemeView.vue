<script setup lang="ts">
import { computed, onMounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
const currentTheme = computed(() => themeStore.currentTheme)
const themes = themeStore.themes

async function changeTheme(themeName: string) {
  themeStore.applyTheme(themeName)
  try {
    await apiClient.post('/api/auth/theme', { theme: themeName })
    showToast('主题切换成功并已保存！', 'success')
  } catch (e) {
    console.error('Failed to save theme preference', e)
  }
}

onMounted(() => {
  themeStore.fetchUserTheme()
})
</script>

<template>
  <div class="theme-view" style="width: 100%;">
    <header style="margin-bottom: 30px; width: 100%;">
      <h2 style="font-size: 1.4rem; font-weight: 800;">🎨 个性化配色主题</h2>
      <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">为您的管理控制台选择一款赏心悦目的配色风格，支持实时切换预览</p>
    </header>

    <div class="card" style="max-width: 600px; border: 1px solid var(--card-border);">
      <div class="card-title">切换系统配色风格</div>
      <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 25px; line-height: 1.6;">
        选择您喜爱的色彩方案。切换后页面风格将立即无缝更新，并同步至云端偏好设置，下次登录时自动载入。
      </p>

      <div class="form-group">
        <label class="form-label">选择系统主题</label>
        <div class="theme-grid">
          <button
            v-for="t in themes"
            :id="'theme-btn-' + t.id"
            :key="t.id"
            type="button"
            class="theme-btn"
            :class="{ active: currentTheme === t.id }"
            @click="changeTheme(t.id)"
          >
            <span>{{ t.name }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.theme-view {
  display: flex;
  flex-direction: column;
}

.theme-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 15px;
}

.theme-btn {
  height: 44px;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  color: var(--text-main);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: flex-start;
  text-align: left;
}

.theme-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--primary, #8b5cf6);
  transform: translateY(-1px);
}

.theme-btn.active {
  background: rgba(139, 92, 246, 0.15) !important;
  border-color: #8b5cf6 !important;
  color: #c084fc !important;
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.2) !important;
}

/* 浅色主题下的按钮高亮优化 */
:root.theme-light-warm .theme-btn.active,
:root.theme-nordic-cool .theme-btn.active,
:root.theme-sakura-peach .theme-btn.active,
:root.theme-autumn-maple .theme-btn.active,
:root.theme-macaron-pink .theme-btn.active,
:root.theme-macaron-blue .theme-btn.active,
:root.theme-macaron-green .theme-btn.active,
:root.theme-macaron-yellow .theme-btn.active,
:root.theme-macaron-purple .theme-btn.active,
:root.theme-macaron-orange .theme-btn.active {
  background: rgba(139, 92, 246, 0.12) !important;
  border-color: #8b5cf6 !important;
  color: #7c3aed !important;
}
</style>
