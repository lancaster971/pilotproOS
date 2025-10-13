#!/bin/bash
# Test rigoroso schema standardization + React prompt effectiveness

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║   🧪 TEST SCHEMA STANDARDIZATION + REACT PROMPT EFFECTIVENESS           ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Test suite con 3 categorie
declare -a univocal_queries=(
    "quanti workflow attivi?"
    "statistiche sistema"
    "ultime esecuzioni"
    "ci sono errori?"
    "top 5 workflow migliori"
)

declare -a ambiguous_queries=(
    "processi"
    "tabelle"
    "dati"
    "informazioni"
    "cose"
)

declare -a explicit_queries=(
    "quanti processi intendo business process"
    "statistiche processi aziendali"
    "esecuzioni workflow"
)

function test_query() {
    local query="$1"
    local expected="$2"
    local session_id="test-$(echo $query | md5sum | cut -c1-8)"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Query: \"$query\""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    response=$(curl -s -X POST http://localhost:8000/api/n8n/agent/customer-support \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"$session_id\"}" | \
        jq -r '.response')

    echo "📝 Response (first 200 chars):"
    echo "$response" | head -c 200
    echo "..."
    echo ""

    # Check logs for tool call
    tool_called=$(docker logs pilotpros-intelligence-engine-dev 2>&1 | \
        grep -A 5 "session_id.*$session_id" | \
        grep -E "Tool called:|Instant match|CLARIFICATION" | \
        tail -1)

    echo "🔧 Tool Action:"
    if echo "$tool_called" | grep -q "Tool called"; then
        echo "   ✅ TOOL CALLED (direct action)"
    elif echo "$tool_called" | grep -q "CLARIFICATION"; then
        echo "   ❓ CLARIFICATION REQUEST (ambiguous query)"
    elif echo "$tool_called" | grep -q "Instant match"; then
        echo "   ⚡ FAST-PATH (pattern learned)"
    else
        echo "   ⚠️  UNKNOWN ACTION"
    fi

    # Validation
    if [ "$expected" == "TOOL" ]; then
        if echo "$tool_called" | grep -qE "Tool called|Instant match"; then
            echo "   ✅ TEST PASSED (expected tool call)"
        else
            echo "   ❌ TEST FAILED (expected tool call, got clarification)"
        fi
    elif [ "$expected" == "CLARIFY" ]; then
        if echo "$response" | grep -qi "cosa intendi\|specifica\|stai chiedendo"; then
            echo "   ✅ TEST PASSED (expected clarification)"
        else
            echo "   ❌ TEST FAILED (expected clarification, got direct answer)"
        fi
    fi

    echo ""
    sleep 3  # Avoid rate limiting
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 CATEGORIA 1: QUERY UNIVOCHE (dovrebbero chiamare tool direttamente)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for query in "${univocal_queries[@]}"; do
    test_query "$query" "TOOL"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "❓ CATEGORIA 2: QUERY AMBIGUE (dovrebbero chiedere clarification)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for query in "${ambiguous_queries[@]}"; do
    test_query "$query" "CLARIFY"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CATEGORIA 3: QUERY ESPLICITE (dovrebbero chiamare tool con context)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for query in "${explicit_queries[@]}"; do
    test_query "$query" "TOOL"
done

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                        📊 TEST SUMMARY                                   ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ UNIVOCAL QUERIES: Should call tools directly (keywords match)"
echo "❓ AMBIGUOUS QUERIES: Should ask clarification (safety first)"
echo "✅ EXPLICIT QUERIES: Should call tools with context (user specified intent)"
echo ""
echo "Expected behavior:"
echo "  • Keywords in tool descriptions guide LLM selection"
echo "  • React prompt vocabulary defines UNIVOCAL terms"
echo "  • Ambiguous terms trigger clarification (intentional design)"
echo "  • Pattern A schema provides USE WHEN/DO NOT USE guidance"
echo ""
