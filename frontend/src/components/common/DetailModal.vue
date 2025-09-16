<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 premium-modal-overlay"
      @click.self="handleClickOutside"
    >
      <div class="w-full max-w-5xl h-[80vh] premium-glass premium-modal-container overflow-hidden flex flex-col premium-float">

        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-800/50 bg-gradient-to-r from-gray-900/50 to-gray-800/30">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-primary/20 border border-primary/40 rounded-lg premium-glow-subtle premium-hover-lift">
              <Icon :icon="headerIcon" class="h-6 w-6 text-primary premium-text-glow" />
            </div>
            <div>
              <h2 class="text-xl font-bold text-white premium-gradient-text">{{ title }}</h2>
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
              class="p-2 text-gray-400 hover:text-primary disabled:text-gray-600 transition-all duration-200 premium-hover-lift rounded-lg hover:bg-gray-800/50"
              :title="isLoading ? 'Aggiornamento...' : 'Aggiorna dati'"
            >
              <Icon icon="lucide:refresh-cw" :class="['h-4 w-4', { 'animate-spin': isLoading }]" />
            </button>

            <button
              @click="$emit('close')"
              class="p-2 text-gray-400 hover:text-red-400 transition-all duration-200 premium-hover-lift rounded-lg hover:bg-red-900/20"
            >
              <Icon icon="lucide:x" class="h-5 w-5" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading && !hasContent" class="flex items-center justify-center p-12 bg-gray-900/30">
          <div class="text-center">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary premium-neon-pulse"></div>
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
          <div v-if="tabs.length > 1" class="flex items-center gap-1 p-3 border-b border-gray-800/50 bg-gradient-to-r from-gray-900/30 to-gray-800/20">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all duration-200 premium-hover-lift',
                activeTab === tab.id
                  ? 'bg-primary text-white premium-glow-intense premium-text-glow'
                  : 'text-gray-400 hover:bg-gray-800/50 hover:text-white'
              ]"
            >
              <component :is="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Tab Content -->
          <div class="overflow-y-auto flex-1 bg-gray-900/20" style="max-height: calc(70vh - 140px);">
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