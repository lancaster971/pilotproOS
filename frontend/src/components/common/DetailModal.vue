<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 premium-modal-overlay"
      @click.self="handleClickOutside"
    >
      <div class="w-full max-w-5xl min-h-[70vh] max-h-[90vh] modal-glassmorphism premium-modal-container overflow-hidden flex flex-col">

        <!-- Header -->
        <div class="modal-header flex items-center justify-between p-4">
          <div class="flex items-center gap-4">
            <div class="modal-icon-box p-3 rounded-lg">
              <Icon :icon="headerIcon" class="h-6 w-6 text-emerald-400" />
            </div>
            <div>
              <h2 class="text-xl font-bold text-white">{{ title }}</h2>
              <div v-if="subtitle || $slots.subtitle" class="flex items-center gap-3 mt-1">
                <slot name="subtitle">
                  <span class="text-sm text-gray-400">{{ subtitle }}</span>
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
              class="p-2 text-gray-400 hover:text-emerald-400 disabled:text-gray-600 transition-all duration-200 rounded-lg hover:bg-white/5"
              :title="isLoading ? 'Aggiornamento...' : 'Aggiorna dati'"
            >
              <Icon icon="lucide:refresh-cw" :class="['h-4 w-4', { 'animate-spin': isLoading }]" />
            </button>

            <button
              @click="$emit('close')"
              class="p-2 text-gray-400 hover:text-red-400 transition-all duration-200 rounded-lg hover:bg-red-500/10"
            >
              <Icon icon="lucide:x" class="h-5 w-5" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading && !hasContent" class="flex items-center justify-center p-12">
          <div class="text-center">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400"></div>
            <p class="mt-4 text-gray-300">{{ loadingText }}</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="p-6 bg-red-900/10 border border-red-500/20 m-4 rounded-lg">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-red-400 premium-text-glow">Errore nel caricamento</h2>
          </div>
          <p class="text-gray-300">{{ error }}</p>
          <div class="mt-4 flex gap-2">
            <button @click="$emit('retry')" class="btn-premium">Riprova</button>
            <button @click="$emit('close')" class="btn-premium-secondary">Chiudi</button>
          </div>
        </div>

        <!-- Content with Tabs -->
        <div v-else class="flex flex-col flex-1">
          <!-- Tabs Navigation -->
          <div v-if="tabs.length > 1" class="modal-tabs flex items-center gap-1 p-3">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all duration-200',
                activeTab === tab.id
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              ]"
            >
              <component :is="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Tab Content -->
          <div class="overflow-y-auto flex-1" style="max-height: calc(85vh - 120px);">
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
/* Glassmorphism Modal Theme - Insights Style */
.modal-glassmorphism {
  background: linear-gradient(135deg,
    rgba(15, 15, 15, 0.95) 0%,
    rgba(20, 20, 20, 0.9) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.modal-header {
  background: linear-gradient(135deg,
    rgba(30, 30, 30, 0.5) 0%,
    rgba(25, 25, 25, 0.3) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.modal-icon-box {
  background: linear-gradient(135deg,
    rgba(16, 185, 129, 0.15) 0%,
    rgba(16, 185, 129, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.1);
}

.modal-tabs {
  background: rgba(20, 20, 20, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

/* Premium Modal Animations */
.premium-modal-overlay {
  animation: modalOverlayFadeIn 0.15s ease-out;
}

.premium-modal-container {
  animation: modalSlideIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalOverlayFadeIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

@keyframes modalSlideIn {
  0% {
    transform: translateY(-20px) scale(0.95);
    opacity: 0;
  }
  100% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

/* Enhanced scrollbar for content */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(17, 24, 39, 0.5);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(16, 185, 129, 0.3);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(16, 185, 129, 0.5);
}
</style>