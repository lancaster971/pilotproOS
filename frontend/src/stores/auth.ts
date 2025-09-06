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

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const tenantId = computed(() => user.value?.tenantId || 'client_simulation_a')

  // Actions - same API pattern as n8n
  const login = async (email: string, password: string) => {
    isLoading.value = true
    error.value = null

    try {
      // Simulate authentication for demo
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const mockUser: User = {
        id: '1',
        email: email,
        name: 'Admin User',
        role: 'admin',
        tenantId: 'client_simulation_a',
        createdAt: new Date().toISOString(),
      }

      user.value = mockUser
      token.value = 'demo-token-' + Date.now()
      localStorage.setItem('pilotpro_token', token.value)
      
      console.log('✅ Login successful:', mockUser)
      
    } catch (err: any) {
      error.value = err.message || 'Login failed'
      console.error('❌ Login failed:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('pilotpro_token')
    console.log('✅ Logout successful')
  }

  const initializeAuth = () => {
    const savedToken = localStorage.getItem('pilotpro_token')
    if (savedToken) {
      token.value = savedToken
      // Mock user for demo
      user.value = {
        id: '1',
        email: 'admin@pilotpro.com',
        name: 'Admin User',
        role: 'admin',
        tenantId: 'client_simulation_a',
        createdAt: new Date().toISOString(),
      }
      console.log('✅ Auth initialized from localStorage')
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
  }
})