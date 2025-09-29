#!/bin/bash

# 🧪 SCRIPT RAPIDO TEST MILHENA
# Esegue la suite completa di test per Milhena

echo "🧪 Avvio Test Suite Completa per Milhena..."
echo "=========================================="

# Verifica che l'Intelligence Engine sia running
echo "📋 Controllo prerequisiti..."

if ! docker ps | grep -q "pilotpros-intelligence-engine-dev"; then
    echo "❌ ERRORE: Intelligence Engine non è in running!"
    echo "   Avvia prima lo stack con: ./stack-safe.sh start"
    exit 1
fi

# Verifica che l'endpoint risponda
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ ERRORE: Endpoint Intelligence Engine non risponde!"
    echo "   Verifica che il servizio sia attivo su http://localhost:8000"
    exit 1
fi

echo "✅ Prerequisiti OK"
echo ""

# Esegue i test
echo "🚀 Esecuzione test..."
python3 test_milhena_suite_completa.py

# Controlla il risultato
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test completati!"
    echo "📊 Controlla i risultati sopra per dettagli"
else
    echo ""
    echo "❌ Test falliti!"
    echo "🔍 Controlla gli errori sopra"
    exit 1
fi