# Hot-Reload Pattern System - Testing Guide

## 🎯 Overview

This document provides manual testing commands for the hot-reload pattern system implemented in v3.3.0.

**System**: Redis PubSub-based hot-reload for auto-learned patterns
**Goal**: Patterns available instantly (<100ms) without container restart
**Channel**: `pilotpros:patterns:reload`

---

## 🚀 Prerequisites

1. Stack running: `./stack-safe.sh start`
2. Intelligence Engine container active
3. Backend API available (port 3001)
4. Redis available (port 6379)

---

## 📋 Test Scenario 1: Manual DB Insert + Auto-Reload

### Step 1: Check Initial Pattern Count

```bash
# Connect to PostgreSQL
docker exec -it pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db

# Query existing patterns
SELECT COUNT(*) as total_patterns FROM pilotpros.auto_learned_patterns WHERE enabled = true;
SELECT normalized_pattern, category, confidence FROM pilotpros.auto_learned_patterns ORDER BY id DESC LIMIT 5;

# Exit psql
\q
```

### Step 2: Monitor Intelligence Engine Logs

```bash
# Open new terminal window
docker logs pilotpros-intelligence-engine-dev -f --tail 50
```

**Expected on startup**:
```
[AUTO-LEARN] asyncpg connection pool created (min=2, max=10)
[AUTO-LEARN] Loaded 64 patterns from database
[HOT-RELOAD] Subscribed to Redis channel: pilotpros:patterns:reload
[HOT-RELOAD] Background subscriber task started
```

### Step 3: Insert New Test Pattern

```bash
# Insert test pattern with high confidence
docker exec -it pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "
INSERT INTO pilotpros.auto_learned_patterns
(pattern, normalized_pattern, category, confidence, created_by, enabled)
VALUES
('test pattern hot reload?', 'test pattern hot reload', 'WORKFLOW_QUERY', 0.95, 'manual', true)
RETURNING id, normalized_pattern, category;
"
```

**Expected output**:
```
 id  | normalized_pattern        | category
-----+---------------------------+----------------
 123 | test pattern hot reload   | WORKFLOW_QUERY
```

### Step 4: Trigger Manual Reload via Backend API

```bash
# Trigger reload (replace pattern_id with ID from Step 3)
curl -X POST http://localhost:3001/api/milhena/patterns/reload \
  -H "Content-Type: application/json" \
  -d '{"pattern_id": 123}'
```

**Expected response**:
```json
{
  "success": true,
  "message": "Pattern reload triggered successfully",
  "subscribers": 1,
  "pattern_id": 123
}
```

**Expected in Intelligence Engine logs** (check terminal from Step 2):
```
[HOT-RELOAD] Received message: action=reload, pattern_id=123
[AUTO-LEARN] Loaded 65 patterns from database
[HOT-RELOAD] Pattern reload complete in 45.23ms (total_reloads=1)
```

### Step 5: Verify Pattern Match WITHOUT Restart

```bash
# Test the new pattern
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "test pattern hot reload", "session_id": "test-hot-reload"}'
```

**Expected in Intelligence Engine logs**:
```
[AUTO-LEARNED-MATCH] 'test pattern hot reload' → WORKFLOW_QUERY (accuracy=0.00)
[FAST-PATH] Instant match: WORKFLOW_QUERY (bypassed LLM)
```

✅ **SUCCESS CRITERIA**: Pattern matched without container restart!

---

## 📋 Test Scenario 2: Auto-Learning Triggers Reload

### Step 1: Clear Previous Test Pattern

```bash
docker exec -it pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "
DELETE FROM pilotpros.auto_learned_patterns WHERE pattern = 'test pattern hot reload?';
"
```

### Step 2: Monitor Logs

```bash
docker logs pilotpros-intelligence-engine-dev -f --tail 50
```

### Step 3: Send High-Confidence Query (triggers auto-learning)

```bash
# Send query that will trigger auto-learning (>0.9 confidence)
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quali sono gli ultimi workflow attivi?", "session_id": "test-auto-learn"}'
```

**Expected in logs** (if confidence >0.9):
```
[AUTO-LEARN] New pattern saved: 'ultimi workflow attivi' → WORKFLOW_QUERY (confidence=0.92, id=124)
[AUTO-LEARN] Loaded 65 patterns from database
[HOT-RELOAD] Published reload message to 1 subscriber(s)
[HOT-RELOAD] Received message: action=reload, pattern_id=124
[HOT-RELOAD] Pattern reload complete in 38.91ms (total_reloads=1)
```

### Step 4: Verify Pattern Now Available

```bash
# Test the same query again (should hit fast-path now)
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quali sono gli ultimi workflow attivi?", "session_id": "test-auto-learn-2"}'
```

**Expected in logs**:
```
[AUTO-LEARNED-MATCH] 'ultimi workflow attivi' → WORKFLOW_QUERY (accuracy=0.00)
[FAST-PATH] Instant match: WORKFLOW_QUERY (bypassed LLM)
```

✅ **SUCCESS CRITERIA**: Auto-learned pattern immediately available!

---

## 📋 Test Scenario 3: Graceful Shutdown

### Step 1: Restart Intelligence Engine

```bash
docker restart pilotpros-intelligence-engine-dev
```

### Step 2: Monitor Logs

```bash
docker logs pilotpros-intelligence-engine-dev -f --tail 50
```

**Expected shutdown sequence**:
```
🔄 Shutting down Intelligence Engine...
[HOT-RELOAD] Initiating graceful shutdown...
[HOT-RELOAD] Subscriber loop exited
[HOT-RELOAD] Subscriber task stopped
[HOT-RELOAD] Shutdown complete
✅ Hot-reload pattern system stopped gracefully
✅ AsyncRedisSaver closed gracefully
```

**Expected startup sequence**:
```
🚀 Starting Intelligence Engine...
[AUTO-LEARN] asyncpg connection pool created (min=2, max=10)
[AUTO-LEARN] Loaded 65 patterns from database
[HOT-RELOAD] Subscribed to Redis channel: pilotpros:patterns:reload
[HOT-RELOAD] Background subscriber task started
✅ Hot-reload pattern system started (Redis PubSub subscriber)
✅ Intelligence Engine ready!
```

✅ **SUCCESS CRITERIA**: Clean shutdown + startup with no errors

---

## 📋 Test Scenario 4: Performance Verification

### Step 1: Measure Reload Latency

```bash
# Trigger reload and measure time
time curl -X POST http://localhost:3001/api/milhena/patterns/reload \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected**:
- HTTP response: <500ms
- Reload latency (from logs): <100ms

### Step 2: Check Pattern Match Latency

```bash
# Test fast-path latency
time curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "test pattern hot reload", "session_id": "perf-test"}'
```

**Expected**:
- Total response: <2s
- Fast-path match: <10ms (check logs)

---

## 📋 Test Scenario 5: Error Handling

### Step 1: Redis Disconnect Simulation

```bash
# Stop Redis temporarily
docker pause pilotpros-redis-dev

# Check Intelligence Engine logs
docker logs pilotpros-intelligence-engine-dev -f --tail 20
```

**Expected**:
```
[HOT-RELOAD] Redis connection lost: ConnectionError, reconnecting (attempt 1/5)...
[HOT-RELOAD] Subscribed to Redis channel: pilotpros:patterns:reload
[HOT-RELOAD] Background subscriber task started
```

### Step 2: Resume Redis

```bash
# Resume Redis
docker unpause pilotpros-redis-dev
```

**Expected**:
```
[HOT-RELOAD] Reconnection successful after 1 attempt(s)
```

✅ **SUCCESS CRITERIA**: Auto-reconnect with exponential backoff

---

## 🔍 Debugging Commands

### Check Redis PubSub Subscribers

```bash
# Connect to Redis CLI
docker exec -it pilotpros-redis-dev redis-cli

# Check active subscribers
PUBSUB CHANNELS pilotpros:patterns:*
# Expected: pilotpros:patterns:reload

# Check subscriber count
PUBSUB NUMSUB pilotpros:patterns:reload
# Expected: pilotpros:patterns:reload 1

# Subscribe manually (for debugging)
SUBSCRIBE pilotpros:patterns:reload
# Then trigger reload via API to see messages
```

### Check Pattern Reloader Metrics

```bash
# Add endpoint to FastAPI (optional future enhancement)
curl http://localhost:8000/api/milhena/hot-reload/metrics
```

**Expected response** (future enhancement):
```json
{
  "total_reloads": 5,
  "failed_reloads": 0,
  "last_reload_time": 1707234567.89,
  "subscriber_active": true
}
```

---

## 🎯 Success Criteria Summary

- ✅ Patterns reload in <100ms
- ✅ No container restart required
- ✅ Redis PubSub message received
- ✅ Pattern match works immediately after reload
- ✅ Auto-learning triggers reload automatically
- ✅ Graceful shutdown (no hanging tasks)
- ✅ Auto-reconnect on Redis disconnect
- ✅ Thread-safe pattern map updates (concurrent queries work)

---

## 🐛 Common Issues

### Issue 1: "No subscribers found"

**Symptom**: `"subscribers": 0` in API response

**Cause**: Intelligence Engine not subscribed to channel

**Fix**: Check Intelligence Engine startup logs for subscription confirmation

### Issue 2: Pattern not matching after reload

**Symptom**: Query still hits LLM instead of fast-path

**Cause**: Query normalization mismatch

**Debug**:
```bash
# Check normalized pattern in DB
docker exec -it pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "
SELECT pattern, normalized_pattern FROM pilotpros.auto_learned_patterns WHERE id = 123;
"

# Test normalization manually (Python)
docker exec -it pilotpros-intelligence-engine-dev python -c "
query = 'test pattern hot reload?'
import string
words = query.lower().strip().split()
words = [w.strip(string.punctuation) for w in words]
normalized = ' '.join(words).rstrip('?!.')
print(f'Normalized: {normalized}')
"
```

### Issue 3: Reload latency >100ms

**Symptom**: `[HOT-RELOAD] Pattern reload complete in 250.00ms`

**Cause**: Database query slow (network latency, index missing)

**Debug**:
```sql
-- Check query performance
EXPLAIN ANALYZE
SELECT normalized_pattern, category, confidence, accuracy, times_used
FROM pilotpros.auto_learned_patterns
WHERE enabled = TRUE
ORDER BY accuracy DESC, times_used DESC;
```

---

## 📚 Related Documentation

- **Implementation**: `/intelligence-engine/app/milhena/hot_reload.py`
- **Integration**: `/intelligence-engine/app/main.py` (lines 117-126, 145-151)
- **Graph Integration**: `/intelligence-engine/app/milhena/graph.py` (lines 1944-1967, 2036-2039)
- **Backend Endpoint**: `/backend/src/routes/milhena.routes.js` (lines 171-226)
- **Database Schema**: `/backend/db/migrations/004_auto_learned_patterns.sql`

---

**Last Updated**: 2025-10-11
**Version**: v3.3.0 Hot-Reload System
**Author**: Claude Code (AI Assistant)
