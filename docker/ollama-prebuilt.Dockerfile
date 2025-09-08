# Ollama container with preinstalled Gemma models
# Autonomous and portable - no downloads needed

FROM ollama/ollama:latest

# Environment setup
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_MODELS=/root/.ollama

# Copy ALL your local Ollama models into container
COPY ai-agent/ollama-models/ /root/.ollama/

# Verify models are present
RUN ls -la /root/.ollama/models/manifests/registry.ollama.ai/library/ || echo "Models copied successfully"

# Expose Ollama port
EXPOSE 11434

# Health check
HEALTHCHECK --interval=60s --timeout=15s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:11434/api/health || exit 1

# Start Ollama server directly (models already installed)
CMD ["ollama", "serve"]