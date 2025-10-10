#!/bin/bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIxNTRmYzgwYy03NTdjLTRiZTEtYTYyMi1mZGYwZDZlMzUzZmMiLCJlbWFpbCI6ImFkbWluQHBpbG90cHJvcy5sb2NhbCIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTc1OTkzODMxOCwiZXhwIjoxNzYwNTQzMTE4fQ.AiKwdih-CRm2x9zgdWIAxEb3kpxDFey6MBxIGZThVqE"
WORKFLOW_ID="c5b22202-d4e2-42f2-95d7-887395682461"

echo "🧪 Test /api/business/dashboard/$WORKFLOW_ID"
curl -s -X GET "http://localhost:3001/api/business/dashboard/$WORKFLOW_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"✅ Success: {d.get('success')}\")
print(f\"   Workflow: {d.get('workflow', {}).get('name', 'N/A')}\")
print(f\"   Executions: {len(d.get('executions', []))}\")
print(f\"   Business Metrics: {d.get('businessMetrics', {}).get('operationsCount', 0)} operations\")
"
