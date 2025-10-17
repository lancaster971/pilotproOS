#!/bin/bash

# ============================================================================
# TEST CLASSIFIER v3.5.2 - Verifica classificazione + clarification
# ============================================================================
# Obiettivi:
# 1. Verifica confidence 1.0 per query univoche
# 2. Verifica clarification per query ambigue (TRAPPOLE)
# 3. Verifica uso context reale per query context-dependent
#
# Output: Report sintetico markdown (tabella risultati)
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Config
API_URL="http://localhost:8000/api/chat"
DELAY=3  # seconds between requests (rate limit)
SESSION_PREFIX="test-classifier-$(date +%s)"
RESULTS_FILE="/tmp/test-classifier-results.json"

# Initialize results file
echo "[]" > "$RESULTS_FILE"

# ============================================================================
# Helper Functions
# ============================================================================

test_query() {
    local test_id="$1"
    local query="$2"
    local expected_behavior="$3"  # "univoque" | "ambiguous" | "context"
    local expected_category="$4"  # Expected category (or "any" for ambiguous)

    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[$test_id] Testing: \"$query\"${NC}"
    echo -e "${BLUE}Expected: $expected_behavior${NC}"

    # Create unique session ID for this test
    session_id="${SESSION_PREFIX}-${test_id}"

    # Make API request
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"$session_id\"}" \
        --max-time 30)

    # Extract fields from response
    category=$(echo "$response" | jq -r '.metadata.category // "ERROR"')
    confidence=$(echo "$response" | jq -r '.metadata.confidence // 0')
    response_text=$(echo "$response" | jq -r '.response // ""')

    # Check if clarification was asked (look for "cosa intendi" or "opzione" in response)
    clarification_asked="NO"
    if echo "$response_text" | grep -qi "cosa intendi\|opzione\|vuoi dire\|specificamente"; then
        clarification_asked="YES"
    fi

    # Determine success based on expected behavior
    success="❌"
    reason=""

    case "$expected_behavior" in
        "univoque")
            if [[ "$category" == "$expected_category" ]] && (( $(echo "$confidence >= 0.9" | bc -l) )); then
                success="✅"
                reason="Category correct + confidence high"
            else
                reason="Expected $expected_category conf≥0.9, got $category conf=$confidence"
            fi
            ;;
        "ambiguous")
            if [[ "$clarification_asked" == "YES" ]]; then
                success="✅"
                reason="Clarification asked (GOOD)"
            else
                reason="NO clarification asked (BAD - should be ambiguous)"
            fi
            ;;
        "context")
            if [[ "$category" == "$expected_category" ]] && (( $(echo "$confidence >= 0.9" | bc -l) )); then
                # Check if response mentions real data (workflow names, numbers)
                if echo "$response_text" | grep -qE "[0-9]+|Gestione|Backup|ChatOne|Database"; then
                    success="✅"
                    reason="Category correct + uses real context data"
                else
                    success="⚠️"
                    reason="Category correct but context data unclear"
                fi
            else
                reason="Expected $expected_category conf≥0.9, got $category conf=$confidence"
            fi
            ;;
    esac

    # Print result
    echo -e "  Category: ${YELLOW}$category${NC}"
    echo -e "  Confidence: ${YELLOW}$confidence${NC}"
    echo -e "  Clarification: ${YELLOW}$clarification_asked${NC}"
    echo -e "  Result: $success $reason"

    # Save result to JSON
    result_json=$(jq -n \
        --arg id "$test_id" \
        --arg query "$query" \
        --arg expected "$expected_behavior" \
        --arg category "$category" \
        --arg confidence "$confidence" \
        --arg clarification "$clarification_asked" \
        --arg success "$success" \
        --arg reason "$reason" \
        '{id: $id, query: $query, expected: $expected, category: $category, confidence: $confidence, clarification: $clarification, success: $success, reason: $reason}')

    # Append to results file
    jq ". += [$result_json]" "$RESULTS_FILE" > "${RESULTS_FILE}.tmp" && mv "${RESULTS_FILE}.tmp" "$RESULTS_FILE"

    # Delay before next request (rate limit)
    if [[ "$DELAY" -gt 0 ]]; then
        echo -e "  ${YELLOW}Waiting ${DELAY}s (rate limit)...${NC}"
        sleep "$DELAY"
    fi
}

# ============================================================================
# Test Suite
# ============================================================================

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  TEST CLASSIFIER v3.5.2 - Comprehensive Test Suite        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "API URL: $API_URL"
echo "Delay: ${DELAY}s between requests"
echo "Results: $RESULTS_FILE"
echo ""

# ============================================================================
# GROUP A: Query Univoche (4) - Expected confidence 1.0
# ============================================================================

echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}GROUP A: Query Univoche (confidence 1.0 expected)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

test_query "A1" "lista completa processi business attivi" "univoque" "PROCESS_LIST"
test_query "A2" "errori nelle esecuzioni degli ultimi 7 giorni" "univoque" "ERROR_ANALYSIS"
test_query "A3" "email ricevute oggi da clienti ChatOne" "univoque" "EMAIL_ACTIVITY"
test_query "A4" "attiva il workflow Gestione Lead" "univoque" "PROCESS_ACTION"

# ============================================================================
# GROUP B: Query AMBIGUE (4) - Expected clarification
# ============================================================================

echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}GROUP B: Query AMBIGUE (clarification expected)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

test_query "B1" "dammi i dati" "ambiguous" "any"
test_query "B2" "cosa sta succedendo?" "ambiguous" "any"
test_query "B3" "ieri" "ambiguous" "any"
test_query "B4" "controllo" "ambiguous" "any"

# ============================================================================
# GROUP C: Query Context-Dependent (4) - Test context injection
# ============================================================================

echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}GROUP C: Context-Dependent (uses real system data)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

test_query "C1" "quanti workflow abbiamo in produzione?" "context" "PROCESS_LIST"
test_query "C2" "errori nel processo Backup Database stamattina" "context" "ERROR_ANALYSIS"
test_query "C3" "quante email abbiamo gestito questa settimana?" "context" "EMAIL_ACTIVITY"
test_query "C4" "quale workflow ha fallito più volte recentemente?" "context" "ERROR_ANALYSIS"

# ============================================================================
# Generate Report
# ============================================================================

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  REPORT SINTETICO - Test Results Summary                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Read results from JSON
results=$(cat "$RESULTS_FILE")

# Calculate stats
total_tests=$(echo "$results" | jq 'length')
passed_tests=$(echo "$results" | jq '[.[] | select(.success == "✅")] | length')
failed_tests=$(echo "$results" | jq '[.[] | select(.success == "❌")] | length')
warning_tests=$(echo "$results" | jq '[.[] | select(.success == "⚠️")] | length')

# Group stats
univoque_total=$(echo "$results" | jq '[.[] | select(.expected == "univoque")] | length')
univoque_passed=$(echo "$results" | jq '[.[] | select(.expected == "univoque" and .success == "✅")] | length')

ambiguous_total=$(echo "$results" | jq '[.[] | select(.expected == "ambiguous")] | length')
ambiguous_passed=$(echo "$results" | jq '[.[] | select(.expected == "ambiguous" and .success == "✅")] | length')

context_total=$(echo "$results" | jq '[.[] | select(.expected == "context")] | length')
context_passed=$(echo "$results" | jq '[.[] | select(.expected == "context" and (.success == "✅" or .success == "⚠️"))] | length')

# Print markdown table
echo "┌──────┬─────────────────────────────┬──────────────────┬────────────┬───────────────┬──────┐"
echo "│ ID   │ Query                       │ Category         │ Confidence │ Clarification │ Pass │"
echo "├──────┼─────────────────────────────┼──────────────────┼────────────┼───────────────┼──────┤"

echo "$results" | jq -r '.[] |
    "│ \(.id | ljust(4)) │ \(.query[:27] | ljust(27)) │ \(.category[:16] | ljust(16)) │ \(.confidence | tostring | ljust(10)) │ \(.clarification | ljust(13)) │ \(.success | ljust(4)) │"'

echo "└──────┴─────────────────────────────┴──────────────────┴────────────┴───────────────┴──────┘"

# Print summary
echo ""
echo "SUMMARY:"
echo "─────────────────────────────────────────────────────────"
echo -e "✅ Univoche (confidence 1.0):     ${univoque_passed}/${univoque_total} ($(( univoque_passed * 100 / univoque_total ))%)"
echo -e "⚠️  Ambigue (clarification):       ${ambiguous_passed}/${ambiguous_total} ($(( ambiguous_passed * 100 / ambiguous_total ))%) ${RED}← CRITICO${NC}"
echo -e "✅ Context-dependent (real data):  ${context_passed}/${context_total} ($(( context_passed * 100 / context_total ))%)"
echo "─────────────────────────────────────────────────────────"

# Calculate pass percentage
pass_percentage=$(( (passed_tests + warning_tests) * 100 / total_tests ))
echo -e "TOTAL: ${passed_tests}+${warning_tests}/${total_tests} (${pass_percentage}%) - Target ≥10/12 (83%)"

# Final verdict
if [[ $pass_percentage -ge 83 ]] && [[ $ambiguous_passed -ge 3 ]]; then
    echo -e "\n${GREEN}✅✅✅ TEST SUITE PASSED ✅✅✅${NC}"
    echo -e "${GREEN}Classifier v3.5.2 is working correctly!${NC}"
    exit 0
else
    echo -e "\n${RED}❌❌❌ TEST SUITE FAILED ❌❌❌${NC}"
    echo -e "${RED}Classifier v3.5.2 needs debugging.${NC}"

    # Print failed tests details
    echo ""
    echo "Failed tests details:"
    echo "$results" | jq -r '.[] | select(.success == "❌") | "  [\(.id)] \(.query): \(.reason)"'

    exit 1
fi
