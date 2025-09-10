/**
 * Enhanced Authentication Store
 * 
 * Pinia store for LDAP + MFA authentication
 * Extends existing auth capabilities with enterprise features
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface EnhancedUser {
  id: string
  email: string
  role: string
  tenant_id?: string
  authMethod?: 'local' | 'ldap'
  mfaEnabled?: boolean
}

export interface AuthStatus {
  mfaEnabled: boolean
  ldapEnabled: boolean
  authMethod: 'local' | 'ldap'
}

export interface MFASetupData {
  secret: string
  qrCodeUrl: string
  backupCodes: string[]
}

export const useEnhancedAuthStore = defineStore('enhancedAuth', () => {
  // State
  const user = ref<EnhancedUser | null>(null)
  const token = ref<string | null>(localStorage.getItem('pilotpro_token'))
  const authStatus = ref<AuthStatus>({
    mfaEnabled: false,
    ldapEnabled: false,
    authMethod: 'local'
  })
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isMFAEnabled = computed(() => authStatus.value.mfaEnabled)
  const isLDAPAvailable = computed(() => authStatus.value.ldapEnabled)
  const currentAuthMethod = computed(() => authStatus.value.authMethod)

  // API Helper
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...(token.value && { 'Authorization': `Bearer ${token.value}` }),
      ...options.headers
    }

    const response = await fetch(`/api/auth/enhanced${endpoint}`, {
      ...options,
      headers
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Request failed')
    }

    return data
  }

  // Actions
  const login = async (email: string, password: string, method = 'auto') => {
    isLoading.value = true
    error.value = null

    try {
      const data = await apiCall('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password, method })
      })

      if (data.requiresMFA) {
        // Return MFA session for next step
        return {
          requiresMFA: true,
          mfaSession: data.mfaSession,
          user: data.user
        }
      } else {
        // Complete authentication
        user.value = data.user
        token.value = data.token
        localStorage.setItem('pilotpro_token', data.token)
        
        await loadAuthStatus()
        console.log('✅ Enhanced login successful')
        
        return { success: true }
      }
    } catch (err: any) {
      error.value = err.message || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const verifyMFA = async (mfaSession: string, mfaToken: string) => {
    isLoading.value = true
    error.value = null

    try {
      const data = await apiCall('/mfa/verify', {
        method: 'POST',
        body: JSON.stringify({ mfaSession, mfaToken })
      })

      // Complete authentication
      user.value = data.user
      token.value = data.token
      localStorage.setItem('pilotpro_token', data.token)
      
      await loadAuthStatus()
      console.log('✅ MFA verification successful')
      
      return { success: true }
    } catch (err: any) {
      error.value = err.message || 'MFA verification failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const setupMFA = async (): Promise<MFASetupData> => {
    try {
      const data = await apiCall('/mfa/setup', {
        method: 'POST'
      })

      console.log('✅ MFA setup data received')
      return {
        secret: data.secret,
        qrCodeUrl: data.qrCodeUrl,
        backupCodes: data.backupCodes
      }
    } catch (err: any) {
      error.value = err.message || 'MFA setup failed'
      throw err
    }
  }

  const verifyMFASetup = async (token: string): Promise<boolean> => {
    try {
      await apiCall('/mfa/verify-setup', {
        method: 'POST',
        body: JSON.stringify({ token })
      })

      // Update status
      authStatus.value.mfaEnabled = true
      if (user.value) {
        user.value.mfaEnabled = true
      }
      
      console.log('✅ MFA setup verified')
      return true
    } catch (err: any) {
      error.value = err.message || 'MFA verification failed'
      return false
    }
  }

  const disableMFA = async () => {
    try {
      await apiCall('/mfa/disable', {
        method: 'POST'
      })

      // Update status
      authStatus.value.mfaEnabled = false
      if (user.value) {
        user.value.mfaEnabled = false
      }
      
      console.log('✅ MFA disabled')
    } catch (err: any) {
      error.value = err.message || 'Failed to disable MFA'
      throw err
    }
  }

  const regenerateBackupCodes = async (): Promise<string[]> => {
    try {
      const data = await apiCall('/backup-codes', {
        method: 'POST'
      })

      console.log('✅ Backup codes regenerated')
      return data.backupCodes
    } catch (err: any) {
      error.value = err.message || 'Failed to regenerate backup codes'
      throw err
    }
  }

  const loadAuthStatus = async () => {
    try {
      const data = await apiCall('/status')
      
      authStatus.value = {
        mfaEnabled: data.mfaEnabled || false,
        ldapEnabled: data.ldapEnabled || false,
        authMethod: data.authMethod || 'local'
      }

      console.log('✅ Auth status loaded:', authStatus.value)
    } catch (err: any) {
      console.error('❌ Failed to load auth status:', err)
    }
  }

  const testLDAPConnection = async (config: any): Promise<boolean> => {
    try {
      const data = await apiCall('/ldap/test', {
        method: 'POST',
        body: JSON.stringify(config)
      })

      return data.success
    } catch (err: any) {
      error.value = err.message || 'LDAP test failed'
      throw err
    }
  }

  const saveLDAPConfig = async (config: any) => {
    try {
      const data = await apiCall('/ldap/config', {
        method: 'POST',
        body: JSON.stringify(config)
      })

      await loadAuthStatus() // Reload to get new LDAP status
      console.log('✅ LDAP config saved')
      return data.configId
    } catch (err: any) {
      error.value = err.message || 'Failed to save LDAP config'
      throw err
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    authStatus.value = {
      mfaEnabled: false,
      ldapEnabled: false,
      authMethod: 'local'
    }
    error.value = null
    localStorage.removeItem('pilotpro_token')
    console.log('✅ Enhanced logout successful')
  }

  const initializeAuth = async () => {
    const savedToken = localStorage.getItem('pilotpro_token')
    if (savedToken && savedToken !== 'null') {
      token.value = savedToken
      await loadAuthStatus()
      
      // Try to get user profile (would need regular auth endpoint)
      // This assumes the existing auth system can validate the token
      console.log('✅ Enhanced auth initialized from localStorage')
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    user,
    token,
    authStatus,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    isMFAEnabled,
    isLDAPAvailable,
    currentAuthMethod,
    
    // Actions
    login,
    verifyMFA,
    setupMFA,
    verifyMFASetup,
    disableMFA,
    regenerateBackupCodes,
    loadAuthStatus,
    testLDAPConnection,
    saveLDAPConfig,
    logout,
    initializeAuth,
    clearError
  }
})