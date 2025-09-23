#!/bin/bash

# PilotProOS - SSL Certificate Automation with Let's Encrypt
# Handles SSL certificate generation, renewal, and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSL_DIR="${PROJECT_ROOT}/ssl"
NGINX_DIR="${PROJECT_ROOT}/nginx"

# Load environment variables
if [ -f "${PROJECT_ROOT}/.env.production" ]; then
    export $(grep -v '^#' "${PROJECT_ROOT}/.env.production" | xargs)
fi

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ASCII Art Header
show_header() {
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                      PilotProOS                           ║
║               SSL Certificate Automation                  ║
║                 Let's Encrypt + Certbot                  ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if running as root (required for port 80)
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. This is OK for SSL setup."
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        exit 1
    fi

    # Check domain configuration
    if [ -z "$DOMAIN_NAME" ] || [ "$DOMAIN_NAME" == "localhost" ]; then
        print_error "DOMAIN_NAME not configured in .env.production"
        echo "Please edit .env.production and set your domain name"
        exit 1
    fi

    if [ -z "$ADMIN_EMAIL" ] || [ "$ADMIN_EMAIL" == "admin@localhost" ]; then
        print_error "ADMIN_EMAIL not configured in .env.production"
        echo "Please edit .env.production and set your admin email"
        exit 1
    fi

    print_success "Prerequisites checked"
}

# Function to test DNS resolution
test_dns() {
    print_info "Testing DNS resolution for ${DOMAIN_NAME}..."

    # Get server's public IP
    PUBLIC_IP=$(curl -s ifconfig.me)

    # Get domain's resolved IP
    DOMAIN_IP=$(dig +short ${DOMAIN_NAME} | tail -1)

    if [ -z "$DOMAIN_IP" ]; then
        print_error "Domain ${DOMAIN_NAME} does not resolve!"
        echo "Please configure your DNS A record to point to: ${PUBLIC_IP}"
        exit 1
    fi

    if [ "$PUBLIC_IP" != "$DOMAIN_IP" ]; then
        print_warning "Domain IP ($DOMAIN_IP) doesn't match server IP ($PUBLIC_IP)"
        echo "This might be OK if you're behind a proxy/load balancer"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "DNS configured correctly (${DOMAIN_NAME} -> ${PUBLIC_IP})"
    fi

    # Test www subdomain if applicable
    if [[ ! "$DOMAIN_NAME" =~ ^www\. ]]; then
        WWW_DOMAIN="www.${DOMAIN_NAME}"
        WWW_IP=$(dig +short ${WWW_DOMAIN} | tail -1)
        if [ ! -z "$WWW_IP" ]; then
            print_info "Also found www subdomain: ${WWW_DOMAIN} -> ${WWW_IP}"
            USE_WWW=true
        fi
    fi
}

# Function to create SSL directories
create_ssl_directories() {
    print_info "Creating SSL directories..."

    directories=(
        "${SSL_DIR}"
        "${SSL_DIR}/live"
        "${SSL_DIR}/renewal"
        "${SSL_DIR}/archive"
        "${SSL_DIR}/renewal-hooks"
        "${SSL_DIR}/renewal-hooks/pre"
        "${SSL_DIR}/renewal-hooks/post"
        "${SSL_DIR}/dhparam"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            chmod 755 "$dir"
        fi
    done

    print_success "SSL directories created"
}

# Function to generate DH parameters
generate_dhparam() {
    print_info "Generating Diffie-Hellman parameters (this may take a while)..."

    DH_PARAM_FILE="${SSL_DIR}/dhparam/dhparam.pem"

    if [ -f "$DH_PARAM_FILE" ]; then
        print_warning "DH parameters already exist"
        return
    fi

    openssl dhparam -out "$DH_PARAM_FILE" 2048
    chmod 644 "$DH_PARAM_FILE"

    print_success "DH parameters generated"
}

# Function to generate self-signed certificate (fallback)
generate_self_signed() {
    print_info "Generating self-signed certificate as fallback..."

    SELF_SIGNED_DIR="${SSL_DIR}/self-signed"
    mkdir -p "$SELF_SIGNED_DIR"

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${SELF_SIGNED_DIR}/privkey.pem" \
        -out "${SELF_SIGNED_DIR}/fullchain.pem" \
        -subj "/C=US/ST=State/L=City/O=PilotProOS/CN=${DOMAIN_NAME}"

    chmod 644 "${SELF_SIGNED_DIR}/fullchain.pem"
    chmod 600 "${SELF_SIGNED_DIR}/privkey.pem"

    print_success "Self-signed certificate generated (for initial setup)"
}

# Function to obtain Let's Encrypt certificate
obtain_letsencrypt_cert() {
    print_info "Obtaining Let's Encrypt certificate..."

    # Prepare domains list
    DOMAINS="-d ${DOMAIN_NAME}"
    if [ "$USE_WWW" == "true" ]; then
        DOMAINS="${DOMAINS} -d ${WWW_DOMAIN}"
    fi

    # Stop nginx if running (to free port 80)
    if docker ps | grep -q pilotpros-nginx; then
        print_info "Stopping nginx to free port 80..."
        docker stop pilotpros-nginx || true
    fi

    # Run certbot in standalone mode
    docker run --rm \
        -p 80:80 \
        -v "${SSL_DIR}:/etc/letsencrypt" \
        -v "${PROJECT_ROOT}/certbot_data:/var/www/certbot" \
        certbot/certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email "${ADMIN_EMAIL}" \
        ${DOMAINS} \
        --expand

    if [ $? -eq 0 ]; then
        print_success "SSL certificate obtained successfully!"
    else
        print_error "Failed to obtain SSL certificate"
        print_warning "Using self-signed certificate as fallback"
        generate_self_signed
        return 1
    fi

    # Set proper permissions
    chmod -R 755 "${SSL_DIR}/live"
    chmod -R 755 "${SSL_DIR}/archive"

    return 0
}

# Function to create nginx SSL configuration
create_nginx_ssl_config() {
    print_info "Creating Nginx SSL configuration..."

    # Determine certificate path
    if [ -d "${SSL_DIR}/live/${DOMAIN_NAME}" ]; then
        CERT_PATH="/etc/nginx/ssl/live/${DOMAIN_NAME}"
        CERT_TYPE="letsencrypt"
    else
        CERT_PATH="/etc/nginx/ssl/self-signed"
        CERT_TYPE="self-signed"
        print_warning "Using self-signed certificate"
    fi

    # Create main nginx configuration
    cat > "${NGINX_DIR}/nginx.conf.production" << EOF
user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main buffer=16k;

    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml application/atom+xml image/svg+xml
               text/x-js text/x-cross-domain-policy application/x-font-ttf
               application/x-font-opentype application/vnd.ms-fontobject
               image/x-icon;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK;
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_dhparam /etc/nginx/ssl/dhparam/dhparam.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting zones
    limit_req_zone \$binary_remote_addr zone=general:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=api:10m rate=30r/s;
    limit_req_zone \$binary_remote_addr zone=auth:10m rate=5r/s;

    # Upstream definitions
    upstream backend {
        least_conn;
        server backend:3001 max_fails=3 fail_timeout=30s;
    }

    upstream n8n {
        server n8n:5678 max_fails=3 fail_timeout=30s;
    }

    upstream frontend {
        server frontend:80 max_fails=3 fail_timeout=30s;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        listen [::]:80;
        server_name ${DOMAIN_NAME}${USE_WWW:+ www.${DOMAIN_NAME}};

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://\$host\$request_uri;
        }
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name ${DOMAIN_NAME}${USE_WWW:+ www.${DOMAIN_NAME}};

        # SSL certificates
        ssl_certificate ${CERT_PATH}/fullchain.pem;
        ssl_certificate_key ${CERT_PATH}/privkey.pem;

        # Frontend application
        location / {
            limit_req zone=general burst=20 nodelay;

            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_cache_bypass \$http_upgrade;

            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                proxy_pass http://frontend;
                expires 30d;
                add_header Cache-Control "public, immutable";
            }
        }

        # Backend API
        location /api/ {
            limit_req zone=api burst=50 nodelay;

            proxy_pass http://backend/api/;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;

            # Increased timeouts for long-running operations
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }

        # Authentication endpoints (stricter rate limiting)
        location /api/auth/ {
            limit_req zone=auth burst=10 nodelay;

            proxy_pass http://backend/api/auth/;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # n8n webhooks
        location /webhook/ {
            proxy_pass http://n8n/webhook/;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header Connection '';
            proxy_buffering off;

            # Webhooks might need longer timeouts
            proxy_connect_timeout 90s;
            proxy_send_timeout 600s;
            proxy_read_timeout 600s;
        }

        # n8n admin interface (separate subdomain would be better)
        location /n8n/ {
            auth_basic "n8n Admin";
            auth_basic_user_file /etc/nginx/.htpasswd;

            proxy_pass http://n8n/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_cache_bypass \$http_upgrade;
        }

        # Health check endpoint
        location /health {
            access_log off;
            add_header Content-Type text/plain;
            return 200 'healthy\\n';
        }

        # Security: Deny access to hidden files
        location ~ /\\. {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
EOF

    print_success "Nginx SSL configuration created"
}

# Function to create renewal script
create_renewal_script() {
    print_info "Creating automatic renewal script..."

    cat > "${PROJECT_ROOT}/scripts/renew-ssl.sh" << 'EOF'
#!/bin/bash

# PilotProOS SSL Certificate Renewal Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${PROJECT_ROOT}/logs/ssl-renewal.log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_message "Starting SSL certificate renewal check..."

# Run certbot renewal
docker run --rm \
    -v "${PROJECT_ROOT}/ssl:/etc/letsencrypt" \
    -v "${PROJECT_ROOT}/certbot_data:/var/www/certbot" \
    certbot/certbot renew \
    --webroot \
    --webroot-path=/var/www/certbot \
    --quiet

if [ $? -eq 0 ]; then
    log_message "Certificate renewal check completed successfully"

    # Reload nginx if certificate was renewed
    if docker ps | grep -q pilotpros-nginx; then
        docker exec pilotpros-nginx nginx -s reload
        log_message "Nginx configuration reloaded"
    fi
else
    log_message "ERROR: Certificate renewal failed"
fi

log_message "SSL renewal check completed"
EOF

    chmod +x "${PROJECT_ROOT}/scripts/renew-ssl.sh"

    print_success "Renewal script created"
}

# Function to setup cron job for renewal
setup_renewal_cron() {
    print_info "Setting up automatic renewal cron job..."

    CRON_FILE="/etc/cron.d/pilotpros-ssl-renewal"
    RENEWAL_SCRIPT="${PROJECT_ROOT}/scripts/renew-ssl.sh"

    # Create cron job (runs twice daily)
    echo "0 0,12 * * * root ${RENEWAL_SCRIPT} 2>&1" | sudo tee "$CRON_FILE" > /dev/null

    # Set proper permissions
    sudo chmod 644 "$CRON_FILE"

    print_success "Cron job created for automatic renewal"
    print_info "Certificates will be checked for renewal twice daily"
}

# Function to create htpasswd for n8n
create_htpasswd() {
    print_info "Creating htpasswd for n8n admin protection..."

    HTPASSWD_FILE="${NGINX_DIR}/.htpasswd"

    # Generate htpasswd file
    N8N_ADMIN_PASSWORD=${N8N_PASSWORD:-$(openssl rand -base64 20)}

    # Use htpasswd or openssl
    if command -v htpasswd &> /dev/null; then
        htpasswd -bc "$HTPASSWD_FILE" "${N8N_USER:-admin}" "$N8N_ADMIN_PASSWORD"
    else
        # Use openssl as fallback
        echo "${N8N_USER:-admin}:$(openssl passwd -apr1 $N8N_ADMIN_PASSWORD)" > "$HTPASSWD_FILE"
    fi

    chmod 644 "$HTPASSWD_FILE"

    print_success "htpasswd created for n8n admin interface"
    echo ""
    echo "n8n Admin Credentials:"
    echo "  Username: ${N8N_USER:-admin}"
    echo "  Password: $N8N_ADMIN_PASSWORD"
    echo ""
    print_warning "Save these credentials securely!"
}

# Function to display summary
display_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}              SSL CONFIGURATION COMPLETE                      ${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""

    if [ "$CERT_TYPE" == "letsencrypt" ]; then
        echo "🔒 SSL Certificate Status: ${GREEN}Let's Encrypt (Production)${NC}"
        echo "   • Domain: ${DOMAIN_NAME}"
        if [ "$USE_WWW" == "true" ]; then
            echo "   • WWW Domain: www.${DOMAIN_NAME}"
        fi
        echo "   • Valid for: 90 days"
        echo "   • Auto-renewal: Enabled (twice daily)"
    else
        echo "🔒 SSL Certificate Status: ${YELLOW}Self-Signed (Development)${NC}"
        echo "   ⚠️  Browsers will show security warning"
    fi

    echo ""
    echo "📝 Next Steps:"
    echo ""
    echo "1. Start the production stack:"
    echo "   ${BLUE}docker-compose -f docker-compose.production.yml up -d${NC}"
    echo ""
    echo "2. Access your services:"
    echo "   • Business Portal: https://${DOMAIN_NAME}"
    echo "   • API Endpoint: https://${DOMAIN_NAME}/api"
    echo "   • n8n Admin: https://${DOMAIN_NAME}/n8n"
    echo "   • Health Check: https://${DOMAIN_NAME}/health"
    echo ""

    if [ "$CERT_TYPE" == "letsencrypt" ]; then
        echo "3. Monitor certificate renewal:"
        echo "   ${BLUE}tail -f logs/ssl-renewal.log${NC}"
    else
        echo "3. For production, obtain a real certificate:"
        echo "   • Configure DNS to point to this server"
        echo "   • Re-run this script with correct domain"
    fi

    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
}

# Main execution
main() {
    show_header

    cd "$PROJECT_ROOT"

    # Run setup steps
    check_prerequisites
    test_dns
    create_ssl_directories
    generate_dhparam

    # Try to obtain Let's Encrypt certificate
    if obtain_letsencrypt_cert; then
        CERT_TYPE="letsencrypt"
        setup_renewal_cron
    else
        CERT_TYPE="self-signed"
    fi

    # Configure nginx
    create_nginx_ssl_config
    create_htpasswd
    create_renewal_script

    # Display summary
    display_summary

    print_success "SSL automation complete! 🎉"
}

# Run main function
main "$@"