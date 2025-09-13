# PilotProOS - Architettura Tecnica Dettagliata

**Documento**: Architettura 3-Layer con Reverse Proxy System  
**Versione**: 1.6.0  
**Target**: Team Tecnico di Sviluppo  
**Ultimo aggiornamento**: 2025-09-05  

---

## 🏗️ Panoramica Architetturale

### Principio Fondamentale: Clean Architecture

L'architettura ONESERVER implementa una **Clean Architecture** a 3 layer con separazione netta delle responsabilità e zero accoppiamento tra livelli.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ONESERVER STACK                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │   LAYER 1       │    │   LAYER 2       │    │      LAYER 3            │ │
│  │   FRONTEND      │◄──►│   BACKEND       │◄──►│   DATA LAYER            │ │
│  │                 │    │   MIDDLEWARE    │    │                         │ │
│  │  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌─────────┬─────────┐  │ │
│  │  │   React   │  │    │  │ Express   │  │    │  │PostgreSQL│ n8n     │  │ │
│  │  │   Vite    │  │    │  │ API       │  │    │  │Database  │Server   │  │ │
│  │  │   SPA     │  │    │  │ Gateway   │  │    │  │Port 5432 │Port 5678│  │ │
│  │  └───────────┘  │    │  └───────────┘  │    │  └─────────┴─────────┘  │ │
│  │  Port: 3000     │    │  Port: 3001     │    │  Schema Separation       │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
│           │                       │                        │                │
│           │                       │                        │                │
│    ┌─────────────┐        ┌─────────────┐         ┌─────────────────┐       │
│    │ HTTP/REST   │        │SQL Queries  │         │n8n API Internal │       │
│    │ API Calls   │        │+ Security   │         │+ DB Direct      │       │
│    │ (ONLY)      │        │Layer        │         │Access           │       │
│    └─────────────┘        └─────────────┘         └─────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Layer 1: Frontend Presentation

### Tecnologie Core
- **Framework**: React 18.2+ con TypeScript
- **Build Tool**: Vite 4+ per performance ottimali
- **Styling**: TailwindCSS + Control Room theme
- **State Management**: Zustand (semplificato mono-tenant)
- **HTTP Client**: Axios con interceptors
- **Icons**: Lucide React (consistency design)

### Struttura Componenti
```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Layout.tsx              # Layout principale con sidebar
│   │   │   ├── Sidebar.tsx             # Navigazione business-oriented
│   │   │   └── Header.tsx              # Header con user context
│   │   ├── dashboard/
│   │   │   ├── Dashboard.tsx           # Dashboard overview business
│   │   │   ├── ProcessMetrics.tsx      # Metriche processi (ex workflows)
│   │   │   └── RecentActivity.tsx      # Attività recenti
│   │   ├── processes/                  # Ex-workflows (anonimizzato)
│   │   │   ├── ProcessList.tsx         # Lista processi business
│   │   │   ├── ProcessDetail.tsx       # Dettaglio processo
│   │   │   └── ProcessExecutions.tsx   # Esecuzioni processo
│   │   ├── analytics/
│   │   │   ├── PerformanceMetrics.tsx  # Analytics performance
│   │   │   ├── BusinessInsights.tsx    # Insights business
│   │   │   └── ReportingDashboard.tsx  # Dashboard reportistica
│   │   └── ui/                         # Componenti UI base
│   │       ├── Button.tsx              # Button system
│   │       ├── Card.tsx                # Card containers
│   │       ├── Table.tsx               # Data tables
│   │       └── Modal.tsx               # Modal system
│   ├── services/
│   │   ├── api.service.ts              # API layer con middleware backend
│   │   ├── auth.service.ts             # Authentication service
│   │   └── websocket.service.ts        # Real-time updates (future)
│   ├── store/
│   │   ├── app.store.ts                # Main Zustand store
│   │   ├── auth.store.ts               # Authentication state
│   │   └── processes.store.ts          # Processes state (ex-workflows)
│   └── utils/
│       ├── constants.ts                # Terminologia business anonimizzata
│       ├── formatters.ts               # Data formatting utilities
│       └── validation.ts               # Input validation
```

### API Integration Layer
```typescript
// services/api.service.ts - Interfaccia con Backend Middleware
class ApiService {
  private baseURL = 'http://localhost:3001/api';
  
  // Business Processes (anonimizzato da "workflows")
  async getBusinessProcesses() {
    return this.get('/business/processes');
  }
  
  async getProcessExecutions(processId: string) {
    return this.get(`/business/processes/${processId}/executions`);
  }
  
  async triggerProcess(processId: string, data: any) {
    return this.post(`/business/processes/${processId}/trigger`, data);
  }
  
  // Analytics Business
  async getBusinessAnalytics() {
    return this.get('/analytics/business-overview');
  }
  
  // ZERO reference a n8n, PostgreSQL, o altre tecnologie
  private async get(endpoint: string) {
    // Standard HTTP calls al middleware - NEVER direct DB
    return axios.get(`${this.baseURL}${endpoint}`);
  }
}
```

### Anonimizzazione Terminologia
```typescript
// utils/constants.ts - Business-Friendly Terminology
export const BUSINESS_TERMINOLOGY = {
  // Mapping da terminologia tecnica a business
  workflow: 'Business Process',
  workflows: 'Business Processes',
  execution: 'Process Run',
  executions: 'Process Runs',
  node: 'Process Step',
  nodes: 'Process Steps',
  trigger: 'Event Handler',
  webhook: 'Integration Endpoint',
  
  // Status mapping
  running: 'In Progress',
  success: 'Completed Successfully',
  error: 'Requires Attention',
  waiting: 'Pending Input'
};

export const UI_LABELS = {
  pageTitle: 'Business Process Automation',
  navigation: {
    dashboard: 'Overview',
    processes: 'Automation Processes',
    executions: 'Process Activity',
    analytics: 'Business Insights',
    settings: 'Configuration'
  }
};
```

---

## ⚙️ Layer 2: Backend Middleware

### Tecnologie Core
- **Runtime**: Node.js 18+ LTS
- **Framework**: Express.js 4.18+
- **Language**: TypeScript per type safety
- **Database**: PostgreSQL driver (pg 8+)
- **Authentication**: JWT + bcryptjs (enterprise cross-platform)
- **Security**: Helmet, CORS, Rate limiting
- **Process Manager**: PM2 per production

### Architettura Middleware
```
backend/
├── src/
│   ├── controllers/
│   │   ├── auth.controller.ts          # Authentication endpoints
│   │   ├── business.controller.ts      # Business processes (ex-workflows)
│   │   ├── analytics.controller.ts     # Business analytics
│   │   └── system.controller.ts        # System health/status
│   ├── services/
│   │   ├── database.service.ts         # PostgreSQL connection pool
│   │   ├── business.service.ts         # Business logic layer
│   │   ├── analytics.service.ts        # Analytics computation
│   │   └── security.service.ts         # Security utilities
│   ├── middleware/
│   │   ├── auth.middleware.ts          # JWT validation
│   │   ├── security.middleware.ts      # Security headers + sanitization
│   │   ├── rateLimit.middleware.ts     # Rate limiting protection
│   │   └── logging.middleware.ts       # Request/response logging
│   ├── models/
│   │   ├── process.model.ts            # Business process model
│   │   ├── execution.model.ts          # Process execution model
│   │   └── user.model.ts               # User model
│   ├── repositories/
│   │   ├── process.repository.ts       # Process data access
│   │   ├── execution.repository.ts     # Execution data access
│   │   └── analytics.repository.ts     # Analytics data access
│   └── utils/
│       ├── crypto.utils.ts             # Encryption utilities
│       ├── validation.utils.ts         # Input validation
│       └── sanitization.utils.ts       # Data sanitization
```

### Database Access Strategy
```typescript
// services/database.service.ts - Controlled DB Access
class DatabaseService {
  private pool: Pool;
  
  constructor() {
    this.pool = new Pool({
      host: 'localhost',
      port: 5432,
      database: 'oneserver_db',
      user: 'oneserver_user',
      password: process.env.DB_PASSWORD,
      // Connection pool optimization
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });
  }
  
  // Business Processes (reads from n8n schema but abstracts it)
  async getBusinessProcesses(): Promise<BusinessProcess[]> {
    const query = `
      SELECT 
        w.id,
        w.name as process_name,
        w.active as is_active,
        w.created_at,
        w.updated_at,
        -- Analytics from our schema
        a.success_rate,
        a.avg_duration_ms,
        a.last_execution
      FROM n8n.workflow_entity w
      LEFT JOIN app.process_analytics a ON w.id = a.n8n_workflow_id
      WHERE w.active = true
      ORDER BY w.updated_at DESC
    `;
    
    const result = await this.pool.query(query);
    return result.rows.map(this.mapToBusinessProcess);
  }
  
  // NEVER expose n8n API, sempre query dirette controlled
  private mapToBusinessProcess(row: any): BusinessProcess {
    return {
      id: row.id,
      name: row.process_name,
      isActive: row.is_active,
      successRate: row.success_rate || 0,
      avgDuration: row.avg_duration_ms || 0,
      lastExecution: row.last_execution,
      // Zero esposizione di dati tecnici n8n
    };
  }
}
```

### Security Middleware Stack
```typescript
// middleware/security.middleware.ts - Enterprise Security
export const securityStack = [
  // Helmet per security headers
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        scriptSrc: ["'self'"],
        imgSrc: ["'self'", "data:", "https:"],
      },
    },
    // Hide technology information
    hidePoweredBy: true,
  }),
  
  // CORS configuration
  cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  }),
  
  // Rate limiting per endpoint
  rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP',
    standardHeaders: true,
    legacyHeaders: false,
  }),
  
  // Input sanitization
  sanitizationMiddleware,
  
  // Request logging (no sensitive data)
  loggingMiddleware,
];
```

---

## 💾 Layer 3: Data Layer

### Database Architecture

#### Schema Separation Strategy
```sql
-- Database: oneserver_db
-- Due schema separati per isolamento completo

-- SCHEMA 1: n8n (n8n ownership completo)
CREATE SCHEMA n8n;
-- Tabelle gestite automaticamente da n8n:
-- - workflow_entity (workflows)
-- - execution_entity (executions)  
-- - credentials_entity (credentials)
-- - settings (n8n settings)

-- SCHEMA 2: app (nostro controllo completo)
CREATE SCHEMA app;

-- Business Analytics (nostri dati aggregati)
CREATE TABLE app.process_analytics (
    id SERIAL PRIMARY KEY,
    n8n_workflow_id VARCHAR(255) UNIQUE, -- Reference a n8n.workflow_entity.id
    process_name VARCHAR(255),
    success_rate DECIMAL(5,2) DEFAULT 0,
    avg_duration_ms INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    last_execution TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business Users (authentication nostro)
CREATE TABLE app.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business Process Templates (workflow templates)
CREATE TABLE app.process_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    template_data JSONB, -- n8n workflow JSON
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Audit Logs
CREATE TABLE app.audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES app.users(id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Database Views per Sicurezza
```sql
-- Views sicure che aggregano dati cross-schema
CREATE VIEW app.business_process_summary AS
SELECT 
    w.id as process_id,
    w.name as process_name,
    w.active as is_active,
    w.created_at,
    w.updated_at,
    -- Metriche calcolate
    COALESCE(a.success_rate, 0) as success_rate,
    COALESCE(a.avg_duration_ms, 0) as avg_duration_ms,
    COALESCE(a.total_executions, 0) as total_executions,
    a.last_execution,
    -- Process health score (business logic)
    CASE 
        WHEN a.success_rate >= 95 THEN 'Excellent'
        WHEN a.success_rate >= 80 THEN 'Good'
        WHEN a.success_rate >= 60 THEN 'Needs Attention'
        ELSE 'Critical'
    END as health_status
FROM n8n.workflow_entity w
LEFT JOIN app.process_analytics a ON w.id = a.n8n_workflow_id
WHERE w.active = true;

-- View per execution analytics
CREATE VIEW app.process_execution_summary AS
SELECT 
    DATE_TRUNC('day', e.started_at) as execution_date,
    COUNT(*) as total_executions,
    COUNT(CASE WHEN e.finished = true THEN 1 END) as successful_executions,
    AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000) as avg_duration_ms,
    COUNT(CASE WHEN e.finished = false THEN 1 END) as failed_executions
FROM n8n.execution_entity e
WHERE e.started_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', e.started_at)
ORDER BY execution_date DESC;
```

### n8n Server Integration

#### n8n Configuration
```javascript
// config/n8n.config.js - n8n Production Configuration
module.exports = {
  // Database connection (shared PostgreSQL)
  database: {
    type: 'postgresdb',
    host: 'localhost',
    port: 5432,
    database: 'oneserver_db',
    schema: 'n8n', // Isolated schema
    username: 'oneserver_user',
    password: process.env.DB_PASSWORD,
  },
  
  // Server configuration
  port: 5678,
  host: '127.0.0.1', // ONLY localhost access
  
  // Security configuration  
  basicAuth: {
    active: true,
    user: 'admin',
    password: process.env.N8N_ADMIN_PASSWORD,
  },
  
  // Webhook configuration
  webhookUrl: process.env.DOMAIN_URL || 'http://localhost',
  
  // Disable external access
  endpoints: {
    rest: '/api/v1', // Hidden behind firewall
    webhook: '/webhook',
    webhookWaiting: '/webhook-waiting',
  },
  
  // Logging
  logs: {
    level: 'info',
    output: 'file',
    file: '/opt/oneserver/logs/n8n.log',
  },
  
  // Performance tuning
  executions: {
    saveDataOnError: 'all',
    saveDataOnSuccess: 'none',
    maxNumberOfExecutions: 10000,
  },
};
```

#### Data Sync Service
```typescript
// services/sync.service.ts - Sync n8n → app analytics
class DataSyncService {
  private dbService: DatabaseService;
  private syncInterval: NodeJS.Timer;
  
  constructor() {
    this.dbService = new DatabaseService();
  }
  
  startSyncScheduler() {
    // Sync ogni 5 minuti
    this.syncInterval = setInterval(async () => {
      await this.syncProcessAnalytics();
      await this.syncExecutionMetrics();
    }, 5 * 60 * 1000);
  }
  
  private async syncProcessAnalytics() {
    // Calcola metriche dai dati n8n e aggiorna app schema
    const query = `
      INSERT INTO app.process_analytics (
        n8n_workflow_id, process_name, success_rate, 
        avg_duration_ms, total_executions, last_execution, updated_at
      )
      SELECT 
        w.id,
        w.name,
        COALESCE(
          COUNT(CASE WHEN e.finished = true THEN 1 END)::float / 
          NULLIF(COUNT(e.id), 0) * 100, 0
        ) as success_rate,
        COALESCE(
          AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000), 0
        ) as avg_duration_ms,
        COUNT(e.id) as total_executions,
        MAX(e.started_at) as last_execution,
        NOW() as updated_at
      FROM n8n.workflow_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
      WHERE e.started_at >= NOW() - INTERVAL '24 hours'
      GROUP BY w.id, w.name
      ON CONFLICT (n8n_workflow_id) 
      DO UPDATE SET
        success_rate = EXCLUDED.success_rate,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        total_executions = EXCLUDED.total_executions,
        last_execution = EXCLUDED.last_execution,
        updated_at = EXCLUDED.updated_at
    `;
    
    await this.dbService.query(query);
  }
}
```

---

## 🔄 Data Flow Architecture

### Request Flow: Frontend → Backend → Database

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    FRONTEND     │    │    BACKEND      │    │   DATABASE      │
│                 │    │   MIDDLEWARE    │    │                 │
│  1. User click  │    │                 │    │                 │
│     "Processes" │───►│ 2. GET /api/    │    │                 │
│                 │    │    business/    │    │                 │
│                 │    │    processes    │───►│ 3. Query n8n +  │
│                 │    │                 │    │    app schemas  │
│                 │    │ 4. Business     │◄───│                 │
│  5. Display     │◄───│    data format  │    │                 │
│     "Processes" │    │    (anonimized) │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Security Isolation Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLIENT SEES   │    │  MIDDLEWARE     │    │  ACTUAL TECH    │
│                 │    │   TRANSLATES    │    │                 │
│ "Business       │    │                 │    │ n8n workflow    │
│  Process"       │◄──►│ Terminology     │◄──►│ PostgreSQL      │
│                 │    │ Mapping         │    │ Express.js      │
│ "Process Run"   │    │                 │    │ Node.js         │
│                 │    │ Zero Tech       │    │                 │
│ "Integration    │    │ Exposure        │    │ Webhook/API     │
│  Endpoint"      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🎯 Performance Optimization

### Database Optimization
```sql
-- Indexes per performance ottimali
CREATE INDEX idx_workflow_active ON n8n.workflow_entity(active) WHERE active = true;
CREATE INDEX idx_execution_workflow_date ON n8n.execution_entity(workflow_id, started_at);
CREATE INDEX idx_process_analytics_workflow ON app.process_analytics(n8n_workflow_id);
CREATE INDEX idx_audit_logs_timestamp ON app.audit_logs(timestamp);

-- Partitioning per execution_entity (high volume table)
CREATE TABLE n8n.execution_entity_y2025 PARTITION OF n8n.execution_entity
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### Connection Pool Tuning
```typescript
// Database connection pool optimization
const poolConfig = {
  max: 20,                    // Max connections
  min: 5,                     // Min connections
  acquire: 30000,             // Max time to get connection
  idle: 10000,                // Max idle time
  evict: 1000,                // Eviction run interval
  handleDisconnects: true,    // Auto-reconnect
  charset: 'utf8mb4',
  logging: false,             // Disable query logging in production
};
```

### Caching Strategy
```typescript
// In-memory caching per frequent queries
class CacheService {
  private cache: Map<string, {data: any, expiry: number}> = new Map();
  
  async getProcessSummary() {
    const cacheKey = 'process_summary';
    const cached = this.cache.get(cacheKey);
    
    if (cached && cached.expiry > Date.now()) {
      return cached.data;
    }
    
    // Fetch from database
    const data = await this.dbService.getProcessSummary();
    
    // Cache for 5 minutes
    this.cache.set(cacheKey, {
      data,
      expiry: Date.now() + (5 * 60 * 1000)
    });
    
    return data;
  }
}
```

---

## 🔧 Configuration Management

### Environment Configuration
```bash
# .env.production - Production Configuration
NODE_ENV=production
PORT=3001

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=oneserver_db
DB_USER=oneserver_user
DB_PASSWORD=secure_random_password
DB_POOL_MAX=20
DB_POOL_MIN=5

# n8n Configuration
N8N_PORT=5678
N8N_HOST=127.0.0.1
N8N_ADMIN_PASSWORD=secure_n8n_admin_password
N8N_WEBHOOK_URL=https://client-domain.com

# Security Configuration
JWT_SECRET=ultra_secure_jwt_secret_min_32_chars
JWT_EXPIRY=24h
BCRYPT_ROUNDS=12

# SSL Configuration
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/client-domain.crt
SSL_KEY_PATH=/etc/ssl/private/client-domain.key

# Logging Configuration
LOG_LEVEL=info
LOG_FILE=/opt/oneserver/logs/backend.log
LOG_MAX_SIZE=10MB
LOG_ROTATE=7d

# Client Branding
CLIENT_NAME=Business Process Automation
CLIENT_DOMAIN=client-domain.com
CLIENT_SUPPORT_EMAIL=support@client-domain.com
```

---

## 📊 Monitoring & Observability

### Health Check Endpoints
```typescript
// System health monitoring
app.get('/health', async (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    services: {
      database: await checkDatabaseHealth(),
      n8n: await checkN8nHealth(),
      filesystem: await checkFilesystemHealth(),
      memory: process.memoryUsage(),
      uptime: process.uptime(),
    }
  };
  
  res.json(health);
});

async function checkDatabaseHealth() {
  try {
    await dbService.query('SELECT 1');
    return { status: 'healthy', response_time: Date.now() };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
}
```

### Performance Metrics
```typescript
// Performance monitoring middleware
const performanceMonitoring = (req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    
    // Log slow requests (>1000ms)
    if (duration > 1000) {
      logger.warn('Slow request detected', {
        method: req.method,
        url: req.url,
        duration: `${duration}ms`,
        status: res.statusCode
      });
    }
    
    // Store metrics for analytics
    metricsService.recordRequestMetric({
      endpoint: req.route?.path || req.url,
      method: req.method,
      duration,
      statusCode: res.statusCode,
      timestamp: new Date()
    });
  });
  
  next();
};
```

---

## 🛡️ **n8n VERSION COMPATIBILITY SYSTEM**

### **Problema Risolto: Backend Obsolescenza**
Con l'evoluzione di n8n, ogni upgrade poteva rendere il backend obsoleto a causa di:
- **Breaking changes** schema database (workflow_id → workflowId)
- **API modifications** e deprecazioni
- **Nuovi campi obbligatori** o tabelle rimosse

### **Soluzione: Automatic Compatibility Layer**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    n8n UPGRADE RESILIENCE SYSTEM                            │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │   n8n v1.107    │    │   n8n v1.108    │    │   n8n v1.109+          │ │
│  │                 │    │                 │    │   (Future Versions)    │ │
│  │ workflow_id     │───►│ workflowId      │───►│ newFieldName           │ │
│  │ started_at      │    │ startedAt       │    │ enhancedTimestamp      │ │
│  │ stopped_at      │    │ stoppedAt       │    │ completionTime         │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
│           │                       │                        │                │
│           └───────────────────────┼────────────────────────┘                │
│                                   │                                         │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐   │
│  │              COMPATIBILITY LAYER (PilotProOS)                        │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │   │
│  │  │ Version         │  │ Field Mapper    │  │ Query Builder       │   │   │
│  │  │ Detection       │  │                 │  │                     │   │   │
│  │  │                 │  │ workflow_id     │  │ Graceful            │   │   │
│  │  │ • Migration     │  │ ↕                │  │ Degradation         │   │   │
│  │  │   Analysis      │  │ workflowId      │  │                     │   │   │
│  │  │ • Schema        │  │                 │  │ • Modern Query      │   │   │
│  │  │   Inspection    │  │ started_at      │  │ • Legacy Query      │   │   │
│  │  │ • Auto-Update   │  │ ↕                │  │ • Fallback Query    │   │   │
│  │  │                 │  │ startedAt       │  │                     │   │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐   │
│  │                    BUSINESS API LAYER                                 │   │
│  │                   (Always Compatible)                                 │   │
│  │                                                                       │   │
│  │  GET /api/business/processes     ✅ Works with any n8n version        │   │
│  │  GET /api/business/analytics     ✅ Automatic field adaptation        │   │
│  │  GET /api/system/compatibility   ✅ Real-time monitoring              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Implementation Components**

#### **DatabaseCompatibilityService**
```typescript
// backend/src/services/database-compatibility.service.js
class DatabaseCompatibilityService {
  async detectN8nVersion() {
    // Analizza le migrazioni per determinare versione
    const migrations = await this.getMigrations();
    return this.parseVersionFromMigrations(migrations);
  }
  
  async getWorkflowsCompatible() {
    // Query con fallback automatico per diverse versioni
    const modernQuery = "SELECT w.id, w.\"createdAt\" FROM n8n.workflow_entity w";
    const legacyQuery = "SELECT w.id, w.created_at FROM n8n.workflow_entity w";
    return await this.executeWithFallback([modernQuery, legacyQuery]);
  }
}
```

#### **N8nFieldMapper**
```typescript
// backend/src/utils/n8n-field-mapper.js
const N8N_FIELD_MAPPINGS = {
  '1.108.1': { workflowId: 'workflowId', startedAt: 'startedAt' },
  '1.107.3': { workflowId: 'workflowId', startedAt: 'startedAt' },
  '1.106.0': { workflowId: 'workflow_id', startedAt: 'started_at' }
};
```

#### **Runtime Monitoring**
```javascript
// API endpoints per monitoring
GET /api/system/compatibility          // Status completo compatibilità
GET /api/system/compatibility/health   // Health check rapido

// Response example:
{
  "compatibility": {
    "version": "1.108.1",
    "status": "compatible", 
    "isReady": true
  },
  "schemaInfo": {
    "execution_entity fields": ["workflowId", "startedAt", "stoppedAt"]
  }
}
```

### **Benefits del Sistema**
- **✅ Zero Maintenance**: Backend si adatta automaticamente
- **✅ Future-Proof**: Compatibile con versioni future n8n
- **✅ Zero Downtime**: Upgrade senza interruzioni
- **✅ Automatic Detection**: Rileva cambi schema in runtime
- **✅ Fallback Protection**: Query degradano gracefully
- **✅ Monitoring**: Alerting per problemi compatibilità

---

Questa architettura garantisce **separazione completa**, **performance ottimali**, **sicurezza enterprise** e **resilienza agli upgrade** mantenendo la **semplicità operativa** di un sistema monolitico.

**Next**: Consultare `deployment.md` per le strategie di deployment automatico.