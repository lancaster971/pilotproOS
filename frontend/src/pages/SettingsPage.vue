<template>
  <MainLayout>
    <div class="space-y-4">
      <!-- Settings Tabs -->
      <TabView class="premium-tabs">
        <TabPanel>
          <template #header>
            <div class="flex items-center gap-2">
              <Icon icon="mdi:account-group" class="h-4 w-4" />
              <span>Gestione Utenti</span>
            </div>
          </template>
          
          <!-- Action Buttons -->
          <div class="flex items-center gap-3 mb-4">
            <Button
              @click="loadUsers"
              :disabled="isLoading"
              severity="secondary"
              size="small"
              class="premium-button"
            >
              <Icon icon="mdi:refresh" :class="['h-3 w-3 mr-2', { 'animate-spin': isLoading }]" />
              Aggiorna
            </Button>
            <Button
              @click="showCreateModal = true"
              severity="success"
              size="small"
              class="premium-button"
            >
              <Icon icon="mdi:account-plus" class="h-3 w-3 mr-2" />
              Nuovo Utente
            </Button>
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
                  <Icon icon="mdi:alert-circle" class="h-5 w-5 text-red-400 mr-3" />
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
                
                <Column field="role" header="Ruolo">
                  <template #body="{ data }">
                    <Tag 
                      :value="data.role" 
                      :severity="getRoleSeverity(data.role)"
                      class="premium-tag"
                    />
                  </template>
                </Column>
                
                <Column field="created_at" header="Creato">
                  <template #body="{ data }">
                    <span class="text-sm text-text-muted">
                      {{ formatDate(data.created_at) }}
                    </span>
                  </template>
                </Column>
                
                <Column field="is_active" header="Stato">
                  <template #body="{ data }">
                    <Tag 
                      :value="data.is_active ? 'Attivo' : 'Disattivo'" 
                      :severity="data.is_active ? 'success' : 'danger'"
                      class="premium-tag"
                    />
                  </template>
                </Column>
                
                <Column header="Azioni">
                  <template #body="{ data }">
                    <div class="flex gap-2">
                      <Button
                        @click="editUser(data)"
                        severity="info"
                        size="small"
                        class="premium-button p-2"
                      >
                        <Icon icon="mdi:pencil" class="h-3 w-3" />
                      </Button>
                      <Button
                        @click="confirmDeleteUser(data)"
                        severity="danger"
                        size="small"
                        class="premium-button p-2"
                      >
                        <Icon icon="mdi:delete" class="h-3 w-3" />
                      </Button>
                    </div>
                  </template>
                </Column>
              </DataTable>
            </template>
          </Card>
        </TabPanel>

        <TabPanel>
          <template #header>
            <div class="flex items-center gap-2">
              <Icon icon="mdi:shield" class="h-4 w-4" />
              <span>Autenticazione</span>
            </div>
          </template>
          
          <!-- Current Authentication Method -->
          <Card class="premium-glass mb-6">
            <template #title>
              <h3 class="text-lg font-semibold text-text">Metodo Autenticazione Corrente</h3>
            </template>
            <template #content>
              <div class="flex items-center">
                <div class="flex-shrink-0 mr-4">
                  <div class="h-10 w-10 rounded-full bg-primary flex items-center justify-center">
                    <Icon icon="mdi:shield" class="h-5 w-5 text-white" />
                  </div>
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-text">{{ currentAuthMethod.label }}</span>
                    <Tag 
                      :value="currentAuthMethod.label" 
                      :severity="currentAuthMethod.severity"
                      class="premium-tag"
                    />
                  </div>
                  <p class="text-sm text-text-muted mt-1">{{ currentAuthMethod.description }}</p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Authentication Methods Selection -->
          <Card class="premium-glass">
            <template #title>
              <h3 class="text-lg font-semibold text-text">Configurazione Metodi di Autenticazione</h3>
            </template>
            <template #content>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Local Authentication -->
                <div 
                  class="premium-glass cursor-pointer border-2 transition-all duration-200 rounded-lg hover:border-primary hover:scale-105"
                  :class="authConfig.method === 'local' ? 'border-primary border-4' : 'border-gray-600'"
                  @click="openAuthConfigModal('local')"
                >
                  <div class="p-6 text-center">
                    <Icon icon="mdi:key" class="h-12 w-12 mx-auto mb-4 text-primary" />
                    <h3 class="text-lg font-medium text-text mb-2">Local</h3>
                    <p class="text-sm text-text-muted mb-4">Autenticazione con database locale</p>
                    <Button 
                      severity="info" 
                      size="small"
                      class="premium-button w-full"
                      @click.stop="openAuthConfigModal('local')"
                    >
                      Configura Local
                    </Button>
                  </div>
                </div>
                
                <!-- LDAP Authentication -->
                <div 
                  class="premium-glass cursor-pointer border-2 transition-all duration-200 rounded-lg hover:border-warning hover:scale-105"
                  :class="authConfig.method === 'ldap' ? 'border-warning border-4' : 'border-gray-600'"
                  @click="openAuthConfigModal('ldap')"
                >
                  <div class="p-6 text-center">
                    <Server class="h-12 w-12 mx-auto mb-4 text-warning" />
                    <h3 class="text-lg font-medium text-text mb-2">LDAP</h3>
                    <p class="text-sm text-text-muted mb-4">Autenticazione con Active Directory</p>
                    <Button 
                      severity="warning" 
                      size="small"
                      class="premium-button w-full"
                      @click.stop="openAuthConfigModal('ldap')"
                    >
                      Configura LDAP
                    </Button>
                  </div>
                </div>
                
                <!-- LDAP + MFA -->
                <div 
                  class="premium-glass cursor-pointer border-2 transition-all duration-200 rounded-lg hover:border-success hover:scale-105"
                  :class="authConfig.method === 'ldap_mfa' ? 'border-success border-4' : 'border-gray-600'"
                  @click="openAuthConfigModal('ldap_mfa')"
                >
                  <div class="p-6 text-center">
                    <Shield class="h-12 w-12 mx-auto mb-4 text-success" />
                    <h3 class="text-lg font-medium text-text mb-2">LDAP + MFA</h3>
                    <p class="text-sm text-text-muted mb-4">LDAP con autenticazione a due fattori</p>
                    <Button 
                      severity="success" 
                      size="small"
                      class="premium-button w-full"
                      @click.stop="openAuthConfigModal('ldap_mfa')"
                    >
                      Configura LDAP+MFA
                    </Button>
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </TabPanel>

        <!-- Backup & Restore Tab -->
        <TabPanel>
          <template #header>
            <div class="flex items-center gap-2">
              <Icon icon="mdi:database-export" class="h-4 w-4" />
              <span>Backup & Ripristino</span>
            </div>
          </template>

          <!-- Create Backup Section -->
          <Card class="premium-glass mb-6">
            <template #title>
              <h3 class="text-lg font-semibold text-text">Crea Backup</h3>
            </template>
            <template #content>
              <div class="space-y-4">
                <p class="text-text-muted text-sm">
                  Crea un backup completo del database inclusi workflow, credenziali, esecuzioni e configurazioni.
                </p>
                <Button
                  @click="createBackup"
                  :disabled="isCreatingBackup"
                  severity="success"
                  class="premium-button"
                >
                  <Icon icon="mdi:database-export" :class="['h-4 w-4 mr-2', { 'animate-spin': isCreatingBackup }]" />
                  {{ isCreatingBackup ? 'Creazione in corso...' : 'Crea Backup Ora' }}
                </Button>
              </div>
            </template>
          </Card>

          <!-- Backup List -->
          <Card class="premium-glass">
            <template #title>
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-text">Backup Disponibili</h3>
                <Button
                  @click="loadBackups"
                  :disabled="isLoadingBackups"
                  severity="secondary"
                  size="small"
                  text
                >
                  <Icon icon="mdi:refresh" :class="['h-4 w-4', { 'animate-spin': isLoadingBackups }]" />
                </Button>
              </div>
            </template>
            <template #content>
              <!-- Loading State -->
              <div v-if="isLoadingBackups && backups.length === 0" class="text-center py-8">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p class="mt-3 text-text-muted text-sm">Caricamento backup...</p>
              </div>

              <!-- Empty State -->
              <div v-else-if="backups.length === 0" class="text-center py-8">
                <Icon icon="mdi:database-off" class="h-12 w-12 text-text-muted mb-3" />
                <p class="text-text-muted">Nessun backup disponibile</p>
                <p class="text-text-muted text-sm mt-1">Crea il tuo primo backup per proteggere i dati</p>
              </div>

              <!-- Backups Table -->
              <DataTable
                v-else
                :value="backups"
                class="premium-table"
                :paginator="true"
                :rows="5"
                stripedRows
              >
                <Column field="filename" header="Nome File">
                  <template #body="{ data }">
                    <div class="flex items-center">
                      <Icon icon="mdi:file-document" class="h-5 w-5 text-primary mr-2" />
                      <span class="text-sm font-mono">{{ data.filename }}</span>
                    </div>
                  </template>
                </Column>

                <Column field="size" header="Dimensione">
                  <template #body="{ data }">
                    <span class="text-sm">{{ formatBytes(data.size) }}</span>
                  </template>
                </Column>

                <Column field="created" header="Data Creazione">
                  <template #body="{ data }">
                    <span class="text-sm">{{ formatDate(data.created) }}</span>
                  </template>
                </Column>

                <Column header="Azioni">
                  <template #body="{ data }">
                    <div class="flex gap-2">
                      <Button
                        @click="downloadBackup(data.filename)"
                        severity="secondary"
                        size="small"
                        text
                        v-tooltip.top="'Scarica'"
                      >
                        <Icon icon="mdi:download" class="h-4 w-4" />
                      </Button>
                      <Button
                        @click="confirmRestore(data.filename)"
                        severity="warning"
                        size="small"
                        text
                        v-tooltip.top="'Ripristina'"
                      >
                        <Icon icon="mdi:database-import" class="h-4 w-4" />
                      </Button>
                      <Button
                        @click="confirmDelete(data.filename)"
                        severity="danger"
                        size="small"
                        text
                        v-tooltip.top="'Elimina'"
                      >
                        <Icon icon="mdi:delete" class="h-4 w-4" />
                      </Button>
                    </div>
                  </template>
                </Column>
              </DataTable>
            </template>
          </Card>
        </TabPanel>
      </TabView>

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
        @close="showEditModal = false; selectedUser = null"
        @updated="handleUserUpdated"
      />

      <!-- Delete Confirmation Modal -->
      <ConfirmModal
        v-if="showDeleteModal && userToDelete"
        title="Conferma Eliminazione"
        :message="`Sei sicuro di voler eliminare l'utente ${userToDelete.email}? Questa azione non può essere annullata.`"
        confirm-text="Elimina"
        confirm-class="bg-red-600 hover:bg-red-700"
        :is-loading="isDeletingUser"
        @close="showDeleteModal = false; userToDelete = null"
        @confirm="deleteUser"
      />

      <!-- Auth Configuration Modal -->
      <AuthConfigModal
        v-model:visible="showAuthConfigModal"
        :config="authConfig"
        :is-editing="true"
        @saved="handleAuthConfigSaved"
      />

      <!-- Restore Backup Confirmation Modal -->
      <ConfirmModal
        v-if="showRestoreModal && selectedBackup"
        title="Conferma Ripristino"
        :message="`Sei sicuro di voler ripristinare il database dal backup ${selectedBackup}? Tutti i dati attuali saranno sovrascritti. Questa azione non può essere annullata.`"
        confirm-text="Ripristina"
        confirm-class="bg-yellow-600 hover:bg-yellow-700"
        @close="showRestoreModal = false; selectedBackup = null"
        @confirm="restoreBackup"
      />

      <!-- Delete Backup Confirmation Modal -->
      <ConfirmModal
        v-if="showDeleteBackupModal && selectedBackup"
        title="Conferma Eliminazione Backup"
        :message="`Sei sicuro di voler eliminare il backup ${selectedBackup}? Questa azione non può essere annullata.`"
        confirm-text="Elimina"
        confirm-class="bg-red-600 hover:bg-red-700"
        @close="showDeleteBackupModal = false; selectedBackup = null"
        @confirm="deleteBackup"
      />
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import MainLayout from '../components/layout/MainLayout.vue'
import UserCreateModal from '../components/settings/UserCreateModal.vue'
import UserEditModal from '../components/settings/UserEditModal.vue'
import AuthConfigModal from '../components/settings/AuthConfigModal.vue'
import ConfirmModal from '../components/common/ConfirmModal.vue'
import { useToast } from 'vue-toastification'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Tag from 'primevue/tag'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'

const toast = useToast()

// State
const isLoading = ref(false)
const users = ref([])
const roles = ref([])
const error = ref('')
const isDeletingUser = ref(false)

// Modals
const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedUser = ref(null)
const showDeleteModal = ref(false)
const userToDelete = ref(null)
const showAuthConfigModal = ref(false)

// Authentication Configuration
const authConfig = ref({
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

const currentAuthMethod = ref({
  label: 'Local',
  severity: 'info',
  description: 'Autenticazione tramite database locale con username e password'
})

// Backup & Restore State
const backups = ref([])
const isLoadingBackups = ref(false)
const isCreatingBackup = ref(false)
const showRestoreModal = ref(false)
const showDeleteBackupModal = ref(false)
const selectedBackup = ref(null)

// API configuration - use dynamic base URL
import { API_BASE_URL } from '../utils/api-config'
const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL

// Load users and roles
const loadUsers = async () => {
  isLoading.value = true
  error.value = ''
  
  try {
    const [usersResponse, rolesResponse] = await Promise.all([
      fetch(`${API_BASE}/api/users`, {
        // NO credentials: 'include' - JWT in localStorage
      }),
      fetch(`${API_BASE}/api/roles`, {
        // NO credentials: 'include' - JWT in localStorage
      })
    ])

    const usersData = await usersResponse.json()
    const rolesData = await rolesResponse.json()

    if (!usersData.success) {
      throw new Error(usersData.message)
    }

    if (!rolesData.success) {
      throw new Error(rolesData.message)
    }

    users.value = usersData.users
    roles.value = rolesData.roles
  } catch (err) {
    error.value = err.message || 'Errore nel caricamento dati'
    console.error('Error loading users:', err)
  } finally {
    isLoading.value = false
  }
}

// Load auth configuration
const loadAuthConfig = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/auth/config`, {
      // NO credentials: 'include' - JWT in localStorage
    })

    const data = await response.json()

    if (data.success && data.config) {
      Object.assign(authConfig.value, data.config)
      
      // Update current auth method display
      const methodLabels = {
        local: {
          label: 'Local',
          severity: 'info',
          description: 'Autenticazione tramite database locale con username e password'
        },
        ldap: {
          label: 'LDAP',
          severity: 'warning',
          description: 'Autenticazione tramite server LDAP esterno'
        },
        ldap_mfa: {
          label: 'LDAP + MFA',
          severity: 'success',
          description: 'Autenticazione LDAP con autenticazione a due fattori'
        }
      }
      
      currentAuthMethod.value = methodLabels[authConfig.value.method] || methodLabels.local
    }
  } catch (err) {
    console.error('Errore caricamento configurazione:', err)
    // Keep default configuration on error
  }
}

// Edit user
const editUser = (user) => {
  selectedUser.value = { ...user }
  showEditModal.value = true
}

// Delete user functions
const confirmDeleteUser = (user) => {
  userToDelete.value = user
  showDeleteModal.value = true
}

const deleteUser = async () => {
  if (!userToDelete.value) return
  
  isDeletingUser.value = true
  
  try {
    const response = await fetch(`${API_BASE}/api/users/${userToDelete.value.id}`, {
      method: 'DELETE'
      // NO credentials: 'include' - JWT in localStorage
    })

    const data = await response.json()

    if (!data.success) {
      throw new Error(data.message)
    }

    // Remove user from list
    users.value = users.value.filter(u => u.id !== userToDelete.value.id)
    
    toast.success('Utente eliminato con successo')
    showDeleteModal.value = false
    userToDelete.value = null
  } catch (err) {
    console.error('Error deleting user:', err)
    toast.error(`Errore nell'eliminazione: ${err.message}`)
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

// Open auth config modal with specific method
const openAuthConfigModal = (method = null) => {
  if (method) {
    // Pre-select the method in the modal
    authConfig.value.method = method
  }
  showAuthConfigModal.value = true
}

// Handle auth config saved
const handleAuthConfigSaved = (updatedConfig) => {
  Object.assign(authConfig.value, updatedConfig)
  
  // Update current auth method display
  const methodLabels = {
    local: {
      label: 'Local',
      severity: 'info',
      description: 'Autenticazione tramite database locale con username e password'
    },
    ldap: {
      label: 'LDAP',
      severity: 'warning',
      description: 'Autenticazione tramite server LDAP esterno'
    },
    ldap_mfa: {
      label: 'LDAP + MFA',
      severity: 'success',
      description: 'Autenticazione LDAP con autenticazione a due fattori'
    }
  }
  
  currentAuthMethod.value = methodLabels[updatedConfig.method] || methodLabels.local
  toast.success('Configurazione autenticazione aggiornata')
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

// Utility functions
const formatDate = (dateString) => {
  if (!dateString) return 'Mai'
  return new Date(dateString).toLocaleDateString('it-IT', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getRoleSeverity = (role) => {
  const severities = {
    admin: 'danger',
    editor: 'warning',
    viewer: 'info'
  }
  return severities[role] || 'info'
}

// ============================================================================
// BACKUP & RESTORE FUNCTIONS
// ============================================================================

// Load available backups
const loadBackups = async () => {
  isLoadingBackups.value = true
  try {
    const response = await fetch(`${API_BASE}/api/backup/list`, {
      credentials: 'include'
    })
    const data = await response.json()

    if (data.success) {
      backups.value = data.backups
    } else {
      toast.error('Errore nel caricamento dei backup')
    }
  } catch (error) {
    console.error('Load backups error:', error)
    toast.error('Errore nella connessione al server')
  } finally {
    isLoadingBackups.value = false
  }
}

// Create new backup
const createBackup = async () => {
  isCreatingBackup.value = true
  try {
    const response = await fetch(`${API_BASE}/api/backup/create`, {
      method: 'POST',
      credentials: 'include'
    })
    const data = await response.json()

    if (data.success) {
      toast.success('Backup creato con successo!')
      await loadBackups()
    } else {
      toast.error('Errore nella creazione del backup')
    }
  } catch (error) {
    console.error('Create backup error:', error)
    toast.error('Errore nella connessione al server')
  } finally {
    isCreatingBackup.value = false
  }
}

// Download backup file
const downloadBackup = (filename) => {
  window.location.href = `${API_BASE}/api/backup/download/${filename}`
  toast.success('Download avviato')
}

// Confirm restore
const confirmRestore = (filename) => {
  selectedBackup.value = filename
  showRestoreModal.value = true
}

// Restore from backup
const restoreBackup = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/backup/restore/${selectedBackup.value}`, {
      method: 'POST',
      credentials: 'include'
    })
    const data = await response.json()

    if (data.success) {
      toast.success('Database ripristinato con successo!')
      showRestoreModal.value = false
      // Reload page after 2 seconds
      setTimeout(() => window.location.reload(), 2000)
    } else {
      toast.error('Errore nel ripristino del database')
    }
  } catch (error) {
    console.error('Restore error:', error)
    toast.error('Errore nella connessione al server')
  }
}

// Confirm delete backup
const confirmDelete = (filename) => {
  selectedBackup.value = filename
  showDeleteBackupModal.value = true
}

// Delete backup
const deleteBackup = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/backup/delete/${selectedBackup.value}`, {
      method: 'DELETE',
      credentials: 'include'
    })
    const data = await response.json()

    if (data.success) {
      toast.success('Backup eliminato')
      showDeleteBackupModal.value = false
      await loadBackups()
    } else {
      toast.error('Errore nell\'eliminazione del backup')
    }
  } catch (error) {
    console.error('Delete backup error:', error)
    toast.error('Errore nella connessione al server')
  }
}

// Format bytes to human readable
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// Format date
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('it-IT', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

// Initialize on mount
onMounted(() => {
  loadUsers()
  loadAuthConfig()
  loadBackups()
})
</script>

<style scoped>
/* Import Insights Theme Consistency */
.settings-container {
  width: 100%;
  padding: 20px;
  background: #0a0a0a;
  min-height: 100vh;
}

/* Override PrimeVue Components to match Insights */
:deep(.p-tabview) {
  background: transparent !important;
}

:deep(.p-tabview-nav) {
  background: rgba(15, 15, 15, 0.6) !important;
  border: 1px solid rgba(31, 41, 55, 0.3) !important;
  border-radius: 8px 8px 0 0 !important;
  backdrop-filter: blur(10px) !important;
}

:deep(.p-tabview-header) {
  background: transparent !important;
  border: none !important;
}

:deep(.p-tabview-header.p-highlight .p-tabview-nav-link) {
  background: rgba(16, 185, 129, 0.1) !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
  color: #10b981 !important;
}

:deep(.p-tabview-nav-link) {
  color: #9ca3af !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

:deep(.p-tabview-panels) {
  background: rgba(15, 15, 15, 0.6) !important;
  border: 1px solid rgba(31, 41, 55, 0.3) !important;
  border-top: none !important;
  backdrop-filter: blur(10px) !important;
  padding: 24px !important;
}

/* Card Styling to match Insights */
:deep(.p-card) {
  background: rgba(10, 10, 15, 0.9) !important;
  border: 1px solid rgba(31, 41, 55, 0.5) !important;
  border-radius: 12px !important;
  backdrop-filter: blur(10px) !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.6) !important;
}

:deep(.p-card-title) {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: #9ca3af !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  padding-bottom: 12px !important;
  border-bottom: 1px solid rgba(31, 41, 55, 0.5) !important;
}

:deep(.p-card-content) {
  background: transparent !important;
  color: #e5e7eb !important;
}

/* Button Styling to match Insights */
:deep(.p-button) {
  background: rgba(31, 41, 55, 0.5) !important;
  border: 1px solid rgba(107, 114, 128, 0.3) !important;
  border-radius: 6px !important;
  color: #e5e7eb !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
  box-shadow: none !important;
}

:deep(.p-button:hover:not(:disabled)) {
  background: rgba(31, 41, 55, 0.8) !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
  transform: translateY(-1px) !important;
}

:deep(.p-button-success) {
  background: rgba(16, 185, 129, 0.1) !important;
  border: 1px solid rgba(16, 185, 129, 0.3) !important;
  color: #10b981 !important;
}

:deep(.p-button-danger) {
  background: rgba(239, 68, 68, 0.1) !important;
  border: 1px solid rgba(239, 68, 68, 0.3) !important;
  color: #ef4444 !important;
}

/* DataTable Styling to match Insights */
:deep(.p-datatable) {
  background: transparent !important;
  border: none !important;
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
  background: transparent !important;
  color: #9ca3af !important;
  border-bottom: 1px solid rgba(31, 41, 55, 0.5) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  padding: 12px !important;
}

:deep(.p-datatable .p-datatable-tbody > tr) {
  background: transparent !important;
  color: #e5e7eb !important;
}

:deep(.p-datatable .p-datatable-tbody > tr:hover) {
  background: rgba(31, 41, 55, 0.1) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr > td) {
  border-bottom: 1px solid rgba(31, 41, 55, 0.2) !important;
  padding: 12px !important;
  font-size: 13px !important;
}

/* Tag/Badge Styling */
:deep(.p-tag) {
  padding: 2px 8px !important;
  border-radius: 4px !important;
  font-size: 10px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  border: 1px solid !important;
}

:deep(.p-tag-success) {
  background: rgba(16, 185, 129, 0.1) !important;
  color: #10b981 !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
}

:deep(.p-tag-danger) {
  background: rgba(239, 68, 68, 0.1) !important;
  color: #ef4444 !important;
  border-color: rgba(239, 68, 68, 0.3) !important;
}

:deep(.p-tag-warning) {
  background: rgba(245, 158, 11, 0.1) !important;
  color: #f59e0b !important;
  border-color: rgba(245, 158, 11, 0.3) !important;
}

:deep(.p-tag-info) {
  background: rgba(59, 130, 246, 0.1) !important;
  color: #93bbfc !important;
  border-color: rgba(59, 130, 246, 0.3) !important;
}

/* Custom Classes matching Insights */
.premium-glass {
  background: rgba(15, 15, 15, 0.6) !important;
  border: 1px solid rgba(31, 41, 55, 0.3) !important;
  border-radius: 12px !important;
  backdrop-filter: blur(10px) !important;
}

.premium-hover-lift:hover {
  border-color: rgba(16, 185, 129, 0.3) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3) !important;
}

/* Loading State */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Empty State */
:deep(.p-datatable-emptymessage) {
  text-align: center !important;
  padding: 60px 20px !important;
  color: #9ca3af !important;
}

/* Responsive */
@media (max-width: 768px) {
  :deep(.p-tabview-nav-link) {
    font-size: 11px !important;
  }

  :deep(.p-card) {
    padding: 16px !important;
  }
}
</style>

<style scoped>
.premium-tabs :deep(.p-tabview-nav) {
  @apply bg-surface border-b border-gray-600;
  backdrop-filter: blur(10px);
  border-radius: 0.5rem 0.5rem 0 0;
}

.premium-tabs :deep(.p-tabview-nav-link) {
  @apply text-text-muted hover:text-text transition-all duration-200;
}

.premium-tabs :deep(.p-tabview-nav-link.p-highlight) {
  @apply text-primary border-b-2 border-primary;
}

.premium-tabs :deep(.p-tabview-panels) {
  @apply bg-surface text-text p-4;
  backdrop-filter: blur(5px);
  border-radius: 0 0 0.5rem 0.5rem;
}

.premium-glass {
  @apply bg-surface backdrop-blur-xl border border-gray-600 shadow-2xl;
  border-radius: 1rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  background-color: rgba(var(--surface-rgb), 0.8);
}

.premium-hover-lift {
  @apply transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl;
}

.premium-button {
  @apply transition-all duration-200 hover:scale-105 active:scale-95;
  backdrop-filter: blur(10px);
}

.premium-table :deep(.p-datatable) {
  @apply bg-transparent;
}

.premium-table :deep(.p-datatable-header) {
  @apply bg-surface border-gray-600;
  backdrop-filter: blur(10px);
}

.premium-table :deep(.p-datatable-tbody > tr) {
  @apply border-gray-600 hover:bg-surface transition-colors duration-200;
}

.premium-table :deep(.p-datatable-thead > tr > th) {
  @apply bg-surface text-text border-gray-600;
  backdrop-filter: blur(5px);
}

.premium-tag {
  @apply text-xs font-medium px-2 py-1 rounded-md;
}

.text-gradient {
  @apply bg-gradient-to-r from-primary via-primary to-primary bg-clip-text text-transparent;
}
</style>