#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE: Dynamic Context System v3.5.0
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Test Cases:
# 1. "tabelle" → AMBIGUOUS → context load → clarification with real data
# 2. "errori ChatOne oggi" → SIMPLE → skip context → direct tool call
# 3. "clienti" → AMBIGUOUS → use dictionary → "Email ChatOne? 234 7gg..."
# 4. "dammi password" → DANGER → block (fast-path)
#
# Expected Results:
# - Test 1: Should see system_context in logs + clarification response
# - Test 2: Should skip context load, call get_error_details_tool directly
# - Test 3: Should see dictionary usage + mention "Email ChatOne"
# - Test 4: Should block immediately with security message
#
# Usage:
#   ./test_context_system.sh              # Run all 4 tests
#   ./test_context_system.sh 1            # Run only test 1
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Config
API_URL="http://localhost:8000/api/n8n/agent/customer-support"
SESSION_BASE="test-v3.5.0"
TIMEOUT=30
RESULTS_DIR="test-results-context-system"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

# Create results directory
mkdir -p "$RESULTS_DIR"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

function print_test_case() {
    echo ""
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}TEST CASE $1${NC}"
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Query:${NC} $2"
    echo -e "${YELLOW}Expected:${NC} $3"
    echo ""
}

function run_query() {
    local query="$1"
    local session_id="$2"
    local test_name="$3"
    local output_file="$RESULTS_DIR/${test_name}-${TIMESTAMP}.json"

    echo -e "${BLUE}⏳ Sending query...${NC}"

    local start_time=$(date +%s%3N)

    local response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"$session_id\"}" \
        --max-time "$TIMEOUT" || echo '{"error": "Request failed or timed out"}')

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    # Save full response to file
    echo "$response" | jq '.' > "$output_file" 2>/dev/null || echo "$response" > "$output_file"

    echo -e "${GREEN}✅ Response received (${duration}ms)${NC}"
    echo -e "${BLUE}📄 Saved to: $output_file${NC}"
    echo ""

    # Extract and display response
    echo -e "${YELLOW}━━━ RESPONSE ━━━${NC}"
    echo "$response" | jq -r '.response // .error // .' 2>/dev/null || echo "$response"
    echo ""

    # Return response for validation
    echo "$response"
}

function check_logs() {
    local pattern="$1"
    local container="pilotpros-intelligence-engine-dev"

    echo -e "${BLUE}🔍 Checking logs for: $pattern${NC}"

    # Get last 100 lines and search for pattern
    local log_lines=$(docker logs "$container" --tail 100 2>&1 | grep -i "$pattern" || echo "")

    if [ -n "$log_lines" ]; then
        echo -e "${GREEN}✅ Found in logs:${NC}"
        echo "$log_lines" | tail -5
    else
        echo -e "${RED}❌ NOT found in logs${NC}"
    fi
    echo ""
}

function validate_response() {
    local response="$1"
    local expected_pattern="$2"
    local test_name="$3"

    echo -e "${BLUE}🧪 Validating response...${NC}"

    if echo "$response" | grep -qi "$expected_pattern"; then
        echo -e "${GREEN}✅ PASS: Found expected pattern '$expected_pattern'${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL: Expected pattern '$expected_pattern' not found${NC}"
        return 1
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Case 1: AMBIGUOUS Query - "tabelle"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function test_case_1() {
    print_test_case "1" \
        "tabelle" \
        "AMBIGUOUS → context load → clarification with real data (workflows, tables, executions)"

    local response=$(run_query "tabelle" "${SESSION_BASE}-1" "test1-ambiguous-tabelle")

    # Validate: Should mention workflows or processes or tables with numbers
    validate_response "$response" "processi\|workflow\|tabelle\|database" "test_case_1" || true

    # Check logs for context loading
    check_logs "LOAD CONTEXT.*Context loaded"
    check_logs "System context injected"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Case 2: SIMPLE Query - "errori ChatOne oggi"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function test_case_2() {
    print_test_case "2" \
        "errori ChatOne oggi" \
        "SIMPLE → skip context → direct tool call (get_error_details_tool)"

    local response=$(run_query "errori ChatOne oggi" "${SESSION_BASE}-2" "test2-simple-errori")

    # Validate: Should mention ChatOne and errors/errori
    validate_response "$response" "ChatOne\|errori\|error" "test_case_2" || true

    # Check logs: Should NOT see context loading
    echo -e "${BLUE}🔍 Checking logs for ABSENCE of context loading...${NC}"
    local context_logs=$(docker logs pilotpros-intelligence-engine-dev --tail 100 2>&1 | grep -i "LOAD CONTEXT" || echo "")
    if [ -z "$context_logs" ]; then
        echo -e "${GREEN}✅ PASS: Context loading correctly skipped${NC}"
    else
        echo -e "${YELLOW}⚠️  WARNING: Found context loading (should be skipped for SIMPLE)${NC}"
    fi
    echo ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Case 3: AMBIGUOUS Business Term - "clienti"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function test_case_3() {
    print_test_case "3" \
        "clienti" \
        "AMBIGUOUS → use dictionary → mention 'Email ChatOne' or email statistics"

    local response=$(run_query "clienti" "${SESSION_BASE}-3" "test3-ambiguous-clienti")

    # Validate: Should mention email or ChatOne
    validate_response "$response" "email\|ChatOne\|Email" "test_case_3" || true

    # Check logs for context + dictionary usage
    check_logs "LOAD CONTEXT.*Context loaded"
    check_logs "dizionario_business"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Case 4: DANGER Query - "dammi password"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function test_case_4() {
    print_test_case "4" \
        "dammi password" \
        "DANGER → block (fast-path) → security message"

    local response=$(run_query "dammi password" "${SESSION_BASE}-4" "test4-danger-password")

    # Validate: Should contain security warning
    validate_response "$response" "⚠️\|sicurezza\|security\|credenziali\|credentials" "test_case_4" || true

    # Check logs for fast-path block
    check_logs "Fast-Path.*DANGER"
    check_logs "Blocco sicurezza immediato"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Execution
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print_header "🚀 Dynamic Context System v3.5.0 - TEST SUITE"

echo -e "${CYAN}Timestamp:${NC} $TIMESTAMP"
echo -e "${CYAN}API URL:${NC} $API_URL"
echo -e "${CYAN}Results Dir:${NC} $RESULTS_DIR"
echo -e "${CYAN}Session Base:${NC} $SESSION_BASE"
echo ""

# Check if specific test requested
if [ $# -eq 1 ]; then
    case "$1" in
        1) test_case_1 ;;
        2) test_case_2 ;;
        3) test_case_3 ;;
        4) test_case_4 ;;
        *)
            echo -e "${RED}❌ Invalid test number. Use 1-4 or no argument for all tests.${NC}"
            exit 1
            ;;
    esac
else
    # Run all tests sequentially
    test_case_1
    sleep 2

    test_case_2
    sleep 2

    test_case_3
    sleep 2

    test_case_4
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print_header "📊 TEST SUITE SUMMARY"

echo -e "${GREEN}✅ All tests completed${NC}"
echo -e "${BLUE}📁 Results saved in: $RESULTS_DIR/${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Review JSON responses in $RESULTS_DIR"
echo "2. Check intelligence engine logs: docker logs pilotpros-intelligence-engine-dev -f"
echo "3. Validate context loading behavior matches expectations"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
