# 🔐 Security Fixes - TODO Next Session

**Branch**: `security`
**Session Date**: 2025-10-18
**Status**: 5/6 fix completati ✅
**Time Invested**: 9 ore
**Remaining**: 6 ore (Fix #2 only)

---

## ✅ Completati e Testati (9 ore)

- ✅ **Fix #3**: JWT_SECRET validation (1h) - CVSS 7.2
- ✅ **Fix #4**: Rate limiting /login (1h) - CVSS 4.1
- ✅ **Fix #5**: CORS lockdown (1h) - CVSS 5.3
- ✅ **Fix #6**: Token expiry verification (2h) - CVSS 5.8
- ✅ **Fix #1**: HttpOnly cookies (4h) - CVSS 8.1 🔐

**Testing**: Tutti i fix testati e funzionanti ✅

**Commits**:
```
7d36a0e0 fix(security): Migrate JWT to HttpOnly cookies (Fix #1)
92fd7b31 fix(security): Token expiry verification (Fix #6)
8cf328de fix(security): CORS lockdown (Fix #5)
85b4ea0c fix(security): Rate limiting (Fix #4)
1010b3fa fix(security): JWT_SECRET validation (Fix #3)
```

---

## ⏳ Da Completare (6 ore)

### **Fix #2 - Refresh Token Strategy** 🔴 P0 BLOCKER
**CVSS**: 6.5
**Effort**: 6 ore
**Complexity**: ALTA ⚠️

#### Modifiche Necessarie:

**1. Database Migration** (1h)
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
CREATE INDEX idx_user_active ON pilotpros.refresh_tokens(user_id, revoked_at)
  WHERE revoked_at IS NULL;
```

**2. Backend - Token Generation** (2h)
- `auth.controller.js`:
  * `/login`: Generate Access (30min) + Refresh (7 days)
  * Set 2 cookies: `access_token` + `refresh_token`
  * Store refresh token in PostgreSQL

**3. Backend - Refresh Endpoint** (2h)
- `auth.controller.js`:
  * `POST /api/auth/refresh`
  * Validate refresh token from cookie
  * Check DB (not revoked)
  * Generate new access token
  * Return new access_token cookie

**4. Frontend - Auto-Refresh** (1h)
- `auth.ts`:
  * Intercept 401 responses
  * Call `/api/auth/refresh` automatically
  * Retry original request
  * Logout if refresh fails

---

## 🚀 Quick Start Next Session

### Step 1: Resume Branch
```bash
cd /Volumes/BK12/Dropbox/Dropbox/TIZIANO/AI/PilotProOS
git status  # Should be on 'security' branch
git log --oneline -5  # Verify 5 commits present
```

### Step 2: Verify Stack Running
```bash
./stack-safe.sh status
# If stopped: ./stack-safe.sh start
```

### Step 3: Start Fix #2
```bash
# Create migration file
touch backend/db/migrations/005_refresh_tokens.sql

# Edit auth.controller.js for dual tokens
code backend/src/controllers/auth.controller.js
```

---

## 📋 Implementation Checklist Fix #2

**Database**:
- [ ] Create `005_refresh_tokens.sql` migration
- [ ] Run migration in Docker
- [ ] Verify table created

**Backend /login**:
- [ ] Generate refresh_token (crypto.randomBytes)
- [ ] Store in PostgreSQL with expiry
- [ ] Set 2 cookies: access_token (30min) + refresh_token (7d)
- [ ] Update response (backward compatible)

**Backend /refresh**:
- [ ] Create `POST /api/auth/refresh` endpoint
- [ ] Read refresh_token from cookie
- [ ] Validate against DB
- [ ] Check not revoked
- [ ] Generate new access_token
- [ ] Set new access_token cookie
- [ ] Return success

**Backend /logout**:
- [ ] Revoke refresh_token in DB (set revoked_at)
- [ ] Clear both cookies

**Frontend**:
- [ ] Add 401 interceptor in auth.ts
- [ ] Auto-call `/refresh` on 401
- [ ] Retry original request
- [ ] Logout if refresh fails (403)

**Testing**:
- [ ] Login → 2 cookies set
- [ ] Wait 31 min → access_token expired
- [ ] API call → Auto-refresh triggered
- [ ] New access_token received
- [ ] Logout → Both tokens revoked

---

## ⚠️ Gotchas & Warnings

1. **Migration**: Run INSIDE Docker container
   ```bash
   docker exec -it pilotpros-backend-dev sh
   psql $DATABASE_URL -f db/migrations/005_refresh_tokens.sql
   ```

2. **Token Generation**: Use `crypto.randomBytes(32).toString('hex')`
   - NOT jwt.sign for refresh tokens!

3. **Backward Compatibility**: Keep JSON token in response initially
   - Remove in Phase 2 (future)

4. **Race Conditions**: Handle concurrent refresh attempts
   - Use DB transaction + unique constraint

5. **Testing**: Clear localStorage before testing
   ```javascript
   localStorage.clear()
   ```

---

## 🎯 Success Criteria

- [ ] Access token: 30 minutes expiry
- [ ] Refresh token: 7 days expiry
- [ ] Auto-refresh funziona (transparente per user)
- [ ] Logout revoca entrambi i token
- [ ] Zero breaking changes per utenti esistenti
- [ ] Security score: 4.5/10 → 7.5/10 🔐

---

## 📊 Final Merge Strategy

**After Fix #2 completed**:
```bash
# Test completo
npm run test  # Backend
npm run type-check  # Frontend

# Merge in main
git checkout main
git merge security --no-ff -m "feat(security): Complete security hardening (Fixes #1-6)"

# Tag release
git tag -a v3.5.8-security -m "Security fixes: HttpOnly cookies, Refresh tokens, Rate limiting"

# Push
git push origin main --tags
```

---

## 📚 References

- **OWASP JWT Best Practices**: https://cheatsheetsecurity.com/html/cheatsheet/JWT_Security.html
- **RFC 6749 OAuth 2.0**: https://datatracker.ietf.org/doc/html/rfc6749#section-1.5
- **DEBITO-TECNICO.md**: Lines 59-94 (Refresh Token spec)

---

**Next Session Goal**: Complete Fix #2 (6h) → Merge to main → Production ready! 🚀
