<template>
  <div class="min-h-screen">
    <div class="flex min-h-screen">
      <!-- Left Side - Integrations Gradient with Brand Texts -->
      <div class="hidden lg:flex lg:w-1/2 relative bg-black overflow-hidden">
        <!-- Dark gradient -->
        <div class="absolute inset-0 bg-gradient-to-br from-green-900/40 via-green-800/30 to-black/50"></div>
        <div class="absolute inset-0 bg-gradient-to-tr from-black/60 via-transparent to-green-900/40"></div>
        
        <div class="relative z-10 flex flex-col justify-center items-center text-center px-12 w-full">
          <div class="max-w-2xl">
            <!-- Logo PilotPro -->
            <div class="mb-12">
              <span class="text-6xl md:text-7xl font-light text-white">Pilot</span>
              <span class="text-6xl md:text-7xl font-light" style="color: #10b981;">Pro</span>
            </div>

            <h1 class="text-4xl sm:text-5xl md:text-6xl text-white mb-6 tracking-tight leading-tight" style="font-weight: 300;">
              {{ BRAND_TITLE }}
            </h1>
            <p class="text-lg md:text-xl text-gray-300 leading-relaxed mb-8" style="font-weight: 200;">
              {{ BRAND_DESCRIPTION }}
            </p>
            <p class="text-lg md:text-xl text-gray-300" style="font-weight: 200;">
              Benvenuto!
            </p>
          </div>
        </div>
      </div>

      <!-- Right Side - Black Background with Auth Form -->
      <div class="w-full lg:w-1/2 bg-black flex flex-col">
        <div class="flex-1 flex items-center justify-center px-8 py-12">
          <div class="w-full max-w-md">
            <div class="bg-gray-900 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-700 p-6 text-left relative">
              <div>
                <h3 class="text-lg md:text-xl text-white mb-6" style="font-weight: 300;">
                  {{ isSignUp ? SIGNUP_TITLE : LOGIN_TITLE }}
                </h3>
                <p v-if="isSignUp && SIGNUP_DESCRIPTION" class="text-base text-gray-300 leading-relaxed mb-6" style="font-weight: 200;">
                  {{ SIGNUP_DESCRIPTION }}
                </p>
                
                <!-- Enhanced Login Form DISABLED - using fixed auth system -->
                <!-- <EnhancedLoginForm /> -->
                
                <!-- Main Login Form -->
                <form @submit.prevent="handleSubmit" class="space-y-4">
                  <div class="space-y-2">
                    <label for="email" class="text-sm text-gray-300" style="font-weight: 300;">
                      Email
                    </label>
                    <input
                      id="email"
                      v-model="formData.email"
                      type="text"
                      placeholder="inserisci la tua email"
                      required
                      class="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-white placeholder-gray-500 rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none transition-colors"
                    />
                  </div>
                  
                  <div class="space-y-2">
                    <label for="password" class="text-sm text-gray-300" style="font-weight: 300;">
                      Password
                    </label>
                    <div class="relative">
                      <input
                        id="password"
                        v-model="formData.password"
                        :type="showPassword ? 'text' : 'password'"
                        :placeholder="isSignUp ? 'crea una password sicura' : 'inserisci la tua password'"
                        required
                        class="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-white placeholder-gray-500 rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none transition-colors pr-10"
                      />
                      <button
                        type="button"
                        @click="showPassword = !showPassword"
                        class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-gray-700 rounded-r-lg transition-colors"
                      >
                        <Icon v-if="!showPassword" icon="lucide:eye" class="h-4 w-4 text-gray-400" />
                        <Icon v-else icon="lucide:eye-off" class="h-4 w-4 text-gray-400" />
                      </button>
                    </div>
                  </div>

                  <!-- Error Message Display -->
                  <div v-if="localError" class="bg-red-900/50 border border-red-500/50 text-red-200 px-3 py-2 rounded-lg text-sm">
                    {{ localError }}
                  </div>
                  
                  <button 
                    type="submit" 
                    class="w-full bg-green-600 hover:bg-green-700 text-white rounded-lg shadow-lg py-2 px-4 transition-all duration-200 flex items-center justify-center gap-2"
                    :disabled="authStore.isLoading"
                    :class="{ 'opacity-50 cursor-not-allowed': authStore.isLoading }"
                  >
                    <Icon v-if="authStore.isLoading" icon="lucide:loader-2" class="h-4 w-4 animate-spin" />
                    <span>
                      {{ authStore.isLoading 
                        ? (isSignUp ? 'Creazione account...' : 'Accesso in corso...') 
                        : (isSignUp ? 'Crea Account' : 'Accedi') 
                      }}
                    </span>
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Back to Top Button -->
    <button 
      v-if="showBackToTop"
      @click="scrollToTop"
      class="fixed bottom-8 right-8 bg-green-600 hover:bg-green-700 text-white p-3 rounded-full shadow-lg transition-all duration-300 z-50"
    >
      <Icon icon="lucide:arrow-up" class="h-5 w-5" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from 'vue-toastification'

// Constants - same as new loginPage design
const LOGIN_TITLE = "Login on OS System"
const LOGIN_DESCRIPTION = ""
const SIGNUP_TITLE = "Crea un Account"
const SIGNUP_DESCRIPTION = "Registrati per iniziare a trasformare la tua azienda con PilotPro."
const BRAND_TITLE = "I primi Ai business Agent in Italia"
const BRAND_DESCRIPTION = "Trasformiamo il modo di lavorare delle aziende attraverso l'intelligenza artificiale."

// Stores - Pinia composition pattern like n8n
const authStore = useAuthStore()
const toast = useToast()
const router = useRouter()

// Local state
const isSignUp = ref(false)
const showPassword = ref(false)
const showBackToTop = ref(false)
const useEnhancedAuth = ref(true) // Enable enhanced auth by default

const formData = ref({
  email: '',
  password: '',
})

const localError = ref('')

// Methods
const toggleMode = () => {
  isSignUp.value = !isSignUp.value
  formData.value.email = ''
  formData.value.password = ''
}

const handleSubmit = async () => {
  console.log('🔍 LOGIN SUBMIT:', formData.value)
  localError.value = '' // Clear previous errors
  
  try {
    if (isSignUp.value) {
      // For signup, redirect to demo booking
      window.location.href = '/prenota-demo'
    } else {
      // Login with any credentials
      console.log('🔐 Calling authStore.login...')
      await authStore.login(formData.value.email, formData.value.password)
      router.push('/dashboard')
    }
  } catch (error: any) {
    console.error('❌ Login error:', error)
    localError.value = error.message || 'Credenziali non valide'
  }
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Lifecycle - Vue 3 composition API
onMounted(() => {
  // Handle back to top button
  const handleScroll = () => {
    showBackToTop.value = window.scrollY > 400
  }
  
  window.addEventListener('scroll', handleScroll)
  
  // Cleanup
  onUnmounted(() => {
    window.removeEventListener('scroll', handleScroll)
  })
})
</script>

<style scoped>
/* Component-specific styles */
.animate-float {
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}
</style>