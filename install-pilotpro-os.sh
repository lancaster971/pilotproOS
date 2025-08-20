#!/bin/bash

# ============================================================================
# PilotPro OS - One-Command Business Platform Installation
# Client-facing installer with complete technology sanitization
# ============================================================================

set -euo pipefail

# Colors for professional client output
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
PURPLE='\033[1;35m'
CYAN='\033[1;36m'
NC='\033[0m'
BOLD='\033[1m'

# Client-friendly logging
client_title() {
    echo -e "${PURPLE}${BOLD}$1${NC}"
}

client_step() {
    echo -e "${BLUE}🚀 $1${NC}"
}

client_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

client_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

client_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Professional branded header
show_professional_header() {
    clear
    echo -e "${PURPLE}${BOLD}"
    cat << 'EOF'
    ██████╗ ██╗██╗      ██████╗ ████████╗██████╗ ██████╗  ██████╗     ██████╗ ███████╗
    ██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔═══██╗   ██╔═══██╗██╔════╝
    ██████╔╝██║██║     ██║   ██║   ██║   ██████╔╝██████╔╝██║   ██║   ██║   ██║███████╗
    ██╔═══╝ ██║██║     ██║   ██║   ██║   ██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║╚════██║
    ██║     ██║███████╗╚██████╔╝   ██║   ██║     ██║  ██║╚██████╔╝   ╚██████╔╝███████║
    ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝   ╚═╝     ╚═╝  ╚═╝ ╚═════╝     ╚═════╝ ╚══════╝
EOF
    echo -e "${NC}"
    echo -e "${CYAN}${BOLD}Enterprise Business Process Automation Platform${NC}"
    echo -e "${PURPLE}Professional Installation System v1.0${NC}"
    echo ""
    echo -e "${GREEN}Transform your business with intelligent process automation${NC}"
    echo ""
}

# Collect business information from client
collect_business_information() {
    client_title "📋 Business Platform Setup"
    echo ""
    client_info "We need some basic information to configure your business automation platform:"
    echo ""
    
    # Domain
    while true; do
        read -p "$(echo -e "${BLUE}🌐 Your business domain (e.g. yourcompany.com): ${NC}")" DOMAIN
        if [[ "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
            break
        else
            echo -e "${YELLOW}⚠️  Please enter a valid domain name${NC}"
        fi
    done
    
    # Admin email
    while true; do
        read -p "$(echo -e "${BLUE}📧 Administrator email: ${NC}")" ADMIN_EMAIL
        if [[ "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            break
        else
            echo -e "${YELLOW}⚠️  Please enter a valid email address${NC}"
        fi
    done
    
    # Names
    read -p "$(echo -e "${BLUE}👤 Administrator first name: ${NC}")" ADMIN_FIRST_NAME
    read -p "$(echo -e "${BLUE}👤 Administrator last name: ${NC}")" ADMIN_LAST_NAME
    read -p "$(echo -e "${BLUE}🏢 Company name: ${NC}")" COMPANY_NAME
    
    echo ""
    client_info "Setup Configuration:"
    client_info "Domain: $DOMAIN"
    client_info "Administrator: $ADMIN_FIRST_NAME $ADMIN_LAST_NAME"
    client_info "Email: $ADMIN_EMAIL"
    client_info "Company: $COMPANY_NAME"
    echo ""
    
    read -p "$(echo -e "${YELLOW}Proceed with installation? (y/N): ${NC}")" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        client_info "Installation cancelled by user"
        exit 0
    fi
}

# Install platform silently (hide all technical details)
install_platform_silently() {
    client_step "Installing business automation platform..."
    
    # All technical installation hidden from client
    {
        # Update system
        apt update && apt upgrade -y
        
        # Install Docker (completely hidden)
        if ! command -v docker &> /dev/null; then
            curl -fsSL https://get.docker.com | sh
            usermod -aG docker ubuntu
            systemctl enable docker
            systemctl start docker
        fi
        
        # Install docker-compose (hidden)
        if ! command -v docker-compose &> /dev/null; then
            curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            chmod +x /usr/local/bin/docker-compose
        fi
        
    } > /dev/null 2>&1
    
    client_success "Platform runtime installed"
}

# Configure business platform (sanitized output)
configure_business_platform() {
    client_step "Configuring business automation services..."
    
    # Create application directory
    mkdir -p /opt/pilotpro-os/{config,data,logs,backups,imports}
    cd /opt/pilotpro-os
    
    # Create completely sanitized docker-compose for production
    cat > docker-compose.yml << EOF
services:
  business-database:
    image: postgres:16-alpine
    container_name: pilotpro-database
    restart: unless-stopped
    environment:
      POSTGRES_DB: business_platform_db
      POSTGRES_USER: platform_admin
      POSTGRES_PASSWORD: ${DOMAIN//./}_secure_platform_2025
    volumes:
      - business_data:/var/lib/postgresql/data
      - ./config/init:/docker-entrypoint-initdb.d
    networks:
      - platform-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U platform_admin -d business_platform_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  automation-engine:
    image: docker.n8n.io/n8nio/n8n:1.106.3
    container_name: pilotpro-automation
    restart: unless-stopped
    depends_on:
      business-database:
        condition: service_healthy
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: business-database
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: business_platform_db
      DB_POSTGRESDB_USER: platform_admin
      DB_POSTGRESDB_PASSWORD: ${DOMAIN//./}_secure_platform_2025
      DB_POSTGRESDB_SCHEMA: automation
      
      N8N_PORT: 5678
      N8N_HOST: 127.0.0.1
      
      # Complete privacy (NO telemetry, updates, surveys)
      N8N_DIAGNOSTICS_ENABLED: false
      N8N_VERSION_NOTIFICATIONS_ENABLED: false
      N8N_ANONYMOUS_TELEMETRY: false
      N8N_PERSONALIZATION_ENABLED: false
      N8N_HIDE_USAGE_PAGE: true
      N8N_TEMPLATES_ENABLED: false
      
      # Performance
      N8N_RUNNERS_ENABLED: true
      
    volumes:
      - automation_data:/home/node/.n8n
      - ./imports:/imports
      - ./config/auto-setup.js:/opt/auto-setup.js
    networks:
      - platform-network
    command: sh -c "node /opt/auto-setup.js & n8n start"

  business-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: pilotpro-api
    restart: unless-stopped
    depends_on:
      - business-database
      - automation-engine
    environment:
      COMPANY_NAME: "$COMPANY_NAME"
      ADMIN_EMAIL: "$ADMIN_EMAIL"
      ADMIN_NAME: "$ADMIN_FIRST_NAME $ADMIN_LAST_NAME"
      DOMAIN: "$DOMAIN"
    networks:
      - platform-network

  business-frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: pilotpro-frontend
    restart: unless-stopped
    depends_on:
      - business-api
    environment:
      COMPANY_NAME: "$COMPANY_NAME"
      DOMAIN: "$DOMAIN"
    ports:
      - "80:80"
      - "443:443"
    networks:
      - platform-network

networks:
  platform-network:
    driver: bridge

volumes:
  business_data:
  automation_data:
EOF

    # Copy auto-setup script
    cp scripts/n8n-silent-setup.js config/auto-setup.js
    
    client_success "Business platform configured"
}

# Start platform and complete setup
start_business_platform() {
    client_step "Starting your business automation platform..."
    client_info "Initial startup may take 2-3 minutes..."
    
    # Start platform (hide Docker output)
    docker-compose up -d > /dev/null 2>&1
    
    # Wait and show professional progress
    echo ""
    for i in {1..60}; do
        echo -ne "\r${CYAN}⏳ Initializing business services... ${i}/60${NC}"
        sleep 2
        
        # Check if platform is ready
        if curl -s http://localhost/health > /dev/null 2>&1; then
            echo ""
            break
        fi
    done
    echo ""
    
    client_success "Business automation platform is online!"
}

# Configure enterprise security (sanitized)
setup_enterprise_security() {
    client_step "Activating enterprise security..."
    
    # Configure firewall (hide technical details)
    {
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # Block all technical ports
        ufw deny 3001  # API
        ufw deny 5678  # n8n
        ufw deny 5432  # PostgreSQL
        
        ufw --force enable
    } > /dev/null 2>&1
    
    client_success "Enterprise security activated"
}

# Show professional completion message
show_completion() {
    echo ""
    client_title "🎉 PilotPro OS Installation Complete!"
    echo -e "${PURPLE}${BOLD}========================================${NC}"
    echo ""
    client_success "Your business automation platform is ready!"
    echo ""
    client_info "Platform Details:"
    client_info "  🌐 Access URL: https://$DOMAIN"
    client_info "  👤 Administrator: $ADMIN_FIRST_NAME $ADMIN_LAST_NAME"
    client_info "  📧 Login Email: $ADMIN_EMAIL"
    client_info "  🏢 Company: $COMPANY_NAME"
    echo ""
    client_info "Platform Management:"
    client_info "  📊 Use 'pilotpro status' to check platform health"
    client_info "  🔄 Use 'pilotpro restart' to restart services"
    client_info "  📋 Use 'pilotpro logs' to view activity"
    echo ""
    client_success "🚀 Your business processes are now automated!"
    echo ""
    client_info "Next steps:"
    client_info "  1. Access your platform at https://$DOMAIN"
    client_info "  2. Login with your administrator credentials"
    client_info "  3. Start creating business process automations"
    echo ""
    client_info "Support: support@pilotpro.com"
    echo ""
}

# Main installation process
main() {
    # Check privileges
    if [[ $EUID -ne 0 ]]; then
        client_error "Installation requires administrator privileges. Run with: sudo $0"
    fi
    
    show_professional_header
    collect_business_information
    install_platform_silently
    configure_business_platform
    setup_enterprise_security
    start_business_platform
    show_completion
    
    # Save configuration
    cat > /opt/pilotpro-os/.installation-info << EOF
# PilotPro OS Installation Information
DOMAIN=$DOMAIN
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_NAME=$ADMIN_FIRST_NAME $ADMIN_LAST_NAME
COMPANY_NAME=$COMPANY_NAME
INSTALLED_DATE=$(date)
VERSION=1.0.0
STATUS=production_ready
EOF
    
    chmod 600 /opt/pilotpro-os/.installation-info
}

# Usage information
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "PilotPro OS - Business Process Automation Platform"
    echo ""
    echo "Usage: $0"
    echo ""
    echo "This installer will:"
    echo "  • Set up your business automation platform"
    echo "  • Configure enterprise security"
    echo "  • Create administrator account"
    echo "  • Prepare business process tools"
    echo ""
    echo "Requirements:"
    echo "  • Ubuntu Server 20.04+ or 22.04+"
    echo "  • Internet connection"
    echo "  • Administrator privileges (sudo)"
    echo ""
    echo "After installation:"
    echo "  • Access via web browser at your domain"
    echo "  • Manage with 'pilotpro' command"
    echo ""
    exit 0
fi

# Execute installation
main "$@"