#!/bin/bash
# Start LangGraph Studio with Milhena Graph
# This ensures LangGraph Studio always works with Milhena

echo "🎨 Starting LangGraph Studio with Milhena v3.0..."

# Kill any existing langgraph process
pkill -f "langgraph dev" 2>/dev/null

# Ensure we're in the right directory
cd /Volumes/BK12/Dropbox/Dropbox/TIZIANO/AI/PilotProOS/intelligence-engine

# Check if Docker container is running
if ! docker ps | grep -q "pilotpros-intelligence-engine-dev"; then
    echo "⚠️  Intelligence Engine container not running!"
    echo "Starting container..."
    cd ..
    ./stack-safe.sh start
    sleep 10
fi

# Export environment variables
export LANGCHAIN_API_KEY=$(grep LANGCHAIN_API_KEY .env | cut -d '=' -f2)
export LANGSMITH_API_KEY=$(grep LANGSMITH_API_KEY .env | cut -d '=' -f2)
export OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2)
export GROQ_API_KEY=$(grep GROQ_API_KEY .env | cut -d '=' -f2)

# Check if port 2024 is available (not used by Docker)
if lsof -Pi :2024 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ LangGraph Studio already running on port 2024 (Docker container)"
    echo ""
    echo "📊 Access LangGraph Studio at:"
    echo "   http://localhost:2024"
    echo ""
    echo "🎯 Or via LangSmith:"
    echo "   https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
    echo ""
    echo "📌 Select 'milhena' graph to see Milhena v3.0!"
else
    echo "Starting LangGraph Studio locally on port 2024..."

    # Start LangGraph dev server
    langgraph dev --port 2024 --host 0.0.0.0 &

    sleep 5

    echo ""
    echo "✅ LangGraph Studio started!"
    echo ""
    echo "📊 Access at:"
    echo "   http://localhost:2024"
    echo ""
    echo "🎯 Or via LangSmith:"
    echo "   https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
    echo ""
    echo "📌 Select 'milhena' graph to see Milhena v3.0!"
fi

echo ""
echo "🔍 Available Graphs:"
echo "   1. milhena - Business Workflow Assistant v3.0"
echo "   2. react_agent - Standard ReAct Agent"
echo ""
echo "Press Ctrl+C to stop LangGraph Studio"

# Keep script running
wait