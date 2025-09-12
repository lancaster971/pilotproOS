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
        <h3 class="text-lg font-semibold text-text">Modifica Utente</h3>
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

    <form @submit.prevent="updateUser" class="space-y-4">
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
        />
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

      <!-- Status -->
      <div>
        <label class="block text-sm font-medium text-text mb-2">
          Stato Account
        </label>
        <div class="flex items-center gap-4">
          <div class="flex items-center">
            <RadioButton 
              id="active" 
              v-model="form.is_active" 
              :value="true" 
            />
            <label for="active" class="ml-2 text-sm text-text">Attivo</label>
          </div>
          <div class="flex items-center">
            <RadioButton 
              id="inactive" 
              v-model="form.is_active" 
              :value="false" 
            />
            <label for="inactive" class="ml-2 text-sm text-text">Disattivo</label>
          </div>
        </div>
      </div>

      <!-- Change Password -->
      <div class="border-t pt-4">
        <div class="flex items-center mb-3">
          <Checkbox 
            id="changePassword" 
            v-model="changePassword" 
            :binary="true" 
          />
          <label for="changePassword" class="ml-2 text-sm font-medium text-text">
            Cambia password
          </label>
        </div>
        
        <div v-if="changePassword">
          <label for="password" class="block text-sm font-medium text-text mb-2">
            Nuova Password *
          </label>
          <Password
            id="password"
            v-model="form.password"
            :feedback="false"
            toggleMask
            class="w-full"
            placeholder="Password sicura"
            :required="changePassword"
          />
          <div class="mt-2 text-xs text-text-muted">
            <div class="font-medium mb-1">Requisiti password:</div>
            <ul class="list-disc list-inside space-y-0.5">
              <li>Almeno 8 caratteri</li>
              <li>Almeno una maiuscola (A-Z)</li>
              <li>Almeno un carattere speciale (!@#$%^&*)</li>
            </ul>
          </div>
        </div>
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
          @click="updateUser"
          :disabled="isUpdating || !form.email || !form.role"
          severity="info"
          size="small"
          :loading="isUpdating"
        >
          {{ isUpdating ? 'Aggiornamento...' : 'Aggiorna Utente' }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { X, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-vue-next'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Dropdown from 'primevue/dropdown'
import RadioButton from 'primevue/radiobutton'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Message from 'primevue/message'

const props = defineProps({
  user: {
    type: Object,
    required: true
  },
  roles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'updated'])

// Form state
const form = ref({
  email: '',
  role: '',
  is_active: true,
  password: ''
})

const changePassword = ref(false)
const isUpdating = ref(false)
const error = ref('')

// Role options for dropdown
const roleOptions = computed(() => {
  return props.roles.map(role => ({
    label: getRoleLabel(role.name),
    value: role.name
  }))
})

// Initialize form with user data
onMounted(() => {
  form.value = {
    email: props.user.email,
    role: props.user.role,
    is_active: props.user.is_active,
    password: ''
  }
})

// API Base URL
import { API_BASE_URL } from '../../utils/api-config'
const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL

// Update user
const updateUser = async () => {
  isUpdating.value = true
  error.value = ''

  try {
    const updateData = {
      email: form.value.email,
      role: form.value.role,
      is_active: form.value.is_active
    }

    // Only include password if changing
    if (changePassword.value && form.value.password) {
      updateData.password = form.value.password
    }

    const response = await fetch(`${API_BASE}/api/users/${props.user.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include', // Include HttpOnly cookies
      body: JSON.stringify(updateData)
    })

    const data = await response.json()

    if (!data.success) {
      throw new Error(data.message)
    }

    emit('updated', data.user)
  } catch (err) {
    error.value = err.message || 'Errore nell\'aggiornamento utente'
  } finally {
    isUpdating.value = false
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