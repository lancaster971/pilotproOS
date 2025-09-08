#!/bin/bash

# MILHENA Ollama Initialization Script
# Pre-downloads Gemma3:1b for shared development

echo "🤖 MILHENA - Ollama Gemma3:1b Initialization"
echo "============================================"

# Start Ollama service in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
sleep 15

# Download Gemma3:1b model (smaller than gemma:2b)
echo "📥 Downloading Gemma3:1b (815MB)..."
ollama pull gemma3:1b

# Test model
echo "🧪 Testing Gemma3:1b model..."
echo "Ciao, sono MILHENA!" | ollama run gemma3:1b

# Keep Ollama running
wait $OLLAMA_PID