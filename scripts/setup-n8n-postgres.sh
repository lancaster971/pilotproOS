#!/bin/bash

# PilotProOS n8n + PostgreSQL Setup Script
echo "🚀 PilotProOS n8n + PostgreSQL Setup"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

echo "📋 Checking prerequisites..."

# Check PostgreSQL
if command_exists psql || [ -f "/opt/homebrew/opt/libpq/bin/psql" ]; then
    print_status 0 "PostgreSQL client available"
    export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
else
    echo -e "${YELLOW}⚠️  Installing PostgreSQL client...${NC}"
    brew install libpq
    export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
    print_status $? "PostgreSQL client installed"
fi

# Check PostgreSQL server
if psql postgres -c "SELECT version();" >/dev/null 2>&1; then
    print_status 0 "PostgreSQL server running"
else
    echo -e "${RED}❌ PostgreSQL server not running. Please start it:${NC}"
    echo "   brew services start postgresql@16"
    exit 1
fi

# Check n8n installation
if [ -d "node_modules/n8n" ]; then
    print_status 0 "n8n installed locally"
else
    echo -e "${YELLOW}⚠️  Installing n8n locally...${NC}"
    npm install n8n
    print_status $? "n8n installed"
fi

echo ""
echo "🗄️  Setting up database..."

# Create database and user if they don't exist
DB_EXISTS=$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='pilotpros_db'")
if [ "$DB_EXISTS" != "1" ]; then
    echo "   Creating database pilotpros_db..."
    psql postgres -c "CREATE DATABASE pilotpros_db ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;"
    print_status $? "Database created"
else
    print_status 0 "Database already exists"
fi

USER_EXISTS=$(psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='pilotpros_user'")
if [ "$USER_EXISTS" != "1" ]; then
    echo "   Creating user pilotpros_user..."
    psql postgres -c "CREATE USER pilotpros_user WITH PASSWORD 'pilotpros_secure_pass_2025';"
    psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE pilotpros_db TO pilotpros_user;"
    print_status $? "User created"
else
    print_status 0 "User already exists"
fi

# Apply schema if temp_schema.sql exists
if [ -f "temp_schema.sql" ]; then
    echo "   Applying PilotProOS schema..."
    psql pilotpros_db -f temp_schema.sql >/dev/null 2>&1
    print_status $? "Schema applied"
fi

# Set proper permissions
echo "   Setting n8n schema permissions..."
psql pilotpros_db -c "
GRANT ALL PRIVILEGES ON SCHEMA n8n TO pilotpros_user;
ALTER SCHEMA n8n OWNER TO pilotpros_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA n8n GRANT ALL ON TABLES TO pilotpros_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA n8n GRANT ALL ON SEQUENCES TO pilotpros_user;
" >/dev/null 2>&1
print_status $? "Permissions set"

echo ""
echo "📁 Creating directories..."
mkdir -p logs
print_status 0 "Logs directory created"

echo ""
print_status 0 "Setup completed successfully!"

echo ""
echo "🎯 Quick Start Commands:"
echo "   npm run n8n:start     # Start n8n server"
echo "   npm run n8n:stop      # Stop n8n server"
echo "   npm run dev           # Start full development stack"
echo ""
echo "🌐 Access Points:"
echo "   n8n Editor:      http://localhost:5678"
echo "   Login:           admin / pilotpros_admin_2025"
echo "   Database:        pilotpros_db (PostgreSQL)"
echo ""
echo "📊 Database Schemas:"
echo "   n8n:             Workflow engine tables"
echo "   pilotpros:       Business application tables"
echo ""
echo -e "${GREEN}🚀 PilotProOS n8n setup complete!${NC}"