<template>
  <Dialog 
    v-model:visible="isVisible" 
    modal 
    :header="isEditing ? 'Modifica Configurazione Autenticazione' : 'Configurazione Autenticazione'"
    class="premium-modal w-full max-w-4xl"
    :dismissableMask="false"
    :closable="!isSaving"
  >
    <div class="space-y-6">
      <!-- Configuration Forms -->
      <!-- LDAP Configuration -->
      <div v-if="authConfig.method.includes('ldap')" class="premium-glass p-6 rounded-lg">
          <h4 class="text-lg font-semibold text-text mb-4 flex items-center">
            <Server class="h-5 w-5 mr-2 text-warning" />
            Configurazione LDAP
          </h4>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-text mb-2">Server LDAP</label>
              <InputText 
                v-model="authConfig.ldap.server"
                placeholder="ldap.example.com"
                class="w-full premium-input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text mb-2">Porta</label>
              <InputText 
                v-model="authConfig.ldap.port"
                placeholder="389"
                type="number"
                class="w-full premium-input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text mb-2">Base DN</label>
              <InputText 
                v-model="authConfig.ldap.baseDN"
                placeholder="DC=example,DC=com"
                class="w-full premium-input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text mb-2">User DN Template</label>
              <InputText 
                v-model="authConfig.ldap.userDN"
                placeholder="cn=%s,ou=users,dc=example,dc=com"
                class="w-full premium-input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text mb-2">Password Admin</label>
              <InputText 
                v-model="authConfig.ldap.password"
                type="password"
                placeholder="Password per test connessione"
                class="w-full premium-input"
              />
            </div>
            <div class="flex items-center">
              <input 
                id="useSSL" 
                v-model="authConfig.ldap.useSSL" 
                type="checkbox"
                class="premium-checkbox mr-2"
              />
              <label for="useSSL" class="text-sm font-medium text-text">Usa SSL/TLS</label>
            </div>
          </div>
        </div>

      <!-- MFA Configuration -->
      <div v-if="authConfig.method === 'ldap_mfa'" class="premium-glass p-6 rounded-lg">
          <h4 class="text-lg font-semibold text-text mb-4 flex items-center">
            <Shield class="h-5 w-5 mr-2 text-success" />
            Configurazione MFA
          </h4>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-text mb-2">Metodo MFA</label>
              <Dropdown
                v-model="authConfig.mfa.method"
                :options="mfaMethods"
                optionLabel="label"
                optionValue="value"
                placeholder="Seleziona metodo"
                class="w-full premium-dropdown"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text mb-2">Timeout (secondi)</label>
              <InputText 
                v-model="authConfig.mfa.timeout"
                placeholder="300"
                type="number"
                class="w-full premium-input"
              />
            </div>
          </div>
        </div>

      <!-- Current Status -->
      <div class="premium-glass p-4 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <h4 class="font-medium text-text">Stato Attuale</h4>
            <p class="text-sm text-text-muted">
              Metodo: <span class="font-medium">{{ getAuthMethodLabel(authConfig.method) }}</span>
            </p>
          </div>
          <Tag 
            :value="getAuthMethodLabel(authConfig.method)"
            :severity="getAuthMethodSeverity(authConfig.method)"
            class="premium-tag"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center">
        <Button
          @click="testConfiguration"
          :disabled="isTestingAuth"
          severity="info"
          outlined
          class="premium-button"
        >
          <template v-if="isTestingAuth">
            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
            Testando...
          </template>
          <template v-else>
            Test Connessione
          </template>
        </Button>
        <div></div>
        <div class="flex gap-2">
          <Button 
            @click="closeModal"
            :disabled="isSaving"
            severity="secondary" 
            outlined
            class="premium-button"
          >
            Annulla
          </Button>
          <Button 
            @click="saveConfiguration"
            :disabled="isSaving"
            class="premium-button"
          >
            <template v-if="isSaving">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
              Salvando...
            </template>
            <template v-else>
              Salva Configurazione
            </template>
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, watch, nextTick, computed } from 'vue'
import { Key, Server, Shield } from 'lucide-vue-next'
import { useToast } from 'vue-toastification'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import { API_BASE_URL } from '../../utils/api-config'

const props = defineProps({
  visible: Boolean,
  config: Object,
  isEditing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'saved'])
const toast = useToast()

// Computed property for visibility
const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// Reactive data
const isSaving = ref(false)
const isTestingAuth = ref(false)

const authConfig = reactive({
  method: 'local',
  ldap: {
    server: '',
    port: '389',
    baseDN: '',
    userDN: '',
    password: '',
    useSSL: false
  },
  mfa: {
    method: 'totp',
    timeout: 300,
    enabled: false
  }
})

const mfaMethods = ref([
  { label: 'TOTP (Google Authenticator)', value: 'totp' },
  { label: 'SMS', value: 'sms' },
  { label: 'Email', value: 'email' }
])

// Watch for config changes
watch(() => props.config, (newConfig) => {
  if (newConfig) {
    Object.assign(authConfig, newConfig)
  }
}, { immediate: true })

// Methods
const selectAuthMethod = async (method) => {
  console.log('🔵 Selecting auth method:', method)
  console.log('🔵 Current method before:', authConfig.method)
  
  authConfig.method = method
  
  console.log('🔵 Method after assignment:', authConfig.method)
  console.log('🔵 Should show LDAP form?:', authConfig.method !== 'local')
  console.log('🔵 Should show LDAP section?:', authConfig.method.includes('ldap'))
  
  // Reset MFA when switching methods
  if (method === 'ldap_mfa') {
    authConfig.mfa.enabled = true
  } else {
    authConfig.mfa.enabled = false
  }
  
  await nextTick()
  console.log('🔵 Auth config after nextTick:', authConfig.method)
}

const getAuthMethodLabel = (method) => {
  const labels = {
    local: 'Local',
    ldap: 'LDAP',
    ldap_mfa: 'LDAP + MFA'
  }
  return labels[method] || 'Sconosciuto'
}

const getAuthMethodSeverity = (method) => {
  const severities = {
    local: 'info',
    ldap: 'warning',
    ldap_mfa: 'success'
  }
  return severities[method] || 'info'
}

const testConfiguration = async () => {
  isTestingAuth.value = true
  
  try {
    const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
    const response = await fetch(`${API_BASE}/api/auth/test-config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('pilotpro_token')}`
      },
      body: JSON.stringify({
        method: authConfig.method,
        ldap: authConfig.ldap,
        mfa: authConfig.mfa
      })
    })

    const data = await response.json()

    if (data.success) {
      toast.success('Test configurazione completato con successo!')
    } else {
      toast.error(`Errore test: ${data.message}`)
    }
  } catch (error) {
    console.error('Errore test configurazione:', error)
    toast.error(`Errore durante il test: ${error.message}`)
  } finally {
    isTestingAuth.value = false
  }
}

const saveConfiguration = async () => {
  isSaving.value = true
  
  try {
    const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
    const response = await fetch(`${API_BASE}/api/auth/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('pilotpro_token')}`
      },
      body: JSON.stringify({
        method: authConfig.method,
        ldap: authConfig.ldap,
        mfa: authConfig.mfa
      })
    })

    const data = await response.json()

    if (data.success) {
      toast.success('Configurazione salvata con successo!')
      emit('saved', { ...authConfig })
      closeModal()
    } else {
      throw new Error(data.message || 'Errore nel salvataggio')
    }
  } catch (err) {
    console.error('Errore salvataggio configurazione:', err)
    toast.error(`Errore nel salvataggio: ${err.message}`)
  } finally {
    isSaving.value = false
  }
}

const closeModal = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.premium-input {
  @apply bg-surface border border-gray-600 rounded-lg px-3 py-2 text-text placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200;
}

.premium-dropdown {
  @apply bg-surface border border-gray-600 rounded-lg text-text focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200;
}

.premium-checkbox {
  @apply bg-surface border border-gray-600 rounded text-primary focus:ring-2 focus:ring-primary transition-all duration-200;
}

.premium-tag {
  @apply px-2 py-1 text-xs font-medium rounded-md;
}

.premium-modal :deep(.p-dialog) {
  @apply bg-surface border border-gray-600 shadow-2xl;
  backdrop-filter: blur(20px);
  border-radius: 1rem;
}

.premium-modal :deep(.p-dialog-header) {
  @apply bg-surface border-b border-gray-600 text-text px-6 py-4;
  backdrop-filter: blur(10px);
}

.premium-modal :deep(.p-dialog-content) {
  @apply bg-surface text-text px-6 py-4;
  backdrop-filter: blur(5px);
}

.premium-modal :deep(.p-dialog-footer) {
  @apply bg-surface border-t border-gray-600 px-6 py-4;
  backdrop-filter: blur(10px);
}
</style>