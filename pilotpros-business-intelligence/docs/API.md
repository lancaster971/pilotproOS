# 📡 PilotProOS Business Intelligence API

**Documentazione completa degli endpoints del Business Intelligence Engine**

---

## 🎯 **Base URL**

```
Development: http://localhost:8000
Production:  https://your-domain.com/api/business-intelligence
```

## 🔒 **Autenticazione**

Tutti gli endpoints richiedono autenticazione JWT condivisa con il backend PilotProOS.

```http
Authorization: Bearer <jwt_token>
```

---

## 📊 **Business Intelligence Endpoints**

### **POST /api/business-intelligence/analyze**
Esegue analisi AI intelligente su dati business.

#### **Request**
```json
{
  "type": "process_analysis",
  "data": {
    "workflow_id": "wf_12345",
    "context": "Analizza performance ultimo mese",
    "metadata": {
      "business_area": "sales",
      "priority": "high"
    }
  },
  "options": {
    "analysis_depth": "comprehensive",
    "include_recommendations": true,
    "format": "business_report"
  }
}
```

#### **Response**
```json
{
  "success": true,
  "analysis_id": "analysis_67890",
  "status": "processing",
  "estimated_completion": "2025-01-15T10:30:00Z",
  "data": {
    "message": "Analisi avviata con AI Team Business Analyst",
    "progress_url": "/api/business-intelligence/status/analysis_67890"
  }
}
```

#### **Analysis Types**
- `process_analysis` - Analisi performance processi
- `data_interpretation` - Interpretazione dataset complessi
- `trend_analysis` - Identificazione pattern e tendenze
- `optimization_review` - Raccomandazioni ottimizzazione
- `custom_analysis` - Analisi personalizzata

---

### **GET /api/business-intelligence/status/{analysis_id}**
Monitora lo stato di un'analisi in corso.

#### **Response**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_67890",
    "status": "completed",
    "progress": 100,
    "started_at": "2025-01-15T10:00:00Z",
    "completed_at": "2025-01-15T10:25:00Z",
    "duration_seconds": 1500,
    "ai_team": {
      "business_analyst": "completed",
      "data_interpreter": "completed",
      "report_generator": "completed"
    },
    "results": {
      "summary": "Identificate 3 opportunità di ottimizzazione",
      "confidence_score": 0.92,
      "recommendations_count": 5,
      "data_url": "/api/business-intelligence/results/analysis_67890"
    }
  }
}
```

#### **Status Values**
- `queued` - In coda di elaborazione
- `processing` - Analisi in corso
- `completed` - Completata con successo
- `failed` - Errore durante elaborazione
- `cancelled` - Annullata dall'utente

---

### **GET /api/business-intelligence/results/{analysis_id}**
Recupera i risultati completi di un'analisi.

#### **Response**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_67890",
    "type": "process_analysis",
    "results": {
      "executive_summary": "Il processo sales ha mostrato...",
      "key_insights": [
        {
          "insight": "Bottleneck identificato nel step approval",
          "impact": "high",
          "confidence": 0.95
        }
      ],
      "recommendations": [
        {
          "title": "Automatizza approval per ordini < €1000",
          "description": "Implementare regola automatica...",
          "priority": "high",
          "estimated_impact": "30% riduzione tempo processo",
          "implementation_effort": "medium"
        }
      ],
      "data_analysis": {
        "metrics": {
          "average_process_time": "2.5 days",
          "success_rate": "94%",
          "bottlenecks_detected": 2
        },
        "charts": [
          {
            "type": "timeline",
            "title": "Process Performance Trend",
            "data_url": "/api/business-intelligence/charts/analysis_67890/timeline"
          }
        ]
      }
    },
    "ai_team_notes": {
      "business_analyst": "Pattern ricorrente ogni venerdì...",
      "data_interpreter": "Correlazione con volume ordini...",
      "report_generator": "Report generato in formato business-friendly"
    }
  }
}
```

---

### **POST /api/business-intelligence/templates**
Crea template di analisi riutilizzabili.

#### **Request**
```json
{
  "name": "Sales Performance Weekly",
  "description": "Analisi settimanale performance vendite",
  "type": "process_analysis",
  "template": {
    "analysis_steps": [
      "Calcola KPI vendite settimana corrente",
      "Confronta con settimana precedente",
      "Identifica trend e anomalie",
      "Genera raccomandazioni"
    ],
    "ai_team_config": {
      "business_analyst": {
        "focus": "KPI analysis",
        "tools": ["data_calculator", "trend_analyzer"]
      },
      "report_generator": {
        "format": "executive_summary",
        "charts": ["timeline", "comparison"]
      }
    }
  }
}
```

#### **Response**
```json
{
  "success": true,
  "data": {
    "template_id": "tpl_sales_weekly",
    "name": "Sales Performance Weekly",
    "status": "active",
    "usage_count": 0,
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

---

### **GET /api/business-intelligence/templates**
Lista template disponibili.

#### **Response**
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "template_id": "tpl_sales_weekly",
        "name": "Sales Performance Weekly",
        "description": "Analisi settimanale performance vendite",
        "type": "process_analysis",
        "usage_count": 15,
        "last_used": "2025-01-14T09:00:00Z"
      }
    ],
    "total_count": 1
  }
}
```

---

## 🔧 **System Endpoints**

### **GET /health**
Health check per Stack Controller.

#### **Response**
```json
{
  "status": "healthy",
  "service": "pilotpros-business-intelligence",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:00:00Z",
  "dependencies": {
    "crewai": "healthy",
    "database": "healthy",
    "llm_provider": "healthy"
  },
  "metrics": {
    "active_analyses": 3,
    "queue_size": 1,
    "avg_response_time_ms": 250,
    "uptime_seconds": 86400
  }
}
```

### **GET /metrics**
Metriche per monitoring (Prometheus format).

---

## 🚨 **Error Handling**

### **Error Response Format**
```json
{
  "success": false,
  "error": {
    "code": "ANALYSIS_FAILED",
    "message": "AI team non riuscito a completare analisi",
    "details": {
      "analysis_id": "analysis_67890",
      "failure_stage": "data_interpretation",
      "retry_possible": true
    }
  },
  "timestamp": "2025-01-15T10:00:00Z"
}
```

### **Error Codes**
- `INVALID_REQUEST` - Request malformata
- `AUTHENTICATION_REQUIRED` - Token JWT mancante/invalido
- `ANALYSIS_FAILED` - Errore durante analisi AI
- `RESOURCE_NOT_FOUND` - Analisi/template non trovata
- `RATE_LIMIT_EXCEEDED` - Troppe richieste
- `SERVICE_UNAVAILABLE` - Servizio temporaneamente non disponibile

---

## 🔄 **Rate Limiting**

### **Limits**
- **Analysis Requests**: 10/minuto per utente
- **Status Checks**: 60/minuto per utente
- **Template Operations**: 5/minuto per utente

### **Headers**
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1642234567
```

---

## 📋 **Usage Examples**

### **n8n HTTP Request Node**
```json
{
  "method": "POST",
  "url": "http://pilotpros-business-intelligence-dev:8000/api/business-intelligence/analyze",
  "headers": {
    "Authorization": "Bearer {{$node.auth.token}}",
    "Content-Type": "application/json"
  },
  "body": {
    "type": "process_analysis",
    "data": {
      "workflow_id": "{{$node.Webhook.json.workflow_id}}",
      "context": "Analizza questo processo per inefficienze"
    }
  }
}
```

### **Backend Service Call**
```javascript
// backend/src/services/business-intelligence.service.js
const analysis = await this.httpClient.post('/api/business-intelligence/analyze', {
  type: 'data_interpretation',
  data: processData,
  options: { analysis_depth: 'comprehensive' }
});
```

### **Frontend Dashboard**
```javascript
// frontend/src/services/business-intelligence.api.js
const startAnalysis = async (data) => {
  const response = await apiClient.post('/api/business-intelligence/analyze', data);
  return response.data;
};
```

---

## 🛠️ **Development**

### **Local Testing**
```bash
# Start service
docker-compose up pilotpros-business-intelligence-dev

# Test endpoint
curl -X POST http://localhost:8000/api/business-intelligence/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "process_analysis", "data": {"test": true}}'
```

### **API Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**🔗 Links Utili**
- [README.md](./README.md) - Overview generale
- [INTEGRATION.md](./INTEGRATION.md) - Guida integrazione
- [SETUP.md](./SETUP.md) - Installazione e setup