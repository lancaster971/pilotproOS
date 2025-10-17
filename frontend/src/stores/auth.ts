import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types'
import { API_BASE_URL } from '../utils/api-config'

export const useAuthStore = defineStore('auth', () => {
  // State (HttpOnly cookie, no token in localStorage)
  const user = ref<User | null>(
    localStorage.getItem('user')
      ? JSON.parse(localStorage.getItem('user')!)
      : null
  )
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isInitialized = ref(true)

  // Computed
  const isAuthenticated = computed(() => !!user.value)
  const tenantId = computed(() => user.value?.tenantId || 'client_simulation_a')

  // Login function - uses HttpOnly cookies
  const login = async (email: string, password: string) => {
    isLoading.value = true
    error.value = null

    try {
      console.log('🔐 Logging in with HttpOnly cookies...')

      const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // CRITICAL: Send/receive HttpOnly cookies
        body: JSON.stringify({ email, password })
      })

      console.log('📡 Response:', response.status)

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.message || 'Login failed')
      }

      const data = await response.json()
      console.log('✅ Login successful:', data)

      // Store user info in localStorage (NOT sensitive)
      user.value = {
        id: data.user.id,
        email: data.user.email,
        name: data.user.email.split('@')[0],
        role: data.user.role,
        tenantId: 'pilotpros_client',
        createdAt: new Date().toISOString()
      }

      localStorage.setItem('user', JSON.stringify(user.value))

      console.log('✅ User saved to localStorage (token in HttpOnly cookie)')

    } catch (err: any) {
      error.value = err.message || 'Login failed'
      console.error('❌ Login failed:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Logout - clears HttpOnly cookie
  const logout = async () => {
    console.log('🚪 Logging out...')

    // Call logout endpoint to clear HttpOnly cookie
    try {
      const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include' // Send HttpOnly cookie
      })
    } catch (err) {
      console.error('Logout error:', err)
      // Continue logout even on error
    }

    // Clear memory
    user.value = null
    error.value = null

    // Clear localStorage (user info only, no token)
    localStorage.removeItem('user')

    console.log('✅ Logged out - HttpOnly cookie cleared')
  }

  // Initialize auth - verify HttpOnly cookie with backend
  const initializeAuth = async () => {
    // No user in localStorage - not authenticated
    if (!user.value) {
      return false
    }

    // User exists - verify HttpOnly cookie is still valid
    try {
      console.log('🔐 Verifying HttpOnly cookie with backend...')
      const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
      const response = await fetch(`${API_BASE}/api/auth/verify`, {
        method: 'GET',
        credentials: 'include' // Send HttpOnly cookie
      })

      if (!response.ok) {
        // Cookie is invalid or expired - logout
        console.warn('⚠️ Cookie verification failed - logging out')
        await logout()
        return false
      }

      console.log('✅ Cookie verified successfully')
      return true

    } catch (err) {
      // Network error or backend unavailable - logout for security
      console.error('❌ Cookie verification error:', err)
      await logout()
      return false
    }
  }

  // Add credentials: 'include' to all fetch requests (for HttpOnly cookies)
  const originalFetch = window.fetch
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    init = init || {}

    // CRITICAL: Always send cookies for authenticated requests
    if (!init.credentials) {
      init.credentials = 'include'
    }

    return originalFetch(input, init)
  }

  return {
    // State
    user,
    isLoading,
    error,
    isInitialized,

    // Computed
    isAuthenticated,
    tenantId,

    // Actions
    login,
    logout,
    initializeAuth,

    // Legacy compatibility
    resetAutoLogoutTimer: () => {}, // Not needed with HttpOnly cookies
    clearAutoLogoutTimer: () => {}, // Not needed with HttpOnly cookies
    ensureInitialized: async () => {
      await initializeAuth()
    }
  }
})