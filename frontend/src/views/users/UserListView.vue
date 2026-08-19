<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import AddUserModal from './components/AddUserModal.vue'
import EditUserModal from './components/EditUserModal.vue'
import ResetPasswordModal from './components/ResetPasswordModal.vue'
import ViewLockSeqModal from './components/ViewLockSeqModal.vue'
import ResetLockModal from './components/ResetLockModal.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

interface UserItem {
  id: number
  username: string
  nickname?: string
  egg_energy?: number
  lock_pattern?: string
  lock_reset_flag?: string
  is_active?: boolean
  is_admin?: boolean
}

const users = ref<UserItem[]>([])
const loading = ref(false)

const isAddModalOpen = ref(false)
const isEditModalOpen = ref(false)
const isResetPasswordModalOpen = ref(false)
const isViewLockSeqModalOpen = ref(false)
const isResetLockModalOpen = ref(false)
const isDeactivateModalOpen = ref(false)

const selectedUser = ref<UserItem | null>(null)

async function loadUsers() {
  loading.value = true
  try {
    const res: any = await apiClient.get('/api/admin/users')
    users.value = res || []
  } catch (e) {
  } finally {
    loading.value = false
  }
}

function handleOpenEdit(user: UserItem) {
  selectedUser.value = user
  isEditModalOpen.value = true
}

function handleOpenResetPassword(user: UserItem) {
  selectedUser.value = user
  isResetPasswordModalOpen.value = true
}

function handleOpenViewLockSeq(user: UserItem) {
  selectedUser.value = user
  isViewLockSeqModalOpen.value = true
}

function handleOpenResetLock(user: UserItem) {
  selectedUser.value = user
  isResetLockModalOpen.value = true
}

function promptDeactivateUser(user: UserItem) {
  selectedUser.value = user
  isDeactivateModalOpen.value = true
}

async function confirmDeactivateUser() {
  if (!selectedUser.value) return
  try {
    await apiClient.post(`/api/admin/users/${selectedUser.value.id}/deactivate`)
    showToast('账户停用成功！', 'success')
    isDeactivateModalOpen.value = false
    loadUsers()
  } catch (err: any) {
    showToast(err.response?.data?.detail || '停用失败', 'error')
  }
}

async function handleActivateUser(user: UserItem) {
  try {
    await apiClient.post(`/api/admin/users/${user.id}/activate`)
    showToast('账户已重新启用！', 'success')
    loadUsers()
  } catch (err: any) {
    showToast(err.response?.data?.detail || '启用失败', 'error')
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div style="display: flex; flex-direction: column; width: 100%;">
    <!-- 顶部 Header (1:1 严格对齐 194) -->
    <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; width: 100%;">
      <div>
        <h2 style="font-size: 1.4rem; font-weight: 800; margin: 0; color: var(--text-main);">👦 账号列表</h2>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; margin-bottom: 0;">
          管理孩子的账户、初始密码以及安全解锁手势
        </p>
      </div>
      <button class="btn btn-primary-purple" @click="isAddModalOpen = true">
        + 新增账户
      </button>
    </header>

    <!-- 账号列表卡片 (1:1 严格对齐 194) -->
    <div class="card" style="border: 1px solid var(--card-border); padding: 0; overflow: hidden;">
      <table class="user-table" style="margin: 0; width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="width: 80px;">ID</th>
            <th>用户名</th>
            <th>昵称</th>
            <th>解锁序列</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 40px;">
              数据加载中...
            </td>
          </tr>
          <tr v-else-if="users.filter((u) => !u.is_admin).length === 0">
            <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 40px;">
              暂无孩子账号，请点击右上角新增
            </td>
          </tr>
          <tr v-for="user in users.filter((u) => !u.is_admin)" :key="user.id">
            <td style="font-size: 0.88rem; font-weight: 700; color: var(--text-muted);">
              {{ user.id }}
            </td>
            <td style="font-weight: 600; color: var(--text-main);">
              {{ user.username }}
              <span
                v-if="user.lock_reset_flag === 'default_requested'"
                style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; margin-left: 5px; cursor: help; border: 1px solid rgba(245, 158, 11, 0.3);"
                title="待手机端下次网络请求时重置解锁序列"
              >
                ⚠️ 待重置
              </span>
              <span
                v-if="user.is_active === false"
                style="background: rgba(239, 68, 68, 0.12); color: #fca5a5; font-size: 0.72rem; padding: 2px 6px; border-radius: 6px; margin-left: 5px; font-weight: 700; border: 1px solid rgba(239, 68, 68, 0.2);"
              >
                已停用
              </span>
            </td>
            <td>
              <span v-if="user.nickname" style="color: var(--text-main);">{{ user.nickname }}</span>
              <span v-else style="color: var(--text-muted);">未设置</span>
            </td>
            <td>
              <button
                type="button"
                class="btn-sm btn-sm-primary"
                title="查看最新解锁码序列"
                @click="handleOpenViewLockSeq(user)"
              >
                👁️ 查看
              </button>
            </td>
            <td>
              <div class="action-links" style="display: inline-flex; align-items: center; gap: 8px;">
                <button
                  type="button"
                  class="btn-sm btn-sm-primary"
                  title="修改账户用户名与昵称"
                  @click="handleOpenEdit(user)"
                >
                  ✏️
                </button>
                <button
                  type="button"
                  class="btn-sm btn-sm-primary"
                  title="重置安全密码"
                  @click="handleOpenResetPassword(user)"
                >
                  🔑
                </button>
                <button
                  type="button"
                  class="btn-sm btn-sm-warning"
                  title="重置解锁序列"
                  @click="handleOpenResetLock(user)"
                >
                  🦕
                </button>
                <button
                  v-if="user.is_active !== false"
                  type="button"
                  class="btn-sm btn-sm-danger"
                  title="停用该账户 (保留数据)"
                  @click="promptDeactivateUser(user)"
                >
                  停用
                </button>
                <button
                  v-else
                  type="button"
                  class="btn-sm"
                  style="background: rgba(34, 197, 94, 0.15) !important; color: #4ade80 !important; border: 1px solid rgba(34, 197, 94, 0.25) !important;"
                  title="重新启用该账户"
                  @click="handleActivateUser(user)"
                >
                  启用
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 模态框组件群 -->
    <AddUserModal v-model="isAddModalOpen" @success="loadUsers" />
    <EditUserModal v-model="isEditModalOpen" :user="selectedUser" @success="loadUsers" />
    <ResetPasswordModal v-model="isResetPasswordModalOpen" :user="selectedUser" @success="loadUsers" />
    <ViewLockSeqModal v-model="isViewLockSeqModalOpen" :user="selectedUser" />
    <ResetLockModal v-model="isResetLockModalOpen" :user="selectedUser" @success="loadUsers" />

    <!-- 停用警告确认弹窗 -->
    <ConfirmModal
      v-model="isDeactivateModalOpen"
      title="⚠️ 停用账号警告"
      :message="`您确定要停用孩子账户「${selectedUser?.username}」吗？停用后该账户将无法登录使用，但其全部日记及录音文件均将完好保留在服务器，您可随时在后台一键重新启用。`"
      confirm-text="确定停用"
      type="danger"
      @confirm="confirmDeactivateUser"
    />
  </div>
</template>
