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

  // Auto-refresh interceptor: transparently refresh access token on 401
  let isRefreshing = false
  let refreshPromise: Promise<boolean> | null = null

  const refreshAccessToken = async (): Promise<boolean> => {
    // Prevent concurrent refresh attempts
    if (isRefreshing && refreshPromise) {
      return refreshPromise
    }

    isRefreshing = true
    refreshPromise = (async () => {
      try {
        console.log('🔄 Access token expired - attempting refresh...')
        const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
        const response = await originalFetch(`${API_BASE}/api/auth/refresh`, {
          method: 'POST',
          credentials: 'include' // Send refresh_token cookie
        })

        if (!response.ok) {
          // Refresh failed (403) - logout required
          console.warn('⚠️ Refresh token invalid or expired - logging out')
          await logout()
          return false
        }

        console.log('✅ Access token refreshed successfully')
        return true

      } catch (error) {
        console.error('❌ Token refresh error:', error)
        await logout()
        return false
      } finally {
        isRefreshing = false
        refreshPromise = null
      }
    })()

    return refreshPromise
  }

  // Add credentials: 'include' + auto-refresh on 401
  const originalFetch = window.fetch
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    init = init || {}

    // CRITICAL: Always send cookies for authenticated requests
    if (!init.credentials) {
      init.credentials = 'include'
    }

    // Make initial request
    let response = await originalFetch(input, init)

    // If 401 and not the refresh endpoint itself, try auto-refresh
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
    const isRefreshEndpoint = url.includes('/api/auth/refresh')
    const isLoginEndpoint = url.includes('/api/auth/login')

    if (response.status === 401 && !isRefreshEndpoint && !isLoginEndpoint) {
      console.log('🔒 401 Unauthorized - attempting auto-refresh...')

      const refreshSuccess = await refreshAccessToken()

      if (refreshSuccess) {
        // Retry original request with new access token
        console.log('🔄 Retrying original request with new token...')
        response = await originalFetch(input, init)
      } else {
        // Refresh failed - user logged out, return 401
        console.warn('⚠️ Auto-refresh failed - request aborted')
      }
    }

    return response
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