import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types'
import { API_BASE_URL } from '../utils/api-config'

export const useAuthStore = defineStore('auth', () => {
  // Initialize from localStorage on startup
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(
    localStorage.getItem('user')
      ? JSON.parse(localStorage.getItem('user')!)
      : null
  )
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isInitialized = ref(true) // Always initialized from localStorage

  // Computed
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const tenantId = computed(() => user.value?.tenantId || 'client_simulation_a')

  // Login function - saves to localStorage
  const login = async (email: string, password: string) => {
    isLoading.value = true
    error.value = null

    try {
      console.log('🌐 Logging in with new JWT system...')

      const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
        // NO credentials: 'include' - we don't use cookies anymore!
      })

      console.log('📡 Response:', response.status)

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.message || 'Login failed')
      }

      const data = await response.json()
      console.log('✅ Login successful:', data)

      // Store token and user in memory
      token.value = data.token
      user.value = {
        id: data.user.id,
        email: data.user.email,
        name: data.user.email.split('@')[0],
        role: data.user.role,
        tenantId: 'pilotpros_client',
        createdAt: new Date().toISOString()
      }

      // Persist to localStorage
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(user.value))

      console.log('✅ Token saved to localStorage')

    } catch (err: any) {
      error.value = err.message || 'Login failed'
      console.error('❌ Login failed:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Logout - clears localStorage
  const logout = async () => {
    console.log('🚪 Logging out...')

    // Optional: Call logout endpoint (not really needed)
    try {
      const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
    } catch (err) {
      // Ignore errors - we're logging out anyway
    }

    // Clear memory
    token.value = null
    user.value = null
    error.value = null

    // Clear localStorage
    localStorage.removeItem('token')
    localStorage.removeItem('user')

    console.log('✅ Logged out - localStorage cleared')
  }

  // Initialize auth - verify token with backend
  const initializeAuth = async () => {
    // No token in localStorage - user not authenticated
    if (!token.value) {
      return false
    }

    // Token exists - verify it's still valid with backend
    try {
      console.log('🔐 Verifying token with backend...')
      const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
      const response = await fetch(`${API_BASE}/api/auth/verify`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })

      if (!response.ok) {
        // Token is invalid or expired - logout
        console.warn('⚠️ Token verification failed - logging out')
        await logout()
        return false
      }

      console.log('✅ Token verified successfully')
      return true

    } catch (err) {
      // Network error or backend unavailable - logout for security
      console.error('❌ Token verification error:', err)
      await logout()
      return false
    }
  }

  // Add Authorization header to all fetch requests
  const originalFetch = window.fetch
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    // If we have a token, add it to the headers
    if (token.value) {
      init = init || {}

      // CRITICAL FIX: Properly handle Headers object vs plain object
      // ofetch passes a Headers instance which doesn't spread correctly
      const headers = new Headers(init.headers || {})
      headers.set('Authorization', `Bearer ${token.value}`)
      init.headers = headers
    }
    return originalFetch(input, init)
  }

  return {
    // State
    user,
    token,
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
    resetAutoLogoutTimer: () => {}, // Not needed with JWT
    clearAutoLogoutTimer: () => {}, // Not needed with JWT
    ensureInitialized: async () => {
      await initializeAuth()
    }
  }
})