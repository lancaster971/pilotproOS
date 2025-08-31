import { ref, watch } from 'vue'
import { useUIStore } from '../stores/ui'

export interface ModalState {
  show: boolean
  isLoading: boolean
  error: string | null
}

export interface ModalConfig {
  closeOnEscape?: boolean
  closeOnClickOutside?: boolean
  showLoadingSpinner?: boolean
}

export function useModal(initialShow = false, config: ModalConfig = {}) {
  const uiStore = useUIStore()
  
  const show = ref(initialShow)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  
  const {
    closeOnEscape = true,
    closeOnClickOutside = true,
    showLoadingSpinner = true
  } = config

  const open = () => {
    show.value = true
    error.value = null
  }

  const close = () => {
    show.value = false
    error.value = null
  }

  const setLoading = (loading: boolean) => {
    isLoading.value = loading
  }

  const setError = (err: string | Error | null) => {
    if (err === null) {
      error.value = null
    } else if (typeof err === 'string') {
      error.value = err
    } else {
      error.value = err.message
    }
    isLoading.value = false
  }

  const showToast = (type: 'success' | 'error' | 'warning' | 'info', title: string, message?: string) => {
    uiStore.showToast(title, message || '', type)
  }

  const handleKeydown = (event: KeyboardEvent) => {
    if (closeOnEscape && event.key === 'Escape' && show.value) {
      close()
    }
  }

  const handleClickOutside = () => {
    if (closeOnClickOutside) {
      close()
    }
  }

  watch(show, (newShow) => {
    if (newShow && closeOnEscape) {
      document.addEventListener('keydown', handleKeydown)
    } else {
      document.removeEventListener('keydown', handleKeydown)
    }
  })

  return {
    // State
    show,
    isLoading,
    error,
    
    // Actions
    open,
    close,
    setLoading,
    setError,
    showToast,
    handleClickOutside,
    
    // Computed helpers
    hasError: () => error.value !== null,
    canSubmit: () => !isLoading.value && error.value === null
  }
}