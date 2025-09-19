# PilotProOS - n8n Upgrade Troubleshooting Guide

**Documento**: Troubleshooting Upgrade n8n  
**Versione**: 1.0.0  
**Target**: DevOps & Technical Support  

---

## 🚨 **EMERGENCY PROCEDURES**

### **Quick Recovery Commands**
```bash
# EMERGENCY: Rollback to previous n8n version
./scripts/emergency-rollback.sh

# EMERGENCY: Restore database from backup
./scripts/emergency-restore.sh

# EMERGENCY: Check system health
curl http://localhost:3001/health
curl http://localhost:3001/api/system/compatibility/health
```

---

## 🔍 **DIAGNOSTIC PROCEDURES**

### **1. Upgrade Health Check**
```bash
#!/bin/bash
# scripts/diagnose-upgrade.sh - Complete upgrade diagnosis

echo "🔍 PilotProOS n8n Upgrade Diagnosis"
echo "==================================="

# Check container status
echo "📦 Container Status:"
docker ps --filter "name=pilotpros" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

# Check n8n version
echo ""
echo "🎯 n8n Version:"
echo "Container: $(docker exec pilotpros-n8n-dev n8n --version 2>/dev/null || echo 'NOT RUNNING')"
echo "Expected: Latest pulled version"

# Check database connectivity
echo ""
echo "🗄️ Database Status:"
DB_STATUS=$(docker exec $(docker ps -q --filter "name=postgres") psql -U pilotpros_user -d pilotpros_db -c "SELECT 1;" 2>/dev/null && echo "✅ Connected" || echo "❌ Failed")
echo "PostgreSQL: $DB_STATUS"

# Check migration status
echo ""
echo "🔄 Migration Status:"
MIGRATION_COUNT=$(docker exec $(docker ps -q --filter "name=postgres") psql -U pilotpros_user -d pilotpros_db -t -c "SELECT COUNT(*) FROM n8n.migrations;" 2>/dev/null || echo "ERROR")
echo "Total migrations: $MIGRATION_COUNT"

LATEST_MIGRATION=$(docker exec $(docker ps -q --filter "name=postgres") psql -U pilotpros_user -d pilotpros_db -t -c "SELECT name FROM n8n.migrations ORDER BY timestamp DESC LIMIT 1;" 2>/dev/null || echo "ERROR")
echo "Latest migration: $LATEST_MIGRATION"

# Check data preservation
echo ""
echo "📊 Data Preservation:"
WORKFLOWS=$(docker exec $(docker ps -q --filter "name=postgres") psql -U pilotpros_user -d pilotpros_db -t -c "SELECT COUNT(*) FROM n8n.workflow_entity;" 2>/dev/null || echo "ERROR")
CREDENTIALS=$(docker exec $(docker ps -q --filter "name=postgres") psql -U pilotpros_user -d pilotpros_db -t -c "SELECT COUNT(*) FROM n8n.credentials_entity;" 2>/dev/null || echo "ERROR")
echo "Workflows: $WORKFLOWS"
echo "Credentials: $CREDENTIALS"

# Check backend compatibility
echo ""
echo "🔧 Backend Compatibility:"
BACKEND_STATUS=$(curl -s http://localhost:3001/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "UNREACHABLE")
COMPAT_STATUS=$(curl -s http://localhost:3001/api/system/compatibility/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "UNREACHABLE")
echo "Backend: $BACKEND_STATUS"
echo "Compatibility: $COMPAT_STATUS"

# Check n8n API
echo ""
echo "🚀 n8n API Status:"
N8N_STATUS=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows 2>/dev/null | jq -r 'type' 2>/dev/null || echo "UNREACHABLE")
echo "n8n API: $N8N_STATUS"

# Summary
echo ""
echo "📋 DIAGNOSIS SUMMARY:"
if [ "$DB_STATUS" = "✅ Connected" ] && [ "$BACKEND_STATUS" = "healthy" ] && [ "$COMPAT_STATUS" = "healthy" ]; then
    echo "✅ System is healthy after upgrade"
else
    echo "⚠️ Issues detected - see details above"
fi
```

### **2. Migration Analysis**
```sql
-- Check n8n migration history
SELECT 
    name,
    TO_TIMESTAMP(timestamp/1000) as applied_at,
    CASE 
        WHEN timestamp > 1754000000000 THEN 'v1.108+ (Aug 2025)'
        WHEN timestamp > 1750000000000 THEN 'v1.107+ (Jul 2025)'
        WHEN timestamp > 1745000000000 THEN 'v1.106+ (Jun 2025)'
        ELSE 'Legacy'
    END as version_era
FROM n8n.migrations 
ORDER BY timestamp DESC 
LIMIT 20;

-- Check for failed migrations
SELECT 
    schemaname, 
    tablename, 
    attname, 
    atttypid::regtype as data_type
FROM pg_attribute 
JOIN pg_class ON pg_attribute.attrelid = pg_class.oid 
JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid 
WHERE pg_namespace.nspname = 'n8n' 
AND attnum > 0 
AND NOT attisdropped
AND (attname LIKE '%workflow%' OR attname LIKE '%execution%')
ORDER BY tablename, attnum;
```

### **3. Schema Compatibility Check**
```bash
#!/bin/bash
# Check schema compatibility after upgrade

echo "🔍 Schema Compatibility Analysis"
echo "================================"

# Check execution_entity fields (most likely to change)
echo "📋 execution_entity field check:"
EXECUTION_FIELDS=$(docker exec $(docker ps -q --filter "name=postgres") psql -U pilotpros_user -d pilotpros_db -t -c "SELECT column_name FROM information_schema.columns WHERE table_schema = 'n8n' AND table_name = 'execution_entity';" | tr '\n' ',' | sed 's/,$//')
echo "Fields: $EXECUTION_FIELDS"

# Check for critical field changes
if echo "$EXECUTION_FIELDS" | grep -q "workflowId"; then
    echo "✅ Modern format (workflowId found)"
elif echo "$EXECUTION_FIELDS" | grep -q "workflow_id"; then
    echo "✅ Legacy format (workflow_id found)"
else
    echo "❌ Unknown format - field mapping may need update"
fi

# Check workflow_entity fields
echo ""
echo "📋 workflow_entity field check:"
WORKFLOW_FIELDS=$(docker exec $(docker ps -q --filter "name=postgres") psql -U pilotpros_user -d pilotpros_db -t -c "SELECT column_name FROM information_schema.columns WHERE table_schema = 'n8n' AND table_name = 'workflow_entity';" | tr '\n' ',' | sed 's/,$//')
echo "Fields: $WORKFLOW_FIELDS"

# Check for timestamp format
if echo "$WORKFLOW_FIELDS" | grep -q "createdAt"; then
    echo "✅ Modern timestamps (createdAt found)"
elif echo "$WORKFLOW_FIELDS" | grep -q "created_at"; then
    echo "✅ Legacy timestamps (created_at found)"
else
    echo "❌ Unknown timestamp format"
fi
```

---

## 🛠️ **COMMON ISSUES & SOLUTIONS**

### **Issue 1: Backend Returns 0 Workflows After Upgrade**

#### **Symptom:**
```bash
curl http://localhost:3001/api/business/processes
# Returns: {"total": 0, "data": []}
```

#### **Diagnosis:**
```sql
-- Check if workflows exist but are inactive
SELECT COUNT(*) as total_workflows, 
       COUNT(CASE WHEN active = true THEN 1 END) as active_workflows
FROM n8n.workflow_entity;
```

#### **Solution:**
```bash
# Option A: Activate workflows that should be active
UPDATE n8n.workflow_entity SET active = true WHERE name IN ('Important Workflow 1', 'Important Workflow 2');

# Option B: Modify backend to include inactive workflows for debugging
curl "http://localhost:3001/api/business/processes?include_inactive=true"
```

### **Issue 2: "Column does not exist" Errors**

#### **Symptom:**
```
ERROR: column e.workflow_id does not exist
```

#### **Diagnosis:**
```bash
# Check which field format is used
./scripts/check-field-format.sh
```

#### **Solution:**
```bash
# Backend automatically adapts, but if manual fix needed:
# Update field mappings in backend/src/utils/n8n-field-mapper.js

# Force compatibility service refresh
curl -X POST http://localhost:3001/api/system/compatibility/refresh
```

### **Issue 3: Migration Fails or Hangs**

#### **Symptom:**
```
n8n container stuck in "starting" state
Migration logs show timeouts
```

#### **Diagnosis:**
```bash
# Check migration logs
docker logs pilotpros-n8n-dev | grep -i migration

# Check database locks
SELECT pid, usename, application_name, state, query 
FROM pg_stat_activity 
WHERE datname = 'pilotpros_db' AND state != 'idle';
```

#### **Solution:**
```bash
# Option A: Kill blocking queries
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE datname = 'pilotpros_db' AND pid != pg_backend_pid() AND state != 'idle';

# Option B: Increase timeouts
docker exec pilotpros-n8n-dev sh -c "echo 'EXECUTIONS_TIMEOUT=600' >> /home/node/.n8n/.env"

# Option C: Restart with clean slate
docker stop pilotpros-n8n-dev
docker start pilotpros-n8n-dev
```

### **Issue 4: New Tables Not Recognized**

#### **Symptom:**
```
ERROR: relation "n8n.new_table" does not exist
```

#### **Diagnosis:**
```sql
-- Check if new tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'n8n' 
AND table_name LIKE '%data_store%' OR table_name LIKE '%role%';
```

#### **Solution:**
```bash
# Update field mappings to include new tables
# Edit: backend/src/utils/n8n-field-mapper.js

# Add new table mappings:
'1.108.1': {
  data_store: { id: 'id', key: 'key', value: 'value' },
  roles: { id: 'id', name: 'name', scope: 'scope' }
}
```

---

## 📊 **MONITORING & ALERTING**

### **Automated Health Monitoring**
```bash
#!/bin/bash
# cron job: */5 * * * * /opt/pilotpros/scripts/monitor-upgrade-health.sh

HEALTH_STATUS=$(curl -s http://localhost:3001/api/system/compatibility/health | jq -r '.status')
N8N_VERSION=$(curl -s http://localhost:3001/api/system/compatibility | jq -r '.compatibility.version')

if [ "$HEALTH_STATUS" != "healthy" ]; then
    echo "🚨 ALERT: n8n compatibility issues detected"
    echo "Version: $N8N_VERSION"
    echo "Status: $HEALTH_STATUS"
    
    # Send alert (email, Slack, etc.)
    # ./scripts/send-alert.sh "n8n compatibility issue"
fi
```

### **Performance Monitoring Post-Upgrade**
```sql
-- Monitor query performance after upgrade
SELECT 
    query,
    mean_exec_time,
    calls,
    total_exec_time
FROM pg_stat_statements 
WHERE query LIKE '%n8n.%'
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

### **Business Impact Assessment**
```bash
# Check business operations continuity
echo "🎯 Business Impact Assessment:"

# Test critical endpoints
ENDPOINTS=(
    "http://localhost:3001/api/business/processes"
    "http://localhost:3001/api/business/analytics" 
    "http://localhost:3001/health"
)

for endpoint in "${ENDPOINTS[@]}"; do
    RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" "$endpoint")
    STATUS=$(curl -s "$endpoint" | jq -r '.status // "unknown"')
    echo "  $endpoint: ${RESPONSE_TIME}s - $STATUS"
done
```

---

## 📚 **REFERENCE MATERIALS**

### **Version Compatibility Matrix**
```
n8n Version    | PostgreSQL | Backend | Status    | Notes
---------------|------------|---------|-----------|------------------
1.108.1        | ✅         | ✅      | TESTED    | Current (Aug 2025)
1.107.3        | ✅         | ✅      | TESTED    | Previous stable  
1.106.x        | ✅         | ✅      | SUPPORTED | Legacy format
1.105.x        | ✅         | 🔶      | LEGACY    | May need manual fixes
< 1.100        | ❌         | ❌      | NOT SUPPORTED
```

### **Breaking Changes History**
```
v1.108.1: + Data Store tables, + Roles system
v1.107.3: + Test case execution, + User activity tracking
v1.106.x: Field format changes (workflow_id → workflowId)
v1.100.x: Major schema restructure
```

### **Emergency Contacts & Procedures**
```
🚨 Production Issues:
   1. Check /opt/pilotpros/logs/upgrade-issues.log
   2. Run ./scripts/diagnose-upgrade.sh
   3. Contact DevOps team if critical

📞 Escalation Path:
   Level 1: Auto-recovery scripts
   Level 2: Manual troubleshooting (this guide)
   Level 3: Database restore from backup
   Level 4: Complete system rollback
```

---

**🎯 Questo sistema di troubleshooting garantisce risoluzione rapida di qualsiasi problema durante upgrade n8n, mantenendo business continuity e zero data loss.**