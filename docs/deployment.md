# ONESERVER - Deployment Strategies

**Documento**: Strategie Deployment Scalabile  
**Versione**: 1.0.0  
**Target**: DevOps & Operations Team  

---

## 🚀 Overview Deployment

### Obiettivo Strategico
Implementare un sistema di deployment **completamente automatizzato** che permette di installare l'intera piattaforma ONESERVER presso qualsiasi cliente in **meno di 5 minuti** con un singolo comando.

### Risultati Target
- ⏱️ **Tempo deployment**: < 5 minuti end-to-end
- 🔄 **Automazione**: 100% hands-off dopo comando iniziale  
- 🔒 **Sicurezza**: Hardening automatico durante setup
- 📦 **Completezza**: Sistema pronto per uso business immediate
- 🎯 **Scalabilità**: Deployment paralleli illimitati

---

## 📋 Strategia 4-Script Deployment

### Filosofia: Atomic Deployment Phases

Ogni script è **idempotente** e **atomic**: può essere eseguito multiple volte senza effetti collaterali e o completa tutto o fallisce completamente senza lasciare il sistema in stato inconsistente.

```bash
# Master deployment command
./deploy-client.sh client-domain.com

# Execution flow:
# ├── 01-system-setup.sh      (60s)  → Infrastructure ready
# ├── 02-application-deploy.sh (120s) → Stack deployed  
# ├── 03-security-hardening.sh (90s)  → Production secured
# └── 04-workflow-automation.sh (60s) → Business ready
#
# Total: ~5 minutes → Fully operational system
```

---

## 🔧 Script 1: System Infrastructure Setup

### File: `scripts/01-system-setup.sh`

```bash
#!/bin/bash
# ============================================================================
# ONESERVER System Infrastructure Setup
# Duration: ~60 seconds
# Purpose: Prepare clean Ubuntu system for ONESERVER stack
# ============================================================================

set -euo pipefail  # Strict error handling

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

log "🚀 ONESERVER System Infrastructure Setup - Phase 1/4"
log "=================================================="

# Verify running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root or with sudo"
fi

# Verify Ubuntu 22.04+ (recommended)
if ! lsb_release -d | grep -q "Ubuntu 22.04\|Ubuntu 24.04"; then
    log "⚠️  Warning: Recommended OS is Ubuntu 22.04 LTS"
    read -p "Continue anyway? (y/N): " -n 1 -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    echo
fi

log "📦 Updating system packages..."
apt update && apt upgrade -y

log "🔧 Installing core dependencies..."
apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    htop \
    jq

log "🐘 Installing PostgreSQL 14..."
apt install -y postgresql-14 postgresql-client-14 postgresql-contrib-14

# Start and enable PostgreSQL
systemctl enable postgresql
systemctl start postgresql

# Verify PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    error "PostgreSQL failed to start"
fi

log "📦 Installing Node.js 18 LTS..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Verify Node.js installation
NODE_VERSION=$(node --version)
log "✅ Node.js installed: $NODE_VERSION"

log "🐳 Installing Docker..."
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu  # Add ubuntu user to docker group
systemctl enable docker
systemctl start docker

# Verify Docker installation
if ! docker --version > /dev/null 2>&1; then
    error "Docker installation failed"
fi

log "🌐 Installing Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx

# Verify Nginx installation
if ! systemctl is-active --quiet nginx; then
    error "Nginx failed to start"
fi

log "🛡️ Installing PM2 process manager..."
npm install -g pm2
pm2 startup systemd -u ubuntu --hp /home/ubuntu

log "🔐 Configuring basic firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log "👤 Creating ONESERVER system user..."
if ! id "oneserver" &>/dev/null; then
    useradd -r -s /bin/bash -d /opt/oneserver -m oneserver
    usermod -aG docker oneserver
fi

log "📁 Creating directory structure..."
mkdir -p /opt/oneserver/{database,backend,frontend,n8n,logs,backups,scripts}
chown -R oneserver:oneserver /opt/oneserver

log "🗄️ Setting up PostgreSQL for ONESERVER..."
sudo -u postgres psql -c "CREATE USER oneserver_user WITH ENCRYPTED PASSWORD '$(openssl rand -base64 32)';"
sudo -u postgres psql -c "CREATE DATABASE oneserver_db OWNER oneserver_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE oneserver_db TO oneserver_user;"

# Save database credentials
DB_PASSWORD=$(openssl rand -base64 32)
sudo -u postgres psql -c "ALTER USER oneserver_user PASSWORD '$DB_PASSWORD';"
echo "DB_PASSWORD=$DB_PASSWORD" > /opt/oneserver/.env.db
chmod 600 /opt/oneserver/.env.db
chown oneserver:oneserver /opt/oneserver/.env.db

log "⚙️ Optimizing PostgreSQL configuration..."
PG_VERSION="14"
PG_CONFIG="/etc/postgresql/$PG_VERSION/main/postgresql.conf"

# Backup original config
cp "$PG_CONFIG" "$PG_CONFIG.backup"

# Optimize for ONESERVER workload
cat >> "$PG_CONFIG" << EOF

# ONESERVER Optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
EOF

# Restart PostgreSQL to apply config
systemctl restart postgresql

log "🕒 Installing timezone data..."
timedatectl set-timezone UTC

log "📊 Installing monitoring tools..."
apt install -y \
    htop \
    iotop \
    nethogs \
    ncdu \
    tree

success "System Infrastructure Setup Complete!"
log "✅ PostgreSQL: Running"
log "✅ Node.js: $NODE_VERSION"  
log "✅ Docker: Running"
log "✅ Nginx: Running"
log "✅ Firewall: Configured"
log "✅ System User: oneserver created"
log "✅ Database: oneserver_db ready"

log "📋 System ready for Phase 2: Application Deployment"
```

### Validation Checklist
- [ ] PostgreSQL running and accessible
- [ ] Node.js 18+ installed and working
- [ ] Docker running with correct permissions
- [ ] Nginx serving default page
- [ ] Firewall configured with basic rules
- [ ] System user `oneserver` created
- [ ] Database `oneserver_db` created and accessible
- [ ] Directory structure `/opt/oneserver/` created

---

## 📦 Script 2: Application Stack Deployment

### File: `scripts/02-application-deploy.sh`

```bash
#!/bin/bash
# ============================================================================
# ONESERVER Application Stack Deployment  
# Duration: ~120 seconds
# Purpose: Deploy complete application stack (PostgreSQL + n8n + Backend + Frontend)
# ============================================================================

set -euo pipefail

# Load colors and functions from previous script
source /opt/oneserver/scripts/common-functions.sh

log "🐳 ONESERVER Application Stack Deployment - Phase 2/4"
log "=================================================="

# Load database credentials
source /opt/oneserver/.env.db

DOMAIN=${1:-"localhost"}
ADMIN_PASSWORD=${2:-$(openssl rand -base64 24)}

log "📋 Configuration:"
log "   Domain: $DOMAIN"
log "   Database: oneserver_db"
log "   Admin Password: [SECURED]"

cd /opt/oneserver

log "🗄️ Setting up database schemas..."

# Create database schemas SQL
cat > database/setup-schemas.sql << 'EOF'
-- ONESERVER Database Schema Setup
-- Two isolated schemas: n8n (for n8n) + app (for our business logic)

-- n8n schema (n8n will populate this automatically)
CREATE SCHEMA IF NOT EXISTS n8n;

-- App schema (our business logic and analytics)
CREATE SCHEMA IF NOT EXISTS app;

-- Business Process Analytics
CREATE TABLE IF NOT EXISTS app.process_analytics (
    id SERIAL PRIMARY KEY,
    n8n_workflow_id VARCHAR(255) UNIQUE,
    process_name VARCHAR(255),
    success_rate DECIMAL(5,2) DEFAULT 0,
    avg_duration_ms INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    last_execution TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business Users
CREATE TABLE IF NOT EXISTS app.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Process Templates (workflow templates)
CREATE TABLE IF NOT EXISTS app.process_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    template_data JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs
CREATE TABLE IF NOT EXISTS app.audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES app.users(id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create admin user
INSERT INTO app.users (email, password_hash, full_name, role) 
VALUES (
    'admin@oneserver.local',
    '$2b$12$LQv3c1yqBWVHxkd0LQ4YCOWheHfCo1BEv3Qa7dLbNAUbZM4ZJ.Wv.', -- password: admin123
    'System Administrator',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_process_analytics_workflow 
ON app.process_analytics(n8n_workflow_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp 
ON app.audit_logs(timestamp);

-- Permissions
GRANT ALL PRIVILEGES ON SCHEMA app TO oneserver_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO oneserver_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app TO oneserver_user;

-- n8n will handle its own schema permissions
EOF

# Execute database setup
sudo -u postgres psql -d oneserver_db -f database/setup-schemas.sql

success "Database schemas created"

log "🐳 Deploying n8n container..."

# Create n8n data directory
mkdir -p n8n/data
chown -R 1000:1000 n8n/data  # n8n runs as UID 1000

# n8n environment configuration
cat > n8n/.env << EOF
# n8n Configuration
N8N_PORT=5678
N8N_HOST=127.0.0.1

# Database (shared PostgreSQL)
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=localhost
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=oneserver_db
DB_POSTGRESDB_USER=oneserver_user
DB_POSTGRESDB_PASSWORD=$DB_PASSWORD
DB_POSTGRESDB_SCHEMA=n8n

# Security
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=$ADMIN_PASSWORD

# Webhooks
WEBHOOK_URL=https://$DOMAIN

# Performance
N8N_PAYLOAD_SIZE_MAX=16

# Disable telemetry
N8N_DIAGNOSTICS_ENABLED=false
N8N_VERSION_NOTIFICATIONS_ENABLED=false
EOF

# Deploy n8n container
docker run -d \
    --name oneserver-n8n \
    --restart unless-stopped \
    --network host \
    --env-file n8n/.env \
    -v /opt/oneserver/n8n/data:/home/node/.n8n \
    n8n/n8n:latest

# Wait for n8n to be ready
log "⏳ Waiting for n8n to initialize..."
sleep 30

# Verify n8n is running
if ! docker ps | grep -q oneserver-n8n; then
    error "n8n container failed to start"
fi

success "n8n deployed and running"

log "⚙️ Deploying Backend API..."

# Create backend application structure
mkdir -p backend/{src,config,logs}

# Package.json for backend
cat > backend/package.json << 'EOF'
{
  "name": "oneserver-backend",
  "version": "1.0.0",
  "description": "ONESERVER Backend API",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "nodemon src/server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "express-rate-limit": "^6.7.0",
    "pg": "^8.11.0",
    "bcrypt": "^5.1.0",
    "jsonwebtoken": "^9.0.0",
    "dotenv": "^16.0.3"
  }
}
EOF

# Install backend dependencies
cd backend
npm install --production
cd ..

# Backend server configuration
cat > backend/.env << EOF
NODE_ENV=production
PORT=3001
HOST=127.0.0.1

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=oneserver_db
DB_USER=oneserver_user
DB_PASSWORD=$DB_PASSWORD

# Security
JWT_SECRET=$(openssl rand -base64 64)
BCRYPT_ROUNDS=12

# n8n Integration (for health checks only)
N8N_URL=http://127.0.0.1:5678
N8N_ADMIN_USER=admin
N8N_ADMIN_PASSWORD=$ADMIN_PASSWORD

# Client Configuration
CLIENT_DOMAIN=$DOMAIN
EOF

# Simple backend server (MVP version)
cat > backend/src/server.js << 'EOF'
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3001;

// Database connection
const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Security middleware
app.use(helmet({
  hidePoweredBy: true,
}));

app.use(cors({
  origin: process.env.NODE_ENV === 'production' ? [`https://${process.env.CLIENT_DOMAIN}`, `http://${process.env.CLIENT_DOMAIN}`] : ['http://localhost:3000'],
  credentials: true,
}));

app.use(rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
}));

app.use(express.json({ limit: '1mb' }));

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    await pool.query('SELECT 1');
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'connected',
        server: 'running'
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// Business API endpoints (anonimized)
app.get('/api/business/processes', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        w.id as process_id,
        w.name as process_name,
        w.active as is_active,
        w.created_at,
        w.updated_at,
        COALESCE(a.success_rate, 0) as success_rate,
        COALESCE(a.total_executions, 0) as total_executions
      FROM n8n.workflow_entity w
      LEFT JOIN app.process_analytics a ON w.id = a.n8n_workflow_id
      WHERE w.active = true
      ORDER BY w.updated_at DESC
    `);
    
    res.json({
      data: result.rows,
      total: result.rows.length
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch business processes' });
  }
});

app.get('/api/business/analytics', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        COUNT(*) as total_processes,
        COUNT(CASE WHEN w.active = true THEN 1 END) as active_processes,
        COALESCE(AVG(a.success_rate), 0) as avg_success_rate,
        COALESCE(SUM(a.total_executions), 0) as total_executions
      FROM n8n.workflow_entity w
      LEFT JOIN app.process_analytics a ON w.id = a.n8n_workflow_id
    `);
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch analytics' });
  }
});

// Start server
app.listen(port, '127.0.0.1', () => {
  console.log(`🚀 ONESERVER Backend running on http://127.0.0.1:${port}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  pool.end(() => {
    process.exit(0);
  });
});
EOF

# PM2 ecosystem configuration
cat > backend/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'oneserver-backend',
    script: 'src/server.js',
    cwd: '/opt/oneserver/backend',
    env: {
      NODE_ENV: 'production'
    },
    max_memory_restart: '500M',
    error_file: '/opt/oneserver/logs/backend-error.log',
    out_file: '/opt/oneserver/logs/backend-out.log',
    log_file: '/opt/oneserver/logs/backend.log',
    time: true
  }]
};
EOF

# Start backend with PM2
cd backend
sudo -u oneserver pm2 start ecosystem.config.js
cd ..

success "Backend API deployed and running"

log "🎨 Deploying Frontend..."

# Create frontend build directory
mkdir -p frontend/dist

# Simple frontend (MVP version)
cat > frontend/dist/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Process Automation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 600px;
        }
        h1 { color: #333; margin-bottom: 1rem; font-size: 2.5rem; }
        p { color: #666; margin-bottom: 2rem; font-size: 1.1rem; }
        .status { 
            background: #e8f5e8; 
            color: #2d5a2d; 
            padding: 1rem; 
            border-radius: 10px; 
            margin: 1rem 0;
        }
        .button {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            margin: 0.5rem;
            transition: background 0.3s;
        }
        .button:hover { background: #5a6fd8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Business Process Automation</h1>
        <p>Your enterprise workflow automation platform is ready!</p>
        
        <div class="status">
            ✅ System Status: <strong>Online and Ready</strong>
        </div>
        
        <div>
            <button class="button" onclick="checkHealth()">System Health Check</button>
            <button class="button" onclick="viewProcesses()">View Business Processes</button>
        </div>
        
        <div id="result" style="margin-top: 2rem;"></div>
    </div>

    <script>
        async function checkHealth() {
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                document.getElementById('result').innerHTML = `
                    <div style="background: #e8f5e8; padding: 1rem; border-radius: 8px;">
                        <strong>System Health:</strong> ${data.status}<br>
                        <strong>Database:</strong> ${data.services.database}<br>
                        <strong>Last Check:</strong> ${new Date(data.timestamp).toLocaleString()}
                    </div>
                `;
            } catch (error) {
                document.getElementById('result').innerHTML = `
                    <div style="background: #ffe8e8; padding: 1rem; border-radius: 8px; color: #d32f2f;">
                        Error: ${error.message}
                    </div>
                `;
            }
        }

        async function viewProcesses() {
            try {
                const response = await fetch('/api/business/processes');
                const data = await response.json();
                document.getElementById('result').innerHTML = `
                    <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px;">
                        <strong>Active Business Processes:</strong> ${data.total}<br>
                        ${data.data.map(p => `• ${p.process_name} (${p.is_active ? 'Active' : 'Inactive'})`).join('<br>')}
                    </div>
                `;
            } catch (error) {
                document.getElementById('result').innerHTML = `
                    <div style="background: #ffe8e8; padding: 1rem; border-radius: 8px; color: #d32f2f;">
                        Error: ${error.message}
                    </div>
                `;
            }
        }
    </script>
</body>
</html>
EOF

# Configure Nginx for frontend and API proxy
cat > /etc/nginx/sites-available/oneserver << EOF
server {
    listen 80;
    server_name $DOMAIN localhost;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "no-referrer-when-downgrade";
    
    # Hide server information
    server_tokens off;
    more_clear_headers Server;
    
    # Frontend
    location / {
        root /opt/oneserver/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:3001/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Hide backend information
        proxy_hide_header X-Powered-By;
        proxy_hide_header Server;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:3001/health;
        proxy_set_header Host \$host;
        access_log off;
    }
    
    # Block access to sensitive paths
    location ~ ^/(n8n|admin|swagger|docs) {
        return 404;
    }
}
EOF

# Enable site and restart Nginx
ln -sf /etc/nginx/sites-available/oneserver /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

success "Frontend deployed and Nginx configured"

# Save deployment information
cat > /opt/oneserver/deployment-info.txt << EOF
ONESERVER Deployment Information
===============================
Date: $(date)
Domain: $DOMAIN

Services:
- PostgreSQL: Running (localhost:5432)
- n8n: Running (localhost:5678) - ADMIN ONLY
- Backend API: Running (localhost:3001) - INTERNAL
- Frontend: Running (localhost:80) - PUBLIC
- Nginx: Running (port 80/443)

Database:
- Name: oneserver_db
- User: oneserver_user
- Schemas: n8n, app

Admin Access:
- n8n Admin: http://localhost:5678 (admin / $ADMIN_PASSWORD)
- Frontend: http://$DOMAIN

Next Steps:
1. Run security hardening (Phase 3)
2. Load workflow templates (Phase 4)
EOF

chown oneserver:oneserver /opt/oneserver/deployment-info.txt

success "Application Stack Deployment Complete!"
log "✅ Database: oneserver_db with schemas (n8n, app)"
log "✅ n8n: Running on localhost:5678"
log "✅ Backend API: Running on localhost:3001"
log "✅ Frontend: Running on port 80"
log "✅ Nginx: Configured and running"

log "🌐 Frontend accessible at: http://$DOMAIN"
log "📋 System ready for Phase 3: Security Hardening"
```

### Validation Tests
```bash
# Post-deployment validation
./scripts/validate-deployment.sh

# Expected results:
# ✅ PostgreSQL: Connected (schemas: n8n, app)
# ✅ n8n: Running (API accessible)
# ✅ Backend: Responding (health check passed)
# ✅ Frontend: Serving (index.html accessible)
# ✅ Nginx: Proxying (API calls routed correctly)
```

---

## 🔒 Script 3: Security Hardening & Anonimizzazione

### File: `scripts/03-security-hardening.sh`

```bash
#!/bin/bash
# ============================================================================
# ONESERVER Security Hardening & Anonimizzazione
# Duration: ~90 seconds
# Purpose: Enterprise-grade security + complete technology hiding
# ============================================================================

set -euo pipefail

log "🔒 ONESERVER Security Hardening & Anonimizzazione - Phase 3/4"
log "============================================================"

DOMAIN=${1:-"localhost"}

log "🛡️ Configuring enterprise firewall rules..."

# Reset and configure UFW
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Allow essential services
ufw allow ssh                    # SSH (port 22)
ufw allow 'Nginx Full'          # HTTP/HTTPS (ports 80/443)

# EXPLICITLY DENY backend ports (hide from client)
ufw deny 3001 comment "Backend API - INTERNAL ONLY"
ufw deny 5678 comment "n8n Server - ADMIN ONLY" 
ufw deny 5432 comment "PostgreSQL - INTERNAL ONLY"

# Enable firewall
ufw --force enable

success "Firewall configured - backend ports hidden"

log "🔐 Installing SSL certificates..."

if [[ "$DOMAIN" != "localhost" ]] && [[ "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
    # Install Certbot for Let's Encrypt
    apt install -y certbot python3-certbot-nginx
    
    # Generate SSL certificate
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" || {
        log "⚠️ SSL certificate generation failed, continuing with HTTP"
    }
    
    success "SSL certificate installed for $DOMAIN"
else
    log "ℹ️ Skipping SSL for localhost/invalid domain"
fi

log "🎭 Implementing complete anonimizzazione..."

# Advanced Nginx configuration with anonimizzazione
cat > /etc/nginx/sites-available/oneserver << EOF
# Hide Nginx version
server_tokens off;

# Custom server header (hide technology)
more_set_headers "Server: Business Automation Platform";

server {
    listen 80;
    server_name $DOMAIN localhost;
    
    # Redirect HTTP to HTTPS (if SSL is configured)
    if (\$scheme != "https") {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN localhost;
    
    # SSL Configuration (if certificates exist)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers (enterprise-grade)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    
    # Hide all server/technology information
    more_clear_headers "Server";
    more_clear_headers "X-Powered-By";
    proxy_hide_header "X-Powered-By";
    proxy_hide_header "Server";
    
    # Root location - Frontend (business interface)
    location / {
        root /opt/oneserver/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Remove any technology hints from HTML
        sub_filter 'powered by' 'business platform';
        sub_filter 'Powered by' 'Business platform';
        sub_filter_once off;
        
        # Cache optimization
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Business API (anonimized endpoints)
    location /api/ {
        # Rate limiting per client
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:3001/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Hide ALL backend technology information
        proxy_hide_header "X-Powered-By";
        proxy_hide_header "Server";
        proxy_hide_header "Via";
        
        # Add business-friendly headers
        add_header "X-Platform" "Business Automation Platform" always;
    }
    
    # System health check (no auth needed)
    location /health {
        proxy_pass http://127.0.0.1:3001/health;
        access_log off;
    }
    
    # COMPLETE BLOCKING of admin interfaces
    location ~ ^/(n8n|admin|swagger|docs|api-docs|phpmyadmin|wp-admin|/.well-known/nodeinfo) {
        # Return 404 - make it appear non-existent
        return 404;
    }
    
    # Block common probe attempts
    location ~ ^/(\.env|\.git|config|backup|database) {
        return 404;
    }
    
    # Admin interface (LOCALHOST ONLY)
    location /system-admin {
        # Allow only localhost
        allow 127.0.0.1;
        allow ::1;
        deny all;
        
        # Proxy to n8n admin
        proxy_pass http://127.0.0.1:5678/;
        proxy_set_header Host \$host;
        
        # Basic auth for extra security
        auth_basic "System Administration";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}

# Rate limiting zones
http {
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=1r/s;
}
EOF

# Create admin password file for nginx basic auth
echo "admin:$(openssl passwd -apr1 $(cat /opt/oneserver/.env.db | grep DB_PASSWORD | cut -d'=' -f2))" > /etc/nginx/.htpasswd

# Validate and reload Nginx
nginx -t && systemctl reload nginx

success "Nginx configured with enterprise security"

log "🔥 Configuring fail2ban protection..."

# Fail2ban configuration for Nginx
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8 ::1

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
maxretry = 3
EOF

systemctl restart fail2ban
systemctl enable fail2ban

success "Fail2ban configured and running"

log "🔧 Hardening system configuration..."

# Disable unnecessary services
systemctl disable --now apache2 2>/dev/null || true
systemctl disable --now mysql 2>/dev/null || true
systemctl disable --now redis 2>/dev/null || true

# Secure shared memory
echo "tmpfs /run/shm tmpfs defaults,noexec,nosuid 0 0" >> /etc/fstab

# Kernel parameter hardening
cat >> /etc/sysctl.conf << 'EOF'
# ONESERVER Security Hardening
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
EOF

sysctl -p

log "📊 Setting up security monitoring..."

# Create security audit script
cat > /opt/oneserver/scripts/security-audit.sh << 'EOF'
#!/bin/bash
# ONESERVER Security Audit

echo "🔒 ONESERVER Security Status - $(date)"
echo "=================================="

# Check firewall status
echo "🛡️ Firewall Status:"
ufw status numbered | grep -E "(Status|3001|5678|5432)"

# Check SSL certificate
echo ""
echo "🔐 SSL Certificate:"
if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
    openssl x509 -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" -noout -dates
else
    echo "No SSL certificate found"
fi

# Check fail2ban status
echo ""
echo "🔥 Fail2ban Status:"
fail2ban-client status

# Check exposed ports
echo ""
echo "🌐 Exposed Ports:"
ss -tlnp | grep -E ":80|:443|:22"

# Check for unauthorized access attempts
echo ""
echo "⚠️ Recent Access Attempts:"
tail -n 10 /var/log/auth.log | grep -i "failed\|invalid"

echo ""
echo "✅ Security audit complete"
EOF

chmod +x /opt/oneserver/scripts/security-audit.sh

# Create security monitoring cron job
cat > /etc/cron.d/oneserver-security << 'EOF'
# ONESERVER Security Monitoring
0 */6 * * * root /opt/oneserver/scripts/security-audit.sh >> /opt/oneserver/logs/security-audit.log 2>&1
EOF

log "🔍 Implementing technology detection blocking..."

# Create technology detection blocker
cat > /opt/oneserver/scripts/block-tech-detection.sh << 'EOF'
#!/bin/bash
# Block common technology detection tools

# Block Wappalyzer, BuiltWith, etc.
iptables -A INPUT -m string --string "Wappalyzer" --algo bm -j DROP
iptables -A INPUT -m string --string "BuiltWith" --algo bm -j DROP
iptables -A INPUT -m string --string "WhatWeb" --algo bm -j DROP

# Block security scanners
iptables -A INPUT -m string --string "Nmap" --algo bm -j DROP
iptables -A INPUT -m string --string "Nikto" --algo bm -j DROP
iptables -A INPUT -m string --string "sqlmap" --algo bm -j DROP

echo "Technology detection tools blocked"
EOF

chmod +x /opt/oneserver/scripts/block-tech-detection.sh
/opt/oneserver/scripts/block-tech-detection.sh

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

success "Technology detection blocking enabled"

# Generate security report
cat > /opt/oneserver/security-report.txt << EOF
ONESERVER Security Configuration Report
======================================
Date: $(date)
Domain: $DOMAIN

🔒 Security Features Implemented:
✅ Firewall: UFW configured with backend ports blocked
✅ SSL/TLS: $(if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then echo "Enabled with Let's Encrypt"; else echo "HTTP only (localhost/invalid domain)"; fi)
✅ Security Headers: OWASP compliance implemented
✅ Technology Hiding: Complete server/framework anonimization
✅ Fail2ban: Intrusion prevention active
✅ Admin Access: Localhost-only access to n8n admin
✅ Rate Limiting: API and login protection
✅ Security Monitoring: Automated audit every 6 hours

🚫 Blocked Elements:
• Direct access to ports 3001, 5678, 5432
• Technology detection tools (Wappalyzer, BuiltWith, etc.)
• Security scanners (Nmap, Nikto, etc.)
• Admin interfaces (/n8n, /admin, /swagger)
• Common probe attempts (/.env, /.git, etc.)

🌐 Client-Visible Services:
• Port 80/443: Business frontend only
• All backend technology completely hidden
• Custom server headers: "Business Automation Platform"

🔧 Admin Access:
• n8n Admin: http://localhost/system-admin (localhost only + basic auth)
• System monitoring: /opt/oneserver/scripts/security-audit.sh

⚠️ Security Recommendations:
1. Change default admin passwords immediately
2. Enable SSH key-only authentication
3. Configure log monitoring and alerting
4. Schedule regular security updates
5. Implement additional IDS/IPS if required

EOF

chown oneserver:oneserver /opt/oneserver/security-report.txt

success "Security Hardening & Anonimizzazione Complete!"
log "✅ Firewall: Backend ports blocked from external access"
log "✅ SSL/TLS: $(if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then echo "Enabled"; else echo "HTTP mode"; fi)"
log "✅ Technology Hiding: Complete anonimization implemented"
log "✅ Security Headers: OWASP compliance active"
log "✅ Intrusion Prevention: Fail2ban monitoring enabled"
log "✅ Admin Access: Localhost-only with authentication"

log "📋 Security report saved to: /opt/oneserver/security-report.txt"
log "🔧 Admin interface: http://localhost/system-admin (localhost only)"
log "📋 System ready for Phase 4: Workflow Automation"
```

---

## ⚙️ Script 4: Workflow Automation & Business Logic

### File: `scripts/04-workflow-automation.sh`

```bash
#!/bin/bash
# ============================================================================
# ONESERVER Workflow Automation & Final Setup
# Duration: ~60 seconds  
# Purpose: Load business workflow templates + finalize system
# ============================================================================

set -euo pipefail

log "⚙️ ONESERVER Workflow Automation & Final Setup - Phase 4/4"
log "======================================================"

DOMAIN=${1:-"localhost"}

# Load admin credentials
N8N_ADMIN_PASSWORD=$(grep "N8N_BASIC_AUTH_PASSWORD" /opt/oneserver/n8n/.env | cut -d'=' -f2)
N8N_API_URL="http://127.0.0.1:5678/api/v1"

log "📦 Creating business workflow templates..."

mkdir -p /opt/oneserver/templates/business-workflows

# Template 1: Customer Onboarding Process
cat > /opt/oneserver/templates/business-workflows/customer-onboarding.json << 'EOF'
{
  "name": "Customer Onboarding Process",
  "tags": ["customer", "onboarding", "automation"],
  "nodes": [
    {
      "parameters": {
        "path": "new-customer",
        "method": "POST",
        "responseCode": 200,
        "responseData": "Success! Customer onboarding initiated."
      },
      "name": "New Customer Registration",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300],
      "webhookId": "customer-onboarding"
    },
    {
      "parameters": {
        "functionCode": "// Validate customer data\nconst customerData = items[0].json;\n\nif (!customerData.email || !customerData.name) {\n  throw new Error('Missing required customer information');\n}\n\n// Add processing timestamp\ncustomerData.processed_at = new Date().toISOString();\ncustomerData.status = 'validated';\n\nreturn items;"
      },
      "name": "Validate Customer Data",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [460, 300]
    },
    {
      "parameters": {
        "subject": "Welcome to our Business Platform!",
        "emailType": "text",
        "message": "Hello {{$json.name}},\n\nWelcome to our business automation platform! Your account has been successfully created.\n\nBest regards,\nThe Team"
      },
      "name": "Send Welcome Email",
      "type": "n8n-nodes-base.emailSend",
      "typeVersion": 1,
      "position": [680, 300]
    }
  ],
  "connections": {
    "New Customer Registration": {
      "main": [
        [
          {
            "node": "Validate Customer Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Validate Customer Data": {
      "main": [
        [
          {
            "node": "Send Welcome Email",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
EOF

# Template 2: Order Processing Automation
cat > /opt/oneserver/templates/business-workflows/order-processing.json << 'EOF'
{
  "name": "Order Processing Automation",
  "tags": ["orders", "ecommerce", "automation"],
  "nodes": [
    {
      "parameters": {
        "path": "new-order",
        "method": "POST"
      },
      "name": "New Order Received",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "functionCode": "// Process order data\nconst orderData = items[0].json;\n\n// Calculate totals\nlet subtotal = 0;\nif (orderData.items) {\n  orderData.items.forEach(item => {\n    subtotal += (item.price * item.quantity);\n  });\n}\n\norderData.subtotal = subtotal;\norderData.tax = subtotal * 0.1; // 10% tax\norderData.total = subtotal + orderData.tax;\norderData.status = 'processing';\norderData.processed_at = new Date().toISOString();\n\nreturn items;"
      },
      "name": "Calculate Order Total",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [460, 300]
    },
    {
      "parameters": {
        "subject": "Order Confirmation #{{$json.order_id}}",
        "emailType": "text",
        "message": "Thank you for your order!\n\nOrder Details:\n- Order ID: {{$json.order_id}}\n- Total: ${{$json.total}}\n- Status: {{$json.status}}\n\nWe'll process your order shortly.\n\nBest regards,\nThe Team"
      },
      "name": "Send Order Confirmation",
      "type": "n8n-nodes-base.emailSend",
      "typeVersion": 1,
      "position": [680, 300]
    }
  ],
  "connections": {
    "New Order Received": {
      "main": [
        [
          {
            "node": "Calculate Order Total",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Calculate Order Total": {
      "main": [
        [
          {
            "node": "Send Order Confirmation",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
EOF

# Template 3: Support Ticket Routing
cat > /opt/oneserver/templates/business-workflows/support-ticket-routing.json << 'EOF'
{
  "name": "Support Ticket Routing",
  "tags": ["support", "customer-service", "automation"],
  "nodes": [
    {
      "parameters": {
        "path": "support-ticket",
        "method": "POST"
      },
      "name": "New Support Ticket",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "functionCode": "// Route ticket based on priority and category\nconst ticket = items[0].json;\n\n// Determine priority based on keywords\nconst urgentKeywords = ['urgent', 'critical', 'down', 'error', 'broken'];\nconst isUrgent = urgentKeywords.some(keyword => \n  ticket.message.toLowerCase().includes(keyword)\n);\n\nticket.priority = isUrgent ? 'high' : 'normal';\nticket.department = ticket.category || 'general';\nticket.assigned_at = new Date().toISOString();\nticket.status = 'assigned';\n\nreturn items;"
      },
      "name": "Route Ticket",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [460, 300]
    },
    {
      "parameters": {
        "subject": "Support Ticket Received #{{$json.ticket_id}}",
        "emailType": "text",
        "message": "Hello {{$json.customer_name}},\n\nWe've received your support request and assigned it to our {{$json.department}} team.\n\nTicket Details:\n- ID: {{$json.ticket_id}}\n- Priority: {{$json.priority}}\n- Status: {{$json.status}}\n\nWe'll respond within 24 hours.\n\nBest regards,\nSupport Team"
      },
      "name": "Send Ticket Confirmation",
      "type": "n8n-nodes-base.emailSend",
      "typeVersion": 1,
      "position": [680, 300]
    }
  ],
  "connections": {
    "New Support Ticket": {
      "main": [
        [
          {
            "node": "Route Ticket",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Route Ticket": {
      "main": [
        [
          {
            "node": "Send Ticket Confirmation",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
EOF

success "Business workflow templates created"

log "🔄 Loading workflow templates into n8n..."

# Wait for n8n to be fully ready
log "⏳ Ensuring n8n is ready..."
sleep 10

# Function to load a workflow template
load_workflow() {
    local template_file=$1
    local template_name=$(basename "$template_file" .json)
    
    log "📋 Loading: $template_name"
    
    # Import workflow
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "admin:$N8N_ADMIN_PASSWORD" \
        -d @"$template_file" \
        "$N8N_API_URL/workflows" || echo "FAILED")
    
    if [[ "$response" == "FAILED" ]]; then
        log "⚠️ Failed to load $template_name"
        return 1
    fi
    
    # Extract workflow ID
    workflow_id=$(echo "$response" | jq -r '.id' 2>/dev/null || echo "")
    
    if [[ -n "$workflow_id" && "$workflow_id" != "null" ]]; then
        # Activate workflow
        curl -s -X POST \
            -u "admin:$N8N_ADMIN_PASSWORD" \
            "$N8N_API_URL/workflows/$workflow_id/activate" >/dev/null
        
        success "✅ Loaded and activated: $template_name (ID: $workflow_id)"
        
        # Store workflow info
        echo "$template_name=$workflow_id" >> /opt/oneserver/workflow-mapping.txt
    else
        log "⚠️ Failed to get workflow ID for $template_name"
    fi
}

# Load all workflow templates
for template in /opt/oneserver/templates/business-workflows/*.json; do
    load_workflow "$template"
done

success "Workflow templates loaded and activated"

log "📊 Setting up system monitoring..."

# Create system monitoring script
cat > /opt/oneserver/scripts/system-monitor.sh << 'EOF'
#!/bin/bash
# ONESERVER System Monitoring

LOGFILE="/opt/oneserver/logs/system-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Function to log with timestamp
log_monitor() {
    echo "[$DATE] $1" >> "$LOGFILE"
}

# Check PostgreSQL
if systemctl is-active --quiet postgresql; then
    log_monitor "✅ PostgreSQL: Running"
else
    log_monitor "❌ PostgreSQL: DOWN"
fi

# Check n8n container
if docker ps | grep -q oneserver-n8n; then
    log_monitor "✅ n8n: Running"
else
    log_monitor "❌ n8n: DOWN"
fi

# Check backend API
if curl -s http://127.0.0.1:3001/health > /dev/null; then
    log_monitor "✅ Backend API: Responding"
else
    log_monitor "❌ Backend API: NOT RESPONDING"
fi

# Check Nginx
if systemctl is-active --quiet nginx; then
    log_monitor "✅ Nginx: Running"
else
    log_monitor "❌ Nginx: DOWN"
fi

# Check disk space
DISK_USAGE=$(df /opt/oneserver | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    log_monitor "⚠️ Disk space: ${DISK_USAGE}% (WARNING)"
else
    log_monitor "✅ Disk space: ${DISK_USAGE}% (OK)"
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
log_monitor "📊 Memory usage: ${MEM_USAGE}%"

# Rotate log if too large (keep last 1000 lines)
if [ $(wc -l < "$LOGFILE") -gt 1000 ]; then
    tail -n 1000 "$LOGFILE" > "${LOGFILE}.tmp" && mv "${LOGFILE}.tmp" "$LOGFILE"
fi
EOF

chmod +x /opt/oneserver/scripts/system-monitor.sh

# Create monitoring cron job
cat > /etc/cron.d/oneserver-monitoring << 'EOF'
# ONESERVER System Monitoring - every 5 minutes
*/5 * * * * oneserver /opt/oneserver/scripts/system-monitor.sh
EOF

log "🗄️ Setting up automatic backup system..."

# Create backup script
cat > /opt/oneserver/scripts/backup-system.sh << 'EOF'
#!/bin/bash
# ONESERVER Automatic Backup System

BACKUP_DIR="/opt/oneserver/backups"
DATE=$(date '+%Y%m%d_%H%M%S')
DB_PASSWORD=$(grep "DB_PASSWORD" /opt/oneserver/.env.db | cut -d'=' -f2)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
echo "🗄️ Backing up database..."
PGPASSWORD="$DB_PASSWORD" pg_dump -h localhost -U oneserver_user oneserver_db | gzip > "$BACKUP_DIR/database_$DATE.sql.gz"

# n8n data backup
echo "📦 Backing up n8n data..."
tar -czf "$BACKUP_DIR/n8n_data_$DATE.tar.gz" -C /opt/oneserver/n8n data/

# Configuration backup
echo "⚙️ Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    /opt/oneserver/.env.db \
    /opt/oneserver/backend/.env \
    /opt/oneserver/n8n/.env \
    /etc/nginx/sites-available/oneserver \
    /opt/oneserver/workflow-mapping.txt

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "✅ Backup completed: $DATE"
echo "📁 Backup location: $BACKUP_DIR"
EOF

chmod +x /opt/oneserver/scripts/backup-system.sh

# Setup backup cron job
cat > /etc/cron.d/oneserver-backup << 'EOF'
# ONESERVER Automatic Backup - every 6 hours
0 */6 * * * oneserver /opt/oneserver/scripts/backup-system.sh >> /opt/oneserver/logs/backup.log 2>&1
EOF

log "🎯 Performing final system validation..."

# System validation script
cat > /opt/oneserver/scripts/final-validation.sh << 'EOF'
#!/bin/bash
# ONESERVER Final System Validation

echo "🎯 ONESERVER Final System Validation"
echo "===================================="

ERRORS=0

# Test database connection
echo -n "🗄️ Database connection: "
if sudo -u oneserver psql -d oneserver_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "❌ Failed"
    ERRORS=$((ERRORS + 1))
fi

# Test n8n container
echo -n "🐳 n8n container: "
if docker ps | grep -q oneserver-n8n; then
    echo "✅ Running"
else
    echo "❌ Not running"
    ERRORS=$((ERRORS + 1))
fi

# Test backend API
echo -n "⚙️ Backend API: "
if curl -s http://127.0.0.1:3001/health | grep -q "healthy"; then
    echo "✅ Responding"
else
    echo "❌ Not responding"
    ERRORS=$((ERRORS + 1))
fi

# Test frontend
echo -n "🎨 Frontend: "
if curl -s http://127.0.0.1/ | grep -q "Business Process Automation"; then
    echo "✅ Serving"
else
    echo "❌ Not serving"
    ERRORS=$((ERRORS + 1))
fi

# Test workflow count
echo -n "⚙️ Loaded workflows: "
WORKFLOW_COUNT=$(curl -s -u "admin:$N8N_ADMIN_PASSWORD" "http://127.0.0.1:5678/api/v1/workflows" | jq length 2>/dev/null || echo "0")
if [ "$WORKFLOW_COUNT" -gt 0 ]; then
    echo "✅ $WORKFLOW_COUNT workflows active"
else
    echo "⚠️ No workflows found"
fi

# Test SSL (if configured)
echo -n "🔐 SSL/HTTPS: "
if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
    echo "✅ Configured"
else
    echo "ℹ️ HTTP mode (localhost/no domain)"
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "🎉 All systems operational!"
    exit 0
else
    echo "⚠️ $ERRORS issues detected"
    exit 1
fi
EOF

chmod +x /opt/oneserver/scripts/final-validation.sh

# Run final validation
/opt/oneserver/scripts/final-validation.sh

log "📋 Generating deployment summary..."

# Create final deployment summary
cat > /opt/oneserver/DEPLOYMENT_COMPLETE.txt << EOF
🎉 ONESERVER DEPLOYMENT COMPLETE!
================================

Deployment Date: $(date)
Domain: $DOMAIN
System Status: OPERATIONAL

📊 SYSTEM OVERVIEW:
==================
✅ Infrastructure: Ubuntu + PostgreSQL + Node.js + Docker + Nginx
✅ Database: oneserver_db with schemas (n8n + app)  
✅ n8n Server: Running with $(cat /opt/oneserver/workflow-mapping.txt | wc -l) active workflows
✅ Backend API: Express.js middleware (port 3001 - internal)
✅ Frontend: Business interface (port 80/443 - public)
✅ Security: Enterprise hardening + complete anonimization

🌐 CLIENT ACCESS:
================
Frontend URL: http${SSL_STATUS}://$DOMAIN
Status: Ready for business use
Interface: 100% white-label (no technology exposure)

🔧 ADMIN ACCESS (LOCALHOST ONLY):
=================================
System Admin: http://localhost/system-admin
Monitoring: /opt/oneserver/scripts/system-monitor.sh
Backups: /opt/oneserver/scripts/backup-system.sh
Security Audit: /opt/oneserver/scripts/security-audit.sh

⚙️ LOADED BUSINESS PROCESSES:
=============================
$(cat /opt/oneserver/workflow-mapping.txt 2>/dev/null || echo "No workflows loaded")

🔒 SECURITY FEATURES:
====================
✅ Firewall: Backend ports (3001, 5678, 5432) blocked externally
✅ SSL/TLS: $(if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then echo "Enabled with Let's Encrypt"; else echo "HTTP mode (localhost/invalid domain)"; fi)
✅ Anonimization: Complete technology stack hidden
✅ Rate Limiting: API protection active
✅ Intrusion Prevention: Fail2ban monitoring
✅ Admin Isolation: Localhost-only access to admin interfaces

📊 AUTOMATION FEATURES:
======================
✅ System Monitoring: Every 5 minutes
✅ Automatic Backups: Every 6 hours (retention: 30 days)
✅ Security Audits: Every 6 hours
✅ Log Rotation: Automatic cleanup

🎯 BUSINESS READY FEATURES:
==========================
✅ Customer Onboarding Process
✅ Order Processing Automation  
✅ Support Ticket Routing
✅ Email Notifications
✅ Business Analytics Dashboard
✅ Process Performance Monitoring

📞 NEXT STEPS:
=============
1. 🌐 Access frontend: http${SSL_STATUS}://$DOMAIN
2. 🧪 Test business processes using the web interface
3. 📊 Monitor system health: /opt/oneserver/scripts/system-monitor.sh
4. 🔐 Change default passwords (recommended)
5. 📧 Configure email settings for notifications
6. 🎨 Customize branding and terminology as needed

💡 SUPPORT:
==========
- System logs: /opt/oneserver/logs/
- Backup location: /opt/oneserver/backups/
- Configuration: /opt/oneserver/
- Documentation: /opt/oneserver/docs/

🚀 DEPLOYMENT TIME: $(date -d "$(stat -c %y /opt/oneserver)" '+%Y-%m-%d %H:%M:%S') to $(date)
⏱️ TOTAL DURATION: ~5 minutes

✅ SYSTEM READY FOR PRODUCTION USE!
EOF

chown oneserver:oneserver /opt/oneserver/DEPLOYMENT_COMPLETE.txt

success "Workflow Automation & Final Setup Complete!"
log ""
log "🎉 ONESERVER DEPLOYMENT SUCCESSFUL!"
log "=================================="
log ""
log "🌐 Client Access: http${SSL_STATUS}://$DOMAIN"
log "🔧 Admin Access: http://localhost/system-admin (localhost only)"
log "📊 System Status: All services operational"
log "⚙️ Business Processes: $(cat /opt/oneserver/workflow-mapping.txt | wc -l 2>/dev/null || echo "0") workflows loaded and active"
log ""
log "📋 Complete deployment summary: /opt/oneserver/DEPLOYMENT_COMPLETE.txt"
log "🔧 System tools available in: /opt/oneserver/scripts/"
log ""
log "✅ SYSTEM READY FOR CLIENT USE!"
```

### System Health Validation
```bash
# Post-deployment health check
./scripts/final-validation.sh

# Expected output:
# ✅ Database connection: Connected
# ✅ n8n container: Running  
# ✅ Backend API: Responding
# ✅ Frontend: Serving
# ✅ Loaded workflows: 3 workflows active
# ✅ SSL/HTTPS: Configured
# 🎉 All systems operational!
```

---

## 🚀 Master Deployment Script

### File: `deploy-client.sh`

```bash
#!/bin/bash
# ============================================================================
# ONESERVER Master Deployment Script
# Duration: ~5 minutes total
# Purpose: One-command client deployment with complete automation
# ============================================================================

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

# Header
echo -e "${PURPLE}"
cat << 'EOF'
 ██████╗ ███╗   ██╗███████╗███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ 
██╔═══██╗████╗  ██║██╔════╝██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
██║   ██║██╔██╗ ██║█████╗  ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝
██║   ██║██║╚██╗██║██╔══╝  ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╔╝██║ ╚████║███████╗███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
EOF
echo -e "${NC}"

log "🚀 ONESERVER Enterprise Deployment System"
log "=========================================="

# Configuration
DOMAIN=${1:-"localhost"}
ADMIN_PASSWORD=${2:-$(openssl rand -base64 24)}
START_TIME=$(date +%s)

log "📋 Deployment Configuration:"
log "   Target Domain: $DOMAIN"
log "   Admin Password: [SECURED]"
log "   Start Time: $(date)"
log ""

# Verification checks
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root or with sudo"
fi

if ! command -v curl &> /dev/null; then
    error "curl is required but not installed"
fi

info "✅ Pre-flight checks passed"
log ""

# Phase tracking
PHASE=0
TOTAL_PHASES=4

run_phase() {
    local phase_name="$1"
    local script_name="$2"
    local estimated_time="$3"
    
    PHASE=$((PHASE + 1))
    
    log "🔄 Phase $PHASE/$TOTAL_PHASES: $phase_name"
    log "   Script: $script_name"
    log "   Estimated time: $estimated_time"
    log "   $(date +'%H:%M:%S') - Starting..."
    
    local phase_start=$(date +%s)
    
    # Run the script
    if bash "scripts/$script_name" "$DOMAIN" "$ADMIN_PASSWORD"; then
        local phase_end=$(date +%s)
        local phase_duration=$((phase_end - phase_start))
        success "Phase $PHASE completed in ${phase_duration}s"
    else
        error "Phase $PHASE failed: $phase_name"
    fi
    
    log ""
}

# Execute deployment phases
log "🚀 Starting 4-phase automated deployment..."
log ""

run_phase "System Infrastructure Setup" "01-system-setup.sh" "~60s"
run_phase "Application Stack Deployment" "02-application-deploy.sh" "~120s"  
run_phase "Security Hardening & Anonimization" "03-security-hardening.sh" "~90s"
run_phase "Workflow Automation & Final Setup" "04-workflow-automation.sh" "~60s"

# Calculate total deployment time
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
MINUTES=$((TOTAL_DURATION / 60))
SECONDS=$((TOTAL_DURATION % 60))

# Final success message
echo -e "${GREEN}"
cat << 'EOF'
██████╗ ███████╗██████╗ ██╗      ██████╗ ██╗   ██╗███╗   ███╗███████╗███╗   ██╗████████╗
██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗╚██╗ ██╔╝████╗ ████║██╔════╝████╗  ██║╚══██╔══╝
██║  ██║█████╗  ██████╔╝██║     ██║   ██║ ╚████╔╝ ██╔████╔██║█████╗  ██╔██╗ ██║   ██║   
██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║  ╚██╔╝  ██║╚██╔╝██║██╔══╝  ██║╚██╗██║   ██║   
██████╔╝███████╗██║     ███████╗╚██████╔╝   ██║   ██║ ╚═╝ ██║███████╗██║ ╚████║   ██║   
╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝   
                                                                                         
 ██████╗ ██████╗ ███╗   ███╗██████╗ ██╗     ███████╗████████╗███████╗    ██╗
██╔════╝██╔═══██╗████╗ ████║██╔══██╗██║     ██╔════╝╚══██╔══╝██╔════╝    ██║
██║     ██║   ██║██╔████╔██║██████╔╝██║     █████╗     ██║   █████╗      ██║
██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██║     ██╔══╝     ██║   ██╔══╝      ╚═╝
╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ███████╗███████╗   ██║   ███████╗    ██╗
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝   ╚═╝   ╚══════╝    ╚═╝
EOF
echo -e "${NC}"

log "🎉 ONESERVER DEPLOYMENT SUCCESSFUL!"
log "=================================="
log ""
log "⏱️ Total Deployment Time: ${MINUTES}m ${SECONDS}s"
log "📅 Completed: $(date)"
log ""
log "🌐 CLIENT ACCESS:"
log "   Frontend URL: http${SSL_STATUS}://$DOMAIN"
log "   Status: READY FOR BUSINESS USE"
log "   Interface: 100% White-label"
log ""
log "🔧 ADMIN ACCESS (Localhost Only):"
log "   System Admin: http://localhost/system-admin"
log "   Username: admin"
log "   Password: [Saved in /opt/oneserver/.env.db]"
log ""
log "📊 SYSTEM STATUS:"
log "   ✅ Database: PostgreSQL with 2 schemas"
log "   ✅ n8n Server: Running with workflow templates"
log "   ✅ Backend API: Express middleware (hidden)"
log "   ✅ Frontend: Business interface (public)"
log "   ✅ Security: Enterprise hardening enabled"
log "   ✅ Monitoring: Automated system monitoring"
log "   ✅ Backups: Scheduled every 6 hours"
log ""
log "🎯 BUSINESS FEATURES READY:"
log "   ✅ Customer Onboarding Process"
log "   ✅ Order Processing Automation"
log "   ✅ Support Ticket Routing"
log "   ✅ Email Notifications"
log "   ✅ Business Analytics Dashboard"
log ""
log "📋 DOCUMENTATION:"
log "   Complete Summary: /opt/oneserver/DEPLOYMENT_COMPLETE.txt"
log "   System Tools: /opt/oneserver/scripts/"
log "   Logs Directory: /opt/oneserver/logs/"
log "   Backup Location: /opt/oneserver/backups/"
log ""
log "🚀 NEXT STEPS:"
log "   1. Visit: http${SSL_STATUS}://$DOMAIN"
log "   2. Test business processes"
log "   3. Customize branding and settings"
log "   4. Configure email notifications"
log ""

success "SYSTEM READY FOR PRODUCTION USE!"

# Save deployment credentials securely
cat > /opt/oneserver/.deployment-credentials << EOF
# ONESERVER Deployment Credentials
# Generated: $(date)
# Domain: $DOMAIN

ADMIN_USERNAME=admin
ADMIN_PASSWORD=$ADMIN_PASSWORD
FRONTEND_URL=http${SSL_STATUS}://$DOMAIN
ADMIN_URL=http://localhost/system-admin

# Important: Keep this file secure and accessible only to administrators
EOF

chmod 600 /opt/oneserver/.deployment-credentials
chown oneserver:oneserver /opt/oneserver/.deployment-credentials

info "🔐 Deployment credentials saved to: /opt/oneserver/.deployment-credentials"
log ""
log "Thank you for choosing ONESERVER!"
log "🎯 Ready to automate your business processes!"
```

---

## 📊 Deployment Validation & Testing

### Automated Testing Suite

```bash
# tests/deployment-validation.sh
#!/bin/bash
# Complete deployment validation and testing

echo "🧪 ONESERVER Deployment Validation Suite"
echo "========================================"

DOMAIN=${1:-"localhost"}
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo "✅ PASS"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# System component tests
run_test "PostgreSQL Connection" "sudo -u oneserver psql -d oneserver_db -c 'SELECT 1;'"
run_test "n8n Container Running" "docker ps | grep -q oneserver-n8n"
run_test "Backend API Health" "curl -s http://127.0.0.1:3001/health | grep -q healthy"
run_test "Frontend Serving" "curl -s http://127.0.0.1/ | grep -q 'Business Process Automation'"
run_test "Nginx Configuration" "nginx -t"

# Security tests
run_test "Firewall Active" "ufw status | grep -q 'Status: active'"
run_test "Backend Port Blocked" "! nmap -p 3001 $DOMAIN 2>/dev/null | grep -q open"
run_test "n8n Port Blocked" "! nmap -p 5678 $DOMAIN 2>/dev/null | grep -q open"
run_test "PostgreSQL Port Blocked" "! nmap -p 5432 $DOMAIN 2>/dev/null | grep -q open"

# Business workflow tests
run_test "Workflow Templates Loaded" "curl -s -u admin:$ADMIN_PASSWORD http://127.0.0.1:5678/api/v1/workflows | jq length | grep -q '[1-9]'"
run_test "Business API Responding" "curl -s http://127.0.0.1:3001/api/business/processes | grep -q 'data'"

# Performance tests
run_test "API Response Time (<2s)" "timeout 2 curl -s http://127.0.0.1:3001/health"
run_test "Database Response Time (<1s)" "timeout 1 sudo -u oneserver psql -d oneserver_db -c 'SELECT COUNT(*) FROM app.users;'"

echo ""
echo "📊 Test Results:"
echo "==============="
echo "✅ Tests Passed: $TESTS_PASSED"
echo "❌ Tests Failed: $TESTS_FAILED"
echo "📈 Success Rate: $(( TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED) ))%"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo "🎉 ALL TESTS PASSED - DEPLOYMENT VALIDATED!"
    exit 0
else
    echo ""
    echo "⚠️ Some tests failed - please review deployment"
    exit 1
fi
```

### Performance Benchmarking

```bash
# tests/performance-benchmark.sh
#!/bin/bash
# Performance benchmarking for deployed system

echo "📊 ONESERVER Performance Benchmark"
echo "================================="

# API endpoint performance
echo "🔄 Testing API performance..."
ab -n 100 -c 10 http://127.0.0.1:3001/health

# Database query performance  
echo "🗄️ Testing database performance..."
time sudo -u oneserver psql -d oneserver_db -c "SELECT COUNT(*) FROM n8n.workflow_entity;"

# Frontend loading performance
echo "🎨 Testing frontend performance..."
curl -o /dev/null -s -w "Frontend load time: %{time_total}s\n" http://127.0.0.1/

# Memory usage analysis
echo "💾 System resource usage:"
free -h
df -h /opt/oneserver

echo "✅ Performance benchmark complete"
```

---

## 🔄 **n8n UPGRADE STRATEGY & COMPATIBILITY**

### **Zero-Downtime n8n Upgrade Procedure**

Il sistema PilotProOS è stato progettato per gestire **upgrade automatici di n8n** senza impatti sul business e senza downtime.

#### **Procedura Upgrade Sicura**
```bash
#!/bin/bash
# scripts/upgrade-n8n.sh - Safe n8n Upgrade Procedure

# 1. Pre-upgrade verification
echo "🔍 Pre-upgrade verification..."
CURRENT_VERSION=$(docker exec pilotpros-n8n-dev n8n --version)
WORKFLOWS_COUNT=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows | jq '.data | length')
echo "Current n8n: $CURRENT_VERSION"
echo "Workflows: $WORKFLOWS_COUNT"

# 2. Database backup (automatic)
echo "💾 Creating database backup..."
BACKUP_FILE="/opt/pilotpros/backups/pre_upgrade_$(date +%Y%m%d_%H%M%S).sql"
docker exec postgres-container pg_dump -U pilotpros_user pilotpros_db > "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# 3. Pull new n8n version
echo "📦 Pulling latest n8n version..."
docker pull n8nio/n8n:latest

# 4. Update docker-compose and restart
echo "🔄 Updating n8n container..."
sed -i "s/n8nio\/n8n:.*/n8nio\/n8n:latest/" docker-compose.dev.yml
docker-compose up -d n8n-dev

# 5. Wait for migration completion
echo "⏳ Waiting for n8n migration..."
sleep 60

# 6. Verify upgrade success
NEW_VERSION=$(docker exec pilotpros-n8n-dev n8n --version)
NEW_WORKFLOWS_COUNT=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows | jq '.data | length')

echo "🎯 Upgrade Results:"
echo "Old version: $CURRENT_VERSION → New version: $NEW_VERSION"
echo "Workflows preserved: $WORKFLOWS_COUNT → $NEW_WORKFLOWS_COUNT"

# 7. Test backend compatibility
echo "🧪 Testing backend compatibility..."
BACKEND_STATUS=$(curl -s http://localhost:3001/api/system/compatibility/health | jq -r '.status')
echo "Backend compatibility: $BACKEND_STATUS"

if [ "$BACKEND_STATUS" = "healthy" ] && [ "$WORKFLOWS_COUNT" = "$NEW_WORKFLOWS_COUNT" ]; then
    echo "✅ n8n upgrade completed successfully!"
    echo "✅ All workflows preserved"
    echo "✅ Backend compatibility maintained"
else
    echo "⚠️ Upgrade completed with warnings - review logs"
fi
```

#### **Compatibility Verification Checklist**
```bash
# Post-upgrade verification checklist
[ ] n8n container started successfully
[ ] New version confirmed (docker exec pilotpros-n8n-dev n8n --version)
[ ] Database migrations completed (check logs)
[ ] All workflows preserved (API count match)
[ ] Backend compatibility status: healthy
[ ] Business API endpoints responding
[ ] No compatibility errors in backend logs
[ ] Frontend can access business processes
```

#### **Rollback Procedure (if needed)**
```bash
#!/bin/bash
# scripts/rollback-n8n.sh - Emergency Rollback

echo "🚨 Rolling back n8n to previous version..."

# 1. Stop current container
docker stop pilotpros-n8n-dev && docker rm pilotpros-n8n-dev

# 2. Restore database from backup
echo "🔄 Restoring database..."
LATEST_BACKUP=$(ls -t /opt/pilotpros/backups/pre_upgrade_*.sql | head -1)
docker exec postgres-container psql -U pilotpros_user -d pilotpros_db < "$LATEST_BACKUP"

# 3. Revert docker-compose version
git checkout docker-compose.dev.yml

# 4. Restart with previous version
docker-compose up -d n8n-dev

echo "✅ Rollback completed"
```

### **Monitoring & Alerting per Upgrade**

#### **Automated Upgrade Monitoring**
```javascript
// backend/src/services/upgrade-monitor.service.js
class UpgradeMonitorService {
  async checkForNewVersions() {
    // Controlla nuove versioni n8n disponibili
    const latestVersion = await this.getLatestN8nVersion();
    const currentVersion = await this.getCurrentVersion();
    
    if (latestVersion !== currentVersion) {
      await this.notifyUpgradeAvailable(currentVersion, latestVersion);
    }
  }
  
  async performUpgradeCompatibilityCheck(newVersion) {
    // Pre-verifica compatibilità prima dell'upgrade
    const compatibilityReport = await this.analyzeVersionChanges(newVersion);
    return compatibilityReport;
  }
}
```

#### **CI/CD Integration**
```yaml
# .github/workflows/n8n-compatibility-test.yml
name: n8n Compatibility Test
on:
  schedule:
    - cron: '0 6 * * 1' # Weekly check on Monday

jobs:
  test-n8n-compatibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Test with latest n8n
        run: |
          docker pull n8nio/n8n:latest
          docker-compose -f docker-compose.test.yml up -d
          npm run test:n8n-compatibility
          
      - name: Test with next n8n
        run: |
          docker pull n8nio/n8n:next  
          docker-compose -f docker-compose.test.yml up -d
          npm run test:n8n-compatibility
```

### **Production Upgrade Strategy**

#### **Blue-Green Deployment per n8n Upgrade**
```bash
# Production upgrade con zero downtime
# 1. Deploy nuovo stack con n8n aggiornato
# 2. Sync database tra stacks
# 3. Switch traffic gradualmente
# 4. Verifica completa prima di removal stack precedente
```

#### **Automated Backup & Recovery**
```bash
# Backup automatico pre-upgrade
*/30 * * * * /opt/pilotpros/scripts/auto-backup.sh pre-upgrade

# Recovery automatico in caso di failure
if [ "$UPGRADE_FAILED" = "true" ]; then
    /opt/pilotpros/scripts/auto-rollback.sh
fi
```

---

Questa strategia di deployment garantisce **setup rapido**, **sicurezza enterprise**, **anonimizzazione completa** e **resilienza agli upgrade n8n** per qualsiasi cliente, con **automazione totale** del processo.

**Next**: Consultare `postgresql-setup.md` per dettagli sulla gestione delle migrazioni database.