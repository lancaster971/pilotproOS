#!/bin/bash

HEALTH_STATUS=0

check_service() {
    local name=$1
    local url=$2
    local port=$3

    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✓ $name (port $port): healthy"
        return 0
    else
        echo "✗ $name (port $port): unhealthy"
        return 1
    fi
}

echo "Intelligence Engine Health Check"
echo "================================="

check_service "Intelligence API" "http://localhost:8000/health" "8000" || HEALTH_STATUS=1

check_service "Intelligence Dashboard" "http://localhost:8501" "8501" || HEALTH_STATUS=1

check_service "Development Studio" "http://localhost:2024/docs" "2024" || true

if [ $HEALTH_STATUS -eq 0 ]; then
    echo ""
    echo "Status: All critical services healthy"
    exit 0
else
    echo ""
    echo "Status: Some services unhealthy"
    exit 1
fi
