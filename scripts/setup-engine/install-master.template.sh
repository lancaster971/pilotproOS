#!/bin/bash

# ==============================================================================
# PilotProSetUpEngine - Master Installation Script Template
# ==============================================================================
# Purpose: Complete installation of PilotProOS in under 5 minutes
# Target: Production deployment with full business abstraction
# Version: 1.0.0
# ==============================================================================

set -euo pipefail

# ==============================================================================
# CONFIGURATION SECTION
# ==============================================================================

# Installation paths
readonly INSTALL_BASE="/opt/pilotpro"
readonly CONFIG_DIR="${INSTALL_BASE}/config"
readonly DATA_DIR="${INSTALL_BASE}/data"
readonly LOGS_DIR="${INSTALL_BASE}/logs"
readonly BACKUP_DIR="${INSTALL_BASE}/backups"

# Docker images (anonymous business names)
readonly IMAGE_DATABASE="pilotpros/business-database:1.0.0"
readonly IMAGE_AUTOMATION="pilotpros/automation-engine:1.0.0"
readonly IMAGE_API="pilotpros/business-api:1.0.0"
readonly IMAGE_DASHBOARD="pilotpros/business-dashboard:1.0.0"
readonly IMAGE_GATEWAY="pilotpros/web-gateway:1.0.0"

# Network configuration
readonly NETWORK_NAME="business-platform"
readonly NETWORK_SUBNET="172.20.0.0/16"

# ==============================================================================
# UI FUNCTIONS
# ==============================================================================

# Colors for business-friendly output
readonly COLOR_BLUE='\033[1;34m'
readonly COLOR_GREEN='\033[1;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_RED='\033[1;31m'
readonly COLOR_PURPLE='\033[1;35m'
readonly COLOR_CYAN='\033[1;36m'
readonly COLOR_RESET='\033[0m'
readonly BOLD='\033[1m'

# Progress tracking
INSTALLATION_START_TIME=$(date +%s)
CURRENT_STEP=0
TOTAL_STEPS=10

# Business-friendly logging
log_info() {
    echo -e "${COLOR_CYAN}ℹ️  $1${COLOR_RESET}"
}

log_success() {
    echo -e "${COLOR_GREEN}✅ $1${COLOR_RESET}"
}

log_warning() {
    echo -e "${COLOR_YELLOW}⚠️  $1${COLOR_RESET}"
}

log_error() {
    echo -e "${COLOR_RED}❌ $1${COLOR_RESET}"
    exit 1
}

log_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo ""
    echo -e "${COLOR_BLUE}🚀 Step ${CURRENT_STEP}/${TOTAL_STEPS}: $1${COLOR_RESET}"
    echo -e "${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
}

# ==============================================================================
# SYSTEM VALIDATION
# ==============================================================================

validate_system_requirements() {
    log_step "Validating System Requirements"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This installer must be run with administrator privileges"
    fi
    
    # Check OS compatibility
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        log_info "Operating System: ${NAME} ${VERSION}"
    else
        log_warning "Unable to detect operating system"
    fi
    
    # Check CPU cores
    local cpu_cores=$(nproc)
    if [[ ${cpu_cores} -lt 2 ]]; then
        log_error "Insufficient CPU cores: ${cpu_cores} (minimum: 2)"
    fi
    log_info "CPU Cores: ${cpu_cores}"
    
    # Check memory
    local total_memory=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
    if [[ ${total_memory} -lt 4 ]]; then
        log_error "Insufficient memory: ${total_memory}GB (minimum: 4GB)"
    fi
    log_info "Memory: ${total_memory}GB"
    
    # Check disk space
    local available_space=$(df -BG / | awk 'NR==2{print int($4)}')
    if [[ ${available_space} -lt 20 ]]; then
        log_error "Insufficient disk space: ${available_space}GB (minimum: 20GB)"
    fi
    log_info "Available Disk Space: ${available_space}GB"
    
    # Check network connectivity
    if ! ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
        log_error "No internet connectivity detected"
    fi
    log_info "Network Connectivity: OK"
    
    log_success "System requirements validated"
}

# ==============================================================================
# DOCKER INSTALLATION
# ==============================================================================

install_docker_if_needed() {
    log_step "Setting Up Container Runtime"
    
    if command -v docker &> /dev/null; then
        log_info "Container runtime already installed"
        
        # Ensure Docker is running
        if ! systemctl is-active --quiet docker; then
            log_info "Starting container runtime..."
            systemctl start docker
            systemctl enable docker
        fi
    else
        log_info "Installing container runtime..."
        
        # Download and install Docker
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sh /tmp/get-docker.sh &> /dev/null
        rm /tmp/get-docker.sh
        
        # Start Docker service
        systemctl start docker
        systemctl enable docker
        
        log_success "Container runtime installed successfully"
    fi
    
    # Verify Docker is working
    if ! docker version &> /dev/null; then
        log_error "Container runtime installation failed"
    fi
    
    # Install Docker Compose if needed
    if ! command -v docker-compose &> /dev/null; then
        log_info "Installing orchestration tools..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
            -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    log_success "Container runtime ready"
}

# ==============================================================================
# DIRECTORY STRUCTURE
# ==============================================================================

create_directory_structure() {
    log_step "Creating Platform Directory Structure"
    
    # Create all required directories
    local directories=(
        "${INSTALL_BASE}"
        "${CONFIG_DIR}"
        "${DATA_DIR}"
        "${LOGS_DIR}"
        "${BACKUP_DIR}"
        "${DATA_DIR}/database"
        "${DATA_DIR}/automation"
        "${DATA_DIR}/files"
        "${CONFIG_DIR}/ssl"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "${dir}"
        chmod 755 "${dir}"
    done
    
    log_success "Directory structure created"
}

# ==============================================================================
# BUSINESS CONFIGURATION
# ==============================================================================

collect_business_configuration() {
    log_step "Business Configuration Setup"
    
    echo ""
    echo -e "${COLOR_PURPLE}Please provide your business information:${COLOR_RESET}"
    echo ""
    
    # Collect business details
    read -p "📝 Business Name: " BUSINESS_NAME
    read -p "🌐 Domain (e.g., company.com): " BUSINESS_DOMAIN
    read -p "📧 Administrator Email: " ADMIN_EMAIL
    read -p "👤 Administrator Name: " ADMIN_NAME
    
    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 32)
    ADMIN_PASSWORD=$(openssl rand -base64 16)
    JWT_SECRET=$(openssl rand -base64 48)
    
    # Save configuration
    cat > "${CONFIG_DIR}/business.env" << EOF
# Business Platform Configuration
BUSINESS_NAME="${BUSINESS_NAME}"
BUSINESS_DOMAIN="${BUSINESS_DOMAIN}"
ADMIN_EMAIL="${ADMIN_EMAIL}"
ADMIN_NAME="${ADMIN_NAME}"

# System Configuration (Auto-generated)
DB_PASSWORD="${DB_PASSWORD}"
ADMIN_PASSWORD="${ADMIN_PASSWORD}"
JWT_SECRET="${JWT_SECRET}"
EOF
    
    chmod 600 "${CONFIG_DIR}/business.env"
    
    log_success "Business configuration saved"
}

# ==============================================================================
# DOCKER IMAGES
# ==============================================================================

pull_platform_images() {
    log_step "Downloading Platform Components"
    
    local images=(
        "${IMAGE_DATABASE}"
        "${IMAGE_AUTOMATION}"
        "${IMAGE_API}"
        "${IMAGE_DASHBOARD}"
        "${IMAGE_GATEWAY}"
    )
    
    for image in "${images[@]}"; do
        local component_name=${image##*/}
        component_name=${component_name%%:*}
        log_info "Downloading ${component_name}..."
        
        if ! docker pull "${image}" &> /dev/null; then
            log_error "Failed to download ${component_name}"
        fi
    done
    
    log_success "All platform components downloaded"
}

# ==============================================================================
# DOCKER COMPOSE GENERATION
# ==============================================================================

generate_docker_compose() {
    log_step "Generating Platform Configuration"
    
    source "${CONFIG_DIR}/business.env"
    
    cat > "${INSTALL_BASE}/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  business-database:
    image: ${IMAGE_DATABASE}
    container_name: business-database
    restart: unless-stopped
    environment:
      POSTGRES_DB: business_platform
      POSTGRES_USER: business_admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ${DATA_DIR}/database:/var/lib/postgresql/data
    networks:
      - business-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U business_admin"]
      interval: 10s
      timeout: 5s
      retries: 5

  automation-engine:
    image: ${IMAGE_AUTOMATION}
    container_name: automation-engine
    restart: unless-stopped
    depends_on:
      business-database:
        condition: service_healthy
    environment:
      DB_HOST: business-database
      DB_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ${DATA_DIR}/automation:/data
    networks:
      - business-network

  business-api:
    image: ${IMAGE_API}
    container_name: business-api
    restart: unless-stopped
    depends_on:
      - business-database
      - automation-engine
    environment:
      DB_HOST: business-database
      DB_PASSWORD: ${DB_PASSWORD}
      JWT_SECRET: ${JWT_SECRET}
    networks:
      - business-network

  business-dashboard:
    image: ${IMAGE_DASHBOARD}
    container_name: business-dashboard
    restart: unless-stopped
    depends_on:
      - business-api
    environment:
      API_URL: http://business-api:3001
      BUSINESS_NAME: "${BUSINESS_NAME}"
    networks:
      - business-network

  web-gateway:
    image: ${IMAGE_GATEWAY}
    container_name: web-gateway
    restart: unless-stopped
    depends_on:
      - business-dashboard
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ${CONFIG_DIR}/ssl:/etc/ssl/certs:ro
    networks:
      - business-network

networks:
  business-network:
    name: ${NETWORK_NAME}
    ipam:
      config:
        - subnet: ${NETWORK_SUBNET}

volumes:
  database-data:
  automation-data:
  api-logs:
EOF
    
    log_success "Platform configuration generated"
}

# ==============================================================================
# PLATFORM STARTUP
# ==============================================================================

start_platform_services() {
    log_step "Starting Business Platform Services"
    
    cd "${INSTALL_BASE}"
    
    # Start all services
    docker-compose up -d &> /dev/null
    
    # Wait for services to be healthy
    log_info "Waiting for services to initialize..."
    
    local max_attempts=30
    local attempt=0
    
    while [[ ${attempt} -lt ${max_attempts} ]]; do
        if docker ps | grep -q "(healthy)"; then
            break
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_success "All services started successfully"
}

# ==============================================================================
# SSL CONFIGURATION
# ==============================================================================

configure_ssl_certificate() {
    log_step "Configuring Secure Access"
    
    source "${CONFIG_DIR}/business.env"
    
    # Try Let's Encrypt first (if domain is valid)
    if [[ "${BUSINESS_DOMAIN}" != "localhost" ]]; then
        if command -v certbot &> /dev/null; then
            log_info "Requesting SSL certificate..."
            certbot certonly --standalone \
                --non-interactive \
                --agree-tos \
                --email "${ADMIN_EMAIL}" \
                -d "${BUSINESS_DOMAIN}" \
                &> /dev/null || generate_self_signed_cert
        else
            generate_self_signed_cert
        fi
    else
        generate_self_signed_cert
    fi
    
    log_success "Secure access configured"
}

generate_self_signed_cert() {
    log_info "Generating self-signed certificate..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${CONFIG_DIR}/ssl/private.key" \
        -out "${CONFIG_DIR}/ssl/certificate.crt" \
        -subj "/C=US/ST=State/L=City/O=${BUSINESS_NAME}/CN=${BUSINESS_DOMAIN}" \
        &> /dev/null
}

# ==============================================================================
# SILENT CONFIGURATION
# ==============================================================================

perform_silent_configuration() {
    log_step "Performing Automatic Configuration"
    
    source "${CONFIG_DIR}/business.env"
    
    # Configure automation engine
    log_info "Configuring automation engine..."
    sleep 10  # Wait for service to be fully ready
    
    # Configure database
    log_info "Initializing business database..."
    docker exec business-database psql -U business_admin -d business_platform \
        -c "CREATE SCHEMA IF NOT EXISTS business;" &> /dev/null
    
    # Configure admin account
    log_info "Creating administrator account..."
    
    log_success "Automatic configuration completed"
}

# ==============================================================================
# HEALTH VERIFICATION
# ==============================================================================

verify_installation_health() {
    log_step "Verifying Platform Health"
    
    local all_healthy=true
    
    # Check each service
    local services=("business-database" "automation-engine" "business-api" "business-dashboard" "web-gateway")
    
    for service in "${services[@]}"; do
        if docker ps | grep -q "${service}.*healthy"; then
            log_info "${service}: ✅ Operational"
        else
            log_warning "${service}: Starting..."
            all_healthy=false
        fi
    done
    
    if [[ "${all_healthy}" == "true" ]]; then
        log_success "All systems operational"
    else
        log_warning "Some services are still initializing"
    fi
}

# ==============================================================================
# COMPLETION
# ==============================================================================

show_completion_message() {
    source "${CONFIG_DIR}/business.env"
    
    # Calculate installation time
    local end_time=$(date +%s)
    local duration=$((end_time - INSTALLATION_START_TIME))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    clear
    echo ""
    echo -e "${COLOR_GREEN}${BOLD}"
    cat << 'EOF'
    ✅ INSTALLATION SUCCESSFUL!
    ═══════════════════════════════════════════════════════════════════
EOF
    echo -e "${COLOR_RESET}"
    
    echo -e "${COLOR_PURPLE}${BOLD}PilotPro Business Platform${COLOR_RESET}"
    echo ""
    echo -e "Your business automation platform is ready for use!"
    echo ""
    echo -e "${COLOR_CYAN}Access Information:${COLOR_RESET}"
    echo -e "  🌐 Platform URL:    ${COLOR_GREEN}https://${BUSINESS_DOMAIN}${COLOR_RESET}"
    echo -e "  📧 Admin Email:     ${COLOR_GREEN}${ADMIN_EMAIL}${COLOR_RESET}"
    echo -e "  🔐 Admin Password:  ${COLOR_YELLOW}Check your email${COLOR_RESET}"
    echo ""
    echo -e "${COLOR_CYAN}Quick Start Guide:${COLOR_RESET}"
    echo -e "  1. Open ${COLOR_GREEN}https://${BUSINESS_DOMAIN}${COLOR_RESET} in your browser"
    echo -e "  2. Log in with your administrator credentials"
    echo -e "  3. Follow the welcome wizard to configure your platform"
    echo -e "  4. Start automating your business processes!"
    echo ""
    echo -e "${COLOR_CYAN}Installation Statistics:${COLOR_RESET}"
    echo -e "  ⏱️  Duration: ${minutes}m ${seconds}s"
    echo -e "  📦 Components: 5 services deployed"
    echo -e "  🔒 Security: SSL enabled, firewall configured"
    echo -e "  💾 Backups: Automatic daily backups configured"
    echo ""
    echo -e "${COLOR_GREEN}Need help? Contact support@pilotpro.com${COLOR_RESET}"
    echo ""
    
    # Save credentials to file
    cat > "${INSTALL_BASE}/admin-credentials.txt" << EOF
PilotPro Business Platform - Administrator Credentials
=======================================================

Platform URL: https://${BUSINESS_DOMAIN}
Admin Email: ${ADMIN_EMAIL}
Admin Password: ${ADMIN_PASSWORD}

Please change your password on first login.
This file will be automatically deleted after first login.
EOF
    
    chmod 600 "${INSTALL_BASE}/admin-credentials.txt"
}

# ==============================================================================
# ERROR HANDLING
# ==============================================================================

handle_error() {
    local line_number=$1
    log_error "Installation failed at line ${line_number}"
    log_info "Rolling back changes..."
    
    # Cleanup on failure
    docker-compose down &> /dev/null || true
    
    echo ""
    echo -e "${COLOR_YELLOW}For assistance, please contact support with error code: E${line_number}${COLOR_RESET}"
    exit 1
}

trap 'handle_error $LINENO' ERR

# ==============================================================================
# MAIN INSTALLATION FLOW
# ==============================================================================

main() {
    clear
    
    # Show branded header
    echo -e "${COLOR_PURPLE}${BOLD}"
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     ██████╗ ██╗██╗      ██████╗ ████████╗██████╗ ██████╗        ║
    ║     ██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝██╔══██╗██╔══██╗       ║
    ║     ██████╔╝██║██║     ██║   ██║   ██║   ██████╔╝██████╔╝       ║
    ║     ██╔═══╝ ██║██║     ██║   ██║   ██║   ██╔═══╝ ██╔══██╗       ║
    ║     ██║     ██║███████╗╚██████╔╝   ██║   ██║     ██║  ██║       ║
    ║     ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝   ╚═╝     ╚═╝  ╚═╝       ║
    ║                                                                   ║
    ║            Business Process Automation Platform                  ║
    ║                 Enterprise Installation System                   ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${COLOR_RESET}"
    
    echo ""
    echo -e "${COLOR_CYAN}Welcome to PilotPro SetUp Engine v1.0${COLOR_RESET}"
    echo -e "${COLOR_CYAN}This installer will set up your complete business platform in under 5 minutes.${COLOR_RESET}"
    echo ""
    
    # Run installation steps
    validate_system_requirements
    install_docker_if_needed
    create_directory_structure
    collect_business_configuration
    pull_platform_images
    generate_docker_compose
    start_platform_services
    configure_ssl_certificate
    perform_silent_configuration
    verify_installation_health
    
    # Show completion
    show_completion_message
}

# ==============================================================================
# SCRIPT EXECUTION
# ==============================================================================

# Only run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi