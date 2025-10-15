#!/bin/bash

# ============================================================================
# TEST CLASSIFIER v3.5.4 - HARD MODE (Ambiguità IMPOSSIBILI)
# ============================================================================
# Obiettivo: Verificare che classifier CHIEDA CHIARIMENTI quando SERVE
# Query progettate per essere IMPOSSIBILI da classificare senza chiedere
# ============================================================================

set -e

API_URL="http://localhost:8000/api/chat"
DELAY=3
SESSION_PREFIX="hard-test-$(date +%s)"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  HARD MODE TEST - Query Impossibili da Classificare        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Target: 100% CLARIFICATION_NEEDED (6/6)"
echo ""

test_hard_query() {
    local id="$1"
    local query="$2"
    local why_impossible="$3"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "[$id] Query: \"$query\""
    echo "Why impossible: $why_impossible"
    echo ""

    session_id="${SESSION_PREFIX}-${id}"

    # Make request
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"$session_id\"}" \
        --max-time 30 2>/dev/null || echo '{"error": "timeout"}')

    # Extract from response
    response_text=$(echo "$response" | jq -r '.response // "ERROR"' 2>/dev/null || echo "ERROR")

    # Check if asked clarification
    asked_clarification="NO"
    if echo "$response_text" | grep -qiE "specifica|chiarimento|cosa intendi|vuoi dire|quale|puoi dire|più dettagli|sii più specifico"; then
        asked_clarification="YES"
    fi

    # Print result
    if [[ "$asked_clarification" == "YES" ]]; then
        echo "✅ CLARIFICATION ASKED"
        echo "Response preview: ${response_text:0:150}..."
    else
        echo "❌ NO CLARIFICATION (should ask!)"
        echo "Response: $response_text"
    fi

    # Delay
    sleep "$DELAY"
}

# ============================================================================
# HARD TEST SUITE - 6 Query IMPOSSIBILI
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "GROUP 1: Pronomi senza riferimento"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_hard_query "H1" "quello" \
    "Pronome senza antecedente - impossibile sapere a cosa si riferisce"

test_hard_query "H2" "anche" \
    "Congiunzione senza contesto - anche COSA?"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "GROUP 2: Query incomplete/paradossali"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_hard_query "H3" "e poi?" \
    "Domanda incompleta - e poi COSA? Serve contesto precedente"

test_hard_query "H4" "quanti?" \
    "Interrogativo senza oggetto - quanti COSA? (processi? errori? email?)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "GROUP 3: Termini ambigui nel contesto business"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_hard_query "H5" "stato" \
    "Ambiguo: stato dei processi? stato di un'esecuzione? stato del sistema?"

test_hard_query "H6" "report" \
    "Ambiguo: report errori? report analytics? report esecuzioni? quale?"

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  HARD MODE RESULTS                                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Check logs above:"
echo "- Expected: 6/6 queries ask CLARIFICATION"
echo "- Any ❌ means classifier answered without asking (BAD)"
echo ""
echo "Next: Check intelligence engine logs for 'CLARIFICATION_NEEDED'"
echo "  docker logs pilotpros-intelligence-engine-dev --since 2m | grep CLARIFICATION"
