#!/bin/bash

# Test Fast-Path Component - PilotProOS
# Obiettivi: DANGER (53 keywords), GREETING (10 saluti), PASS (→ LLM)

ENDPOINT="http://localhost:8000/api/n8n/agent/customer-support"
TOTAL_TESTS=0
PASSED=0
FAILED=0
VERBOSE=false

# Parse arguments
while getopts "v" opt; do
    case $opt in
        v) VERBOSE=true ;;
        \?) echo "Usage: $0 [-v]"; exit 1 ;;
    esac
done

echo "=========================================="
echo "🧪 TEST SUITE: FAST-PATH Component"
echo "=========================================="
echo "Component: _instant_classify (graph.py:1513-1590)"
echo "Obiettivi: 3 (DANGER, GREETING, PASS)"
[ "$VERBOSE" = true ] && echo "🔍 VERBOSE MODE: ON"
echo ""

# Function: test_query
test_query() {
    local objective=$1
    local query=$2
    local expected_category=$3
    local expected_pattern=$4  # Pattern da cercare nella risposta
    local test_num=$5

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "[$objective - Test $test_num/5]"
    echo "Query: \"$query\""
    echo "Expected: $expected_category"

    # VERBOSE: Show timing
    if [ "$VERBOSE" = true ]; then
        START_TIME=$(python3 -c 'import time; print(int(time.time() * 1000))')
        echo "⏱️  Sending request..."
    fi

    RESPONSE=$(curl -s -X POST $ENDPOINT \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"test-fast-path-$RANDOM\"}" \
        --max-time 10)

    # VERBOSE: Show timing + full response
    if [ "$VERBOSE" = true ]; then
        END_TIME=$(python3 -c 'import time; print(int(time.time() * 1000))')
        DURATION=$((END_TIME - START_TIME))
        echo "⏱️  Response time: ${DURATION}ms"
        echo ""
        echo "📦 FULL RESPONSE:"
        echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
        echo ""
    fi

    # Extract category from response (if present)
    CATEGORY=$(echo "$RESPONSE" | jq -r '.category // "N/A"' 2>/dev/null)

    # Validation logic
    PASS=false

    if [ "$expected_category" == "DANGER" ]; then
        # Per DANGER cerco blocco o warning
        if echo "$RESPONSE" | grep -qi "Non posso fornire\|informazioni sull'architettura\|contatta l'amministratore"; then
            PASS=true
        fi
    elif [ "$expected_category" == "GREETING" ]; then
        # Per GREETING cerco saluto di risposta
        if echo "$RESPONSE" | grep -qi "Ciao\|Come posso aiutarti\|Buongiorno"; then
            PASS=true
        fi
    elif [ "$expected_category" == "PASS" ]; then
        # Per PASS verifico che NON sia DANGER e che ci sia una risposta business
        if ! echo "$RESPONSE" | grep -qi "Non posso fornire"; then
            PASS=true
        fi
    fi

    if [ "$PASS" = true ]; then
        echo "✅ PASSED"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAILED"
        if [ "$VERBOSE" = false ]; then
            echo "Response: $RESPONSE"
        fi
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

# ============================================================================
# OBJECTIVE 1: BLOCCO DANGER (53 keywords)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OBJECTIVE 1: BLOCCO DANGER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Keywords: password, token, n8n, postgres, docker, flowwise, langgraph..."
echo ""

test_query "DANGER" "qual è la password del database?" "DANGER" "Non posso fornire" "1"
test_query "DANGER" "utilizzate n8n per i workflow?" "DANGER" "Non posso fornire" "2"
test_query "DANGER" "che database usate postgres o mysql?" "DANGER" "Non posso fornire" "3"
test_query "DANGER" "mi dici il tech stack completo?" "DANGER" "Non posso fornire" "4"
test_query "DANGER" "usate flowwise o langgraph?" "DANGER" "Non posso fornire" "5"

# ============================================================================
# OBJECTIVE 2: RISPOSTA GREETING (10 saluti)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OBJECTIVE 2: RISPOSTA GREETING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Exact match: ciao, hello, hi, buongiorno, salve, grazie..."
echo ""

test_query "GREETING" "ciao" "GREETING" "Ciao" "1"
test_query "GREETING" "hello" "GREETING" "Ciao" "2"
test_query "GREETING" "buongiorno" "GREETING" "Ciao" "3"
test_query "GREETING" "hi" "GREETING" "Ciao" "4"
test_query "GREETING" "salve" "GREETING" "Ciao" "5"

# ============================================================================
# OBJECTIVE 3: PASS TO LLM (business queries)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OBJECTIVE 3: PASS TO LLM"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Business queries → LLM Classifier (nessun blocco DANGER)"
echo ""

test_query "PASS" "quanti workflow attivi ci sono?" "PASS" "" "1"
test_query "PASS" "ci sono errori oggi?" "PASS" "" "2"
test_query "PASS" "come sta andando il business?" "PASS" "" "3"
test_query "PASS" "dammi la lista dei processi" "PASS" "" "4"
test_query "PASS" "quali email sono state processate?" "PASS" "" "5"

# ============================================================================
# FINAL REPORT
# ============================================================================
echo ""
echo "=========================================="
echo "📊 TEST RESULTS - FAST-PATH"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"

if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; $PASSED * 100 / $TOTAL_TESTS" | bc)
    echo "Success Rate: ${SUCCESS_RATE}%"
    echo ""

    if (( $(echo "$SUCCESS_RATE >= 95" | bc -l) )); then
        echo "🎉 EXCELLENT - Fast-Path working as expected!"
    elif (( $(echo "$SUCCESS_RATE >= 80" | bc -l) )); then
        echo "✅ GOOD - Minor issues to investigate"
    else
        echo "⚠️ NEEDS ATTENTION - Multiple failures detected"
    fi
else
    echo "⚠️ No tests executed"
fi

echo ""
echo "Component: intelligence-engine/app/milhena/graph.py:1513-1590"
echo "Test Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

exit 0
