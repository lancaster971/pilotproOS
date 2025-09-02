#!/bin/bash

# ==============================================================================
# PilotProSetUpEngine - Anonymous Docker Images Builder
# ==============================================================================
# Purpose: Build completely anonymized Docker images for PilotProOS
# Target: Remove all technical branding and replace with business terminology
# Version: 1.0.0
# ==============================================================================

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Docker registry configuration
REGISTRY="${DOCKER_REGISTRY:-docker.io}"
NAMESPACE="${DOCKER_NAMESPACE:-pilotpros}"
VERSION="${VERSION:-1.0.0}"
PUSH_TO_REGISTRY="${PUSH_TO_REGISTRY:-false}"

# Build configuration
BUILD_DIR="${BUILD_DIR:-./docker}"
CACHE_FROM="${CACHE_FROM:-}"
BUILD_ARGS="${BUILD_ARGS:-}"

# Image names (business-friendly)
declare -A IMAGES=(
    ["automation-engine"]="Automation Engine"
    ["business-database"]="Business Database"
    ["business-api"]="Business API"
    ["business-dashboard"]="Business Dashboard"
    ["web-gateway"]="Web Gateway"
)

# Colors for output
readonly COLOR_BLUE='\033[1;34m'
readonly COLOR_GREEN='\033[1;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_RED='\033[1;31m'
readonly COLOR_CYAN='\033[1;36m'
readonly COLOR_RESET='\033[0m'
readonly BOLD='\033[1m'

# ==============================================================================
# LOGGING FUNCTIONS
# ==============================================================================

log_header() {
    echo ""
    echo -e "${COLOR_CYAN}${BOLD}═══════════════════════════════════════════════════════${COLOR_RESET}"
    echo -e "${COLOR_CYAN}${BOLD}  $1${COLOR_RESET}"
    echo -e "${COLOR_CYAN}${BOLD}═══════════════════════════════════════════════════════${COLOR_RESET}"
    echo ""
}

log_info() {
    echo -e "${COLOR_BLUE}ℹ️  $1${COLOR_RESET}"
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

# ==============================================================================
# DOCKERFILE GENERATORS
# ==============================================================================

# Generate Dockerfile for Automation Engine (anonymized n8n)
generate_automation_engine_dockerfile() {
    cat > "${BUILD_DIR}/automation-engine/Dockerfile" << 'EOF'
# Automation Engine - Business Process Automation Platform
# Based on n8n but completely anonymized for business use

FROM n8nio/n8n:1.108.1 AS base

# Remove all n8n branding
LABEL maintainer="PilotPro Systems <support@pilotpro.com>"
LABEL vendor="PilotPro Systems"
LABEL name="pilotpros-automation-engine"
LABEL version="1.0.0"
LABEL description="Enterprise Business Process Automation Engine"
LABEL org.opencontainers.image.title="Business Automation Engine"
LABEL org.opencontainers.image.vendor="PilotPro Systems"

# Business-friendly environment variables
ENV APPLICATION_NAME="Business Automation Platform" \
    DEPLOYMENT_TYPE="enterprise" \
    PLATFORM_VERSION="1.0.0" \
    VENDOR_NAME="PilotPro Systems"

# Disable all telemetry and external connections
ENV N8N_DIAGNOSTICS_ENABLED="false" \
    N8N_VERSION_NOTIFICATIONS_ENABLED="false" \
    N8N_TEMPLATES_ENABLED="false" \
    N8N_PERSONALIZATION_ENABLED="false" \
    N8N_ANONYMOUS_TELEMETRY="false" \
    N8N_HIDE_USAGE_PAGE="true"

# Configure logging to hide technical details
ENV N8N_LOG_LEVEL="error" \
    N8N_LOG_OUTPUT="file" \
    N8N_LOG_FILE_LOCATION="/var/log/automation.log"

# Create business-friendly directories
RUN mkdir -p /var/business-automation \
    /var/business-automation/workflows \
    /var/business-automation/credentials \
    /var/business-automation/logs

# Custom entrypoint to filter technical output
COPY docker-entrypoint-wrapper.sh /entrypoint-wrapper.sh
RUN chmod +x /entrypoint-wrapper.sh

# Override user folder location
ENV N8N_USER_FOLDER=/var/business-automation

WORKDIR /var/business-automation

ENTRYPOINT ["/entrypoint-wrapper.sh"]
CMD ["automation-engine"]
EOF

    # Create entrypoint wrapper
    cat > "${BUILD_DIR}/automation-engine/docker-entrypoint-wrapper.sh" << 'WRAPPER'
#!/bin/sh
# Wrapper to hide technical output and provide business-friendly messages

# Function to filter technical logs
filter_logs() {
    sed -e 's/n8n/automation engine/gi' \
        -e 's/workflow/business process/gi' \
        -e 's/node/process step/gi' \
        -e 's/webhook/integration endpoint/gi' \
        -e 's/trigger/event handler/gi' \
        -e 's/execution/process run/gi'
}

# Start the original entrypoint but filter output
exec tini -- /docker-entrypoint.sh "$@" 2>&1 | filter_logs
WRAPPER
}

# Generate Dockerfile for Business Database (anonymized PostgreSQL)
generate_business_database_dockerfile() {
    cat > "${BUILD_DIR}/business-database/Dockerfile" << 'EOF'
# Business Database - Enterprise Data Platform
# Based on PostgreSQL but branded for business use

FROM postgres:16-alpine AS base

# Business branding
LABEL maintainer="PilotPro Systems <support@pilotpro.com>"
LABEL vendor="PilotPro Systems"
LABEL name="pilotpros-business-database"
LABEL version="1.0.0"
LABEL description="Enterprise Business Data Platform"

# Business-friendly environment
ENV POSTGRES_DB="business_platform" \
    POSTGRES_USER="business_admin" \
    PGDATA="/var/lib/business-data"

# Create business schemas on initialization
COPY init-business-schemas.sql /docker-entrypoint-initdb.d/01-init.sql
COPY health-check.sh /usr/local/bin/business-health-check
RUN chmod +x /usr/local/bin/business-health-check

# Business-friendly healthcheck
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD /usr/local/bin/business-health-check

# Custom logging configuration
COPY postgresql-business.conf /etc/postgresql/postgresql.conf

VOLUME ["/var/lib/business-data"]

EXPOSE 5432

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
EOF

    # Create initialization SQL
    cat > "${BUILD_DIR}/business-database/init-business-schemas.sql" << 'SQL'
-- Business Platform Database Initialization
-- Creates dual-schema architecture for business and automation

-- Create business schema
CREATE SCHEMA IF NOT EXISTS business;
COMMENT ON SCHEMA business IS 'Business platform core data';

-- Create automation schema
CREATE SCHEMA IF NOT EXISTS automation;
COMMENT ON SCHEMA automation IS 'Process automation data';

-- Business tables
CREATE TABLE IF NOT EXISTS business.organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS business.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50),
    organization_id INTEGER REFERENCES business.organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS business.audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES business.users(id),
    action VARCHAR(100),
    resource VARCHAR(100),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_audit_log_created ON business.audit_log(created_at DESC);
CREATE INDEX idx_users_email ON business.users(email);

-- Grant permissions
GRANT ALL ON SCHEMA business TO business_admin;
GRANT ALL ON SCHEMA automation TO business_admin;
SQL

    # Create health check script
    cat > "${BUILD_DIR}/business-database/health-check.sh" << 'HEALTH'
#!/bin/sh
pg_isready -U business_admin -d business_platform || exit 1
HEALTH
}

# Generate Dockerfile for Business API
generate_business_api_dockerfile() {
    cat > "${BUILD_DIR}/business-api/Dockerfile" << 'EOF'
# Business API - Enterprise Service Layer
FROM node:20-alpine AS base

LABEL maintainer="PilotPro Systems <support@pilotpro.com>"
LABEL vendor="PilotPro Systems"
LABEL name="pilotpros-business-api"
LABEL version="1.0.0"
LABEL description="Enterprise Business API Gateway"

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Business-friendly environment
ENV NODE_ENV="production" \
    SERVICE_NAME="Business API" \
    LOG_LEVEL="info"

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

EXPOSE 3001

CMD ["node", "src/server.js"]
EOF
}

# Generate Dockerfile for Business Dashboard
generate_business_dashboard_dockerfile() {
    cat > "${BUILD_DIR}/business-dashboard/Dockerfile" << 'EOF'
# Business Dashboard - Enterprise UI Platform
FROM node:20-alpine AS builder

WORKDIR /app

# Build stage
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine AS production

LABEL maintainer="PilotPro Systems <support@pilotpro.com>"
LABEL vendor="PilotPro Systems"
LABEL name="pilotpros-business-dashboard"
LABEL version="1.0.0"
LABEL description="Enterprise Business Dashboard"

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Business-friendly nginx configuration
COPY nginx-business.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF
}

# Generate Dockerfile for Web Gateway
generate_web_gateway_dockerfile() {
    cat > "${BUILD_DIR}/web-gateway/Dockerfile" << 'EOF'
# Web Gateway - Enterprise Traffic Router
FROM nginx:alpine AS base

LABEL maintainer="PilotPro Systems <support@pilotpro.com>"
LABEL vendor="PilotPro Systems"
LABEL name="pilotpros-web-gateway"
LABEL version="1.0.0"
LABEL description="Enterprise Web Gateway"

# Remove nginx branding
RUN sed -i 's/nginx/Business Platform/g' /usr/share/nginx/html/index.html

# Copy business configuration
COPY gateway-business.conf /etc/nginx/nginx.conf
COPY ssl-business.conf /etc/nginx/conf.d/ssl.conf

# Create SSL directory
RUN mkdir -p /etc/ssl/business

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
EOF
}

# ==============================================================================
# BUILD FUNCTIONS
# ==============================================================================

prepare_build_context() {
    log_info "Preparing build contexts..."
    
    # Create directory structure
    mkdir -p "${BUILD_DIR}"/{automation-engine,business-database,business-api,business-dashboard,web-gateway}
    
    # Generate all Dockerfiles
    generate_automation_engine_dockerfile
    generate_business_database_dockerfile
    generate_business_api_dockerfile
    generate_business_dashboard_dockerfile
    generate_web_gateway_dockerfile
    
    log_success "Build contexts prepared"
}

build_image() {
    local image_name=$1
    local display_name=$2
    local dockerfile_path="${BUILD_DIR}/${image_name}/Dockerfile"
    
    log_info "Building ${display_name}..."
    
    # Construct build command
    local build_cmd="docker build"
    
    # Add cache if specified
    if [[ -n "${CACHE_FROM}" ]]; then
        build_cmd="${build_cmd} --cache-from ${CACHE_FROM}"
    fi
    
    # Add build args if specified
    if [[ -n "${BUILD_ARGS}" ]]; then
        build_cmd="${build_cmd} ${BUILD_ARGS}"
    fi
    
    # Add tags
    build_cmd="${build_cmd} -t ${NAMESPACE}/${image_name}:${VERSION}"
    build_cmd="${build_cmd} -t ${NAMESPACE}/${image_name}:latest"
    
    # Add dockerfile and context
    build_cmd="${build_cmd} -f ${dockerfile_path} ${BUILD_DIR}/${image_name}"
    
    # Execute build
    if ${build_cmd}; then
        log_success "${display_name} built successfully"
        return 0
    else
        log_error "Failed to build ${display_name}"
        return 1
    fi
}

build_all_images() {
    log_header "Building Anonymous Docker Images"
    
    local failed_builds=()
    
    for image_name in "${!IMAGES[@]}"; do
        if ! build_image "${image_name}" "${IMAGES[${image_name}]}"; then
            failed_builds+=("${image_name}")
        fi
    done
    
    if [[ ${#failed_builds[@]} -gt 0 ]]; then
        log_error "Failed to build: ${failed_builds[*]}"
    else
        log_success "All images built successfully"
    fi
}

# ==============================================================================
# REGISTRY FUNCTIONS
# ==============================================================================

push_to_registry() {
    log_header "Pushing Images to Registry"
    
    # Login to registry if credentials provided
    if [[ -n "${DOCKER_USERNAME:-}" ]] && [[ -n "${DOCKER_PASSWORD:-}" ]]; then
        log_info "Logging into registry..."
        echo "${DOCKER_PASSWORD}" | docker login "${REGISTRY}" -u "${DOCKER_USERNAME}" --password-stdin
    fi
    
    # Push each image
    for image_name in "${!IMAGES[@]}"; do
        log_info "Pushing ${IMAGES[${image_name}]}..."
        
        docker push "${NAMESPACE}/${image_name}:${VERSION}"
        docker push "${NAMESPACE}/${image_name}:latest"
        
        log_success "${IMAGES[${image_name}]} pushed"
    done
    
    log_success "All images pushed to registry"
}

# ==============================================================================
# VERIFICATION
# ==============================================================================

verify_images() {
    log_header "Verifying Built Images"
    
    echo -e "${COLOR_CYAN}Built Images:${COLOR_RESET}"
    echo ""
    
    for image_name in "${!IMAGES[@]}"; do
        local full_image="${NAMESPACE}/${image_name}:${VERSION}"
        
        if docker image inspect "${full_image}" &> /dev/null; then
            local size=$(docker image inspect "${full_image}" --format='{{.Size}}' | numfmt --to=iec)
            echo -e "  ✅ ${IMAGES[${image_name}]}: ${COLOR_GREEN}${full_image}${COLOR_RESET} (${size})"
        else
            echo -e "  ❌ ${IMAGES[${image_name}]}: ${COLOR_RED}Not found${COLOR_RESET}"
        fi
    done
    
    echo ""
    
    # Show total size
    local total_size=$(docker images "${NAMESPACE}/*" --format "{{.Size}}" | \
        awk '{s+=$1} END {print s}' | numfmt --to=iec)
    
    echo -e "${COLOR_CYAN}Total Size: ${total_size}${COLOR_RESET}"
}

# ==============================================================================
# CLEANUP
# ==============================================================================

cleanup_build_context() {
    if [[ "${KEEP_BUILD_CONTEXT:-false}" != "true" ]]; then
        log_info "Cleaning up build context..."
        rm -rf "${BUILD_DIR}"
        log_success "Build context cleaned"
    fi
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

show_header() {
    clear
    echo -e "${COLOR_CYAN}${BOLD}"
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════════╗
    ║               PilotPro Anonymous Image Builder                   ║
    ║                                                                   ║
    ║     Building business-friendly Docker images with complete       ║
    ║        anonymization of technical infrastructure                 ║
    ╚═══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${COLOR_RESET}"
    echo ""
}

main() {
    show_header
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --push)
                PUSH_TO_REGISTRY=true
                shift
                ;;
            --version)
                VERSION="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --registry)
                REGISTRY="$2"
                shift 2
                ;;
            --keep-context)
                KEEP_BUILD_CONTEXT=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                ;;
        esac
    done
    
    log_info "Configuration:"
    log_info "  Registry:  ${REGISTRY}"
    log_info "  Namespace: ${NAMESPACE}"
    log_info "  Version:   ${VERSION}"
    log_info "  Push:      ${PUSH_TO_REGISTRY}"
    echo ""
    
    # Execute build process
    prepare_build_context
    build_all_images
    verify_images
    
    # Push if requested
    if [[ "${PUSH_TO_REGISTRY}" == "true" ]]; then
        push_to_registry
    fi
    
    # Cleanup
    cleanup_build_context
    
    echo ""
    log_success "Build process completed successfully!"
    echo ""
    echo -e "${COLOR_CYAN}Next steps:${COLOR_RESET}"
    echo -e "  1. Test images locally: ${COLOR_GREEN}docker-compose up${COLOR_RESET}"
    echo -e "  2. Push to registry:    ${COLOR_GREEN}$0 --push${COLOR_RESET}"
    echo -e "  3. Deploy to production: ${COLOR_GREEN}./install-master.sh${COLOR_RESET}"
    echo ""
}

# Only run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi