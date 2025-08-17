#!/bin/bash

# PilotProOS n8n Startup Script with PostgreSQL
echo "🚀 Starting PilotProOS n8n Server with PostgreSQL..."

# Add PostgreSQL client to PATH
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"

# Set n8n environment variables directly
export DB_TYPE=postgresdb
export DB_POSTGRESDB_HOST=localhost
export DB_POSTGRESDB_PORT=5432
export DB_POSTGRESDB_DATABASE=pilotpros_db
export DB_POSTGRESDB_USER=pilotpros_user
export DB_POSTGRESDB_PASSWORD=pilotpros_secure_pass_2025
export DB_POSTGRESDB_SCHEMA=n8n
export DB_POSTGRESDB_POOL_SIZE=10
export DB_POSTGRESDB_SSL_MODE=disable

export N8N_PORT=5678
export N8N_HOST=127.0.0.1
export N8N_BASIC_AUTH_ACTIVE=true
export N8N_BASIC_AUTH_USER=admin
export N8N_BASIC_AUTH_PASSWORD=pilotpros_admin_2025

export WEBHOOK_URL=http://localhost:5678
export N8N_PAYLOAD_SIZE_MAX=16

export EXECUTIONS_TIMEOUT=300
export EXECUTIONS_TIMEOUT_MAX=3600
export EXECUTIONS_DATA_SAVE_ON_ERROR=all
export EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
export EXECUTIONS_DATA_MAX_AGE=336

export N8N_METRICS=true
export N8N_LOG_LEVEL=info
export N8N_LOG_OUTPUT=console

export N8N_DIAGNOSTICS_ENABLED=false
export N8N_VERSION_NOTIFICATIONS_ENABLED=false
export N8N_ANONYMOUS_TELEMETRY=false
export N8N_PERSONALIZATION_ENABLED=false

export N8N_SECURE_COOKIE=false
export N8N_COOKIE_SAME_SITE=strict

export N8N_DEFAULT_BINARY_DATA_MODE=filesystem
# N8N_BINARY_DATA_TTL removed - deprecated in v1.106.3

export N8N_HIDE_USAGE_PAGE=true
export N8N_TEMPLATES_ENABLED=false

# Enable task runners (new in v1.106.3)
export N8N_RUNNERS_ENABLED=true

# Create logs directory if it doesn't exist
mkdir -p logs

# Display configuration
echo "✅ Database: PostgreSQL (pilotpros_db)"
echo "✅ Schema: n8n (isolated)"
echo "✅ User: pilotpros_user"
echo "✅ Port: 5678 (localhost only)"
echo "✅ Auth: admin / pilotpros_admin_2025"
echo ""
echo "🌐 n8n will be available at: http://localhost:5678"
echo ""

# Start n8n
npx n8n start