# REST Endpoint Cleanup Plan

## Endpoint da rimuovere (tutti migrati a tRPC):

### ✅ Migrati a `system` router:
- `GET /api/n8n-icons/:nodeType` → `system.getNodeIcon`
- `GET /health` → `system.health`
- `GET /api/debug/execution/:id` → `system.debugExecution`
- `GET /api/business/test-raw-data` → `system.getTestRawData`
- `POST /api/business/test-error-notification` → `system.testErrorNotification`
- `GET /api/business/test-drizzle` → `system.testDrizzle`

### ✅ Migrati a `processes` router:
- `GET /api/business/processes` → `processes.getAll`
- `GET /api/business/process-details/:processId` → `processes.getDetails`

### ✅ Migrati a `analytics` router:
- `GET /api/business/analytics` → `analytics.getOverview`
- `GET /api/business/statistics` → `analytics.getStatistics`
- `GET /api/business/automation-insights` → `analytics.getAutomationInsights`
- `GET /api/business/integration-health` → `analytics.getIntegrationHealth`

### ✅ Migrati a `executions` router:
- `GET /api/business/process-runs` → `executions.getProcessRuns`
- `GET /api/business/process-timeline/:processId` → `executions.getProcessTimeline`
- `GET /api/business/raw-data-for-modal/:workflowId` → `executions.getRawDataForModal`
- `GET /api/business/process-timeline/:processId/report` → `executions.getTimelineReport`

### ✅ Migrati a `workflow` router:
- `POST /api/business/toggle-workflow/:workflowId` → `workflow.toggle`
- `POST /api/business/execute-workflow/:workflowId` → `workflow.execute`  
- `POST /api/business/stop-workflow/:workflowId` → `workflow.stop`

## Totale: 19 endpoint REST da rimuovere

## Strategia di cleanup:
1. Backup del file server.js attuale
2. Rimozione graduale degli endpoint in gruppi
3. Test dopo ogni gruppo rimosso
4. Cleanup di imports/middleware inutilizzati
5. Test finale del sistema

## Note di sicurezza:
- Mantenere gli endpoint tRPC intatti
- Non toccare il middleware di sicurezza essenziale
- Preservare la configurazione WebSocket
- Mantenere il setup del database