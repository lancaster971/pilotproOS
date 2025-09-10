<template>
  <div v-if="isVisible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-gray-900 rounded-2xl shadow-xl max-w-md w-full mx-4 border border-gray-700">
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-semibold text-white">
            {{ currentStep === 'setup' ? 'Setup Two-Factor Authentication' : 'Verify Setup' }}
          </h3>
          <button 
            @click="closeModal"
            class="text-gray-400 hover:text-white transition-colors"
          >
            <Icon icon="lucide:x" class="h-5 w-5" />
          </button>
        </div>

        <!-- Step 1: Setup -->
        <div v-if="currentStep === 'setup'" class="space-y-6">
          <!-- QR Code -->
          <div class="text-center">
            <div class="bg-white p-4 rounded-lg inline-block mb-4">
              <img 
                v-if="setupData?.qrCodeUrl"
                :src="setupData.qrCodeUrl"
                alt="QR Code for MFA Setup"
                class="w-48 h-48"
              />
              <div v-else class="w-48 h-48 bg-gray-100 flex items-center justify-center">
                <Icon icon="lucide:loader-2" class="h-8 w-8 animate-spin text-gray-400" />
              </div>
            </div>
            <p class="text-gray-300 text-sm">
              Scan this QR code with your authenticator app
            </p>
          </div>

          <!-- Instructions -->
          <div class="bg-gray-800 rounded-lg p-4">
            <h4 class="text-white font-medium mb-2">Setup Instructions:</h4>
            <ol class="text-gray-300 text-sm space-y-1 list-decimal list-inside">
              <li>Download an authenticator app (Google Authenticator, Microsoft Authenticator, Authy)</li>
              <li>Scan the QR code above with your app</li>
              <li>Enter the 6-digit code from your app to verify setup</li>
            </ol>
          </div>

          <!-- Manual Entry -->
          <div class="bg-gray-800 rounded-lg p-4">
            <p class="text-gray-300 text-sm mb-2">Can't scan? Enter this code manually:</p>
            <div class="bg-gray-900 rounded p-2 font-mono text-sm text-green-400 break-all">
              {{ setupData?.secret }}
            </div>
          </div>

          <!-- Next Button -->
          <button 
            @click="currentStep = 'verify'"
            :disabled="!setupData"
            class="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
          >
            Continue to Verification
          </button>
        </div>

        <!-- Step 2: Verify -->
        <div v-if="currentStep === 'verify'" class="space-y-6">
          <div class="text-center">
            <Icon icon="lucide:shield-check" class="h-12 w-12 text-green-400 mx-auto mb-4" />
            <p class="text-gray-300">
              Enter the 6-digit code from your authenticator app to complete setup:
            </p>
          </div>

          <!-- Verification Code Input -->
          <div class="space-y-2">
            <label class="text-sm text-gray-300 font-medium">Verification Code</label>
            <input
              v-model="verificationCode"
              type="text"
              maxlength="6"
              placeholder="000000"
              class="w-full px-4 py-3 bg-gray-800 border border-gray-700 text-white text-center text-lg tracking-widest rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none"
              @input="verificationCode = verificationCode.replace(/[^0-9]/g, '')"
            />
          </div>

          <!-- Action Buttons -->
          <div class="flex space-x-3">
            <button 
              @click="currentStep = 'setup'"
              class="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              Back
            </button>
            <button 
              @click="verifySetup"
              :disabled="verificationCode.length !== 6 || isVerifying"
              class="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Icon v-if="isVerifying" icon="lucide:loader-2" class="h-4 w-4 animate-spin mr-2" />
              {{ isVerifying ? 'Verifying...' : 'Enable MFA' }}
            </button>
          </div>
        </div>

        <!-- Backup Codes -->
        <div v-if="currentStep === 'complete'" class="space-y-6">
          <div class="text-center">
            <Icon icon="lucide:check-circle" class="h-12 w-12 text-green-400 mx-auto mb-4" />
            <h4 class="text-white font-semibold mb-2">MFA Enabled Successfully!</h4>
            <p class="text-gray-300 text-sm">
              Save these backup codes in a secure location. You can use them to access your account if you lose your authenticator device.
            </p>
          </div>

          <!-- Backup Codes Display -->
          <div class="bg-gray-800 rounded-lg p-4">
            <h5 class="text-white font-medium mb-3">Backup Codes</h5>
            <div class="grid grid-cols-2 gap-2">
              <div 
                v-for="code in setupData?.backupCodes" 
                :key="code"
                class="bg-gray-900 rounded p-2 font-mono text-sm text-center text-green-400"
              >
                {{ code }}
              </div>
            </div>
          </div>

          <!-- Warning -->
          <div class="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
            <div class="flex items-start">
              <Icon icon="lucide:alert-triangle" class="h-5 w-5 text-yellow-400 mr-3 mt-0.5" />
              <div>
                <p class="text-yellow-300 font-medium">Important:</p>
                <p class="text-yellow-200 text-sm">
                  Each backup code can only be used once. Store them securely and don't share them with anyone.
                </p>
              </div>
            </div>
          </div>

          <!-- Complete Button -->
          <button 
            @click="completeMFASetup"
            class="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            I've Saved My Backup Codes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'completed'])

const authStore = useAuthStore()
const uiStore = useUIStore()

const currentStep = ref('setup') // 'setup', 'verify', 'complete'
const setupData = ref(null)
const verificationCode = ref('')
const isVerifying = ref(false)

const closeModal = () => {
  currentStep.value = 'setup'
  verificationCode.value = ''
  setupData.value = null
  emit('close')
}

const setupMFA = async () => {
  try {
    const response = await fetch('/api/auth/enhanced/mfa/setup', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('MFA setup failed')
    }

    const data = await response.json()
    setupData.value = data
    console.log('✅ MFA setup data received')
  } catch (error) {
    console.error('❌ MFA setup failed:', error)
    uiStore.showToast('Error', 'Failed to setup MFA', 'error')
  }
}

const verifySetup = async () => {
  isVerifying.value = true
  try {
    const response = await fetch('/api/auth/enhanced/mfa/verify-setup', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token: verificationCode.value
      })
    })

    if (!response.ok) {
      throw new Error('Invalid verification code')
    }

    currentStep.value = 'complete'
    uiStore.showToast('Success', 'MFA enabled successfully!', 'success')
    console.log('✅ MFA verification successful')
  } catch (error) {
    console.error('❌ MFA verification failed:', error)
    uiStore.showToast('Error', 'Invalid verification code', 'error')
  } finally {
    isVerifying.value = false
  }
}

const completeMFASetup = () => {
  emit('completed')
  closeModal()
}

onMounted(() => {
  if (props.isVisible) {
    setupMFA()
  }
})

// Watch for visibility changes
watch(() => props.isVisible, (newVal) => {
  if (newVal) {
    setupMFA()
  }
})
</script>