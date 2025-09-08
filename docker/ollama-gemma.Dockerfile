# Ollama container with Gemma3:1b for MILHENA
# Shared development setup - works across all workstations

FROM ollama/ollama:latest

# Environment setup
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_MODELS=/root/.ollama

# Copy initialization script
COPY docker/init-ollama-gemma.sh /usr/local/bin/init-ollama-gemma.sh
RUN chmod +x /usr/local/bin/init-ollama-gemma.sh

# Create models directory
RUN mkdir -p /root/.ollama

# Expose Ollama port
EXPOSE 11434

# Health check
HEALTHCHECK --interval=60s --timeout=15s --start-period=120s --retries=3 \
  CMD curl -f http://localhost:11434/api/health || exit 1

# Start with initialization
CMD ["/usr/local/bin/init-ollama-gemma.sh"]