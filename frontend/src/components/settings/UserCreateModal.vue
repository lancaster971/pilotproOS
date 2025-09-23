<template>
  <Dialog 
    :visible="true" 
    @update:visible="$emit('close')"
    modal 
    :closable="false"
    :dismissableMask="true"
    class="premium-modal"
    :style="{ width: '28rem' }"
    :ptOptions="{ mergeProps: false }"
    :pt="{
      mask: { 
        style: 'animation: modalFadeIn 0.15s ease-out !important;'
      },
      root: { 
        style: 'animation: modalSlideIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) !important;'
      }
    }"
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <h3 class="text-lg font-semibold text-text">Nuovo Utente</h3>
        <Button
          @click="$emit('close')"
          severity="secondary"
          text
          rounded
          size="small"
        >
          <X class="h-4 w-4" />
        </Button>
      </div>
    </template>

    <form @submit.prevent="createUser" class="space-y-4">
      <!-- Email -->
      <div>
        <label for="email" class="block text-sm font-medium text-text mb-2">
          Email *
        </label>
        <InputText
          id="email"
          v-model="form.email"
          type="email"
          required
          class="w-full"
          placeholder="utente@esempio.it"
        />
      </div>

      <!-- Password -->
      <div>
        <label for="password" class="block text-sm font-medium text-text mb-2">
          Password *
        </label>
        <Password
          id="password"
          v-model="form.password"
          :feedback="false"
          toggleMask
          class="w-full"
          placeholder="Password sicura"
          required
        />
      </div>

      <!-- Confirm Password -->
      <div>
        <label for="confirmPassword" class="block text-sm font-medium text-text mb-2">
          Conferma Password *
        </label>
        <Password
          id="confirmPassword"
          v-model="form.confirmPassword"
          :feedback="false"
          toggleMask
          class="w-full"
          placeholder="Conferma password"
          required
          :invalid="form.confirmPassword && form.password !== form.confirmPassword"
        />
        <div v-if="form.confirmPassword && form.password !== form.confirmPassword"
             class="mt-1 text-sm text-red-500">
          Le password non coincidono
        </div>
        <div class="mt-2 text-xs text-text-muted">
          <div class="font-medium mb-1">Requisiti password:</div>
          <ul class="list-disc list-inside space-y-0.5">
            <li>Almeno 8 caratteri</li>
            <li>Almeno una maiuscola (A-Z)</li>
            <li>Almeno un carattere speciale (!@#$%^&*)</li>
          </ul>
        </div>
      </div>

      <!-- Role -->
      <div>
        <label for="role" class="block text-sm font-medium text-text mb-2">
          Ruolo *
        </label>
        <Dropdown
          id="role"
          v-model="form.role"
          :options="roleOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Seleziona ruolo"
          class="w-full"
          required
        />
      </div>


      <!-- Error Message -->
      <Message v-if="error" severity="error" :closable="false">
        {{ error }}
      </Message>

    </form>
    
    <template #footer>
      <div class="flex justify-end gap-3">
        <Button
          @click="$emit('close')"
          severity="secondary"
          size="small"
        >
          Annulla
        </Button>
        <Button
          @click="createUser"
          :disabled="isCreating || !form.email || !form.password || !form.confirmPassword || form.password !== form.confirmPassword || !form.role"
          severity="success"
          size="small"
          :loading="isCreating"
        >
          {{ isCreating ? 'Creazione...' : 'Crea Utente' }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { X, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-vue-next'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Message from 'primevue/message'

const props = defineProps({
  roles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'created'])

// Form state
const form = ref({
  email: '',
  password: '',
  confirmPassword: '',
  role: 'viewer'
})

const showPassword = ref(false)
const isCreating = ref(false)
const error = ref('')

// Role options for dropdown
const roleOptions = computed(() => {
  return props.roles.map(role => ({
    label: getRoleLabel(role.name),
    value: role.name
  }))
})

// API Base URL
import { API_BASE_URL } from '../../utils/api-config'
const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL

// Create user
const createUser = async () => {
  isCreating.value = true
  error.value = ''

  // Validate password confirmation
  if (!form.value.password) {
    error.value = 'Inserisci la password'
    isCreating.value = false
    return
  }
  if (!form.value.confirmPassword) {
    error.value = 'Conferma la password'
    isCreating.value = false
    return
  }
  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Le password non coincidono'
    isCreating.value = false
    return
  }

  try {
    // Don't send confirmPassword to backend
    const userData = {
      email: form.value.email,
      password: form.value.password,
      role: form.value.role
    }

    const response = await fetch(`${API_BASE}/api/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      // NO credentials: 'include' - JWT in localStorage
      body: JSON.stringify(userData)
    })

    const data = await response.json()

    if (!data.success) {
      throw new Error(data.message)
    }

    emit('created', data.user)
  } catch (err) {
    error.value = err.message || 'Errore nella creazione utente'
  } finally {
    isCreating.value = false
  }
}

// Get selected role permissions
const getSelectedRolePermissions = () => {
  const selectedRole = props.roles.find(r => r.name === form.value.role)
  return selectedRole?.permissions || []
}

// Helper functions
const getRoleLabel = (role) => {
  const labels = {
    admin: 'Amministratore',
    viewer: 'Visualizzatore'
  }
  return labels[role] || role
}

const formatPermission = (permission) => {
  const parts = permission.split(':')
  if (parts.length === 2) {
    const [resource, action] = parts
    const resourceLabels = {
      users: 'Utenti',
      workflows: 'Processi',
      system: 'Sistema'
    }
    const actionLabels = {
      read: 'Lettura',
      write: 'Scrittura', 
      delete: 'Eliminazione'
    }
    return `${resourceLabels[resource] || resource}: ${actionLabels[action] || action}`
  }
  return permission
}
</script>