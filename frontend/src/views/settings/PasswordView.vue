<script setup lang="ts">
import { ref } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function handleChangePassword() {
  if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
    showToast('请填写所有密码字段', 'warning')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    showToast('两次输入的新密码不一致', 'warning')
    return
  }

  loading.value = true
  try {
    await apiClient.post('/api/admin/change-password', {
      current_password: currentPassword.value,
      new_password: newPassword.value
    })
    showToast('密码修改成功，请牢记您的新密码！', 'success')
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e) {
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="password-view" style="width: 100%;">
    <header style="margin-bottom: 30px; width: 100%;">
      <h2 style="font-size: 1.4rem; font-weight: 800;">🔒 修改管理员密码</h2>
      <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">定期更新您的管理员安全密码以保护服务器数据安全</p>
    </header>

    <div class="card" style="max-width: 550px; border: 1px solid var(--card-border);">
      <div class="card-title">安全验证与修改</div>

      <form @submit.prevent="handleChangePassword">
        <div class="form-group">
          <label class="form-label" for="currentPassword">当前登录密码</label>
          <input
            id="currentPassword"
            v-model="currentPassword"
            class="form-control"
            type="password"
            placeholder="输入当前登录密码"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="newPassword">设置新密码</label>
          <input
            id="newPassword"
            v-model="newPassword"
            class="form-control"
            type="password"
            placeholder="输入新密码 (6位以上)"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="confirmPassword">确认新密码</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            class="form-control"
            type="password"
            placeholder="再次输入新密码以进行确认"
            required
          />
        </div>

        <button
          type="submit"
          class="btn btn-primary-purple"
          :disabled="loading"
          style="margin-top: 15px; width: 100%; justify-content: center;"
        >
          {{ loading ? '正在提交...' : '确定修改密码' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.password-view {
  display: flex;
  flex-direction: column;
}
</style>
