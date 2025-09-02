#!/bin/bash
# ============================================================================
# PilotProOS Webhook URL Auto-Detection Script
# Purpose: Auto-detect best webhook URL for current environment
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# ENVIRONMENT DETECTION
# ============================================================================

detect_environment() {
    if [[ "${NODE_ENV:-}" == "production" ]]; then
        echo "production"
    elif [[ "${NODE_ENV:-}" == "development" ]]; then
        echo "development"
    elif [[ -f "docker-compose.dev.yml" ]]; then
        echo "development"
    elif [[ -f "docker-compose.yml" ]]; then
        echo "production"
    else
        echo "unknown"
    fi
}

# ============================================================================
# IP DETECTION FUNCTIONS
# ============================================================================

get_local_ip() {
    # Try multiple methods to get local IP
    local ip=""
    
    # Method 1: macOS specific (en0 interface)
    if command -v ipconfig >/dev/null 2>&1; then
        ip=$(ipconfig getifaddr en0 2>/dev/null || echo "")
    fi
    
    # Method 2: Linux hostname command
    if [[ -z "$ip" ]] && command -v hostname >/dev/null 2>&1; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "")
    fi
    
    # Method 3: ip command (Linux)
    if [[ -z "$ip" ]] && command -v ip >/dev/null 2>&1; then
        ip=$(ip route get 8.8.8.8 | grep -oP 'src \K\S+' 2>/dev/null || echo "")
    fi
    
    # Method 4: Network interface inspection
    if [[ -z "$ip" ]]; then
        # Try common interface names
        for interface in eth0 wlan0 en0 en1 wlp3s0; do
            if ip=$(ifconfig $interface 2>/dev/null | grep -oP 'inet \K\d+\.\d+\.\d+\.\d+' | head -1); then
                break
            fi
        done
    fi
    
    # Method 5: Fallback to localhost
    if [[ -z "$ip" ]]; then
        ip="127.0.0.1"
    fi
    
    echo "$ip"
}

get_public_ip() {
    # Try multiple services to get public IP
    local ip=""
    
    # Method 1: ipinfo.io
    ip=$(curl -s --max-time 5 ipinfo.io/ip 2>/dev/null || echo "")
    
    # Method 2: ifconfig.me (backup)
    if [[ -z "$ip" ]]; then
        ip=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "")
    fi
    
    # Method 3: icanhazip.com (backup)
    if [[ -z "$ip" ]]; then
        ip=$(curl -s --max-time 5 icanhazip.com 2>/dev/null || echo "")
    fi
    
    # Fallback to local IP
    if [[ -z "$ip" ]]; then
        ip=$(get_local_ip)
    fi
    
    echo "$ip"
}

# ============================================================================
# DOMAIN VALIDATION
# ============================================================================

is_valid_domain() {
    local domain="$1"
    # Regex for valid domain format
    if [[ "$domain" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

test_domain_reachability() {
    local domain="$1"
    log "Testing domain reachability: $domain"
    
    # Test DNS resolution
    if ! nslookup "$domain" >/dev/null 2>&1; then
        warning "Domain $domain does not resolve"
        return 1
    fi
    
    # Test HTTP connectivity
    if curl -s --max-time 10 "http://$domain" >/dev/null 2>&1; then
        success "Domain $domain is reachable via HTTP"
        return 0
    elif curl -s --max-time 10 "https://$domain" >/dev/null 2>&1; then
        success "Domain $domain is reachable via HTTPS"
        return 0
    else
        warning "Domain $domain is not responding to HTTP/HTTPS"
        return 1
    fi
}

# ============================================================================
# WEBHOOK URL GENERATION
# ============================================================================

generate_webhook_url() {
    local environment="$1"
    local domain="${2:-}"
    local webhook_url=""
    
    case "$environment" in
        "production")
            if [[ -n "$domain" ]] && is_valid_domain "$domain"; then
                if test_domain_reachability "$domain"; then
                    webhook_url="https://$domain/webhook"
                else
                    webhook_url="http://$domain/webhook"
                fi
            else
                local public_ip=$(get_public_ip)
                webhook_url="http://$public_ip/webhook"
            fi
            ;;
            
        "development")
            local local_ip=$(get_local_ip)
            webhook_url="http://$local_ip/webhook"
            
            # Test if port 80 is available for Nginx
            if ! lsof -i :80 >/dev/null 2>&1; then
                log "Port 80 available for Nginx webhook proxy"
            else
                warning "Port 80 in use - webhook may need different configuration"
                # Fallback to direct n8n port
                webhook_url="http://$local_ip:5678/webhook"
            fi
            ;;
            
        *)
            webhook_url="http://localhost:5678/webhook"
            ;;
    esac
    
    echo "$webhook_url"
}

# ============================================================================
# CONFIGURATION OUTPUT
# ============================================================================

generate_env_config() {
    local webhook_url="$1"
    local environment="$2"
    
    log "📝 Generating environment configuration..."
    
    cat << EOF
# PilotProOS Webhook Configuration - Generated $(date)
# Environment: $environment
# Generated by: scripts/detect-webhook-url.sh

# Webhook Configuration
WEBHOOK_URL=$webhook_url
WEBHOOK_BASE_URL=${webhook_url%/webhook}

# n8n Configuration  
N8N_WEBHOOK_URL=$webhook_url
N8N_EDITOR_BASE_URL=${webhook_url%/webhook}

# Environment Detection
DETECTED_ENVIRONMENT=$environment
LOCAL_IP=$(get_local_ip)
PUBLIC_IP=$(get_public_ip)

# Service URLs
FRONTEND_URL=${webhook_url%/webhook}
BACKEND_URL=${webhook_url%/webhook}/api
AI_AGENT_URL=${webhook_url%/webhook}/ai

# Development Access (if development)
EOF

    if [[ "$environment" == "development" ]]; then
        cat << EOF
N8N_ADMIN_URL=${webhook_url%/webhook}/dev/n8n
PGADMIN_URL=${webhook_url%/webhook}/dev/db
STATUS_URL=${webhook_url%/webhook}/dev/status
EOF
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log "🚀 PilotProOS Webhook URL Auto-Detection"
    log "========================================"
    
    # Detect environment
    local environment=$(detect_environment)
    log "Environment detected: $environment"
    
    # Get domain from arguments or environment
    local domain="${1:-${DOMAIN:-${CLIENT_DOMAIN:-}}}"
    
    if [[ -n "$domain" ]]; then
        log "Using provided domain: $domain"
    else
        log "No domain provided, using IP-based configuration"
    fi
    
    # Generate webhook URL
    local webhook_url=$(generate_webhook_url "$environment" "$domain")
    
    # Output results
    echo ""
    success "WEBHOOK URL DETECTED: $webhook_url"
    echo ""
    
    # Generate configuration
    generate_env_config "$webhook_url" "$environment"
    
    # Additional recommendations
    echo ""
    log "📋 RECOMMENDATIONS:"
    
    case "$environment" in
        "development")
            echo "  1. Start Nginx with development configuration:"
            echo "     nginx -c $(pwd)/config/nginx-development.conf"
            echo ""
            echo "  2. Update docker-compose.dev.yml:"
            echo "     WEBHOOK_URL: $webhook_url"
            echo ""
            echo "  3. Test webhook accessibility:"
            echo "     curl -X POST $webhook_url/test-webhook-id"
            ;;
            
        "production")
            echo "  1. Ensure domain points to this server"
            echo "  2. Configure SSL certificate for HTTPS"
            echo "  3. Update firewall to allow port 80/443"
            echo "  4. Test webhook from external service"
            ;;
    esac
    
    echo ""
    log "🎯 Webhook URL ready for external services (Microsoft Outlook, APIs, etc.)"
}

# Execute main function with arguments
main "$@"