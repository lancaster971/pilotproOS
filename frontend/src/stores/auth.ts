import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types'
import { authAPI } from '../services/api-client'

export const useAuthStore = defineStore('auth', () => {
  // State - same pattern as n8n stores
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('pilotpro_token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const autoLogoutTimer = ref<NodeJS.Timeout | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const tenantId = computed(() => user.value?.tenantId || 'client_simulation_a')

  // Actions - HttpOnly cookies + real API
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
        credentials: 'include' // Include HttpOnly cookies
      })

      console.log('📡 Response received:', response.status, response.statusText)
      
      const data = await response.json()
      console.log('📄 Response data:', data)

      if (!response.ok) {
        throw new Error(data.message || 'Login failed')
      }

      // HttpOnly cookies are set automatically by browser
      user.value = {
        id: data.user.id,
        email: data.user.email,
        name: data.user.email.split('@')[0], // Use email prefix as name
        role: data.user.role,
        tenantId: 'pilotpros_client',
        createdAt: new Date().toISOString(),
      }

      // No token in localStorage - it's in HttpOnly cookies
      token.value = 'authenticated' // Flag for UI state
      
      // Set auto-logout timer for 15 minutes (matching access token expiry)
      setAutoLogoutTimer()
      
      console.log('✅ Login successful with HttpOnly cookies:', user.value)
      
    } catch (err: any) {
      error.value = err.message || 'Login failed'
      console.error('❌ Login failed:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include' // Clear HttpOnly cookies
      })
    } catch (error) {
      console.error('❌ Logout API failed:', error)
    }

    // Clear client state
    user.value = null
    token.value = null
    localStorage.removeItem('pilotpro_token') // Legacy cleanup
    console.log('✅ Logout successful - HttpOnly cookies cleared')
  }

  const initializeAuth = async () => {
    // Clean up old localStorage token
    localStorage.removeItem('pilotpro_token')
    
    // Check if user is already authenticated via HttpOnly cookies
    try {
      const response = await fetch('/api/auth/profile', {
        credentials: 'include' // Send HttpOnly cookies
      })

      if (response.ok) {
        const data = await response.json()
        
        user.value = {
          id: data.user.id,
          email: data.user.email,
          name: data.user.email.split('@')[0],
          role: data.user.role,
          tenantId: 'pilotpros_client',
          createdAt: data.user.createdAt,
        }
        
        token.value = 'authenticated'
        setAutoLogoutTimer() // Set timer if already authenticated
        console.log('✅ Auth initialized from HttpOnly cookies:', user.value)
      } else {
        // Silent fail for 401 - user just not authenticated
        console.log('ℹ️ No existing authentication found (expected)')
      }
    } catch (error) {
      // Suppress network errors on auth init
      console.log('ℹ️ Auth initialization skipped (no connection)')
    }
  }

  // Auto-logout timer management
  const setAutoLogoutTimer = () => {
    clearAutoLogoutTimer()
    
    // Set timer for 14 minutes (1 minute before token expiry for safety)
    autoLogoutTimer.value = setTimeout(async () => {
      console.log('⏰ Auto-logout: Token expired')
      await logout()
      // Optional: Show notification to user
      error.value = 'Sessione scaduta. Effettua nuovamente il login.'
    }, 14 * 60 * 1000) // 14 minutes
  }

  const clearAutoLogoutTimer = () => {
    if (autoLogoutTimer.value) {
      clearTimeout(autoLogoutTimer.value)
      autoLogoutTimer.value = null
    }
  }

  // Reset timer on user activity
  const resetAutoLogoutTimer = () => {
    if (isAuthenticated.value) {
      setAutoLogoutTimer()
    }
  }

  return {
    // State
    user,
    token,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    tenantId,
    
    // Actions
    login,
    logout,
    initializeAuth,
    resetAutoLogoutTimer,
    clearAutoLogoutTimer,
  }
})