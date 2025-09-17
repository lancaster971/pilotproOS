import { ref } from 'vue'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
  timestamp: number
}

const notifications = ref<Notification[]>([])

export function useNotification() {
  const show = (type: Notification['type'], message: string) => {
    const notification: Notification = {
      id: `${Date.now()}-${Math.random()}`,
      type,
      message,
      timestamp: Date.now()
    }

    notifications.value.push(notification)

    // Auto-remove after 5 seconds
    setTimeout(() => {
      const index = notifications.value.findIndex(n => n.id === notification.id)
      if (index !== -1) {
        notifications.value.splice(index, 1)
      }
    }, 5000)

    // Also log to console for debugging
    console.log(`📢 Notification [${type.toUpperCase()}]: ${message}`)

    return notification.id
  }

  return {
    notifications,
    success: (msg: string) => show('success', msg),
    error: (msg: string) => show('error', msg),
    info: (msg: string) => show('info', msg),
    warning: (msg: string) => show('warning', msg)
  }
}