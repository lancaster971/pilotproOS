#!/bin/bash

# PilotProOS - Automatic Environment Detection and Configuration
# Detects system resources and selects appropriate docker-compose configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                      PilotProOS                           ║
║           Automatic Environment Detection                 ║
║                    Version 1.0.0                         ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

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

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        # Detect specific Linux distribution
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$NAME
            DISTRO_VERSION=$VERSION_ID
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macOS"
        DISTRO_VERSION=$(sw_vers -productVersion)
    else
        OS="unknown"
        DISTRO="Unknown"
        DISTRO_VERSION="Unknown"
    fi
}

# Function to detect system resources
detect_resources() {
    print_info "Detecting system resources..."

    # Detect RAM (in MB)
    if [ "$OS" == "linux" ]; then
        RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        RAM_MB=$((RAM_KB / 1024))
        RAM_GB=$((RAM_MB / 1024))
    elif [ "$OS" == "macos" ]; then
        RAM_BYTES=$(sysctl -n hw.memsize)
        RAM_MB=$((RAM_BYTES / 1024 / 1024))
        RAM_GB=$((RAM_MB / 1024))
    else
        print_error "Cannot detect RAM on this system"
        exit 1
    fi

    # Detect CPU cores
    if [ "$OS" == "linux" ]; then
        CPU_CORES=$(nproc)
    elif [ "$OS" == "macos" ]; then
        CPU_CORES=$(sysctl -n hw.ncpu)
    else
        CPU_CORES=1
    fi

    # Detect available disk space (in GB)
    DISK_AVAILABLE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')

    print_success "System Resources Detected:"
    echo "  • RAM: ${RAM_GB}GB (${RAM_MB}MB)"
    echo "  • CPU Cores: ${CPU_CORES}"
    echo "  • Disk Available: ${DISK_AVAILABLE}GB"
    echo "  • OS: ${DISTRO} ${DISTRO_VERSION}"
}

# Function to determine deployment tier
determine_tier() {
    print_info "Determining optimal deployment tier..."

    if [ $RAM_GB -le 2 ]; then
        TIER="development"
        COMPOSE_FILE="docker-compose.yml"
        print_warning "System has only ${RAM_GB}GB RAM. Using development configuration."
        print_warning "For production, minimum 2GB RAM is required."
    elif [ $RAM_GB -le 4 ]; then
        TIER="vps"
        COMPOSE_FILE="docker-compose.vps.yml"
        print_success "VPS tier selected (2-4GB RAM)"
    elif [ $RAM_GB -le 16 ]; then
        TIER="enterprise-s"
        COMPOSE_FILE="docker-compose.enterprise-s.yml"
        print_success "Enterprise Small tier selected (8-16GB RAM)"
    elif [ $RAM_GB -le 32 ]; then
        TIER="enterprise-m"
        COMPOSE_FILE="docker-compose.enterprise-s.yml"  # Use S config but with tuning
        print_success "Enterprise Medium tier selected (16-32GB RAM)"
        print_info "Using Enterprise-S configuration with enhanced limits"
    else
        TIER="enterprise-l"
        COMPOSE_FILE="docker-compose.enterprise-l.yml"
        print_success "Enterprise Large tier selected (32GB+ RAM)"
    fi

    echo ""
    echo "  📊 Deployment Tier: ${TIER^^}"
    echo "  📄 Configuration: ${COMPOSE_FILE}"
}

# Function to check Docker installation
check_docker() {
    print_info "Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo ""
        echo "Please install Docker first:"
        if [ "$OS" == "linux" ]; then
            echo "  curl -fsSL https://get.docker.com | sh"
            echo "  sudo usermod -aG docker $USER"
        elif [ "$OS" == "macos" ]; then
            echo "  Download Docker Desktop from: https://www.docker.com/products/docker-desktop"
        fi
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed!"
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running!"
        if [ "$OS" == "linux" ]; then
            echo "Try: sudo systemctl start docker"
        elif [ "$OS" == "macos" ]; then
            echo "Please start Docker Desktop"
        fi
        exit 1
    fi

    print_success "Docker is properly installed and running"
}

# Function to generate .env file
generate_env_file() {
    print_info "Generating environment configuration..."

    if [ -f .env.production ]; then
        print_warning ".env.production already exists"
        read -p "Do you want to overwrite it? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing configuration"
            return
        fi
    fi

    # Generate secure passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    JWT_SECRET=$(openssl rand -base64 64)
    SESSION_SECRET=$(openssl rand -base64 32)
    N8N_PASSWORD=$(openssl rand -base64 20)
    GRAFANA_PASSWORD=$(openssl rand -base64 20)
    REPLICATION_PASSWORD=$(openssl rand -base64 32)

    cat > .env.production << EOF
# PilotProOS Production Environment Configuration
# Generated on $(date)
# Tier: ${TIER^^}

# System Configuration
NODE_ENV=production
DEPLOYMENT_TIER=${TIER}
SYSTEM_RAM_GB=${RAM_GB}
SYSTEM_CPU_CORES=${CPU_CORES}

# Database Configuration
POSTGRES_USER=pilotpros_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=pilotpros_db

# Authentication Secrets
JWT_SECRET=${JWT_SECRET}
SESSION_SECRET=${SESSION_SECRET}

# n8n Configuration
N8N_HOST=localhost
N8N_PROTOCOL=https
N8N_USER=admin
N8N_PASSWORD=${N8N_PASSWORD}
WEBHOOK_URL=https://\${N8N_HOST}/webhook

# Frontend Configuration
FRONTEND_URL=https://localhost

# SSL Configuration (update with your domain)
DOMAIN_NAME=localhost
ADMIN_EMAIL=admin@localhost

# Monitoring (Enterprise tiers only)
GRAFANA_USER=admin
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}

# Replication (Enterprise-L only)
REPLICATION_USER=replicator
REPLICATION_PASSWORD=${REPLICATION_PASSWORD}
EOF

    chmod 600 .env.production
    print_success "Environment configuration generated (.env.production)"
    print_warning "⚠️  IMPORTANT: Save these passwords in a secure location!"
}

# Function to create required directories
create_directories() {
    print_info "Creating required directories..."

    directories=(
        "ssl"
        "monitoring"
        "monitoring/prometheus"
        "monitoring/grafana"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "backend/init-scripts"
        "nginx"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        fi
    done
}

# Function to create symbolic link for active configuration
create_symlink() {
    print_info "Setting up active configuration..."

    if [ -L docker-compose.production.yml ]; then
        rm docker-compose.production.yml
    fi

    ln -s ${COMPOSE_FILE} docker-compose.production.yml
    print_success "Created symlink: docker-compose.production.yml -> ${COMPOSE_FILE}"
}

# Function to optimize Docker daemon
optimize_docker() {
    print_info "Optimizing Docker daemon configuration..."

    DOCKER_CONFIG_DIR=""
    DOCKER_CONFIG_FILE=""

    if [ "$OS" == "linux" ]; then
        DOCKER_CONFIG_DIR="/etc/docker"
        DOCKER_CONFIG_FILE="${DOCKER_CONFIG_DIR}/daemon.json"
    elif [ "$OS" == "macos" ]; then
        print_info "Docker Desktop manages daemon configuration on macOS"
        return
    fi

    if [ ! -z "$DOCKER_CONFIG_FILE" ]; then
        # Create docker config directory if it doesn't exist
        if [ ! -d "$DOCKER_CONFIG_DIR" ]; then
            sudo mkdir -p "$DOCKER_CONFIG_DIR"
        fi

        # Check if we need sudo
        if [ -w "$DOCKER_CONFIG_FILE" ]; then
            SUDO=""
        else
            SUDO="sudo"
        fi

        # Create optimized daemon.json
        cat > /tmp/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "50m",
        "max-file": "5"
    },
    "storage-driver": "overlay2",
    "metrics-addr": "127.0.0.1:9323",
    "experimental": true
}
EOF

        if [ -f "$DOCKER_CONFIG_FILE" ]; then
            print_warning "Docker daemon.json already exists"
            print_info "Current configuration will be backed up"
            $SUDO cp "$DOCKER_CONFIG_FILE" "${DOCKER_CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        fi

        $SUDO mv /tmp/daemon.json "$DOCKER_CONFIG_FILE"

        print_success "Docker daemon optimized"
        print_warning "Docker daemon needs to be restarted for changes to take effect"
        read -p "Restart Docker daemon now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $SUDO systemctl restart docker
            print_success "Docker daemon restarted"
        fi
    fi
}

# Function to display deployment summary
display_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           DEPLOYMENT CONFIGURATION COMPLETE                  ${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "📊 System Profile:"
    echo "   • OS: ${DISTRO} ${DISTRO_VERSION}"
    echo "   • RAM: ${RAM_GB}GB"
    echo "   • CPU: ${CPU_CORES} cores"
    echo "   • Disk: ${DISK_AVAILABLE}GB available"
    echo ""
    echo "🚀 Deployment Configuration:"
    echo "   • Tier: ${TIER^^}"
    echo "   • Config: ${COMPOSE_FILE}"
    echo ""
    echo "📝 Next Steps:"
    echo ""
    echo "1. Update .env.production with your domain:"
    echo "   ${BLUE}nano .env.production${NC}"
    echo ""
    echo "2. Start the stack:"
    echo "   ${BLUE}docker-compose -f docker-compose.production.yml up -d${NC}"
    echo ""
    echo "3. Run SSL setup (after DNS is configured):"
    echo "   ${BLUE}./scripts/ssl-automation.sh${NC}"
    echo ""
    echo "4. Access your services:"
    echo "   • Business Portal: https://your-domain.com"
    echo "   • n8n Admin: https://your-domain.com:5678"
    echo "   • API: https://your-domain.com/api"

    if [[ "$TIER" == "enterprise-s" ]] || [[ "$TIER" == "enterprise-l" ]]; then
        echo "   • Monitoring: https://your-domain.com:3000 (Grafana)"
        echo "   • Metrics: https://your-domain.com:9090 (Prometheus)"
    fi

    if [[ "$TIER" == "enterprise-l" ]]; then
        echo "   • HAProxy Stats: https://your-domain.com:8404"
    fi

    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
}

# Main execution flow
main() {
    # Change to script directory
    cd "$(dirname "$0")/.."

    print_info "Starting PilotProOS environment detection..."
    echo ""

    # Run detection and configuration steps
    detect_os
    detect_resources
    determine_tier
    check_docker
    create_directories
    generate_env_file
    create_symlink
    optimize_docker

    # Display summary
    display_summary

    print_success "Configuration complete! 🎉"
}

# Run main function
main "$@"