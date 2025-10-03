#!/bin/bash
# debug-milhena.sh - Complete Milhena debugging script
# Usage: ./debug-milhena.sh

set -e

echo "🔍 MILHENA DEBUG SESSION"
echo "=================================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Check container health
echo -e "\n${YELLOW}1️⃣ Container Health Check${NC}"
echo "-----------------------------------"
if docker ps | grep -q intelligence-engine; then
    echo -e "${GREEN}✓${NC} Intelligence Engine container is running"
    docker ps | grep intelligence-engine | awk '{print "  Status: " $7 " " $8}'
else
    echo -e "${RED}✗${NC} Intelligence Engine container NOT running"
    exit 1
fi

# 2. Health endpoint
echo -e "\n${YELLOW}2️⃣ Health Endpoint Test${NC}"
echo "-----------------------------------"
HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
if echo "$HEALTH" | grep -q "healthy\|ok"; then
    echo -e "${GREEN}✓${NC} Health endpoint OK"
    echo "$HEALTH" | jq '.' 2>/dev/null || echo "$HEALTH"
else
    echo -e "${RED}✗${NC} Health endpoint FAILED"
    echo "$HEALTH"
fi

# 3. Test query with real data
echo -e "\n${YELLOW}3️⃣ Test Query: 'Quanti workflow in errore abbiamo?'${NC}"
echo "-----------------------------------"
TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quanti workflow in errore abbiamo?", "session_id": "debug-'$(date +%s)'"}' \
  2>/dev/null || echo '{"error": "Request failed"}')

if echo "$TEST_RESPONSE" | jq -e '.response' >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Query executed successfully"
    echo ""
    echo "Response:"
    echo "$TEST_RESPONSE" | jq -r '.response' | head -20
    echo ""
    echo "Metadata:"
    echo "$TEST_RESPONSE" | jq '{tool_used, execution_time_ms, model_used, cost}'
else
    echo -e "${RED}✗${NC} Query FAILED"
    echo "$TEST_RESPONSE"
fi

# 4. Business masking verification
echo -e "\n${YELLOW}4️⃣ Business Masking Verification${NC}"
echo "-----------------------------------"
LEAKED_TERMS=$(echo "$TEST_RESPONSE" | jq -r '.response' | grep -iE "(workflow|error|execution|node|webhook)" || echo "")
if [ -z "$LEAKED_TERMS" ]; then
    echo -e "${GREEN}✓${NC} No technical leaks detected"
    echo "  All technical terms properly masked"
else
    echo -e "${RED}✗${NC} Technical leaks detected:"
    echo "$LEAKED_TERMS" | head -5
fi

# 5. Database connectivity
echo -e "\n${YELLOW}5️⃣ Database Connectivity Check${NC}"
echo "-----------------------------------"
DB_CHECK=$(docker exec pilotpros-postgres-dev psql -U n8n -d pilotpros -t -c "
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as errors,
    SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success
FROM n8n.execution_entity
WHERE \"startedAt\" >= NOW() - INTERVAL '7 days';
" 2>/dev/null || echo "FAILED")

if [ "$DB_CHECK" != "FAILED" ]; then
    echo -e "${GREEN}✓${NC} Database connection OK"
    echo "$DB_CHECK" | awk '{print "  Total executions (7d): " $1 "\n  Errors: " $2 "\n  Success: " $3}'
else
    echo -e "${RED}✗${NC} Database connection FAILED"
fi

# 6. Recent logs
echo -e "\n${YELLOW}6️⃣ Recent Logs (last 20 lines)${NC}"
echo "-----------------------------------"
docker logs pilotpros-intelligence-engine-dev --tail 20 2>&1 | grep -v "GET /health" | tail -20

# 7. Prometheus metrics
echo -e "\n${YELLOW}7️⃣ Prometheus Metrics${NC}"
echo "-----------------------------------"
METRICS=$(curl -s http://localhost:8000/metrics 2>/dev/null | grep "^pilotpros_agent" | head -10 || echo "FAILED")
if [ "$METRICS" != "FAILED" ]; then
    echo -e "${GREEN}✓${NC} Metrics endpoint OK"
    echo "$METRICS"
else
    echo -e "${RED}✗${NC} Metrics endpoint FAILED"
fi

# 8. LangSmith trace check
echo -e "\n${YELLOW}8️⃣ LangSmith Configuration${NC}"
echo "-----------------------------------"
LANGCHAIN_CONFIG=$(docker exec pilotpros-intelligence-engine-dev env | grep LANGCHAIN || echo "NOT_CONFIGURED")
if echo "$LANGCHAIN_CONFIG" | grep -q "LANGCHAIN_TRACING_V2=true"; then
    echo -e "${GREEN}✓${NC} LangSmith tracing enabled"
    echo "$LANGCHAIN_CONFIG" | grep LANGCHAIN_PROJECT
else
    echo -e "${YELLOW}⚠${NC} LangSmith tracing not configured"
fi

# Summary
echo -e "\n${GREEN}=================================================="
echo "✅ Debug session complete!"
echo "==================================================${NC}"
echo ""
echo "Next steps:"
echo "  - View full logs: docker logs pilotpros-intelligence-engine-dev -f"
echo "  - LangSmith traces: https://smith.langchain.com"
echo "  - Metrics: http://localhost:8000/metrics"
echo ""
