# 📋 TECHNICAL DEBT PLAN - PILOTPROS REFACTORING ROADMAP

## 🚨 P0 - CRITICITÀ SICUREZZA (1-2 giorni)

### **1. Fix Vulnerabilità NPM** ⚠️ **IMMEDIATO**
```bash
# Fix automatico vulnerabilità
npm audit fix
npm audit fix --force

# Update dipendenze critiche
npm install axios@latest
npm install @sendgrid/mail@latest
npm install form-data@latest
```

**File interessati**:
- `package.json` (root)
- `backend/package.json`
- `frontend/package.json`

**Impact**: 33 vulnerabilità (15 critiche) risolte

---

### **2. Cleanup File Obsoleti** 🗑️ **IMMEDIATO**
```bash
# Rimuovere file temporanei/obsoleti
rm .DS_Store
rm -rf logs/ai-agent.log
rm -rf frontend/dist/
rm frontend/src/pages/ExecutionsPagePrime.vue
rm test-production.js

# Aggiungere a .gitignore
echo "dist/" >> .gitignore
echo ".DS_Store" >> .gitignore
echo "*.log" >> .gitignore
```

**File da rimuovere**:
- `frontend/src/pages/ExecutionsPagePrime.vue` ❌
- `test-production.js` ❌
- `.DS_Store` ❌
- `logs/ai-agent.log` ❌

---

## 🔧 P1 - ARCHITETTURA CRITICA (3-5 giorni)

### **3. Sostituzione Sistema Autenticazione** 🔐 **ALTO IMPATTO**

**Da sostituire**: `backend/src/auth/jwt-auth.js` (700+ righe custom)

**Con**:
```bash
# Installazione Passport.js + Redis
npm install passport passport-jwt passport-local redis connect-redis express-session
```

**Implementazione**:
```javascript
// backend/src/auth/passport-config.js
import passport from 'passport'
import { Strategy as JwtStrategy } from 'passport-jwt'
import { Strategy as LocalStrategy } from 'passport-local'
import redis from 'redis'

// Configurazione Redis per sessioni
const redisClient = redis.createClient({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379
})

// Session store Redis
import session from 'express-session'
import RedisStore from 'connect-redis'

app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    maxAge: 1000 * 60 * 30 // 30 minuti
  }
}))
```

**File da modificare**:
- `backend/src/auth/passport-config.js` ✨ **NUOVO**
- `backend/src/middleware/auth.js` 🔄 **REFACTOR**
- `backend/src/controllers/auth.controller.js` 🔄 **REFACTOR**
- `docker-compose.yml` ➕ **ADD REDIS SERVICE**

**Vantaggi**:
- ✅ Standard industry
- ✅ Session revocation immediata
- ✅ Multi-strategy auth (OAuth, LDAP)
- ✅ Security patches automatiche

---

### **4. Servizio Email Esterno** 📧 **MEDIO IMPATTO**

**Da sostituire**: Custom email handling in `backend/src/services/`

**Con SendGrid**:
```bash
npm install @sendgrid/mail
```

```javascript
// backend/src/services/email.service.js
import sgMail from '@sendgrid/mail'

sgMail.setApiKey(process.env.SENDGRID_API_KEY)

export class EmailService {
  static async sendTransactional(to, subject, html) {
    const msg = {
      to,
      from: process.env.FROM_EMAIL,
      subject,
      html,
    }
    return sgMail.send(msg)
  }
}
```

**File da modificare**:
- `backend/src/services/email.service.js` ✨ **NUOVO**
- `backend/src/controllers/auth.controller.js` 🔄 **UPDATE**

---

### **5. Reverse Proxy Implementation** 🌐 **NETWORK ISOLATION**

**Timing critico**: Solo DOPO completamento Redis + Passport.js

**Dipendenze**:
- ✅ Redis session store funzionante
- ✅ Passport.js authentication implementata
- ✅ Backend API aggiornate per session management

**Implementazione**:
```bash
# Update docker-compose per reverse proxy
# Aggiungere Redis alla rete isolata
# Configurare nginx per session affinity
./scripts/setup-reverse-proxy.sh
```

**File da modificare**:
- `docker-compose.reverseproxy.yml` 🔄 **UPDATE con Redis**
- `nginx/nginx.conf` 🔄 **UPDATE per session management**
- `.env` ➕ **ADD REDIS/SESSION variables**

**Documentazione di riferimento**: `docs/STRATEGY/REVERSE_PROXY_README.md`

**Vantaggi**:
- ✅ Network isolation completa
- ✅ Branding injection per clienti
- ✅ Dev panel per team tecnico
- ✅ SSL termination
- ✅ Rate limiting

---

### **6. Consolidazione Versioni n8n** 🔄 **CONSISTENCY**

**Problema**: Versioni inconsistenti
- `docker-compose.yml`: `n8nio/n8n:1.110.1`
- `package.json`: `"n8n": "^1.107.3"`

**Fix**:
```yaml
# docker-compose.yml
automation-engine-dev:
  image: n8nio/n8n:1.110.1
```

```json
// package.json
{
  "dependencies": {
    "n8n": "^1.110.1"
  }
}
```

---

## 📊 P2 - CODICE QUALITY (5-7 giorni)

### **7. Sostituzione Business Parsers** 🔄 **REFACTOR CUSTOM**

**Da sostituire**:
- `backend/src/utils/business-terminology.js` (440 righe)
- `frontend/src/shared/business-parsers/unified-processor.ts`

**Con librerie standard**:
```bash
# Installazione i18next per mappature
npm install i18next i18next-node-fs-backend i18next-browser-languagedetector

# Joi per validazione
npm install joi

# Natural per text processing
npm install natural

# Node-cache per caching
npm install node-cache
```

**Implementazione**:
```javascript
// backend/src/services/terminology.service.js
import i18next from 'i18next'
import Backend from 'i18next-node-fs-backend'

i18next.use(Backend).init({
  lng: 'business',
  fallbackLng: 'technical',
  backend: {
    loadPath: './locales/{{lng}}/{{ns}}.json'
  }
})

export class TerminologyService {
  static translate(technicalTerm) {
    return i18next.t(technicalTerm) || technicalTerm
  }
}
```

**File da creare**:
- `backend/locales/business/terminology.json` ✨ **NUOVO**
- `backend/src/services/terminology.service.js` ✨ **NUOVO**
- `frontend/src/services/text-processor.ts` ✨ **NUOVO**

---

### **8. Standardizzazione Logging** 📝 **CONSOLIDATION**

**Problema**: Doppio logging (`winston` + `pino`)

**Soluzione**: Mantenere solo Winston
```bash
npm uninstall pino pino-pretty
```

**File da modificare**:
- `backend/src/utils/logger.js` 🔄 **CLEANUP**
- `backend/src/server.js` 🔄 **UPDATE**

---

### **9. Caching Standard** ⚡ **PERFORMANCE**

**Da sostituire**: Custom caching in `unified-processor.ts`

**Con Redis/Node-cache**:
```bash
npm install ioredis node-cache
```

```javascript
// backend/src/services/cache.service.js
import Redis from 'ioredis'
import NodeCache from 'node-cache'

export class CacheService {
  constructor() {
    this.redis = new Redis(process.env.REDIS_URL)
    this.nodeCache = new NodeCache({ stdTTL: 600 }) // 10 min fallback
  }

  async get(key) {
    try {
      return await this.redis.get(key)
    } catch {
      return this.nodeCache.get(key)
    }
  }

  async set(key, value, ttl = 600) {
    try {
      await this.redis.setex(key, ttl, value)
    } catch {
      this.nodeCache.set(key, value, ttl)
    }
  }
}
```

---

### **10. Rimozione Console.log** 🐛 **DEBUGGING**

**File con console.log da pulire**:
- `frontend/src/pages/ExecutionsPage.vue` (linee 380-381, 434, etc.)
- `backend/src/server.js`
- `frontend/src/stores/auth.ts`

**Sostituzione**:
```javascript
// Invece di console.log
if (process.env.NODE_ENV === 'development') {
  console.log('Debug info')
}

// O meglio con logger
import { logger } from '../utils/logger'
logger.debug('Debug info')
```

---

### **11. Fix Memory Leak** 🧠 **STABILITY**

**File**: `frontend/src/pages/ExecutionsPage.vue:363`

**Problema**:
```javascript
let refreshInterval: NodeJS.Timeout
// Non viene sempre cleared
```

**Fix**:
```javascript
import { onUnmounted } from 'vue'

let refreshInterval: NodeJS.Timeout | null = null

const startRefresh = () => {
  if (refreshInterval) clearInterval(refreshInterval)
  refreshInterval = setInterval(refreshExecutions, 30000)
}

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})
```

---

## 🔍 P3 - OPTIMIZATION (2-3 giorni)

### **12. TypeScript Strict Mode** 📘 **TYPE SAFETY**

**File**: `frontend/tsconfig.json`

**Da**:
```json
{
  "compilerOptions": {
    "strict": false
  }
}
```

**A**:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true
  }
}
```

**File da tipizzare**:
- `frontend/src/pages/ExecutionsPage.vue` (rimuovere `any[]`)
- `frontend/src/stores/*` (aggiungere proper types)

---

### **13. Database Connection Optimization** 🗄️ **PERFORMANCE**

**File**: `backend/src/db/connection.js`

**Review**:
```javascript
// Verifica pool settings
const dbPool = postgres(connectionString, {
  max: 20,          // Connessioni massime
  idle_timeout: 20, // Timeout idle
  connect_timeout: 10 // Timeout connessione
})
```

---

### **14. Frontend Bundle Optimization** 📦 **SIZE**

**File**: `frontend/vite.config.ts`

**Aggiungere**:
```javascript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['primevue', '@primevue/themes'],
          charts: ['chart.js', 'vue-chartjs']
        }
      }
    }
  }
})
```

---

### **15. Documentazione API** 📚 **DOCUMENTATION**

**Installazione Swagger**:
```bash
npm install swagger-jsdoc swagger-ui-express
```

**File**: `backend/src/docs/swagger.js` (già presente - da completare)

---

## 🧪 P4 - TESTING & QUALITY (3-4 giorni)

### **16. Test Suite Setup** 🧪 **TESTING**

```bash
# Backend testing
npm install --save-dev jest supertest @types/jest

# Frontend testing
npm install --save-dev vitest @vue/test-utils jsdom
```

**File da creare**:
- `backend/tests/auth.test.js` ✨ **NUOVO**
- `frontend/tests/ExecutionsPage.test.ts` ✨ **NUOVO**

---

### **17. Linting Rules** 📏 **CODE STYLE**

**File**: `frontend/.eslintrc.js`

**Aggiungere**:
```javascript
module.exports = {
  rules: {
    'no-console': 'warn',
    'no-unused-vars': 'error',
    '@typescript-eslint/no-explicit-any': 'warn'
  }
}
```

---

## 📈 TIMELINE IMPLEMENTAZIONE

### **Settimana 1**:
- ✅ P0: Fix vulnerabilità + cleanup (1-2 giorni)
- 🔧 P1: Autenticazione Passport.js (3 giorni)

### **Settimana 2**:
- 📧 P1: Email service + n8n versioning (2 giorni)
- 🌐 **P1.5: Reverse Proxy Implementation** (1 giorno) - **DOPO Redis+Passport.js**
- 🔄 P2: Business parsers refactor (2 giorni)

### **Settimana 3**:
- 📝 P2: Logging + caching (2 giorni)
- 🐛 P2: Console.log cleanup + memory fixes (2 giorni)
- 📘 P3: TypeScript strict (1 giorno)

### **Settimana 4**:
- 📦 P3: Performance optimization (2 giorni)
- 🧪 P4: Testing setup (2 giorni)
- 📚 P4: Documentation (1 giorno)

---

## 🎯 ROI PRIORITARIO

1. **Autenticazione Passport.js**: ⭐⭐⭐⭐⭐ (Security + Maintainability)
2. **Fix Vulnerabilità**: ⭐⭐⭐⭐⭐ (Critical Security)
3. **Reverse Proxy**: ⭐⭐⭐⭐⭐ (Network Security + Client Branding)
4. **Email Service**: ⭐⭐⭐⭐ (Reliability + Deliverability)
5. **Business Parsers**: ⭐⭐⭐ (Code Quality + Maintainability)
6. **Performance Optimization**: ⭐⭐⭐ (User Experience)

---

## 📊 METRICHE DI SUCCESSO

### **Sicurezza**:
- ✅ 0 vulnerabilità critiche
- ✅ Autenticazione standard-compliant
- ✅ Session management sicuro

### **Performance**:
- ✅ Bundle size ridotto del 20%
- ✅ Time to Interactive < 3s
- ✅ Memory leaks eliminati

### **Maintainability**:
- ✅ Code coverage > 80%
- ✅ TypeScript strict mode
- ✅ Zero console.log in production

### **Standards Compliance**:
- ✅ Battle-tested libraries utilizzate
- ✅ Documentazione API completa
- ✅ Linting rules enforced

---

## 💰 EFFORT STIMATO

**Effort totale**: 15-20 giorni lavorativi (3-4 settimane)
**Team size**: 1-2 developers
**Budget**: Medio (principalmente tempo sviluppo + eventuali servizi esterni)

**Benefici a lungo termine**:
- 🔐 Security hardening
- 🛠️ Reduced maintenance overhead
- 📈 Improved developer experience
- ⚡ Better performance
- 📏 Standards compliance