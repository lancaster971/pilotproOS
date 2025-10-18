<template>
  <MainLayout>
    <div class="rag-manager-page">
      <!-- Tab Navigation -->
      <TabView v-model:activeIndex="activeTab" class="rag-tabs">
        <!-- Tab 1: Upload Documenti -->
        <TabPanel>
          <template #header>
            <div class="tab-header">
              <Icon icon="lucide:upload" />
              <span>Carica Documenti</span>
            </div>
          </template>
          <DocumentUploader @upload-success="onUploadSuccess" />
        </TabPanel>

        <!-- Tab 2: Ricerca Semantica -->
        <TabPanel>
          <template #header>
            <div class="tab-header">
              <Icon icon="lucide:search" />
              <span>Ricerca Intelligente</span>
            </div>
          </template>
          <SemanticSearch />
        </TabPanel>

        <!-- Tab 3: Gestione Documenti -->
        <TabPanel>
          <template #header>
            <div class="tab-header">
              <Icon icon="lucide:file-text" />
              <span>Gestione Documenti</span>
              <Badge v-if="stats?.total_documents" :value="stats.total_documents" severity="info" />
            </div>
          </template>
          <DocumentList ref="documentListRef" />
        </TabPanel>

        <!-- Tab 4: Statistiche -->
        <TabPanel>
          <template #header>
            <div class="tab-header">
              <Icon icon="lucide:bar-chart-3" />
              <span>Statistiche</span>
            </div>
          </template>
          <RAGStatistics :stats="stats" />
        </TabPanel>
      </TabView>

      <!-- Toast per notifiche -->
      <Toast position="top-right" />

      <!-- Confirm Dialog per azioni -->
      <ConfirmDialog />
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Icon } from '@iconify/vue'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Badge from 'primevue/badge'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import { useToast } from 'primevue/usetoast'
import { useRAGStore } from '../stores/rag'
import MainLayout from '../components/layout/MainLayout.vue'

// Import componenti RAG
import DocumentUploader from '../components/rag/DocumentUploader.vue'
import SemanticSearch from '../components/rag/SemanticSearch.vue'
import DocumentList from '../components/rag/DocumentList.vue'
import RAGStatistics from '../components/rag/RAGStatistics.vue'

// Composables
const toast = useToast()
const ragStore = useRAGStore()

// State
const activeTab = ref(0)
const documentListRef = ref<any>(null)

// Computed
const stats = computed(() => ragStore.statistics)

// Methods
const onUploadSuccess = async () => {
  toast.add({
    severity: 'success',
    summary: 'Upload Completato',
    detail: 'Documenti caricati con successo nella base di conoscenza',
    life: 3000
  })

  // Aggiorna statistiche SEMPRE
  await ragStore.fetchStatistics()

  // Aggiorna lista documenti SEMPRE (anche se non visibile ora)
  if (documentListRef.value) {
    documentListRef.value.refresh()
  }

  // Switch automatico al tab Gestione Documenti per vedere il risultato
  activeTab.value = 2
}

// Lifecycle
onMounted(async () => {
  try {
    await ragStore.fetchStatistics()
  } catch (error) {
    console.error('Errore caricamento statistiche:', error)
    toast.add({
      severity: 'warn',
      summary: 'Avviso',
      detail: 'Impossibile caricare le statistiche del sistema',
      life: 5000
    })
  }
})
</script>

<style scoped>
/* Container principale */
[data-theme="vscode"] .rag-manager-page {
  padding: 1.5rem;
  background: var(--vscode-bg-primary);
  min-height: 100vh;
}

/* Tab styles */
[data-theme="vscode"] .rag-tabs {
  background: transparent;
}

[data-theme="vscode"] .rag-tabs :deep(.p-tabview-nav) {
  background: var(--vscode-glass-bg);
  backdrop-filter: var(--vscode-glass-blur);
  border: 1px solid var(--vscode-border);
  border-radius: 8px 8px 0 0;
  padding: 0.5rem;
}

[data-theme="vscode"] .rag-tabs :deep(.p-tabview-header) {
  background: transparent;
}

[data-theme="vscode"] .rag-tabs :deep(.p-tabview-header.p-highlight .p-tabview-nav-link) {
  background: var(--vscode-success);
  color: var(--vscode-text-inverse);
  border-color: transparent;
}

[data-theme="vscode"] .rag-tabs :deep(.p-tabview-nav-link) {
  background: transparent;
  color: var(--vscode-text-muted);
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

[data-theme="vscode"] .rag-tabs :deep(.p-tabview-nav-link:hover) {
  background: var(--vscode-highlight-bg);
  color: var(--vscode-text-inverse);
}

[data-theme="vscode"] .rag-tabs :deep(.p-tabview-panels) {
  background: var(--vscode-glass-bg);
  backdrop-filter: var(--vscode-glass-blur);
  border: 1px solid var(--vscode-border);
  border-top: none;
  border-radius: 0 0 8px 8px;
  padding: 1.5rem;
  min-height: 500px;
}

/* Tab header personalizzato */
[data-theme="vscode"] .tab-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
}

[data-theme="vscode"] .tab-header :deep(.p-badge) {
  margin-left: 0.5rem;
}

/* Responsive */
@media (max-width: 768px) {
  [data-theme="vscode"] .rag-manager-page {
    padding: 1rem;
  }

  [data-theme="vscode"] .rag-tabs :deep(.p-tabview-nav) {
    flex-direction: column;
  }

  [data-theme="vscode"] .tab-header {
    width: 100%;
    justify-content: center;
  }
}

/* Animazioni */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

[data-theme="vscode"] .rag-tabs {
  animation: slideIn 0.3s ease-out both;
}
</style>