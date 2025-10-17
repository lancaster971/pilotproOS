#!/bin/bash

# RAG Simple Test (macOS compatible)
# Verifica rapida delle funzionalità RAG essenziali

echo "🧪 RAG Simple Test Suite"
echo "================================"
echo ""

# API Base
API="http://localhost:3001/api/rag"

# Test 1: Statistics
echo "📋 Test 1: GET /api/rag/stats"
curl -s --max-time 5 "$API/stats" | jq '.'
echo ""

# Test 2: List Documents
echo "📋 Test 2: GET /api/rag/documents"
curl -s --max-time 5 "$API/documents" | jq '.'
echo ""

# Test 3: Semantic Search
echo "📋 Test 3: POST /api/rag/search"
curl -s --max-time 10 "$API/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "come funziona PilotProOS", "top_k": 3}' | jq '.'
echo ""

# Test 4: Upload Document
echo "📋 Test 4: POST /api/rag/documents (upload)"
cat > /tmp/test-rag.txt <<'EOF'
Test document per verificare il sistema RAG.
Questo documento contiene informazioni di test per PilotProOS.
Il sistema include Intelligence Engine, RAG, Backend e Frontend.
EOF

echo "Uploading test file..."
UPLOAD_RESPONSE=$(curl -s --max-time 30 "$API/documents" \
    -F "files=@/tmp/test-rag.txt" \
    -F "category=test" \
    -F 'tags=["test","pilotpros"]')

echo "$UPLOAD_RESPONSE" | jq '.'

# Extract document ID
DOC_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.document_id // ""')
echo ""
echo "Uploaded document ID: $DOC_ID"
echo ""

# Wait for indexing
echo "⏳ Waiting 3s for indexing..."
sleep 3
echo ""

# Test 5: Search with uploaded content
echo "📋 Test 5: Search for uploaded content"
curl -s --max-time 10 "$API/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test document pilotpros", "top_k": 5}' | jq '.results[] | {score, preview: .page_content[:100]}'
echo ""

# Test 6: Delete uploaded document
if [ ! -z "$DOC_ID" ] && [ "$DOC_ID" != "null" ]; then
    echo "📋 Test 6: DELETE /api/rag/documents/$DOC_ID"
    curl -s --max-time 5 -X DELETE "$API/documents/$DOC_ID" | jq '.'
    echo ""
else
    echo "⏭️  Skipped delete (no doc ID)"
    echo ""
fi

# Cleanup
rm -f /tmp/test-rag.txt

echo "================================"
echo "✅ Test completato!"
echo ""
echo "Verifica manualmente su: http://localhost:3000/rag"
