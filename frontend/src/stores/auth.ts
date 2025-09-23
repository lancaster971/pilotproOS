import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isInitialized = ref(false)

  const tokenRefreshTimer = ref<ReturnType<typeof setTimeout> | null>(null)
  const inactivityTimer = ref<ReturnType<typeof setTimeout> | null>(null)
  let initializationPromise: Promise<boolean> | null = null

  const ACCESS_TOKEN_REFRESH_INTERVAL_MS = 13 * 60 * 1000
  const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000

  const isAuthenticated = computed(() => !!user.value)
  const tenantId = computed(() => user.value?.tenantId || 'client_simulation_a')

  const clearTokenRefreshTimer = () => {
    if (tokenRefreshTimer.value) {
      clearTimeout(tokenRefreshTimer.value)
      tokenRefreshTimer.value = null
    }
  }

  const clearInactivityTimer = () => {
    if (inactivityTimer.value) {
      clearTimeout(inactivityTimer.value)
      inactivityTimer.value = null
    }
  }

  const clearAutoLogoutTimer = () => {
    clearTokenRefreshTimer()
    clearInactivityTimer()
  }

  const scheduleTokenRefresh = () => {
    clearTokenRefreshTimer()

    tokenRefreshTimer.value = setTimeout(async () => {
      console.log('🔄 Auto-refresh: Refreshing token before expiry...')

      try {
        const response = await fetch('/api/auth/refresh', {
          method: 'POST',
          credentials: 'include'
        })

        if (response.ok) {
          console.log('✅ Token refreshed successfully!')
          scheduleTokenRefresh()
        } else {
          console.log('❌ Token refresh failed, logging out')
          await logout()
          error.value = 'Sessione scaduta. Effettua nuovamente il login.'
        }
      } catch (err) {
        console.error('❌ Error refreshing token:', err)
        scheduleTokenRefresh()
      }
    }, ACCESS_TOKEN_REFRESH_INTERVAL_MS)
  }

  const scheduleInactivityLogout = () => {
    clearInactivityTimer()

    inactivityTimer.value = setTimeout(async () => {
      console.log('⏳ Session expired due to inactivity, logging out...')
      await logout()
      error.value = 'Sessione scaduta per inattività.'
    }, INACTIVITY_TIMEOUT_MS)
  }

  const setAutoLogoutTimer = () => {
    scheduleTokenRefresh()
    scheduleInactivityLogout()
  }

  const markInitialized = () => {
    if (!isInitialized.value) {
      isInitialized.value = true
    }
  }

  const handleAuthSuccess = (data: { id: string; email: string; role: string; createdAt?: string }) => {
    user.value = {
      id: data.id,
      email: data.email,
      name: data.email.split('@')[0],
      role: data.role,
      tenantId: 'pilotpros_client',
      createdAt: data.createdAt || new Date().toISOString(),
    }

    token.value = 'authenticated'
    setAutoLogoutTimer()
  }

  const login = async (email: string, password: string) => {
    isLoading.value = true
    error.value = null

    try {
      console.log('🌐 Making fetch to /api/auth/login...')

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
        credentials: 'include'
      })

      console.log('📡 Response received:', response.status, response.statusText)

      const data = await response.json()
      console.log('📄 Response data:', data)

      if (!response.ok) {
        throw new Error(data.message || 'Login failed')
      }

      // Store JWT token if present in response
      if (data.token) {
        localStorage.setItem('jwt_token', data.token)
        token.value = data.token
        console.log('🔐 JWT token stored for API authentication')
      }

      handleAuthSuccess({
        id: data.user.id,
        email: data.user.email,
        role: data.user.role
      })

      markInitialized()

      console.log('✅ Login successful with JWT token:', user.value)
    } catch (err: any) {
      error.value = err.message || 'Login failed'
      console.error('❌ Login failed:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    console.log('🚪 Logout initiated...')

    clearAutoLogoutTimer()

    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      })
      console.log('✅ Server logout successful')
    } catch (err) {
      console.error('❌ Logout API failed (continuing anyway):', err)
    }

    // Clear JWT token from localStorage
    localStorage.removeItem('jwt_token')

    user.value = null
    token.value = null
    error.value = null
    isInitialized.value = false
    initializationPromise = null

    console.log('✅ Logout completed - all state cleared')
  }

  const initializeAuth = async () => {
    if (isInitialized.value && !initializationPromise) {
      return !!user.value
    }

    if (initializationPromise) {
      return initializationPromise
    }

    console.log('🔄 Initializing auth...')

    // Check for JWT token in localStorage first
    const storedToken = localStorage.getItem('jwt_token')
    if (storedToken) {
      token.value = storedToken
      console.log('🔐 JWT token found in localStorage')
    }

    initializationPromise = (async () => {
      try {
        const headers: HeadersInit = {
          'Content-Type': 'application/json'
        }

        // Add JWT token if available
        if (token.value) {
          headers['Authorization'] = `Bearer ${token.value}`
        }

        const response = await fetch('/api/auth/profile', {
          method: 'GET',
          credentials: 'include',
          headers
        })

        console.log('📡 Profile response status:', response.status)

        if (response.ok) {
          const data = await response.json()
          console.log('✅ Profile data received:', data)

          handleAuthSuccess({
            id: data.user.id,
            email: data.user.email,
            role: data.user.role,
            createdAt: data.user.createdAt
          })

          console.log('✅ Auth initialized from HttpOnly cookies:', user.value)
          return true
        }

        if (response.status !== 401) {
          const errorText = await response.text()
          console.log('❌ Auth check failed:', response.status, errorText)
        }

        return false
      } catch (err) {
        console.error('❌ Auth initialization error:', err)
        return false
      } finally {
        markInitialized()
        initializationPromise = null
      }
    })()

    return initializationPromise
  }

  const resetAutoLogoutTimer = () => {
    if (isAuthenticated.value) {
      scheduleInactivityLogout()
    }
  }

  return {
    user,
    token,
    isLoading,
    error,
    isInitialized,
    isAuthenticated,
    tenantId,
    login,
    logout,
    initializeAuth,
    resetAutoLogoutTimer,
    clearAutoLogoutTimer,
    ensureInitialized: async () => {
      if (!isInitialized.value) {
        await initializeAuth()
      }
    },
  }
})
