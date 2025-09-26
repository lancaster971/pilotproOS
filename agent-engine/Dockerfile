FROM python:3.11-slim

# FUCK CREWAI - SISTEMA DIRETTO!
LABEL maintainer="Direct Implementation - No CrewAI bullshit"
LABEL description="Agent Engine DIRETTO senza framework inutili"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements PULITI
COPY requirements.txt .

# Install Python dependencies SENZA CREWAI
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check DIRETTO
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the DIRECT application
CMD ["python", "main.py"]