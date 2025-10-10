#!/bin/bash
# Test 10+ turn conversation without degradation

SESSION_ID="test-10-turns-$(date +%s)"
API_URL="http://localhost:8000/api/n8n/agent/customer-support"

echo "🧪 Testing 10-turn conversation - Session: $SESSION_ID"
echo "================================================"

# Array of test queries
queries=(
    "quanti workflow abbiamo in totale?"
    "quanti sono attivi?"
    "e quelli inattivi?"
    "dammi la lista dei workflow attivi"
    "qual è il primo della lista?"
    "quando è stato creato?"
    "quante esecuzioni ha avuto?"
    "ci sono stati errori recenti?"
    "mostrami le statistiche complete"
    "grazie, puoi riassumere tutto?"
)

# Execute queries
for i in "${!queries[@]}"; do
    turn=$((i+1))
    query="${queries[$i]}"

    echo ""
    echo "Turn $turn/10: $query"
    echo "---"

    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"session_id\": \"$SESSION_ID\"}" \
        --max-time 30)

    status=$(echo "$response" | jq -r '.status')
    response_text=$(echo "$response" | jq -r '.response' | head -c 200)

    if [ "$status" == "success" ]; then
        echo "✅ Success: $response_text..."
    else
        error=$(echo "$response" | jq -r '.metadata.error')
        echo "❌ Error: $error"
        exit 1
    fi

    sleep 1
done

echo ""
echo "================================================"
echo "✅ All 10 turns completed successfully!"
echo "Session ID: $SESSION_ID"
