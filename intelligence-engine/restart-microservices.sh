#!/bin/bash

echo "Stopping Intelligence Microservices..."

# Kill running services
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "  - Intelligence API stopped" || echo "  - Intelligence API not running"
pkill -f "streamlit run" 2>/dev/null && echo "  - Intelligence Dashboard stopped" || echo "  - Intelligence Dashboard not running"
pkill -f "langgraph dev" 2>/dev/null && echo "  - Development Studio stopped" || echo "  - Development Studio not running"

sleep 2

echo ""
echo "Starting microservices via supervisor..."
/app/supervisor.sh &

echo "Microservices restart initiated"
