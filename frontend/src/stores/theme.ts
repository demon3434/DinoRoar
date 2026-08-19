import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiClient from '@/api/client'

export interface ThemeOption {
  id: string
  name: string
  color: string
}

export const THEME_PRESETS: ThemeOption[] = [
  { id: 'dark-neon', name: '🌌 暗色霓虹 (默认)', color: '#8b5cf6' },
  { id: 'light-warm', name: '☀️ 温暖浅沙', color: '#f59e0b' },
  { id: 'nordic-cool', name: '❄️ 极简冷灰', color: '#64748b' },
  { id: 'deep-forest', name: '🌲 深邃苍林', color: '#10b981' },
  { id: 'aurora-night', name: '💚 极光幻夜', color: '#06b6d4' },
  { id: 'violet-dream', name: '💜 罗兰紫幻', color: '#a855f7' },
  { id: 'sakura-peach', name: '🌸 樱粉蜜桃', color: '#ec4899' },
  { id: 'autumn-maple', name: '🍁 枫叶秋枫', color: '#ea580c' },
  { id: 'macaron-pink', name: '🍭 马卡龙粉', color: '#f472b6' },
  { id: 'macaron-blue', name: '🌊 马卡龙蓝', color: '#38bdf8' },
  { id: 'macaron-green', name: '🍃 马卡龙绿', color: '#4ade80' },
  { id: 'macaron-yellow', name: '🍌 马卡龙黄', color: '#facc15' },
  { id: 'macaron-purple', name: '🍇 马卡龙紫', color: '#c084fc' },
  { id: 'macaron-orange', name: '🍊 马卡龙橙', color: '#fb923c' },
  { id: 'dark-cyber', name: '🦾 暗色赛博', color: '#00f0ff' },
  { id: 'dark-obsidian', name: '🖤 黑曜石暗', color: '#1e293b' }
]

export const useThemeStore = defineStore('theme', () => {
  const currentTheme = ref<string>(localStorage.getItem('cachedTheme') || 'dark-neon')

  function applyTheme(themeName: string) {
    if (!themeName) themeName = 'dark-neon'
    currentTheme.value = themeName
    localStorage.setItem('cachedTheme', themeName)
    document.documentElement.className = 'theme-' + themeName
  }

  async function fetchUserTheme() {
    try {
      const res: any = await apiClient.get('/api/auth/me')
      if (res && res.theme) {
        applyTheme(res.theme)
      }
    } catch (e) {}
  }

  // Initialize theme on store creation
  applyTheme(currentTheme.value)

  return {
    currentTheme,
    themes: THEME_PRESETS,
    applyTheme,
    fetchUserTheme
  }
})
