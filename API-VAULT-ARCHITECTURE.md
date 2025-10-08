# 🔐 API VAULT - SISTEMA BLINDATO PER GESTIONE API KEYS

**Data Creazione**: 2025-10-08
**Last Updated**: 2025-10-08 (Post Best Practices Research)
**Status**: 🚧 Design Document v2.0 - INDUSTRY-COMPLIANT
**Priorità**: 🔴 CRITICAL - Sistema vendibile multi-cliente

**RESEARCH STATUS**: ✅ Validated against OWASP/NIST/AWS/Azure standards
**CRITICAL FIXES REQUIRED**: 3 (Envelope Encryption, IV Generation, No .env Fallback)

---

## 📋 PROBLEMA IDENTIFICATO

**SCENARIO ATTUALE:**
- ❌ API Keys hardcoded in `.env` files (33 occorrenze in codebase)
- ❌ Chiavi LLM sparse in multipli servizi (backend, intelligence-engine, agent-engine)
- ❌ Ogni cambio cliente = debug manuale + restart container
- ❌ NO validazione automatica delle chiavi
- ❌ NO rotazione sicura
- ❌ NO audit trail delle modifiche
- ❌ Rischio leak chiavi in logs/backups

**IMPACT:**
- 🚫 Sistema NON scalabile per vendita multi-cliente
- 🚫 Onboarding cliente richiede intervento tecnico manuale
- 🚫 Ogni errore API key = ticket supporto + downtime
- 🚫 Zero compliance (GDPR, SOC2) per gestione secrets

---

## 🎯 OBIETTIVO

**Sistema API Vault Production-Ready:**

1. ✅ **Database-driven Configuration** - Chiavi in PostgreSQL encrypted table
2. ✅ **Zero Restart Policy** - Cambio API = reload in-memory senza restart container
3. ✅ **Self-Service Admin UI** - Cliente può gestire proprie chiavi (con validazione)
4. ✅ **Auto-Validation** - Health check automatico prima di attivare nuove chiavi
5. ✅ **Audit Trail** - Log completo modifiche (chi, quando, cosa)
6. ✅ **Encryption at Rest** - AES-256-GCM + master key rotation
7. ✅ **Graceful Fallback** - Backup API keys in caso di DB failure

---

## 🏗️ ARCHITETTURA PROPOSTA

### **3-Layer Security Model**

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Admin UI (Frontend + Backend API)             │
│  - React settings page (admin-only)                      │
│  - Masked input fields (••••••••••)                      │
│  - Test Connection button (pre-validation)               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: API Vault Service (Backend)                   │
│  - Envelope Encryption (DEK + KEK)                       │
│  - Counter-based IV generation (NIST compliant)          │
│  - In-memory cache (5min TTL, Buffer-based)              │
│  - Auto-refresh mechanism (every 5min check DB)          │
│  - Health check validators (OpenAI, Groq, LangSmith)     │
│  - No .env fallback in production (fail-safe)            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: PostgreSQL Vault Table                        │
│  - pilotpros.api_credentials (encrypted storage)         │
│  - pilotpros.api_credentials_audit (change history)      │
│  - Row-level security (RLS)                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🚨 CRITICAL UPDATES (Post Industry Research)

**Research Completed**: 2025-10-08
**Sources**: OWASP, NIST SP 800-38D, AWS/Azure Best Practices, Security Forums

### **🔴 CRITICAL FIX #1: Envelope Encryption (NIST Compliant)**

**Problem**: Original design usa direct encryption (plaintext → AES-256-GCM → ciphertext).
**Industry Standard**: Envelope encryption (Data Encryption Key + Key Encryption Key).

**Why Required:**
- ✅ Master key rotation WITHOUT re-encrypting all data
- ✅ Reduced master key exposure (used only for DEK encryption)
- ✅ NIST SP 800-57 compliance
- ✅ AWS/Azure/HashiCorp Vault standard

**Implementation:**
```javascript
// OLD (Direct Encryption) - NON COMPLIANT
ciphertext = AES-256-GCM(apiKey, masterKey)

// NEW (Envelope Encryption) - INDUSTRY STANDARD
dek = generateRandomKey(32) // 256-bit Data Encryption Key
encryptedApiKey = AES-256-GCM(apiKey, dek)
encryptedDEK = AES-256-GCM(dek, masterKey) // Master Key = KEK
store(encryptedApiKey, encryptedDEK, iv, authTag)
```

**Database Changes:**
```sql
ALTER TABLE pilotpros.api_credentials
ADD COLUMN dek_encrypted TEXT NOT NULL,  -- Encrypted DEK
ADD COLUMN dek_iv TEXT NOT NULL,          -- DEK encryption IV
ADD COLUMN dek_auth_tag TEXT NOT NULL;    -- DEK auth tag
```

---

### **🔴 CRITICAL FIX #2: Counter-Based IV Generation**

**Problem**: Original design usa random IV per ogni encryption.
**Risk**: NIST SP 800-38D warning - "IV collision dopo 2^32 encryptions = CATASTROPHIC"

**Why Required:**
- ❌ Random IV = birthday paradox (collision probability after ~2^32 operations)
- ❌ IV collision in GCM = plaintext recovery attack possible
- ✅ Counter-based IV = guaranteed uniqueness (deterministic)

**Implementation:**
```javascript
class SecureIVGenerator {
  constructor() {
    this.randomPrefix = crypto.randomBytes(8); // 64-bit random prefix
    this.counter = 0; // 32-bit counter (max 4B operations)
  }

  generate() {
    // 96-bit IV = 64-bit random prefix + 32-bit counter
    const iv = Buffer.alloc(12);
    this.randomPrefix.copy(iv, 0, 0, 8);
    iv.writeUInt32BE(this.counter++, 8);

    // Safety: Alert BEFORE counter overflow
    if (this.counter >= 0xFFFF0000) { // 2^32 - 65536
      logger.critical('IV counter approaching limit - ROTATE ENCRYPTION KEY NOW');
      // Trigger auto-rotation
    }

    if (this.counter >= 0xFFFFFFFF) {
      throw new Error('IV counter exhausted - KEY ROTATION REQUIRED');
    }

    return iv;
  }

  reset() {
    // Reset counter on key rotation
    this.randomPrefix = crypto.randomBytes(8);
    this.counter = 0;
  }
}
```

**Database Changes:**
```sql
ALTER TABLE pilotpros.api_credentials
ADD COLUMN iv_counter BIGINT DEFAULT 0,           -- Track IV usage
ADD COLUMN iv_random_prefix TEXT NOT NULL,        -- 64-bit prefix
ADD COLUMN rotation_threshold BIGINT DEFAULT 4294967000; -- Alert before 2^32
```

---

### **🔴 CRITICAL FIX #3: No .env Fallback in Production**

**Problem**: Original design allows fallback to environment variables if vault unavailable.
**Security Issue**: OWASP Anti-Pattern - "Environment variables exposed in crash dumps, logs"

**Why Required:**
- ❌ Process memory dumps reveal .env secrets
- ❌ CI/CD pipelines leak .env in logs
- ❌ Zero audit trail for .env access
- ✅ Fail-safe better than insecure fallback

**Implementation:**
```javascript
async getApiKey(provider, environment = 'production') {
  const isProduction = process.env.NODE_ENV === 'production';

  // Fetch from vault
  const key = await this.fetchFromVault(provider, environment);

  if (!key) {
    if (isProduction) {
      // Production: FAIL-SAFE (no fallback)
      throw new VaultError(
        `API key not found for ${provider} - no fallback in production. ` +
        `Add key via Admin UI: ${config.frontendUrl}/settings/api-vault`
      );
    } else {
      // Development: Allow .env fallback (with warning)
      logger.warn(`⚠️ Vault miss for ${provider} - falling back to .env (DEV ONLY)`);
      return process.env[`${provider.toUpperCase()}_API_KEY`];
    }
  }

  return key;
}
```

---

### **⚠️ HIGH PRIORITY FIXES**

#### **FIX #4: Auto Key Rotation (NIST 90-day policy)**

**Current**: Manual rotation only
**Required**: Automatic rotation before 2^32 operations OR every 90 days

```sql
ALTER TABLE pilotpros.api_credentials
ADD COLUMN key_version INTEGER DEFAULT 1,
ADD COLUMN rotation_schedule VARCHAR(50) DEFAULT '0 0 1 */3 *', -- Every 90 days
ADD COLUMN next_rotation TIMESTAMP,
ADD COLUMN rotation_count INTEGER DEFAULT 0,
ADD COLUMN operations_count BIGINT DEFAULT 0; -- Track usage
```

#### **FIX #5: Memory Zeroing (Buffer-based cache)**

**Current**: String-based cache (immutable, stays in memory)
**Required**: Buffer-based cache (can be zeroed)

```javascript
class SecureCache {
  set(key, value) {
    const buffer = Buffer.from(value, 'utf8'); // NOT String!
    this.cache.set(key, { buffer, timestamp: Date.now() });

    // Auto-evict after 5 minutes (reduced from 30)
    setTimeout(() => {
      const entry = this.cache.get(key);
      if (entry) {
        entry.buffer.fill(0); // Zero memory
        this.cache.delete(key);
      }
    }, 5 * 60 * 1000); // 5min TTL (not 30!)
  }
}
```

#### **FIX #6: Row-Level Security (Multi-Tenant Isolation)**

**Current**: Application-level filtering
**Required**: Database-enforced isolation (PostgreSQL RLS)

```sql
-- Enable Row-Level Security
ALTER TABLE pilotpros.api_credentials ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their organization's keys
CREATE POLICY api_credentials_isolation ON pilotpros.api_credentials
  USING (
    organization_id = current_setting('app.organization_id', true)::uuid
  );

-- Add organization column
ALTER TABLE pilotpros.api_credentials
ADD COLUMN organization_id UUID REFERENCES pilotpros.organizations(id);
```

---

## 📊 DATABASE SCHEMA

### **Main Vault Table**

```sql
CREATE TABLE pilotpros.api_credentials (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'groq', 'langsmith', 'anthropic'
    api_key_encrypted TEXT NOT NULL,  -- AES-256-GCM encrypted
    encryption_iv TEXT NOT NULL,  -- Initialization vector
    api_key_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash (for duplicate detection)

    -- Metadata
    environment VARCHAR(20) DEFAULT 'production',  -- 'production', 'staging', 'test'
    is_active BOOLEAN DEFAULT false,  -- Only ONE active key per provider
    is_validated BOOLEAN DEFAULT false,  -- Passed health check
    last_validated_at TIMESTAMP,
    validation_error TEXT,  -- Last validation error message

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    rate_limit_remaining INTEGER,
    rate_limit_reset_at TIMESTAMP,

    -- Audit
    created_by UUID REFERENCES pilotpros.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES pilotpros.users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_active_provider UNIQUE NULLS NOT DISTINCT (provider, environment, is_active)
);

-- Indexes
CREATE INDEX idx_api_credentials_provider ON pilotpros.api_credentials(provider, environment, is_active);
CREATE INDEX idx_api_credentials_active ON pilotpros.api_credentials(is_active, is_validated);
```

### **Audit Trail Table**

```sql
CREATE TABLE pilotpros.api_credentials_audit (
    id SERIAL PRIMARY KEY,
    credential_id INTEGER REFERENCES pilotpros.api_credentials(id),
    action VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'activated', 'deactivated', 'validated', 'deleted'
    old_values JSONB,
    new_values JSONB,
    performed_by UUID REFERENCES pilotpros.users(id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_credentials_audit_credential_id ON pilotpros.api_credentials_audit(credential_id);
CREATE INDEX idx_api_credentials_audit_timestamp ON pilotpros.api_credentials_audit(timestamp);
```

---

## 🔐 ENCRYPTION STRATEGY

### **Master Key Management**

```javascript
// backend/src/services/encryption.service.js

import crypto from 'crypto';
import config from '../config/index.js';

class EncryptionService {
  constructor() {
    // Master key from environment (NEVER in database)
    // Generated once per installation: openssl rand -base64 32
    this.masterKey = process.env.API_VAULT_MASTER_KEY;

    if (!this.masterKey) {
      throw new Error('API_VAULT_MASTER_KEY not set - CRITICAL SECURITY ERROR');
    }

    this.algorithm = 'aes-256-gcm';
    this.keyLength = 32; // 256 bits
  }

  /**
   * Encrypt API key
   * @returns {object} {encrypted, iv, authTag}
   */
  encrypt(plaintext) {
    const iv = crypto.randomBytes(16); // Initialization vector
    const key = Buffer.from(this.masterKey, 'base64');

    const cipher = crypto.createCipheriv(this.algorithm, key, iv);

    let encrypted = cipher.update(plaintext, 'utf8', 'base64');
    encrypted += cipher.final('base64');

    const authTag = cipher.getAuthTag();

    return {
      encrypted,
      iv: iv.toString('base64'),
      authTag: authTag.toString('base64')
    };
  }

  /**
   * Decrypt API key
   * @param {object} data - {encrypted, iv, authTag}
   * @returns {string} Plaintext API key
   */
  decrypt(data) {
    const key = Buffer.from(this.masterKey, 'base64');
    const iv = Buffer.from(data.iv, 'base64');
    const authTag = Buffer.from(data.authTag, 'base64');

    const decipher = crypto.createDecipheriv(this.algorithm, key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(data.encrypted, 'base64', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }

  /**
   * Hash API key (for duplicate detection without storing plaintext)
   */
  hash(plaintext) {
    return crypto.createHash('sha256').update(plaintext).digest('hex');
  }
}

export default new EncryptionService();
```

---

## 🔄 API VAULT SERVICE

### **Core Service**

```javascript
// backend/src/services/api-vault.service.js

import db from '../db/index.js';
import encryptionService from './encryption.service.js';
import logger from '../utils/logger.js';

class ApiVaultService {
  constructor() {
    this.cache = new Map(); // In-memory cache
    this.cacheExpiry = 30 * 60 * 1000; // 30 minutes
    this.autoRefreshInterval = 5 * 60 * 1000; // 5 minutes
    this.lastRefresh = null;

    // Start auto-refresh
    this.startAutoRefresh();
  }

  /**
   * Get active API key for provider
   * @param {string} provider - 'openai', 'groq', etc.
   * @param {string} environment - 'production', 'staging', 'test'
   * @returns {string|null} Decrypted API key
   */
  async getApiKey(provider, environment = 'production') {
    const cacheKey = `${provider}:${environment}`;

    // Check cache first
    const cached = this.cache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp < this.cacheExpiry)) {
      logger.debug(`API key cache HIT for ${provider}`);
      return cached.apiKey;
    }

    // Fetch from database
    logger.debug(`API key cache MISS for ${provider} - fetching from DB`);

    const result = await db.query(`
      SELECT api_key_encrypted, encryption_iv, auth_tag
      FROM pilotpros.api_credentials
      WHERE provider = $1
        AND environment = $2
        AND is_active = true
        AND is_validated = true
      ORDER BY updated_at DESC
      LIMIT 1
    `, [provider, environment]);

    if (result.rows.length === 0) {
      logger.warn(`No active API key found for ${provider} (${environment})`);
      return null;
    }

    const { api_key_encrypted, encryption_iv, auth_tag } = result.rows[0];

    // Decrypt
    const decrypted = encryptionService.decrypt({
      encrypted: api_key_encrypted,
      iv: encryption_iv,
      authTag: auth_tag
    });

    // Update cache
    this.cache.set(cacheKey, {
      apiKey: decrypted,
      timestamp: Date.now()
    });

    // Update usage tracking
    await this.trackUsage(provider, environment);

    return decrypted;
  }

  /**
   * Set new API key (with validation)
   * @param {object} params - {provider, apiKey, userId}
   * @returns {object} Result with validation status
   */
  async setApiKey({ provider, apiKey, environment = 'production', userId }) {
    // 1. Validate key format
    if (!this.validateKeyFormat(provider, apiKey)) {
      throw new Error(`Invalid API key format for ${provider}`);
    }

    // 2. Test connection (pre-validation)
    const validationResult = await this.validateApiKey(provider, apiKey);
    if (!validationResult.valid) {
      throw new Error(`API key validation failed: ${validationResult.error}`);
    }

    // 3. Encrypt
    const { encrypted, iv, authTag } = encryptionService.encrypt(apiKey);
    const hash = encryptionService.hash(apiKey);

    // 4. Deactivate old keys
    await db.query(`
      UPDATE pilotpros.api_credentials
      SET is_active = false,
          updated_at = CURRENT_TIMESTAMP,
          updated_by = $1
      WHERE provider = $2 AND environment = $3 AND is_active = true
    `, [userId, provider, environment]);

    // 5. Insert new key
    const result = await db.query(`
      INSERT INTO pilotpros.api_credentials (
        provider,
        api_key_encrypted,
        encryption_iv,
        auth_tag,
        api_key_hash,
        environment,
        is_active,
        is_validated,
        last_validated_at,
        created_by,
        updated_by
      ) VALUES ($1, $2, $3, $4, $5, $6, true, true, CURRENT_TIMESTAMP, $7, $7)
      RETURNING id
    `, [provider, encrypted, iv, authTag, hash, environment, userId]);

    const credentialId = result.rows[0].id;

    // 6. Audit log
    await this.logAudit({
      credentialId,
      action: 'created',
      newValues: { provider, environment, is_active: true },
      userId
    });

    // 7. Clear cache to force reload
    this.invalidateCache(provider, environment);

    logger.info(`✅ New API key activated for ${provider} (${environment})`);

    return {
      success: true,
      credentialId,
      validationResult
    };
  }

  /**
   * Validate API key by making test request
   */
  async validateApiKey(provider, apiKey) {
    try {
      switch (provider) {
        case 'openai':
          return await this.validateOpenAI(apiKey);
        case 'groq':
          return await this.validateGroq(apiKey);
        case 'langsmith':
          return await this.validateLangSmith(apiKey);
        case 'anthropic':
          return await this.validateAnthropic(apiKey);
        default:
          throw new Error(`Unknown provider: ${provider}`);
      }
    } catch (error) {
      logger.error(`API validation error for ${provider}:`, error);
      return {
        valid: false,
        error: error.message
      };
    }
  }

  async validateOpenAI(apiKey) {
    const response = await fetch('https://api.openai.com/v1/models', {
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      return { valid: false, error: error.error?.message || 'Invalid API key' };
    }

    const data = await response.json();
    return {
      valid: true,
      details: {
        models_count: data.data?.length || 0,
        verified_at: new Date().toISOString()
      }
    };
  }

  async validateGroq(apiKey) {
    const response = await fetch('https://api.groq.com/openai/v1/models', {
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    });

    if (!response.ok) {
      return { valid: false, error: 'Invalid Groq API key' };
    }

    return { valid: true, details: { verified_at: new Date().toISOString() } };
  }

  async validateLangSmith(apiKey) {
    const response = await fetch('https://api.smith.langchain.com/api/v1/sessions', {
      method: 'GET',
      headers: {
        'X-API-Key': apiKey
      }
    });

    if (!response.ok) {
      return { valid: false, error: 'Invalid LangSmith API key' };
    }

    return { valid: true, details: { verified_at: new Date().toISOString() } };
  }

  async validateAnthropic(apiKey) {
    // Anthropic doesn't have a public test endpoint - basic format check only
    if (!apiKey.startsWith('sk-ant-')) {
      return { valid: false, error: 'Invalid Anthropic API key format' };
    }

    return { valid: true, details: { format_check: true } };
  }

  /**
   * Auto-refresh cache from database
   */
  startAutoRefresh() {
    setInterval(async () => {
      logger.debug('🔄 Auto-refreshing API vault cache...');

      // Check if any keys were updated in DB since last refresh
      const lastRefreshTime = this.lastRefresh || new Date(Date.now() - this.autoRefreshInterval);

      const result = await db.query(`
        SELECT DISTINCT provider, environment
        FROM pilotpros.api_credentials
        WHERE updated_at > $1 AND is_active = true
      `, [lastRefreshTime]);

      if (result.rows.length > 0) {
        logger.info(`🔄 Detected ${result.rows.length} updated API key(s) - invalidating cache`);

        result.rows.forEach(({ provider, environment }) => {
          this.invalidateCache(provider, environment);
        });
      }

      this.lastRefresh = new Date();
    }, this.autoRefreshInterval);
  }

  /**
   * Clear cache for specific provider
   */
  invalidateCache(provider, environment = 'production') {
    const cacheKey = `${provider}:${environment}`;
    this.cache.delete(cacheKey);
    logger.debug(`Cache invalidated for ${cacheKey}`);
  }

  /**
   * Track API key usage
   */
  async trackUsage(provider, environment) {
    await db.query(`
      UPDATE pilotpros.api_credentials
      SET usage_count = usage_count + 1,
          last_used_at = CURRENT_TIMESTAMP
      WHERE provider = $1 AND environment = $2 AND is_active = true
    `, [provider, environment]);
  }

  /**
   * Audit log helper
   */
  async logAudit({ credentialId, action, oldValues = null, newValues = null, userId, ipAddress = null, userAgent = null }) {
    await db.query(`
      INSERT INTO pilotpros.api_credentials_audit (
        credential_id, action, old_values, new_values,
        performed_by, ip_address, user_agent
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
    `, [
      credentialId,
      action,
      oldValues ? JSON.stringify(oldValues) : null,
      newValues ? JSON.stringify(newValues) : null,
      userId,
      ipAddress,
      userAgent
    ]);
  }

  /**
   * Validate API key format (basic checks)
   */
  validateKeyFormat(provider, apiKey) {
    const patterns = {
      openai: /^sk-[a-zA-Z0-9-_]{20,}$/,
      groq: /^gsk_[a-zA-Z0-9]{32,}$/,
      langsmith: /^ls__[a-zA-Z0-9-_]{20,}$/,
      anthropic: /^sk-ant-[a-zA-Z0-9-_]{20,}$/
    };

    const pattern = patterns[provider];
    if (!pattern) {
      logger.warn(`No validation pattern for provider: ${provider}`);
      return true; // Allow unknown providers
    }

    return pattern.test(apiKey);
  }
}

export default new ApiVaultService();
```

---

## 🌐 BACKEND API ROUTES

```javascript
// backend/src/routes/api-vault.routes.js

import express from 'express';
import apiVaultService from '../services/api-vault.service.js';
import { requireAuth, requireAdmin } from '../middleware/auth.js';

const router = express.Router();

/**
 * GET /api/vault/credentials
 * List all API credentials (masked)
 * ADMIN ONLY
 */
router.get('/credentials', requireAuth, requireAdmin, async (req, res) => {
  try {
    const result = await db.query(`
      SELECT
        id,
        provider,
        environment,
        is_active,
        is_validated,
        last_validated_at,
        validation_error,
        usage_count,
        last_used_at,
        created_at,
        updated_at
      FROM pilotpros.api_credentials
      ORDER BY provider, environment, updated_at DESC
    `);

    res.json({
      success: true,
      credentials: result.rows
    });
  } catch (error) {
    logger.error('Error fetching credentials:', error);
    res.status(500).json({ error: 'Failed to fetch credentials' });
  }
});

/**
 * POST /api/vault/credentials
 * Add new API credential
 * ADMIN ONLY
 */
router.post('/credentials', requireAuth, requireAdmin, async (req, res) => {
  try {
    const { provider, apiKey, environment = 'production' } = req.body;

    if (!provider || !apiKey) {
      return res.status(400).json({ error: 'Provider and API key required' });
    }

    const result = await apiVaultService.setApiKey({
      provider,
      apiKey,
      environment,
      userId: req.user.id
    });

    res.json({
      success: true,
      message: `API key for ${provider} added and validated successfully`,
      credentialId: result.credentialId
    });
  } catch (error) {
    logger.error('Error adding credential:', error);
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/vault/credentials/:id/validate
 * Re-validate existing credential
 * ADMIN ONLY
 */
router.post('/credentials/:id/validate', requireAuth, requireAdmin, async (req, res) => {
  try {
    const { id } = req.params;

    // Fetch encrypted key
    const result = await db.query(`
      SELECT provider, api_key_encrypted, encryption_iv, auth_tag, environment
      FROM pilotpros.api_credentials
      WHERE id = $1
    `, [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Credential not found' });
    }

    const { provider, api_key_encrypted, encryption_iv, auth_tag, environment } = result.rows[0];

    // Decrypt
    const apiKey = encryptionService.decrypt({
      encrypted: api_key_encrypted,
      iv: encryption_iv,
      authTag: auth_tag
    });

    // Validate
    const validationResult = await apiVaultService.validateApiKey(provider, apiKey);

    // Update validation status
    await db.query(`
      UPDATE pilotpros.api_credentials
      SET is_validated = $1,
          last_validated_at = CURRENT_TIMESTAMP,
          validation_error = $2
      WHERE id = $3
    `, [validationResult.valid, validationResult.error || null, id]);

    // Audit log
    await apiVaultService.logAudit({
      credentialId: id,
      action: 'validated',
      newValues: { validation_result: validationResult },
      userId: req.user.id
    });

    res.json({
      success: true,
      validation: validationResult
    });
  } catch (error) {
    logger.error('Error validating credential:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * DELETE /api/vault/credentials/:id
 * Delete API credential
 * ADMIN ONLY
 */
router.delete('/credentials/:id', requireAuth, requireAdmin, async (req, res) => {
  try {
    const { id } = req.params;

    await db.query(`
      DELETE FROM pilotpros.api_credentials
      WHERE id = $1
    `, [id]);

    // Audit log
    await apiVaultService.logAudit({
      credentialId: id,
      action: 'deleted',
      userId: req.user.id
    });

    res.json({
      success: true,
      message: 'Credential deleted successfully'
    });
  } catch (error) {
    logger.error('Error deleting credential:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/vault/audit/:credentialId
 * Get audit history for credential
 * ADMIN ONLY
 */
router.get('/audit/:credentialId', requireAuth, requireAdmin, async (req, res) => {
  try {
    const { credentialId } = req.params;

    const result = await db.query(`
      SELECT
        a.*,
        u.email as performed_by_email
      FROM pilotpros.api_credentials_audit a
      LEFT JOIN pilotpros.users u ON a.performed_by = u.id
      WHERE a.credential_id = $1
      ORDER BY a.timestamp DESC
    `, [credentialId]);

    res.json({
      success: true,
      audit: result.rows
    });
  } catch (error) {
    logger.error('Error fetching audit:', error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
```

---

## 🖥️ FRONTEND ADMIN UI

### **Settings Page Component**

```vue
<!-- frontend/src/pages/APIVaultSettings.vue -->

<template>
  <div class="api-vault-settings">
    <Card>
      <template #title>
        <div class="flex items-center justify-between">
          <span>🔐 API Credentials Vault</span>
          <Button
            label="Add New Credential"
            icon="pi pi-plus"
            @click="showAddDialog = true"
          />
        </div>
      </template>

      <template #content>
        <!-- Credentials Table -->
        <DataTable
          :value="credentials"
          :loading="loading"
          class="p-datatable-sm"
          stripedRows
        >
          <Column field="provider" header="Provider">
            <template #body="{ data }">
              <Tag :value="data.provider" :severity="getProviderSeverity(data.provider)" />
            </template>
          </Column>

          <Column field="environment" header="Environment">
            <template #body="{ data }">
              <Badge :value="data.environment" :severity="data.environment === 'production' ? 'success' : 'info'" />
            </template>
          </Column>

          <Column field="is_active" header="Status">
            <template #body="{ data }">
              <Tag
                :value="data.is_active ? 'Active' : 'Inactive'"
                :severity="data.is_active ? 'success' : 'secondary'"
              />
            </template>
          </Column>

          <Column field="is_validated" header="Validation">
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <i
                  :class="data.is_validated ? 'pi pi-check-circle text-green-500' : 'pi pi-exclamation-triangle text-orange-500'"
                />
                <span class="text-sm">
                  {{ data.is_validated ? 'Valid' : 'Invalid' }}
                </span>
                <Button
                  icon="pi pi-refresh"
                  class="p-button-sm p-button-text"
                  @click="revalidate(data.id)"
                  v-tooltip="'Re-validate'"
                />
              </div>
            </template>
          </Column>

          <Column field="usage_count" header="Usage">
            <template #body="{ data }">
              {{ formatNumber(data.usage_count) }} calls
            </template>
          </Column>

          <Column field="last_used_at" header="Last Used">
            <template #body="{ data }">
              {{ formatDate(data.last_used_at) }}
            </template>
          </Column>

          <Column header="Actions">
            <template #body="{ data }">
              <div class="flex gap-2">
                <Button
                  icon="pi pi-history"
                  class="p-button-sm p-button-text"
                  @click="showAuditHistory(data.id)"
                  v-tooltip="'Audit History'"
                />
                <Button
                  icon="pi pi-trash"
                  class="p-button-sm p-button-text p-button-danger"
                  @click="confirmDelete(data.id)"
                  v-tooltip="'Delete'"
                />
              </div>
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <!-- Add Credential Dialog -->
    <Dialog
      v-model:visible="showAddDialog"
      header="Add API Credential"
      :modal="true"
      :style="{ width: '600px' }"
    >
      <div class="flex flex-col gap-4">
        <div class="field">
          <label for="provider">Provider</label>
          <Dropdown
            id="provider"
            v-model="newCredential.provider"
            :options="providerOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select Provider"
            class="w-full"
          />
        </div>

        <div class="field">
          <label for="environment">Environment</label>
          <Dropdown
            id="environment"
            v-model="newCredential.environment"
            :options="['production', 'staging', 'test']"
            placeholder="Select Environment"
            class="w-full"
          />
        </div>

        <div class="field">
          <label for="apiKey">API Key</label>
          <InputText
            id="apiKey"
            v-model="newCredential.apiKey"
            type="password"
            placeholder="sk-..."
            class="w-full"
          />
          <small class="text-muted">Key will be encrypted before storage</small>
        </div>

        <div v-if="validationStatus" class="field">
          <Message
            :severity="validationStatus.valid ? 'success' : 'error'"
            :closable="false"
          >
            {{ validationStatus.message }}
          </Message>
        </div>
      </div>

      <template #footer>
        <Button
          label="Test Connection"
          icon="pi pi-check-circle"
          @click="testConnection"
          :loading="testing"
          class="p-button-secondary"
        />
        <Button
          label="Cancel"
          icon="pi pi-times"
          @click="showAddDialog = false"
          class="p-button-text"
        />
        <Button
          label="Save"
          icon="pi pi-save"
          @click="saveCredential"
          :loading="saving"
          :disabled="!validationStatus?.valid"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import apiVaultService from '@/services/api-vault.service';

const toast = useToast();

const credentials = ref([]);
const loading = ref(false);
const showAddDialog = ref(false);

const newCredential = ref({
  provider: null,
  environment: 'production',
  apiKey: ''
});

const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Groq', value: 'groq' },
  { label: 'LangSmith', value: 'langsmith' },
  { label: 'Anthropic', value: 'anthropic' }
];

const validationStatus = ref(null);
const testing = ref(false);
const saving = ref(false);

const loadCredentials = async () => {
  loading.value = true;
  try {
    const response = await apiVaultService.getCredentials();
    credentials.value = response.credentials;
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load credentials',
      life: 3000
    });
  } finally {
    loading.value = false;
  }
};

const testConnection = async () => {
  testing.value = true;
  validationStatus.value = null;

  try {
    const result = await apiVaultService.validateKey(
      newCredential.value.provider,
      newCredential.value.apiKey
    );

    validationStatus.value = {
      valid: result.valid,
      message: result.valid
        ? '✅ API key validated successfully!'
        : `❌ Validation failed: ${result.error}`
    };
  } catch (error) {
    validationStatus.value = {
      valid: false,
      message: `❌ Validation error: ${error.message}`
    };
  } finally {
    testing.value = false;
  }
};

const saveCredential = async () => {
  saving.value = true;

  try {
    await apiVaultService.addCredential(newCredential.value);

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'API credential added successfully',
      life: 3000
    });

    showAddDialog.value = false;
    loadCredentials();
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message,
      life: 5000
    });
  } finally {
    saving.value = false;
  }
};

const revalidate = async (credentialId) => {
  try {
    const result = await apiVaultService.revalidateCredential(credentialId);

    toast.add({
      severity: result.validation.valid ? 'success' : 'error',
      summary: result.validation.valid ? 'Valid' : 'Invalid',
      detail: result.validation.valid
        ? 'API key is still valid'
        : result.validation.error,
      life: 3000
    });

    loadCredentials();
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to revalidate credential',
      life: 3000
    });
  }
};

onMounted(() => {
  loadCredentials();
});
</script>
```

---

## 📝 MIGRATION SQL

```sql
-- database/migrations/004_api_vault.sql

-- Enable pgcrypto extension for encryption helpers
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- API Credentials Vault
CREATE TABLE IF NOT EXISTS pilotpros.api_credentials (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    encryption_iv TEXT NOT NULL,
    auth_tag TEXT NOT NULL,
    api_key_hash VARCHAR(64) NOT NULL,

    environment VARCHAR(20) DEFAULT 'production',
    is_active BOOLEAN DEFAULT false,
    is_validated BOOLEAN DEFAULT false,
    last_validated_at TIMESTAMP,
    validation_error TEXT,

    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    rate_limit_remaining INTEGER,
    rate_limit_reset_at TIMESTAMP,

    created_by UUID REFERENCES pilotpros.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES pilotpros.users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Only ONE active key per provider+environment
    CONSTRAINT unique_active_provider EXCLUDE (provider WITH =, environment WITH =)
      WHERE (is_active = true)
);

-- Audit Trail
CREATE TABLE IF NOT EXISTS pilotpros.api_credentials_audit (
    id SERIAL PRIMARY KEY,
    credential_id INTEGER REFERENCES pilotpros.api_credentials(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    performed_by UUID REFERENCES pilotpros.users(id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_api_credentials_provider ON pilotpros.api_credentials(provider, environment, is_active);
CREATE INDEX idx_api_credentials_active ON pilotpros.api_credentials(is_active, is_validated);
CREATE INDEX idx_api_credentials_hash ON pilotpros.api_credentials(api_key_hash);

CREATE INDEX idx_api_credentials_audit_credential_id ON pilotpros.api_credentials_audit(credential_id);
CREATE INDEX idx_api_credentials_audit_timestamp ON pilotpros.api_credentials_audit(timestamp);

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE pilotpros.api_credentials TO pilotpros_user;
GRANT ALL PRIVILEGES ON TABLE pilotpros.api_credentials_audit TO pilotpros_user;
GRANT ALL PRIVILEGES ON SEQUENCE pilotpros.api_credentials_id_seq TO pilotpros_user;
GRANT ALL PRIVILEGES ON SEQUENCE pilotpros.api_credentials_audit_id_seq TO pilotpros_user;

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_api_credentials_updated_at
    BEFORE UPDATE ON pilotpros.api_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 🔄 INTEGRATION CON INTELLIGENCE ENGINE

### **Adattatore per Python**

```python
# intelligence-engine/app/services/api_vault_client.py

import requests
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class APIVaultClient:
    """
    Client for fetching API keys from Backend API Vault
    Fallback to environment variables if vault unavailable
    """

    def __init__(self):
        self.backend_url = os.getenv("BACKEND_URL", "http://backend-dev:3001")
        self.service_auth_token = os.getenv("SERVICE_AUTH_TOKEN")
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def get_api_key(self, provider: str, environment: str = "production") -> Optional[str]:
        """
        Get API key from vault with fallback to .env
        """
        cache_key = f"{provider}:{environment}"

        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                logger.debug(f"API key cache HIT for {provider}")
                return cached['value']

        # Try to fetch from vault
        try:
            response = requests.get(
                f"{self.backend_url}/api/vault/key/{provider}",
                headers={
                    "X-Service-Auth": self.service_auth_token
                },
                params={"environment": environment},
                timeout=2
            )

            if response.status_code == 200:
                data = response.json()
                api_key = data.get("api_key")

                # Update cache
                self.cache[cache_key] = {
                    'value': api_key,
                    'timestamp': time.time()
                }

                logger.info(f"✅ API key fetched from vault for {provider}")
                return api_key

        except Exception as e:
            logger.warning(f"⚠️ Vault fetch failed for {provider}: {e} - falling back to .env")

        # Fallback to environment variable
        env_key = f"{provider.upper()}_API_KEY"
        fallback_key = os.getenv(env_key)

        if fallback_key:
            logger.info(f"✅ Using fallback .env for {provider}")
            return fallback_key

        logger.error(f"❌ No API key found for {provider} (vault + .env failed)")
        return None

# Global instance
api_vault = APIVaultClient()

# Usage in graph.py
# OLD: api_key=os.getenv("OPENAI_API_KEY")
# NEW: api_key=api_vault.get_api_key("openai")
```

---

## 🚀 DEPLOYMENT PLAN (Updated with Critical Fixes)

### **Phase 0: Critical Security Fixes (Week 1) 🔴 MUST DO FIRST**

**CRITICAL FIX #1: Envelope Encryption** (3 giorni)
1. ⚠️ Implement DEK/KEK hierarchy in `encryption.service.js`
2. ⚠️ Add database columns: `dek_encrypted`, `dek_iv`, `dek_auth_tag`
3. ⚠️ Update all encrypt/decrypt functions
4. ⚠️ Test encryption cycle (DEK generation + master key encryption)
5. ⚠️ Migration script for existing encrypted data (if any)

**CRITICAL FIX #2: Counter-Based IV** (1 giorno)
1. ⚠️ Implement `SecureIVGenerator` class
2. ⚠️ Add database columns: `iv_counter`, `iv_random_prefix`, `rotation_threshold`
3. ⚠️ Replace `crypto.randomBytes(12)` with counter-based IV
4. ⚠️ Add auto-rotation trigger (when counter approaches 2^32)
5. ⚠️ Test IV uniqueness (no collisions)

**CRITICAL FIX #3: No .env Fallback in Production** (2 ore)
1. ⚠️ Update `api-vault.service.js` getApiKey() method
2. ⚠️ Throw error in production if vault unavailable (fail-safe)
3. ⚠️ Keep .env fallback ONLY for `NODE_ENV=development`
4. ⚠️ Update error messages with Admin UI link
5. ⚠️ Test production fail-safe behavior

**Phase 0 Total: 4 giorni** (BLOCCA Phase 1)

---

### **Phase 1: Database Setup (Week 2)**
1. ✅ Create migration `004_api_vault.sql` (with envelope encryption schema)
2. ✅ Add RLS (Row-Level Security) policies
3. ✅ Add `organization_id` column (multi-tenant isolation)
4. ✅ Add key rotation columns (`key_version`, `operations_count`, etc.)
5. ✅ Run migration in dev environment
6. ✅ Test table creation + constraints + RLS
7. ✅ Insert test encrypted credential manually

**Phase 1 Total: 2 giorni**

---

### **Phase 2: Backend Service (Week 3-4)**
1. ✅ Implement `encryption.service.js` (ENVELOPE encryption + counter IV)
2. ✅ Implement `SecureCache` class (Buffer-based, 5min TTL)
3. ✅ Implement `api-vault.service.js` (core logic)
4. ✅ Create API routes `/api/vault/*`
5. ✅ Add admin middleware protection
6. ✅ Implement auto-rotation scheduler (cron-based)
7. ✅ Add memory zeroing on cache eviction
8. ✅ Test encryption/decryption cycle (envelope + counter IV)
9. ✅ Test auto-refresh mechanism
10. ✅ Test auto-rotation (90 days OR 2^32 operations)

**Phase 2 Total: 6 giorni** (+1 giorno per auto-rotation)

---

### **Phase 3: Frontend UI (Week 5)**
1. ✅ Create `APIVaultSettings.vue` page
2. ✅ Implement credentials DataTable (with key version display)
3. ✅ Implement Add/Validate/Delete dialogs
4. ✅ Add "Test Connection" button (pre-validation)
5. ✅ Add audit history viewer (immutable log)
6. ✅ Add key rotation UI (manual trigger + schedule config)
7. ✅ Test all CRUD operations

**Phase 3 Total: 4 giorni**

---

### **Phase 4: Intelligence Engine Integration (Week 6)**
1. ✅ Implement `api_vault_client.py` (with NO .env fallback in prod)
2. ✅ Replace all `os.getenv()` calls in `graph.py`
3. ❌ ~~Test fallback to .env on vault failure~~ (REMOVED - fail-safe only)
4. ✅ Test production error handling (vault unavailable)
5. ✅ Verify zero-downtime key rotation
6. ✅ Test service-to-service authentication

**Phase 4 Total: 3 giorni**

---

### **Phase 5: Production Hardening (Week 7)**
1. ✅ Generate production master key (AWS Secrets Manager)
2. ✅ Add rate limiting to vault endpoints (100 req/min per IP)
3. ✅ Implement key rotation schedule (90 days default)
4. ✅ Add monitoring alerts (failed validations, counter threshold)
5. ✅ Add Prometheus metrics (vault_operations_total, vault_key_age_days)
6. ✅ Create admin onboarding docs
7. ✅ Setup Slack/email notifications (critical events)

**Phase 5 Total: 4 giorni**

---

### **Phase 6: Multi-Cliente Testing (Week 8)**
1. ✅ Setup 3 test environments (production/staging/test)
2. ✅ Test RLS isolation (tenant A cannot see tenant B keys)
3. ✅ Rotate keys for each environment (envelope encryption test)
4. ✅ Verify zero-downtime on live system
5. ✅ Load test (1000 req/min with vault + cache performance)
6. ✅ Security audit (penetration test + IV collision test)
7. ✅ Test counter-based IV (no collisions after 10M operations)

**Phase 6 Total: 4 giorni**

---

## 📊 REVISED ESTIMATED EFFORT

**Development (Post Research Update):**
- **Phase 0 (Critical Fixes)**: 4 giorni 🔴 **MUST DO FIRST**
- Database schema (updated): 2 giorni
- Backend service (envelope + auto-rotation): 6 giorni (+1 giorno)
- Frontend UI: 4 giorni
- Intelligence Engine integration: 3 giorni
- Testing + hardening: 4 giorni
- Multi-tenant testing: 4 giorni

**TOTAL: 27 giorni (~5.5 settimane)** (+9 giorni vs original estimate)

**CRITICAL PATH:**
1. Week 1: Phase 0 (Critical Fixes) - BLOCCA TUTTO
2. Week 2: Phase 1 (Database)
3. Week 3-4: Phase 2 (Backend)
4. Week 5: Phase 3 (Frontend)
5. Week 6: Phase 4 (Intelligence Engine)
6. Week 7: Phase 5 (Production Hardening)
7. Week 8: Phase 6 (Multi-Cliente Testing)

**Minimum Viable Product (MVP):**
- Week 1-4: Critical Fixes + Database + Backend = 12 giorni
- **Go-Live Gate**: Security audit MUST pass before production deployment

---

## ✅ SUCCESS CRITERIA

**Business Goals:**
- ✅ Cliente può cambiare API keys senza supporto tecnico
- ✅ Zero restart container su cambio chiavi
- ✅ Onboarding nuovo cliente < 10 minuti
- ✅ Audit trail completo (compliance GDPR/SOC2)

**Technical Goals:**
- ✅ API keys crittografate at-rest (AES-256-GCM)
- ✅ Auto-validation prima di attivare chiavi
- ✅ Cache performance < 5ms per key fetch
- ✅ Graceful fallback se DB down
- ✅ Zero API key leaks in logs/backups

**Security Goals:**
- ✅ Master key stored in AWS Secrets Manager (production)
- ✅ Row-level security (RLS) sul database
- ✅ Rate limiting su vault endpoints
- ✅ IP whitelisting per admin UI
- ✅ Penetration test passed

---

## 📊 ESTIMATED EFFORT

**Development:**
- Database schema: 2 giorni
- Backend service: 5 giorni
- Frontend UI: 4 giorni
- Intelligence Engine integration: 3 giorni
- Testing + hardening: 4 giorni

**TOTAL: 18 giorni (~4 settimane)**

**Team Required:**
- 1 Backend Developer (Node.js + PostgreSQL)
- 1 Frontend Developer (Vue 3 + PrimeVue)
- 1 DevOps Engineer (Docker + AWS Secrets)

---

## 🛡️ SECURITY CONSIDERATIONS

1. **Master Key Protection**:
   - Development: ENV variable (`.env` gitignored)
   - Production: AWS Secrets Manager with rotation
   - Kubernetes: Sealed Secrets

2. **Network Security**:
   - Vault endpoints only accessible from backend network
   - Service-to-service auth via shared secret
   - Admin UI behind VPN in production

3. **Audit & Compliance**:
   - Immutable audit log (append-only)
   - Weekly audit review (failed validations)
   - Quarterly key rotation policy

4. **Incident Response**:
   - Automatic deactivation on 3 failed validations
   - Slack/email alerts on suspicious activity
   - Rollback procedure (< 5 min RTO)

---

## 📚 ALTERNATIVE SOLUTIONS CONSIDERED

1. **HashiCorp Vault** ❌
   - PRO: Industry standard, battle-tested
   - CON: Complex setup, requires separate infra, overkill per use case

2. **AWS Secrets Manager** ❌
   - PRO: Cloud-native, auto-rotation
   - CON: Vendor lock-in, costs, latency (API calls)

3. **Encrypted Environment Variables** ❌
   - PRO: Simple, no DB dependency
   - CON: Requires container restart, no audit trail

4. **Custom PostgreSQL Solution** ✅ **WINNER**
   - PRO: Zero external dependencies, full control, audit trail included
   - PRO: Works on-premise + cloud, no vendor lock-in
   - PRO: Integration with existing auth system
   - CON: Custom implementation (but well-documented libraries exist)

---

## 📖 REFERENCES

- [Node.js Crypto Module](https://nodejs.org/api/crypto.html)
- [AES-256-GCM Best Practices](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)

---

**Document Owner**: PilotProOS Security Team
**Next Review**: After Phase 1 completion
**Status**: 🚧 READY FOR IMPLEMENTATION
