# tRPC Migration Plan - Complete REST API Migration

## Current REST Endpoints Analysis

### 1. **Business Processes (Workflows)**
- `GET /api/business/processes` - Lista tutti i processi business
- `GET /api/business/process-details/:processId` - Dettagli processo specifico  
- `POST /api/business/toggle-workflow/:workflowId` - ✅ **MIGRATO**
- `POST /api/business/execute-workflow/:workflowId` - ✅ **MIGRATO**  
- `POST /api/business/stop-workflow/:workflowId` - ✅ **MIGRATO**

### 2. **Analytics & Statistics**
- `GET /api/business/analytics` - Analytics generali business
- `GET /api/business/statistics` - Statistiche operative
- `GET /api/business/automation-insights` - Insights automazione
- `GET /api/business/integration-health` - Stato integrazioni

### 3. **Executions (Process Runs)**
- `GET /api/business/process-runs` - Lista esecuzioni processi
- `GET /api/business/process-timeline/:processId` - Timeline processo
- `GET /api/business/process-timeline/:processId/report` - Report timeline

### 4. **Data & Debug**
- `GET /api/business/raw-data-for-modal/:workflowId` - Dati per modal
- `GET /api/business/test-raw-data` - Test dati raw
- `GET /api/debug/execution/:id` - Debug esecuzione
- `GET /api/business/test-drizzle` - Test Drizzle ORM

### 5. **System & Health**
- `GET /health` - Health check sistema
- `GET /api/n8n-icons/:nodeType` - Icone n8n nodes
- `POST /api/business/test-error-notification` - Test notifiche errore

## Migration Strategy

### Phase 1: Core Business Operations ✅ **DONE** 
- `workflow.toggle` ✅
- `workflow.execute` ✅  
- `workflow.stop` ✅

### Phase 2: Business Data Queries (Priority High)
- Create `processes` router
- Create `analytics` router
- Create `executions` router

### Phase 3: System & Utilities (Priority Medium)  
- Create `system` router
- Create `debug` router

### Phase 4: Frontend Migration (Priority High)
- Update all Vue components to use tRPC
- Remove Axios API calls
- Update stores to use tRPC

### Phase 5: Cleanup (Priority Low)
- Remove deprecated REST endpoints
- Update documentation

## tRPC Router Structure

```typescript
export const appRouter = router({
  // ✅ Already implemented
  workflow: workflowRouter,
  
  // 🔄 To implement
  processes: processesRouter,     // Business processes management
  analytics: analyticsRouter,     // Analytics & statistics  
  executions: executionsRouter,   // Process runs & timeline
  system: systemRouter,          // Health, icons, utilities
  debug: debugRouter,            // Debug & testing endpoints
});
```

## Benefits of Complete Migration

1. **Type Safety**: End-to-end TypeScript types for ALL API calls
2. **Developer Experience**: Auto-completion for entire API surface
3. **Request Optimization**: Automatic batching for all requests
4. **Consistent Error Handling**: Unified error management
5. **Schema Validation**: Runtime validation on all endpoints
6. **Business Abstraction**: Consistent terminology across entire API

## Next Steps

1. Analyze each endpoint's input/output schemas
2. Create Zod validation schemas for all endpoints
3. Implement tRPC routers by category
4. Update frontend components progressively
5. Test each migration step
6. Remove deprecated REST endpoints