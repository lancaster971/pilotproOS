# 🤖 PilotProOS Business Intelligence Engine

**AI-Powered Business Analysis & Automation Service**

Servizio di intelligenza artificiale integrato nello stack PilotProOS per analisi avanzate e automazione intelligente dei processi business.

---

## 🎯 **Panoramica**

Il **Business Intelligence Engine** è un microservizio che estende PilotProOS con capacità di AI multi-agente, fornendo analisi intelligenti e automazione avanzata per i processi business.

### **Caratteristiche Principali**
- 🧠 **Analisi AI Multi-Agente**: Powered by CrewAI per analisi complesse
- 🔌 **Integrazione n8n**: Seamless integration con workflow automation
- 🏢 **Business Terminology**: Terminologia orientata al business (no termini tecnici)
- 📊 **Real-time Monitoring**: Monitoraggio esecuzioni in tempo reale
- 🔒 **Enterprise Security**: JWT authentication e audit logging
- 🐳 **Containerized**: Deployment Docker con stack PilotProOS

---

## 🏗️ **Architettura**

### **Stack Integration**
```
Frontend (Vue 3) → Backend (Express) → Business Intelligence Engine → CrewAI
                                  ↓
                              n8n Workflows → HTTP Requests → AI Analysis
```

### **Wrapper Layer Strategy**
- **Core CrewAI**: Libreria originale (upgradabile via pip)
- **PilotProOS Wrapper**: Business abstraction layer
- **Branded API**: Endpoints con terminologia business
- **Zero Conflicts**: Updates CrewAI senza breaking changes

---

## 🚀 **Features**

### **Business Intelligence**
- **Smart Process Analysis**: Analisi intelligente dei workflow business
- **Large Context Processing**: Gestione documenti e dataset complessi
- **Business Insights**: Report e raccomandazioni automatiche
- **Trend Analysis**: Identificazione pattern e anomalie

### **AI Assistants (Agents)**
- **Business Analyst**: Analisi performance e KPI
- **Process Optimizer**: Ottimizzazione workflow
- **Data Interpreter**: Interpretazione dati complessi
- **Report Generator**: Generazione report automatici

### **Integration Points**
- **n8n HTTP Nodes**: Chiamate API dirette dai workflow
- **Backend Service**: Proxy per frontend e API esterne
- **Database Integration**: Salvataggio risultati in PostgreSQL
- **Real-time Updates**: WebSocket per monitoring live

---

## 🔧 **Tecnologie**

### **Core Technologies**
- **FastAPI**: High-performance async API framework
- **CrewAI**: Multi-agent AI orchestration
- **LangChain**: LLM integration and tools
- **PostgreSQL**: Data persistence
- **Docker**: Containerization

### **Security & Monitoring**
- **JWT Authentication**: Shared with PilotProOS backend
- **Health Checks**: Integrated with Stack Controller
- **Audit Logging**: Complete operation tracking
- **Rate Limiting**: Protection against abuse

---

## 📦 **Installation**

Vedi [SETUP.md](./SETUP.md) per istruzioni complete di installazione e configurazione.

### **Quick Start**
```bash
# Nel docker-compose.yml PilotProOS
docker-compose up pilotpros-business-intelligence-dev

# Verifica health
curl http://localhost:8000/health
```

---

## 📚 **Documentazione**

### **Developer Documentation**
- [API.md](./API.md) - Documentazione completa API endpoints
- [INTEGRATION.md](./INTEGRATION.md) - Guida integrazione n8n/backend
- [SETUP.md](./SETUP.md) - Installazione e configurazione

### **Business User Documentation**
- [TEMPLATES.md](./TEMPLATES.md) - Template business pre-configurati
- [WORKFLOWS.md](./WORKFLOWS.md) - Esempi workflow n8n
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Risoluzione problemi comuni

---

## 🔄 **Workflow di Utilizzo**

### **1. Via n8n Workflow**
```
n8n Node → HTTP Request → POST /api/business-intelligence/analyze
                      ← Response with analysis results
```

### **2. Via Backend API**
```javascript
// Backend service call
const analysis = await businessIntelligenceService.analyzeProcess(data);
```

### **3. Via Frontend Dashboard**
```
Business Portal → AI Assistants → Smart Analysis → Real-time Results
```

---

## 🎨 **Business Terminology**

| Technical Term | Business Term |
|----------------|---------------|
| CrewAI Agents | AI Assistants |
| Crews | AI Teams |
| Tasks | Analysis Jobs |
| Executions | Process Runs |
| Endpoints | Service Features |

---

## 📊 **Performance**

### **Resource Usage**
- **Memory**: ~512MB (development)
- **CPU**: 0.5-1.0 cores
- **Startup Time**: ~30 seconds
- **Response Time**: 2-10 seconds (depending on analysis complexity)

### **Scalability**
- **Concurrent Requests**: 50+ (async processing)
- **Queue Management**: Background task processing
- **Load Balancing**: Ready for multiple instances

---

## 🛡️ **Security**

### **Authentication**
- JWT tokens shared with PilotProOS backend
- API key rotation support
- Role-based access control

### **Data Protection**
- No sensitive data logging
- Secure API communication
- Audit trail for all operations

---

## 🔍 **Monitoring**

### **Health Checks**
- **Endpoint**: `GET /health`
- **Stack Controller**: Integrated monitoring
- **Metrics**: CPU, memory, response times
- **Alerts**: Automatic failure detection

### **Logging**
- **Structured Logging**: JSON format
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Audit Trail**: Complete operation history

---

## 🤝 **Contributing**

1. **Wrapper Layer**: Modifiche solo nel wrapper PilotProOS
2. **Core CrewAI**: Non modificare, solo aggiornamenti upstream
3. **Documentation**: Sempre aggiornare docs per nuove features
4. **Testing**: Unit tests per tutti i wrapper

---

## 📄 **License**

Parte del progetto PilotProOS. Vedi LICENSE nel repository principale.

---

**🏢 PilotProOS Business Intelligence Engine - Trasforma i tuoi dati in decisioni intelligenti**