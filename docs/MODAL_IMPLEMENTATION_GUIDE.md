# MODAL IMPLEMENTATION GUIDE
**PilotProOS - Complete Modal Development Reference**

**Documento**: Guida Completa Implementazione Modal  
**Versione**: 1.0.0  
**Target**: Sviluppatori Frontend  
**Integrazione**: CLAUDE.md Guidelines Compliance  

---

## 🎯 **OVERVIEW**

Questa guida documenta i pattern completi per implementare modal nel sistema PilotProOS, basata sull'analisi dei modal esistenti e l'integrazione con le linee guida CLAUDE.md.

**Principi Fondamentali**:
- **Business Language Only**: Mai esporre terminologia tecnica (n8n, PostgreSQL)
- **Design System Compliance**: Usare classi `control-card`, `btn-control`, colori semantici
- **Vue 3 Best Practices**: Composition API, TypeScript, reactive patterns
- **Premium UX**: Glassmorphism, animazioni, micro-interazioni

---

## 📚 **MODAL TYPES IDENTIFICATI**

### **1. SimpleModal** 
*Pattern: CreateWorkflowModal.vue*

**Use Case**: Form-based modals per creazione/editing
```vue
<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="control-card w-full max-w-md">
        <!-- Header -->
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-text">{{ title }}</h3>
            <button @click="$emit('close')" class="text-text-muted hover:text-text">
              <X class="h-5 w-5" />
            </button>
          </div>

          <!-- Form Content -->
          <form @submit.prevent="handleSubmit" class="space-y-4">
            <!-- Form fields here -->
            
            <!-- Footer Actions -->
            <div class="flex items-center justify-end gap-3 pt-4">
              <button type="button" @click="$emit('close')" class="btn-control">
                Annulla
              </button>
              <button type="submit" :disabled="isLoading" class="btn-control-primary">
                {{ submitLabel }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>
```

### **2. DetailModal**
*Pattern: WorkflowDetailModal.vue*

**Use Case**: Multi-tab modal per visualizzazione dati complessi
```vue
<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="w-full max-w-6xl max-h-[90vh] bg-gray-900 border border-green-500/30 rounded-xl shadow-2xl overflow-hidden">
        
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-border">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <component :is="iconComponent" class="h-6 w-6 text-green-400" />
            </div>
            <div>
              <h2 class="text-xl font-semibold text-text">{{ title }}</h2>
              <div class="flex items-center gap-3 mt-1">
                <!-- Metadata badges -->
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            <!-- Action buttons -->
            <button @click="$emit('close')" class="p-2 text-text-muted hover:text-red-400">
              <X class="h-5 w-5" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center p-12">
          <div class="text-center">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
            <p class="mt-4 text-text-muted">{{ loadingText }}</p>
          </div>
        </div>

        <!-- Content -->
        <div v-else>
          <!-- Tabs Navigation -->
          <div class="flex items-center gap-1 p-2 border-b border-border bg-gray-900/50">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-all',
                activeTab === tab.id
                  ? 'bg-green-500 text-text'
                  : 'text-text-secondary hover:bg-surface hover:text-text'
              ]"
            >
              <component :is="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Tab Content -->
          <div class="overflow-y-auto" style="max-height: calc(90vh - 200px);">
            <!-- Tab content here -->
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
```

### **3. TimelineModal**
*Pattern: AgentDetailModal.vue*

**Use Case**: Business process timeline con focus sui nodi show-n business-critical

**Key Features**:
- **rawDataForModal API**: Endpoint backend specializzato per estrazione dati show-n
- **Multi-Source Support**: Supporta chiamate da workflow, executions, dashboard
- **Business Data Parsing**: Funzione `humanizeStepData()` per convertire JSON tecnici
- **Show-N Focus**: Mostra solo i nodi business-critical marcati con tag show-n
- **Execution Flexibility**: Supporta execution specifica o ultima available
- **Real-time Refresh**: Force refresh da backend con dati sempre coerenti

```vue
<!-- Timeline Tab Content -->
<div v-if="activeTab === 'timeline'" class="p-6">
  <!-- Timeline Steps -->
  <div v-if="timelineData?.timeline?.length > 0" class="space-y-4">
    <div
      v-for="(step, index) in timelineData.timeline"
      :key="step.nodeId || index"
      :class="['border rounded-lg p-4', getStepColor(step.status)]"
    >
      <div 
        class="flex items-center justify-between cursor-pointer"
        @click="toggleExpanded(step.nodeId || index)"
      >
        <div class="flex items-center">
          <component :is="getStepIcon(step.status)" class="w-4 h-4 mr-3" />
          <div>
            <div class="font-medium text-white">{{ step.nodeName || `Step ${index + 1}` }}</div>
            <div class="text-sm text-gray-400">{{ step.summary || 'Execution step' }}</div>
          </div>
        </div>
        <div class="flex items-center">
          <span class="text-xs text-gray-400 mr-3">
            {{ formatDuration(step.executionTime || 0) }}
          </span>
          <ChevronDown v-if="expandedStep === (step.nodeId || index)" class="w-4 h-4 text-gray-400" />
          <ChevronRight v-else class="w-4 h-4 text-gray-400" />
        </div>
      </div>

      <!-- Expanded Step Details -->
      <div v-if="expandedStep === (step.nodeId || index)" class="mt-4 pt-4 border-t border-gray-700">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Input Data -->
          <div>
            <div class="text-sm font-medium text-white mb-2">Input:</div>
            <div class="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
              {{ humanizeStepData(step.inputData, 'input', step.nodeType, step.nodeName) }}
            </div>
          </div>
          
          <!-- Output Data -->
          <div>
            <div class="text-sm font-medium text-white mb-2">Output:</div>
            <div class="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
              {{ humanizeStepData(step.outputData, 'output', step.nodeType, step.nodeName) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

## 🎨 **DESIGN SYSTEM PATTERNS**

### **Colori e Styling**
```css
/* Modal Container */
.modal-container {
  @apply w-full max-w-6xl max-h-[90vh] bg-gray-900 border border-green-500/30 rounded-xl shadow-2xl overflow-hidden;
}

/* Step Status Colors */
.step-success { @apply border-green-400/30 bg-green-400/5; }
.step-error { @apply border-red-400/30 bg-red-400/5; }
.step-running { @apply border-yellow-400/30 bg-yellow-400/5; }
.step-not-executed { @apply border-gray-600/30 bg-gray-800/50; }

/* Premium Effects */
.premium-modal {
  backdrop-filter: blur(25px) saturate(200%);
  background: rgba(17, 24, 39, 0.95);
  box-shadow: 
    0 40px 80px rgba(0, 0, 0, 0.3),
    0 1px 0 rgba(255, 255, 255, 0.1) inset,
    0 0 40px rgba(16, 185, 129, 0.2);
}
```

### **Icon Mapping per Step Status**
```javascript
const getStepIcon = (status: string) => {
  switch (status) {
    case 'success': return CheckCircle
    case 'error': return XCircle  
    case 'running': return Settings
    case 'not-executed': return Clock
    default: return Clock
  }
}
```

---

## 🧠 **BUSINESS DATA PARSING**

### **Funzione `humanizeStepData()`**

Questa funzione è il cuore della business transformation dei dati:

```javascript
const humanizeStepData = (data: any, dataType: 'input' | 'output', nodeType?: string, nodeName?: string): string => {
  // Sanitizzazione terminologia tecnica
  const sanitizedType = nodeType?.replace(/n8n/gi, 'WFEngine').replace(/\.nodes\./g, '.engine.')
  
  if (!data) return 'Nessun dato disponibile'

  const processData = Array.isArray(data) ? data[0] : data
  const insights: string[] = []
  
  // Parser specifici per tipo di nodo
  const nodeNameLower = nodeName?.toLowerCase() || ''
  
  // 1. EMAIL NODES
  if (nodeNameLower.includes('mail') || nodeNameLower.includes('ricezione')) {
    insights.push('--- EMAIL RICEVUTA ---')
    
    if (processData.json?.oggetto || processData.json?.subject) {
      insights.push(`Oggetto: "${processData.json?.oggetto || processData.json?.subject}"`)
    }
    
    // Mittente parsing
    const sender = processData.json?.mittente || processData.sender?.emailAddress?.address
    if (sender) insights.push(`Da: ${sender}`)
    
    // Contenuto email parsing
    const emailBody = processData.json?.messaggio_cliente || processData.json?.body?.content
    if (emailBody) {
      const cleanContent = emailBody.replace(/<[^>]+>/g, ' ').trim()
      const preview = cleanContent.substring(0, 150)
      insights.push(`Messaggio: "${preview}${preview.length >= 150 ? '...' : ''}"`)
    }
  }
  
  // 2. AI NODES
  else if (nodeNameLower.includes('milena') || nodeNameLower.includes('ai')) {
    insights.push('--- RISPOSTA AI GENERATA ---')
    
    const aiResponse = processData.json?.output?.risposta_html || processData.json?.ai_response
    if (aiResponse) {
      const cleanResponse = aiResponse.replace(/<[^>]+>/g, ' ').trim()
      const preview = cleanResponse.substring(0, 200)
      insights.push(`Risposta: "${preview}${preview.length >= 200 ? '...' : ''}"`)
    }
    
    if (processData.json?.categoria) {
      insights.push(`Categoria: ${processData.json.categoria}`)
    }
  }
  
  // 3. ORDER NODES
  else if (nodeNameLower.includes('ordini') || nodeNameLower.includes('order')) {
    insights.push('--- DATI ORDINE RECUPERATI ---')
    
    if (processData.json?.order_reference) {
      insights.push(`Riferimento: ${processData.json.order_reference}`)
    }
    if (processData.json?.customer_full_name) {
      insights.push(`Cliente: ${processData.json.customer_full_name}`)
    }
  }
  
  return insights.length > 0 ? insights.join('\n') : 'Dati complessi - espandi per dettagli'
}
```

---

## 🔄 **STATE MANAGEMENT PATTERNS**

### **Modal Visibility Control**
```javascript
// Standard pattern per tutti i modal
const showModal = ref(false)
const isLoading = ref(false)
const error = ref<string | null>(null)

// Apertura modal
const openModal = (data?: any) => {
  if (data) {
    // Set initial data
  }
  showModal.value = true
}

// Chiusura modal
const closeModal = () => {
  showModal.value = false
  // Reset state if needed
}

// Error handling
const handleError = (err: any) => {
  error.value = err.message
  isLoading.value = false
}
```

### **API Integration Pattern**
```javascript
const loadData = async () => {
  isLoading.value = true
  error.value = null
  
  try {
    const response = await fetch(`/api/business/data/${id}`)
    if (!response.ok) throw new Error(`API error: ${response.status}`)
    
    const data = await response.json()
    // Process and set data
    
  } catch (err: any) {
    handleError(err)
  } finally {
    isLoading.value = false
  }
}
```

---

## 🎯 **TODO CHECKLIST IMPLEMENTAZIONE**

### **Phase 1: Setup Base Modal**
- [ ] Create base modal component con Teleport
- [ ] Implement backdrop blur + glassmorphism
- [ ] Add header con title + close button
- [ ] Setup loading/error states
- [ ] Add premium entrance animations

### **Phase 2: Content Structure**
- [ ] Implement tab system per modal complessi  
- [ ] Create scrollable content area
- [ ] Add footer actions con btn-control classes
- [ ] Implement responsive breakpoints

### **Phase 3: Business Logic**
- [ ] Add API integration con error handling
- [ ] Implement data transformation layer
- [ ] Create business language parser
- [ ] Add real-time refresh functionality

### **Phase 4: Timeline Features**
- [ ] Implement timeline step visualization
- [ ] Add expandable step details
- [ ] Create status-based color coding
- [ ] Add business context parsing

### **Phase 5: UX Polish**
- [ ] Add micro-interactions
- [ ] Implement keyboard navigation
- [ ] Add export functionality
- [ ] Create mobile-responsive layout

### **Phase 6: Integration**
- [ ] Connect to Pinia stores
- [ ] Integrate con UI toast system
- [ ] Add to route navigation
- [ ] Update CLAUDE.md compliance

---

---

## 🎯 **NUOVO SISTEMA: rawDataForModal**

### **Architettura rawDataForModal**

Il nuovo sistema centralizza l'estrazione dati attraverso un singolo endpoint backend che:

1. **Estrae definizione workflow** dalla tabella `workflow_entity.nodes`
2. **Identifica nodi show-n** dal campo `notes` di ogni nodo 
3. **Recupera dati execution** dalla tabella `execution_entity` 
4. **Merge intelligente** tra definizione e dati runtime
5. **Output business-friendly** con solo i nodi critici

### **Endpoint API**
```javascript
GET /api/business/raw-data-for-modal/:workflowId?executionId=optional
```

**Response Structure**:
```json
{
  "workflow": {
    "id": "iZnBHM7mDFS2wW0u",
    "name": "Milena",
    "totalNodes": 20,
    "showNodesCount": 7
  },
  "businessNodes": [
    {
      "showTag": "show-1",
      "name": "Ricezione Mail", 
      "nodeType": "email_trigger",
      "executed": true,
      "status": "success",
      "executionTime": 1959,
      "data": {
        "email": "francesco@...",
        "subject": "Richiesta info",
        "message": "Buonasera vorrei..."
      }
    }
  ],
  "execution": {
    "id": 212,
    "status": "completed",
    "startedAt": "2025-08-31T18:06:54.886Z",
    "businessContext": {
      "customerEmail": "francesco@...",
      "orderId": null,
      "classification": "Informazioni Aziendali"
    }
  }
}
```

### **Multi-Source Timeline Modal**

Il TimelineModal può essere chiamato da più sorgenti:

| Sorgente | Parametri | Comportamento |
|----------|-----------|---------------|
| **WorkflowsPage** | `workflowId` | Mostra ultima execution |
| **ExecutionsTable** | `workflowId + executionId` | Mostra execution specifica |
| **Dashboard** | `workflowId + executionId` | Mostra execution specifica |
| **AgentsPage** | `workflowId` | Mostra ultima execution |

### **Garanzia di Coerenza**

**Struttura sempre identica**:
- Stessi 7 nodi show-n per il workflow Milena
- Dati execution variabili per ogni run
- Parsing business identico per tutti i casi d'uso

**Formula**: `rawDataForModal = nodi_show_n (FISSI) + dati_execution (VARIABILI)`

### **Backend Implementation**

```javascript
// Backend query pattern
app.get('/api/business/raw-data-for-modal/:workflowId', async (req, res) => {
  const { workflowId } = req.params;
  const { executionId } = req.query;
  
  // 1. Get workflow definition
  const workflowQuery = `
    SELECT name, nodes FROM n8n.workflow_entity WHERE id = $1
  `;
  
  // 2. Get execution data (specific or latest)
  const executionQuery = executionId 
    ? `SELECT * FROM n8n.execution_entity WHERE id = $1`
    : `SELECT * FROM n8n.execution_entity WHERE workflowId = $1 ORDER BY startedAt DESC LIMIT 1`;
  
  // 3. Extract show-n nodes from workflow.nodes JSON
  const showNodes = workflowNodes.filter(node => 
    node.notes && node.notes.includes('show-')
  );
  
  // 4. Merge with execution data
  // 5. Format business-friendly output
  
  res.json(rawDataForModal);
});
```

### **Frontend Usage**

```vue
<template>
  <TimelineModal
    v-if="selectedWorkflowId"
    :workflow-id="selectedWorkflowId"
    :execution-id="selectedExecutionId"
    :show="showModal"
    @close="closeModal"
  />
</template>

<script setup>
// Modal può essere chiamato da qualsiasi componente
const openTimeline = (workflowId: string, executionId?: string) => {
  selectedWorkflowId.value = workflowId
  selectedExecutionId.value = executionId // opzionale
  showModal.value = true
}
</script>
```

---

## 📋 **INTEGRATION CON CLAUDE.MD**

### **Terminologia Business**
- ✅ **Mai usare**: n8n, PostgreSQL, workflow, execution, node
- ✅ **Sempre usare**: Process, Business Process, Process Run, Process Step
- ✅ **Pattern**: "Business Process Automation" invece di "Workflow Engine"
- ✅ **Show-N Nodes**: "Business-Critical Steps" nella UI

### **Code Style Compliance**
- ✅ **Vue 3 Composition API** con TypeScript
- ✅ **Design System Classes**: `control-card`, `btn-control`, semantic colors
- ✅ **No Comments**: Solo codice, no spiegazioni inline
- ✅ **Premium UX**: Glassmorphism, animazioni, micro-interazioni

### **Architecture Patterns**  
- ✅ **Clean Separation**: Business layer nasconde tecnologia
- ✅ **API Middleware**: Backend traduce da tecnico a business
- ✅ **State Management**: Pinia stores con terminologia business
- ✅ **Error Handling**: User-friendly messages, no technical details

---

## 🎯 **IMPLEMENTED COMPONENTS**

### **Core Components Created**
1. **`useModal.ts`** - Composable per logica condivisa modal
2. **`useBusinessParser.ts`** - Parser business data da dati tecnici
3. **`SimpleModal.vue`** - Modal base per form e azioni semplici
4. **`DetailModal.vue`** - Modal complesso con sistema tabs
5. **`TimelineModal.vue`** - Modal specializzato per timeline business

### **Integration Files**
- **`MODAL_INTEGRATION_EXAMPLES.md`** - Esempi pratici di utilizzo
- **File path**: `/frontend/src/components/common/` per tutti i modal
- **Composables path**: `/frontend/src/composables/` per logica condivisa

### **Key Features Implemented**
- ✅ **Business Data Parsing**: Conversione automatica da JSON tecnico a linguaggio business
- ✅ **Timeline Visualization**: Steps expandibili con parsing intelligente
- ✅ **Force Refresh**: Aggiornamento real-time da backend
- ✅ **Premium Animations**: Glassmorphism + entrance/exit effects
- ✅ **Error Handling**: User-friendly error states
- ✅ **Responsive Design**: Mobile/tablet/desktop support
- ✅ **Keyboard Navigation**: ESC/Enter/Tab support
- ✅ **TypeScript**: Type safety completo

---

## 🚀 **NEXT STEPS**

1. **Usa questo documento** come riferimento per ogni implementazione modal
2. **Segui i pattern** esatti dei modal esistenti  
3. **Mantieni business language** in tutto il UI
4. **Testa real-time refresh** e error states
5. **Valida responsive design** su tutti i breakpoints

**Questo documento è la guida completa per implementare modal che rispettano gli standard PilotProOS e le linee guida CLAUDE.md.**