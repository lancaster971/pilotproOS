#!/bin/bash
# ============================================================================
# PilotProOS Development SSL Setup
# Configura HTTPS per sviluppo locale con certificati self-signed
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }
info() { echo -e "${CYAN}ℹ️ $1${NC}"; }

# ============================================================================
# FUNCTIONS
# ============================================================================

check_dependencies() {
    log "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker not found. Please install Docker first."
    fi
    
    # Check OpenSSL
    if ! command -v openssl >/dev/null 2>&1; then
        error "OpenSSL not found. Please install OpenSSL first."
    fi
    
    success "All dependencies satisfied"
}

generate_ssl_certificate() {
    log "Generating SSL certificate for local development..."
    
    # Create SSL directory
    mkdir -p "$(pwd)/config/ssl"
    cd "$(pwd)/config/ssl"
    
    # Create SSL configuration
    cat > ssl-config.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C=IT
ST=Development
L=Local
O=PilotProOS
CN=localhost

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = pilotpros.local
DNS.3 = *.pilotpros.local
IP.1 = 127.0.0.1
IP.2 = 10.42.178.174
IP.3 = 192.168.1.100
IP.4 = 172.18.0.1
EOF
    
    # Generate certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout pilotpros-dev.key \
        -out pilotpros-dev.crt \
        -config ssl-config.conf \
        -extensions v3_req
        
    success "SSL certificate generated"
    
    # Verify certificate
    log "Certificate details:"
    openssl x509 -in pilotpros-dev.crt -noout -text | grep -A5 "Subject Alternative Name" || true
}

update_docker_compose() {
    log "Updating docker-compose.dev.yml for HTTPS..."
    
    # Backup current file
    cp docker-compose.dev.yml docker-compose.dev.yml.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update n8n environment variables
    sed -i.bak \
        -e 's|WEBHOOK_URL:.*|WEBHOOK_URL: https://localhost/webhook|' \
        -e 's|N8N_EDITOR_BASE_URL:.*|N8N_EDITOR_BASE_URL: https://localhost|' \
        -e 's|N8N_PROTOCOL:.*|N8N_PROTOCOL: https|' \
        -e 's|N8N_HOST_IP:.*|N8N_HOST_IP: localhost|' \
        docker-compose.dev.yml
    
    # Update frontend environment variables  
    sed -i.bak \
        -e 's|VITE_API_URL:.*|VITE_API_URL: https://localhost/api|' \
        -e 's|VITE_N8N_URL:.*|VITE_N8N_URL: https://localhost/dev/n8n|' \
        docker-compose.dev.yml
        
    success "Docker Compose updated for HTTPS"
}

restart_services() {
    log "Restarting Docker services..."
    
    # Restart n8n and frontend to apply new environment variables
    docker-compose -f docker-compose.dev.yml restart n8n-dev frontend-dev
    
    success "Services restarted"
}

test_https_setup() {
    log "Testing HTTPS setup..."
    
    # Wait for services to be ready
    sleep 10
    
    # Test HTTPS endpoints
    local endpoints=(
        "https://localhost/health"
        "https://localhost/dev/n8n/"
        "https://localhost/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log "Testing: $endpoint"
        if curl -k -s --connect-timeout 5 "$endpoint" >/dev/null; then
            success "$endpoint - OK"
        else
            warning "$endpoint - Failed (may be normal during startup)"
        fi
    done
}

show_results() {
    echo ""
    success "🔒 HTTPS Development Environment Ready!"
    log "=================================="
    
    echo -e "${CYAN}🌐 Access URLs:${NC}"
    echo "  Frontend:      https://localhost/"
    echo "  n8n Admin:     https://localhost/dev/n8n/"
    echo "  Backend API:   https://localhost/api/"
    echo "  Health Check:  https://localhost/health"
    echo ""
    
    echo -e "${CYAN}🔗 OAuth Callback URLs:${NC}"
    echo "  Microsoft:     https://localhost/rest/oauth2-credential/callback"
    echo "  Google:        https://localhost/rest/oauth2-credential/callback"
    echo "  General:       https://localhost/webhook/{workflow-name}"
    echo ""
    
    echo -e "${YELLOW}📋 Next Steps for OAuth Setup:${NC}"
    echo "  1. Configure your OAuth providers with callback URL:"
    echo "     https://localhost/rest/oauth2-credential/callback"
    echo ""  
    echo "  2. Add localhost to your hosts file for better compatibility:"
    echo "     echo '127.0.0.1 pilotpros.local' | sudo tee -a /etc/hosts"
    echo ""
    echo "  3. For production, replace 'localhost' with your actual domain"
    echo ""
    
    echo -e "${GREEN}✨ Your development environment now supports HTTPS!${NC}"
    echo -e "${GREEN}   All OAuth providers (Microsoft, Google, Supabase) should work correctly.${NC}"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log "🚀 PilotProOS Development HTTPS Setup"
    log "====================================="
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "docker-compose.dev.yml" ]]; then
        error "Please run this script from the PilotProOS root directory"
    fi
    
    # Run setup steps
    check_dependencies
    generate_ssl_certificate
    update_docker_compose
    restart_services
    test_https_setup
    show_results
}

# Execute main function
main "$@"