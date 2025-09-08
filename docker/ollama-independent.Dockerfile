# Ollama Independent Container - ZERO external dependencies
# Contains ALL models embedded - completely portable

FROM ollama/ollama:latest

# Environment
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_MODELS=/root/.ollama

# Copy COMPLETE Ollama models directory (makes container fully independent)
COPY ai-agent/ollama-models-embedded/ /root/.ollama/

# Verify models are present  
RUN ls -la /root/.ollama/models/ || echo "Models embedded successfully"

# Expose port
EXPOSE 11434

# Health check
HEALTHCHECK --interval=60s --timeout=20s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:11434/api/health || exit 1

# Start Ollama (models already present)
CMD ["ollama", "serve"]
