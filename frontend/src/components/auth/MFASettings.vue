<template>
  <div class="bg-gray-900 rounded-xl border border-gray-700 p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-white">Two-Factor Authentication</h3>
        <p class="text-gray-400 text-sm mt-1">
          Add an extra layer of security to your account
        </p>
      </div>
      <div class="flex items-center">
        <div :class="[
          'w-3 h-3 rounded-full mr-2',
          authStatus.mfaEnabled ? 'bg-green-400' : 'bg-gray-500'
        ]"></div>
        <span :class="[
          'text-sm font-medium',
          authStatus.mfaEnabled ? 'text-green-400' : 'text-gray-400'
        ]">
          {{ authStatus.mfaEnabled ? 'Enabled' : 'Disabled' }}
        </span>
      </div>
    </div>

    <!-- MFA Status -->
    <div v-if="!authStatus.mfaEnabled" class="mb-6">
      <div class="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
        <div class="flex items-start">
          <Icon icon="lucide:shield-alert" class="h-5 w-5 text-yellow-400 mr-3 mt-0.5" />
          <div>
            <p class="text-yellow-300 font-medium">MFA Not Enabled</p>
            <p class="text-yellow-200 text-sm mt-1">
              Your account is not protected by two-factor authentication. We strongly recommend enabling MFA to secure your account.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Enabled State -->
    <div v-if="authStatus.mfaEnabled" class="space-y-4">
      <!-- Status Info -->
      <div class="bg-green-900/20 border border-green-700 rounded-lg p-4">
        <div class="flex items-center">
          <Icon icon="lucide:shield-check" class="h-5 w-5 text-green-400 mr-3" />
          <div>
            <p class="text-green-300 font-medium">MFA is Active</p>
            <p class="text-green-200 text-sm">
              Your account is protected with two-factor authentication.
            </p>
          </div>
        </div>
      </div>

      <!-- Management Options -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Regenerate Backup Codes -->
        <button
          @click="regenerateBackupCodes"
          :disabled="isRegenerating"
          class="flex items-center justify-center p-4 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-600 transition-colors disabled:opacity-50"
        >
          <Icon icon="lucide:refresh-cw" :class="[
            'h-5 w-5 mr-3',
            isRegenerating ? 'animate-spin' : '',
            'text-blue-400'
          ]" />
          <div class="text-left">
            <p class="text-white font-medium">Backup Codes</p>
            <p class="text-gray-400 text-sm">Generate new codes</p>
          </div>
        </button>

        <!-- Disable MFA -->
        <button
          @click="showDisableConfirm = true"
          class="flex items-center justify-center p-4 bg-gray-800 hover:bg-red-800/50 rounded-lg border border-gray-600 hover:border-red-600 transition-colors"
        >
          <Icon icon="lucide:shield-x" class="h-5 w-5 mr-3 text-red-400" />
          <div class="text-left">
            <p class="text-white font-medium">Disable MFA</p>
            <p class="text-gray-400 text-sm">Turn off protection</p>
          </div>
        </button>
      </div>
    </div>

    <!-- Disabled State -->
    <div v-else>
      <button
        @click="showMFASetup = true"
        class="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center"
      >
        <Icon icon="lucide:shield-plus" class="h-5 w-5 mr-2" />
        Enable Two-Factor Authentication
      </button>
    </div>

    <!-- Authentication Method Info -->
    <div class="mt-6 pt-6 border-t border-gray-700">
      <h4 class="text-white font-medium mb-3">Authentication Status</h4>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div class="flex justify-between">
          <span class="text-gray-400">Method:</span>
          <span :class="[
            'font-medium',
            authStatus.authMethod === 'ldap' ? 'text-blue-400' : 'text-green-400'
          ]">
            {{ authStatus.authMethod.toUpperCase() }}
          </span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-400">LDAP Available:</span>
          <span :class="[
            'font-medium',
            authStatus.ldapEnabled ? 'text-green-400' : 'text-gray-400'
          ]">
            {{ authStatus.ldapEnabled ? 'Yes' : 'No' }}
          </span>
        </div>
      </div>
    </div>

    <!-- MFA Setup Modal -->
    <MFASetupModal
      :is-visible="showMFASetup"
      @close="showMFASetup = false"
      @completed="handleMFASetupCompleted"
    />

    <!-- Disable Confirmation Modal -->
    <div v-if="showDisableConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-gray-900 rounded-2xl shadow-xl max-w-md w-full mx-4 border border-gray-700">
        <div class="p-6">
          <div class="flex items-center mb-4">
            <Icon icon="lucide:alert-triangle" class="h-6 w-6 text-red-400 mr-3" />
            <h3 class="text-lg font-semibold text-white">Disable MFA</h3>
          </div>
          
          <p class="text-gray-300 mb-6">
            Are you sure you want to disable two-factor authentication? This will make your account less secure.
          </p>
          
          <div class="flex space-x-3">
            <button 
              @click="showDisableConfirm = false"
              class="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button 
              @click="disableMFA"
              :disabled="isDisabling"
              class="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Icon v-if="isDisabling" icon="lucide:loader-2" class="h-4 w-4 animate-spin mr-2" />
              {{ isDisabling ? 'Disabling...' : 'Disable MFA' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Backup Codes Modal -->
    <div v-if="showBackupCodes" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-gray-900 rounded-2xl shadow-xl max-w-md w-full mx-4 border border-gray-700">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">New Backup Codes</h3>
            <button 
              @click="showBackupCodes = false"
              class="text-gray-400 hover:text-white"
            >
              <Icon icon="lucide:x" class="h-5 w-5" />
            </button>
          </div>
          
          <p class="text-gray-300 mb-4 text-sm">
            Save these backup codes in a secure location. Each code can only be used once.
          </p>
          
          <div class="bg-gray-800 rounded-lg p-4 mb-4">
            <div class="grid grid-cols-2 gap-2">
              <div 
                v-for="code in newBackupCodes" 
                :key="code"
                class="bg-gray-900 rounded p-2 font-mono text-sm text-center text-green-400"
              >
                {{ code }}
              </div>
            </div>
          </div>
          
          <button 
            @click="showBackupCodes = false"
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
import { ref, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import MFASetupModal from './MFASetupModal.vue'

const authStore = useAuthStore()
const uiStore = useUIStore()

const authStatus = ref({
  mfaEnabled: false,
  ldapEnabled: false,
  authMethod: 'local'
})

const showMFASetup = ref(false)
const showDisableConfirm = ref(false)
const showBackupCodes = ref(false)
const isRegenerating = ref(false)
const isDisabling = ref(false)
const newBackupCodes = ref([])

const loadAuthStatus = async () => {
  try {
    const response = await fetch('/api/auth/enhanced/status', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      authStatus.value = {
        mfaEnabled: data.mfaEnabled || false,
        ldapEnabled: data.ldapEnabled || false,
        authMethod: data.authMethod || 'local'
      }
    }
  } catch (error) {
    console.error('❌ Failed to load auth status:', error)
  }
}

const handleMFASetupCompleted = () => {
  authStatus.value.mfaEnabled = true
  uiStore.showToast('Success', 'MFA has been enabled successfully!', 'success')
}

const regenerateBackupCodes = async () => {
  isRegenerating.value = true
  try {
    const response = await fetch('/api/auth/enhanced/backup-codes', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to regenerate backup codes')
    }

    const data = await response.json()
    newBackupCodes.value = data.backupCodes
    showBackupCodes.value = true
    
    uiStore.showToast('Success', 'New backup codes generated', 'success')
  } catch (error) {
    console.error('❌ Failed to regenerate backup codes:', error)
    uiStore.showToast('Error', 'Failed to generate backup codes', 'error')
  } finally {
    isRegenerating.value = false
  }
}

const disableMFA = async () => {
  isDisabling.value = true
  try {
    const response = await fetch('/api/auth/enhanced/mfa/disable', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to disable MFA')
    }

    authStatus.value.mfaEnabled = false
    showDisableConfirm.value = false
    
    uiStore.showToast('Success', 'MFA has been disabled', 'success')
  } catch (error) {
    console.error('❌ Failed to disable MFA:', error)
    uiStore.showToast('Error', 'Failed to disable MFA', 'error')
  } finally {
    isDisabling.value = false
  }
}

onMounted(() => {
  loadAuthStatus()
})
</script>