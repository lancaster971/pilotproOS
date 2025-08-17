# PilotProOS - Business Process Operating System

**Version**: 1.0.0  
**Type**: Containerized Business Appliance  
**Target**: SMB & Mid-Market Companies (10-100 employees)  

---

## 🎯 Overview

**PilotProOS** è un **sistema operativo per processi aziendali** - un appliance software containerizzato che automatizza completamente i workflow business. Progettato per deployment plug-and-play presso aziende che vogliono automazione enterprise senza complessità IT.

### 🚀 **"Operating System" Approach**
Come un OS gestisce le risorse del computer, **PilotProOS gestisce i processi aziendali** della tua organizzazione con un'interfaccia unificata, AI conversazionale e zero configurazione.

### ⚡ Caratteristiche Principali

- **🚀 One-Command Deploy**: `docker run` = sistema operativo in 60 secondi
- **🤖 AI Conversational Interface**: "Mostra i processi attivi", "Crea report settimanale" 
- **🔒 100% White-Label**: Zero technology exposure, interfaccia business-friendly
- **📦 Business Process Templates**: Onboarding clienti, ordini, supporto pre-configurati
- **🛡️ Enterprise Security**: Firewall, SSL, anonimizzazione completa
- **🔄 Real-time Analytics**: Dashboard business con insights automatici

---

## 🏗️ Architettura OS-Style

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PILOTPROS KERNEL                                  │
│                      (Single Docker Container)                              │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  BUSINESS UI    │  │   AI AGENT      │  │      PROCESS ENGINE         │ │
│  │                 │  │                 │  │                             │ │
│  │ • Dashboard     │  │ • Chat Interface│  │ • PostgreSQL Database       │ │
│  │ • Process Mgmt  │  │ • NLP Engine    │  │ • n8n Workflow Engine       │ │
│  │ • Analytics     │  │ • MCP Integration│  │ • Business Logic Layer      │ │
│  │ • Reports       │  │ • Business Lang │  │ • Security & Auth           │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│          │                       │                        │                │
│          └───────────────────────┼────────────────────────┘                │
│                                  │                                         │
│  📱 CLIENT ACCESS: Port 3000 ONLY (Business Interface)                     │
│  🔒 ALL BACKEND: Hidden & Secured (OS manages everything)                  │
│  🔧 DEVELOPER ACCESS: Port 5678 (n8n) - VPN Protected                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Principi OS Design

1. **Single Container Kernel**: Un solo processo gestisce tutto il sistema
2. **Business Interface Only**: Cliente vede solo interfaccia business-friendly  
3. **AI-First Interaction**: Linguaggio naturale per tutte le operazioni
4. **Zero Configuration**: Deploy plug-and-play senza setup tecnico

---

## 📋 Documentazione

### 📚 Documenti Principali

| Documento | Descrizione | Audience |
|-----------|-------------|----------|
| **[ANALYSIS.md](./ANALYSIS.md)** | 📋 Analisi completa architetttura e strategia | Technical & Business |
| **[docs/architecture.md](./docs/architecture.md)** | 🏗️ Dettagli tecnici architettura 3-layer | Technical Team |
| **[docs/deployment.md](./docs/deployment.md)** | 🚀 Strategie deployment scalabile | DevOps & Operations |
| **[docs/security.md](./docs/security.md)** | 🔒 Sistema anonimizzazione e sicurezza | Security Team |
| **[docs/workflows.md](./docs/workflows.md)** | ⚙️ Sistema workflow templates | Business & Technical |

### 📝 Documenti di Pianificazione

| Documento | Descrizione | Status |
|-----------|-------------|--------|
| **[planning/component-migration.md](./planning/component-migration.md)** | Migrazione componenti da progetto esistente | 📋 Planning |
| **[planning/database-schema.md](./planning/database-schema.md)** | Schema database unificato | 📋 Planning |
| **[planning/deployment-scripts.md](./planning/deployment-scripts.md)** | Specifica 4 script deployment | 📋 Planning |

---

## 🚀 Quick Start

### Prerequisiti
- **Node.js**: 18.0.0+ LTS
- **npm**: 8.0.0+
- **PostgreSQL**: 16+ (brew install postgresql@16)
- **Sistema**: macOS, Linux, o Windows con WSL

### Setup Automatico Completo
```bash
# Clone repository
git clone https://github.com/lancaster971/pilotproOS.git
cd pilotproOS

# Install dependencies
npm run install:all

# Setup PostgreSQL + n8n (first time only)
npm run n8n:setup

# Start development environment
npm run dev
```

### Accesso Sistema
- **Business Interface**: http://localhost:3000
- **Backend API**: http://localhost:3001
- **AI Agent**: http://localhost:3002
- **n8n Workflows** (dev only): http://localhost:5678

### 🛠️ Development Commands
```bash
# Individual services
npm run dev:frontend    # React + Vite (port 3000)
npm run dev:backend     # Express API (port 3001)  
npm run dev:ai-agent    # MCP Agent (port 3002)
npm run dev:n8n         # Workflow Engine (port 5678)

# n8n Management
npm run n8n:start       # Start n8n server
npm run n8n:stop        # Stop n8n server

# Database access
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
psql pilotpros_db       # Connect to database
```

### 🚀 Production Deployment
```bash
# Step 1: System Infrastructure (60s)
./scripts/01-system-setup.sh

# Step 2: Application Stack (120s)  
./scripts/02-application-deploy.sh

# Step 3: Security Hardening (90s)
./scripts/03-security-hardening.sh

# Step 4: Workflow Loading (60s)
./scripts/04-workflow-automation.sh
```

---

## 🔧 Configurazione

### Environment Configuration
```bash
# PostgreSQL Database
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=localhost
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=pilotpros_db
DB_POSTGRESDB_USER=pilotpros_user
DB_POSTGRESDB_SCHEMA=n8n

# n8n Configuration (v1.106.3)
N8N_PORT=5678
N8N_HOST=127.0.0.1
N8N_BASIC_AUTH_ACTIVE=true
N8N_RUNNERS_ENABLED=true
WEBHOOK_URL=http://localhost:5678

# Backend API
PORT=3001
JWT_SECRET=auto-generated-secure-key

# AI Agent
AI_AGENT_PORT=3002

# Security
N8N_DIAGNOSTICS_ENABLED=false
N8N_ANONYMOUS_TELEMETRY=false
N8N_PERSONALIZATION_ENABLED=false
```

### Client Branding
```javascript
// config/client-branding.js
module.exports = {
  appName: "Business Process Automation",
  companyName: "Client Company Name",
  logoUrl: "/assets/client-logo.png",
  primaryColor: "#007bff",
  supportEmail: "support@client-domain.com",
  
  // Terminology mapping (anonimizzazione)
  terminology: {
    workflows: "Business Processes",
    executions: "Process Runs",
    nodes: "Process Steps"
  }
};
```

---

## 📦 Workflow Templates

### Template Business Disponibili

| Template | Descrizione | Settore | Setup Time |
|----------|-------------|---------|------------|
| **Customer Onboarding** | Processo registrazione e welcome | General | 5 min |
| **Order Processing** | Gestione ordini automatica | E-commerce | 10 min |
| **Invoice Automation** | Fatturazione automatica | Finance | 15 min |
| **Support Ticket** | Routing ticket assistenza | Customer Service | 5 min |
| **Email Marketing** | Campagne email automatiche | Marketing | 20 min |
| **Data Integration** | Sync tra sistemi | IT/Data | 30 min |

### Caricamento Automatico
```bash
# I template vengono caricati automaticamente durante deployment
# Path: /templates/client-workflows/*.json

# Customizzazione per cliente
./scripts/customize-workflows.sh client-config.json
```

---

## 🔒 Sicurezza & Compliance

### Security Features
- ✅ **SSL/HTTPS**: Certificati automatici Let's Encrypt
- ✅ **Firewall**: Porte backend completamente bloccate
- ✅ **Authentication**: JWT enterprise-grade
- ✅ **Rate Limiting**: Protezione DDoS/brute force
- ✅ **Security Headers**: OWASP compliance
- ✅ **Zero Tech Exposure**: Tecnologie completamente nascoste

### Compliance Standards
- 🛡️ **GDPR Ready**: Data privacy by design
- 🛡️ **SOC 2**: Security controls implementation
- 🛡️ **ISO 27001**: Information security management
- 🛡️ **OWASP Top 10**: Web application security

---

## 📊 Monitoring & Maintenance

### Health Monitoring
```bash
# Sistema health check
./scripts/health-check.sh

# Expected output:
# ✅ PostgreSQL: Running (connections: 5/100)
# ✅ n8n Server: Running (workflows: 12 active)  
# ✅ Backend API: Running (response time: 45ms)
# ✅ Frontend: Running (nginx: active)
# ✅ SSL Certificate: Valid (expires: 89 days)
```

### Backup Automatico
- **Schedule**: Ogni 6 ore
- **Retention**: 30 giorni rolling
- **Location**: `/opt/workflow-system/backups/`
- **Includes**: Database, workflow configs, system settings

### Log Management
```bash
# Application logs
tail -f /opt/workflow-system/logs/backend.log
tail -f /opt/workflow-system/logs/n8n.log

# System logs
journalctl -f -u workflow-system
```

---

## 🛠️ Development & Customization

### Local Development Setup
```bash
# Clone e setup development environment
git clone <oneserver-repo>
cd ONESERVER
npm run dev:setup

# Start development stack
npm run dev:stack
# Backend: http://localhost:3001
# Frontend: http://localhost:3000
# n8n: http://localhost:5678
```

### Customization Points
1. **Frontend Branding**: Logo, colori, terminologia
2. **Workflow Templates**: Processi business-specific  
3. **Integration Endpoints**: Connessioni sistemi cliente
4. **Email Templates**: Comunicazioni personalizzate
5. **Reporting Dashboard**: KPI business specifici

---

## 📞 Support & Documentation

### Technical Support
- 📧 **Email**: tech-support@your-company.com
- 📚 **Documentation**: Complete in `/docs/` folder
- 🎯 **Best Practices**: Industry-specific guides available
- 🚨 **Emergency**: 24/7 enterprise support available

### Training Resources
- 🎓 **Admin Training**: Sistema management e configurazione
- 🏢 **Business User Training**: Workflow creation e management
- 🔧 **Developer Training**: Customization e integration
- 📊 **Analytics Training**: Dashboard e reporting avanzato

---

## 🚀 Roadmap

### Versione 1.1 (Q2 2025)
- ✨ **Advanced Analytics**: Machine learning insights
- 🔄 **Multi-region**: Deployment geografico distribuito
- 📱 **Mobile App**: iOS/Android companion app
- 🤖 **AI Assistant**: Conversational workflow builder

### Versione 2.0 (Q4 2025)  
- ☁️ **Cloud Native**: Kubernetes auto-scaling
- 🔗 **Blockchain**: Smart contract integration
- 🎯 **Predictive Analytics**: AI-powered process optimization
- 🌐 **Global Marketplace**: Workflow template ecosystem

---

## 📄 License & Copyright

**Copyright** © 2025 Enterprise Workflow Solutions  
**License**: Commercial Enterprise License  
**Support**: Enterprise support included

---

**🎯 Ready to deploy your first ONESERVER instance?**  
**👉 Start with: `./deploy-client.sh your-domain.com`**