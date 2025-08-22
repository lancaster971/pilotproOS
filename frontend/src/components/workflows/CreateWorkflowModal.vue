<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-md">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-white">Nuovo Workflow</h3>
            <button
              @click="$emit('close')"
              class="text-gray-400 hover:text-white"
            >
              <X class="h-5 w-5" />
            </button>
          </div>

          <form @submit.prevent="createWorkflow" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                Nome Workflow
              </label>
              <input
                v-model="formData.name"
                type="text"
                required
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-white placeholder-gray-500 rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none"
                placeholder="Inserisci nome workflow"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                Descrizione (opzionale)
              </label>
              <textarea
                v-model="formData.description"
                rows="3"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-white placeholder-gray-500 rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none"
                placeholder="Descrivi il workflow"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                Tags (opzionali)
              </label>
              <input
                v-model="tagsInput"
                type="text"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-white placeholder-gray-500 rounded-lg focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none"
                placeholder="tag1, tag2, tag3"
              />
              <p class="text-xs text-gray-500 mt-1">Separa i tag con virgole</p>
            </div>

            <div class="flex items-center gap-3 pt-4">
              <button
                type="button"
                @click="$emit('close')"
                class="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Annulla
              </button>
              <button
                type="submit"
                :disabled="isLoading || !formData.name.trim()"
                class="flex-1 bg-green-600 hover:bg-green-700 text-white rounded-lg py-2 px-4 transition-colors flex items-center justify-center gap-2"
                :class="{ 'opacity-50 cursor-not-allowed': isLoading || !formData.name.trim() }"
              >
                <Loader2 v-if="isLoading" class="h-4 w-4 animate-spin" />
                {{ isLoading ? 'Creazione...' : 'Crea Workflow' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, Loader2 } from 'lucide-vue-next'
import { useWorkflowsStore } from '../../stores/workflows'
import type { Workflow } from '../../types'

// Props
interface Props {
  show: boolean
}

defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
  created: [workflow: Workflow]
}>()

// Stores
const workflowsStore = useWorkflowsStore()

// Local state
const isLoading = ref(false)
const formData = ref({
  name: '',
  description: '',
})
const tagsInput = ref('')

// Computed
const tags = computed(() => {
  return tagsInput.value
    .split(',')
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)
})

// Methods
const createWorkflow = async () => {
  isLoading.value = true
  
  try {
    const workflowData = {
      name: formData.value.name,
      tags: tags.value,
      settings: {
        description: formData.value.description,
      },
    }
    
    const newWorkflow = await workflowsStore.createWorkflow(workflowData)
    emit('created', newWorkflow)
    
    // Reset form
    formData.value.name = ''
    formData.value.description = ''
    tagsInput.value = ''
    
  } catch (error: any) {
    console.error('Failed to create workflow:', error)
  } finally {
    isLoading.value = false
  }
}
</script>