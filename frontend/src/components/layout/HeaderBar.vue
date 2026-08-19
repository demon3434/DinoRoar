<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { Palette, LogOut, User } from 'lucide-vue-next'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const router = useRouter()

const isThemeMenuOpen = ref(false)
const showLogoutConfirm = ref(false)

function handleSelectTheme(themeId: string) {
  themeStore.applyTheme(themeId)
  isThemeMenuOpen.value = false
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="header-bar">
    <div class="header-left">
      <!-- Breadcrumb / Slot -->
      <slot name="title" />
    </div>

    <div class="header-right">
      <!-- Theme Switcher -->
      <div class="theme-dropdown-container">
        <button
          type="button"
          class="icon-btn"
          title="切换主题"
          @click="isThemeMenuOpen = !isThemeMenuOpen"
        >
          <Palette class="w-5 h-5 text-blue-400" />
        </button>

        <div v-if="isThemeMenuOpen" class="theme-menu glass-panel animate-fade-in" @click.stop>
          <div class="theme-menu-title">选择系统主题</div>
          <button
            v-for="t in themeStore.themes"
            :key="t.id"
            type="button"
            class="theme-menu-item"
            :class="{ 'is-selected': themeStore.currentTheme === t.id }"
            @click="handleSelectTheme(t.id)"
          >
            <span class="theme-color-dot" :style="{ backgroundColor: t.color }" />
            <span>{{ t.name }}</span>
          </button>
        </div>
      </div>

      <!-- User Profile & Logout -->
      <div class="user-profile">
        <div class="avatar-box">
          <User class="w-4 h-4 text-emerald-400" />
        </div>
        <span class="username">{{ authStore.user?.username || '管理员' }}</span>
      </div>

      <button
        type="button"
        class="icon-btn btn-logout"
        title="退出登录"
        @click="showLogoutConfirm = true"
      >
        <LogOut class="w-5 h-5 text-rose-400" />
      </button>
    </div>

    <!-- Logout Confirmation Modal -->
    <ConfirmModal
      v-model="showLogoutConfirm"
      title="退出登录确认"
      message="确定要退出 DinoRoar 管理后台吗？"
      confirm-text="退出登录"
      type="danger"
      @confirm="handleLogout"
    />
  </header>
</template>

<style scoped>
.header-bar {
  height: 64px;
  background: var(--header-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--card-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 90;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-btn {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--card-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.theme-dropdown-container {
  position: relative;
}

.theme-menu {
  position: absolute;
  top: 48px;
  right: 0;
  width: 180px;
  padding: 8px;
  background: var(--modal-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-md);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 120;
}

.theme-menu-title {
  font-size: 0.76rem;
  color: var(--text-muted);
  font-weight: 600;
  padding: 6px 8px;
}

.theme-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: transparent;
  border: none;
  color: var(--text-main);
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s ease;
  text-align: left;
}

.theme-menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.theme-menu-item.is-selected {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  font-weight: 600;
}

.theme-color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  shrink: 0;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--card-border);
  border-radius: 9999px;
}

.avatar-box {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.username {
  font-size: 0.86rem;
  font-weight: 500;
  color: var(--text-main);
}
</style>
