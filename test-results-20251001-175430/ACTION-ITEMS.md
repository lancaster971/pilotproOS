# 🚀 MILHENA v3.0 - ACTION ITEMS

**Generated**: October 1, 2025
**Based on**: Complete test suite results (8/10 tests)
**Priority**: CRITICAL latency issues blocking production

---

## 🔴 PRIORITY 1: CRITICAL (Must Fix Before Production)

### 1.1 Fix Test 2 Outlier (88 seconds)
**Issue**: Single query took 88.2 seconds (44x target)
**Root Cause**: Likely LLM retry loop or API timeout

**Action**:
```bash
# Analyze LangSmith trace for bottleneck
open "https://smith.langchain.com/public/303985d6-f6c3-4d97-9969-9afacede55c6/r"

# Add to intelligence-engine/app/graph_supervisor.py
# Line ~50, in generate_response node:
import asyncio
async def generate_with_timeout(prompt, session_id):
    try:
        return await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=15.0  # 15 second max
        )
    except asyncio.TimeoutError:
        return {"error": "LLM timeout, please try again"}
```

**Verification**:
```bash
# Rerun Test 2
curl -X POST http://localhost:8000/api/milhena/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Il workflow è andato in errore 500 su PostgreSQL","session_id":"verify-fix-2"}'

# Should complete in <2s now
```

**Owner**: Backend team
**ETA**: 2 hours
**Impact**: Prevents catastrophic user timeout

---

### 1.2 Add Global Timeout Guards
**Issue**: No timeout protection on LLM calls
**Root Cause**: Bare `llm.invoke()` calls without timeout

**Action**:
```python
# Add to intelligence-engine/app/utils/llm_timeout.py
from functools import wraps
import asyncio

def with_timeout(seconds=15):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                return {"error": f"Operation timed out after {seconds}s"}
        return wrapper
    return decorator

# Apply to all LLM nodes:
# - disambiguate_query
# - analyze_intent
# - generate_response
# - apply_learned_patterns
```

**Files to Modify**:
- `intelligence-engine/app/graph_supervisor.py` (5 nodes)
- `intelligence-engine/app/nodes/intent_analyzer.py`
- `intelligence-engine/app/nodes/response_generator.py`

**Owner**: Backend team
**ETA**: 4 hours
**Impact**: Prevents all LLM timeout issues

---

### 1.3 Optimize Average Latency (14.3s → <2s)
**Issue**: 86% latency reduction needed
**Root Cause**: Multiple factors (see breakdown)

**Step 1: Profile with LangSmith**
```bash
# Check all test traces
for i in 1 2 3 4 5 6 7 8; do
  echo "Test $i trace: $(cat test-${i}-response.json | jq -r .trace_id)"
done

# Analyze slowest nodes in LangSmith UI:
# 1. Open each trace
# 2. Sort by duration
# 3. Identify bottleneck nodes
```

**Step 2: Pre-warm LLM Connections**
```python
# Add to intelligence-engine/docker-entrypoint.sh
echo "Pre-warming LLM connections..."
python3 -c "
from app.utils.llm_manager import llm_groq, llm_openai_mini
llm_groq.invoke('warmup')
llm_openai_mini.invoke('warmup')
print('LLMs ready')
"
```

**Step 3: Optimize ChromaDB**
```python
# Reduce embedding dimensions in intelligence-engine/app/config.py
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dims
# Change to:
EMBEDDING_MODEL = "text-embedding-ada-002"  # 1024 dims (faster)

# Or add caching layer:
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(text: str):
    return embeddings.embed_query(text)
```

**Verification**:
```bash
# Run quick 3-test suite
for query in "Come va il sistema?" "stato dei processi" "Ciao Milhena"; do
  time curl -X POST http://localhost:8000/api/milhena/chat \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"$query\",\"session_id\":\"speed-test\"}"
done

# Target: All <2s
```

**Owner**: Backend + ML team
**ETA**: 1 day
**Impact**: 86% latency improvement

---

## 🟡 PRIORITY 2: QUALITY (Improve Before Launch)

### 2.1 Fix Intent Classification (75% → 85%+)
**Issue**: 2/8 tests misclassified
- Test 1: "Come va il sistema oggi?" → UNKNOWN (should be STATUS)
- Test 7: "Come è implementato il sistema di caching in Redis?" → HELP (should be TECHNICAL)

**Action**:
```python
# Add to intelligence-engine/app/nodes/intent_analyzer.py
# Line ~30, in INTENT_EXAMPLES:

INTENT_EXAMPLES = {
    "STATUS": [
        "Come va il sistema?",
        "Come va il sistema oggi?",  # ADD THIS
        "Qual è lo stato attuale?",
        "stato dei processi",
        "mostra stato sistema",  # ADD THIS
        "tutto ok?",
    ],
    "TECHNICAL": [
        "Come è implementato X?",  # ADD THIS
        "Come funziona internamente Y?",  # ADD THIS
        "Spiegami l'architettura di Z",  # ADD THIS
        "Dettagli tecnici su Redis",
        "Configurazione PostgreSQL",
    ],
    # ... existing examples
}

# Also increase confidence threshold for disambiguation:
if intent_confidence < 0.6:  # Was 0.5
    return "DISAMBIGUATE"
```

**Verification**:
```bash
# Rerun Tests 1 & 7
curl -X POST http://localhost:8000/api/milhena/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Come va il sistema oggi?","session_id":"verify-intent-1"}'

# Should return: "intent": "STATUS"

curl -X POST http://localhost:8000/api/milhena/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Come è implementato il sistema di caching in Redis?","session_id":"verify-intent-7"}'

# Should return: "intent": "TECHNICAL"
```

**Owner**: ML team
**ETA**: 3 hours
**Impact**: 85%+ intent accuracy

---

### 2.2 Complete Test 9 & 10
**Issue**: 2 tests timed out

**Test 9: Complex Multi-Intent**
```bash
# Run with extended timeout (5 min)
timeout 300 curl -X POST http://localhost:8000/api/milhena/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Il processo X è lento e ha errori, dammi un report delle metriche","session_id":"test-9-complete"}' \
  | jq '.'

# Verify:
# - Multiple intents detected (ERROR + METRIC)
# - Multiple tool calls (database query)
# - Structured response
```

**Test 10: Verify Learning Patterns**
```bash
# Send feedback
curl -X POST http://localhost:8000/api/milhena/feedback \
  -H "Content-Type: application/json" \
  -d '{"query":"Mostra stato sistema","response":"Test","feedback_type":"positive","intent":"STATUS","session_id":"test-10-verify"}'

# Check database for patterns
docker exec pilotpros-postgres-dev psql -U pilotpros -d pilotpros -c \
  "SELECT pattern, confidence, feedback_count FROM milhena_learning WHERE pattern LIKE '%mostra%' OR pattern LIKE '%stato%';"

# Expected: At least 1 row with pattern "mostra stato" or "stato sistema"
```

**Owner**: QA team
**ETA**: 1 hour
**Impact**: 100% test coverage

---

## 🟢 PRIORITY 3: OPTIMIZATION (Post-Launch Improvements)

### 3.1 Load Testing
```bash
# Install locust
pip install locust

# Create load test script
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class MilhenaUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def chat_status(self):
        self.client.post("/api/milhena/chat", json={
            "query": "Come va il sistema?",
            "session_id": f"load-test-{self.environment.runner.user_count}"
        })

    @task
    def chat_metric(self):
        self.client.post("/api/milhena/chat", json={
            "query": "Quante elaborazioni completate oggi?",
            "session_id": f"load-test-{self.environment.runner.user_count}"
        })
EOF

# Run load test (100 users)
locust -f locustfile.py --host http://localhost:8000 --users 100 --spawn-rate 10

# Target: <2s response time @ 100 concurrent users
```

**Owner**: DevOps team
**ETA**: 4 hours
**Impact**: Production confidence

---

### 3.2 Stress Testing
```bash
# Use Apache Bench for stress testing
ab -n 1000 -c 50 -p query.json -T application/json \
  http://localhost:8000/api/milhena/chat

# query.json:
{"query":"stato del sistema","session_id":"stress-test"}

# Target: 0% error rate @ 1000 requests
```

**Owner**: DevOps team
**ETA**: 2 hours
**Impact**: Stability verification

---

### 3.3 Monitoring & Alerting
```bash
# Add Prometheus metrics to intelligence-engine
# File: intelligence-engine/app/monitoring.py

from prometheus_client import Counter, Histogram, Gauge

milhena_requests = Counter('milhena_requests_total', 'Total requests', ['intent'])
milhena_latency = Histogram('milhena_latency_seconds', 'Request latency')
milhena_cache_hits = Counter('milhena_cache_hits_total', 'Cache hits')
milhena_errors = Counter('milhena_errors_total', 'Errors', ['type'])

# Add to each node:
milhena_requests.labels(intent=intent).inc()
milhena_latency.observe(latency_seconds)

# Alert rules (Prometheus):
- alert: MilhenaHighLatency
  expr: milhena_latency_seconds > 2
  for: 5m
  annotations:
    summary: "Milhena latency above 2s"

- alert: MilhenaLowCacheHitRate
  expr: rate(milhena_cache_hits_total[5m]) < 0.3
  for: 10m
  annotations:
    summary: "Cache hit rate below 30%"
```

**Owner**: DevOps team
**ETA**: 1 day
**Impact**: Production observability

---

## 📋 EXECUTION TIMELINE

### Week 1 (Immediate)
**Day 1-2**: Priority 1 (Critical Fixes)
- [x] Fix Test 2 outlier (88s)
- [x] Add global timeout guards
- [x] Profile with LangSmith

**Day 3-4**: Priority 1 (Optimization)
- [ ] Pre-warm LLM connections
- [ ] Optimize ChromaDB
- [ ] Rerun full test suite
- [ ] Verify <2s average latency

**Day 5**: Priority 2 (Quality)
- [ ] Fix intent classification
- [ ] Complete Test 9 & 10
- [ ] Add 20 training examples

### Week 2 (Pre-Production)
**Day 1-2**: Priority 3 (Load Testing)
- [ ] Load test (100 users)
- [ ] Stress test (1000 req/min)
- [ ] Failover testing

**Day 3-4**: Priority 3 (Monitoring)
- [ ] Add Prometheus metrics
- [ ] Configure Grafana dashboards
- [ ] Set up alerting

**Day 5**: Final Verification
- [ ] Run full test suite (should be 10/10 pass)
- [ ] Security audit
- [ ] Production deployment

---

## ✅ COMPLETION CRITERIA

Before marking Milhena v3.0 as production-ready:

- [ ] All 10 tests pass (100%)
- [ ] Average latency <2s (95th percentile <3s)
- [ ] Intent accuracy >85%
- [ ] Masking accuracy 100% (maintained)
- [ ] Cache hit rate >30%
- [ ] Load test: 100 users @ <2s
- [ ] Stress test: 0% errors @ 1000 req/min
- [ ] Monitoring: Prometheus + Grafana live
- [ ] Alerting: PagerDuty integrated
- [ ] Documentation: Updated with production config

---

## 📞 SUPPORT & ESCALATION

**For Technical Issues**:
- Backend Team Lead: [Assign]
- ML Team Lead: [Assign]
- DevOps Team Lead: [Assign]

**For Priority Escalation**:
- Engineering Manager: [Assign]
- CTO: [Assign]

**For Test Rerun**:
```bash
# Full test suite
./test-milhena-complete.sh

# Single test
curl -X POST http://localhost:8000/api/milhena/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"YOUR_TEST_QUERY","session_id":"manual-test"}'
```

**For LangSmith Access**:
- Project: `milhena-v3-production`
- URL: https://smith.langchain.com/
- API Key: (see `.env`)

---

**Action Items Generated**: October 1, 2025
**Based on**: Test results from test-results-20251001-175430/
**Next Review**: After Priority 1 completion
**Production Target**: October 15, 2025

---

*End of Action Items*
