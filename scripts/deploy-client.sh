#!/bin/bash
# PilotProOS Master Deployment Script
# One-command client deployment for Business Process Operating System

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }

# Header
echo -e "${PURPLE}"
cat << 'EOF'
██████╗ ██╗██╗      ██████╗ ████████╗██████╗ ██████╗  ██████╗  ██████╗ ███████╗
██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔════╝
██████╔╝██║██║     ██║   ██║   ██║   ██████╔╝██████╔╝██║   ██║███████╗███████╗
██╔═══╝ ██║██║     ██║   ██║   ██║   ██╔═══╝ ██╔══██╗██║   ██║╚════██║╚════██║
██║     ██║███████╗╚██████╔╝   ██║   ██║     ██║  ██║╚██████╔╝███████║███████║
╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝
EOF
echo -e "${NC}"

log "🚀 PilotProOS - Business Process Operating System"
log "================================================"
log "One-command deployment for business automation"
log ""

# Configuration
DOMAIN=${1:-"localhost"}
ADMIN_PASSWORD=${2:-$(openssl rand -base64 24)}
START_TIME=$(date +%s)

log "📋 Deployment Configuration:"
log "   Domain: $DOMAIN"
log "   Deployment Mode: Complete Stack"
log "   Start Time: $(date)"
log ""

# Verification
if [[ $EUID -ne 0 ]]; then
   error "Script must be run as root: sudo ./deploy-client.sh"
fi

# Phase execution
run_phase() {
    local phase_name="$1"
    local script_name="$2"
    local estimated_time="$3"
    
    log "🔄 $phase_name"
    log "   Script: $script_name"
    log "   Estimated: $estimated_time"
    
    local phase_start=$(date +%s)
    
    if bash "deployment/$script_name" "$DOMAIN" "$ADMIN_PASSWORD"; then
        local phase_end=$(date +%s)
        local duration=$((phase_end - phase_start))
        success "$phase_name completed in ${duration}s"
    else
        error "$phase_name failed"
    fi
    log ""
}

log "🚀 Starting PilotProOS deployment phases..."
log ""

# Execute 4-phase deployment
run_phase "Phase 1/4: System Infrastructure" "01-system-setup.sh" "60s"
run_phase "Phase 2/4: Application Stack" "02-application-deploy.sh" "120s"  
run_phase "Phase 3/4: Security & Anonimization" "03-security-hardening.sh" "90s"
run_phase "Phase 4/4: Business Automation" "04-workflow-automation.sh" "60s"

# Calculate total time
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
MINUTES=$((TOTAL_DURATION / 60))
SECONDS=$((TOTAL_DURATION % 60))

# Success message
echo -e "${GREEN}"
cat << 'EOF'
🎉 DEPLOYMENT SUCCESSFUL!
========================
EOF
echo -e "${NC}"

log "⏱️ Total Time: ${MINUTES}m ${SECONDS}s"
log "🌐 Client Access: http${SSL_STATUS}://$DOMAIN"
log "🤖 AI Assistant: Integrated and ready"
log "🔒 Security: Enterprise-grade"
log "📊 Analytics: Real-time business insights"
log ""
success "PilotProOS Ready for Business Use!"
log "🎯 Your Business Process Operating System is operational!"