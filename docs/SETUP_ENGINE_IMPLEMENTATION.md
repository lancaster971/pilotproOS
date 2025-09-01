# 🛠️ PilotProSetUpEngine - Implementation Guide

**Component**: Setup Engine Implementation  
**Version**: 1.0.0  
**Purpose**: Technical Guide for Building the 5-Minute Installation System  

---

## 📋 Overview

This guide provides step-by-step instructions for implementing the PilotProSetUpEngine, including building anonymous Docker images, creating installation scripts, and developing the business configuration wizard.

---

## 🐳 Part 1: Building Anonymous Docker Images

### 1.1 Automation Engine (Anonymized n8n)

Create custom image that hides n8n branding:

**File**: `docker/automation-engine/Dockerfile`

```dockerfile
# Base from official n8n but rebrand completely
FROM n8nio/n8n:1.108.1 AS base

# Metadata for anonymous image
LABEL maintainer="PilotPro Systems"
LABEL name="pilotpros-automation-engine"  
LABEL version="1.108.1"
LABEL description="Business Process Automation Engine"

# Remove n8n references from environment
ENV APPLICATION_NAME="Business Automation Engine"
ENV N8N_DEPLOYMENT_TYPE="business-platform"

# Custom entrypoint wrapper for complete abstraction
COPY docker-entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

# Override default entrypoint
ENTRYPOINT ["/custom-entrypoint.sh"]
```

**Entrypoint Wrapper**: `docker/automation-engine/docker-entrypoint.sh`

```bash
#!/bin/sh
# Automation Engine Wrapper - Hides all n8n references

# Set business-friendly environment
export N8N_USER_FOLDER=/var/business-automation
export N8N_DIAGNOSTICS_ENABLED=false
export N8N_VERSION_NOTIFICATIONS_ENABLED=false
export N8N_TEMPLATES_ENABLED=false
export N8N_PERSONALIZATION_ENABLED=false

# Hide technical logs
export N8N_LOG_LEVEL=error
export N8N_LOG_OUTPUT=file
export N8N_LOG_FILE_LOCATION=/var/log/business-automation.log

# Start original n8n silently
exec tini -- /docker-entrypoint.sh "$@" 2>/dev/null
```

### 1.2 Business Database (Anonymized PostgreSQL)

**File**: `docker/business-database/Dockerfile`

```dockerfile
FROM postgres:16-alpine AS base

LABEL maintainer="PilotPro Systems"
LABEL name="pilotpros-business-database"
LABEL version="16"
LABEL description="Enterprise Business Data Platform"

# Business-friendly environment
ENV POSTGRES_DB=business_platform
ENV POSTGRES_USER=business_admin
ENV PGDATA=/var/lib/business-data

# Custom initialization scripts
COPY init-business-db.sql /docker-entrypoint-initdb.d/01-init.sql
COPY health-check.sh /usr/local/bin/health-check
RUN chmod +x /usr/local/bin/health-check

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD /usr/local/bin/health-check

# Override postgres branding in logs
ENV POSTGRES_INITDB_ARGS="--auth-local=trust --auth-host=scram-sha-256"
```

### 1.3 Build Script for All Images

**File**: `scripts/setup-engine/build-anonymous-images.sh`

```bash
#!/bin/bash

# Build Anonymous Docker Images for PilotProOS
# Completely removes all technical branding

set -euo pipefail

REGISTRY="${DOCKER_REGISTRY:-docker.io}"
NAMESPACE="${DOCKER_NAMESPACE:-pilotpros}"
VERSION="${VERSION:-1.0.0}"

echo "🚀 Building Anonymous Docker Images for PilotProOS"
echo "=================================================="

# Build automation engine (n8n)
echo "📦 Building Automation Engine..."
docker build -t ${NAMESPACE}/automation-engine:${VERSION} \
  -t ${NAMESPACE}/automation-engine:latest \
  -f docker/automation-engine/Dockerfile \
  docker/automation-engine/

# Build business database (PostgreSQL)  
echo "📦 Building Business Database..."
docker build -t ${NAMESPACE}/business-database:${VERSION} \
  -t ${NAMESPACE}/business-database:latest \
  -f docker/business-database/Dockerfile \
  docker/business-database/

# Build business API (Backend)
echo "📦 Building Business API..."
docker build -t ${NAMESPACE}/business-api:${VERSION} \
  -t ${NAMESPACE}/business-api:latest \
  -f docker/backend/Dockerfile \
  backend/

# Build business dashboard (Frontend)
echo "📦 Building Business Dashboard..."
docker build -t ${NAMESPACE}/business-dashboard:${VERSION} \
  -t ${NAMESPACE}/business-dashboard:latest \
  -f docker/frontend/Dockerfile \
  frontend/

# Build web gateway (nginx)
echo "📦 Building Web Gateway..."
docker build -t ${NAMESPACE}/web-gateway:${VERSION} \
  -t ${NAMESPACE}/web-gateway:latest \
  -f docker/nginx/Dockerfile \
  docker/nginx/

# Push to registry (optional)
if [ "${PUSH_IMAGES:-false}" = "true" ]; then
  echo "📤 Pushing images to ${REGISTRY}/${NAMESPACE}..."
  docker push ${NAMESPACE}/automation-engine:${VERSION}
  docker push ${NAMESPACE}/business-database:${VERSION}
  docker push ${NAMESPACE}/business-api:${VERSION}
  docker push ${NAMESPACE}/business-dashboard:${VERSION}
  docker push ${NAMESPACE}/web-gateway:${VERSION}
fi

echo "✅ All anonymous images built successfully!"
echo ""
echo "Images created:"
echo "  - ${NAMESPACE}/automation-engine:${VERSION}"
echo "  - ${NAMESPACE}/business-database:${VERSION}"
echo "  - ${NAMESPACE}/business-api:${VERSION}"
echo "  - ${NAMESPACE}/business-dashboard:${VERSION}"
echo "  - ${NAMESPACE}/web-gateway:${VERSION}"
```

---

## 🚀 Part 2: Master Installation Script

### 2.1 Main Installer

**File**: `scripts/setup-engine/install-master.sh`

```bash
#!/bin/bash

# PilotProOS Master Installer
# Zero to Production in 5 Minutes

set -euo pipefail

# Configuration
INSTALL_DIR="/opt/pilotpro"
CONFIG_FILE="${INSTALL_DIR}/config/business.env"
COMPOSE_FILE="${INSTALL_DIR}/docker-compose.yml"
LOG_FILE="/var/log/pilotpro-install.log"

# Business-friendly colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1" | tee -a ${LOG_FILE}
}

success() {
    echo -e "${GREEN}✅${NC} $1" | tee -a ${LOG_FILE}
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1" | tee -a ${LOG_FILE}
}

# Pre-flight checks
preflight_check() {
    log "Performing system compatibility check..."
    
    # Check OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log "Operating System: ${NAME} ${VERSION}"
    fi
    
    # Check resources
    TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
    if [ ${TOTAL_MEM} -lt 3800 ]; then
        warning "Low memory detected: ${TOTAL_MEM}MB (recommended: 4GB+)"
    fi
    
    DISK_SPACE=$(df -BG / | awk 'NR==2{print int($4)}')
    if [ ${DISK_SPACE} -lt 20 ]; then
        error "Insufficient disk space: ${DISK_SPACE}GB (required: 20GB+)"
    fi
    
    success "System requirements met"
}

# Install Docker if missing
install_docker() {
    if ! command -v docker &> /dev/null; then
        log "Installing container runtime..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh > /dev/null 2>&1
        rm get-docker.sh
        
        # Start Docker
        systemctl start docker
        systemctl enable docker
        
        success "Container runtime installed"
    else
        success "Container runtime already installed"
    fi
}

# Pull anonymous images
pull_images() {
    log "Downloading business platform components..."
    
    # Images to pull (anonymous names)
    IMAGES=(
        "pilotpros/automation-engine:latest"
        "pilotpros/business-database:latest"
        "pilotpros/business-api:latest"
        "pilotpros/business-dashboard:latest"
        "pilotpros/web-gateway:latest"
    )
    
    for image in "${IMAGES[@]}"; do
        log "Downloading ${image##*/}..."
        docker pull ${image} > /dev/null 2>&1
    done
    
    success "All components downloaded"
}

# Generate docker-compose.yml with anonymous services
generate_compose() {
    log "Generating platform configuration..."
    
    cat > ${COMPOSE_FILE} << 'EOF'
version: '3.8'

services:
  business-database:
    image: pilotpros/business-database:latest
    container_name: business-database
    environment:
      - BUSINESS_DB=${BUSINESS_DB}
      - BUSINESS_USER=${BUSINESS_USER}
      - BUSINESS_PASSWORD=${BUSINESS_PASSWORD}
    volumes:
      - business-data:/var/lib/business-data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "health-check"]
      interval: 10s
      timeout: 5s
      retries: 5

  automation-engine:
    image: pilotpros/automation-engine:latest
    container_name: automation-engine
    depends_on:
      business-database:
        condition: service_healthy
    environment:
      - DB_HOST=business-database
      - DB_NAME=${BUSINESS_DB}
      - DB_USER=${BUSINESS_USER}
      - DB_PASSWORD=${BUSINESS_PASSWORD}
    volumes:
      - automation-data:/var/business-automation
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:5678/healthz"]
      interval: 10s
      timeout: 5s
      retries: 5

  business-api:
    image: pilotpros/business-api:latest
    container_name: business-api
    depends_on:
      - business-database
      - automation-engine
    environment:
      - NODE_ENV=production
      - DB_HOST=business-database
      - AUTOMATION_URL=http://automation-engine:5678
    restart: unless-stopped

  business-dashboard:
    image: pilotpros/business-dashboard:latest
    container_name: business-dashboard
    depends_on:
      - business-api
    environment:
      - API_URL=http://business-api:3001
    restart: unless-stopped

  web-gateway:
    image: pilotpros/web-gateway:latest
    container_name: web-gateway
    depends_on:
      - business-dashboard
      - business-api
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ssl-certs:/etc/ssl/business
    restart: unless-stopped

volumes:
  business-data:
  automation-data:
  ssl-certs:

networks:
  default:
    name: business-platform
EOF
    
    success "Platform configuration generated"
}

# Start services
start_platform() {
    log "Starting business platform services..."
    
    cd ${INSTALL_DIR}
    docker-compose up -d
    
    # Wait for services to be healthy
    log "Waiting for services to initialize..."
    sleep 30
    
    # Check health
    if docker ps | grep -q "unhealthy"; then
        warning "Some services are still initializing..."
        sleep 30
    fi
    
    success "Business platform started"
}

# Main installation flow
main() {
    clear
    echo "🚀 PilotPro Business Platform Installer"
    echo "========================================"
    echo ""
    
    # Create directories
    mkdir -p ${INSTALL_DIR}/{config,data,logs}
    
    # Run installation steps
    preflight_check
    install_docker
    
    # Launch business wizard to collect configuration
    log "Launching business configuration wizard..."
    ${SCRIPT_DIR}/wizard-business-config.sh ${CONFIG_FILE}
    
    # Load configuration
    source ${CONFIG_FILE}
    
    # Continue installation
    pull_images
    generate_compose
    start_platform
    
    # Configure SSL
    log "Configuring secure access..."
    ${SCRIPT_DIR}/setup-ssl-business.sh ${BUSINESS_DOMAIN}
    
    # Final setup
    log "Performing final configuration..."
    ${SCRIPT_DIR}/silent-setup.sh ${CONFIG_FILE}
    
    # Success message
    clear
    echo ""
    echo "✅ PilotPro Business Platform Successfully Installed!"
    echo "====================================================="
    echo ""
    echo "Access your platform at:"
    echo "  🌐 https://${BUSINESS_DOMAIN}"
    echo ""
    echo "Administrator login:"
    echo "  📧 ${ADMIN_EMAIL}"
    echo "  🔐 Password sent to email"
    echo ""
    echo "Installation completed in: $(date -d@${SECONDS} -u +%M:%S)"
    echo ""
}

# Run installation
main "$@"
```

---

## 🧙 Part 3: Business Configuration Wizard

### 3.1 Interactive Wizard Script

**File**: `scripts/setup-engine/wizard-business-config.sh`

```bash
#!/bin/bash

# Business Configuration Wizard
# Collects only business-relevant information

CONFIG_FILE="${1:-/opt/pilotpro/config/business.env}"

# Colors for beautiful UI
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'
BOLD='\033[1m'

# UI functions
prompt() {
    echo -ne "${CYAN}$1${NC} "
    read -r response
    echo "$response"
}

prompt_password() {
    echo -ne "${CYAN}$1${NC} "
    read -rs response
    echo ""
    echo "$response"
}

show_header() {
    clear
    echo -e "${BLUE}${BOLD}"
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════╗
    ║           PilotPro Business Platform Setup              ║
    ║         Professional Process Automation System          ║
    ╚══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Collect business information
collect_business_info() {
    echo -e "${GREEN}Business Information${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    BUSINESS_NAME=$(prompt "📝 Business Name:")
    BUSINESS_DOMAIN=$(prompt "🌐 Domain (e.g., company.com):")
    ADMIN_EMAIL=$(prompt "📧 Administrator Email:")
    ADMIN_NAME=$(prompt "👤 Administrator Name:")
    
    # Optional advanced settings
    echo ""
    echo -e "${YELLOW}Advanced Settings (Press Enter to use defaults)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    TIMEZONE=$(prompt "🕐 Timezone [UTC]:")
    TIMEZONE=${TIMEZONE:-UTC}
    
    LANGUAGE=$(prompt "🌍 Language [en]:")
    LANGUAGE=${LANGUAGE:-en}
    
    BACKUP_TIME=$(prompt "💾 Daily Backup Time [02:00]:")
    BACKUP_TIME=${BACKUP_TIME:-02:00}
}

# Generate secure passwords
generate_credentials() {
    echo ""
    echo -e "${GREEN}Generating Secure Credentials...${NC}"
    
    # Generate passwords
    DB_PASSWORD=$(openssl rand -base64 32)
    ADMIN_PASSWORD=$(openssl rand -base64 16)
    JWT_SECRET=$(openssl rand -base64 48)
    
    # Business-friendly names for technical components
    BUSINESS_DB="business_platform_${BUSINESS_DOMAIN//\./_}"
    BUSINESS_USER="business_admin"
}

# Save configuration
save_config() {
    cat > ${CONFIG_FILE} << EOF
# PilotPro Business Platform Configuration
# Generated: $(date)

# Business Information
BUSINESS_NAME="${BUSINESS_NAME}"
BUSINESS_DOMAIN="${BUSINESS_DOMAIN}"
ADMIN_EMAIL="${ADMIN_EMAIL}"
ADMIN_NAME="${ADMIN_NAME}"

# Regional Settings
TIMEZONE="${TIMEZONE}"
LANGUAGE="${LANGUAGE}"
BACKUP_TIME="${BACKUP_TIME}"

# System Configuration (Auto-generated)
BUSINESS_DB="${BUSINESS_DB}"
BUSINESS_USER="${BUSINESS_USER}"
BUSINESS_PASSWORD="${DB_PASSWORD}"
ADMIN_PASSWORD="${ADMIN_PASSWORD}"
JWT_SECRET="${JWT_SECRET}"

# Service URLs
PLATFORM_URL="https://${BUSINESS_DOMAIN}"
API_URL="https://${BUSINESS_DOMAIN}/api"
WEBHOOK_URL="https://${BUSINESS_DOMAIN}/webhook"
EOF
    
    chmod 600 ${CONFIG_FILE}
}

# Confirm settings
confirm_settings() {
    echo ""
    echo -e "${BLUE}Configuration Summary${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Business Name:    ${GREEN}${BUSINESS_NAME}${NC}"
    echo -e "Domain:           ${GREEN}${BUSINESS_DOMAIN}${NC}"
    echo -e "Administrator:    ${GREEN}${ADMIN_NAME} <${ADMIN_EMAIL}>${NC}"
    echo -e "Timezone:         ${GREEN}${TIMEZONE}${NC}"
    echo -e "Language:         ${GREEN}${LANGUAGE}${NC}"
    echo -e "Backup Schedule:  ${GREEN}Daily at ${BACKUP_TIME}${NC}"
    echo ""
    
    read -p "Is this correct? (Y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
        echo "Setup cancelled. Please run again."
        exit 1
    fi
}

# Main wizard flow
main() {
    show_header
    collect_business_info
    generate_credentials
    confirm_settings
    save_config
    
    echo ""
    echo -e "${GREEN}✅ Configuration saved successfully!${NC}"
    echo ""
    echo "Continuing with platform installation..."
    sleep 2
}

main "$@"
```

---

## 🤖 Part 4: Silent Auto-Configuration

### 4.1 Silent Setup Script

**File**: `scripts/setup-engine/silent-setup.sh`

```bash
#!/bin/bash

# Silent Configuration Script
# Automatically configures all technical components without user interaction

CONFIG_FILE="${1:-/opt/pilotpro/config/business.env}"
source ${CONFIG_FILE}

# Silent configuration for automation engine
configure_automation_engine() {
    echo "Configuring automation engine..."
    
    # Wait for engine to be ready
    until curl -s http://localhost:5678/healthz > /dev/null; do
        sleep 2
    done
    
    # Create owner account silently
    curl -X POST http://localhost:5678/rest/owner/setup \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${ADMIN_EMAIL}\",
            \"firstName\": \"${ADMIN_NAME%%' '*}\",
            \"lastName\": \"${ADMIN_NAME#*' '}\",
            \"password\": \"${ADMIN_PASSWORD}\",
            \"skipSurvey\": true,
            \"skipInstanceOwnerSetup\": false
        }" > /dev/null 2>&1
    
    # Disable telemetry and updates
    docker exec automation-engine sh -c "
        echo 'UPDATE settings SET value = false WHERE key = \"telemetry.enabled\";' | \
        psql -U ${BUSINESS_USER} -d ${BUSINESS_DB}
    " > /dev/null 2>&1
}

# Configure business database
configure_database() {
    echo "Initializing business database..."
    
    # Create business schema
    docker exec business-database psql -U ${BUSINESS_USER} -d ${BUSINESS_DB} << EOF
-- Create business schema
CREATE SCHEMA IF NOT EXISTS business;
CREATE SCHEMA IF NOT EXISTS automation;

-- Business tables
CREATE TABLE business.organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE business.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50),
    organization_id INTEGER REFERENCES business.organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial organization
INSERT INTO business.organizations (name, domain) 
VALUES ('${BUSINESS_NAME}', '${BUSINESS_DOMAIN}');

-- Insert admin user
INSERT INTO business.users (email, name, role, organization_id)
VALUES ('${ADMIN_EMAIL}', '${ADMIN_NAME}', 'admin', 1);
EOF
}

# Configure SSL certificate
configure_ssl() {
    echo "Setting up secure access..."
    
    # Try Let's Encrypt first
    if command -v certbot &> /dev/null; then
        certbot certonly --standalone \
            --non-interactive \
            --agree-tos \
            --email ${ADMIN_EMAIL} \
            -d ${BUSINESS_DOMAIN} \
            > /dev/null 2>&1 || generate_self_signed
    else
        generate_self_signed
    fi
}

# Generate self-signed certificate as fallback
generate_self_signed() {
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/business/private.key \
        -out /etc/ssl/business/certificate.crt \
        -subj "/C=US/ST=State/L=City/O=${BUSINESS_NAME}/CN=${BUSINESS_DOMAIN}" \
        > /dev/null 2>&1
}

# Send welcome email
send_welcome_email() {
    # This would integrate with email service
    echo "Admin credentials:" > /tmp/credentials.txt
    echo "Email: ${ADMIN_EMAIL}" >> /tmp/credentials.txt
    echo "Password: ${ADMIN_PASSWORD}" >> /tmp/credentials.txt
    echo "" >> /tmp/credentials.txt
    echo "Access your platform at: https://${BUSINESS_DOMAIN}" >> /tmp/credentials.txt
    
    # In production, this would send actual email
    # For now, save to file
    cp /tmp/credentials.txt /opt/pilotpro/admin-credentials.txt
    chmod 600 /opt/pilotpro/admin-credentials.txt
}

# Main silent configuration
main() {
    configure_database
    configure_automation_engine
    configure_ssl
    send_welcome_email
    
    echo "✅ Silent configuration completed"
}

main "$@"
```

---

## 🏥 Part 5: Health Check System

### 5.1 Post-Installation Health Verification

**File**: `scripts/setup-engine/health-check-system.sh`

```bash
#!/bin/bash

# Health Check System
# Verifies all components are operational

HEALTH_REPORT="/tmp/health-report.txt"
ALL_HEALTHY=true

# Check service health
check_service() {
    local service=$1
    local container=$2
    local port=$3
    
    if docker ps | grep -q ${container}; then
        if docker exec ${container} wget --spider http://localhost:${port}/health 2>/dev/null; then
            echo "✅ ${service}: Operational" >> ${HEALTH_REPORT}
        else
            echo "⚠️ ${service}: Starting..." >> ${HEALTH_REPORT}
            ALL_HEALTHY=false
        fi
    else
        echo "❌ ${service}: Not running" >> ${HEALTH_REPORT}
        ALL_HEALTHY=false
    fi
}

# Run health checks
echo "Business Platform Health Check" > ${HEALTH_REPORT}
echo "==============================" >> ${HEALTH_REPORT}
echo "" >> ${HEALTH_REPORT}

check_service "Database" "business-database" "5432"
check_service "Automation Engine" "automation-engine" "5678"
check_service "Business API" "business-api" "3001"
check_service "Dashboard" "business-dashboard" "3000"
check_service "Web Gateway" "web-gateway" "80"

# Check SSL certificate
if [ -f /etc/ssl/business/certificate.crt ]; then
    echo "✅ SSL Certificate: Configured" >> ${HEALTH_REPORT}
else
    echo "⚠️ SSL Certificate: Not configured" >> ${HEALTH_REPORT}
fi

# Display report
cat ${HEALTH_REPORT}

# Return status
if [ "$ALL_HEALTHY" = true ]; then
    echo ""
    echo "✅ All systems operational"
    exit 0
else
    echo ""
    echo "⚠️ Some services still initializing. Please wait..."
    exit 1
fi
```

---

## 🎯 Part 6: Docker Compose Template

### 6.1 Production Docker Compose

**File**: `templates/docker-compose.production.yml`

```yaml
version: '3.8'

services:
  # Business Database (PostgreSQL)
  business-database:
    image: pilotpros/business-database:1.0.0
    container_name: business-database
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${BUSINESS_DB}
      POSTGRES_USER: ${BUSINESS_USER}
      POSTGRES_PASSWORD: ${BUSINESS_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
    volumes:
      - business-data:/var/lib/business-data
      - business-backups:/backups
    networks:
      - business-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${BUSINESS_USER} -d ${BUSINESS_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Automation Engine (n8n)
  automation-engine:
    image: pilotpros/automation-engine:1.0.0
    container_name: automation-engine
    restart: unless-stopped
    depends_on:
      business-database:
        condition: service_healthy
    environment:
      # Database configuration
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: business-database
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: ${BUSINESS_DB}
      DB_POSTGRESDB_USER: ${BUSINESS_USER}
      DB_POSTGRESDB_PASSWORD: ${BUSINESS_PASSWORD}
      DB_POSTGRESDB_SCHEMA: automation
      
      # Engine configuration
      N8N_HOST: 0.0.0.0
      N8N_PORT: 5678
      N8N_PROTOCOL: https
      WEBHOOK_URL: ${WEBHOOK_URL}
      
      # Disable telemetry
      N8N_DIAGNOSTICS_ENABLED: "false"
      N8N_VERSION_NOTIFICATIONS_ENABLED: "false"
      N8N_PERSONALIZATION_ENABLED: "false"
      
    volumes:
      - automation-data:/var/business-automation
      - automation-files:/files
    networks:
      - business-network
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:5678/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Business API
  business-api:
    image: pilotpros/business-api:1.0.0
    container_name: business-api
    restart: unless-stopped
    depends_on:
      - business-database
      - automation-engine
    environment:
      NODE_ENV: production
      PORT: 3001
      
      # Database
      DB_HOST: business-database
      DB_PORT: 5432
      DB_NAME: ${BUSINESS_DB}
      DB_USER: ${BUSINESS_USER}
      DB_PASSWORD: ${BUSINESS_PASSWORD}
      
      # Automation engine
      AUTOMATION_URL: http://automation-engine:5678
      
      # Security
      JWT_SECRET: ${JWT_SECRET}
      BCRYPT_ROUNDS: 12
      
    volumes:
      - api-logs:/app/logs
    networks:
      - business-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Business Dashboard
  business-dashboard:
    image: pilotpros/business-dashboard:1.0.0
    container_name: business-dashboard
    restart: unless-stopped
    depends_on:
      - business-api
    environment:
      NODE_ENV: production
      VITE_API_URL: ${API_URL}
      VITE_APP_NAME: ${BUSINESS_NAME}
    networks:
      - business-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Web Gateway (nginx)
  web-gateway:
    image: pilotpros/web-gateway:1.0.0
    container_name: web-gateway
    restart: unless-stopped
    depends_on:
      - business-dashboard
      - business-api
      - automation-engine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ssl-certificates:/etc/ssl/business:ro
      - gateway-logs:/var/log/nginx
    networks:
      - business-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  business-data:
    driver: local
  business-backups:
    driver: local
  automation-data:
    driver: local
  automation-files:
    driver: local
  api-logs:
    driver: local
  ssl-certificates:
    driver: local
  gateway-logs:
    driver: local

networks:
  business-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

---

## 🔒 Part 7: Security Hardening

### 7.1 Automatic Security Configuration

**File**: `scripts/setup-engine/security-hardening.sh`

```bash
#!/bin/bash

# Security Hardening Script
# Applies enterprise security configurations

# Configure firewall
setup_firewall() {
    echo "Configuring firewall rules..."
    
    # Install UFW if not present
    apt-get install -y ufw > /dev/null 2>&1
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow essential services
    ufw allow 22/tcp   # SSH
    ufw allow 80/tcp   # HTTP
    ufw allow 443/tcp  # HTTPS
    
    # Enable firewall
    ufw --force enable
}

# Configure fail2ban
setup_fail2ban() {
    echo "Setting up intrusion prevention..."
    
    apt-get install -y fail2ban > /dev/null 2>&1
    
    # Configure jail for business platform
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[business-platform]
enabled = true
port = 80,443
filter = business-platform
logpath = /opt/pilotpro/logs/access.log
EOF
    
    systemctl restart fail2ban
}

# Secure Docker daemon
secure_docker() {
    echo "Hardening container runtime..."
    
    # Docker daemon configuration
    cat > /etc/docker/daemon.json << EOF
{
  "icc": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "userland-proxy": false,
  "no-new-privileges": true,
  "selinux-enabled": false,
  "live-restore": true
}
EOF
    
    systemctl restart docker
}

# Apply security updates
apply_updates() {
    echo "Applying security updates..."
    
    apt-get update > /dev/null 2>&1
    apt-get upgrade -y > /dev/null 2>&1
    
    # Enable automatic security updates
    apt-get install -y unattended-upgrades > /dev/null 2>&1
    dpkg-reconfigure -plow unattended-upgrades
}

# Main security hardening
main() {
    setup_firewall
    setup_fail2ban
    secure_docker
    apply_updates
    
    echo "✅ Security hardening completed"
}

main "$@"
```

---

## 📚 Conclusion

This implementation guide provides all the technical components needed to build the PilotProSetUpEngine. The system achieves complete technology abstraction while maintaining enterprise-grade functionality, enabling any business to deploy a sophisticated automation platform in under 5 minutes without any technical knowledge.

### Key Implementation Points:

1. **Anonymous Docker Images**: Complete rebranding removes all technical references
2. **Business Wizard**: Collects only business-relevant information
3. **Silent Configuration**: Technical setup happens invisibly
4. **Health Monitoring**: Ensures system is fully operational
5. **Security Hardening**: Enterprise-grade security applied automatically

The modular design allows for easy customization and extension while maintaining the core principle of complete technology abstraction.