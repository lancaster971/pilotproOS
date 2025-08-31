# MODAL INTEGRATION EXAMPLES
**PilotProOS - Practical Usage Examples**

**Documento**: Esempi Pratici di Integrazione Modal  
**Versione**: 1.0.0  
**Target**: Sviluppatori che implementano modal  

---

## 🎯 **QUICK INTEGRATION GUIDE**

### **1. SimpleModal - Form Creation**

#### **Example: Create Business Process Modal**
```vue
<template>
  <div>
    <!-- Trigger Button -->
    <button @click="openCreateModal" class="btn-control-primary">
      <Plus class="h-4 w-4" />
      New Business Process
    </button>

    <!-- Modal Component -->
    <SimpleModal
      :show="showCreateModal"
      title="Create New Business Process"
      submit-text="Create Process"
      :is-loading="isCreating"
      :can-submit="isFormValid"
      @close="closeCreateModal"
      @submit="handleCreateProcess"
    >
      <template #content="{ close }">
        <form @submit.prevent="handleCreateProcess" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-2">
              Process Name
            </label>
            <input
              v-model="formData.name"
              type="text"
              required
              class="w-full px-3 py-2 bg-surface border border-border text-text rounded-lg focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
              placeholder="Enter process name"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-text-secondary mb-2">
              Description
            </label>
            <textarea
              v-model="formData.description"
              rows="3"
              class="w-full px-3 py-2 bg-surface border border-border text-text rounded-lg focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
              placeholder="Process description"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-text-secondary mb-2">
              Business Category
            </label>
            <select
              v-model="formData.category"
              class="w-full px-3 py-2 bg-surface border border-border text-text rounded-lg focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
            >
              <option value="">Select category</option>
              <option value="customer-service">Customer Service</option>
              <option value="order-processing">Order Processing</option>
              <option value="data-analysis">Data Analysis</option>
            </select>
          </div>
        </form>
      </template>
    </SimpleModal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { Plus } from 'lucide-vue-next'
import SimpleModal from '@/components/common/SimpleModal.vue'
import { useModal } from '@/composables/useModal'

// Modal state
const { show: showCreateModal, open: openCreateModal, close: closeCreateModal, showToast } = useModal()
const isCreating = ref(false)

// Form data
const formData = reactive({
  name: '',
  description: '',
  category: ''
})

// Validation
const isFormValid = computed(() => {
  return formData.name.trim().length > 0 && formData.category
})

// Actions
const handleCreateProcess = async () => {
  if (!isFormValid.value) return
  
  isCreating.value = true
  
  try {
    const response = await fetch('/api/business/processes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: formData.name,
        description: formData.description,
        category: formData.category
      })
    })
    
    if (!response.ok) throw new Error('Failed to create process')
    
    const newProcess = await response.json()
    
    showToast('success', 'Process Created', `"${formData.name}" created successfully`)
    closeCreateModal()
    
    // Reset form
    Object.assign(formData, { name: '', description: '', category: '' })
    
    // Emit or update parent component
    emit('processCreated', newProcess)
    
  } catch (error: any) {
    showToast('error', 'Creation Failed', error.message)
  } finally {
    isCreating.value = false
  }
}

const emit = defineEmits<{
  processCreated: [process: any]
}>()
</script>
```

### **2. DetailModal - Process Information**

#### **Example: Process Details with Tabs**
```vue
<template>
  <div>
    <!-- Trigger -->
    <button @click="openDetailsModal(process.id)" class="btn-control">
      <Info class="h-4 w-4" />
      View Details
    </button>

    <!-- Detail Modal -->
    <DetailModal
      :show="showDetailsModal"
      :title="selectedProcess?.name || 'Process Details'"
      :subtitle="`ID: ${selectedProcessId} • Status: ${selectedProcess?.status || 'Unknown'}`"
      :header-icon="GitBranch"
      :tabs="detailTabs"
      default-tab="overview"
      :is-loading="isLoadingDetails"
      :error="detailsError"
      :data="selectedProcess"
      @close="closeDetailsModal"
      @refresh="refreshProcessDetails"
      @retry="loadProcessDetails"
    >
      <!-- Header Actions -->
      <template #headerActions="{ isLoading }">
        <button
          @click="exportProcess"
          class="p-2 text-text-muted hover:text-green-400 transition-colors"
          title="Export Process"
        >
          <Download class="h-4 w-4" />
        </button>
      </template>

      <!-- Overview Tab -->
      <template #overview="{ data }">
        <div class="p-6 space-y-6">
          <!-- Stats Cards -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="control-card p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm text-text-muted">Total Executions</span>
                <Play class="h-4 w-4 text-gray-600" />
              </div>
              <p class="text-lg font-bold text-text">{{ data?.executionCount || 0 }}</p>
            </div>
            
            <div class="control-card p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm text-text-muted">Success Rate</span>
                <CheckCircle class="h-4 w-4 text-gray-600" />
              </div>
              <p class="text-lg font-bold text-green-400">
                {{ data?.successRate ? `${data.successRate.toFixed(1)}%` : 'N/A' }}
              </p>
            </div>
            
            <div class="control-card p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm text-text-muted">Avg Duration</span>
                <Clock class="h-4 w-4 text-gray-600" />
              </div>
              <p class="text-lg font-bold text-text">
                {{ formatDuration(data?.avgDuration || 0) }}
              </p>
            </div>
          </div>

          <!-- Process Information -->
          <div class="control-card p-6">
            <h3 class="text-lg font-semibold text-text mb-4">Process Information</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-text-muted">Created</span>
                  <span class="text-text">{{ formatDate(data?.createdAt) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-text-muted">Last Updated</span>
                  <span class="text-text">{{ formatDate(data?.updatedAt) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-text-muted">Category</span>
                  <span class="text-text">{{ data?.category || 'Uncategorized' }}</span>
                </div>
              </div>
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-text-muted">Active</span>
                  <span :class="data?.active ? 'text-green-400' : 'text-red-400'">
                    {{ data?.active ? 'Yes' : 'No' }}
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-text-muted">Last Execution</span>
                  <span class="text-text">
                    {{ data?.lastExecution ? formatDate(data.lastExecution) : 'Never' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Performance Tab -->
      <template #performance="{ data }">
        <div class="p-6">
          <div class="control-card p-6">
            <h3 class="text-lg font-semibold text-text mb-4">Performance Metrics</h3>
            
            <!-- Performance chart would go here -->
            <div class="bg-surface p-8 rounded-lg text-center">
              <TrendingUp class="h-12 w-12 text-text-muted mx-auto mb-4" />
              <p class="text-text-muted">Performance chart integration</p>
            </div>
          </div>
        </div>
      </template>

      <!-- Settings Tab -->
      <template #settings="{ data }">
        <div class="p-6">
          <div class="control-card p-6">
            <h3 class="text-lg font-semibold text-text mb-4">Process Settings</h3>
            
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <span class="text-text">Enable Process</span>
                  <p class="text-sm text-text-muted">Allow this process to run automatically</p>
                </div>
                <button
                  @click="toggleProcessStatus"
                  :class="[
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    data?.active ? 'bg-green-600' : 'bg-gray-600'
                  ]"
                >
                  <span
                    :class="[
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      data?.active ? 'translate-x-6' : 'translate-x-1'
                    ]"
                  />
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </DetailModal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Info, GitBranch, Download, Play, CheckCircle, Clock, TrendingUp } from 'lucide-vue-next'
import DetailModal from '@/components/common/DetailModal.vue'
import { useModal } from '@/composables/useModal'

interface Props {
  process: any
}

defineProps<Props>()

// Modal state
const { 
  show: showDetailsModal, 
  isLoading: isLoadingDetails, 
  error: detailsError,
  open: openDetailsModal, 
  close: closeDetailsModal,
  setLoading,
  setError,
  showToast 
} = useModal()

const selectedProcessId = ref<string | null>(null)
const selectedProcess = ref<any>(null)

// Tab configuration
const detailTabs = [
  { id: 'overview', label: 'Overview', icon: Info },
  { id: 'performance', label: 'Performance', icon: TrendingUp },
  { id: 'settings', label: 'Settings', icon: GitBranch }
]

// Actions
const openDetailsModal = async (processId: string) => {
  selectedProcessId.value = processId
  openDetailsModal()
  await loadProcessDetails()
}

const loadProcessDetails = async () => {
  if (!selectedProcessId.value) return
  
  setLoading(true)
  setError(null)
  
  try {
    const response = await fetch(`/api/business/processes/${selectedProcessId.value}`)
    if (!response.ok) throw new Error('Failed to load process details')
    
    const data = await response.json()
    selectedProcess.value = data.data
    
  } catch (error: any) {
    setError(error.message)
  } finally {
    setLoading(false)
  }
}

const refreshProcessDetails = async () => {
  await loadProcessDetails()
  showToast('success', 'Data Refreshed', 'Process details updated')
}

const exportProcess = () => {
  if (!selectedProcess.value) return
  
  const dataStr = JSON.stringify(selectedProcess.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `process-${selectedProcessId.value}-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const toggleProcessStatus = async () => {
  if (!selectedProcess.value) return
  
  try {
    const response = await fetch(`/api/business/processes/${selectedProcessId.value}/toggle`, {
      method: 'POST'
    })
    
    if (!response.ok) throw new Error('Failed to toggle process status')
    
    selectedProcess.value.active = !selectedProcess.value.active
    showToast('success', 'Status Updated', `Process ${selectedProcess.value.active ? 'enabled' : 'disabled'}`)
    
  } catch (error: any) {
    showToast('error', 'Update Failed', error.message)
  }
}

// Utility functions
const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
```

### **3. TimelineModal - Process Execution**

#### **Example: Timeline Integration**
```vue
<template>
  <div>
    <!-- Timeline Button -->
    <button 
      @click="openTimeline(process.id)" 
      class="p-2 text-text-muted hover:text-green-400 transition-colors"
      title="View Process Timeline"
    >
      <Clock class="h-4 w-4" />
    </button>

    <!-- Timeline Modal -->
    <TimelineModal
      v-if="selectedProcessId"
      :workflow-id="selectedProcessId"
      :tenant-id="tenantId"
      :show="showTimelineModal"
      @close="closeTimeline"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Clock } from 'lucide-vue-next'
import TimelineModal from '@/components/common/TimelineModal.vue'

interface Props {
  process: any
  tenantId?: string
}

defineProps<Props>()

// State
const showTimelineModal = ref(false)
const selectedProcessId = ref<string | null>(null)

// Actions
const openTimeline = (processId: string) => {
  selectedProcessId.value = processId
  showTimelineModal.value = true
}

const closeTimeline = () => {
  showTimelineModal.value = false
  selectedProcessId.value = null
}
</script>
```

### **4. Confirm Modal - Actions**

#### **Example: Delete Confirmation**
```vue
<template>
  <div>
    <!-- Delete Button -->
    <button @click="confirmDelete" class="btn-control border-red-500/30 text-red-400 hover:bg-red-500/10">
      <Trash2 class="h-4 w-4" />
      Delete Process
    </button>

    <!-- Confirmation Modal -->
    <SimpleModal
      :show="showDeleteModal"
      title="Delete Business Process"
      submit-text="Delete"
      cancel-text="Cancel"
      :submit-icon="Trash2"
      :is-loading="isDeleting"
      @close="cancelDelete"
      @submit="executeDelete"
    >
      <template #content>
        <div class="space-y-4">
          <div class="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div class="flex items-center gap-2 mb-2">
              <AlertTriangle class="h-5 w-5 text-red-400" />
              <span class="font-medium text-red-400">Warning</span>
            </div>
            <p class="text-sm text-red-300">
              This action cannot be undone. The process and all its execution history will be permanently deleted.
            </p>
          </div>

          <div class="space-y-2">
            <p class="text-text">
              You are about to delete the process:
            </p>
            <div class="p-3 bg-surface rounded-lg border border-border">
              <p class="font-medium text-text">{{ process.name }}</p>
              <p class="text-sm text-text-muted">ID: {{ process.id }}</p>
              <p class="text-sm text-text-muted">
                Created: {{ formatDate(process.createdAt) }}
              </p>
            </div>
          </div>

          <div class="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
            <p class="text-sm text-yellow-300">
              Type the process name to confirm deletion:
            </p>
            <input
              v-model="confirmationText"
              type="text"
              class="mt-2 w-full px-3 py-2 bg-surface border border-border text-text rounded-lg focus:border-red-400 focus:ring-1 focus:ring-red-400"
              :placeholder="process.name"
            />
          </div>
        </div>
      </template>
    </SimpleModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Trash2, AlertTriangle } from 'lucide-vue-next'
import SimpleModal from '@/components/common/SimpleModal.vue'
import { useModal } from '@/composables/useModal'

interface Props {
  process: any
}

const props = defineProps<Props>()

// Modal state
const { show: showDeleteModal, open: openDeleteModal, close: closeDeleteModal, showToast } = useModal()
const isDeleting = ref(false)
const confirmationText = ref('')

// Validation
const canDelete = computed(() => {
  return confirmationText.value === props.process.name
})

// Actions
const confirmDelete = () => {
  confirmationText.value = ''
  openDeleteModal()
}

const cancelDelete = () => {
  confirmationText.value = ''
  closeDeleteModal()
}

const executeDelete = async () => {
  if (!canDelete.value) {
    showToast('warning', 'Confirmation Required', 'Please type the process name to confirm')
    return
  }
  
  isDeleting.value = true
  
  try {
    const response = await fetch(`/api/business/processes/${props.process.id}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) throw new Error('Failed to delete process')
    
    showToast('success', 'Process Deleted', `"${props.process.name}" has been deleted`)
    closeDeleteModal()
    
    emit('processDeleted', props.process.id)
    
  } catch (error: any) {
    showToast('error', 'Deletion Failed', error.message)
  } finally {
    isDeleting.value = false
  }
}

const emit = defineEmits<{
  processDeleted: [processId: string]
}>()

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('it-IT')
}
</script>
```

---

## 🔧 **INTEGRATION CHECKLIST**

### **Before Implementation**
- [ ] **Import components**: SimpleModal, DetailModal, TimelineModal da `/components/common/`
- [ ] **Import composable**: `useModal` da `/composables/useModal`
- [ ] **Import icons**: Lucide Vue Next icons necessarie
- [ ] **Check API endpoints**: Verificare che gli endpoint backend esistano

### **During Implementation**
- [ ] **Props validation**: Definire interfacce TypeScript per props
- [ ] **Error handling**: Implementare try/catch per API calls
- [ ] **Loading states**: Gestire isLoading durante operazioni async
- [ ] **Toast notifications**: Usare showToast per feedback utente
- [ ] **Business terminology**: Usare solo terminologia business, mai tecnica

### **After Implementation**
- [ ] **Test responsive**: Verificare su mobile/tablet/desktop
- [ ] **Test keyboard**: ESC chiude, Enter submit, tab navigation
- [ ] **Test error states**: Simulare errori API e network
- [ ] **Test edge cases**: Dati vuoti, API lente, valori null
- [ ] **Validate accessibility**: Screen reader friendly, focus management

---

## 🎨 **STYLING BEST PRACTICES**

### **Consistent Classes**
```css
/* Modal Containers */
.control-card          /* Standard container */
.btn-control          /* Secondary button */
.btn-control-primary  /* Primary button */

/* Text Colors */
.text-text            /* Primary text */
.text-text-secondary  /* Secondary text */  
.text-text-muted     /* Muted text */

/* Status Colors */
.text-green-400      /* Success */
.text-red-400        /* Error */
.text-yellow-400     /* Warning */
.text-blue-400       /* Info */
```

### **Premium Effects**
```css
/* Add to modal containers */
.premium-modal
.premium-scrollbar
.premium-glass
```

---

**🎯 Usa questi esempi come template per integrare modal nel tuo progetto PilotProOS!**