#!/bin/bash
# ============================================================================
# PilotProOS System Infrastructure Setup - Phase 1/4
# Duration: ~60 seconds
# Purpose: Prepare Ubuntu system for PilotProOS deployment
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

log "🔧 PilotProOS System Infrastructure Setup - Phase 1/4"
log "=================================================="

# Verify root access
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root"
fi

log "📦 Updating system packages..."
apt update && apt upgrade -y

log "🔧 Installing core dependencies..."
apt install -y \
    curl wget git unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates gnupg lsb-release \
    ufw fail2ban htop jq

log "🐘 Installing PostgreSQL 14..."
apt install -y postgresql-14 postgresql-client-14 postgresql-contrib-14
systemctl enable postgresql
systemctl start postgresql

until pg_isready -U postgres; do
  log "⏳ Waiting for PostgreSQL..."
  sleep 2
done

log "📦 Installing Node.js 18 LTS..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

NODE_VERSION=$(node --version)
log "✅ Node.js installed: $NODE_VERSION"

log "🐳 Installing Docker..."
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

log "🌐 Installing Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx

log "🛡️ Installing PM2..."
npm install -g pm2

log "👤 Creating PilotProOS system user..."
if ! id "pilotpros" &>/dev/null; then
    useradd -r -s /bin/bash -d /opt/pilotpros -m pilotpros
    usermod -aG docker pilotpros
fi

log "📁 Creating directory structure..."
mkdir -p /opt/pilotpros/{database,backend,frontend,n8n,logs,backups,scripts}
chown -R pilotpros:pilotpros /opt/pilotpros

log "🗄️ Setting up PostgreSQL for PilotProOS..."
DB_PASSWORD=$(openssl rand -base64 32)
sudo -u postgres psql -c "CREATE USER pilotpros_user WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE pilotpros_db OWNER pilotpros_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE pilotpros_db TO pilotpros_user;"

echo "DB_PASSWORD=$DB_PASSWORD" > /opt/pilotpros/.env.db
chmod 600 /opt/pilotpros/.env.db
chown pilotpros:pilotpros /opt/pilotpros/.env.db

log "🔐 Configuring basic firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

success "System Infrastructure Setup Complete!"
log "✅ PostgreSQL: Running (pilotpros_db)"
log "✅ Node.js: $NODE_VERSION"
log "✅ Docker: Running"
log "✅ Nginx: Running"
log "✅ System User: pilotpros created"
log "✅ Firewall: Basic rules configured"

log "📋 Ready for Phase 2: Application Stack Deployment"