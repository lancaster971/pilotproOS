#!/bin/bash
set -e

echo "Intelligence Engine Supervisor Starting..."
echo "=============================================="

PIDS=()

cleanup() {
    echo ""
    echo "Stopping all microservices..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    wait
    echo "All services stopped"
    exit 0
}

trap cleanup SIGTERM SIGINT EXIT

start_service() {
    local name=$1
    local command=$2
    local port=$3

    echo "Starting $name (port $port)..."
    eval "$command" &
    local pid=$!
    PIDS+=($pid)
    echo "   PID: $pid"
}

monitor_service() {
    local name=$1
    local pid=$2
    local command=$3

    if ! kill -0 "$pid" 2>/dev/null; then
        echo "$name crashed! Restarting..."
        eval "$command" &
        local new_pid=$!
        PIDS=("${PIDS[@]/$pid/$new_pid}")
        echo "   New PID: $new_pid"
    fi
}

echo ""
echo "Starting Intelligence Engine microservices..."
echo "---------------------------------------------"

start_service "Intelligence API" "cd /app && uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info" "8000"
sleep 2

start_service "Intelligence Dashboard" "cd /app && streamlit run app/ui/dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true" "8501"
sleep 2

if [ -f "/home/appuser/.local/bin/langgraph" ]; then
    start_service "Development Studio" "cd /app && /home/appuser/.local/bin/langgraph dev --port 2024 --host 0.0.0.0 --no-browser" "2024"
    sleep 2
else
    echo "Development Studio CLI not found, skipping..."
fi

echo ""
echo "All microservices started successfully!"
echo ""
echo "Service Status:"
echo "  - Intelligence API:       http://0.0.0.0:8000"
echo "  - Intelligence Dashboard: http://0.0.0.0:8501"
echo "  - Development Studio:     http://0.0.0.0:2024"
echo ""
echo "Monitoring services (auto-restart on crash)..."
echo "   Press Ctrl+C to stop all services"
echo ""

while true; do
    sleep 30

    for i in "${!PIDS[@]}"; do
        pid="${PIDS[$i]}"

        case $i in
            0) monitor_service "Intelligence API" "$pid" "cd /app && uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info" ;;
            1) monitor_service "Intelligence Dashboard" "$pid" "cd /app && streamlit run app/ui/dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true" ;;
            2) monitor_service "Development Studio" "$pid" "cd /app && /home/appuser/.local/bin/langgraph dev --port 2024 --host 0.0.0.0 --no-browser" ;;
        esac
    done
done
