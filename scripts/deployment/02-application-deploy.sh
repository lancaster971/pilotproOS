#!/bin/bash
# ============================================================================
# PilotProOS Application Stack Deployment - Phase 2/4
# Duration: ~120 seconds
# Purpose: Deploy PostgreSQL + n8n + Backend + Frontend
# ============================================================================

set -euo pipefail

source /opt/pilotpros/scripts/common-functions.sh 2>/dev/null || {
    log() { echo -e "\033[0;34m[$(date +'%H:%M:%S')] $1\033[0m"; }
    success() { echo -e "\033[0;32m✅ $1\033[0m"; }
    error() { echo -e "\033[0;31m❌ $1\033[0m"; exit 1; }
}

log "🐳 PilotProOS Application Stack Deployment - Phase 2/4"
log "==================================================="

DOMAIN=${1:-"localhost"}
ADMIN_PASSWORD=${2:-$(openssl rand -base64 24)}

# Load database credentials
source /opt/pilotpros/.env.db

log "📋 Configuration:"
log "   Domain: $DOMAIN"
log "   Database: pilotpros_db"

cd /opt/pilotpros

log "🗄️ Setting up database schemas..."
sudo -u postgres psql -d pilotpros_db -f ../PilotProOS/scripts/database/pilotpros-schema.sql

success "Database schemas created (n8n, pilotpros)"

log "🔧 Deploying n8n with PostgreSQL..."

mkdir -p n8n/data
chown -R 1000:1000 n8n/data

# n8n environment configuration
cat > n8n/.env << EOF
# PostgreSQL Configuration
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=localhost
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=pilotpros_db
DB_POSTGRESDB_USER=pilotpros_user
DB_POSTGRESDB_PASSWORD=$DB_PASSWORD
DB_POSTGRESDB_SCHEMA=n8n

# n8n Server
N8N_PORT=5678
N8N_HOST=127.0.0.1
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=$ADMIN_PASSWORD

# Security
WEBHOOK_URL=https://$DOMAIN
N8N_DIAGNOSTICS_ENABLED=false
N8N_VERSION_NOTIFICATIONS_ENABLED=false
EOF

# Deploy n8n container
docker run -d \
    --name pilotpros-n8n \
    --restart unless-stopped \
    --network host \
    --env-file n8n/.env \
    -v /opt/pilotpros/n8n/data:/home/node/.n8n \
    n8n/n8n:latest

log "⏳ Waiting for n8n to initialize PostgreSQL..."
sleep 45

success "n8n deployed with PostgreSQL backend"

log "⚙️ Deploying PilotProOS Backend..."

# Copy backend from PilotProOS
cp -r ../PilotProOS/backend/ .
cd backend

# Install dependencies
npm install --production

# Backend environment
cat > .env << EOF
NODE_ENV=production
PORT=3001
HOST=127.0.0.1

# PostgreSQL (shared with n8n)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pilotpros_db
DB_USER=pilotpros_user
DB_PASSWORD=$DB_PASSWORD

# AI Agent
AI_AGENT_ENABLED=true
AI_AGENT_PORT=3002

# Security
JWT_SECRET=$(openssl rand -base64 64)
BCRYPT_ROUNDS=12

# Business Configuration
DOMAIN=$DOMAIN
COMPANY_NAME=Business Process Automation
EOF

# PM2 configuration
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'pilotpros-backend',
    script: 'src/server.js',
    cwd: '/opt/pilotpros/backend',
    env: {
      NODE_ENV: 'production'
    },
    max_memory_restart: '512M',
    error_file: '/opt/pilotpros/logs/backend-error.log',
    out_file: '/opt/pilotpros/logs/backend-out.log',
    log_file: '/opt/pilotpros/logs/backend.log',
    time: true
  }]
};
EOF

# Start backend
sudo -u pilotpros pm2 start ecosystem.config.js
cd ..

success "Backend API deployed"


log "🎨 Deploying Frontend..."

# Copy and build frontend
cp -r ../PilotProOS/frontend/ .
cd frontend

npm install
npm run build

# Copy build to web directory
cp -r dist/* /var/www/html/
cd ..

# Configure Nginx
cat > /etc/nginx/sites-available/pilotpros << EOF
server {
    listen 80;
    server_name $DOMAIN localhost;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    server_tokens off;
    
    # Frontend
    location / {
        root /var/www/html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:3001/api/;
        proxy_set_header Host \$host;
        proxy_hide_header X-Powered-By;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:3001/health;
        access_log off;
    }
    
    # Block admin interfaces
    location ~ ^/(n8n|admin|swagger) {
        return 404;
    }
}
EOF

ln -sf /etc/nginx/sites-available/pilotpros /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

success "Frontend deployed and Nginx configured"

# Save deployment info
cat > /opt/pilotpros/deployment-info.txt << EOF
PilotProOS Deployment Information
================================
Date: $(date)
Domain: $DOMAIN

Services:
- PostgreSQL: Running (localhost:5432) - pilotpros_db
- n8n: Running (localhost:5678) - PostgreSQL backend
- Backend API: Running (localhost:3001) - Business endpoints
- AI Agent: Running (localhost:3002) - Conversational interface
- Frontend: Running (port 80) - Business interface
- Nginx: Configured and proxying

Access URLs:
- Business Interface: http://$DOMAIN
- AI Assistant: Integrated in frontend
- Admin n8n: http://localhost:5678 (admin / $ADMIN_PASSWORD)

Next: Run Phase 3 (Security Hardening)
EOF

chown pilotpros:pilotpros /opt/pilotpros/deployment-info.txt

success "Application Stack Deployment Complete!"
log "✅ PostgreSQL: pilotpros_db with schemas"
log "✅ n8n: PostgreSQL backend configured"
log "✅ Backend: Business API endpoints"
log "✅ AI Agent: Conversational interface"
log "✅ Frontend: Business process interface"

log "🌐 Preview: http://$DOMAIN"
log "📋 Ready for Phase 3: Security Hardening"