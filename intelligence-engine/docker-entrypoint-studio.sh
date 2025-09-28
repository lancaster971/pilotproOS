#!/bin/bash
set -e

echo "🎨 Starting LangGraph Studio for Milhena..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-postgres-dev} ${DB_PORT:-5432}; do
    sleep 1
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis-dev} ${REDIS_PORT:-6379}; do
    sleep 1
done
echo "✅ Redis is ready!"

# Install langgraph-cli if not present
if ! command -v langgraph &> /dev/null; then
    echo "Installing langgraph-cli..."
    pip install -U "langgraph-cli[inmem]"
    export PATH="/home/appuser/.local/bin:$PATH"
fi

# Start LangGraph Studio
echo "🚀 Starting LangGraph Studio on port 2024..."
echo ""
echo "📊 Access at:"
echo "   Direct: http://localhost:2024"
echo "   Via LangSmith: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
echo ""
echo "Available graphs:"
echo "   - milhena: Business Workflow Assistant v3.0"
echo "   - react_agent: Standard ReAct Agent"
echo ""

# Start LangGraph dev server
cd /app
exec /home/appuser/.local/bin/langgraph dev --port 2024 --host 0.0.0.0