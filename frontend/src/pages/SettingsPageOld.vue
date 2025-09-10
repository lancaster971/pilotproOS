<template>
  <MainLayout>
    <div class="space-y-4">
      <!-- Compact Page Title -->
      <div class="mb-2">
        <h1 class="text-lg font-bold text-gradient">Settings</h1>
        <p class="text-xs text-text-muted">Gestione utenti, ruoli e permessi</p>
      </div>
        <div class="flex items-center gap-3">
          <Button
            @click="loadUsers"
            :disabled="isLoading"
            severity="secondary"
            size="small"
            class="premium-button"
          >
            <RefreshCw :class="['h-3 w-3 mr-2', { 'animate-spin': isLoading }]" />
            Aggiorna
          </Button>
          <Button
            @click="showCreateModal = true"
            severity="success"
            size="small"
            class="premium-button"
          >
            <UserPlus class="h-3 w-3 mr-2" />
            Nuovo Utente
          </Button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading && users.length === 0" class="flex items-center justify-center py-12">
        <div class="text-center">
          <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p class="mt-4 text-text-muted">Caricamento utenti...</p>
        </div>
      </div>

      <!-- Error State -->
      <Card v-else-if="error" class="premium-glass border-red-500/20">
        <template #content>
          <div class="p-4">
            <div class="flex items-center">
              <AlertCircle class="h-5 w-5 text-red-400 mr-3" />
              <div>
                <h3 class="text-red-300 font-medium">Errore nel caricamento</h3>
                <p class="text-red-400 text-sm mt-1">{{ error }}</p>
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Users Table -->
      <Card v-else class="premium-glass premium-hover-lift">
        <template #title>
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-text">Gestione Utenti</h2>
              <p class="text-text-muted text-sm mt-1">{{ users.length }} utenti registrati</p>
            </div>
          </div>
        </template>
        <template #content>
          <DataTable 
            :value="users" 
            class="premium-table"
            :paginator="true"
            :rows="10"
            responsiveLayout="scroll"
            stripedRows
          >
            <Column field="email" header="Utente">
              <template #body="{ data }">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-8 w-8">
                    <div class="h-8 w-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-medium">
                      {{ data.email.charAt(0).toUpperCase() }}
                    </div>
                  </div>
                  <div class="ml-3">
                    <div class="text-sm font-medium text-text">{{ data.email }}</div>
                    <div class="text-xs text-text-muted">ID: {{ data.id.slice(0, 8) }}</div>
                  </div>
                </div>
              </template>
            </Column>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="flex-shrink-0 h-10 w-10">
                      <div class="h-10 w-10 rounded-full bg-primary text-white flex items-center justify-center">
                        {{ user.email.charAt(0).toUpperCase() }}
                      </div>
                    </div>
                    <div class="ml-4">
                      <div class="text-sm font-medium text-text">{{ user.email }}</div>
                      <div class="text-sm text-text-muted">ID: {{ user.id.slice(0, 8) }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getRoleBadgeClass(user.role)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                    {{ getRoleLabel(user.role) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="user.is_active ? 'text-green-800 bg-green-100' : 'text-red-800 bg-red-100'" 
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                    {{ user.is_active ? 'Attivo' : 'Disattivo' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-text-muted">
                  {{ formatDate(user.last_login_at) || 'Mai' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="editUser(user)"
                      class="text-indigo-600 hover:text-indigo-900 p-1 rounded hover:bg-indigo-50"
                      title="Modifica utente"
                    >
                      <Edit2 class="h-4 w-4" />
                    </button>
                    <button
                      @click="confirmDeleteUser(user)"
                      class="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50"
                      title="Elimina utente"
                    >
                      <Trash2 class="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Create User Modal -->
      <UserCreateModal 
        v-if="showCreateModal"
        :roles="roles"
        @close="showCreateModal = false"
        @created="handleUserCreated"
      />

      <!-- Edit User Modal -->
      <UserEditModal 
        v-if="showEditModal && selectedUser"
        :user="selectedUser"
        :roles="roles"
        @close="showEditModal = false"
        @updated="handleUserUpdated"
      />

      <!-- Delete Confirmation Modal -->
      <ConfirmModal
        v-if="showDeleteModal && selectedUser"
        :title="'Elimina Utente'"
        :message="`Sei sicuro di voler eliminare l'utente ${selectedUser.email}? Questa azione non può essere annullata.`"
        :confirmText="'Elimina'"
        :confirmClass="'bg-red-600 hover:bg-red-700'"
        :isLoading="isDeletingUser"
        @close="showDeleteModal = false"
        @confirm="deleteUser"
      />
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RefreshCw, UserPlus, AlertCircle, Edit2, Trash2 } from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import UserCreateModal from '../components/settings/UserCreateModal.vue'
import UserEditModal from '../components/settings/UserEditModal.vue'
import ConfirmModal from '../components/common/ConfirmModal.vue'
import { useToast } from 'vue-toastification'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Tag from 'primevue/tag'

const toast = useToast()

// State
const users = ref([])
const roles = ref([])
const isLoading = ref(false)
const error = ref('')
const isDeletingUser = ref(false)

// Modals
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const selectedUser = ref(null)

// API Base URL (direct backend call)
const API_BASE = 'http://localhost:3001'

// Get auth token
const getAuthToken = () => localStorage.getItem('pilotpro_token')

// Load users from API
const loadUsers = async () => {
  isLoading.value = true
  error.value = ''
  
  try {
    const response = await fetch(`${API_BASE}/api/users`, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    
    const data = await response.json()
    
    if (!data.success) {
      throw new Error(data.message)
    }
    
    users.value = data.users
  } catch (err) {
    error.value = err.message || 'Errore nel caricamento utenti'
    toast.error('Errore nel caricamento utenti')
  } finally {
    isLoading.value = false
  }
}

// Load available roles
const loadRoles = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/roles`, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    
    const data = await response.json()
    
    if (data.success) {
      roles.value = data.roles
    }
  } catch (err) {
    console.error('Error loading roles:', err)
  }
}

// Edit user
const editUser = (user) => {
  selectedUser.value = user
  showEditModal.value = true
}

// Confirm delete user
const confirmDeleteUser = (user) => {
  selectedUser.value = user
  showDeleteModal.value = true
}

// Delete user
const deleteUser = async () => {
  isDeletingUser.value = true
  
  try {
    const response = await fetch(`${API_BASE}/api/users/${selectedUser.value.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    
    const data = await response.json()
    
    if (!data.success) {
      throw new Error(data.message)
    }
    
    // Remove user from list
    users.value = users.value.filter(u => u.id !== selectedUser.value.id)
    toast.success('Utente eliminato con successo')
    
    showDeleteModal.value = false
    selectedUser.value = null
    
  } catch (err) {
    toast.error(err.message || 'Errore nell\'eliminazione utente')
  } finally {
    isDeletingUser.value = false
  }
}

// Handle user created
const handleUserCreated = (newUser) => {
  users.value.unshift(newUser)
  showCreateModal.value = false
  toast.success('Utente creato con successo')
}

// Handle user updated
const handleUserUpdated = (updatedUser) => {
  const index = users.value.findIndex(u => u.id === updatedUser.id)
  if (index >= 0) {
    users.value[index] = updatedUser
  }
  showEditModal.value = false
  selectedUser.value = null
  toast.success('Utente aggiornato con successo')
}

// Role helpers
const getRoleLabel = (role) => {
  const labels = {
    admin: 'Amministratore',
    editor: 'Editor',
    viewer: 'Visualizzatore'
  }
  return labels[role] || role
}

const getRoleSeverity = (role) => {
  const severities = {
    admin: 'danger',
    editor: 'warn',
    viewer: 'info'
  }
  return severities[role] || 'info'
}

const getRoleBadgeClass = (role) => {
  const classes = {
    admin: 'text-red-800 bg-red-100',
    editor: 'text-blue-800 bg-blue-100',
    viewer: 'text-green-800 bg-green-100'
  }
  return classes[role] || 'text-gray-800 bg-gray-100'
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return null
  return new Date(dateString).toLocaleString('it-IT')
}

// Initialize
onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>