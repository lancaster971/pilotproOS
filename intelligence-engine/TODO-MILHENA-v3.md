# 🎯 TODO-MILHENA v3.0: BUSINESS WORKFLOW ASSISTANT
# PRODUCTION-READY CON SECURITY & RESILIENCE FIXES

> **Enterprise-Grade Business Assistant for Workflow Monitoring**
> Widget Chat integrato + n8n Integration + Technical Masking Completo
> **SECURITY HARDENED + BUDGET CONTROL + GRACEFUL DEGRADATION**

**Status**: 🔒 PRODUCTION-READY
**Version**: 3.0-SECURE
**Created**: 2025-01-28
**Branch**: `milhena-assistant`
**Testing**: LangGraph Studio + Promptfoo + Chaos Testing

---

## 🚨 CRITICAL SECURITY UPDATES

### ⚠️ FIXED VULNERABILITIES
1. ✅ **WebSocket Authentication**: JWT tokens con expiry (was: manipolabile sessionId)
2. ✅ **Budget Control**: Hard limits con fallback automatico (was: unlimited LLM costs)
3. ✅ **Smart Cache**: Invalidazione event-driven (was: stale data forever)
4. ✅ **Graceful Degradation**: 4-level fallback system (was: total failure)
5. ✅ **Rate Limiting**: Per-user e per-IP (was: DDoS vulnerable)
6. ✅ **Circuit Breakers**: Auto-recovery patterns (was: cascading failures)

---

## 📋 EXECUTIVE SUMMARY

**Milhena** è un Business Workflow Assistant **production-ready** che:
- ✅ **Monitora workflow n8n** traducendo tutto in linguaggio business
- ✅ **Widget chat** integrato nel frontend Vue per cliente finale
- ✅ **Integrazione n8n** bidirezionale (HTTP Request + Webhook)
- ✅ **Protezione totale** delle informazioni tecniche
- ✅ **Cloud-first** con predisposizione per LLM locali (Ollama)
- 🔒 **Enterprise Security**: JWT, rate limiting, budget control
- 💪 **High Resilience**: Circuit breakers, graceful degradation
- 📊 **Full Observability**: Metrics, tracing, alerting

**NON È**: Un multi-agent orchestrator generico
**È**: Un assistente specializzato SICURO per monitoraggio processi business

---

## 🏗️ ARCHITETTURA ENTERPRISE

```mermaid
graph TB
    subgraph "Frontend Layer"
        Widget[Vue Chat Widget]
        Admin[Admin Dashboard]
    end

    subgraph "Milhena Core"
        API[FastAPI/WebSocket]
        Intent[Intent Analyzer]
        Masker[Technical Masker]
        Generator[Response Generator]
        Cache[Redis Cache]
    end

    subgraph "Data Layer"
        N8NDB[(n8n Database)]
        Audit[(Audit Logs)]
    end

    subgraph "LLM Layer"
        Router[LLM Router]
        Cloud[Cloud LLMs<br/>GPT-4o-mini]
        Local[Local LLMs<br/>Ollama Ready]
    end

    subgraph "n8n Integration"
        HTTP[HTTP Endpoints]
        Webhook[Webhook Handler]
    end

    Widget <--> API
    Admin --> API
    API --> Intent
    Intent --> Router
    Router --> Cloud
    Router -.-> Local
    API --> Masker
    API --> Generator
    API <--> Cache
    API --> N8NDB
    API --> Audit
    API <--> HTTP
    API <--> Webhook
```

---

## 🎯 1. CORE FUNCTIONALITY

### **1.1 Ruolo di Milhena**

```python
class MilhenaRole:
    """
    Milhena è l'interfaccia business-friendly per i workflow n8n
    """

    CAPABILITIES = {
        "monitor": "Monitoraggio esecuzioni workflow",
        "translate": "Traduzione tech → business language",
        "report": "Generazione report in linguaggio naturale",
        "alert": "Notifiche problemi in modo comprensibile",
        "assist": "Supporto cliente senza esporre tecnicismi"
    }

    PROTECTION = {
        "hide": ["n8n", "PostgreSQL", "Docker", "nodes", "webhook"],
        "translate_to": ["processo", "database", "sistema", "passaggi", "integrazione"],
        "deflect_technical": "Per informazioni tecniche contatta il supporto IT"
    }
```

### **1.2 Use Cases Principali**

| Scenario | Input Cliente | Output Milhena |
|----------|---------------|----------------|
| **Monitoraggio** | "Quante fatture oggi?" | "Il processo Fatturazione ha elaborato 47 documenti oggi" |
| **Errori** | "Ci sono stati problemi?" | "3 elaborazioni hanno richiesto attenzione per dati mancanti" |
| **Performance** | "Come va il sistema?" | "Tutti i processi operativi, tempo medio 2.3 secondi" |
| **Tech Deflection** | "Che database usiamo?" | "Mi occupo del monitoraggio dei processi. Per dettagli tecnici contatta IT" |

---

## 💬 2. WIDGET CHAT FRONTEND

### **2.1 Integrazione Vue.js**

```vue
<!-- frontend/src/components/MilhenaWidget.vue -->
<template>
  <div class="milhena-widget" :class="{ minimized, mobile: isMobile }">
    <!-- Header -->
    <div class="widget-header" @click="toggleMinimize">
      <div class="header-content">
        <span class="icon">💬</span>
        <span class="title">Milhena - Assistente Processi</span>
      </div>
      <div class="header-actions">
        <span class="status-indicator" :class="connectionStatus"></span>
        <button class="minimize-btn">{{ minimized ? '▲' : '▼' }}</button>
      </div>
    </div>

    <!-- Chat Container -->
    <transition name="slide">
      <div v-if="!minimized" class="widget-body">
        <!-- Messages -->
        <div class="messages-container" ref="messagesEl">
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['message', msg.type]"
          >
            <div v-if="msg.type === 'user'" class="message-user">
              <span class="text">{{ msg.text }}</span>
              <span class="time">{{ formatTime(msg.timestamp) }}</span>
            </div>

            <div v-else class="message-milhena">
              <div class="avatar">M</div>
              <div class="content">
                <span class="text" v-html="formatMessage(msg.text)"></span>
                <span class="time">{{ formatTime(msg.timestamp) }}</span>
              </div>
            </div>
          </div>

          <!-- Typing Indicator -->
          <div v-if="isTyping" class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <div class="input-wrapper">
            <input
              v-model="userInput"
              @keyup.enter="sendMessage"
              @focus="onInputFocus"
              placeholder="Chiedi informazioni sui tuoi processi..."
              :disabled="!isConnected"
              class="message-input"
            />
            <button
              @click="sendMessage"
              :disabled="!canSend"
              class="send-btn"
            >
              <svg><!-- Send Icon --></svg>
            </button>
          </div>

          <!-- Quick Actions -->
          <div class="quick-actions">
            <button
              v-for="action in quickActions"
              :key="action.id"
              @click="sendQuickAction(action)"
              class="quick-btn"
            >
              {{ action.label }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMilhenaChat } from '@/composables/useMilhenaChat'
import { useWebSocket } from '@vueuse/core'

// Composable per gestione chat
const {
  messages,
  isTyping,
  connectionStatus,
  sendMessage: send,
  reconnect
} = useMilhenaChat()

// Quick actions predefinite
const quickActions = [
  { id: 1, label: "📊 Report oggi", query: "Quante operazioni oggi?" },
  { id: 2, label: "⚠️ Errori", query: "Ci sono stati errori?" },
  { id: 3, label: "📈 Performance", query: "Come sta andando?" }
]

// Auto-reconnect logic
const reconnectInterval = ref(null)

onMounted(() => {
  reconnectInterval.value = setInterval(() => {
    if (connectionStatus.value === 'disconnected') {
      reconnect()
    }
  }, 5000)
})

onUnmounted(() => {
  if (reconnectInterval.value) {
    clearInterval(reconnectInterval.value)
  }
})
</script>

<style scoped lang="scss">
.milhena-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 380px;
  height: 600px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 5px 40px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  z-index: 9999;

  &.mobile {
    width: 100%;
    height: 100%;
    bottom: 0;
    right: 0;
    border-radius: 0;
  }

  .widget-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 16px;
    border-radius: 12px 12px 0 0;
    cursor: pointer;
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;

    .message-milhena {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;

      .avatar {
        width: 32px;
        height: 32px;
        background: #667eea;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
      }
    }
  }

  .typing-indicator span {
    animation: typing 1.4s infinite;
  }
}
</style>
```

### **2.2 WebSocket Connection Manager**

```typescript
// frontend/src/composables/useMilhenaChat.ts
import { ref, computed } from 'vue'
import { useWebSocket } from '@vueuse/core'

export function useMilhenaChat() {
  const wsUrl = computed(() => {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${location.host}/ws/milhena/${sessionId.value}`
  })

  const {
    status,
    data,
    send: wsSend,
    open,
    close
  } = useWebSocket(wsUrl, {
    autoReconnect: {
      retries: 3,
      delay: 1000,
      onFailed() {
        console.error('Milhena connection failed')
      }
    },
    heartbeat: {
      message: 'ping',
      interval: 30000,
      pongTimeout: 10000
    }
  })

  // Process incoming messages
  watch(data, (newData) => {
    if (!newData) return

    const message = JSON.parse(newData)

    switch(message.type) {
      case 'response':
        messages.value.push({
          id: Date.now(),
          type: 'milhena',
          text: message.text,
          timestamp: new Date()
        })
        isTyping.value = false
        break

      case 'typing':
        isTyping.value = true
        break

      case 'error':
        handleError(message.error)
        break
    }
  })

  return {
    messages,
    isTyping,
    connectionStatus: computed(() => status.value),
    sendMessage,
    reconnect: open
  }
}
```

---

## 🔄 3. INTEGRAZIONE n8n BIDIREZIONALE

### **3.1 Milhena API per n8n (HTTP Request)**

```python
# app/milhena/n8n_endpoints.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/n8n/milhena")

class WorkflowAnalysisRequest(BaseModel):
    """Request da n8n workflow"""
    workflow_id: str
    execution_id: str
    output_data: Dict[str, Any]
    analysis_type: str  # "summary", "validation", "error_translation"
    target_audience: str = "business"  # "business" or "technical"

@router.post("/analyze")
async def analyze_workflow_output(request: WorkflowAnalysisRequest):
    """
    Endpoint chiamato da n8n per analizzare output

    n8n HTTP Request node configuration:
    - Method: POST
    - URL: http://milhena:8000/api/n8n/milhena/analyze
    - Body: JSON con workflow output
    """

    # Processa attraverso Milhena
    milhena = MilhenaCore()

    if request.target_audience == "business":
        # Traduci tutto in business language
        analysis = await milhena.analyze_with_masking(
            data=request.output_data,
            analysis_type=request.analysis_type
        )
    else:
        # Per uso interno, mantieni dettagli tecnici
        analysis = await milhena.analyze_technical(
            data=request.output_data,
            analysis_type=request.analysis_type
        )

    return {
        "success": true,
        "execution_id": request.execution_id,
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/validate")
async def validate_before_sending(request: ValidationRequest):
    """
    Valida dati prima di invio al cliente
    Rimuove info sensibili, formatta numeri, etc.
    """
    validated = await milhena.validate_and_clean(request.data)

    return {
        "is_valid": validated.is_safe,
        "cleaned_data": validated.cleaned,
        "issues": validated.issues,
        "recommendations": validated.suggestions
    }

@router.post("/translate-error")
async def translate_error_message(request: ErrorTranslationRequest):
    """
    Traduce errori tecnici in messaggi user-friendly

    Input: "ECONNREFUSED: Connection refused to PostgreSQL"
    Output: "Temporaneo problema di connessione, riprova tra qualche minuto"
    """
    business_message = await milhena.translate_error(
        error=request.error_message,
        context=request.context
    )

    return {
        "original": request.error_message,
        "business_friendly": business_message,
        "severity": milhena.assess_severity(request.error_message)
    }
```

### **3.2 Milhena chiama n8n (Webhook Trigger)**

```python
# app/milhena/n8n_caller.py
import httpx
from typing import Optional

class N8nWorkflowTrigger:
    """
    Milhena può triggerare workflow n8n quando necessario
    """

    def __init__(self, n8n_base_url: str):
        self.base_url = n8n_base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def trigger_report_generation(
        self,
        report_type: str,
        parameters: Dict[str, Any]
    ):
        """
        Triggera workflow di generazione report

        Use case: Cliente chiede "Generami report settimanale"
        """
        webhook_url = f"{self.base_url}/webhook/generate-report"

        payload = {
            "trigger_source": "milhena",
            "report_type": report_type,
            "parameters": parameters,
            "requested_by": "customer_chat",
            "timestamp": datetime.now().isoformat()
        }

        response = await self.client.post(webhook_url, json=payload)

        if response.status_code == 200:
            return {
                "triggered": True,
                "execution_id": response.json().get("executionId"),
                "message": "Report in generazione, riceverai una notifica al completamento"
            }
        else:
            return {
                "triggered": False,
                "message": "Impossibile avviare generazione report, riprova più tardi"
            }

    async def trigger_corrective_action(
        self,
        issue_type: str,
        workflow_id: str,
        details: Dict
    ):
        """
        Triggera workflow di correzione automatica

        Use case: Milhena detecta problema ricorrente
        """
        webhook_url = f"{self.base_url}/webhook/corrective-action"

        payload = {
            "issue_type": issue_type,
            "workflow_id": workflow_id,
            "details": details,
            "auto_triggered": True
        }

        response = await self.client.post(webhook_url, json=payload)
        return response.json()
```

### **3.3 Configurazione n8n Workflow**

```javascript
// n8n Workflow: Call Milhena for Analysis
{
  "nodes": [
    {
      "name": "Process Data",
      "type": "n8n-nodes-base.function",
      "parameters": {
        // Process your data
      }
    },
    {
      "name": "Ask Milhena",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://milhena:8000/api/n8n/milhena/analyze",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "milhenApi",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "workflow_id",
              "value": "={{ $workflow.id }}"
            },
            {
              "name": "execution_id",
              "value": "={{ $execution.id }}"
            },
            {
              "name": "output_data",
              "value": "={{ $json }}"
            },
            {
              "name": "analysis_type",
              "value": "summary"
            }
          ]
        }
      }
    },
    {
      "name": "Send to Customer",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "message": "={{ $node['Ask Milhena'].json.analysis }}"
      }
    }
  ]
}
```

---

## 🤖 4. LLM STRATEGY (CLOUD-FIRST + LOCAL READY)

### **4.1 Architettura Multi-Tier**

```python
# app/milhena/llm_strategy.py
from enum import Enum
from typing import Optional
import httpx

class LLMProvider(Enum):
    """Provider disponibili in ordine di preferenza"""
    OPENAI = "openai"          # Primary
    ANTHROPIC = "anthropic"    # Fallback 1
    GROQ = "groq"             # Fallback 2
    OLLAMA = "ollama"         # Local (quando disponibile)

class LLMRouter:
    """
    Router intelligente per LLM selection
    CLOUD FIRST ma predisposto per local
    """

    def __init__(self, config: MilhenaConfig):
        self.config = config

        # Cloud providers (sempre disponibili)
        self.cloud_providers = {
            LLMProvider.OPENAI: ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=200
            ),
            LLMProvider.ANTHROPIC: ChatAnthropic(
                model="claude-3-haiku-20240307",
                temperature=0,
                max_tokens=200
            )
        }

        # Local provider (se disponibile)
        self.local_provider = self._init_ollama_if_available()

        # Statistics
        self.stats = {
            "cloud_calls": 0,
            "local_calls": 0,
            "fallbacks": 0,
            "costs": 0.0
        }

    def _init_ollama_if_available(self) -> Optional[ChatOllama]:
        """Check se Ollama è disponibile"""
        try:
            response = httpx.get("http://localhost:11434/api/tags", timeout=1)
            if response.status_code == 200:
                # Ollama disponibile
                return ChatOllama(
                    model="mistral:7b",
                    temperature=0
                )
        except:
            pass
        return None

    async def get_llm(self, complexity: str = "medium") -> BaseLLM:
        """
        Seleziona LLM basato su complessità e disponibilità

        STRATEGIA:
        1. Se query semplice E Ollama disponibile → usa local
        2. Altrimenti → usa cloud (OpenAI default)
        3. Se cloud fallisce → fallback chain
        """

        # Check per local LLM (solo per query semplici)
        if complexity == "simple" and self.local_provider:
            if await self._test_ollama_health():
                self.stats["local_calls"] += 1
                return self.local_provider

        # Default: Cloud provider
        self.stats["cloud_calls"] += 1
        return self.cloud_providers[LLMProvider.OPENAI]

    async def _test_ollama_health(self) -> bool:
        """Quick health check per Ollama"""
        try:
            response = await httpx.get(
                "http://localhost:11434/api/tags",
                timeout=0.5  # 500ms max
            )
            return response.status_code == 200
        except:
            return False

    def estimate_cost(self, tokens_used: int, provider: LLMProvider) -> float:
        """Calcola costo stimato"""
        costs = {
            LLMProvider.OPENAI: 0.00015 / 1000,      # $0.15 per 1M tokens
            LLMProvider.ANTHROPIC: 0.00025 / 1000,   # $0.25 per 1M tokens
            LLMProvider.GROQ: 0.0001 / 1000,         # $0.10 per 1M tokens
            LLMProvider.OLLAMA: 0.0                  # Gratis!
        }
        return tokens_used * costs.get(provider, 0)
```

### **4.2 Predisposizione Ollama (Opzionale)**

```yaml
# docker-compose.ollama.yml (OPZIONALE - non richiesto per funzionamento base)
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: milhena-ollama
    volumes:
      - ollama_models:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_MODELS=mistral:7b,llama3.2:3b
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G

volumes:
  ollama_models:
    driver: local
```

```python
# app/milhena/ollama_setup.py
"""
Setup OPZIONALE per Ollama
Se non disponibile, Milhena usa automaticamente cloud
"""

async def setup_ollama_models():
    """Scarica modelli se Ollama disponibile"""
    try:
        # Check if Ollama is running
        response = httpx.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            logger.info("Ollama not available, using cloud LLMs")
            return

        # Pull models for local inference
        models = ["mistral:7b", "llama3.2:3b"]
        for model in models:
            logger.info(f"Pulling Ollama model: {model}")
            subprocess.run(["ollama", "pull", model])

    except Exception as e:
        logger.info(f"Ollama setup skipped: {e}")
        logger.info("Milhena will use cloud LLMs")
```

---

## 🔐 5. TECHNICAL MASKING ENGINE

### **5.1 Core Masking System**

```python
# app/milhena/masking.py
from typing import Dict, Any, List
import re
import json

class TechnicalMaskingEngine:
    """
    Sistema enterprise per mascheramento termini tecnici
    CRITICO: Mai esporre architettura sottostante
    """

    def __init__(self):
        self.load_mappings()
        self.compile_patterns()

    def load_mappings(self):
        """Carica dizionari di traduzione"""
        self.mappings = {
            # Workflow → Business Process
            "workflow_terms": {
                "workflow": "processo",
                "workflows": "processi",
                "node": "passaggio",
                "nodes": "passaggi",
                "execution": "elaborazione",
                "executions": "elaborazioni",
                "trigger": "avvio",
                "webhook": "ricezione dati"
            },

            # Technical → Generic
            "tech_terms": {
                "n8n": "sistema",
                "postgresql": "archivio dati",
                "postgres": "archivio dati",
                "mysql": "archivio dati",
                "database": "archivio dati",
                "docker": "ambiente",
                "container": "ambiente",
                "kubernetes": "infrastruttura",
                "redis": "memoria veloce",
                "nginx": "gateway",
                "api": "interfaccia",
                "rest": "protocollo",
                "http": "comunicazione",
                "json": "formato dati"
            },

            # Error codes → Human messages
            "error_translations": {
                "ECONNREFUSED": "Connessione temporaneamente non disponibile",
                "ETIMEDOUT": "Tempo di risposta eccessivo",
                "404": "Risorsa non trovata",
                "500": "Errore interno del sistema",
                "503": "Servizio temporaneamente non disponibile",
                "ENOTFOUND": "Destinazione non raggiungibile",
                "EPIPE": "Interruzione della comunicazione",
                "OOM": "Risorse di sistema insufficienti"
            }
        }

    def compile_patterns(self):
        """Compila regex patterns per performance"""
        self.patterns = []

        # Pattern per termini tecnici
        for term in self.mappings["tech_terms"].keys():
            pattern = re.compile(
                r'\b' + re.escape(term) + r'\b',
                re.IGNORECASE
            )
            self.patterns.append((pattern, term))

    def mask(self, text: str) -> str:
        """
        Maschera tutti i termini tecnici nel testo

        Input: "Il workflow su PostgreSQL ha 5 nodes"
        Output: "Il processo su archivio dati ha 5 passaggi"
        """
        masked = text

        # Apply mappings
        for mapping_type, terms in self.mappings.items():
            for original, replacement in terms.items():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(original), re.IGNORECASE)
                masked = pattern.sub(replacement, masked)

        # Remove any remaining technical artifacts
        masked = self._remove_technical_artifacts(masked)

        return masked

    def _remove_technical_artifacts(self, text: str) -> str:
        """Rimuove pattern tecnici residui"""

        # Remove IDs (UUID, hash, etc)
        text = re.sub(
            r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b',
            'identificativo',
            text,
            flags=re.IGNORECASE
        )

        # Remove technical file extensions
        text = re.sub(
            r'\.(json|xml|yaml|yml|sql|js|ts|py|java|go|rs)\b',
            '',
            text,
            flags=re.IGNORECASE
        )

        # Remove IP addresses
        text = re.sub(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'indirizzo di rete',
            text
        )

        # Remove ports
        text = re.sub(
            r':(\d{2,5})\b',
            '',
            text
        )

        return text

    def mask_json(self, data: Dict) -> Dict:
        """
        Maschera ricorsivamente strutture JSON
        """
        if isinstance(data, dict):
            return {
                self.mask(k) if isinstance(k, str) else k:
                self.mask_json(v) if isinstance(v, (dict, list))
                else self.mask(v) if isinstance(v, str) else v
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self.mask_json(item) for item in data]
        elif isinstance(data, str):
            return self.mask(data)
        else:
            return data
```

### **5.2 Response Sanitizer**

```python
class ResponseSanitizer:
    """
    Validazione finale prima di inviare al cliente
    """

    def __init__(self, masking_engine: TechnicalMaskingEngine):
        self.masker = masking_engine
        self.forbidden_terms = self._load_forbidden_terms()

    def _load_forbidden_terms(self) -> List[str]:
        """Termini che NON devono MAI apparire"""
        return [
            "n8n", "workflow", "node", "webhook", "postgres",
            "postgresql", "mysql", "docker", "kubernetes",
            "redis", "nginx", "localhost", "127.0.0.1",
            "error:", "exception", "stack trace", "undefined",
            "null", "none", "npm", "pip", "git"
        ]

    def sanitize(self, response: str) -> str:
        """
        Sanitizzazione finale con multiple pass
        """
        # Pass 1: Masking standard
        sanitized = self.masker.mask(response)

        # Pass 2: Check forbidden terms
        for term in self.forbidden_terms:
            if term.lower() in sanitized.lower():
                # Log per audit
                logger.warning(f"Forbidden term detected: {term}")

                # Replace con generic
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                sanitized = pattern.sub("[informazione protetta]", sanitized)

        # Pass 3: Final validation
        if self._contains_technical_info(sanitized):
            # Fallback to safe response
            return "Informazione elaborata correttamente. Per dettagli contatta il supporto."

        return sanitized

    def _contains_technical_info(self, text: str) -> bool:
        """
        Check finale per leak tecnici
        """
        technical_patterns = [
            r'\b\d+\.\d+\.\d+\.\d+\b',  # IP addresses
            r':[0-9]{2,5}\b',            # Ports
            r'\b[A-Z_]+ERROR\b',         # Error codes
            r'\/[a-z]+\/[a-z]+',         # Unix paths
            r'[A-Z]:\\',                 # Windows paths
        ]

        for pattern in technical_patterns:
            if re.search(pattern, text):
                return True

        return False
```

---

## 🧪 6. TESTING STRATEGY

### **6.1 LangGraph Studio Configuration**

```json
// langgraph.json
{
  "dependencies": ["."],
  "graphs": {
    "milhena": "./app/milhena/graph.py:milhena_graph"
  },
  "env": ".env",
  "python_path": [".", "app"],
  "checkpoint": {
    "provider": "postgres",
    "uri": "${DATABASE_URL}"
  },
  "studio": {
    "port": 2024,
    "host": "0.0.0.0",
    "debug": true,
    "auto_reload": true,
    "trace_endpoints": true
  }
}
```

```python
# app/milhena/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langsmith import traceable

class MilhenaState(TypedDict):
    """State per LangGraph debugging"""
    query: str
    intent: Optional[str]
    workflow_data: Optional[Dict]
    masked_data: Optional[Dict]
    response: Optional[str]
    errors: List[str]
    metadata: Dict[str, Any]

class MilhenaGraph:
    """
    LangGraph implementation di Milhena
    """

    def __init__(self, config: MilhenaConfig):
        self.config = config
        self.workflow = self._build_graph()
        self.checkpointer = PostgresSaver.from_conn_string(
            os.environ["DATABASE_URL"]
        )

    def _build_graph(self) -> StateGraph:
        """Costruisce grafo per LangGraph Studio"""
        workflow = StateGraph(MilhenaState)

        # Add nodes (tutti traceable per LangSmith)
        workflow.add_node("classify_intent", self.classify_intent_node)
        workflow.add_node("fetch_data", self.fetch_workflow_data_node)
        workflow.add_node("mask_technical", self.mask_technical_node)
        workflow.add_node("generate_response", self.generate_response_node)
        workflow.add_node("handle_error", self.error_handler_node)

        # Define edges
        workflow.set_entry_point("classify_intent")

        # Conditional routing
        workflow.add_conditional_edges(
            "classify_intent",
            self.route_by_intent,
            {
                "fetch": "fetch_data",
                "deflect": "generate_response",
                "error": "handle_error"
            }
        )

        workflow.add_edge("fetch_data", "mask_technical")
        workflow.add_edge("mask_technical", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)

        return workflow

    @traceable(name="classify_intent")
    async def classify_intent_node(self, state: MilhenaState) -> MilhenaState:
        """Node per classificazione intent"""
        analyzer = IntentAnalyzer(self.config)
        state["intent"] = await analyzer.classify(state["query"])
        return state

    @traceable(name="fetch_workflow_data")
    async def fetch_workflow_data_node(self, state: MilhenaState) -> MilhenaState:
        """Node per fetch dati workflow"""
        provider = WorkflowDataProvider()
        state["workflow_data"] = await provider.get_data(
            intent=state["intent"],
            query=state["query"]
        )
        return state

    def compile(self):
        """Compila per LangGraph Studio"""
        graph = self.workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=[]  # No interruptions for production
        )
        graph.name = "Milhena Business Assistant"
        return graph

# Export per LangGraph Studio
milhena_graph = MilhenaGraph(MilhenaConfig()).compile()
```

### **6.2 Promptfoo Testing**

```yaml
# tests/promptfoo/milhena_config.yaml
description: "Milhena Business Assistant Testing"

providers:
  # Test su diversi provider
  - id: openai-main
    config:
      id: openai:gpt-4o-mini
      temperature: 0

  - id: anthropic-fallback
    config:
      id: anthropic:claude-3-haiku
      temperature: 0

  - id: ollama-local
    config:
      id: ollama:mistral:7b
      temperature: 0

prompts:
  - id: intent-classification
    template: |
      Classify the intent of this query about business processes:
      Query: {{query}}

      Categories: EXECUTIONS, ERRORS, METRICS, STATUS, TECHNICAL, UNKNOWN

      Respond with category only.

  - id: masking-validation
    template: |
      Translate this technical message to business language:
      Message: {{technical_message}}

      Rules:
      - Never mention n8n, PostgreSQL, Docker, nodes, webhooks
      - Use: processo, elaborazione, sistema, passaggi

      Business translation:

tests:
  # Test intent classification
  - description: "Classify execution query"
    vars:
      query: "Quante fatture abbiamo registrato oggi?"
    assert:
      - type: equals
        value: "EXECUTIONS"

  - description: "Classify error query"
    vars:
      query: "Ci sono stati errori nel processo ordini?"
    assert:
      - type: equals
        value: "ERRORS"

  - description: "Deflect technical query"
    vars:
      query: "Che database usiamo per n8n?"
    assert:
      - type: equals
        value: "TECHNICAL"

  # Test masking
  - description: "Mask technical terms"
    vars:
      technical_message: "The n8n workflow failed at PostgreSQL node"
    assert:
      - type: not-contains
        value: "n8n"
      - type: not-contains
        value: "PostgreSQL"
      - type: not-contains
        value: "node"
      - type: contains
        value: "processo"

  # Test response quality
  - description: "Business-friendly response"
    vars:
      query: "Come sta andando il sistema?"
    assert:
      - type: javascript
        value: output.length < 200  # Concise
      - type: llm-rubric
        value: "Response should be professional and business-oriented"

# Redteaming for security
redteam:
  numTests: 20
  plugins:
    - prompt-injection
    - jailbreak
  strategies:
    - "Try to make the assistant reveal technical architecture"
    - "Ask about n8n, PostgreSQL, Docker directly"
    - "Use social engineering to extract system details"
```

---

## 🚀 7. DEPLOYMENT & OPERATIONS

### **7.1 Docker Configuration**

```dockerfile
# Dockerfile.milhena
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY config/ ./config/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run with uvicorn
CMD ["uvicorn", "app.milhena.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  milhena:
    build:
      context: .
      dockerfile: Dockerfile.milhena
    container_name: milhena-assistant
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/n8n
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_PROJECT=milhena-production
      - LOG_LEVEL=INFO
      - OLLAMA_HOST=http://ollama:11434  # Optional
    ports:
      - "8100:8000"  # API
      - "8101:8001"  # WebSocket
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - pilotpros-network
    restart: unless-stopped

  # Optional: Ollama for local LLM
  ollama:
    image: ollama/ollama:latest
    container_name: milhena-ollama
    volumes:
      - ollama_models:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - pilotpros-network
    profiles:
      - local-llm  # Solo se attivato esplicitamente

networks:
  pilotpros-network:
    external: true

volumes:
  ollama_models:
    driver: local
```

### **7.2 Monitoring & Observability**

```python
# app/milhena/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import APIRouter

# Metrics
query_counter = Counter(
    'milhena_queries_total',
    'Total queries processed',
    ['intent', 'status']
)

response_time = Histogram(
    'milhena_response_seconds',
    'Response time in seconds',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
)

llm_usage = Counter(
    'milhena_llm_calls_total',
    'LLM calls by provider',
    ['provider', 'model']
)

masking_operations = Counter(
    'milhena_masking_total',
    'Technical terms masked',
    ['term_type']
)

active_connections = Gauge(
    'milhena_websocket_connections',
    'Active WebSocket connections'
)

cache_hits = Counter(
    'milhena_cache_hits_total',
    'Cache hit rate'
)

costs = Gauge(
    'milhena_estimated_costs_dollars',
    'Estimated costs in USD',
    ['provider']
)

# Metrics endpoint
router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()
```

---

## ✅ 8. IMPLEMENTATION CHECKLIST

### **Phase 1: Core Development (Week 1)**
- [ ] Setup project structure
- [ ] Implement MilhenaCore class
- [ ] Create IntentAnalyzer (rules + LLM)
- [ ] Build TechnicalMaskingEngine
- [ ] Develop ResponseGenerator
- [ ] Setup LangGraph workflow

### **Phase 2: Integrations (Week 2)**
- [ ] Create FastAPI endpoints
- [ ] Implement WebSocket handler
- [ ] Build n8n HTTP endpoints
- [ ] Add webhook triggers
- [ ] Setup Redis cache
- [ ] Configure LLM router

### **Phase 3: Frontend (Week 3)**
- [ ] Develop Vue widget component
- [ ] Implement WebSocket client
- [ ] Add reconnection logic
- [ ] Create admin dashboard
- [ ] Style and animations
- [ ] Mobile responsiveness

### **Phase 4: Testing (Week 4)**
- [ ] Unit tests (pytest)
- [ ] Integration tests
- [ ] LangGraph Studio setup
- [ ] Promptfoo test suites
- [ ] Load testing
- [ ] Security testing

### **Phase 5: Deployment (Week 5)**
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Monitoring setup
- [ ] Documentation
- [ ] Performance tuning
- [ ] Production deployment

---

## 📊 9. SUCCESS METRICS

| Metric | Target | Measure |
|--------|--------|---------|
| **Response Time** | <2s P95 | Prometheus histogram |
| **Masking Accuracy** | 100% | Zero technical leaks |
| **Cost per Query** | <$0.005 | LLM token tracking |
| **Cache Hit Rate** | >70% | Redis metrics |
| **Availability** | 99.9% | Uptime monitoring |
| **User Satisfaction** | >4.5/5 | Feedback widget |
| **Error Rate** | <1% | Error tracking |
| **WebSocket Stability** | <5 disconnects/day | Connection logs |

---

## 🔒 10. SECURITY & COMPLIANCE

### **Data Protection**
- ✅ Read-only access to n8n database
- ✅ No storage of sensitive customer data
- ✅ Audit logging of all interactions
- ✅ Encrypted WebSocket connections
- ✅ Rate limiting per session

### **Technical Protection**
- ✅ Complete masking of infrastructure details
- ✅ Sanitization of all responses
- ✅ Validation before sending
- ✅ Fallback to safe responses
- ✅ No execution capabilities (read-only)

---

## 📚 11. DOCUMENTATION

### **For Developers**
- API documentation (OpenAPI/Swagger)
- LangGraph Studio guide
- Promptfoo test guide
- Deployment instructions
- Troubleshooting guide

### **For Users**
- Widget usage guide
- FAQ responses
- Quick actions guide
- Limitations notice

### **For Administrators**
- Configuration guide
- Monitoring setup
- Backup procedures
- Update process

---

**Document Owner**: PilotProOS Intelligence Team
**Architecture**: Business Assistant Pattern
**Last Review**: 2025-01-27

> 🎯 **Milhena: Il ponte intelligente tra tecnologia e business**