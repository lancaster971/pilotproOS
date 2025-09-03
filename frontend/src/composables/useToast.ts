import { ref, reactive } from 'vue'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  actions?: Array<{
    label: string
    action: () => void
  }>
}

interface ToastState {
  toasts: Toast[]
}

const state = reactive<ToastState>({
  toasts: []
})

let toastCounter = 0

export const useToast = () => {
  const show = (toast: Omit<Toast, 'id'>) => {
    const id = `toast-${++toastCounter}`
    const newToast: Toast = {
      id,
      duration: 5000,
      ...toast
    }
    
    state.toasts.push(newToast)
    
    // Auto remove after duration
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        remove(id)
      }, newToast.duration)
    }
    
    return id
  }
  
  const remove = (id: string) => {
    const index = state.toasts.findIndex(toast => toast.id === id)
    if (index > -1) {
      state.toasts.splice(index, 1)
    }
  }
  
  const clear = () => {
    state.toasts.splice(0)
  }
  
  const success = (title: string, message?: string) => {
    return show({ type: 'success', title, message })
  }
  
  const error = (title: string, message?: string) => {
    return show({ type: 'error', title, message, duration: 8000 })
  }
  
  const warning = (title: string, message?: string) => {
    return show({ type: 'warning', title, message })
  }
  
  const info = (title: string, message?: string) => {
    return show({ type: 'info', title, message })
  }
  
  return {
    toasts: state.toasts,
    show,
    remove,
    clear,
    success,
    error,
    warning,
    info
  }
}