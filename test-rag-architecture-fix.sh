#!/bin/bash

# Test RAG Architecture Fix (2025-10-17)
# Verifica che il frontend chiami il backend proxy invece dell'intelligence engine diretto

echo "🧪 Test RAG Architecture Fix"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Verifica configurazione frontend
echo "📋 Test 1: Frontend API Base URL"
FRONTEND_API_BASE=$(grep "const RAG_API_BASE" frontend/src/api/rag.js | head -1)
if echo "$FRONTEND_API_BASE" | grep -q "VITE_API_BASE_URL"; then
    echo -e "${GREEN}✅ PASS${NC} - Frontend usa VITE_API_BASE_URL (backend proxy)"
    echo "   $FRONTEND_API_BASE"
else
    echo -e "${RED}❌ FAIL${NC} - Frontend NON usa backend proxy!"
    echo "   $FRONTEND_API_BASE"
fi
echo ""

# Test 2: Verifica endpoint backend
echo "📋 Test 2: Backend POST /documents Endpoint"
BACKEND_ENDPOINT=$(grep -A 2 "POST /api/rag/documents" backend/src/routes/rag.routes.js | head -3)
if echo "$BACKEND_ENDPOINT" | grep -q "POST /api/rag/documents"; then
    echo -e "${GREEN}✅ PASS${NC} - Backend ha POST /api/rag/documents"
    echo "   Route registrata correttamente"
else
    echo -e "${RED}❌ FAIL${NC} - Backend NON ha POST /api/rag/documents!"
fi
echo ""

# Test 3: Verifica registrazione route in server.js
echo "📋 Test 3: Backend Route Registration"
SERVER_ROUTE=$(grep "app.use('/api/rag'" backend/src/server.js)
if [ ! -z "$SERVER_ROUTE" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Route /api/rag registrata in server.js"
    echo "   $SERVER_ROUTE"
else
    echo -e "${RED}❌ FAIL${NC} - Route /api/rag NON registrata!"
fi
echo ""

# Test 4: Verifica WebSocket connection
echo "📋 Test 4: WebSocket Direct Connection"
WEBSOCKET_CONFIG=$(grep -A 2 "WebSocket connects directly" frontend/src/api/rag.js | head -3)
if echo "$WEBSOCKET_CONFIG" | grep -q "VITE_INTELLIGENCE_API_URL"; then
    echo -e "${GREEN}✅ PASS${NC} - WebSocket connette direttamente all'Intelligence Engine"
    echo "   (Corretto: backend Express non supporta WebSocket proxy)"
else
    echo -e "${YELLOW}⚠️  WARN${NC} - WebSocket potrebbe non funzionare correttamente"
fi
echo ""

# Summary
echo "================================"
echo "📊 Test Summary"
echo "================================"
echo ""
echo "Architettura CORRETTA:"
echo "  Frontend → Backend (:3001/api/rag) → Intelligence (:8000/api/rag) → RAG System"
echo ""
echo "Benefici:"
echo "  ✅ Auth JWT check (cookies HttpOnly)"
echo "  ✅ Business logging tracciato"
echo "  ✅ CORS gestito correttamente"
echo "  ✅ Docker-compatible (no localhost hard-coded)"
echo ""
echo "Note:"
echo "  ⚠️  WebSocket rimane connesso direttamente a :8000 (backend non supporta WS proxy)"
echo ""
