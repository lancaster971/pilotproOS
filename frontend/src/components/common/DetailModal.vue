<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="handleClickOutside"
    >
      <div class="w-full max-w-5xl h-[80vh] bg-surface border border-border rounded-xl shadow-2xl overflow-hidden flex flex-col">
        
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-border">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-primary/10 border border-primary/30 rounded-lg">
              <Icon :icon="headerIcon" class="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 class="text-xl font-semibold text-text">{{ title }}</h2>
              <div v-if="subtitle || $slots.subtitle" class="flex items-center gap-3 mt-1">
                <slot name="subtitle">
                  <span class="text-sm text-text-muted">{{ subtitle }}</span>
                </slot>
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            <slot name="headerActions" :isLoading="isLoading" :refresh="handleRefresh"></slot>
            
            <button
              v-if="showRefresh"
              @click="handleRefresh"
              :disabled="isLoading"
              class="p-2 text-text-muted hover:text-primary disabled:text-gray-600 transition-colors"
              :title="isLoading ? 'Aggiornamento...' : 'Aggiorna dati'"
            >
              <Icon icon="lucide:refresh-cw" :class="['h-4 w-4', { 'animate-spin': isLoading }]" />
            </button>
            
            <button
              @click="$emit('close')"
              class="p-2 text-text-muted hover:text-red-400 transition-colors"
            >
              <Icon icon="lucide:x" class="h-5 w-5" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading && !hasContent" class="flex items-center justify-center p-12">
          <div class="text-center">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p class="mt-4 text-text-muted">{{ loadingText }}</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-red-400">Errore nel caricamento</h2>
          </div>
          <p class="text-text-muted">{{ error }}</p>
          <div class="mt-4 flex gap-2">
            <button @click="$emit('retry')" class="btn-control-primary">Riprova</button>
            <button @click="$emit('close')" class="btn-control">Chiudi</button>
          </div>
        </div>

        <!-- Content with Tabs -->
        <div v-else>
          <!-- Tabs Navigation -->
          <div v-if="tabs.length > 1" class="flex items-center gap-1 p-2 border-b border-border bg-gray-900/50">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-all',
                activeTab === tab.id
                  ? 'bg-primary text-white'
                  : 'text-text-secondary hover:bg-surface-hover hover:text-text'
              ]"
            >
              <component :is="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Tab Content -->
          <div class="overflow-y-auto" style="max-height: calc(70vh - 140px);">
            <slot 
              :name="activeTab" 
              :activeTab="activeTab"
              :isLoading="isLoading"
              :error="error"
              :data="data"
            >
              <div class="p-6">
                <slot name="default" :activeTab="activeTab" :data="data"></slot>
              </div>
            </slot>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useModal } from '../../composables/useModal'

export interface Tab {
  id: string
  label: string
  icon: any
}

interface Props {
  show: boolean
  title: string
  subtitle?: string
  headerIcon?: any
  tabs?: Tab[]
  defaultTab?: string
  loadingText?: string
  showRefresh?: boolean
  isLoading?: boolean
  error?: string | null
  data?: any
}

const props = withDefaults(defineProps<Props>(), {
  headerIcon: 'lucide:file-text',
  tabs: () => [],
  loadingText: 'Caricamento dati...',
  showRefresh: true,
  isLoading: false,
  error: null,
  data: null
})

const emit = defineEmits<{
  close: []
  refresh: []
  retry: []
  tabChanged: [tabId: string]
}>()

const { handleClickOutside } = useModal(false)

const activeTab = ref(props.defaultTab || props.tabs[0]?.id || 'default')

const hasContent = computed(() => {
  return props.data !== null || props.error !== null
})

const modalClickOutside = () => {
  handleClickOutside()
  emit('close')
}

const handleRefresh = () => {
  emit('refresh')
}

const changeTab = (tabId: string) => {
  activeTab.value = tabId
  emit('tabChanged', tabId)
}
</script>

<style scoped>
/* Minimal styles - no animations per performance requirements */
</style>