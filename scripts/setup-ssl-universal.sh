#!/bin/bash
# ============================================================================
# PilotProOS Universal SSL Setup
# Funziona identicamente in Development e Production
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
# ENVIRONMENT DETECTION
# ============================================================================

detect_ssl_strategy() {
    local domain="${1:-}"
    local environment="${2:-development}"
    
    # Case 1: Valid domain (production or development with domain)
    if [[ -n "$domain" ]] && [[ "$domain" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
        # Test if domain resolves to this server
        if dig +short "$domain" >/dev/null 2>&1; then
            echo "letsencrypt"  # Production Let's Encrypt
        else
            echo "self-signed"  # Development with domain
        fi
        
    # Case 2: Development with IP
    elif [[ "$environment" == "development" ]]; then        
        # Check if ngrok is available
        if command -v ngrok >/dev/null 2>&1 || [[ -f "/tmp/ngrok" ]]; then
            echo "ngrok"  # Development with ngrok tunnel
        else
            echo "self-signed"  # Development with self-signed
        fi
        
    # Case 3: Production with IP only
    else
        echo "self-signed"  # Production fallback
    fi
}

# ============================================================================
# CERTIFICATE GENERATION STRATEGIES
# ============================================================================

setup_letsencrypt_ssl() {
    local domain="$1"
    log "🔒 Setting up Let's Encrypt SSL for: $domain"
    
    # Install certbot if not present
    if ! command -v certbot >/dev/null 2>&1; then
        log "Installing certbot..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install certbot
        else
            apt-get update && apt-get install -y certbot python3-certbot-nginx
        fi
    fi
    
    # Generate certificate
    certbot --nginx -d "$domain" --non-interactive --agree-tos --email "admin@$domain" || {
        warning "Let's Encrypt failed, falling back to self-signed"
        setup_self_signed_ssl "$domain"
        return
    }
    
    success "Let's Encrypt SSL configured for $domain"
    echo "https://$domain"
}

setup_self_signed_ssl() {
    local target="${1:-10.42.178.174}"
    log "🔒 Setting up self-signed SSL for: $target"
    
    # Create certificates directory
    mkdir -p "$(pwd)/config/ssl"
    cd "$(pwd)/config/ssl"
    
    # Generate self-signed certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout pilotpros-dev.key \
        -out pilotpros-dev.crt \
        -subj "/C=IT/ST=Development/L=Local/O=PilotProOS/CN=$target" \
        -addext "subjectAltName=IP:$target,DNS:localhost,DNS:*.local"
    
    success "Self-signed certificate generated"
    echo "https://$target"
}

setup_ngrok_tunnel() {
    local port="${1:-80}"
    log "🌐 Setting up ngrok HTTPS tunnel for port: $port"
    
    # Use downloaded ngrok binary
    local ngrok_cmd="ngrok"
    if [[ -f "/tmp/ngrok" ]]; then
        ngrok_cmd="/tmp/ngrok"
        log "Using downloaded ngrok binary"
    elif ! command -v ngrok >/dev/null 2>&1; then
        error "ngrok not found - use: curl -o /tmp/ngrok.zip -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip && unzip /tmp/ngrok.zip -d /tmp"
    fi
    
    # Check if ngrok auth token is configured
    if ! ngrok config check >/dev/null 2>&1; then
        warning "ngrok auth token not configured"
        info "Get free auth token from: https://dashboard.ngrok.com/get-started/your-authtoken"
        info "Then run: ngrok config add-authtoken YOUR_TOKEN"
        
        # For now, continue without auth (limited tunnel)
    fi
    
    # Start tunnel in background
    log "Starting ngrok tunnel..."
    $ngrok_cmd http "$port" --log=stdout > /tmp/ngrok.log 2>&1 &
    NGROK_PID=$!
    
    # Wait for tunnel to be ready
    sleep 8
    
    # Extract HTTPS URL
    local ngrok_url=""
    for i in {1..15}; do
        ngrok_url=$(curl -s localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url // empty' 2>/dev/null)
        if [[ -n "$ngrok_url" && "$ngrok_url" =~ ^https:// ]]; then
            break
        fi
        log "Waiting for ngrok tunnel... (attempt $i/15)"
        sleep 3
    done
    
    if [[ -n "$ngrok_url" ]]; then
        success "ngrok tunnel ready: $ngrok_url"
        
        # Save tunnel info
        echo "$NGROK_PID" > /tmp/ngrok.pid
        echo "$ngrok_url" > /tmp/ngrok.url
        
        echo "$ngrok_url"
    else
        error "Failed to create ngrok tunnel"
    fi
}

# ============================================================================
# NGINX CONFIGURATION UPDATE
# ============================================================================

update_nginx_for_ssl() {
    local ssl_url="$1"
    local ssl_strategy="$2"
    
    log "🔧 Updating Nginx configuration for SSL"
    
    # Extract components
    local protocol=$(echo "$ssl_url" | cut -d':' -f1)
    local host_port=$(echo "$ssl_url" | cut -d'/' -f3)
    local host=$(echo "$host_port" | cut -d':' -f1)
    local port=$(echo "$host_port" | cut -d':' -f2)
    [[ "$port" == "$host" ]] && port="443"
    
    # Backup current nginx config
    cp "$(pwd)/config/nginx-development.conf" "$(pwd)/config/nginx-development.conf.backup"
    
    case "$ssl_strategy" in
        "letsencrypt")
            # Production Let's Encrypt - nginx handles SSL automatically
            info "Let's Encrypt SSL managed by certbot"
            ;;
            
        "self-signed")
            # Add SSL configuration for self-signed
            cat > "$(pwd)/config/nginx-ssl-addon.conf" << EOF
# SSL Configuration (Self-Signed)
listen 443 ssl http2;
ssl_certificate /app/config/ssl/pilotpros-dev.crt;
ssl_certificate_key /app/config/ssl/pilotpros-dev.key;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# HTTP to HTTPS redirect
if (\$scheme != "https") {
    return 301 https://\$host\$request_uri;
}
EOF
            success "Self-signed SSL configuration created"
            ;;
            
        "ngrok")
            # ngrok manages SSL - no local nginx SSL needed
            info "ngrok tunnel manages HTTPS - no local SSL config needed"
            
            # Update environment variables to use ngrok URL
            cat > "$(pwd)/.env.ngrok" << EOF
# ngrok Development Configuration
WEBHOOK_URL=$ssl_url/webhook
N8N_EDITOR_BASE_URL=$ssl_url
FRONTEND_URL=$ssl_url
BACKEND_URL=$ssl_url/api
EOF
            success "ngrok environment configuration created"
            ;;
    esac
}

# ============================================================================
# DOCKER COMPOSE UPDATE
# ============================================================================

update_docker_compose_ssl() {
    local ssl_url="$1"
    local ssl_strategy="$2"
    
    log "🐳 Updating Docker Compose for SSL"
    
    # Extract host from URL
    local host=$(echo "$ssl_url" | sed 's|https\?://||' | cut -d'/' -f1 | cut -d':' -f1)
    
    # Backup docker-compose
    cp docker-compose.dev.yml docker-compose.dev.yml.backup
    
    # Update webhook URLs in docker-compose
    sed -i.bak \
        -e "s|WEBHOOK_URL:.*|WEBHOOK_URL: $ssl_url/webhook|" \
        -e "s|N8N_EDITOR_BASE_URL:.*|N8N_EDITOR_BASE_URL: $ssl_url|" \
        docker-compose.dev.yml
    
    success "Docker Compose updated with SSL URLs"
    
    # Add SSL volume mapping if self-signed
    if [[ "$ssl_strategy" == "self-signed" ]]; then
        if ! grep -q "config/ssl" docker-compose.dev.yml; then
            # Add SSL volume to nginx service
            sed -i.bak '/volumes:/a\
      - ./config/ssl:/app/config/ssl:ro' docker-compose.dev.yml
        fi
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    local domain="${1:-}"
    local environment="${NODE_ENV:-development}"
    
    log "🚀 PilotProOS Universal SSL Setup"
    log "================================="
    log "Domain: ${domain:-auto-detect}"
    log "Environment: $environment"
    echo ""
    
    # Detect SSL strategy
    local ssl_strategy=$(detect_ssl_strategy "$domain" "$environment")
    log "SSL Strategy: $ssl_strategy"
    
    # Setup SSL based on strategy
    local ssl_url=""
    case "$ssl_strategy" in
        "letsencrypt")
            ssl_url=$(setup_letsencrypt_ssl "$domain")
            ;;
        "self-signed")
            local target="${domain:-$(./scripts/detect-webhook-url.sh | grep "LOCAL_IP=" | cut -d'=' -f2)}"
            ssl_url=$(setup_self_signed_ssl "$target")
            ;;
        "ngrok")
            ssl_url=$(setup_ngrok_tunnel "80")
            ;;
        *)
            error "Unknown SSL strategy: $ssl_strategy"
            ;;
    esac
    
    # Update configurations
    update_nginx_for_ssl "$ssl_url" "$ssl_strategy"
    update_docker_compose_ssl "$ssl_url" "$ssl_strategy"
    
    # Final output
    echo ""
    success "SSL Setup Complete!"
    log "================================="
    log "HTTPS URL: $ssl_url"
    log "OAuth Callback: $ssl_url/rest/oauth2-credential/callback"
    log "Webhook Base: $ssl_url/webhook/"
    log "n8n Admin: $ssl_url/dev/n8n/"
    echo ""
    
    # Restart instructions
    case "$ssl_strategy" in
        "letsencrypt"|"self-signed")
            log "📋 Next Steps:"
            log "1. Restart Docker stack: npm run docker:reset"
            log "2. Test HTTPS: curl -k $ssl_url/health"
            log "3. Configure Microsoft OAuth with: $ssl_url/rest/oauth2-credential/callback"
            ;;
        "ngrok")
            log "📋 Next Steps:"
            log "1. Use ngrok URL in Microsoft Azure: $ssl_url/rest/oauth2-credential/callback"
            log "2. Keep ngrok tunnel running in background"
            log "3. Restart n8n container: docker-compose -f docker-compose.dev.yml restart n8n-dev"
            ;;
    esac
    
    # Save configuration for future use
    cat > "$(pwd)/.env.ssl" << EOF
# PilotProOS SSL Configuration - Generated $(date)
SSL_STRATEGY=$ssl_strategy
SSL_URL=$ssl_url
WEBHOOK_URL=$ssl_url/webhook
N8N_EDITOR_BASE_URL=$ssl_url
OAUTH_CALLBACK_URL=$ssl_url/rest/oauth2-credential/callback
EOF
    
    success "SSL configuration saved to .env.ssl"
}

# Execute with provided domain
main "$@"