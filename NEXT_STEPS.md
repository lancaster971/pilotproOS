# PilotProOS - Next Steps

**Status**: Real-Time Data Integration Phase - Eliminazione TUTTI i dati mock  
**Data**: 2025-08-22  
**Versione**: v1.3.0  

---

## 🎯 **SISTEMA ATTUALE - STATO**

### ✅ **COMPLETATO**

#### **Frontend Vue 3 + TypeScript**
- Stack n8n-compatible: Vue 3.4.21 + TypeScript + Pinia + Vue Router
- 10 Pages complete con routing e navigation
- Parziale integrazione dati reali (Dashboard, Workflows, Executions)

#### **Backend PostgreSQL Integration**
- Database: PostgreSQL dual-schema (n8n + pilotpros)
- 29 workflows reali + 50+ executions nel database
- API endpoints funzionanti:
  - ✅ `/api/business/processes` - Tutti i workflows
  - ✅ `/api/business/process-runs` - Tutte le executions 
  - ✅ `/api/business/analytics` - Analytics aggregati
  - ✅ `/api/business/process-details/:id` - Dettagli processo
  - ✅ `/api/business/integration-health` - Health connections
  - ✅ `/api/business/automation-insights` - Insights avanzati

### ⚠️ **PROBLEMA ATTUALE**
- **6 pagine su 10 usano ancora DATI MOCK/STATICI**
- **NO real-time updates** (solo refresh manuale)
- **NO WebSocket** per notifiche live

---

## 🔴 **PAGINE CON DATI MOCK DA SISTEMARE**

| Pagina | Stato Attuale | Dati Necessari dal DB |
|--------|--------------|----------------------|
| **StatsPage** | Grafici hardcoded | `n8n.execution_entity` aggregati per ora/giorno |
| **SecurityPage** | Mock users/tables | `n8n.user`, `n8n.role`, `pilotpros.audit_logs` |
| **AlertsPage** | Alerts statici | `n8n.execution_entity` WHERE status='error' |
| **SchedulerPage** | Schedule fissi | `n8n.workflow_entity` con CRON triggers |
| **AgentsPage** | Agents statici | `n8n.execution_data` per timeline |
| **DatabasePage** | Info statiche | `information_schema.tables` stats |

---

## 🚀 **PIANO IMPLEMENTAZIONE - REAL-TIME DATA**

### **FASE 1 - Nuovi Endpoint nel server.js (Query dirette PostgreSQL)**

#### **1. Statistics Endpoint**
```javascript
// GET /api/business/statistics
app.get('/api/business/statistics', async (req, res) => {
  // Query executions per day/hour
  const dailyStats = await dbPool.query(`
    SELECT 
      DATE(e."startedAt") as day,
      COUNT(*) as total,
      COUNT(CASE WHEN e.status = 'success' THEN 1 END) as success,
      COUNT(CASE WHEN e.status = 'error' THEN 1 END) as errors,
      AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt"))) as avg_duration
    FROM n8n.execution_entity e
    WHERE e."startedAt" >= NOW() - INTERVAL '30 days'
    GROUP BY DATE(e."startedAt")
    ORDER BY day DESC
  `)
  
  res.json({ daily: dailyStats.rows })
})
```

#### **2. Security Endpoint**
```javascript  
// GET /api/business/security
app.get('/api/business/security', async (req, res) => {
  // Users and roles
  const users = await dbPool.query(`
    SELECT u.id, u.email, u."firstName", u."lastName", 
           u."createdAt", u."lastLogin", r.name as role
    FROM n8n.user u
    LEFT JOIN n8n.role r ON u."globalRoleId" = r.id
    ORDER BY u."createdAt" DESC
  `)
  
  // Audit logs
  const audit = await dbPool.query(`
    SELECT * FROM pilotpros.audit_logs 
    ORDER BY created_at DESC LIMIT 100
  `)
  
  res.json({ users: users.rows, audit: audit.rows })
})
```

#### **3. Alerts Endpoint**
```javascript
// GET /api/business/alerts  
app.get('/api/business/alerts', async (req, res) => {
  // Recent errors
  const errors = await dbPool.query(`
    SELECT 
      e.id, e."workflowId", w.name as workflow_name,
      e."startedAt", e.status, e.mode
    FROM n8n.execution_entity e
    JOIN n8n.workflow_entity w ON e."workflowId" = w.id
    WHERE e.status = 'error' 
    ORDER BY e."startedAt" DESC
    LIMIT 50
  `)
  
  res.json({ alerts: errors.rows })
})
```

#### **4. Schedules Endpoint**  
```javascript
// GET /api/business/schedules
app.get('/api/business/schedules', async (req, res) => {
  // Workflows with CRON triggers
  const scheduled = await dbPool.query(`
    SELECT 
      w.id, w.name, w.active,
      w.nodes::text as nodes_json
    FROM n8n.workflow_entity w
    WHERE w.nodes::text LIKE '%n8n-nodes-base.cron%'
    AND w.active = true
  `)
  
  // Parse CRON expressions from nodes
  const schedules = scheduled.rows.map(w => {
    const nodes = JSON.parse(w.nodes_json)
    const cronNode = nodes.find(n => n.type === 'n8n-nodes-base.cron')
    return {
      workflow_id: w.id,
      workflow_name: w.name,
      cron_expression: cronNode?.parameters?.cronExpression || 'N/A',
      active: w.active
    }
  })
  
  res.json({ schedules })
})
```

#### **5. Database Info Endpoint**
```javascript
// GET /api/business/database-info
app.get('/api/business/database-info', async (req, res) => {
  // Table sizes and stats
  const tables = await dbPool.query(`
    SELECT 
      schemaname, tablename,
      pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
      n_live_tup as row_count
    FROM pg_stat_user_tables
    WHERE schemaname IN ('n8n', 'pilotpros')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
  `)
  
  res.json({ tables: tables.rows })
})
```

#### **6. Agents Timeline Endpoint**
```javascript
// GET /api/tenant/:tenantId/agents/workflow/:workflowId/timeline
app.get('/api/tenant/:tenantId/agents/workflow/:workflowId/timeline', async (req, res) => {
  const { workflowId } = req.params
  
  // Get execution data (execution_data has the details)
  const execution = await dbPool.query(`
    SELECT 
      e.id, e."startedAt", e."stoppedAt",
      ed.data, ed."workflowData",
      w.name as workflow_name
    FROM n8n.execution_entity e
    LEFT JOIN n8n.execution_data ed ON e.id = ed."executionId"
    JOIN n8n.workflow_entity w ON e."workflowId" = w.id  
    WHERE w.id = $1
    ORDER BY e."startedAt" DESC
    LIMIT 1
  `, [workflowId])
  
  if (execution.rows.length === 0) {
    return res.json({ success: false, message: 'No executions found' })
  }
  
  // Parse execution data for timeline
  const data = execution.rows[0]
  const executionData = data.data ? JSON.parse(data.data) : null
  
  res.json({
    success: true,
    data: {
      workflowName: data.workflow_name,
      timeline: parseExecutionToTimeline(executionData)
    }
  })
})
```

---

### **FASE 2 - WebSocket Server per Real-Time Updates**

```javascript
// backend/src/websocket.js
const WebSocket = require('ws')
const wss = new WebSocket.Server({ port: 3002 })

wss.on('connection', (ws) => {
  console.log('New WebSocket client connected')
  
  // Send initial data
  ws.send(JSON.stringify({ 
    type: 'connected', 
    timestamp: new Date() 
  }))
  
  // Setup interval for live updates
  const interval = setInterval(async () => {
    // Query latest executions
    const latest = await dbPool.query(`
      SELECT * FROM n8n.execution_entity 
      ORDER BY "startedAt" DESC LIMIT 1
    `)
    
    ws.send(JSON.stringify({
      type: 'execution_update',
      data: latest.rows[0]
    }))
  }, 5000)
  
  ws.on('close', () => clearInterval(interval))
})
```

---

### **FASE 3 - Frontend: Rimuovere TUTTI i Dati Mock**

#### **StatsPage - Rimuovere dati hardcoded**
```typescript
// Prima (MOCK)
const keyMetrics = computed(() => [
  { label: 'Total Workflows', value: '24', change: '+12%' },
  { label: 'Active Agents', value: '8', change: '+3' }
])

// Dopo (REAL DATA)
const keyMetrics = ref([])

onMounted(async () => {
  const response = await fetch('http://localhost:3001/api/business/statistics')
  const data = await response.json()
  keyMetrics.value = data.metrics
})
```

#### **SecurityPage - Rimuovere mock users**
```typescript
// Prima (MOCK)
const mockTables = [
  { name: 'users', records: 245, size: '1.2 MB' }
]

// Dopo (REAL DATA)
const users = ref([])
const auditLogs = ref([])

onMounted(async () => {
  const response = await fetch('http://localhost:3001/api/business/security')
  const data = await response.json()
  users.value = data.users
  auditLogs.value = data.audit
})
```

---

### **FASE 4 - Auto-Refresh System**

```typescript
// composables/useAutoRefresh.ts
export const useAutoRefresh = (fetchFn: Function, interval: number = 5000) => {
  const isRefreshing = ref(false)
  let intervalId: NodeJS.Timeout
  
  const startRefresh = () => {
    intervalId = setInterval(async () => {
      if (!document.hidden) { // Solo se tab è visibile
        isRefreshing.value = true
        await fetchFn()
        isRefreshing.value = false
      }
    }, interval)
  }
  
  const stopRefresh = () => {
    if (intervalId) clearInterval(intervalId)
  }
  
  onMounted(() => startRefresh())
  onUnmounted(() => stopRefresh())
  
  return { isRefreshing, startRefresh, stopRefresh }
}
```

---

### **FASE 5 - Testing & Optimization**

```bash
# Test all endpoints
curl http://localhost:3001/api/business/statistics
curl http://localhost:3001/api/business/security
curl http://localhost:3001/api/business/alerts
curl http://localhost:3001/api/business/schedules
curl http://localhost:3001/api/business/database-info

# Test WebSocket
wscat -c ws://localhost:3002
```

---

## 📋 **CHECKLIST IMPLEMENTAZIONE**

### **✅ Backend Endpoints Completati**
- [x] `/api/business/processes` - Workflows
- [x] `/api/business/process-runs` - Executions
- [x] `/api/business/analytics` - Analytics
- [x] `/api/business/process-details/:id` - Dettagli
- [x] `/api/business/integration-health` - Health
- [x] `/api/business/automation-insights` - Insights

### **🔴 Backend Endpoints da Implementare**
- [ ] `/api/business/statistics` - Stats per grafici
- [ ] `/api/business/security` - Users e audit logs
- [ ] `/api/business/alerts` - Errori e notifiche
- [ ] `/api/business/schedules` - CRON schedules
- [ ] `/api/business/database-info` - DB stats
- [ ] `/api/tenant/:tenantId/agents/workflow/:workflowId/timeline`
- [ ] WebSocket server su porta 3002

### **🔴 Frontend Pages da Aggiornare**
- [x] Dashboard (partial real data)
- [x] Workflows (real data)
- [x] Executions (real data)
- [ ] Stats (remove hardcoded charts)
- [ ] Security (remove mock users)
- [ ] Alerts (remove static alerts)
- [ ] Scheduler (remove fixed schedules)
- [ ] Agents (add timeline API)
- [ ] Database (add real stats)

### **🔴 Real-Time Features**
- [ ] WebSocket server setup
- [ ] Auto-refresh composable
- [ ] Live notifications
- [ ] Real-time metrics dashboard

---

## 🎯 **NEXT IMMEDIATE ACTIONS**

### **1. Implementare i 6 nuovi endpoints nel server.js**
Aggiungi al file `backend/src/server.js`:
- `/api/business/statistics` 
- `/api/business/security`
- `/api/business/alerts`
- `/api/business/schedules`
- `/api/business/database-info`
- `/api/tenant/:tenantId/agents/workflow/:workflowId/timeline`

### **2. Setup WebSocket Server**
Creare `backend/src/websocket.js` per real-time updates

### **3. Update Frontend Pages**
Rimuovere TUTTI i dati mock da:
- StatsPage
- SecurityPage
- AlertsPage
- SchedulerPage
- AgentsPage
- DatabasePage

### **4. Implementare Auto-Refresh**
Creare composable `useAutoRefresh` e applicare a tutte le pagine

---

**OBIETTIVO FINALE**: Sistema 100% real-time con ZERO dati mock, tutto dal database PostgreSQL condiviso con n8n!