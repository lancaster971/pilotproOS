import { create } from 'zustand'
import { authAPI } from '../services/api'

interface User {
  id: string
  email: string
  role: 'admin' | 'tenant' | 'readonly'
  tenantId?: string
  permissions: string[]
  lastLoginAt: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,
  
  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await authAPI.login(email, password)
      const { token, user } = response.data
      
      localStorage.setItem('token', token)
      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error: any) {
      // Se l'API non è disponibile, usa login mock per development
      if (error.code === 'ERR_NETWORK' || error.response?.status === 404 || error.response?.status === 401) {
        // Mock login per development
        if (email === 'admin@pilotpro.local' && password === 'admin123') {
          const mockToken = 'dev-token-' + Date.now()
          const mockUser = {
            id: '1',
            email,
            role: 'admin' as const,
            tenantId: 'default_tenant',  // MANCAVA QUESTO CAZZO DI CAMPO!
            permissions: ['*'],
            lastLoginAt: new Date().toISOString(),
          }
          
          localStorage.setItem('token', mockToken)
          set({
            user: mockUser,
            token: mockToken,
            isAuthenticated: true,
            isLoading: false,
          })
        } else {
          set({
            error: 'Credenziali non valide',
            isLoading: false,
          })
          throw new Error('Invalid credentials')
        }
      } else {
        set({
          error: error.response?.data?.message || 'Login failed',
          isLoading: false,
        })
        throw error
      }
    }
  },
  
  logout: async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('token')
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      })
    }
  },
  
  checkAuth: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      set({ isAuthenticated: false, user: null })
      return
    }
    
    set({ isLoading: true })
    try {
      const response = await authAPI.profile()
      set({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      localStorage.removeItem('token')
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      })
    }
  },
  
  clearError: () => set({ error: null }),
}))