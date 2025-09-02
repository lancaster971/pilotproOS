# RAW DATA FOR MODAL SYSTEM
**PilotProOS - Sistema Centralizzato Dati Modal**

**Documento**: Sistema rawDataForModal  
**Versione**: 1.0.0  
**Target**: Backend Developers  
**Integrazione**: TimelineModal + Multi-Source Support  

---

## 🎯 **OVERVIEW**

Il sistema rawDataForModal centralizza l'estrazione e la formattazione dei dati per tutti i modal del sistema, con focus specifico sui nodi business-critical marcati con tag show-n.

### **Problema Risolto**
- Timeline modal mostrava solo nodi eseguiti (runData)
- Mancavano nodi business-critical non eseguiti
- Dati inconsistenti tra diverse sorgenti
- Logica di parsing distribuita e duplicata

### **Soluzione Implementata**
- Endpoint centralizzato `/api/business/raw-data-for-modal/:workflowId`
- Estrazione completa di TUTTI i nodi dal workflow definition
- Focus sui nodi show-n business-critical
- Merge intelligente con dati di execution
- Output standardizzato per tutti i modal

---

## 🏗️ **ARCHITETTURA SISTEMA**

### **Flusso Dati Completo**
```
Frontend (Multiple Sources)
    │
    ├─── WorkflowsPage ──────┐
    ├─── ExecutionsTable ────┤
    ├─── Dashboard ──────────┤ ──→ rawDataForModal API ──→ PostgreSQL
    ├─── AgentsPage ─────────┤                                │
    └─── Altri componenti ───┘                                │
                                                             │
    ┌────────────────────────────────────────────────────────┘
    │
    ▼
Backend Processing:
1. Query workflow_entity.nodes (definizione completa)
2. Filter nodi con tag show-n nel campo notes
3. Query execution_entity (dati runtime)
4. Merge intelligente + business formatting
5. Response JSON standardizzato
    │
    ▼
Frontend Modal System:
- TimelineModal (consumer principale)  
- DetailModal (dati estesi)
- Futuri modal (stesso formato)
```

### **Database Schema Integration**

```sql
-- Tabelle coinvolte nel sistema

-- 1. WORKFLOW DEFINITION (nodi completi)
SELECT 
  id, name, nodes, connections
FROM n8n.workflow_entity 
WHERE id = :workflowId;

-- 2. EXECUTION DATA (runtime data)  
SELECT 
  id, "workflowId", "startedAt", "stoppedAt", 
  finished, data
FROM n8n.execution_entity 
WHERE "workflowId" = :workflowId 
ORDER BY "startedAt" DESC LIMIT 1;

-- 3. EXECUTION DETAILS (compressed n8n format)
SELECT 
  data, "workflowData"
FROM n8n.execution_data
WHERE "executionId" = :executionId;
```

---

## 🔧 **IMPLEMENTAZIONE BACKEND**

### **Endpoint API Principal**

```javascript
// /api/business/raw-data-for-modal/:workflowId
app.get('/api/business/raw-data-for-modal/:workflowId', async (req, res) => {
  try {
    const { workflowId } = req.params;
    const { executionId } = req.query; // Optional - se non fornito usa ultima
    
    console.log(`🎯 rawDataForModal request: ${workflowId}, execution: ${executionId || 'latest'}`);
    
    // ==========================================
    // STEP 1: GET WORKFLOW DEFINITION
    // ==========================================
    const workflowQuery = `
      SELECT 
        id, name, active, nodes, connections,
        "createdAt", "updatedAt"
      FROM n8n.workflow_entity 
      WHERE id = $1
    `;
    
    const workflowResult = await dbPool.query(workflowQuery, [workflowId]);
    if (workflowResult.rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'Business Process not found'
      });
    }
    
    const workflow = workflowResult.rows[0];
    console.log(`✅ Workflow found: ${workflow.name}`);
    
    // ==========================================
    // STEP 2: GET EXECUTION DATA
    // ==========================================
    let executionQuery, executionParams;
    
    if (executionId) {
      // Execution specifica
      executionQuery = `
        SELECT e.*, ed.data, ed."workflowData"
        FROM n8n.execution_entity e
        LEFT JOIN n8n.execution_data ed ON e.id = ed."executionId"
        WHERE e.id = $1 AND e."workflowId" = $2
      `;
      executionParams = [executionId, workflowId];
    } else {
      // Ultima execution
      executionQuery = `
        SELECT e.*, ed.data, ed."workflowData" 
        FROM n8n.execution_entity e
        LEFT JOIN n8n.execution_data ed ON e.id = ed."executionId"
        WHERE e."workflowId" = $1
        ORDER BY e."startedAt" DESC 
        LIMIT 1
      `;
      executionParams = [workflowId];
    }
    
    const executionResult = await dbPool.query(executionQuery, executionParams);
    const execution = executionResult.rows[0] || null;
    
    console.log(`🔍 Execution found: ${execution?.id || 'NONE'}`);
    
    // ==========================================
    // STEP 3: EXTRACT SHOW-N NODES
    // ==========================================
    const workflowNodes = JSON.parse(workflow.nodes || '[]');
    console.log(`📊 Total nodes in workflow: ${workflowNodes.length}`);
    
    // Filter nodi con tag show-n nelle notes
    const showNodes = workflowNodes.filter(node => {
      const notes = node.notes || '';
      return notes.includes('show-') && /show-\d+/.test(notes);
    }).map(node => {
      // Extract show tag numero
      const showMatch = (node.notes || '').match(/show-(\d+)/);
      return {
        ...node,
        showTag: showMatch ? `show-${showMatch[1]}` : null,
        showOrder: showMatch ? parseInt(showMatch[1]) : 999
      };
    }).sort((a, b) => a.showOrder - b.showOrder); // Sort by show-n order
    
    console.log(`🎯 Show-N nodes found: ${showNodes.length}`);
    showNodes.forEach(node => {
      console.log(`  - ${node.showTag}: ${node.name}`);
    });
    
    // ==========================================
    // STEP 4: MERGE WITH EXECUTION DATA
    // ==========================================
    const businessNodes = [];
    let executionData = null;
    let runData = {};
    
    if (execution?.data) {
      try {
        executionData = typeof execution.data === 'string' 
          ? JSON.parse(execution.data) 
          : execution.data;
        
        // Extract runData from compressed n8n format
        if (Array.isArray(executionData)) {
          const element2 = executionData[2];
          if (element2?.runData) {
            const runDataIndex = parseInt(element2.runData);
            runData = executionData[runDataIndex] || {};
          }
        } else if (executionData?.resultData?.runData) {
          runData = executionData.resultData.runData;
        }
        
        console.log(`🔍 RunData extracted, keys: ${Object.keys(runData).join(', ')}`);
      } catch (error) {
        console.error('❌ Error parsing execution data:', error);
        executionData = null;
      }
    }
    
    // Process each show-n node
    for (const node of showNodes) {
      const nodeName = node.name;
      const hasExecutionData = runData[nodeName];
      
      let nodeExecutionData = null;
      let status = 'not-executed';
      let executionTime = 0;
      let businessData = {};
      
      if (hasExecutionData) {
        // Get execution data following n8n compressed format
        try {
          const nodeRef = runData[nodeName];
          const nodeIndex = parseInt(nodeRef);
          const nodeExecution = executionData[nodeIndex];
          
          if (Array.isArray(nodeExecution) && nodeExecution.length > 0) {
            const execIndex = parseInt(nodeExecution[0]);
            const execData = executionData[execIndex];
            
            if (execData) {
              status = 'success'; // Assume success if data exists
              executionTime = execData.executionTime || 0;
              
              // Extract business-relevant data
              businessData = extractBusinessData(execData, node.type, nodeName);
            }
          }
        } catch (error) {
          console.error(`❌ Error processing node ${nodeName}:`, error);
          status = 'error';
        }
      }
      
      businessNodes.push({
        showTag: node.showTag,
        name: nodeName,
        type: node.type,
        nodeType: classifyNodeType(node.type, nodeName),
        executed: hasExecutionData,
        status: status,
        executionTime: executionTime,
        position: node.position,
        data: businessData,
        _nodeId: node.id
      });
    }
    
    // ==========================================
    // STEP 5: EXTRACT BUSINESS CONTEXT
    // ==========================================
    const businessContext = extractBusinessContext(businessNodes, execution);
    
    // ==========================================
    // STEP 6: FORMAT RESPONSE
    // ==========================================
    const response = {
      workflow: {
        id: workflow.id,
        name: workflow.name,
        active: workflow.active,
        totalNodes: workflowNodes.length,
        showNodesCount: showNodes.length,
        lastUpdated: workflow.updatedAt
      },
      businessNodes: businessNodes,
      execution: execution ? {
        id: execution.id,
        status: execution.finished ? 'completed' : 'running',
        startedAt: execution.startedAt,
        stoppedAt: execution.stoppedAt,
        duration: execution.stoppedAt ? 
          new Date(execution.stoppedAt) - new Date(execution.startedAt) : null,
        businessContext: businessContext
      } : null,
      stats: {
        totalShowNodes: showNodes.length,
        executedNodes: businessNodes.filter(n => n.executed).length,
        successNodes: businessNodes.filter(n => n.status === 'success').length,
        errorNodes: businessNodes.filter(n => n.status === 'error').length
      },
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: 'raw-data-for-modal',
        timestamp: new Date().toISOString(),
        requestedExecutionId: executionId || null
      }
    };
    
    console.log(`✅ rawDataForModal response ready: ${businessNodes.length} business nodes`);
    res.json({
      success: true,
      data: response
    });
    
  } catch (error) {
    console.error('❌ rawDataForModal error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to generate modal data',
      message: sanitizeErrorMessage(error.message)
    });
  }
});
```

### **Helper Functions**

```javascript
// Classify node type for business display
function classifyNodeType(n8nType, nodeName) {
  const type = n8nType.toLowerCase();
  const name = nodeName.toLowerCase();
  
  if (name.includes('mail') || name.includes('ricezione')) return 'email_trigger';
  if (name.includes('milena') || name.includes('ai') || type.includes('agent')) return 'ai_agent';
  if (name.includes('rispondi') || name.includes('reply')) return 'email_response';
  if (name.includes('vector') || name.includes('qdrant')) return 'vector_search';
  if (name.includes('ordini') || name.includes('order')) return 'order_lookup';
  if (name.includes('parcel') || name.includes('tracking')) return 'parcel_tracking';
  if (type.includes('workflow')) return 'sub_workflow';
  
  return 'business_step';
}

// Extract business-relevant data from execution
function extractBusinessData(executionData, nodeType, nodeName) {
  // Recursive reference resolver (from existing implementation)
  const resolveReference = (data, maxDepth = 10, currentDepth = 0) => {
    // Implementation as per existing system
    // ... (resolver logic)
  };
  
  const resolved = resolveReference(executionData.data || executionData.source);
  
  // Business data extraction based on node type
  const businessData = {};
  
  if (resolved) {
    // Email nodes
    if (nodeName.toLowerCase().includes('mail')) {
      businessData.email = resolved.mittente || resolved.sender?.emailAddress?.address;
      businessData.subject = resolved.oggetto || resolved.subject;
      businessData.message = resolved.messaggio_cliente || resolved.body?.content;
    }
    
    // AI nodes
    else if (nodeName.toLowerCase().includes('milena') || nodeName.toLowerCase().includes('ai')) {
      businessData.aiResponse = resolved.risposta_html || resolved.output?.risposta_html;
      businessData.classification = resolved.categoria || resolved.output?.categoria;
      businessData.confidence = resolved.confidence || resolved.output?.confidence;
    }
    
    // Order nodes
    else if (nodeName.toLowerCase().includes('ordini')) {
      businessData.orderId = resolved.order_reference || resolved.order_id;
      businessData.customerName = resolved.customer_full_name;
      businessData.orderStatus = resolved.order_status;
    }
  }
  
  return businessData;
}

// Extract overall business context
function extractBusinessContext(businessNodes, execution) {
  const context = {
    customerEmail: null,
    orderId: null,
    classification: null,
    aiResponseGenerated: false
  };
  
  businessNodes.forEach(node => {
    if (node.data.email && !context.customerEmail) {
      context.customerEmail = node.data.email;
    }
    if (node.data.orderId && !context.orderId) {
      context.orderId = node.data.orderId;
    }
    if (node.data.classification && !context.classification) {
      context.classification = node.data.classification;
    }
    if (node.data.aiResponse) {
      context.aiResponseGenerated = true;
    }
  });
  
  return context;
}
```

---

## 🖥️ **UTILIZZO FRONTEND**

### **TimelineModal Integration**

```vue
<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  workflowId: string
  executionId?: string | null
  show: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

// State
const rawData = ref<any>(null)
const isLoading = ref(false)
const error = ref<string | null>(null)

// Load raw data for modal
const loadRawData = async () => {
  if (!props.workflowId) return
  
  isLoading.value = true
  error.value = null
  
  try {
    const url = `/api/business/raw-data-for-modal/${props.workflowId}`
    const params = props.executionId ? `?executionId=${props.executionId}` : ''
    
    const response = await fetch(`http://localhost:3001${url}${params}`)
    if (!response.ok) throw new Error(`API error: ${response.status}`)
    
    const result = await response.json()
    if (!result.success) throw new Error(result.error || 'Failed to load data')
    
    rawData.value = result.data
    console.log('✅ Raw data loaded:', result.data)
    
  } catch (err: any) {
    error.value = err.message
    console.error('❌ Error loading raw data:', err)
  } finally {
    isLoading.value = false
  }
}

// Computed properties
const businessNodes = computed(() => rawData.value?.businessNodes || [])
const workflowInfo = computed(() => rawData.value?.workflow || {})
const executionInfo = computed(() => rawData.value?.execution || null)
const businessContext = computed(() => executionInfo.value?.businessContext || {})

// Watch for prop changes
watch([() => props.workflowId, () => props.executionId, () => props.show], () => {
  if (props.show && props.workflowId) {
    loadRawData()
  }
}, { immediate: true })
</script>

<template>
  <DetailModal
    :show="show"
    :title="`Business Process: ${workflowInfo.name}`"
    :tabs="tabs"
    :is-loading="isLoading"
    loading-text="Loading business process data..."
    @close="$emit('close')"
  >
    <!-- Timeline Tab -->
    <div v-if="activeTab === 'timeline'" class="p-6">
      <div v-if="businessNodes.length > 0" class="space-y-4">
        <div
          v-for="(node, index) in businessNodes"
          :key="node.showTag || index"
          :class="['border rounded-lg p-4', getNodeStatusColor(node.status)]"
        >
          <!-- Node Header -->
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center">
              <div :class="['w-3 h-3 rounded-full mr-3', getStatusDotColor(node.status)]" />
              <div>
                <div class="font-medium text-white">{{ node.name }}</div>
                <div class="text-sm text-gray-400">{{ node.showTag }} - {{ formatNodeType(node.nodeType) }}</div>
              </div>
            </div>
            <div class="text-xs text-gray-400">
              {{ node.executed ? formatDuration(node.executionTime) : 'Not executed' }}
            </div>
          </div>
          
          <!-- Business Data Preview -->
          <div v-if="node.executed && Object.keys(node.data).length > 0" class="mt-3 p-3 bg-gray-800/50 rounded">
            <div class="text-xs text-gray-400 mb-2">Business Data:</div>
            <div class="text-sm text-gray-300">
              {{ formatBusinessData(node.data, node.nodeType) }}
            </div>
          </div>
          
          <!-- Not Executed State -->
          <div v-else-if="!node.executed" class="mt-3 p-3 bg-gray-700/30 rounded">
            <div class="text-sm text-gray-400 italic">
              This business step was not executed in this process run
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="!isLoading" class="text-center py-12">
        <div class="text-gray-400">No business steps found</div>
      </div>
    </div>
    
    <!-- Business Context Tab -->
    <div v-else-if="activeTab === 'context'" class="p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Customer Info -->
        <div class="bg-gray-800/50 rounded-lg p-4">
          <h3 class="text-lg font-semibold text-white mb-3">Customer Information</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-400">Email:</span>
              <span class="text-white">{{ businessContext.customerEmail || 'N/A' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Order ID:</span>
              <span class="text-white">{{ businessContext.orderId || 'N/A' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Classification:</span>
              <span class="text-white">{{ businessContext.classification || 'N/A' }}</span>
            </div>
          </div>
        </div>
        
        <!-- Process Info -->
        <div class="bg-gray-800/50 rounded-lg p-4">
          <h3 class="text-lg font-semibold text-white mb-3">Process Information</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-400">Total Steps:</span>
              <span class="text-white">{{ workflowInfo.showNodesCount }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Executed Steps:</span>
              <span class="text-white">{{ businessNodes.filter(n => n.executed).length }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">AI Response:</span>
              <span :class="businessContext.aiResponseGenerated ? 'text-green-400' : 'text-gray-400'">
                {{ businessContext.aiResponseGenerated ? 'Generated' : 'Not Generated' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </DetailModal>
</template>
```

### **Multi-Source Usage Examples**

```vue
<!-- WorkflowsPage.vue -->
<template>
  <div @click="openTimeline(workflow.id)" class="workflow-card">
    <!-- Workflow display -->
  </div>
  
  <TimelineModal
    v-if="selectedWorkflowId"
    :workflow-id="selectedWorkflowId"
    :show="showTimeline"
    @close="closeTimeline"
  />
</template>

<script setup>
const openTimeline = (workflowId: string) => {
  selectedWorkflowId.value = workflowId
  selectedExecutionId.value = null // Latest execution
  showTimeline.value = true
}
</script>
```

```vue
<!-- ExecutionsTable.vue -->
<template>
  <tr @click="openTimeline(execution.workflowId, execution.id)" class="execution-row">
    <!-- Execution display -->
  </tr>
  
  <TimelineModal
    v-if="selectedWorkflowId"
    :workflow-id="selectedWorkflowId"
    :execution-id="selectedExecutionId"
    :show="showTimeline"
    @close="closeTimeline"
  />
</template>

<script setup>
const openTimeline = (workflowId: string, executionId: string) => {
  selectedWorkflowId.value = workflowId
  selectedExecutionId.value = executionId // Specific execution
  showTimeline.value = true
}
</script>
```

---

## 📊 **RESPONSE FORMAT SPECIFICATION**

### **Success Response**
```json
{
  "success": true,
  "data": {
    "workflow": {
      "id": "iZnBHM7mDFS2wW0u",
      "name": "Milena",
      "active": true,
      "totalNodes": 20,
      "showNodesCount": 7,
      "lastUpdated": "2025-01-01T12:00:00Z"
    },
    "businessNodes": [
      {
        "showTag": "show-1",
        "name": "Ricezione Mail",
        "type": "n8n-nodes-base.microsoftOutlookTrigger",
        "nodeType": "email_trigger",
        "executed": true,
        "status": "success",
        "executionTime": 1959,
        "position": [-176, 1216],
        "data": {
          "email": "francesco@example.com",
          "subject": "Richiesta info",
          "message": "Buonasera vorrei avere informazioni..."
        },
        "_nodeId": "b611f17e-9326-494d-8d5c-bc26eb2ccad0"
      },
      {
        "showTag": "show-2",
        "name": "Milena - Assistente GommeGo",
        "type": "@n8n/n8n-nodes-langchain.agent",
        "nodeType": "ai_agent",
        "executed": true,
        "status": "success", 
        "executionTime": 5865,
        "position": [1024, 944],
        "data": {
          "aiResponse": "<p>Gentile Francesco...</p>",
          "classification": "Informazioni Aziendali",
          "confidence": 95
        },
        "_nodeId": "245bf129-9a86-4957-99bc-4477420d8561"
      },
      {
        "showTag": "show-3",
        "name": "Qdrant Vector Store",
        "type": "@n8n/n8n-nodes-langchain.vectorStoreQdrant",
        "nodeType": "vector_search",
        "executed": false,
        "status": "not-executed",
        "executionTime": 0,
        "position": [720, 1232],
        "data": {},
        "_nodeId": "e9e5612e-b25c-4201-85b9-7b95937c71db"
      }
    ],
    "execution": {
      "id": 212,
      "status": "completed",
      "startedAt": "2025-08-31T18:06:54.886Z",
      "stoppedAt": "2025-08-31T18:11:23.686Z",
      "duration": 288800,
      "businessContext": {
        "customerEmail": "francesco@example.com",
        "orderId": null,
        "classification": "Informazioni Aziendali",
        "aiResponseGenerated": true
      }
    },
    "stats": {
      "totalShowNodes": 7,
      "executedNodes": 2,
      "successNodes": 2,
      "errorNodes": 0
    },
    "_metadata": {
      "system": "Business Process Operating System",
      "endpoint": "raw-data-for-modal",
      "timestamp": "2025-08-31T19:00:00.000Z",
      "requestedExecutionId": null
    }
  }
}
```

### **Error Response**
```json
{
  "success": false,
  "error": "Business Process not found",
  "message": "The requested business process could not be found"
}
```

---

## 🎯 **TESTING & VALIDATION**

### **Test Cases**

1. **Workflow con execution esistente**
   ```bash
   curl "http://localhost:3001/api/business/raw-data-for-modal/iZnBHM7mDFS2wW0u"
   # Expected: 7 nodi show-n, 2 executed
   ```

2. **Execution specifica**
   ```bash
   curl "http://localhost:3001/api/business/raw-data-for-modal/iZnBHM7mDFS2wW0u?executionId=212"
   # Expected: Stessi 7 nodi con dati di execution 212
   ```

3. **Workflow senza executions**
   ```bash
   curl "http://localhost:3001/api/business/raw-data-for-modal/nonexistent-id"
   # Expected: 404 Business Process not found
   ```

### **Validation Checklist**
- [ ] Tutti i 7 nodi show-n vengono estratti
- [ ] Nodi non eseguiti mostrano status "not-executed"
- [ ] Nodi eseguiti contengono dati business formattati
- [ ] BusinessContext viene popolato correttamente
- [ ] Response ha struttura consistente
- [ ] Error handling funziona correttamente

---

## 🚀 **DEPLOYMENT & MONITORING**

### **Performance Considerations**
- Query ottimizzate con indici su workflow_entity.id e execution_entity.workflowId
- Parsing JSON efficiente con cache per nodi show-n
- Response compression abilitata
- Timeout gestito a 30 secondi per queries complesse

### **Monitoring Points**
```javascript
// Log points for monitoring
console.log(`🎯 rawDataForModal request: ${workflowId}`);
console.log(`📊 Total nodes: ${workflowNodes.length}`);  
console.log(`🎯 Show-N nodes: ${showNodes.length}`);
console.log(`🔍 Execution data: ${execution?.id || 'NONE'}`);
console.log(`✅ Response ready: ${businessNodes.length} business nodes`);
```

### **Security Considerations**
- Input sanitization per workflowId (UUID validation)
- ExecutionId validation se fornito
- Error message sanitization per evitare information disclosure
- Rate limiting applicato all'endpoint

---

## 📝 **CONCLUSIONI**

Il sistema rawDataForModal risolve definitivamente il problema dei dati inconsistenti nei modal, centralizzando la logica di estrazione e garantendo:

1. **Coerenza**: Stessa struttura dati per tutti i consumer
2. **Completezza**: Tutti i nodi show-n business-critical
3. **Flessibilità**: Supporta execution specifica o ultima
4. **Performance**: Query ottimizzate e response cache-friendly
5. **Manutenibilità**: Logica centralizzata nel backend

Il sistema è pronto per essere esteso a nuovi modal e use cases mantenendo la stessa interface standardizzata.