#!/bin/bash
# Test completo TUTTE le 33 API Frontend PilotProOS
# Dopo migrazione SQLite → PostgreSQL

BASE_URL="http://localhost:3001"
FRONTEND_USER="tiziano@gmail.com"
FRONTEND_PASS="Hamlet@108"

echo "======================================================================"
echo "🧪 TEST FRONTEND APIs - PilotProOS Post-Migrazione"
echo "======================================================================"
echo ""

# Step 1: Login e ottieni JWT token
echo "🔐 [1/34] POST /api/auth/login"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$FRONTEND_USER\", \"password\": \"$FRONTEND_PASS\"}" \
  --max-time 10)

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "" ]; then
  echo "❌ Login fallito! Response:"
  echo "$LOGIN_RESPONSE"
  echo ""
  echo "⚠️  Continuo con test API pubbliche..."
  AUTH_HEADER=""
else
  echo "✅ Login OK - Token: ${TOKEN:0:20}..."
  AUTH_HEADER="Authorization: Bearer $TOKEN"
fi

echo ""

# Function per testare API
test_api() {
  local num=$1
  local method=$2
  local endpoint=$3
  local desc=$4

  echo "📡 [$num/34] $method $endpoint"
  echo "   Descrizione: $desc"

  RESPONSE=$(curl -s -X "$method" "$BASE_URL$endpoint" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    --max-time 10 2>&1)

  # Check se è JSON valido
  IS_JSON=$(echo "$RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin); print('OK')" 2>/dev/null)

  if [ "$IS_JSON" == "OK" ]; then
    # Extract summary
    SUMMARY=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if isinstance(d, dict):
        if 'data' in d:
            if isinstance(d['data'], list):
                print(f\"✅ data: {len(d['data'])} items\")
            else:
                print(f\"✅ data: {type(d['data']).__name__}\")
        elif 'success' in d:
            print(f\"✅ success: {d['success']}\")
        else:
            print(f\"✅ keys: {', '.join(list(d.keys())[:5])}\")
    else:
        print(f\"✅ type: {type(d).__name__}\")
except:
    print('❌ JSON parse error')
" 2>/dev/null)
    echo "   $SUMMARY"
  else
    # Check se è errore HTTP
    if echo "$RESPONSE" | grep -q "Authentication required"; then
      echo "   ⚠️  Auth required (expected if no login)"
    elif echo "$RESPONSE" | grep -q "404\|Not Found"; then
      echo "   ❌ 404 Not Found"
    elif echo "$RESPONSE" | grep -q "500\|Internal Server Error"; then
      echo "   ❌ 500 Internal Server Error"
    else
      echo "   ⚠️  Non-JSON response: ${RESPONSE:0:80}"
    fi
  fi

  echo ""
}

# TEST BUSINESS API (28 endpoints)
test_api 2 GET "/api/business/processes" "Lista workflow (business terminology)"
test_api 3 GET "/api/business/process-runs" "Process runs (executions)"
test_api 4 GET "/api/business/executions" "Executions list"
test_api 5 GET "/api/business/analytics" "Analytics dashboard data"
test_api 6 GET "/api/business/automation-insights" "Automation insights"
test_api 7 GET "/api/business/statistics" "Statistics"
test_api 8 GET "/api/business/integration-health" "Integration health"
test_api 9 GET "/api/business/top-performers" "Top performing workflows"
test_api 10 GET "/api/business/hourly-analytics" "Hourly analytics"
test_api 11 GET "/api/business/daily-trend" "Daily trend (30 days)"
test_api 12 GET "/api/business/live-events" "Live events stream"
test_api 13 GET "/api/business/workflow-cards" "Workflow cards overview"

# TEST AUTH API (2 endpoints - già testato login)
test_api 14 GET "/api/auth/profile" "User profile"
test_api 15 POST "/api/auth/logout" "Logout"

# TEST SYSTEM API
test_api 16 GET "/health" "System health"
test_api 17 GET "/api/system/compatibility" "Compatibility info"

# TEST AI/AGENT API
test_api 18 GET "/api/milhena/stats" "Milhena AI stats"
test_api 19 GET "/api/milhena/performance" "Milhena performance metrics"

# TEST RAG API
test_api 20 GET "/api/rag/stats" "RAG knowledge base stats"
test_api 21 GET "/api/rag/documents" "RAG documents list"

# TEST SECURITY API
test_api 22 GET "/api/security/logs" "Security logs"
test_api 23 GET "/api/security/metrics" "Security metrics"
test_api 24 GET "/api/security/api-keys" "API keys list"

# TEST DATABASE API
test_api 25 GET "/api/database/stats" "Database stats"
test_api 26 GET "/api/database/tables" "Database tables"
test_api 27 GET "/api/database/activity" "Database activity"

# TEST SCHEDULER API
test_api 28 GET "/api/scheduler/status" "Scheduler status"
test_api 29 GET "/api/scheduler/logs" "Scheduler logs"

# TEST ALERTS API
test_api 30 GET "/api/alerts" "Alerts list"
test_api 31 GET "/api/alerts/metrics" "Alerts metrics"

# TEST BACKUP API
test_api 32 GET "/api/backup/list" "Backup files list"
test_api 33 GET "/api/backup-settings" "Backup settings"

# TEST AGENT ENGINE
test_api 34 GET "/api/agent-engine/health" "Agent engine health"

echo "======================================================================"
echo "📊 TEST COMPLETATO"
echo "======================================================================"
echo ""
echo "Total API tested: 34"
echo "Check output above for ✅/❌/⚠️ status"
echo ""
