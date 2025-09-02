<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="control-card w-full max-w-md">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-text">Nuovo Workflow</h3>
            <button
              @click="$emit('close')"
              class="text-text-muted hover:text-text"
            >
              <X class="h-5 w-5" />
            </button>
          </div>

          <form @submit.prevent="createWorkflow" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-text-secondary mb-2">
                Nome Workflow
              </label>
              <input
                v-model="formData.name"
                type="text"
                required
                class="w-full px-3 py-2 bg-surface border border-border text-text placeholder-text-muted rounded-lg focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
                placeholder="Inserisci nome workflow"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-secondary mb-2">
                Descrizione (opzionale)
              </label>
              <textarea
                v-model="formData.description"
                rows="3"
                class="w-full px-3 py-2 bg-surface border border-border text-text placeholder-text-muted rounded-lg focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
                placeholder="Descrizione del workflow"
              />
            </div>

            <div class="flex items-center justify-end gap-3 pt-4">
              <button
                type="button"
                @click="$emit('close')"
                class="btn-control"
              >
                Annulla
              </button>
              <button
                type="submit"
                :disabled="!formData.name || isCreating"
                class="btn-control-primary"
                :class="{ 'opacity-50 cursor-not-allowed': !formData.name || isCreating }"
              >
                <Plus v-if="!isCreating" class="h-4 w-4" />
                <Loader2 v-else class="h-4 w-4 animate-spin" />
                {{ isCreating ? 'Creando...' : 'Crea Workflow' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { X, Plus, Loader2 } from 'lucide-vue-next'
import { useWorkflowsStore } from '../../stores/workflows'
import { useUIStore } from '../../stores/ui'

// Props
interface Props {
  show: boolean
}

defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
  created: [workflow: any]
}>()

// Stores
const workflowsStore = useWorkflowsStore()
const uiStore = useUIStore()

// Local state
const isCreating = ref(false)

const formData = reactive({
  name: '',
  description: ''
})

// Methods
const createWorkflow = async () => {
  if (!formData.name) return
  
  isCreating.value = true
  
  try {
    const newWorkflow = await workflowsStore.createWorkflow({
      name: formData.name,
      description: formData.description
    })
    
    uiStore.showToast('Successo', `Workflow "${formData.name}" creato`, 'success')
    emit('created', newWorkflow)
    emit('close')
    
    // Reset form
    formData.name = ''
    formData.description = ''
    
  } catch (error: any) {
    uiStore.showToast('Errore', 'Impossibile creare workflow', 'error')
  } finally {
    isCreating.value = false
  }
}
</script>

<style scoped>
/* All styles now handled by Design System! */
</style>