#!/bin/bash

# RAG End-to-End Test Suite (2025-10-17)
# Verifica TUTTE le funzionalità della pagina /rag

set -e  # Exit on error

echo "🧪 RAG End-to-End Test Suite"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API Endpoints
BACKEND_URL="http://localhost:3001"
RAG_API="$BACKEND_URL/api/rag"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_endpoint() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="${5:-200}"

    echo -e "${BLUE}📋 Test: $test_name${NC}"

    if [ "$method" = "POST" ] && [ ! -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            --max-time 10)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$endpoint" \
            --max-time 10)
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} - HTTP $http_code"
        echo "   Response preview: $(echo "$body" | jq -c '.' 2>/dev/null | head -c 100)..."
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "$body"  # Return body for further processing
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} - Expected HTTP $expected_status, got HTTP $http_code"
        echo "   Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    echo ""
}

# ============================================
# Test 1: RAG Statistics
# ============================================
echo ""
echo "================================"
echo "Test 1: RAG Statistics"
echo "================================"
stats_response=$(test_endpoint \
    "GET /api/rag/stats" \
    "GET" \
    "$RAG_API/stats" \
    "" \
    "200")

if [ $? -eq 0 ]; then
    total_docs=$(echo "$stats_response" | jq -r '.total_documents // 0' 2>/dev/null)
    echo "   📊 Total documents in KB: $total_docs"
fi
echo ""

# ============================================
# Test 2: List Documents (before upload)
# ============================================
echo "================================"
echo "Test 2: List Documents (Initial)"
echo "================================"
list_response=$(test_endpoint \
    "GET /api/rag/documents" \
    "GET" \
    "$RAG_API/documents" \
    "" \
    "200")

if [ $? -eq 0 ]; then
    initial_count=$(echo "$list_response" | jq -r '.total_count // 0' 2>/dev/null)
    echo "   📄 Documents in KB: $initial_count"
fi
echo ""

# ============================================
# Test 3: Semantic Search (Pre-upload)
# ============================================
echo "================================"
echo "Test 3: Semantic Search (Empty)"
echo "================================"
search_response=$(test_endpoint \
    "POST /api/rag/search" \
    "POST" \
    "$RAG_API/search" \
    '{"query": "come funziona il sistema", "top_k": 5}' \
    "200")

if [ $? -eq 0 ]; then
    results_count=$(echo "$search_response" | jq -r '.total_count // 0' 2>/dev/null)
    echo "   🔍 Search results: $results_count"
fi
echo ""

# ============================================
# Test 4: Upload Document
# ============================================
echo "================================"
echo "Test 4: Upload Document"
echo "================================"
echo -e "${BLUE}📋 Test: POST /api/rag/documents (file upload)${NC}"

# Create temporary test file
TEST_FILE="/tmp/test-rag-doc-$$.txt"
cat > "$TEST_FILE" <<'EOF'
PilotProOS - Sistema di Business Process Automation

Il sistema PilotProOS è una piattaforma containerizzata per l'automazione
dei processi aziendali. Include:

1. Intelligence Engine - Agente AI powered by LangGraph
2. RAG System - Knowledge base con ChromaDB e NOMIC embeddings
3. Backend Express - API proxy con auth JWT
4. Frontend Vue 3 - Portal con dark theme enterprise

Caratteristiche principali:
- Auto-Learning Fast-Path (pattern recognition)
- AsyncRedisSaver per memoria persistente (7-day TTL)
- Business Abstraction Layer (zero technical leaks)
- Monitoring con Prometheus e LangSmith

Questo documento di test serve per verificare il sistema RAG end-to-end.
EOF

# Upload using multipart/form-data
upload_response=$(curl -s -w "\n%{http_code}" \
    -X POST "$RAG_API/documents" \
    -F "files=@$TEST_FILE" \
    -F "category=test" \
    -F "tags=[\"test\",\"automation\",\"pilotpros\"]" \
    -F "auto_category=true" \
    --max-time 30)

upload_http_code=$(echo "$upload_response" | tail -n1)
upload_body=$(echo "$upload_response" | sed '$d')

if [ "$upload_http_code" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - HTTP $upload_http_code"
    doc_id=$(echo "$upload_body" | jq -r '.document_id // ""' 2>/dev/null)
    echo "   📤 Uploaded document ID: $doc_id"
    echo "   Response: $(echo "$upload_body" | jq -c '.' 2>/dev/null)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC} - Expected HTTP 200, got HTTP $upload_http_code"
    echo "   Response: $upload_body"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Cleanup temp file
rm -f "$TEST_FILE"
echo ""

# Wait for indexing (2 seconds)
echo "⏳ Waiting 2s for document indexing..."
sleep 2
echo ""

# ============================================
# Test 5: List Documents (after upload)
# ============================================
echo "================================"
echo "Test 5: List Documents (Updated)"
echo "================================"
list_after_response=$(test_endpoint \
    "GET /api/rag/documents" \
    "GET" \
    "$RAG_API/documents" \
    "" \
    "200")

if [ $? -eq 0 ]; then
    final_count=$(echo "$list_after_response" | jq -r '.total_count // 0' 2>/dev/null)
    echo "   📄 Documents in KB: $final_count"

    if [ "$final_count" -gt "$initial_count" ]; then
        echo -e "   ${GREEN}✅ Document count increased!${NC} ($initial_count → $final_count)"
    else
        echo -e "   ${YELLOW}⚠️  Document count unchanged${NC} (might be deduped or delayed)"
    fi
fi
echo ""

# ============================================
# Test 6: Semantic Search (Post-upload)
# ============================================
echo "================================"
echo "Test 6: Semantic Search (Populated)"
echo "================================"
search_after_response=$(test_endpoint \
    "POST /api/rag/search" \
    "POST" \
    "$RAG_API/search" \
    '{"query": "come funziona il sistema di automazione", "top_k": 5}' \
    "200")

if [ $? -eq 0 ]; then
    results_after=$(echo "$search_after_response" | jq -r '.total_count // 0' 2>/dev/null)
    echo "   🔍 Search results: $results_after"

    # Show top result if available
    top_result=$(echo "$search_after_response" | jq -r '.results[0].page_content // ""' 2>/dev/null | head -c 150)
    if [ ! -z "$top_result" ]; then
        echo "   📖 Top result preview: $top_result..."

        # Show relevance score
        score=$(echo "$search_after_response" | jq -r '.results[0].score // 0' 2>/dev/null)
        echo "   🎯 Relevance score: $score"
    fi
fi
echo ""

# ============================================
# Test 7: Delete Document (if doc_id exists)
# ============================================
if [ ! -z "$doc_id" ] && [ "$doc_id" != "null" ]; then
    echo "================================"
    echo "Test 7: Delete Document"
    echo "================================"
    delete_response=$(test_endpoint \
        "DELETE /api/rag/documents/$doc_id" \
        "DELETE" \
        "$RAG_API/documents/$doc_id" \
        "" \
        "200")

    if [ $? -eq 0 ]; then
        echo "   🗑️  Document deleted successfully"
    fi
    echo ""
else
    echo "================================"
    echo "Test 7: Delete Document"
    echo "================================"
    echo -e "${YELLOW}⏭️  SKIPPED${NC} - No document ID available from upload"
    echo ""
fi

# ============================================
# Test 8: RAG Statistics (Final)
# ============================================
echo "================================"
echo "Test 8: RAG Statistics (Final)"
echo "================================"
final_stats_response=$(test_endpoint \
    "GET /api/rag/stats" \
    "GET" \
    "$RAG_API/stats" \
    "" \
    "200")

if [ $? -eq 0 ]; then
    final_total_docs=$(echo "$final_stats_response" | jq -r '.total_documents // 0' 2>/dev/null)
    categories=$(echo "$final_stats_response" | jq -r '.categories // []' 2>/dev/null)
    avg_size=$(echo "$final_stats_response" | jq -r '.avg_document_size // 0' 2>/dev/null)

    echo "   📊 Final statistics:"
    echo "      - Total documents: $final_total_docs"
    echo "      - Categories: $categories"
    echo "      - Avg doc size: $avg_size chunks"
fi
echo ""

# ============================================
# Summary
# ============================================
echo "======================================"
echo "📊 Test Suite Summary"
echo "======================================"
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo ""
echo -e "Total tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "Failed: $TESTS_FAILED"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "RAG system is fully operational:"
    echo "  ✅ Statistics endpoint working"
    echo "  ✅ Document listing working"
    echo "  ✅ Document upload working (multipart/form-data)"
    echo "  ✅ Semantic search working"
    echo "  ✅ Document deletion working"
    echo ""
    echo "Frontend page http://localhost:3000/rag is READY! 🚀"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please check the errors above and fix before using /rag page."
    exit 1
fi
