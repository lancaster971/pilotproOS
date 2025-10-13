# 🔧 DEBITO TECNICO - PilotProOS

> **Nota**: Implementazioni da completare **DOPO** lo sviluppo core di Milhena

**Last Updated**: 2025-10-11
**Security Audit**: Completato (fullstack-debugger)
**Security Score**: 4.5/10 🔴

---

## 🚨 SECURITY DEBT - CRITICAL

**Priorità**: 🔴 **BLOCKERS PRODUCTION**
**Effort**: 11-15 ore (2 developer-days)
**Owner**: Security Team + Backend Lead
**Status**: ⚠️ **URGENT - Da implementare PRIMA del go-live**

### **⚠️ Production Blockers Identificati**

Il sistema di autenticazione presenta **vulnerabilità critiche** che lo rendono **NON production-ready**. L'audit completo ha identificato 10 issues di cui 3 sono **blockers assoluti**.

**Security Score Breakdown**:
- Authentication: 6/10 (✅ JWT valid, ❌ localStorage vulnerable)
- Session Management: 3/10 (❌ No refresh, ❌ No revocation)
- Rate Limiting: 2/10 (❌ Essentially disabled)
- Input Validation: 5/10 (⚠️ Weak passwords OK)
- CORS/CSP: 5/10 (⚠️ Permissive origins)

---

### **🔴 CRITICAL ISSUES (P0) - 11h**

#### **1. XSS Vulnerability via localStorage** (CVSS 8.1)
**Status**: ❌ **BLOCKER**
**Effort**: 4 ore
**Impact**: Token theft via XSS attacks

**Problema**:
```typescript
// frontend/src/stores/auth.ts:60-61 - VULNERABLE
localStorage.setItem('token', data.token)  // ❌ Accessible by any JS
localStorage.setItem('user', JSON.stringify(user.value))
```

**Soluzione**:
- [ ] Migrate JWT to **HttpOnly cookies**
- [ ] Remove localStorage token storage
- [ ] Update auth.ts to use cookie-based authentication
- [ ] Add SameSite=strict + Secure flags

**File da modificare**:
- `backend/src/controllers/auth.controller.js` (add res.cookie)
- `frontend/src/stores/auth.ts` (remove localStorage)
- `backend/src/middleware/auth.middleware.js` (read from cookies)

**Reference**: [OWASP JWT Cheat Sheet](https://cheatsheetsecurity.com/html/cheatsheet/JWT_Security.html)

---

#### **2. No Refresh Token Strategy** (CVSS 6.5)
**Status**: ❌ **BLOCKER**
**Effort**: 6 ore
**Impact**: Impossibile revocare sessioni, UX negativa

**Problema**:
```javascript
// backend/src/controllers/auth.controller.js:59 - NO REFRESH
const token = jwt.sign({ ... }, secret, { expiresIn: '7d' })  // ❌ Too long
```

**Soluzione**:
- [ ] Implement **access token** (30min) + **refresh token** (7 days)
- [ ] Create database table `pilotpros.refresh_tokens`
- [ ] Add `/api/auth/refresh` endpoint
- [ ] Store refresh tokens in PostgreSQL for revocation
- [ ] Update frontend to auto-refresh access token

**Migration SQL**:
```sql
-- File: backend/db/migrations/005_refresh_tokens.sql
CREATE TABLE pilotpros.refresh_tokens (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES pilotpros.users(id) ON DELETE CASCADE,
  token TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  revoked_at TIMESTAMP DEFAULT NULL
);
CREATE INDEX idx_token ON pilotpros.refresh_tokens(token);
CREATE INDEX idx_user_active ON pilotpros.refresh_tokens(user_id, revoked_at) WHERE revoked_at IS NULL;
```

**Reference**: [RFC 6749 OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749#section-1.5)

---

#### **3. Hardcoded Secret Fallback** (CVSS 7.2)
**Status**: ❌ **BLOCKER**
**Effort**: 1 ora
**Impact**: JWT forgery se misconfigured

**Problema**:
```javascript
// backend/src/controllers/auth.controller.js:58 - DANGER
process.env.JWT_SECRET || 'dev-secret-change-in-production'  // ❌
```

**Soluzione**:
- [ ] Enforce JWT_SECRET validation in production
- [ ] Fail-fast if JWT_SECRET missing or < 32 chars
- [ ] Add startup check in `backend/src/config/index.js`

**Code Fix**:
```javascript
// backend/src/config/index.js
if (process.env.NODE_ENV === 'production') {
  if (!process.env.JWT_SECRET || process.env.JWT_SECRET.length < 32) {
    throw new Error('JWT_SECRET must be set (32+ chars) in production')
  }
}
```

---

### **🟠 HIGH PRIORITY (P1) - 4h**

#### **4. Rate Limiting Disabled** (CVSS 4.1)
**Status**: ⚠️ **HIGH**
**Effort**: 1 ora
**Impact**: Brute-force attacks on /login

**Problema**:
```javascript
// backend/src/server.js:150-156 - RELAXED
max: 10000  // ❌ 10k requests/min = essentially disabled
```

**Soluzione**:
- [ ] Add **strict rate limiter** on `/api/auth/login` (5 attempts / 15min)
- [ ] Keep relaxed global limiter for other routes
- [ ] Add account lockout after 10 failed attempts (24h)

**Code Fix**:
```javascript
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 5,                     // 5 attempts max
  message: 'Too many login attempts, retry in 15min',
  standardHeaders: true,
  legacyHeaders: false
})
router.post('/login', loginLimiter, async (req, res) => { ... })
```

---

#### **5. CORS Overly Permissive** (CVSS 5.3)
**Status**: ⚠️ **HIGH**
**Effort**: 1 ora
**Impact**: Potential origin bypass in production

**Problema**:
```javascript
// backend/src/server.js:125-132 - PERMISSIVE
const corsOrigins = [
  'http://localhost:3000',
  'http://localhost:5173',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:5173'  // ❌ Troppi origins per production
]
```

**Soluzione**:
- [ ] Use **single production origin** from env var
- [ ] Keep multiple origins solo in development
- [ ] Add origin validation middleware

**Code Fix**:
```javascript
const corsOrigins = process.env.NODE_ENV === 'production'
  ? [process.env.FRONTEND_URL]  // ✅ SOLO frontend production
  : ['http://localhost:3000', 'http://localhost:5173', ...]
```

---

#### **6. Token Expiry Not Verified** (CVSS 5.8)
**Status**: ⚠️ **HIGH**
**Effort**: 2 ore
**Impact**: User può rimanere authenticated con token expired

**Problema**:
```typescript
// frontend/src/stores/auth.ts:106-114 - NO VERIFICATION
const initializeAuth = async () => {
  if (token.value) {
    return true  // ❌ NO server-side check!
  }
}
```

**Soluzione**:
- [ ] Call `/api/auth/verify` at app initialization
- [ ] Logout se token expired/invalid
- [ ] Show session expiry warning 5min before timeout

**Code Fix**:
```typescript
const initializeAuth = async () => {
  if (token.value) {
    const response = await fetch(`${API_BASE}/api/auth/verify`, {
      headers: { 'Authorization': `Bearer ${token.value}` }
    })
    if (!response.ok) {
      await logout()  // ✅ Clear expired token
      return false
    }
  }
}
```

---

### **🟡 MEDIUM PRIORITY (P2) - 7h**

#### **7. Weak Password Accepted** (CVSS 3.2)
**Effort**: 2 ore

**Soluzione**:
- [ ] Add password strength validation (min 8 chars, uppercase, lowercase, number, special char)
- [ ] Use zxcvbn library for password strength scoring
- [ ] Show strength indicator in frontend

---

#### **8. Logout Incomplete** (CVSS 2.1)
**Effort**: 3 ore

**Soluzione**:
- [ ] Implement Redis blacklist for revoked tokens
- [ ] Add middleware to check blacklist on protected routes
- [ ] TTL = remaining token expiry time

---

#### **9. User Data in JWT Payload** (CVSS 2.8)
**Effort**: 1 ora

**Soluzione**:
- [ ] Remove email from JWT payload (keep only userId + role)
- [ ] Fetch user details from DB when needed
- [ ] Reduce JWT size

---

#### **10. Window.fetch Monkey-Patching** (Code Smell)
**Effort**: 1 ora

**Soluzione**:
- [ ] Replace with Axios interceptors
- [ ] Remove global fetch override
- [ ] Use proper HTTP client pattern

---

### **📋 Implementation Checklist**

**Phase 1: Production Blockers (URGENT - 11h)**
- [ ] HttpOnly cookies migration (4h)
- [ ] Refresh token implementation (6h)
- [ ] JWT_SECRET enforcement (1h)

**Phase 2: Security Hardening (4h)**
- [ ] Strict rate limiting on /login (1h)
- [ ] Production CORS lockdown (1h)
- [ ] Token expiry verification (2h)

**Phase 3: Code Quality (7h)**
- [ ] Password strength validation (2h)
- [ ] Server-side logout with Redis (3h)
- [ ] JWT payload optimization (1h)
- [ ] Remove fetch override (1h)

**Total Effort**: **22 ore** (3 developer-days)

---

### **🧪 Testing Requirements**

**Security Tests**:
```bash
# XSS Protection Test
curl http://localhost:3001/api/auth/login -c cookies.txt
# ✅ Token must be in httpOnly cookie, NOT in JSON body

# Rate Limit Test (6 attempts)
for i in {1..6}; do curl -X POST http://localhost:3001/api/auth/login \
  -d '{"email":"wrong","password":"wrong"}'; done
# ✅ 6th request must return 429 Too Many Requests

# Token Expiry Test (after 31 minutes)
curl http://localhost:3001/api/protected -b cookies.txt
# ✅ Must return 401 Unauthorized

# Refresh Token Test
curl -X POST http://localhost:3001/api/auth/refresh -b cookies.txt
# ✅ Must return new access_token cookie
```

**Frontend Tests**:
```javascript
// DevTools Console Verification
localStorage.getItem('token')  // ✅ Must return NULL
document.cookie               // ❌ access_token NOT visible (httpOnly)
```

---

### **✅ Go-Live Criteria**

**Production Deployment Blocked Until**:
- ✅ HttpOnly cookies implemented (Fix #1)
- ✅ Refresh token strategy working (Fix #2)
- ✅ JWT_SECRET enforced in production (Fix #3)
- ✅ Rate limit 5/15min on /login (Fix #4)
- ✅ Production CORS single origin (Fix #5)
- ✅ Security test suite 100% passing

**Current Status**: ⚠️ **DEVELOPMENT-READY ONLY**
**Estimated Fix Date**: +2 developer-days da start
**Owner**: Backend Lead + Security Review

---

### **📚 References**

**OWASP Guidelines**:
- [JWT Security Cheat Sheet](https://cheatsheetsecurity.com/html/cheatsheet/JWT_Security.html)
- [OWASP Top 10 2021 - A07 (Auth Failures)](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/)
- [Session Management Cheat Sheet](https://cheatsheetsecurity.com/html/cheatsheet/Session_Management_Cheat_Sheet.html)

**RFCs & Standards**:
- [RFC 8725 - JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [RFC 6749 - OAuth 2.0 (Refresh Tokens)](https://datatracker.ietf.org/doc/html/rfc6749#section-1.5)
- [NIST SP 800-63B - Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)

**Library Documentation**:
- [express-rate-limit GitHub](https://github.com/express-rate-limit/express-rate-limit)
- [bcrypt.js Security Considerations](https://github.com/dcodeIO/bcrypt.js#security-considerations)
- [Helmet.js Documentation](https://helmetjs.github.io/)

---

## 🧠 LEARNING SYSTEM - ARCHITECTURE FLAW

**Priorità**: 🔴 **CRITICA**
**Effort**: 2-3 giorni (16-24h)
**Owner**: AI/ML Lead + Backend Team
**Status**: ❌ **MAL PROGETTATO - Refactoring necessario**
**Version**: v3.4.0 (Pattern Supervision System)

### **❌ Problema Attuale**

Sistema **CUSTOM** (zero standard RLHF) che salva **DOMANDE** basandosi su LLM confidence >0.9.

**Critical Flaw**:
```python
# intelligence-engine/app/milhena/graph.py:1969-2020
async def _maybe_learn_pattern(self, query: str, llm_result: Dict[str, Any]):
    """Apprende pattern se confidence >0.9"""
    if llm_result['confidence'] < 0.9:
        return

    # ❌ Salva SOLO query + category, NIENTE risposta/feedback
    await db.execute(
        "INSERT INTO auto_learned_patterns (pattern, category, confidence) ..."
    )
```

**Cosa vede Admin nella UI**:
- ✅ Query: "ci sono errori oggi?"
- ✅ Category: "ERRORS"
- ✅ Confidence: 0.95
- ❌ **Risposta Milhena**: INVISIBILE
- ❌ **Tool usato**: INVISIBILE
- ❌ **Feedback utente (👍👎)**: IGNORATO

**Conseguenza**: Admin approva pattern "al buio" senza sapere se risposta era corretta.

---

### **✅ Architettura Corretta (RLHF Standard)**

**Flusso feedback-based**:
```
1. User: "ci sono errori oggi?"
   ↓
2. Milhena: "Sì, 3 errori: workflow X, Y, Z"
   Tool: get_error_details_tool
   ↓
3. User clicca: 👍 (risposta corretta) o 👎 (sbagliata)
   ↓
4. Sistema salva:
   - Query: "ci sono errori oggi?"
   - Response: "Sì, 3 errori..."
   - Tool: get_error_details_tool
   - Feedback: thumbs_up
   ↓
5. Admin UI mostra:
   - Query + Risposta + Tool
   - Feedback: 👍 (3 volte) 👎 (0 volte)
   - Accuracy: 100%
   ↓
6. Admin approva → Fast-path usa QUEL tool per query simili
```

**Accuratezza reale**: `accuracy = thumbs_up / (thumbs_up + thumbs_down)`

---

### **🔧 Refactoring Necessario**

#### **1. Database Schema Update**

```sql
-- File: backend/db/migrations/006_feedback_learning.sql

-- Add response + tool to patterns table
ALTER TABLE pilotpros.auto_learned_patterns
ADD COLUMN response TEXT,
ADD COLUMN tool_used VARCHAR(100),
ADD COLUMN thumbs_up INT DEFAULT 0,
ADD COLUMN thumbs_down INT DEFAULT 0;

-- Link feedback to patterns (FK)
ALTER TABLE pilotpros.user_feedback
ADD COLUMN pattern_id INT REFERENCES pilotpros.auto_learned_patterns(id) ON DELETE SET NULL;

-- Index for feedback aggregation
CREATE INDEX idx_pattern_feedback ON pilotpros.user_feedback(pattern_id);
```

#### **2. Learning Trigger Update**

```python
# intelligence-engine/app/milhena/api.py

async def feedback_endpoint(request):
    """Feedback 👍👎 triggers pattern learning"""

    # 1. Save feedback to DB (existing)
    await save_feedback(message_id, feedback_type)

    # 2. If thumbs_up → Check if pattern learnable
    if feedback_type == "positive":
        message = await get_message_details(message_id)

        # Get aggregated feedback for this query
        feedback_stats = await db.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE feedback_type = 'positive') as thumbs_up,
                COUNT(*) FILTER (WHERE feedback_type = 'negative') as thumbs_down
            FROM user_feedback
            WHERE query_normalized = $1
        """, normalize_query(message.query))

        # Learn pattern if 3+ positive, accuracy >70%
        if feedback_stats['thumbs_up'] >= 3:
            accuracy = feedback_stats['thumbs_up'] / (feedback_stats['thumbs_up'] + feedback_stats['thumbs_down'])

            if accuracy >= 0.7:
                await learn_pattern(
                    query=message.query,
                    response=message.response,
                    tool_used=message.tool_used,
                    thumbs_up=feedback_stats['thumbs_up'],
                    thumbs_down=feedback_stats['thumbs_down'],
                    accuracy=accuracy
                )
```

#### **3. Admin UI Update**

```vue
<!-- frontend/src/components/learning/PatternManagement.vue -->

<DataTable :value="patterns" :expandable="true">
  <Column field="pattern" header="Query" />
  <Column field="category" header="Category" />

  <!-- NEW: Feedback count -->
  <Column header="Feedback">
    <template #body="{ data }">
      👍 {{ data.thumbs_up }} | 👎 {{ data.thumbs_down }}
    </template>
  </Column>

  <Column field="accuracy" header="Accuracy">
    <template #body="{ data }">
      {{ (data.accuracy * 100).toFixed(1) }}%
    </template>
  </Column>

  <!-- Row expansion: mostra risposta + tool -->
  <template #expansion="{ data }">
    <div class="pattern-details">
      <p><strong>Query:</strong> {{ data.pattern }}</p>
      <p><strong>Response:</strong> {{ data.response }}</p>
      <p><strong>Tool Used:</strong> {{ data.tool_used }}</p>
      <p><strong>Feedback:</strong>
        👍 {{ data.thumbs_up }} | 👎 {{ data.thumbs_down }}
        ({{ (data.accuracy * 100).toFixed(1) }}%)
      </p>
    </div>
  </template>
</DataTable>
```

---

### **📚 Librerie Standard (DA VALUTARE)**

**Option A: LangSmith Feedback** (Ufficiale LangChain)
- ✅ Pro: Integrato con LangGraph
- ✅ Pro: Dashboard built-in
- ❌ Con: Servizio cloud (costi)

**Option B: LangFuse** (Open Source)
- ✅ Pro: Self-hosted
- ✅ Pro: Observability completa
- ❌ Con: Setup più complesso

**Option C: Argilla** (Annotation Tool)
- ✅ Pro: UI annotation professionale
- ✅ Pro: RLHF workflows
- ❌ Con: Overkill per caso d'uso

**Option D: Custom Refactoring** (Raccomandato)
- ✅ Pro: Feedback buttons già esistono
- ✅ Pro: Zero dipendenze esterne
- ✅ Pro: Full controllo
- ⚠️ Con: Manutenzione custom

---

### **📊 Impact Business**

| Aspetto | Attuale (v3.4.0) | Corretto (v3.5.0+) |
|---------|------------------|---------------------|
| **Visibilità Admin** | Solo query | Query + Risposta + Tool |
| **Fonte Learning** | LLM confidence | User feedback (👍👎) |
| **Accuratezza** | Fittizia (confidence) | Reale (thumbs_up ratio) |
| **Rischio Errori** | ALTO (blind approval) | BASSO (informed decision) |
| **Standard** | Custom (zero RLHF) | RLHF-compliant |

**ROI**: Sistema impara DAVVERO da feedback utente invece di "fidarsi" dell'LLM.

---

### **🔄 Migration Path**

**Phase 1: Database Update (2h)**
- [ ] Migration 006: Add response, tool, feedback columns
- [ ] Backfill existing patterns (NULL response = skip approval)

**Phase 2: Backend Logic (8h)**
- [ ] Update feedback endpoint → trigger learning
- [ ] Implement feedback aggregation query
- [ ] Add pattern learning threshold (3+ thumbs_up, 70% accuracy)
- [ ] Update admin endpoints (include response + tool)

**Phase 3: Frontend UI (6h)**
- [ ] Update PatternManagement.vue (show response + tool)
- [ ] Add feedback count badges
- [ ] Row expansion with full details
- [ ] Filter by accuracy threshold

**Phase 4: Testing (8h)**
- [ ] End-to-end feedback → learning → approval flow
- [ ] Verify accuracy calculation
- [ ] Load testing (1000+ feedback entries)
- [ ] Documentation update

**Total**: 24 ore (3 developer-days)

---

### **📚 References**

**RLHF Theory**:
- [Reinforcement Learning from Human Feedback (RLHF)](https://huggingface.co/blog/rlhf)
- [InstructGPT Paper (OpenAI)](https://arxiv.org/abs/2203.02155)
- [Fine-Tuning Language Models from Human Preferences](https://arxiv.org/abs/1909.08593)

**LangChain Ecosystem**:
- [LangSmith Feedback](https://docs.smith.langchain.com/evaluation/capturing-feedback)
- [LangFuse Documentation](https://langfuse.com/docs)
- [LangGraph Human-in-the-Loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)

**Annotation Tools**:
- [Argilla for RLHF](https://docs.argilla.io/)
- [Label Studio](https://labelstud.io/)
- [Prodigy Annotation](https://prodi.gy/)

---

### **✅ Success Criteria**

- [ ] Admin vede query + risposta + tool COMPLETI prima di approvare
- [ ] Pattern appresi SOLO con feedback positivo (3+ thumbs_up, 70%+ accuracy)
- [ ] Accuracy reale = thumbs_up / (thumbs_up + thumbs_down)
- [ ] Fast-path usa tool specifico (non solo categoria)
- [ ] UI mostra feedback count + accuracy % per ogni pattern
- [ ] End-to-end test: User 👍 → Pattern learned → Admin approved → Fast-path active

---

**Created**: 2025-10-13
**Priority**: 🔴 **CRITICA**
**Status**: ⏳ Da implementare (v3.5.0)
**Owner**: AI/ML Lead + Backend Team

---

## 📋 TEMPLATE-IZZAZIONE MILHENA

**Priorità**: 🔴 ALTA (Post-Development)
**Effort**: 2-3 settimane
**Owner**: Team Development
**Status**: ⏳ PIANIFICATO

### **Obiettivo**
Trasformare Milhena in un **TEMPLATE RIUTILIZZABILE** per altri progetti/clienti.

### **Cosa Fare**

#### **1. Configuration-Driven Architecture**
- [ ] Creare `chatbot.yaml` - Main configuration file
- [ ] Creare `tools.yaml` - Tools definition (domain-specific)
- [ ] Creare `prompts.yaml` - System prompts customization
- [ ] Creare `masking_rules.yaml` - Domain masking rules

#### **2. Separazione Core vs Domain-Specific**

**Core Reusable (80%)**:
- [ ] `core/graph.py` - LangGraph workflow generico
- [ ] `core/llm_strategy.py` - Groq FREE + OpenAI hybrid
- [ ] `core/masking_engine.py` - Multi-level masking
- [ ] `core/rag_system.py` - RAG con ChromaDB
- [ ] `core/learning_system.py` - Continuous learning
- [ ] `core/cache_manager.py` - Smart caching
- [ ] `core/token_manager.py` - Token tracking

**Domain-Specific (20%)**:
- [ ] `domain/tools/` - Custom tools per use case
- [ ] `domain/schemas/` - Data models specifici
- [ ] `domain/prompts/` - Domain prompts

#### **3. Template Generator Script**
```bash
python scripts/generate_project.py
```

**Features**:
- [ ] Interactive setup (questionary)
- [ ] Use case selection (business_process, ecommerce, healthcare, finance, custom)
- [ ] Auto-generate config files
- [ ] Copy core components
- [ ] Generate Docker setup
- [ ] Generate .env.example
- [ ] Generate README.md

#### **4. Use Case Examples**

**Example Projects**:
- [ ] `examples/pilotpros/` - Business Process Assistant (current)
- [ ] `examples/ecommerce/` - E-commerce Support Bot
- [ ] `examples/healthcare/` - Medical Assistant
- [ ] `examples/finance/` - Financial Advisor

Ogni example contiene:
- `config/chatbot.yaml` - Configurazione specifica
- `domain/tools/` - Custom tools
- `README.md` - Deployment guide

#### **5. Deployment Automation**
- [ ] One-click deploy script
- [ ] Docker Compose template
- [ ] Environment configuration
- [ ] Database migration scripts
- [ ] Frontend build automation

#### **6. Documentation**
- [ ] `TEMPLATE-GUIDE.md` - Come usare il template
- [ ] `CUSTOMIZATION.md` - Guida personalizzazione
- [ ] `DEPLOYMENT.md` - Deployment workflow
- [ ] Video tutorial setup
- [ ] API documentation

---

## 📊 Structure Template Finale

```
milhena-template/
├── core/                          # ✅ 100% RIUTILIZZABILE
│   ├── graph.py
│   ├── llm_strategy.py
│   ├── masking_engine.py
│   ├── rag_system.py
│   ├── learning_system.py
│   ├── cache_manager.py
│   └── token_manager.py
│
├── config/                        # 🔧 CUSTOMIZABLE
│   ├── chatbot.yaml               # Main config
│   ├── tools.yaml                 # Tools definition
│   ├── prompts.yaml               # System prompts
│   └── masking_rules.yaml         # Masking rules
│
├── domain/                        # 🎯 DOMAIN-SPECIFIC
│   ├── tools/
│   │   ├── database_tools.py
│   │   └── api_tools.py
│   ├── schemas/
│   └── prompts/
│
├── frontend/                      # ✅ RIUTILIZZABILE
│   ├── ChatWidget.vue
│   ├── RAGManager.vue
│   └── LearningDashboard.vue
│
├── scripts/                       # 🚀 AUTOMATION
│   ├── generate_project.py        # Template generator
│   ├── deploy.sh                  # One-click deploy
│   └── configure.py               # Interactive setup
│
└── examples/                      # 📚 USE CASES
    ├── pilotpros/
    ├── ecommerce/
    ├── healthcare/
    └── finance/
```

---

## 🎯 Benefits del Template

### **Per il Business**
- ✅ **Riutilizzo 80% del codice** per nuovi progetti
- ✅ **Time-to-Market ridotto** da 3 mesi a 2 settimane
- ✅ **Costi sviluppo -70%** per nuovi chatbot
- ✅ **Quality assurance** garantita (core testato)

### **Per gli Sviluppatori**
- ✅ **Setup in 5 minuti** con generator script
- ✅ **Configuration-driven** (zero coding per setup base)
- ✅ **Best practices** integrate
- ✅ **Documentation completa**

### **Per i Clienti**
- ✅ **Chatbot personalizzato** in giorni non mesi
- ✅ **Features enterprise** out-of-the-box (RAG, Learning, Masking)
- ✅ **Scalabile** e maintainable
- ✅ **Deploy automatico**

---

## 📅 Timeline Implementazione

**Quando**: Dopo completamento sviluppo core Milhena v3.1

**Durata Stimata**: 2-3 settimane

**Fasi**:
1. **Week 1**: Refactoring core → configuration-driven
2. **Week 2**: Template generator + use case examples
3. **Week 3**: Documentation + testing deployment

---

## ✅ Success Criteria

- [ ] Generator script funzionante
- [ ] 3+ use case examples documentati
- [ ] Deploy automatico testato
- [ ] Documentation completa
- [ ] Video tutorial creato
- [ ] Template pubblicato (GitHub/Internal)

---

**Created**: 2025-10-04
**Priority**: 🔴 ALTA
**Status**: ⏳ Da implementare post-development
**Owner**: Development Team
