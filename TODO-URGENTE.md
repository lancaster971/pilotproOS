# 🚨 TODO URGENTE - PilotProOS Development Roadmap

> **⚠️ LETTURA OBBLIGATORIA** - Questo documento definisce le priorità di sviluppo e i fix critici per PilotProOS.
> **Last Updated**: 2025-10-10
> **Status**: 🔴 FIX CRITICI IN ATTESA

---

## 🚨 **FIX CRITICI** (Blockers Production - 3-4 ore totali)

### 1. ⚠️ **AsyncRedisSaver - Memoria Persistente** 🔴 CRITICA

**Problema Attuale**:
```python
# intelligence-engine/app/milhena/graph.py:621
checkpointer = None
logger.info("⚠️  NO checkpointer (temporary - using stateless execution)")
```

**Sintomi**:
- ❌ Follow-up queries falliscono: "spiegami meglio" → "meglio cosa?"
- ❌ Context perso dopo restart container
- ❌ Impossibile fare deep-dive multi-step
- ❌ Conversazioni NON persistono tra restart

**Soluzione**:
```python
from langgraph.checkpoint.redis import AsyncRedisSaver

async def _init_checkpointer():
    """Initialize AsyncRedisSaver properly"""
    redis_url = os.getenv("REDIS_URL", "redis://pilotpros-redis-dev:6379/0")

    checkpointer = AsyncRedisSaver.from_conn_string(redis_url)

    # CRITICAL: Await async init
    await checkpointer.__aenter__()

    return checkpointer

# In __init__
self.checkpointer = asyncio.run(self._init_checkpointer())

# Compile graph
self.compiled_graph = graph.compile(
    checkpointer=self.checkpointer,
    debug=False
)
```

**File Coinvolti**:
- `intelligence-engine/app/milhena/graph.py` (modifica linea 621)
- `intelligence-engine/app/main.py` (async init)

**Benefici**:
- ✅ Conversazioni persistenti tra restart
- ✅ Follow-up queries funzionanti
- ✅ Multi-step reasoning possibile
- ✅ Redis Stack già presente (no setup aggiuntivo)

**Stima**: 2-3 ore
**Priorità**: 🔴 MASSIMA

---

### 2. ⚠️ **Test Persistence & Follow-up** 🔴 CRITICA

**Dipende da**: AsyncRedisSaver implementato

**Test da Eseguire**:

```bash
# Test 1: Follow-up query
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quali workflow abbiamo?", "session_id": "test-persistence-1"}'

curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "spiegami meglio il primo", "session_id": "test-persistence-1"}'

# Expected: Risponde con dettagli del primo workflow (context mantenuto)

# Test 2: Restart persistence
# Avvia conversazione
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "ricorda questo codice: ABC123", "session_id": "test-restart"}'

# Restart container
docker restart pilotpros-intelligence-engine-dev

# Continua conversazione
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "che codice ti ho dato?", "session_id": "test-restart"}'

# Expected: Risponde "ABC123" (memoria persistita su Redis)

# Test 3: 10+ turn conversation
# Loop 10 messaggi con stesso session_id
# Expected: No degradation, context completo
```

**Success Criteria**:
- ✅ Follow-up queries mantengono context
- ✅ Restart container NON perde conversazioni
- ✅ 10+ turn conversation senza degradation
- ✅ Redis contiene 500+ checkpoint keys

**Stima**: 1 ora
**Priorità**: 🔴 MASSIMA

---

## 🚀 **SVILUPPO PRIORITARIO** (High ROI - 7-10 ore totali)

### 3. 🎯 **Auto-Learning Fast-Path** 🟠 ALTA

**Obiettivo**: Sistema che apprende automaticamente pattern da classificazioni LLM ad alta confidence, riducendo costi e latenza.

**Come Funziona**:
```
Query → Fast-path (NO match) → LLM Classifier
                                    ↓
                          Confidence > 0.9?
                                    ↓ YES
                    Salva pattern in PostgreSQL
                                    ↓
            Prossima query simile → Fast-path match (0ms!)
```

**Database Schema**:
```sql
CREATE TABLE auto_learned_patterns (
    id SERIAL PRIMARY KEY,
    pattern VARCHAR(200) UNIQUE NOT NULL,
    normalized_pattern VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    times_used INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    accuracy FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    created_by VARCHAR(20) DEFAULT 'llm',
    enabled BOOLEAN DEFAULT true,
    INDEX idx_normalized (normalized_pattern),
    INDEX idx_accuracy (accuracy DESC)
);
```

**Pattern Normalization**:
```python
def _normalize_query(self, query: str) -> str:
    """
    Normalizza query per pattern matching
    Esempi:
        "ci sono problemi oggi?" → "ci sono problemi"
        "ci sono problemi adesso?" → "ci sono problemi"
    """
    query = query.lower().strip()

    # Rimuovi parole temporali comuni
    temporal_words = ['oggi', 'adesso', 'ora', 'attualmente', 'ieri', 'domani']
    words = query.split()
    words = [w for w in words if w not in temporal_words]

    # Rimuovi punteggiatura finale
    normalized = ' '.join(words).rstrip('?!.')

    return normalized
```

**Learning Logic**:
```python
async def _maybe_learn_pattern(self, query: str, llm_result: Dict[str, Any]):
    """Apprende nuovo pattern se confidence alta"""

    # Solo pattern ad alta confidence
    if llm_result['confidence'] < 0.9:
        return

    # Normalizza query
    normalized = self._normalize_query(query)

    # Verifica se già esiste
    existing = await db.fetchrow(
        "SELECT * FROM auto_learned_patterns WHERE normalized_pattern = $1",
        normalized
    )

    if existing:
        # Incrementa usage counter
        await db.execute(
            "UPDATE auto_learned_patterns SET times_used = times_used + 1, last_used_at = NOW() WHERE id = $1",
            existing['id']
        )
    else:
        # Nuovo pattern
        await db.execute(
            """
            INSERT INTO auto_learned_patterns
            (pattern, normalized_pattern, category, confidence)
            VALUES ($1, $2, $3, $4)
            """,
            query, normalized, llm_result['category'], llm_result['confidence']
        )
        logger.info(f"[AUTO-LEARN] Nuovo pattern salvato: '{normalized}' → {llm_result['category']}")
```

**Fast-Path Integration**:
```python
def _instant_classify(self, query: str) -> Optional[Dict[str, Any]]:
    """Enhanced con pattern auto-appresi"""

    # 1. Pattern hardcoded (massima priorità)
    if "quanti" in query.lower():
        return {"category": "SIMPLE_METRIC", ...}

    # 2. Pattern auto-appresi (seconda priorità)
    normalized = self._normalize_query(query)
    if normalized in self.learned_patterns:
        pattern_info = self.learned_patterns[normalized]
        logger.info(f"[AUTO-LEARNED-MATCH] '{normalized}' → {pattern_info['category']}")
        return {
            "category": pattern_info['category'],
            "confidence": pattern_info['confidence'],
            "reasoning": "Auto-learned pattern match",
            "llm_used": "auto-learned-fast-path"
        }

    # 3. Nessun match → chiama LLM
    return None
```

**ROI Atteso**:
- **Riduzione costi**: -20-30% chiamate LLM dopo 1 mese
- **Velocità**: 0ms invece di 200-500ms per query frequenti
- **Auto-miglioramento**: Sistema migliora nel tempo senza intervento
- **Risparmio stimato**: $5-10/mese con 1000 query/giorno

**File Coinvolti**:
- `intelligence-engine/app/milhena/graph.py` (supervisor_orchestrator, _instant_classify)
- `backend/db/migrations/004_auto_learned_patterns.sql` (NEW)
- Nuove API: `GET/POST /api/admin/learned-patterns`

**Stima**: 4-6 ore
**Priorità**: 🟠 ALTA

---

### 4. 🔄 **Hot-Reload Pattern con Redis PubSub** 🟠 ALTA

**Dipende da**: Auto-Learning Fast-Path implementato

**Obiettivo**: Ricarica pattern auto-appresi senza restart container (real-time 0-100ms).

**Architettura**:
```python
# 1. Quando salvi nuovo pattern (in graph.py)
async def _save_new_pattern(self, pattern_data):
    # Salva in PostgreSQL
    await db.execute("INSERT INTO auto_learned_patterns ...")

    # Notifica altri processi via Redis
    await redis.publish('pattern_updates', json.dumps(pattern_data))

# 2. Background listener (sempre attivo)
async def _listen_pattern_updates(self):
    """Background task che ascolta Redis"""
    pubsub = redis.pubsub()
    await pubsub.subscribe('pattern_updates')

    async for message in pubsub.listen():
        if message['type'] == 'message':
            pattern = json.loads(message['data'])

            # Aggiorna cache in-memory IMMEDIATAMENTE
            self.learned_patterns[pattern['normalized']] = {
                'category': pattern['category'],
                'confidence': pattern['confidence']
            }

            logger.info(f"[REAL-TIME] Pattern aggiornato: {pattern['normalized']}")

# 3. Avvio listener in __init__
def __init__(self):
    # ...
    asyncio.create_task(self._listen_pattern_updates())
```

**Vantaggi**:
- ✅ **Aggiornamento istantaneo** (0-100ms)
- ✅ Scalabile (multi-container)
- ✅ Event-driven architecture
- ✅ Redis Stack già disponibile in PilotProOS

**Alternative Valutate**:
- ❌ Polling Database (overhead query ogni 5min)
- ❌ File Watcher (non funziona con DB-only)
- ✅ **Redis PubSub** (scelta ottimale per PilotProOS)

**Stima**: 3-4 ore
**Priorità**: 🟠 ALTA

---

## 🎨 **SVILUPPO UI** (Frontend - 7-9 ore totali)

### 5. 📊 **Learning Dashboard UI** 🟡 MEDIA

**Dipende da**: Auto-Learning implementato

**Componenti da Creare**:

```vue
<!-- frontend/src/pages/LearningDashboard.vue -->
<template>
  <div class="learning-dashboard">
    <h2>📊 Learning System - Metriche</h2>

    <!-- Accuracy Trend -->
    <Card title="Accuracy Over Time">
      <Chart type="line" :data="accuracyTrend" />
    </Card>

    <!-- Pattern Performance -->
    <Card title="Pattern Appresi">
      <DataTable :value="patterns" :paginator="true">
        <Column field="pattern" header="Pattern" />
        <Column field="category" header="Categoria" />
        <Column field="accuracy" header="Accuracy" />
        <Column field="usage" header="Utilizzi" />
        <Column header="Azioni">
          <template #body="{ data }">
            <Button @click="disablePattern(data.id)" v-if="data.accuracy < 0.7">
              Disabilita
            </Button>
          </template>
        </Column>
      </DataTable>
    </Card>

    <!-- Recent Feedback -->
    <Card title="Feedback Recente">
      <Timeline :value="recentFeedback" />
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useLearningStor } from '@/stores/learning-store'

const learningStore = useLearningStore()

const accuracyTrend = ref([])
const patterns = ref([])
const recentFeedback = ref([])

onMounted(async () => {
  await learningStore.fetchMetrics()
  accuracyTrend.value = learningStore.accuracyTrend
  patterns.value = learningStore.topPatterns
  recentFeedback.value = learningStore.recentFeedback
})
</script>
```

**Pinia Store**:
```typescript
// frontend/src/stores/learning-store.ts
import { defineStore } from 'pinia'
import { ofetch } from 'ofetch'

export const useLearningStore = defineStore('learning', {
  state: () => ({
    accuracyTrend: [],
    topPatterns: [],
    recentFeedback: [],
    isLoading: false
  }),

  actions: {
    async fetchMetrics() {
      this.isLoading = true
      try {
        const response = await ofetch('/api/milhena/performance')
        this.accuracyTrend = response.accuracy_trend
        this.topPatterns = response.top_patterns
        this.recentFeedback = response.recent_feedback
      } finally {
        this.isLoading = false
      }
    },

    async sendFeedback(messageId: string, type: 'positive' | 'negative') {
      await ofetch('/api/milhena/feedback', {
        method: 'POST',
        body: { message_id: messageId, feedback_type: type }
      })
    }
  }
})
```

**File da Creare**:
- `frontend/src/pages/LearningDashboard.vue` (NEW)
- `frontend/src/stores/learning-store.ts` (NEW)
- `frontend/src/router/index.ts` (add route)

**Stima**: 3-4 ore
**Priorità**: 🟡 MEDIA

---

### 6. 👍 **Feedback Buttons in ChatWidget** 🟡 MEDIA

**Backend**: ✅ Già pronto (`/api/milhena/feedback`)

**Modifiche a ChatWidget**:
```vue
<!-- frontend/src/components/ChatWidget.vue -->
<template>
  <div v-for="msg in messages" :key="msg.id" class="message-wrapper">
    <div :class="['message', msg.type]">
      <div class="message-content">{{ msg.text }}</div>

      <!-- Feedback buttons for Milhena messages -->
      <div v-if="msg.type === 'milhena' && !msg.feedback" class="feedback-buttons">
        <button
          @click="sendFeedback(msg.id, 'positive')"
          class="feedback-btn positive"
          title="Risposta utile"
        >
          👍
        </button>
        <button
          @click="sendFeedback(msg.id, 'negative')"
          class="feedback-btn negative"
          title="Risposta non utile"
        >
          👎
        </button>
      </div>

      <!-- Feedback confirmed -->
      <div v-if="msg.feedback" class="feedback-confirmed">
        <span v-if="msg.feedback === 'positive'" class="positive">
          ✅ Grazie per il feedback!
        </span>
        <span v-else class="negative">
          ❌ Grazie, sto imparando...
        </span>
      </div>

      <!-- Reformulation helper -->
      <div v-if="msg.feedback === 'negative' && !msg.reformulated" class="reformulation-helper">
        <p>Puoi riformulare la domanda per aiutarmi a capire meglio?</p>
        <div class="suggestions">
          <button
            v-for="suggestion in getReformulationSuggestions(msg)"
            :key="suggestion"
            @click="sendMessage(suggestion)"
            class="suggestion-btn"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useLearningStore } from '@/stores/learning-store'

const learningStore = useLearningStore()

async function sendFeedback(messageId: string, type: 'positive' | 'negative') {
  await learningStore.sendFeedback(messageId, type)

  // Update message
  const msg = messages.value.find(m => m.id === messageId)
  if (msg) {
    msg.feedback = type
  }
}

function getReformulationSuggestions(msg: any): string[] {
  if (msg.detectedIntent === 'ERRORS') {
    return [
      'Mostra solo gli errori di oggi',
      'Quali processi hanno avuto problemi?'
    ]
  } else if (msg.detectedIntent === 'METRICS') {
    return [
      'Quante fatture sono state elaborate oggi?',
      'Dammi le statistiche complete'
    ]
  }
  return ['Mostra lo stato generale del sistema']
}
</script>

<style scoped>
.feedback-buttons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.feedback-btn {
  padding: 4px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 16px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.feedback-btn:hover {
  transform: scale(1.1);
}

.feedback-btn.positive:hover {
  background: #e8f5e9;
  border-color: #4caf50;
}

.feedback-btn.negative:hover {
  background: #ffebee;
  border-color: #f44336;
}

.reformulation-helper {
  margin-top: 12px;
  padding: 12px;
  background: #fff3e0;
  border-radius: 8px;
}

.suggestion-btn {
  padding: 6px 12px;
  background: white;
  border: 1px solid #ff9800;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
}

.suggestion-btn:hover {
  background: #ff9800;
  color: white;
}
</style>
```

**File da Modificare**:
- `frontend/src/components/ChatWidget.vue` (add feedback UI)

**Stima**: 2 ore
**Priorità**: 🟡 MEDIA

---

### 7. 📈 **Pattern Visualization + Charts** 🟢 BASSA

**Dipende da**: Learning Dashboard creato

**Features**:
- Pattern performance heatmap (D3.js)
- Learned examples timeline
- Accuracy improvement curve (ultimi 30 giorni)
- Cache hit rate trend
- Cost savings visualization

**Stima**: 2-3 ore
**Priorità**: 🟢 BASSA

---

## 📦 **ORDINE ESECUZIONE RACCOMANDATO**

```
SPRINT 1 - FIX CRITICI (Week 1, Day 1-2)
┌─────────────────────────────────────────────┐
│ 1. AsyncRedisSaver                   2-3h   │
│ 2. Test Persistence                  1h     │
└─────────────────────────────────────────────┘
                    ↓
SPRINT 2 - BACKEND FEATURES (Week 1, Day 3-5)
┌─────────────────────────────────────────────┐
│ 3. Auto-Learning Fast-Path           4-6h   │
│ 4. Hot-Reload Pattern (Redis PubSub) 3-4h   │
└─────────────────────────────────────────────┘
                    ↓
SPRINT 3 - FRONTEND UI (Week 2)
┌─────────────────────────────────────────────┐
│ 5. Learning Dashboard UI              3-4h  │
│ 6. Feedback Buttons ChatWidget        2h    │
│ 7. Pattern Visualization              2-3h  │
└─────────────────────────────────────────────┘

TOTALE: 17-23 ore (3-4 giorni full-time)
```

---

## ⏱️ **TIMELINE DETTAGLIATA**

### **Week 1: Backend + Fix**

**Day 1-2** (FIX CRITICI - 3-4h):
- ✅ Implementare AsyncRedisSaver
- ✅ Modificare graph.py + main.py
- ✅ Test follow-up queries
- ✅ Test restart persistence
- ✅ Verify Redis checkpoint keys

**Day 3-4** (BACKEND - 4-6h):
- ✅ Database migration auto_learned_patterns
- ✅ Pattern normalization logic
- ✅ Learning trigger (confidence >0.9)
- ✅ Fast-path integration
- ✅ Test auto-learning con query reali

**Day 5** (BACKEND - 3-4h):
- ✅ Redis PubSub subscriber
- ✅ Pattern cache management
- ✅ Background listener task
- ✅ Test real-time updates

### **Week 2: Frontend**

**Day 1-2** (UI - 3-4h):
- ✅ Create LearningDashboard.vue
- ✅ Create learning-store.ts
- ✅ Accuracy trend chart
- ✅ Top patterns table
- ✅ Recent feedback timeline

**Day 3** (UI - 2h):
- ✅ Add feedback buttons to ChatWidget
- ✅ Reformulation helper UI
- ✅ Feedback confirmation messages

**Day 4-5** (UI + Testing - 2-3h):
- ✅ Pattern visualization
- ✅ Cost savings dashboard
- ✅ End-to-end testing
- ✅ Documentation update

---

## 🎯 **SUCCESS CRITERIA**

### **Fix Critici**:
- [x] Checkpointer != None
- [x] Follow-up queries funzionanti
- [x] Restart NON perde conversazioni
- [x] Redis checkpoint keys > 100

### **Auto-Learning**:
- [x] Pattern salvati in PostgreSQL
- [x] Fast-path usa pattern auto-appresi
- [x] Accuracy >= 70% pattern appresi
- [x] Latency <10ms fast-path matches

### **Hot-Reload**:
- [x] Pattern updates <100ms
- [x] Redis PubSub funzionante
- [x] Background task attivo

### **Frontend**:
- [x] Dashboard mostra metriche real-time
- [x] Feedback buttons visibili
- [x] Charts responsive + dark theme

---

## 📊 **METRICHE ATTESE**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Follow-up Success** | 0% | 95%+ | +95% |
| **Context Persistence** | 0 turns | 10+ turns | ∞ |
| **Fast-path Coverage** | 30% | 50%+ | +66% |
| **Latency (cached)** | 500ms | <10ms | -98% |
| **LLM Cost Reduction** | $2.10/mo | $1.50/mo | -30% |
| **User Satisfaction** | 3.5/5 | 4.2/5 | +20% |

---

## 🔗 **FILE DI RIFERIMENTO**

**Documentation**:
- `NICE-TO-HAVE-FEATURES.md` - Feature dettagliate (578 righe)
- `TODO-MILHENA-LEARNING-SYSTEM.md` - Learning system completo (1699 righe)
- `CLAUDE.md` - Main project guide (linea 13-24 status features)

**Backend**:
- `intelligence-engine/app/milhena/graph.py:621` - ⚠️ checkpointer = None (FIX!)
- `intelligence-engine/app/milhena/learning.py` - Learning system base
- `intelligence-engine/app/main.py` - Async init

**Frontend**:
- `frontend/src/components/ChatWidget.vue` - Chat widget (add feedback)
- `frontend/src/pages/LearningDashboard.vue` - NEW (da creare)
- `frontend/src/stores/learning-store.ts` - NEW (da creare)

---

## 🚀 **NEXT ACTIONS**

1. **READ**: Questo documento completamente
2. **START**: AsyncRedisSaver implementation (FIX CRITICO)
3. **TEST**: Persistence after implementation
4. **CONTINUE**: Follow roadmap in order

---

**Document Owner**: PilotProOS Development Team
**Created**: 2025-10-10
**Priority**: 🔴 CRITICAL (Fix) + 🟠 HIGH (Development)
**Status**: 📋 READY TO START

---

**⚠️ IMPORTANTE**: Questo documento DEVE essere letto PRIMA di iniziare qualsiasi sviluppo su PilotProOS.
