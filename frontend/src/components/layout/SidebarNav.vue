<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isCollapsed = ref(localStorage.getItem('sidebarCollapsed') === 'true')

type GroupKey = 'users' | 'stickers' | 'promotions' | 'checkin' | 'system' | 'personal'

const defaultGroups: Record<GroupKey, boolean> = {
  users: false,
  stickers: false,
  promotions: false,
  checkin: false,
  system: false,
  personal: false
}

function getGroupFromPath(path: string): GroupKey | null {
  if (path.startsWith('/admin/users')) return 'users'
  if (path.startsWith('/admin/stickers') || path.startsWith('/admin/canvases')) return 'stickers'
  if (path.startsWith('/admin/promotions')) return 'promotions'
  if (path.startsWith('/admin/checkin') || path.startsWith('/admin/energy')) return 'checkin'
  if (path.startsWith('/admin/maintenance')) return 'system'
  if (path.startsWith('/admin/password') || path.startsWith('/admin/theme')) return 'personal'
  return null
}



function loadInitialGroups(): Record<GroupKey, boolean> {
  const currentActiveGroup = getGroupFromPath(route.path) || 'stickers'
  const saved = localStorage.getItem('sidebarOpenGroups')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      return {
        ...defaultGroups,
        ...parsed,
        [currentActiveGroup]: true
      }
    } catch {}
  }
  return {
    ...defaultGroups,
    [currentActiveGroup]: true
  }
}

const openGroups = ref<Record<GroupKey, boolean>>(loadInitialGroups())

function saveGroups() {
  localStorage.setItem('sidebarOpenGroups', JSON.stringify(openGroups.value))
}

function toggleGroup(key: GroupKey) {
  openGroups.value[key] = !openGroups.value[key]
  saveGroups()
}

// 路由变化时自动展开当前页面所在的父菜单组并持久化
watch(
  () => route.path,
  (newPath) => {
    const activeGroup = getGroupFromPath(newPath)
    if (activeGroup && !openGroups.value[activeGroup]) {
      openGroups.value[activeGroup] = true
      saveGroups()
    }
  }
)

function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('sidebarCollapsed', String(isCollapsed.value))
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

const currentPath = computed(() => route.path)
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }" id="appSidebar">
    <!-- 品牌区域 -->
    <div class="sidebar-brand" @click="router.push('/admin/users')" style="cursor: pointer;">
      <div class="dino-avatar" id="sidebarDinoAvatar">
        <img src="/static/images/ic_launcher.png" alt="Dino Avatar" />
      </div>
      <div class="sidebar-title-container">
        <span class="sidebar-title" id="sidebarAdminName">
          {{ authStore.user?.nickname || authStore.user?.username || '管理员' }}
        </span>
        <span class="sidebar-subtitle">控制面板</span>
      </div>
    </div>

    <!-- 菜单区域 -->
    <div class="sidebar-menu">
      <!-- 👥 账户管理 -->
      <div class="menu-group" :class="{ open: openGroups.users }">
        <div
          class="menu-item"
          :class="{ active: currentPath.startsWith('/admin/users') }"
          @click="toggleGroup('users')"
        >
          <div class="menu-label-wrap">
            <span class="menu-emoji">👥</span>
            <span class="sidebar-text">账户管理</span>
          </div>
          <span class="menu-arrow" :class="{ rotated: openGroups.users }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </span>
        </div>
        <div class="submenu" :class="{ open: openGroups.users }">
          <router-link
            to="/admin/users"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/users' }"
          >
            👦 账号列表
          </router-link>
        </div>
      </div>

      <!-- 🎨 手账资产管理 -->
      <div class="menu-group" :class="{ open: openGroups.stickers }">
        <div
          class="menu-item"
          :class="{ active: currentPath.startsWith('/admin/stickers') || currentPath.startsWith('/admin/canvases') }"
          @click="toggleGroup('stickers')"
        >
          <div class="menu-label-wrap">
            <span class="menu-emoji">🎨</span>
            <span class="sidebar-text">手账资产管理</span>
          </div>
          <span class="menu-arrow" :class="{ rotated: openGroups.stickers }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </span>
        </div>
        <div class="submenu" :class="{ open: openGroups.stickers }">
          <router-link
            to="/admin/stickers"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/stickers' }"
          >
            🦄 贴纸管理
          </router-link>
          <router-link
            to="/admin/canvases"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/canvases' }"
          >
            🖼️ 画布管理
          </router-link>
        </div>
      </div>

      <!-- 🎉 优惠活动 -->
      <div class="menu-group" :class="{ open: openGroups.promotions }">
        <div
          class="menu-item"
          :class="{ active: currentPath.startsWith('/admin/promotions') }"
          @click="toggleGroup('promotions')"
        >
          <div class="menu-label-wrap">
            <span class="menu-emoji">🎉</span>
            <span class="sidebar-text">优惠活动</span>
          </div>
          <span class="menu-arrow" :class="{ rotated: openGroups.promotions }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </span>
        </div>
        <div class="submenu" :class="{ open: openGroups.promotions }">
          <router-link
            to="/admin/promotions"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/promotions' }"
          >
            🏷️ 优惠活动管理
          </router-link>
        </div>
      </div>

      <!-- 🥚 签到与能量调控 -->
      <div class="menu-group" :class="{ open: openGroups.checkin }">
        <div
          class="menu-item"
          :class="{ active: currentPath === '/admin/checkin' }"
          @click="toggleGroup('checkin')"
        >
          <div class="menu-label-wrap">
            <span class="menu-emoji">🥚</span>
            <span class="sidebar-text">签到与能量</span>
          </div>
          <span class="menu-arrow" :class="{ rotated: openGroups.checkin }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </span>
        </div>
        <div class="submenu" :class="{ open: openGroups.checkin }">
          <router-link
            to="/admin/checkin"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/checkin' }"
          >
            🥚 签到与能量配置
          </router-link>
          <router-link
            to="/admin/energy/ledger"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/energy/ledger' }"
          >
            📜 蛋能量流水账本
          </router-link>
        </div>

      </div>

      <!-- ⚙️ 系统维护 -->
      <div class="menu-group" :class="{ open: openGroups.system }">

        <div
          class="menu-item"
          :class="{ active: currentPath === '/admin/maintenance' }"
          @click="toggleGroup('system')"
        >
          <div class="menu-label-wrap">
            <span class="menu-emoji">⚙️</span>
            <span class="sidebar-text">系统维护</span>
          </div>
          <span class="menu-arrow" :class="{ rotated: openGroups.system }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </span>
        </div>
        <div class="submenu" :class="{ open: openGroups.system }">
          <router-link
            to="/admin/maintenance"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/maintenance' }"
          >
            🧹 磁盘冗余清理
          </router-link>
        </div>
      </div>

      <!-- 🔧 个人设置 -->
      <div class="menu-group" :class="{ open: openGroups.personal }">
        <div
          class="menu-item"
          :class="{ active: currentPath === '/admin/password' || currentPath === '/admin/theme' }"
          @click="toggleGroup('personal')"
        >
          <div class="menu-label-wrap">
            <span class="menu-emoji">🔧</span>
            <span class="sidebar-text">个人设置</span>
          </div>
          <span class="menu-arrow" :class="{ rotated: openGroups.personal }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </span>
        </div>
        <div class="submenu" :class="{ open: openGroups.personal }">
          <router-link
            to="/admin/password"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/password' }"
          >
            🔒 修改安全密码
          </router-link>
          <router-link
            to="/admin/theme"
            class="submenu-item"
            :class="{ active: currentPath === '/admin/theme' }"
          >
            🎨 个性化主题色
          </router-link>
        </div>
      </div>
    </div>

    <!-- 底部退出按钮 -->
    <div class="sidebar-footer">
      <button type="button" class="logout-btn" @click="handleLogout">
        <span>🚪</span>
        <span class="sidebar-text">退出控制台</span>
      </button>
    </div>

    <!-- 侧边栏折叠按钮 -->
    <div class="sidebar-collapse-btn" @click="toggleSidebar">
      <span id="collapseIcon">{{ isCollapsed ? '▶' : '◀' }}</span>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 260px;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid var(--card-border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: sticky;
  top: 0;
  height: 100vh;
  flex-shrink: 0;
  z-index: 100;
}

.sidebar.collapsed {
  width: 78px;
}

.sidebar-brand {
  padding: 20px 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  overflow: hidden;
  white-space: nowrap;
}

.dino-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  background: rgba(139, 92, 246, 0.15);
}

.dino-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sidebar-title-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: opacity 0.2s ease;
}

.sidebar-title {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-subtitle {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
}

.sidebar-menu {
  flex: 1;
  padding: 16px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}

.menu-group {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 14px;
  border-radius: 12px;
  color: var(--text-muted);
  text-decoration: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.92rem;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-main);
}

.menu-item.active {
  background: rgba(139, 92, 246, 0.15);
  color: #c084fc;
}

.menu-label-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.menu-arrow {
  width: 14px;
  height: 14px;
  transition: transform 0.3s ease;
}

.menu-arrow.rotated {
  transform: rotate(180deg);
}

.submenu {
  padding-left: 28px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition: max-height 0.3s ease, opacity 0.3s ease;
}

.submenu.open {
  max-height: 200px;
  opacity: 1;
  margin-top: 4px;
  margin-bottom: 6px;
}

.submenu-item {
  font-size: 0.86rem;
  padding: 8px 12px;
  border-radius: 8px;
  color: var(--text-muted);
  text-decoration: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  display: block;
}

.submenu-item:hover {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.04);
}

.submenu-item.active {
  color: #c084fc;
  font-weight: 700;
  background: rgba(139, 92, 246, 0.12);
}

.sidebar-footer {
  padding: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 38px;
  border-radius: 10px;
  padding: 0 10px;
  font-size: 0.85rem;
  font-weight: 600;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.logout-btn:hover {
  background: var(--dino-red);
  border-color: var(--dino-red);
  color: white;
}

.sidebar-collapse-btn {
  padding: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  color: var(--text-muted);
  transition: color 0.2s ease;
}

.sidebar.collapsed .sidebar-title-container,
.sidebar.collapsed .sidebar-text,
.sidebar.collapsed .menu-arrow,
.sidebar.collapsed .submenu {
  display: none !important;
}
</style>
