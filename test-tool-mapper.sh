#!/bin/bash

# Tool Mapper Test Suite - Milhena v3.5.5
# Tests category → tool routing for all 9 categories

set -e

API_URL="http://localhost:8000/api/n8n/agent/customer-support"
BASE_SESSION_ID="test-tool-mapper-$(date +%s)"
CONTAINER="pilotpros-intelligence-engine-dev"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  🔧 TOOL MAPPER TEST SUITE"
echo "  Milhena v3.5.5 - Category → Tool Routing"
echo "=========================================="
echo ""
echo "📋 Testing 10 categories:"
echo "   1. PROCESS_LIST"
echo "   2. PROCESS_DETAIL"
echo "   3. EXECUTION_QUERY"
echo "   4. ERROR_ANALYSIS"
echo "   5. ANALYTICS"
echo "   6. STEP_DETAIL"
echo "   7. EMAIL_ACTIVITY"
echo "   8. PROCESS_ACTION"
echo "   9. SYSTEM_OVERVIEW"
echo "  10. CLARIFICATION_NEEDED"
echo ""
echo "=========================================="
echo ""

# Function to test a query
test_query() {
    local test_num=$1
    local category=$2
    local query=$3
    local expected_tool=$4

    # UNIQUE session_id per test!
    local SESSION_ID="${BASE_SESSION_ID}-test${test_num}"

    echo -e "${BLUE}Test $test_num: $category${NC}"
    echo "Query: \"$query\""
    echo "Session: $SESSION_ID"
    echo "Expected tool: $expected_tool"
    echo ""

    # Clear previous logs
    docker logs $CONTAINER --tail 0 > /dev/null 2>&1

    # Send query
    echo -n "Sending query... "
    response=$(curl -s -X POST $API_URL \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"$SESSION_ID\"}" \
        --max-time 30)

    if [ $? -ne 0 ]; then
        echo -e "${RED}FAILED${NC} (curl error)"
        echo ""
        return 1
    fi

    echo "✓"

    # Extract classification from logs
    sleep 1
    classification=$(docker logs $CONTAINER --tail 100 2>&1 | \
        grep -A 3 "CLASSIFICATION:" | \
        grep "category" | \
        tail -1 | \
        sed 's/.*category['\''": ]*\([A-Z_]*\).*/\1/')

    # Extract tool usage from logs
    tool_used=$(docker logs $CONTAINER --tail 100 2>&1 | \
        grep -E "(Calling tool|Tool called|usando tool)" | \
        tail -1)

    # Analyze response
    echo -n "Analyzing response... "

    # Check classification
    if echo "$classification" | grep -q "$category"; then
        echo -e "${GREEN}✓${NC} Category: $category"
    else
        echo -e "${YELLOW}⚠${NC} Category: $classification (expected $category)"
    fi

    # Check tool usage
    if [ -n "$tool_used" ]; then
        if echo "$tool_used" | grep -qi "$expected_tool"; then
            echo -e "${GREEN}✓${NC} Tool: $expected_tool"
        else
            echo -e "${YELLOW}⚠${NC} Tool: $(echo $tool_used | sed 's/.*tool: //' | awk '{print $1}')"
        fi
    else
        if [ "$expected_tool" = "direct_response" ]; then
            echo -e "${GREEN}✓${NC} Tool: direct_response (no tool call)"
        else
            echo -e "${RED}✗${NC} Tool: NONE (expected $expected_tool)"
        fi
    fi

    # Show response excerpt
    response_text=$(echo "$response" | jq -r '.response // .error // "N/A"' | head -c 100)
    echo "Response: ${response_text}..."

    echo ""
    echo "---"
    echo ""
}

# Test 1: PROCESS_LIST
test_query 1 "PROCESS_LIST" \
    "quali workflow abbiamo?" \
    "get_workflows_tool"

# Test 2: PROCESS_DETAIL
test_query 2 "PROCESS_DETAIL" \
    "dimmi tutto sul workflow Gestione Lead" \
    "smart_workflow_query_tool"

# Test 3: EXECUTION_QUERY
test_query 3 "EXECUTION_QUERY" \
    "quante esecuzioni ci sono state oggi?" \
    "smart_executions_query_tool"

# Test 4: ERROR_ANALYSIS
test_query 4 "ERROR_ANALYSIS" \
    "ci sono errori nel sistema?" \
    "get_error_details_tool"

# Test 5: ANALYTICS
test_query 5 "ANALYTICS" \
    "dammi le statistiche delle esecuzioni" \
    "smart_analytics_query_tool"

# Test 6: STEP_DETAIL
test_query 6 "STEP_DETAIL" \
    "mostrami gli step del workflow Fatturazione" \
    "get_node_execution_details_tool"

# Test 7: EMAIL_ACTIVITY
test_query 7 "EMAIL_ACTIVITY" \
    "quante email sono state processate oggi?" \
    "get_chatone_email_details_tool"

# Test 8: PROCESS_ACTION
test_query 8 "PROCESS_ACTION" \
    "attiva il workflow Gestione Lead" \
    "toggle_workflow_tool"

# Test 9: SYSTEM_OVERVIEW
test_query 9 "SYSTEM_OVERVIEW" \
    "come sta andando il sistema?" \
    "get_full_database_dump"

# Test 10: CLARIFICATION_NEEDED
test_query 10 "CLARIFICATION_NEEDED" \
    "quanti?" \
    "direct_response"

echo ""
echo "=========================================="
echo "  ✅ TEST SUITE COMPLETATO"
echo "=========================================="
echo ""
echo "📊 Risultati salvati in Docker logs"
echo "🔍 Per analisi dettagliata:"
echo "   docker logs $CONTAINER --tail 200"
echo ""
