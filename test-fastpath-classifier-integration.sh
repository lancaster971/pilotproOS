#!/bin/bash

# ============================================================================
# TEST FAST-PATH + CLASSIFIER INTEGRATION
# ============================================================================
# Obiettivi:
# 1. Verifica Fast-path HIT (pattern già appreso)
# 2. Verifica Fast-path MISS → Classifier (query nuova)
# 3. Verifica Auto-learning (confidence >0.9 salva in DB)
# 4. Verifica Latency (fast-path vs classifier)
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Config
API_URL="http://localhost:8000/api/chat"
DELAY=2
SESSION_PREFIX="fastpath-test-$(date +%s)"
RESULTS_FILE="/tmp/fastpath-integration-results.json"

# Initialize results
echo "[]" > "$RESULTS_FILE"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  FAST-PATH + CLASSIFIER INTEGRATION TEST                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Testing workflow: Query → Fast-path check → Classifier (if miss) → Auto-learn"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

test_integration() {
    local test_id="$1"
    local query="$2"
    local expected_category="$3"
    local phase="$4"  # "first" | "second"

    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[$test_id - $phase call] Query: \"$query\"${NC}"

    session_id="${SESSION_PREFIX}-${test_id}"

    # Measure latency (macOS compatible)
    start_time=$(python3 -c 'import time; print(int(time.time() * 1000))')

    # Make API request
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"$session_id\"}" \
        --max-time 30)

    end_time=$(python3 -c 'import time; print(int(time.time() * 1000))')
    latency=$((end_time - start_time))

    # Extract metadata
    category=$(echo "$response" | jq -r '.metadata.category // "ERROR"')
    confidence=$(echo "$response" | jq -r '.metadata.confidence // 0')

    # Print result
    echo -e "  Category: ${YELLOW}$category${NC}"
    echo -e "  Confidence: ${YELLOW}$confidence${NC}"
    echo -e "  Latency: ${CYAN}${latency}ms${NC}"

    # Determine if fast-path or classifier
    path_used="UNKNOWN"
    if [[ "$phase" == "first" ]]; then
        if [[ $latency -lt 50 ]]; then
            path_used="FAST-PATH (unexpected on first call!)"
        else
            path_used="CLASSIFIER (expected)"
        fi
    else
        if [[ $latency -lt 50 ]]; then
            path_used="FAST-PATH (expected!)"
        else
            path_used="CLASSIFIER (learning may have failed)"
        fi
    fi

    echo -e "  Path: ${CYAN}$path_used${NC}"

    # Validation
    success="❌"
    if [[ "$category" == "$expected_category" ]]; then
        success="✅"
    fi

    echo -e "  Result: $success (expected $expected_category)"

    # Save result
    result_json=$(jq -n \
        --arg id "$test_id" \
        --arg query "$query" \
        --arg phase "$phase" \
        --arg category "$category" \
        --arg confidence "$confidence" \
        --arg latency "$latency" \
        --arg path "$path_used" \
        --arg success "$success" \
        '{id: $id, query: $query, phase: $phase, category: $category, confidence: $confidence, latency: ($latency | tonumber), path: $path, success: $success}')

    jq ". += [$result_json]" "$RESULTS_FILE" > "${RESULTS_FILE}.tmp" && mv "${RESULTS_FILE}.tmp" "$RESULTS_FILE"

    # Delay
    if [[ "$DELAY" -gt 0 ]]; then
        sleep "$DELAY"
    fi
}

# ============================================================================
# TEST SUITE - 4 Query Types
# ============================================================================

echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PHASE 1: First Call (Classifier expected)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

# Test 4 clear/unambiguous queries (confidence >0.9 expected)
test_integration "T1" "lista completa processi business" "PROCESS_LIST" "first"
test_integration "T2" "errori nelle esecuzioni ultimi 7 giorni" "ERROR_ANALYSIS" "first"
test_integration "T3" "email ricevute oggi da ChatOne" "EMAIL_ACTIVITY" "first"
test_integration "T4" "quanti workflow abbiamo attivi?" "PROCESS_LIST" "first"

echo -e "\n${YELLOW}⏸️  Waiting 5 seconds for auto-learning to complete...${NC}"
sleep 5

echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PHASE 2: Second Call (Fast-path expected)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

# Same queries again - should hit fast-path
test_integration "T1" "lista completa processi business" "PROCESS_LIST" "second"
test_integration "T2" "errori nelle esecuzioni ultimi 7 giorni" "ERROR_ANALYSIS" "second"
test_integration "T3" "email ricevute oggi da ChatOne" "EMAIL_ACTIVITY" "second"
test_integration "T4" "quanti workflow abbiamo attivi?" "PROCESS_LIST" "second"

# ============================================================================
# REPORT GENERATION
# ============================================================================

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  REPORT SINTETICO - Integration Test Results              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Read results
results=$(cat "$RESULTS_FILE")

# Generate comparison table
echo "┌──────┬─────────────────────────────┬──────────┬──────────────┬────────────┬──────────────────┐"
echo "│ ID   │ Query                       │ Phase    │ Category     │ Latency    │ Path Used        │"
echo "├──────┼─────────────────────────────┼──────────┼──────────────┼────────────┼──────────────────┤"

echo "$results" | jq -r '.[] |
    "│ \(.id)  │ \(.query[:27] | . + (" " * (27 - length))) │ \(.phase[:8] | . + (" " * (8 - length))) │ \(.category[:12] | . + (" " * (12 - length))) │ \(.latency)ms\(" " * (7 - (.latency | tostring | length)))│ \(.path[:16] | . + (" " * (16 - length))) │"'

echo "└──────┴─────────────────────────────┴──────────┴──────────────┴────────────┴──────────────────┘"

# Calculate statistics
echo ""
echo "STATISTICS:"
echo "─────────────────────────────────────────────────────────"

first_call_avg=$(echo "$results" | jq '[.[] | select(.phase == "first") | .latency] | add / length')
second_call_avg=$(echo "$results" | jq '[.[] | select(.phase == "second") | .latency] | add / length')

echo -e "Average Latency (First call - Classifier):  ${first_call_avg}ms"
echo -e "Average Latency (Second call - Fast-path):  ${second_call_avg}ms"

if (( $(echo "$second_call_avg < 50" | bc -l) )); then
    speedup=$(echo "scale=1; $first_call_avg / $second_call_avg" | bc)
    echo -e "${GREEN}Speedup: ${speedup}x faster ✅${NC}"
else
    echo -e "${RED}Fast-path NOT working (latency >50ms) ❌${NC}"
fi

# Count fast-path hits
fastpath_hits=$(echo "$results" | jq '[.[] | select(.phase == "second" and .latency < 50)] | length')
total_second_calls=$(echo "$results" | jq '[.[] | select(.phase == "second")] | length')

echo ""
echo "Fast-path Hit Rate: ${fastpath_hits}/${total_second_calls}"

if [[ $fastpath_hits -eq $total_second_calls ]]; then
    echo -e "${GREEN}✅✅✅ AUTO-LEARNING WORKING ✅✅✅${NC}"
    echo "All queries learned after first call!"
else
    echo -e "${RED}❌ AUTO-LEARNING FAILED ❌${NC}"
    echo "Some queries not learned. Check confidence threshold."
fi

echo ""
echo "Full results: $RESULTS_FILE"
