<template>
  <div class="bg-gray-900 rounded-2xl shadow-lg border border-gray-700 p-6 max-w-md w-full">
    <!-- Header -->
    <div class="mb-6">
      <h3 class="text-xl font-semibold text-white mb-2">
        {{ currentStep === 'mfa' ? 'Two-Factor Authentication' : 'Sign In' }}
      </h3>
      <p class="text-gray-300 text-sm">
        {{ currentStep === 'mfa' 
            ? 'Enter the code from your authenticator app' 
            : 'Access your business process automation platform' 
        }}
      </p>
    </div>

    <!-- Step 1: Credentials -->
    <form v-if="currentStep === 'credentials'" @submit.prevent="handleLogin" class="space-y-4">
      <!-- Email -->
      <div class="space-y-2">
        <label for="email" class="text-sm text-gray-300 font-medium">Email</label>
        <input
          id="email"
          v-model="credentials.email"
          type="text"
          required
          class="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-white rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none"
          placeholder="Enter your email"
        />
      </div>

      <!-- Password -->
      <div class="space-y-2">
        <label for="password" class="text-sm text-gray-300 font-medium">Password</label>
        <div class="relative">
          <input
            id="password"
            v-model="credentials.password"
            :type="showPassword ? 'text' : 'password'"
            required
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-white rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none pr-10"
            placeholder="Enter your password"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
          >
            <Icon :icon="showPassword ? 'lucide:eye-off' : 'lucide:eye'" class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- Authentication Method (if LDAP available) -->
      <div v-if="ldapAvailable" class="space-y-2">
        <label class="text-sm text-gray-300 font-medium">Authentication Method</label>
        <div class="flex space-x-4">
          <label class="flex items-center">
            <input 
              v-model="credentials.method" 
              type="radio" 
              value="auto" 
              class="text-green-500 focus:ring-green-400"
            />
            <span class="ml-2 text-sm text-gray-300">Automatic</span>
          </label>
          <label class="flex items-center">
            <input 
              v-model="credentials.method" 
              type="radio" 
              value="local" 
              class="text-green-500 focus:ring-green-400"
            />
            <span class="ml-2 text-sm text-gray-300">Local</span>
          </label>
          <label class="flex items-center">
            <input 
              v-model="credentials.method" 
              type="radio" 
              value="ldap" 
              class="text-green-500 focus:ring-green-400"
            />
            <span class="ml-2 text-sm text-gray-300">LDAP</span>
          </label>
        </div>
      </div>

      <!-- Login Button -->
      <button 
        type="submit"
        :disabled="isLoading"
        class="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center"
      >
        <Icon v-if="isLoading" icon="lucide:loader-2" class="h-4 w-4 animate-spin mr-2" />
        {{ isLoading ? 'Signing In...' : 'Sign In' }}
      </button>

      <!-- Error Message -->
      <div v-if="errorMessage" class="bg-red-900/20 border border-red-700 rounded-lg p-3">
        <div class="flex items-center">
          <Icon icon="lucide:alert-circle" class="h-4 w-4 text-red-400 mr-2" />
          <p class="text-red-300 text-sm">{{ errorMessage }}</p>
        </div>
      </div>
    </form>

    <!-- Step 2: MFA Verification -->
    <form v-if="currentStep === 'mfa'" @submit.prevent="handleMFAVerification" class="space-y-4">
      <!-- MFA Code Input -->
      <div class="space-y-2">
        <label for="mfaCode" class="text-sm text-gray-300 font-medium">
          Authentication Code
        </label>
        <input
          id="mfaCode"
          v-model="mfaCode"
          type="text"
          maxlength="8"
          required
          class="w-full px-4 py-3 bg-gray-800 border border-gray-700 text-white text-center text-lg tracking-widest rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none"
          placeholder="000000"
          @input="mfaCode = mfaCode.replace(/[^0-9A-Fa-f]/g, '').toUpperCase()"
        />
        <p class="text-xs text-gray-400">
          Enter 6-digit code from your authenticator app or 8-character backup code
        </p>
      </div>

      <!-- MFA Buttons -->
      <div class="flex space-x-3">
        <button 
          type="button"
          @click="backToLogin"
          class="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
        >
          Back
        </button>
        <button 
          type="submit"
          :disabled="mfaCode.length < 6 || isVerifyingMFA"
          class="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center"
        >
          <Icon v-if="isVerifyingMFA" icon="lucide:loader-2" class="h-4 w-4 animate-spin mr-2" />
          {{ isVerifyingMFA ? 'Verifying...' : 'Verify' }}
        </button>
      </div>

      <!-- MFA Error -->
      <div v-if="mfaError" class="bg-red-900/20 border border-red-700 rounded-lg p-3">
        <div class="flex items-center">
          <Icon icon="lucide:alert-circle" class="h-4 w-4 text-red-400 mr-2" />
          <p class="text-red-300 text-sm">{{ mfaError }}</p>
        </div>
      </div>
    </form>

    <!-- LDAP Status Indicator -->
    <div v-if="ldapAvailable" class="mt-4 flex items-center justify-center">
      <div class="flex items-center text-xs text-gray-400">
        <div class="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
        LDAP Authentication Available
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUIStore()

const currentStep = ref('credentials') // 'credentials', 'mfa'
const showPassword = ref(false)
const isLoading = ref(false)
const isVerifyingMFA = ref(false)
const errorMessage = ref('')
const mfaError = ref('')
const ldapAvailable = ref(false)

const credentials = ref({
  email: '',
  password: '',
  method: 'auto'
})

const mfaCode = ref('')
const mfaSession = ref('')
const pendingUser = ref(null)

const handleLogin = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      // NO credentials: 'include' - usiamo JWT in localStorage ora
      body: JSON.stringify(credentials.value)
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Login failed')
    }

    if (data.requiresMFA) {
      // MFA required - store session and show MFA step
      mfaSession.value = data.mfaSession
      pendingUser.value = data.user
      currentStep.value = 'mfa'
      console.log('✅ Login successful, MFA required')
    } else {
      // Complete authentication - Cookie already set by backend
      await completeAuthentication(data.user, null)
    }

  } catch (error) {
    console.error('❌ Login failed:', error)
    errorMessage.value = error.message || 'Login failed'
  } finally {
    isLoading.value = false
  }
}

const handleMFAVerification = async () => {
  isVerifyingMFA.value = true
  mfaError.value = ''

  try {
    const response = await fetch('/api/auth/enhanced/mfa/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        mfaSession: mfaSession.value,
        mfaToken: mfaCode.value
      })
    })

    const data = await response.json()

    if (!data.success) {
      throw new Error(data.message || 'MFA verification failed')
    }

    // Complete authentication
    await completeAuthentication(data.user, data.token)
    console.log('✅ MFA verification successful')

  } catch (error) {
    console.error('❌ MFA verification failed:', error)
    mfaError.value = error.message || 'Invalid code'
  } finally {
    isVerifyingMFA.value = false
  }
}

const completeAuthentication = async (user, token) => {
  // Update auth store
  authStore.user = user
  authStore.isAuthenticated = true
  
  // Token handled via HttpOnly cookie, not localStorage
  if (token) {
    authStore.token = token
    localStorage.setItem('pilotpro_token', token)
  }

  // Show success message
  uiStore.showToast('Success', `Welcome back, ${user.email}!`, 'success')

  // Redirect to dashboard
  router.push('/dashboard')
}

const backToLogin = () => {
  currentStep.value = 'credentials'
  mfaCode.value = ''
  mfaError.value = ''
  mfaSession.value = ''
  pendingUser.value = null
}

const checkLDAPAvailability = async () => {
  try {
    const response = await fetch('/api/auth/enhanced/status')
    if (response.ok) {
      const data = await response.json()
      ldapAvailable.value = data.ldapEnabled || false
    }
  } catch (error) {
    console.log('Could not check LDAP status')
  }
}

onMounted(() => {
  checkLDAPAvailability()
})
</script>