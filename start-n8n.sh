#!/bin/bash

# PilotProOS n8n Startup Script
echo "🚀 Starting PilotProOS n8n Server..."

# Add PostgreSQL client to PATH
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"

# Load n8n environment variables
source .env.n8n

# Create logs directory if it doesn't exist
mkdir -p logs

# Start n8n (without tunnel for local development)
echo "✅ Database: pilotpros_db (PostgreSQL)"
echo "✅ Schema: n8n (isolated)"
echo "✅ Port: 5678 (localhost only)"
echo "✅ Auth: admin / pilotpros_admin_2025"
echo ""
echo "🌐 n8n will be available at: http://localhost:5678"
echo ""

npx n8n start