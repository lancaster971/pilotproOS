# PilotProOS - Architettura Tecnica

**Versione**: 2.0.0
**Target**: Team Tecnico di Sviluppo

---

## 🏗️ Panoramica Architetturale

### Clean Architecture 3-Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PILOTPROOS STACK                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │   LAYER 1       │    │   LAYER 2       │    │      LAYER 3            │ │
│  │   FRONTEND      │◄──►│   BACKEND       │◄──►│   DATA LAYER            │ │
│  │                 │    │   MIDDLEWARE    │    │                         │ │
│  │  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌─────────┬─────────┐  │ │
│  │  │   Vue 3  │  │    │  │ Express   │  │    │  │PostgreSQL│ n8n     │  │ │
│  │  │   Vite    │  │    │  │ API       │  │    │  │Database  │Server   │  │ │
│  │  │   SPA     │  │    │  │ Gateway   │  │    │  │Port 5432 │Port 5678│  │ │
│  │  └───────────┘  │    │  └───────────┘  │    │  └─────────┴─────────┘  │ │
│  │  Port: 3000     │    │  Port: 3001     │    │  Schema Separation       │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Layer 1: Frontend Presentation

### Tecnologie Core
- **Framework**: Vue 3 + TypeScript
- **Build Tool**: Vite 4+
- **Styling**: TailwindCSS
- **State Management**: Pinia
- **Router**: Vue Router
- **HTTP Client**: Axios
- **Workflow Viz**: VueFlow
- **Icone**: Iconify via `N8nIcon.vue`

### Business Terminology Mapping
```typescript
export const BUSINESS_TERMINOLOGY = {
  workflow: 'Business Process',
  execution: 'Process Run',
  node: 'Process Step',
  trigger: 'Event Handler',
  webhook: 'Integration Endpoint'
};
```

---

## ⚙️ Layer 2: Backend Middleware

### Tecnologie Core
- **Runtime**: Node.js 18+ LTS
- **Framework**: Express.js 4.18+
- **Language**: TypeScript
- **Database**: PostgreSQL driver (pg)
- **Authentication**: JWT + bcryptjs (**CURRENTLY DISABLED**)
- **Security**: Helmet, CORS, Rate limiting

### Database Access Strategy
```javascript
// Dual schema access
const query = `
  SELECT
    w.id,
    w.name as process_name,
    w.active as is_active,
    pa.success_rate,
    pa.avg_duration_ms
  FROM n8n.workflow_entity w
  LEFT JOIN pilotpros.process_analytics pa ON w.id = pa.n8n_workflow_id
  WHERE w.active = true
`;
```

---

## 💾 Layer 3: Data Layer

### Database Architecture

#### Schema Separation
```sql
-- Database: pilotpros_db
-- Schema 1: n8n (n8n ownership)
-- Schema 2: pilotpros (application ownership)

-- n8n schema tables:
-- workflow_entity, execution_entity, credentials_entity

-- pilotpros schema tables:
CREATE TABLE pilotpros.process_analytics (
    id SERIAL PRIMARY KEY,
    n8n_workflow_id VARCHAR(255) UNIQUE,
    process_name VARCHAR(255),
    success_rate DECIMAL(5,2),
    avg_duration_ms INTEGER,
    total_executions INTEGER,
    last_execution TIMESTAMP
);

CREATE TABLE pilotpros.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true
);
```

### n8n Integration
- **Port**: 5678 (localhost only)
- **Auth**: Basic auth (admin/pilotpros_admin_2025)
- **Database**: Shared PostgreSQL with schema isolation
- **Webhooks**: Available at `/webhook/*` paths

---

## 🔄 Data Flow

### Request Flow
```
Frontend (3000) → Backend API (3001) → Database (5432)
                                    ↘ n8n API (5678)
```

### Security Isolation
```
Client sees: "Business Process", "Process Run"
Backend translates to: workflow_entity, execution_entity
n8n hidden behind: localhost-only access
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pilotpros_db
DB_USER=pilotpros_user
DB_PASSWORD=secure_password

# n8n
N8N_PORT=5678
N8N_HOST=127.0.0.1
N8N_ADMIN_PASSWORD=pilotpros_admin_2025

# Security
JWT_SECRET=ultra_secure_jwt_secret
BCRYPT_ROUNDS=12
```

---

## 📊 Monitoring

### Health Check Endpoints
- `/health` - System health
- `/api/system/compatibility` - n8n compatibility check
- `/api/business/performance-metrics` - Performance metrics

---

## 🛡️ Current Issues

### ⚠️ CRITICAL: Authentication Disabled
- **Status**: Auth system completely bypassed
- **Impact**: No access control, system insecure
- **Details**: See `docs/AUTH_TECHNICAL_DEBT.md`

---

**Next**: Consultare `deployment.md` per deployment procedures