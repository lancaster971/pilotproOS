import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'
export type SidebarMode = 'expanded' | 'compact' | 'hidden'

export const useUIStore = defineStore('ui', () => {
  // State
  const sidebarMode = ref<SidebarMode>('expanded')
  const sidebarHovered = ref(false)
  const loading = ref(false)
  
  const toast = ref({
    show: false,
    title: '',
    message: '',
    type: 'success' as ToastType,
  })

  // Computed
  const sidebarOpen = computed(() => sidebarMode.value !== 'hidden')
  const sidebarExpanded = computed(() => 
    sidebarMode.value === 'expanded' || (sidebarMode.value === 'compact' && sidebarHovered.value)
  )
  const sidebarWidth = computed(() => {
    if (sidebarMode.value === 'hidden') return '0px'
    if (sidebarMode.value === 'expanded' || sidebarHovered.value) return '256px'
    return '64px' // compact mode
  })

  // Actions
  const toggleSidebar = () => {
    if (sidebarMode.value === 'hidden') {
      sidebarMode.value = getSavedSidebarMode() || 'expanded'
    } else {
      sidebarMode.value = 'hidden'
    }
  }

  const setSidebarMode = (mode: SidebarMode) => {
    sidebarMode.value = mode
    if (mode !== 'hidden') {
      localStorage.setItem('pilotpro-sidebar-mode', mode)
    }
  }

  const setSidebarHovered = (hovered: boolean) => {
    sidebarHovered.value = hovered
  }

  const getSavedSidebarMode = (): SidebarMode | null => {
    const saved = localStorage.getItem('pilotpro-sidebar-mode')
    return saved as SidebarMode || null
  }

  const initializeSidebar = () => {
    const saved = getSavedSidebarMode()
    if (saved) {
      sidebarMode.value = saved
    }
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
    sidebarMode,
    sidebarHovered,
    loading,
    toast,
    
    // Computed
    sidebarOpen,
    sidebarExpanded,
    sidebarWidth,
    
    // Actions
    toggleSidebar,
    setSidebarMode,
    setSidebarHovered,
    initializeSidebar,
    showToast,
    hideToast,
    setLoading,
  }
})