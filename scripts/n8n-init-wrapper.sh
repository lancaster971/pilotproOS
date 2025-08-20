#!/bin/bash

# PilotProOS n8n Initialization Wrapper
# Starts n8n and automatically configures it to prevent client-visible setup

echo "🔧 PilotProOS n8n Auto-Configuration Starting..."

# Start n8n in background
n8n start &
N8N_PID=$!

# Wait for n8n to be ready
echo "⏳ Waiting for n8n to initialize..."
sleep 10

# Check if n8n is responding
attempts=0
max_attempts=30

while [ $attempts -lt $max_attempts ]; do
    if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
        echo "✅ n8n is ready"
        break
    fi
    
    attempts=$((attempts + 1))
    echo "⏳ Waiting for n8n... ($attempts/$max_attempts)"
    sleep 2
done

if [ $attempts -eq $max_attempts ]; then
    echo "❌ n8n failed to start"
    exit 1
fi

# Check if owner setup is needed
if curl -s http://localhost:5678/api/v1/owner | grep -q '"hasOwner":false'; then
    echo "🔧 Setting up owner account automatically..."
    
    # Setup owner account
    curl -s -X POST http://localhost:5678/api/v1/owner/setup \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@pilotpros.local",
            "firstName": "PilotPro", 
            "lastName": "Admin",
            "password": "pilotpros_admin_2025",
            "skipInstanceOwnerSetup": false
        }' > /dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Owner account configured automatically"
    else
        echo "⚠️ Owner account setup failed, may need manual intervention"
    fi
else
    echo "✅ Owner account already exists"
fi

echo "🚀 n8n Auto-Configuration Complete"
echo "🌐 n8n ready at: http://localhost:5678"
echo "🔒 Client will never see setup screens"

# Wait for n8n process to finish
wait $N8N_PID