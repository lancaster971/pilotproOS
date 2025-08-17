# PilotProOS - PostgreSQL Configuration

**Documento**: Configurazione n8n con PostgreSQL  
**Versione**: 1.0.0  
**Target**: DevOps & Technical Implementation  

---

## 🎯 **OVERVIEW: n8n + PostgreSQL Integration**

### **Obiettivo Strategico**
Configurare **n8n workflow engine** per utilizzare **PostgreSQL** come database backend invece del default SQLite, permettendo:

- **🔄 Database condiviso**: n8n + PilotProOS usano stesso PostgreSQL
- **📊 Query unificate**: Analytics cross-schema per business insights
- **⚡ Performance enterprise**: Concurrent access, complex queries
- **🛡️ Security & Backup**: Enterprise-grade data management
- **📈 Scalability**: Supporto per milioni di workflow executions

### **Architettura Database Condivisa**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POSTGRESQL DATABASE                                 │
│                        pilotpros_db (port 5432)                            │
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────────┐ │
│  │          SCHEMA: n8n            │  │       SCHEMA: pilotpros             │ │
│  │      (n8n ownership)            │  │    (PilotProOS ownership)           │ │
│  │                                 │  │                                     │ │
│  │ • workflow_entity               │  │ • business_analytics                │ │
│  │ • execution_entity              │  │ • users                             │ │
│  │ • credentials_entity            │  │ • process_templates                 │ │
│  │ • settings                      │  │ • audit_logs                        │ │
│  │ • tag_entity                    │  │ • chat_conversations                │ │
│  │ • webhook_entity                │  │ • ai_agent_sessions                 │ │
│  │ • workflow_statistics           │  │                                     │ │
│  └─────────────────────────────────┘  └─────────────────────────────────────┘ │
│              ▲                                           ▲                  │
│              │ n8n Direct Access                         │ PilotProOS API   │
│              │ (read/write)                              │ (read/write)     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    CROSS-SCHEMA VIEWS                                   │ │
│  │          (Business Analytics & Reporting)                               │ │
│  │                                                                         │ │
│  │ • business_process_summary (n8n.workflow + pilotpros.analytics)        │ │
│  │ • execution_business_view (n8n.execution + business context)           │ │
│  │ • performance_dashboard (aggregated metrics)                           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ▲
                  ┌───────────────────┼───────────────────┐
                  │                   │                   │
            ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
            │ n8n Server│      │PilotProOS │      │ AI Agent  │
            │Port: 5678 │      │Backend    │      │   MCP     │
            │(internal) │      │Port: 3001 │      │Integration│
            └───────────┘      └───────────┘      └───────────┘
```

---

## ⚙️ **n8n PostgreSQL Configuration**

### **Environment Variables Setup**

```bash
#!/bin/bash
# PostgreSQL configuration for n8n

# Database connection parameters
export DB_TYPE=postgresdb
export DB_POSTGRESDB_HOST=localhost
export DB_POSTGRESDB_PORT=5432
export DB_POSTGRESDB_DATABASE=pilotpros_db
export DB_POSTGRESDB_USER=pilotpros_user
export DB_POSTGRESDB_PASSWORD=secure_database_password
export DB_POSTGRESDB_SCHEMA=n8n

# n8n server configuration  
export N8N_PORT=5678
export N8N_HOST=127.0.0.1

# Security configuration
export N8N_BASIC_AUTH_ACTIVE=true
export N8N_BASIC_AUTH_USER=admin
export N8N_BASIC_AUTH_PASSWORD=secure_admin_password

# Webhook configuration
export WEBHOOK_URL=https://client-domain.com
export N8N_PAYLOAD_SIZE_MAX=16

# Performance optimization
export EXECUTIONS_TIMEOUT=300
export EXECUTIONS_TIMEOUT_MAX=3600
export N8N_METRICS=true

# Disable telemetry (privacy)
export N8N_DIAGNOSTICS_ENABLED=false
export N8N_VERSION_NOTIFICATIONS_ENABLED=false

echo "✅ n8n PostgreSQL environment configured"
```

### **Docker Container Configuration**

```bash
#!/bin/bash
# n8n container with PostgreSQL

# Load database credentials
source /opt/pilotpros/.env.database

# Deploy n8n container configured for PostgreSQL
docker run -d \
  --name pilotpros-n8n \
  --restart unless-stopped \
  --network host \
  -e DB_TYPE=postgresdb \
  -e DB_POSTGRESDB_HOST=localhost \
  -e DB_POSTGRESDB_PORT=5432 \
  -e DB_POSTGRESDB_DATABASE=pilotpros_db \
  -e DB_POSTGRESDB_USER=pilotpros_user \
  -e DB_POSTGRESDB_PASSWORD="$DB_PASSWORD" \
  -e DB_POSTGRESDB_SCHEMA=n8n \
  -e N8N_PORT=5678 \
  -e N8N_HOST=127.0.0.1 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD="$ADMIN_PASSWORD" \
  -e WEBHOOK_URL="https://$DOMAIN" \
  -e N8N_PAYLOAD_SIZE_MAX=16 \
  -e N8N_DIAGNOSTICS_ENABLED=false \
  -v /opt/pilotpros/n8n/data:/home/node/.n8n \
  -v /opt/pilotpros/logs:/opt/n8n/logs \
  n8n/n8n:latest

echo "✅ n8n container deployed with PostgreSQL backend"

# Verify container is running
if docker ps | grep -q pilotpros-n8n; then
    echo "✅ n8n container: Running"
else
    echo "❌ n8n container: Failed to start"
    exit 1
fi

# Wait for n8n to initialize database schema
echo "⏳ Waiting for n8n to initialize database..."
sleep 30

# Verify database schema creation
if psql -h localhost -U pilotpros_user -d pilotpros_db -c "\d n8n.workflow_entity" >/dev/null 2>&1; then
    echo "✅ n8n database schema: Initialized"
else
    echo "⚠️ n8n database schema: Still initializing..."
fi
```

### **PostgreSQL Optimization for n8n Workload**

```sql
-- PostgreSQL configuration optimization for n8n + PilotProOS workload
-- File: /etc/postgresql/14/main/conf.d/pilotpros.conf

# Memory Settings (for 4GB RAM server)
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
work_mem = 64MB

# Checkpoint and WAL Settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9
checkpoint_timeout = 10min
max_wal_size = 2GB
min_wal_size = 512MB

# Connection Settings
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

# Performance Monitoring
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all
track_activity_query_size = 2048

# Logging Configuration  
log_destination = 'stderr,csvlog'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d.log'
log_file_mode = 0644
log_rotation_age = 1d
log_rotation_size = 100MB

# Log slow queries (>1 second)
log_min_duration_statement = 1000
log_line_prefix = '[%m] [%p] [%d] [%u] '
log_statement = 'ddl'

# Performance Tuning for n8n Workload
random_page_cost = 1.1  # SSD optimization
effective_io_concurrency = 200
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
```

---

## 🗄️ **DATABASE SCHEMA STRATEGY**

### **Schema Separation & Security**

```sql
-- Database setup script: database/setup-schemas.sql
-- PilotProOS PostgreSQL Database Schema Setup

-- ============================================================================
-- DATABASE & USERS SETUP
-- ============================================================================

-- Create main database
CREATE DATABASE pilotpros_db 
    WITH ENCODING='UTF8' 
    LC_COLLATE='C' 
    LC_CTYPE='C' 
    TEMPLATE=template0;

-- Connect to database
\c pilotpros_db;

-- Create schemas with proper isolation
CREATE SCHEMA IF NOT EXISTS n8n;
CREATE SCHEMA IF NOT EXISTS pilotpros;

-- Create users with appropriate permissions
CREATE USER pilotpros_user WITH ENCRYPTED PASSWORD 'secure_random_password';
CREATE USER n8n_user WITH ENCRYPTED PASSWORD 'n8n_secure_password';

-- Schema permissions (strict isolation)
GRANT USAGE ON SCHEMA n8n TO n8n_user;
GRANT ALL PRIVILEGES ON SCHEMA n8n TO n8n_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA n8n TO n8n_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA n8n TO n8n_user;

GRANT USAGE ON SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA pilotpros TO pilotpros_user;

-- Cross-schema read access per analytics (pilotpros può leggere n8n)
GRANT USAGE ON SCHEMA n8n TO pilotpros_user;
GRANT SELECT ON ALL TABLES IN SCHEMA n8n TO pilotpros_user;

-- ============================================================================
-- PILOTPROS BUSINESS SCHEMA
-- ============================================================================

-- Business Users (authentication)
CREATE TABLE pilotpros.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business Process Analytics (aggregated da n8n data)
CREATE TABLE pilotpros.business_analytics (
    id SERIAL PRIMARY KEY,
    n8n_workflow_id VARCHAR(255) UNIQUE,
    process_name VARCHAR(255) NOT NULL,
    process_category VARCHAR(100),
    success_rate DECIMAL(5,2) DEFAULT 0,
    avg_duration_ms INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    last_execution TIMESTAMP,
    trend_direction VARCHAR(20), -- 'up', 'down', 'stable'
    business_impact_score INTEGER DEFAULT 0, -- 0-100
    optimization_suggestions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Process Templates (workflow templates business)
CREATE TABLE pilotpros.process_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    template_category VARCHAR(100),
    description TEXT,
    business_description TEXT,
    template_data JSONB NOT NULL,
    estimated_setup_time INTEGER, -- minutes
    industry_tags JSONB DEFAULT '[]',
    complexity_level VARCHAR(20) DEFAULT 'medium', -- easy, medium, hard
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Chat Conversations (per training e analytics)
CREATE TABLE pilotpros.ai_conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id),
    session_id VARCHAR(255),
    query_text TEXT NOT NULL,
    intent_detected VARCHAR(100),
    intent_confidence DECIMAL(3,2),
    mcp_tools_called JSONB DEFAULT '[]',
    response_generated TEXT,
    response_time_ms INTEGER,
    user_satisfaction INTEGER, -- 1-5 rating
    follow_up_query TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Audit Logs
CREATE TABLE pilotpros.audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100), -- 'workflow', 'execution', 'template', 'system'
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Metrics (for monitoring e health)
CREATE TABLE pilotpros.system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(12,4),
    metric_unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BUSINESS ANALYTICS VIEWS (Cross-Schema)
-- ============================================================================

-- View business completa dei processi
CREATE VIEW pilotpros.business_process_overview AS
SELECT 
    w.id as process_id,
    w.name as process_name,
    w.active as is_active,
    w.created_at as process_created,
    w.updated_at as last_modified,
    
    -- Analytics da pilotpros schema
    ba.success_rate,
    ba.avg_duration_ms,
    ba.total_executions,
    ba.business_impact_score,
    ba.trend_direction,
    
    -- Metriche calcolate real-time
    (
        SELECT COUNT(*) 
        FROM n8n.execution_entity e 
        WHERE e.workflow_id = w.id 
        AND e.started_at >= CURRENT_DATE
    ) as executions_today,
    
    (
        SELECT COUNT(*) 
        FROM n8n.execution_entity e 
        WHERE e.workflow_id = w.id 
        AND e.finished = false 
        AND e.started_at >= NOW() - INTERVAL '1 hour'
    ) as errors_last_hour,
    
    -- Health status calcolato
    CASE 
        WHEN ba.success_rate >= 98 THEN 'Excellent'
        WHEN ba.success_rate >= 90 THEN 'Good'
        WHEN ba.success_rate >= 75 THEN 'Fair'
        ELSE 'Needs Attention'
    END as health_status

FROM n8n.workflow_entity w
LEFT JOIN pilotpros.business_analytics ba ON w.id = ba.n8n_workflow_id
WHERE w.active = true
ORDER BY ba.business_impact_score DESC NULLS LAST;

-- View per AI Agent analytics
CREATE VIEW pilotpros.ai_agent_insights AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_queries,
    AVG(intent_confidence) as avg_intent_confidence,
    AVG(response_time_ms) as avg_response_time,
    AVG(user_satisfaction) as avg_satisfaction,
    
    -- Most common intents
    mode() WITHIN GROUP (ORDER BY intent_detected) as most_common_intent,
    
    -- Query categories
    COUNT(CASE WHEN intent_detected LIKE '%status%' THEN 1 END) as status_queries,
    COUNT(CASE WHEN intent_detected LIKE '%analytics%' THEN 1 END) as analytics_queries,
    COUNT(CASE WHEN intent_detected LIKE '%management%' THEN 1 END) as management_queries,
    COUNT(CASE WHEN intent_detected LIKE '%troubleshoot%' THEN 1 END) as troubleshoot_queries

FROM pilotpros.ai_conversations
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- Performance indexes for optimal query speed
CREATE INDEX IF NOT EXISTS idx_workflow_active ON n8n.workflow_entity(active) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_execution_workflow_date ON n8n.execution_entity(workflow_id, started_at);
CREATE INDEX IF NOT EXISTS idx_execution_status ON n8n.execution_entity(finished, started_at);

CREATE INDEX IF NOT EXISTS idx_business_analytics_workflow ON pilotpros.business_analytics(n8n_workflow_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_session ON pilotpros.ai_conversations(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON pilotpros.audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON pilotpros.system_metrics(metric_name, timestamp);

-- Function per aggiornamento automatico business analytics
CREATE OR REPLACE FUNCTION pilotpros.update_business_analytics()
RETURNS VOID AS $$
BEGIN
    -- Aggiorna metriche business dai dati n8n
    INSERT INTO pilotpros.business_analytics (
        n8n_workflow_id,
        process_name,
        success_rate,
        avg_duration_ms,
        total_executions,
        failed_executions,
        last_execution,
        updated_at
    )
    SELECT 
        w.id,
        w.name,
        COALESCE(
            (COUNT(CASE WHEN e.finished = true AND e.data->>'error' IS NULL THEN 1 END)::float / 
             NULLIF(COUNT(e.id), 0)) * 100, 0
        ) as success_rate,
        COALESCE(
            AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000), 0
        ) as avg_duration_ms,
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.finished = false OR e.data->>'error' IS NOT NULL THEN 1 END) as failed_executions,
        MAX(e.started_at) as last_execution,
        NOW() as updated_at
    FROM n8n.workflow_entity w
    LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
    WHERE e.started_at >= NOW() - INTERVAL '24 hours' OR e.started_at IS NULL
    GROUP BY w.id, w.name
    
    ON CONFLICT (n8n_workflow_id) 
    DO UPDATE SET
        process_name = EXCLUDED.process_name,
        success_rate = EXCLUDED.success_rate,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        total_executions = EXCLUDED.total_executions,
        failed_executions = EXCLUDED.failed_executions,
        last_execution = EXCLUDED.last_execution,
        updated_at = EXCLUDED.updated_at;
        
    -- Calcola trend direction
    UPDATE pilotpros.business_analytics 
    SET trend_direction = CASE
        WHEN success_rate > 95 THEN 'stable'
        WHEN success_rate > LAG(success_rate) OVER (ORDER BY updated_at) THEN 'up'
        WHEN success_rate < LAG(success_rate) OVER (ORDER BY updated_at) THEN 'down'
        ELSE 'stable'
    END;
END;
$$ LANGUAGE plpgsql;

-- Trigger automatico per aggiornamento analytics
CREATE OR REPLACE FUNCTION pilotpros.trigger_analytics_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Trigger update analytics quando ci sono nuove esecuzioni
    PERFORM pilotpros.update_business_analytics();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger su nuove esecuzioni n8n
CREATE TRIGGER execution_analytics_trigger
    AFTER INSERT OR UPDATE ON n8n.execution_entity
    FOR EACH STATEMENT
    EXECUTE FUNCTION pilotpros.trigger_analytics_update();
```

---

## 🔄 **DATA SYNC & REAL-TIME UPDATES**

### **Background Sync Service**

```typescript
// backend/services/postgresql-sync.service.ts
class PostgreSQLSyncService {
  private dbPool: Pool;
  private syncInterval: NodeJS.Timer;
  
  constructor() {
    this.dbPool = new Pool({
      host: 'localhost',
      port: 5432,
      database: 'pilotpros_db',
      user: 'pilotpros_user',
      password: process.env.DB_PASSWORD,
      // Optimization for frequent sync operations
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });
  }
  
  startRealTimeSync() {
    // Background sync ogni 30 secondi
    this.syncInterval = setInterval(async () => {
      await this.syncBusinessAnalytics();
      await this.updateSystemMetrics();
    }, 30000);
    
    console.log('✅ PostgreSQL real-time sync started');
  }
  
  private async syncBusinessAnalytics() {
    try {
      // Chiama la function PostgreSQL per update automatico
      await this.dbPool.query('SELECT pilotpros.update_business_analytics()');
      
      // Log sync success
      await this.dbPool.query(`
        INSERT INTO pilotpros.system_metrics (metric_name, metric_value, tags)
        VALUES ('sync_success', 1, '{"type": "business_analytics", "timestamp": "${new Date().toISOString()}"}')
      `);
      
    } catch (error) {
      console.error('❌ Business analytics sync failed:', error);
      
      // Log sync failure
      await this.dbPool.query(`
        INSERT INTO pilotpros.system_metrics (metric_name, metric_value, tags)
        VALUES ('sync_error', 1, '{"type": "business_analytics", "error": "${error.message}"}')
      `);
    }
  }
  
  private async updateSystemMetrics() {
    try {
      // Collect system metrics
      const metrics = await this.collectSystemMetrics();
      
      // Store metrics in database
      for (const [name, value] of Object.entries(metrics)) {
        await this.dbPool.query(`
          INSERT INTO pilotpros.system_metrics (metric_name, metric_value, tags)
          VALUES ($1, $2, $3)
        `, [name, value, JSON.stringify({ collected_at: new Date().toISOString() })]);
      }
      
    } catch (error) {
      console.error('❌ System metrics collection failed:', error);
    }
  }
  
  private async collectSystemMetrics() {
    // System performance metrics
    const memoryUsage = process.memoryUsage();
    const cpuUsage = process.cpuUsage();
    
    // Database metrics
    const dbStats = await this.dbPool.query(`
      SELECT 
        (SELECT COUNT(*) FROM n8n.workflow_entity WHERE active = true) as active_workflows,
        (SELECT COUNT(*) FROM n8n.execution_entity WHERE started_at >= CURRENT_DATE) as executions_today,
        (SELECT AVG(EXTRACT(EPOCH FROM (stopped_at - started_at))) FROM n8n.execution_entity WHERE started_at >= NOW() - INTERVAL '1 hour') as avg_duration_last_hour
    `);
    
    // n8n health check
    const n8nHealth = await this.checkN8nHealth();
    
    return {
      memory_usage_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024),
      active_workflows: dbStats.rows[0].active_workflows,
      executions_today: dbStats.rows[0].executions_today,
      avg_duration_seconds: dbStats.rows[0].avg_duration_last_hour || 0,
      n8n_health_score: n8nHealth ? 100 : 0,
      database_connections: this.dbPool.totalCount
    };
  }
  
  private async checkN8nHealth(): Promise<boolean> {
    try {
      // Verifica che n8n sia raggiungibile
      const response = await fetch('http://127.0.0.1:5678/healthz', {
        timeout: 5000
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
```

---

## 🔧 **AI AGENT DATABASE INTEGRATION**

### **MCP Tool Enhancement per PostgreSQL**

```typescript
// ai-agent/src/mcp/enhanced-mcp-tools.ts
class EnhancedMCPTools {
  private db: Pool;
  
  constructor(dbPool: Pool) {
    this.db = dbPool;
  }
  
  // Enhanced workflow.list con business context
  async getBusinessProcesses(filters: any = {}): Promise<BusinessProcess[]> {
    const query = `
      SELECT * FROM pilotpros.business_process_overview
      WHERE ($1::boolean IS NULL OR is_active = $1)
      AND ($2::text IS NULL OR process_name ILIKE '%' || $2 || '%')
      ORDER BY business_impact_score DESC, last_modified DESC
    `;
    
    const result = await this.db.query(query, [
      filters.active || null,
      filters.search || null
    ]);
    
    return result.rows.map(row => ({
      id: row.process_id,
      name: row.process_name,
      isActive: row.is_active,
      healthStatus: row.health_status,
      successRate: row.success_rate,
      avgDuration: row.avg_duration_ms,
      businessImpact: row.business_impact_score,
      trend: row.trend_direction,
      executionsToday: row.executions_today,
      lastExecution: row.last_modified
    }));
  }
  
  // Enhanced analytics con business insights
  async getBusinessAnalytics(timeframe: string = '7d'): Promise<BusinessAnalytics> {
    const interval = this.parseTimeframe(timeframe);
    
    const analyticsQuery = `
      SELECT 
        COUNT(DISTINCT w.id) as active_processes,
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.finished = true AND e.data->>'error' IS NULL THEN 1 END) as successful_executions,
        AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000) as avg_duration_ms,
        
        -- Business metrics
        COUNT(CASE WHEN e.data->>'type' = 'customer_onboarding' THEN 1 END) as customers_processed,
        COUNT(CASE WHEN e.data->>'type' = 'order_processing' THEN 1 END) as orders_processed,
        COUNT(CASE WHEN e.data->>'type' = 'support_ticket' THEN 1 END) as tickets_processed,
        
        -- Time saved calculation (assumendo 5 minuti per operazione manuale)
        COUNT(CASE WHEN e.finished = true THEN 1 END) * 5 as minutes_saved
        
      FROM n8n.workflow_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
      WHERE w.active = true
      AND (e.started_at IS NULL OR e.started_at >= NOW() - INTERVAL '${interval}')
    `;
    
    const result = await this.db.query(analyticsQuery);
    const data = result.rows[0];
    
    return {
      activeProcesses: data.active_processes,
      totalExecutions: data.total_executions,
      successRate: (data.successful_executions / data.total_executions * 100) || 0,
      avgDuration: data.avg_duration_ms || 0,
      
      businessMetrics: {
        customersProcessed: data.customers_processed || 0,
        ordersProcessed: data.orders_processed || 0,
        ticketsProcessed: data.tickets_processed || 0,
        timeSavedHours: Math.round((data.minutes_saved || 0) / 60)
      },
      
      insights: await this.generateBusinessInsights(data)
    };
  }
  
  // AI Agent specific: Error investigation
  async investigateErrors(timeframe: string = '1d'): Promise<ErrorInvestigation> {
    const interval = this.parseTimeframe(timeframe);
    
    const errorQuery = `
      SELECT 
        w.name as process_name,
        e.started_at,
        e.stopped_at,
        e.data->>'error' as error_message,
        e.data->>'stack' as error_details,
        EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000 as execution_time_ms
      FROM n8n.execution_entity e
      JOIN n8n.workflow_entity w ON e.workflow_id = w.id
      WHERE e.finished = false OR e.data->>'error' IS NOT NULL
      AND e.started_at >= NOW() - INTERVAL '${interval}'
      ORDER BY e.started_at DESC
      LIMIT 50
    `;
    
    const errors = await this.db.query(errorQuery);
    
    // Analizza pattern degli errori
    const errorPatterns = this.analyzeErrorPatterns(errors.rows);
    
    return {
      totalErrors: errors.rows.length,
      errorPatterns,
      affectedProcesses: [...new Set(errors.rows.map(e => e.process_name))],
      recommendations: this.generateErrorRecommendations(errorPatterns),
      urgentIssues: errorPatterns.filter(p => p.frequency > 5),
      recentErrors: errors.rows.slice(0, 10)
    };
  }
}
```

---

## 🚀 **DEPLOYMENT CONFIGURATION**

### **Script Integration: PostgreSQL + n8n**

```bash
#!/bin/bash
# scripts/02-application-deploy.sh (PostgreSQL-enhanced)

log "🗄️ Setting up PostgreSQL for n8n + PilotProOS..."

# Create database with optimized settings
sudo -u postgres psql << 'EOF'
-- Create database with UTF8 encoding
CREATE DATABASE pilotpros_db 
    WITH ENCODING='UTF8' 
    LC_COLLATE='C' 
    LC_CTYPE='C' 
    TEMPLATE=template0;

-- Connect and setup schemas
\c pilotpros_db;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS n8n;
CREATE SCHEMA IF NOT EXISTS pilotpros;

-- Create users
CREATE USER pilotpros_user WITH ENCRYPTED PASSWORD 'RANDOM_PASSWORD_HERE';
CREATE USER n8n_user WITH ENCRYPTED PASSWORD 'N8N_RANDOM_PASSWORD_HERE';

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA n8n TO n8n_user;
GRANT ALL PRIVILEGES ON SCHEMA pilotpros TO pilotpros_user;
GRANT USAGE ON SCHEMA n8n TO pilotpros_user;
GRANT SELECT ON ALL TABLES IN SCHEMA n8n TO pilotpros_user;
EOF

log "✅ PostgreSQL configured with schemas: n8n, pilotpros"

# Run PilotProOS business schema
psql -h localhost -U pilotpros_user -d pilotpros_db -f database/pilotpros-schema.sql

log "🔧 Deploying n8n with PostgreSQL backend..."

# n8n environment with PostgreSQL
cat > n8n/.env << EOF
# PostgreSQL Configuration
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=localhost
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=pilotpros_db
DB_POSTGRESDB_USER=n8n_user
DB_POSTGRESDB_PASSWORD=$N8N_DB_PASSWORD
DB_POSTGRESDB_SCHEMA=n8n

# n8n Server Configuration
N8N_PORT=5678
N8N_HOST=127.0.0.1
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=$ADMIN_PASSWORD

# Webhook Configuration
WEBHOOK_URL=https://$DOMAIN

# Performance Optimization  
N8N_PAYLOAD_SIZE_MAX=16
EXECUTIONS_TIMEOUT=300
EXECUTIONS_TIMEOUT_MAX=3600

# Security & Privacy
N8N_DIAGNOSTICS_ENABLED=false
N8N_VERSION_NOTIFICATIONS_ENABLED=false
N8N_ANONYMOUS_TELEMETRY=false
EOF

# Deploy n8n container with PostgreSQL
docker run -d \
  --name pilotpros-n8n \
  --restart unless-stopped \
  --network host \
  --env-file n8n/.env \
  -v /opt/pilotpros/n8n/data:/home/node/.n8n \
  -v /opt/pilotpros/logs/n8n:/opt/n8n/logs \
  n8n/n8n:latest

log "⏳ Waiting for n8n to initialize PostgreSQL schema..."
sleep 45

# Verify n8n PostgreSQL integration
if psql -h localhost -U pilotpros_user -d pilotpros_db -c "SELECT COUNT(*) FROM n8n.workflow_entity;" >/dev/null 2>&1; then
    log "✅ n8n PostgreSQL integration: Success"
else
    log "⚠️ n8n PostgreSQL integration: Still initializing..."
fi

log "🚀 Deploying PilotProOS Backend with PostgreSQL access..."

# Backend configuration with PostgreSQL
cat > backend/.env << EOF
NODE_ENV=production
PORT=3001
HOST=127.0.0.1

# PostgreSQL Connection (shared with n8n)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pilotpros_db
DB_USER=pilotpros_user
DB_PASSWORD=$DB_PASSWORD

# AI Agent Configuration
AI_AGENT_ENABLED=true
MCP_SERVER_PATH=../src/index.ts

# Security
JWT_SECRET=$(openssl rand -base64 64)
BCRYPT_ROUNDS=12

# Business Configuration
COMPANY_NAME=Business Process Automation
DOMAIN=$DOMAIN
EOF

success "Application stack deployed with PostgreSQL integration"
log "✅ Database: pilotpros_db (schemas: n8n, pilotpros)"
log "✅ n8n: Running on PostgreSQL backend"  
log "✅ Backend: Connected to shared PostgreSQL"
log "✅ AI Agent: Ready for MCP integration"
```

### **Docker Implementation: PostgreSQL**

```dockerfile
# Docker multi-stage build with PostgreSQL
FROM ubuntu:22.04 as base

# Install PostgreSQL 14
RUN apt-get update && apt-get install -y \
    postgresql-14 \
    postgresql-client-14 \
    postgresql-contrib-14

# Configure PostgreSQL for container use
RUN echo "host all all 127.0.0.1/32 md5" >> /etc/postgresql/14/main/pg_hba.conf
RUN echo "listen_addresses = 'localhost'" >> /etc/postgresql/14/main/postgresql.conf

# n8n installation with PostgreSQL support
RUN npm install -g n8n@latest

# Copy database setup scripts
COPY database/ /opt/database/
COPY config/postgresql/ /etc/postgresql/14/main/conf.d/

# Setup database initialization script
COPY scripts/docker-postgres-init.sh /docker-postgres-init.sh
RUN chmod +x /docker-postgres-init.sh

# PostgreSQL + n8n startup script
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh  
RUN chmod +x /docker-entrypoint.sh

# Expose only frontend port (PostgreSQL and n8n are internal)
EXPOSE 80 443

# Health check includes PostgreSQL + n8n
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD /opt/scripts/health-check.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
```

---

## 📊 **PERFORMANCE OPTIMIZATION**

### **PostgreSQL Tuning per n8n Workload**

```sql
-- Indexes specifici per n8n tables (after n8n initialization)
-- Questi indexes migliorano significativamente le performance

-- Workflow entity optimization
CREATE INDEX IF NOT EXISTS idx_workflow_entity_active_name ON n8n.workflow_entity(active, name) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_workflow_entity_updated ON n8n.workflow_entity(updated_at DESC);

-- Execution entity optimization (high-volume table)
CREATE INDEX IF NOT EXISTS idx_execution_entity_workflow_started ON n8n.execution_entity(workflow_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_entity_status_date ON n8n.execution_entity(finished, started_at) WHERE started_at >= '2025-01-01';
CREATE INDEX IF NOT EXISTS idx_execution_entity_today ON n8n.execution_entity(started_at) WHERE started_at >= CURRENT_DATE;

-- Composite index per analytics queries
CREATE INDEX IF NOT EXISTS idx_execution_analytics ON n8n.execution_entity(workflow_id, finished, started_at) 
WHERE started_at >= NOW() - INTERVAL '30 days';

-- Partitioning per execution_entity (se volume alto)
CREATE TABLE n8n.execution_entity_2025 PARTITION OF n8n.execution_entity
FOR VALUES FROM ('2025-01-01 00:00:00') TO ('2026-01-01 00:00:00');

-- Statistics update per query optimizer
ANALYZE n8n.workflow_entity;
ANALYZE n8n.execution_entity;
ANALYZE pilotpros.business_analytics;
```

### **Connection Pool Optimization**

```typescript
// Configurazione pool connections ottimizzata
const poolConfig = {
  // Core connection settings
  host: 'localhost',
  port: 5432,
  database: 'pilotpros_db',
  user: 'pilotpros_user',
  password: process.env.DB_PASSWORD,
  
  // Pool optimization per n8n + PilotProOS workload
  max: 20,                    // Max 20 connections
  min: 5,                     // Keep 5 connections warm
  idleTimeoutMillis: 30000,   // Close idle connections after 30s
  connectionTimeoutMillis: 2000, // Timeout connection attempts after 2s
  acquireTimeoutMillis: 30000,   // Timeout pool acquisition after 30s
  
  // Performance optimization
  keepAlive: true,
  keepAliveInitialDelayMillis: 0,
  
  // Error handling
  parseInputDatesAsUTC: true,
  statement_timeout: 30000,   // Kill queries after 30s
  query_timeout: 30000,
  
  // SSL configuration (if needed)
  ssl: process.env.NODE_ENV === 'production' ? {
    rejectUnauthorized: false
  } : false
};
```

---

## 🧪 **TESTING & VALIDATION**

### **PostgreSQL Integration Tests**

```bash
#!/bin/bash
# tests/postgresql-integration.test.sh

echo "🧪 Testing PostgreSQL + n8n Integration"
echo "======================================"

# Test 1: Database connection
echo -n "🗄️ PostgreSQL connection: "
if psql -h localhost -U pilotpros_user -d pilotpros_db -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "❌ Failed"
    exit 1
fi

# Test 2: n8n schema initialization
echo -n "🔧 n8n schema: "
if psql -h localhost -U pilotpros_user -d pilotpros_db -c "SELECT COUNT(*) FROM n8n.workflow_entity;" >/dev/null 2>&1; then
    echo "✅ Initialized"
else
    echo "❌ Missing"
    exit 1
fi

# Test 3: PilotProOS schema
echo -n "📊 PilotProOS schema: "
if psql -h localhost -U pilotpros_user -d pilotpros_db -c "SELECT COUNT(*) FROM pilotpros.users;" >/dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Missing"
    exit 1
fi

# Test 4: Cross-schema views
echo -n "🔗 Cross-schema views: "
if psql -h localhost -U pilotpros_user -d pilotpros_db -c "SELECT COUNT(*) FROM pilotpros.business_process_overview;" >/dev/null 2>&1; then
    echo "✅ Working"
else
    echo "❌ Failed"
    exit 1
fi

# Test 5: n8n API accessibility
echo -n "🚀 n8n API: "
if curl -s -u admin:$ADMIN_PASSWORD http://127.0.0.1:5678/api/v1/workflows >/dev/null 2>&1; then
    echo "✅ Accessible"
else
    echo "❌ Not responding"
    exit 1
fi

# Test 6: Performance test
echo -n "⚡ Query performance: "
start_time=$(date +%s%N)
psql -h localhost -U pilotpros_user -d pilotpros_db -c "SELECT * FROM pilotpros.business_process_overview LIMIT 10;" >/dev/null 2>&1
end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

if [ $duration -lt 1000 ]; then
    echo "✅ ${duration}ms (excellent)"
else
    echo "⚠️ ${duration}ms (slow)"
fi

echo ""
echo "🎯 PostgreSQL Integration: All tests passed!"
```

---

## 📋 **MIGRATION CHECKLIST**

### **From SQLite to PostgreSQL**

```bash
# Checklist per migrazione n8n esistente da SQLite a PostgreSQL

# ✅ Pre-Migration
[ ] Backup esistente n8n database (SQLite)
[ ] Verify PostgreSQL 14+ installation
[ ] Create pilotpros_db database
[ ] Setup schemas (n8n, pilotpros)
[ ] Configure users and permissions

# ✅ Configuration  
[ ] Update n8n environment variables
[ ] Configure DB_TYPE=postgresdb
[ ] Set PostgreSQL connection parameters
[ ] Verify n8n can connect to PostgreSQL

# ✅ Migration
[ ] Export workflows from existing n8n
[ ] Start n8n with PostgreSQL (schema auto-creation)
[ ] Import workflows to new PostgreSQL n8n
[ ] Verify all workflows are working
[ ] Test workflow execution

# ✅ Integration
[ ] Deploy PilotProOS backend with PostgreSQL access
[ ] Setup cross-schema analytics views
[ ] Test AI Agent MCP integration
[ ] Verify business analytics data

# ✅ Validation
[ ] All workflows active and functional
[ ] Performance meets expectations (<1000ms queries)
[ ] AI Agent responding correctly
[ ] Business analytics updating real-time
[ ] Backup/restore procedures tested
```

---

**🎯 La configurazione PostgreSQL per n8n è semplice ma potente - trasforma n8n da tool standalone a enterprise-grade workflow engine perfettamente integrato con PilotProOS business intelligence.**