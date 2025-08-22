import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export const useUIStore = defineStore('ui', () => {
  // State
  const sidebarOpen = ref(true)
  const loading = ref(false)
  
  const toast = ref({
    show: false,
    title: '',
    message: '',
    type: 'success' as ToastType,
  })

  // Actions
  const toggleSidebar = () => {
    sidebarOpen.value = !sidebarOpen.value
  }

  const showToast = (title: string, message: string, type: ToastType = 'success') => {
    toast.value = {
      show: true,
      title,
      message,
      type,
    }

    // Auto-hide after 4 seconds
    setTimeout(() => {
      toast.value.show = false
    }, 4000)
  }

  const hideToast = () => {
    toast.value.show = false
  }

  const setLoading = (value: boolean) => {
    loading.value = value
  }

  return {
    // State
    sidebarOpen,
    loading,
    toast,
    
    // Actions
    toggleSidebar,
    showToast,
    hideToast,
    setLoading,
  }
})