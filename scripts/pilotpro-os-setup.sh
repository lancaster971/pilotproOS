#!/bin/bash

# ============================================================================
# PilotPro OS - Business Process Automation Platform Setup
# Complete automated installation with zero technical exposure
# ============================================================================

set -euo pipefail

# Colors for branded output
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
PURPLE='\033[1;35m'
CYAN='\033[1;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Branded logging functions
echo_title() {
    echo -e "${PURPLE}${BOLD}$1${NC}"
}

echo_step() {
    echo -e "${BLUE}🚀 $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Branded header
show_header() {
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
    echo -e "${CYAN}${BOLD}Business Process Automation Platform${NC}"
    echo -e "${PURPLE}Installation Wizard v1.0${NC}"
    echo ""
}

# Collect client information
collect_client_info() {
    echo_title "📋 Business Platform Configuration"
    echo ""
    echo_info "Please provide your business information for platform setup:"
    echo ""
    
    # Company Domain
    while true; do
        read -p "$(echo -e "${BLUE}🌐 Your business domain (e.g. yourcompany.com): ${NC}")" DOMAIN
        if [[ "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
            break
        else
            echo_warning "Please enter a valid domain (e.g. yourcompany.com)"
        fi
    done
    
    # Admin Email
    while true; do
        read -p "$(echo -e "${BLUE}📧 Administrator email: ${NC}")" ADMIN_EMAIL
        if [[ "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            break
        else
            echo_warning "Please enter a valid email address"
        fi
    done
    
    # Admin Name
    read -p "$(echo -e "${BLUE}👤 Administrator first name: ${NC}")" ADMIN_FIRST_NAME
    read -p "$(echo -e "${BLUE}👤 Administrator last name: ${NC}")" ADMIN_LAST_NAME
    
    # Company Name
    read -p "$(echo -e "${BLUE}🏢 Company name: ${NC}")" COMPANY_NAME
    
    echo ""
    echo_info "Configuration Summary:"
    echo_info "Domain: $DOMAIN"
    echo_info "Admin: $ADMIN_FIRST_NAME $ADMIN_LAST_NAME <$ADMIN_EMAIL>"
    echo_info "Company: $COMPANY_NAME"
    echo ""
    
    read -p "$(echo -e "${YELLOW}Proceed with installation? (y/N): ${NC}")" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo_info "Installation cancelled"
        exit 0
    fi
}

# Install system dependencies silently
install_dependencies() {
    echo_step "Preparing business platform environment..."
    
    # Update system (hidden output)
    apt update > /dev/null 2>&1
    
    # Install Docker if not present (hidden)
    if ! command -v docker &> /dev/null; then
        echo_info "Installing platform runtime..."
        curl -fsSL https://get.docker.com | sh > /dev/null 2>&1
        usermod -aG docker ubuntu > /dev/null 2>&1
        systemctl enable docker > /dev/null 2>&1
        systemctl start docker > /dev/null 2>&1
    fi
    
    # Install docker-compose if not present (hidden)
    if ! command -v docker-compose &> /dev/null; then
        curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose > /dev/null 2>&1
        chmod +x /usr/local/bin/docker-compose > /dev/null 2>&1
    fi
    
    echo_success "Platform environment ready"
}

# Create sanitized docker configuration
create_production_config() {
    echo_step "Configuring business automation platform..."
    
    # Create application directory
    mkdir -p /opt/pilotpro-os/{config,data,logs,backups}
    cd /opt/pilotpro-os
    
    # Create production docker-compose (completely sanitized)
    cat > docker-compose.yml << EOF
services:
  # Business Database (PostgreSQL hidden)
  business-database:
    image: postgres:16-alpine
    container_name: pilotpro-database
    restart: unless-stopped
    environment:
      POSTGRES_DB: business_platform_db
      POSTGRES_USER: platform_user
      POSTGRES_PASSWORD: ${DOMAIN//./}_secure_2025
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - business_db_data:/var/lib/postgresql/data
      - ./config/db-init:/docker-entrypoint-initdb.d
    networks:
      - business-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U platform_user -d business_platform_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Process Automation Engine (n8n hidden)
  process-engine:
    image: docker.n8n.io/n8nio/n8n:1.106.3
    container_name: pilotpro-automation
    restart: unless-stopped
    depends_on:
      business-database:
        condition: service_healthy
    environment:
      # Database connection (hidden PostgreSQL)
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: business-database
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: business_platform_db
      DB_POSTGRESDB_USER: platform_user
      DB_POSTGRESDB_PASSWORD: ${DOMAIN//./}_secure_2025
      DB_POSTGRESDB_SCHEMA: automation
      
      # Platform configuration
      N8N_PORT: 5678
      N8N_HOST: 127.0.0.1
      
      # Admin account (same as business admin)
      N8N_BASIC_AUTH_ACTIVE: false
      N8N_DISABLE_UI: false
      
      # Privacy and security (NO telemetry)
      N8N_DIAGNOSTICS_ENABLED: false
      N8N_VERSION_NOTIFICATIONS_ENABLED: false
      N8N_ANONYMOUS_TELEMETRY: false
      N8N_PERSONALIZATION_ENABLED: false
      
      # Performance
      N8N_RUNNERS_ENABLED: true
      N8N_PAYLOAD_SIZE_MAX: 16
      
    volumes:
      - automation_data:/home/node/.n8n
      - ./logs:/var/log
    networks:
      - business-network
    # NO PORTS EXPOSED (internal only)

  # Business Application API
  business-api:
    image: pilotpro/business-api:latest
    container_name: pilotpro-api
    restart: unless-stopped
    depends_on:
      business-database:
        condition: service_healthy
      process-engine:
        condition: service_started
    environment:
      NODE_ENV: production
      PORT: 3001
      
      # Database connection
      DB_HOST: business-database
      DB_PORT: 5432
      DB_NAME: business_platform_db
      DB_USER: platform_user
      DB_PASSWORD: ${DOMAIN//./}_secure_2025
      
      # Business configuration
      COMPANY_NAME: "$COMPANY_NAME"
      ADMIN_EMAIL: "$ADMIN_EMAIL"
      ADMIN_NAME: "$ADMIN_FIRST_NAME $ADMIN_LAST_NAME"
      DOMAIN: "$DOMAIN"
      
    volumes:
      - ./logs:/app/logs
    networks:
      - business-network
    # Internal only - no external ports

  # Business Web Interface  
  business-platform:
    image: pilotpro/business-frontend:latest
    container_name: pilotpro-frontend
    restart: unless-stopped
    depends_on:
      - business-api
    environment:
      COMPANY_NAME: "$COMPANY_NAME"
      API_URL: http://business-api:3001
      DOMAIN: "$DOMAIN"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx:/etc/nginx/conf.d
      - ./logs:/var/log/nginx
    networks:
      - business-network

networks:
  business-network:
    driver: bridge

volumes:
  business_db_data:
  automation_data:
EOF

    echo_success "Business platform configured"
}

# Create automatic n8n setup script
create_n8n_auto_setup() {
    echo_step "Preparing process automation engine..."
    
    # Create n8n auto-configuration script
    cat > config/auto-configure-engine.sh << EOF
#!/bin/bash

# Wait for automation engine to be ready
sleep 15

# Auto-setup owner account (completely hidden from client)
curl -s -X POST http://process-engine:5678/api/v1/owner/setup \\
    -H "Content-Type: application/json" \\
    -d '{
        "email": "$ADMIN_EMAIL",
        "firstName": "$ADMIN_FIRST_NAME", 
        "lastName": "$ADMIN_LAST_NAME",
        "password": "${DOMAIN//./}_automation_admin_2025",
        "skipInstanceOwnerSetup": false,
        "skipSurvey": true,
        "acceptTerms": true
    }' > /dev/null 2>&1

echo "Process automation engine configured"
EOF

    chmod +x config/auto-configure-engine.sh
    
    # Create database initialization for dual schema
    cat > config/db-init/01-business-platform-schema.sql << 'EOF'
-- Business Platform Database Schema
CREATE SCHEMA IF NOT EXISTS automation;
CREATE SCHEMA IF NOT EXISTS business;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA automation TO platform_user;
GRANT ALL PRIVILEGES ON SCHEMA business TO platform_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA automation TO platform_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA business TO platform_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA automation TO platform_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA business TO platform_user;

-- Cross-schema read access
GRANT USAGE ON SCHEMA automation TO platform_user;
GRANT SELECT ON ALL TABLES IN SCHEMA automation TO platform_user;
EOF

    echo_success "Process automation ready"
}

# Start platform with complete sanitization
start_platform() {
    echo_step "Starting your business automation platform..."
    echo_info "This may take a few minutes for the initial setup..."
    
    # Start all services (output hidden)
    docker-compose up -d > /dev/null 2>&1
    
    # Wait for services to be ready
    echo_info "Initializing business platform components..."
    sleep 30
    
    # Run n8n auto-setup (hidden)
    docker-compose exec -T process-engine /bin/bash /opt/setup/auto-configure-engine.sh > /dev/null 2>&1
    
    # Wait for everything to stabilize
    sleep 10
    
    echo_success "Business automation platform is ready!"
}

# Create firewall rules (sanitized)
configure_security() {
    echo_step "Activating enterprise security..."
    
    # Configure UFW (hide technical details)
    ufw --force reset > /dev/null 2>&1
    ufw default deny incoming > /dev/null 2>&1
    ufw default allow outgoing > /dev/null 2>&1
    ufw allow ssh > /dev/null 2>&1
    ufw allow 80/tcp > /dev/null 2>&1
    ufw allow 443/tcp > /dev/null 2>&1
    
    # BLOCK all technical ports from external access
    ufw deny 3001 > /dev/null 2>&1  # API port
    ufw deny 5678 > /dev/null 2>&1  # Automation engine port  
    ufw deny 5432 > /dev/null 2>&1  # Database port
    
    ufw --force enable > /dev/null 2>&1
    
    echo_success "Enterprise security active"
}

# Generate final summary
show_completion_summary() {
    echo ""
    echo_title "🎉 PilotPro OS Installation Complete!"
    echo -e "${PURPLE}${BOLD}============================================${NC}"
    echo ""
    echo_success "Your business automation platform is ready!"
    echo ""
    echo_info "Platform Access:"
    echo_info "  🌐 Web Interface: https://$DOMAIN"
    echo_info "  👤 Administrator: $ADMIN_FIRST_NAME $ADMIN_LAST_NAME"
    echo_info "  📧 Admin Email: $ADMIN_EMAIL"
    echo ""
    echo_info "What you can do now:"
    echo_info "  ✅ Access your business platform via web browser"
    echo_info "  ✅ Create and manage business processes"
    echo_info "  ✅ Monitor platform analytics and performance"
    echo_info "  ✅ Configure business automation workflows"
    echo ""
    echo_success "🚀 Your business is now automated!"
    echo ""
    echo_info "For support: support@pilotpro.com"
    echo ""
}

# Create management commands for client
create_client_commands() {
    # Create simple management commands (sanitized)
    cat > /usr/local/bin/pilotpro << 'EOF'
#!/bin/bash
# PilotPro OS Management Commands

case "$1" in
    status)
        echo "🔍 Business Platform Status:"
        if docker ps | grep -q pilotpro; then
            echo "✅ Platform: Online"
            echo "✅ Services: Running"
            echo "🌐 Access: https://$(hostname -f)"
        else
            echo "❌ Platform: Offline"
        fi
        ;;
    restart)
        echo "🔄 Restarting business platform..."
        cd /opt/pilotpro-os && docker-compose restart > /dev/null 2>&1
        echo "✅ Platform restarted"
        ;;
    logs)
        echo "📋 Platform Activity (last 50 lines):"
        cd /opt/pilotpro-os && docker-compose logs --tail=50
        ;;
    backup)
        echo "💾 Creating platform backup..."
        cd /opt/pilotpro-os && ./scripts/backup-platform.sh
        ;;
    *)
        echo "PilotPro OS Management Commands:"
        echo "  pilotpro status   - Check platform status"
        echo "  pilotpro restart  - Restart platform services"
        echo "  pilotpro logs     - View platform activity"
        echo "  pilotpro backup   - Create platform backup"
        ;;
esac
EOF

    chmod +x /usr/local/bin/pilotpro
    echo_success "Management commands installed (use 'pilotpro' command)"
}

# Main installation flow
main() {
    show_header
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        echo_error "Installation requires administrator privileges. Please run with sudo."
    fi
    
    # Check Ubuntu compatibility
    if ! lsb_release -d 2>/dev/null | grep -q "Ubuntu"; then
        echo_warning "This installer is optimized for Ubuntu Server"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    collect_client_info
    install_dependencies
    create_production_config
    create_n8n_auto_setup
    configure_security
    start_platform
    create_client_commands
    show_completion_summary
    
    # Save configuration for future reference
    cat > /opt/pilotpro-os/.platform-config << EOF
# PilotPro OS Configuration
DOMAIN=$DOMAIN
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_NAME=$ADMIN_FIRST_NAME $ADMIN_LAST_NAME
COMPANY_NAME=$COMPANY_NAME
INSTALLED_DATE=$(date)
EOF

    chmod 600 /opt/pilotpro-os/.platform-config
}

# Run installation
main "$@"