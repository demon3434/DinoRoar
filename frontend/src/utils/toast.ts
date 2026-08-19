import { reactive } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastItem {
  id: number
  message: string
  type: ToastType
}

export const toastState = reactive<{ items: ToastItem[] }>({
  items: []
})

let nextId = 1

export function showToast(message: string, type: ToastType = 'info', duration = 3000) {
  const id = nextId++
  toastState.items.push({ id, message, type })

  setTimeout(() => {
    const idx = toastState.items.findIndex(t => t.id === id)
    if (idx !== -1) {
      toastState.items.splice(idx, 1)
    }
  }, duration)
}
