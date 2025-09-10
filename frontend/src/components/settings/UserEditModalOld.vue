<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4">
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-semibold text-text">Modifica Utente</h3>
          <button 
            @click="$emit('close')"
            class="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X class="h-5 w-5" />
          </button>
        </div>

        <!-- Form -->
        <form @submit.prevent="updateUser" class="space-y-4">
          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-text mb-2">
              Email *
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          <!-- Role -->
          <div>
            <label for="role" class="block text-sm font-medium text-text mb-2">
              Ruolo *
            </label>
            <select
              id="role"
              v-model="form.role"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option v-for="role in roles" :key="role.name" :value="role.name">
                {{ getRoleLabel(role.name) }}
              </option>
            </select>
          </div>

          <!-- Status -->
          <div>
            <label class="block text-sm font-medium text-text mb-2">
              Stato Account
            </label>
            <div class="flex items-center gap-4">
              <label class="flex items-center">
                <input
                  v-model="form.is_active"
                  type="radio"
                  :value="true"
                  class="text-green-600 focus:ring-green-500"
                />
                <span class="ml-2 text-sm text-text">Attivo</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="form.is_active"
                  type="radio"
                  :value="false"
                  class="text-red-600 focus:ring-red-500"
                />
                <span class="ml-2 text-sm text-text">Disattivo</span>
              </label>
            </div>
          </div>

          <!-- Change Password -->
          <div class="border-t pt-4">
            <label class="flex items-center mb-3">
              <input
                v-model="changePassword"
                type="checkbox"
                class="text-primary focus:ring-primary"
              />
              <span class="ml-2 text-sm font-medium text-text">Cambia password</span>
            </label>
            
            <div v-if="changePassword">
              <label for="password" class="block text-sm font-medium text-text mb-2">
                Nuova Password *
              </label>
              <div class="relative">
                <input
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  :required="changePassword"
                  minlength="6"
                  class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Minimo 6 caratteri"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <Eye v-if="!showPassword" class="h-4 w-4" />
                  <EyeOff v-else class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <!-- Role Permissions Preview -->
          <div v-if="form.role" class="bg-gray-50 rounded-lg p-3">
            <h4 class="text-sm font-medium text-text mb-2">Permessi per {{ getRoleLabel(form.role) }}:</h4>
            <div class="flex flex-wrap gap-1">
              <span 
                v-for="permission in getSelectedRolePermissions()" 
                :key="permission"
                class="inline-block px-2 py-1 bg-primary/10 text-primary text-xs rounded"
              >
                {{ formatPermission(permission) }}
              </span>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-3">
            <div class="flex items-center">
              <AlertCircle class="h-4 w-4 text-red-500 mr-2" />
              <p class="text-red-700 text-sm">{{ error }}</p>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              @click="$emit('close')"
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Annulla
            </button>
            <button
              type="submit"
              :disabled="isUpdating || !form.email || !form.role"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Loader2 v-if="isUpdating" class="h-4 w-4 animate-spin" />
              {{ isUpdating ? 'Aggiornamento...' : 'Aggiorna Utente' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { X, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-vue-next'

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
const showPassword = ref(false)
const isUpdating = ref(false)
const error = ref('')

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
const API_BASE = 'http://localhost:3001'
const getAuthToken = () => localStorage.getItem('pilotpro_token')

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
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
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
    editor: 'Editor',
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