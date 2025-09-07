#!/bin/bash

# MILHENA AI Agent Startup Script
# Starts MILHENA with Ollama Gemma:2b in Docker containers

set -e

echo "🤖 MILHENA AI Agent - Startup Script"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop first."
    exit 1
fi

print_status "Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose not found. Please install Docker Compose."
    exit 1
fi

print_status "Docker Compose is available"

# Create logs directory for MILHENA
mkdir -p logs/milhena-agent-dev
print_status "Created logs directory"

# Start MILHENA services
print_info "Starting MILHENA AI Agent services..."

# Start Ollama container first
print_info "Starting Ollama service..."
docker-compose -f docker-compose.dev.yml up -d milhena-ollama

# Wait for Ollama to be healthy
print_info "Waiting for Ollama to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose -f docker-compose.dev.yml ps milhena-ollama | grep -q "healthy"; then
        print_status "Ollama is ready!"
        break
    fi
    
    print_info "Attempt $attempt/$max_attempts - Waiting for Ollama..."
    sleep 10
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    print_error "Ollama failed to start within expected time"
    docker-compose -f docker-compose.dev.yml logs milhena-ollama
    exit 1
fi

# Check if Gemma:2b model needs to be downloaded
print_info "Checking Gemma:2b model availability..."
OLLAMA_CONTAINER=$(docker-compose -f docker-compose.dev.yml ps -q milhena-ollama)

if docker exec $OLLAMA_CONTAINER ollama list | grep -q "gemma:2b"; then
    print_status "Gemma:2b model already available"
else
    print_info "Downloading Gemma:2b model (this may take several minutes)..."
    docker exec $OLLAMA_CONTAINER sh -c "ollama pull gemma:2b" || {
        print_warning "Model download in progress - MILHENA will download it automatically"
    }
fi

# Start MILHENA Agent
print_info "Starting MILHENA Agent..."
docker-compose -f docker-compose.dev.yml up -d milhena-agent-dev

# Wait for MILHENA to be ready
print_info "Waiting for MILHENA Agent to be ready..."
max_attempts=20
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:3002/api/health >/dev/null 2>&1; then
        print_status "MILHENA Agent is ready!"
        break
    fi
    
    print_info "Attempt $attempt/$max_attempts - Waiting for MILHENA Agent..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    print_error "MILHENA Agent failed to start within expected time"
    echo ""
    print_info "Checking MILHENA Agent logs:"
    docker-compose -f docker-compose.dev.yml logs --tail=20 milhena-agent-dev
    exit 1
fi

# Test MILHENA functionality
print_info "Testing MILHENA functionality..."
test_response=$(curl -s -X POST http://localhost:3002/api/chat \
    -H "Content-Type: application/json" \
    -d '{"query":"Ciao MILHENA, funzioni correttamente?"}' || echo "error")

if [[ $test_response == *"error"* ]]; then
    print_warning "MILHENA might still be initializing. This is normal on first startup."
else
    print_status "MILHENA responded successfully!"
fi

# Show final status
echo ""
echo "🎉 MILHENA AI Agent Status:"
echo "=========================="
print_status "Ollama (Gemma:2b): http://localhost:11434"
print_status "MILHENA Agent API: http://localhost:3002/api/health"
print_status "Chat Endpoint: http://localhost:3002/api/chat"

echo ""
print_info "Test MILHENA with curl:"
echo 'curl -X POST http://localhost:3002/api/chat \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"query":"Mostra lo stato dei processi"}'"'"

echo ""
print_info "View logs with:"
echo "docker-compose -f docker-compose.dev.yml logs -f milhena-agent-dev"

echo ""
print_info "Stop MILHENA with:"
echo "docker-compose -f docker-compose.dev.yml stop milhena-agent-dev milhena-ollama"

print_status "MILHENA AI Agent startup complete!"