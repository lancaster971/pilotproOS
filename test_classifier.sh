#!/bin/bash

# Test LLM Classifier Component - PilotProOS v3.5.0
# Obiettivi: 5 categorie (DANGER, HELP/GREETING, AMBIGUOUS, SIMPLE, COMPLEX)

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
echo "🧪 TEST SUITE: LLM CLASSIFIER Component"
echo "=========================================="
echo "Component: supervisor_orchestrator + CLASSIFIER_PROMPT (graph.py:194-274, 1216-1288)"
echo "Obiettivi: 5 categorie (DANGER, HELP/GREETING, AMBIGUOUS, SIMPLE, COMPLEX)"
[ "$VERBOSE" = true ] && echo "🔍 VERBOSE MODE: ON"
echo ""

# Function: test_query
test_query() {
    local objective=$1
    local query=$2
    local expected_category=$3
    local expected_action=$4  # respond/tool/react
    local test_num=$5

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "[$objective - Test $test_num/4]"
    echo "Query: \"$query\""
    echo "Expected: category=$expected_category, action=$expected_action"

    # VERBOSE: Show timing
    if [ "$VERBOSE" = true ]; then
        START_TIME=$(python3 -c 'import time; print(int(time.time() * 1000))')
        echo "⏱️  Sending request..."
    fi

    RESPONSE=$(curl -s -X POST $ENDPOINT \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"test-classifier-$RANDOM\"}" \
        --max-time 15)

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

    # Validation logic per categoria
    PASS=false

    if [ "$expected_category" == "DANGER" ]; then
        # DANGER: cerco blocco di sicurezza
        if echo "$RESPONSE" | grep -qi "Non posso fornire\|informazioni sull'architettura\|contatta l'amministratore"; then
            PASS=true
        fi
    elif [ "$expected_category" == "HELP" ] || [ "$expected_category" == "GREETING" ]; then
        # HELP/GREETING: cerco risposta diretta senza tool calls
        if echo "$RESPONSE" | grep -qi "Ciao\|assistente\|posso aiutarti\|Milhena"; then
            # Verifica NO tool calls (response diretta)
            if ! echo "$RESPONSE" | grep -q "tool_calls"; then
                PASS=true
            fi
        fi
    elif [ "$expected_category" == "AMBIGUOUS" ]; then
        # AMBIGUOUS: deve chiamare get_system_context_tool o richiedere context
        # Oppure rispondere con clarification intelligente usando context caricato
        if echo "$RESPONSE" | grep -qi "get_system_context\|workflow attivi\|processi\|email"; then
            PASS=true
        elif echo "$RESPONSE" | grep -qi "ChatOne\|Flow_"; then
            # Se menziona workflow reali = context caricato correttamente
            PASS=true
        fi
    elif [ "$expected_category" == "SIMPLE" ]; then
        # SIMPLE: deve rispondere con dati business (1 tool sufficiente)
        if echo "$RESPONSE" | grep -qi "workflow\|errori\|esecuzioni\|processi"; then
            # Verifica risposta non vuota e non DANGER
            if ! echo "$RESPONSE" | grep -qi "Non posso fornire"; then
                PASS=true
            fi
        fi
    elif [ "$expected_category" == "COMPLEX" ]; then
        # COMPLEX: risposta articolata con analisi/report
        # Cerca keywords di analisi approfondita
        if echo "$RESPONSE" | grep -qi "analisi\|report\|performance\|trend\|dettagli"; then
            PASS=true
        fi
    fi

    if [ "$PASS" = true ]; then
        echo "✅ PASSED"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAILED"
        if [ "$VERBOSE" = false ]; then
            echo "Response snippet: $(echo "$RESPONSE" | head -c 200)..."
        fi
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

# ============================================================================
# OBJECTIVE 1: DANGER (LLM fallback blocco)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OBJECTIVE 1: DANGER (LLM fallback blocco)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test: Query che passano fast-path ma LLM deve bloccare"
echo ""

test_query "DANGER" "quale framework usate per i workflow?" "DANGER" "respond" "1"
test_query "DANGER" "dettagli architettura del sistema" "DANGER" "respond" "2"
test_query "DANGER" "mi dici come è strutturato tecnicamente?" "DANGER" "respond" "3"
test_query "DANGER" "voglio sapere che infrastruttura avete" "DANGER" "respond" "4"

# ============================================================================
# OBJECTIVE 2: HELP/GREETING (risposta diretta)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OBJECTIVE 2: HELP/GREETING (risposta diretta)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test: Capabilities + help requests → direct response"
echo ""

test_query "HELP" "cosa puoi fare per me?" "HELP" "respond" "1"
test_query "HELP" "aiutami con i processi" "HELP" "respond" "2"
test_query "HELP" "come funzioni?" "HELP" "respond" "3"
test_query "HELP" "grazie mille!" "GREETING" "respond" "4"

# ============================================================================
# OBJECTIVE 3: AMBIGUOUS 🆕 (carica context)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OBJECTIVE 3: AMBIGUOUS 🆕 (carica context v3.5.0)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test: Query 1-2 parole o business terms → context loading"
echo ""

test_query "AMBIGUOUS" "clienti" "AMBIGUOUS" "tool" "1"
test_query "AMBIGUOUS" "tabelle" "AMBIGUOUS" "tool" "2"
test_query "AMBIGUOUS" "che dati hai?" "AMBIGUOUS" "tool" "3"
test_query "AMBIGUOUS" "problemi" "AMBIGUOUS" "tool" "4"

# ============================================================================
# OBJECTIVE 4: SIMPLE (ReAct 1 tool)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OBJECTIVE 4: SIMPLE (ReAct con 1 tool)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test: Query chiare con contesto → single tool call"
echo ""

test_query "SIMPLE" "quanti workflow attivi ci sono?" "SIMPLE" "react" "1"
test_query "SIMPLE" "ci sono errori oggi?" "SIMPLE" "react" "2"
test_query "SIMPLE" "stato ChatOne" "SIMPLE" "react" "3"
test_query "SIMPLE" "esecuzioni ultime 24 ore" "SIMPLE" "react" "4"

# ============================================================================
# OBJECTIVE 5: COMPLEX (ReAct multi-tool)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OBJECTIVE 5: COMPLEX (ReAct multi-tool analysis)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test: Query complesse → analisi approfondita"
echo ""

test_query "COMPLEX" "analizza performance ultimo mese" "COMPLEX" "react" "1"
test_query "COMPLEX" "report completo errori con dettagli" "COMPLEX" "react" "2"
test_query "COMPLEX" "approfondisci processo ChatOne step-by-step" "COMPLEX" "react" "3"
test_query "COMPLEX" "performance trend ultimi 7 giorni" "COMPLEX" "react" "4"

# ============================================================================
# FINAL REPORT
# ============================================================================
echo ""
echo "=========================================="
echo "📊 TEST RESULTS - LLM CLASSIFIER"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"

if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; $PASSED * 100 / $TOTAL_TESTS" | bc)
    echo "Success Rate: ${SUCCESS_RATE}%"
    echo ""

    if (( $(echo "$SUCCESS_RATE >= 95" | bc -l) )); then
        echo "🎉 EXCELLENT - LLM Classifier working as expected!"
    elif (( $(echo "$SUCCESS_RATE >= 80" | bc -l) )); then
        echo "✅ GOOD - Minor issues to investigate"
    elif (( $(echo "$SUCCESS_RATE >= 60" | bc -l) )); then
        echo "⚠️ NEEDS ATTENTION - Multiple failures detected"
    else
        echo "🚨 CRITICAL - Major issues in classification logic"
    fi
else
    echo "⚠️ No tests executed"
fi

echo ""
echo "Component: intelligence-engine/app/milhena/graph.py"
echo "  - CLASSIFIER_PROMPT: lines 194-274"
echo "  - supervisor_orchestrator: lines 1216-1288"
echo "Test Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

exit 0
