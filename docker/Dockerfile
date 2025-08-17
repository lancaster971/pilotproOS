# PilotProOS Dockerfile - Business Process Operating System
# Multi-stage build for production deployment

# ============================================================================
# STAGE 1: Base System with Dependencies
# ============================================================================
FROM ubuntu:22.04 as base

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    gnupg \
    lsb-release \
    ca-certificates \
    software-properties-common \
    supervisor \
    nginx \
    postgresql-14 \
    postgresql-client-14 \
    postgresql-contrib-14 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install n8n globally
RUN npm install -g n8n@latest pm2

# ============================================================================
# STAGE 2: PostgreSQL Configuration
# ============================================================================
FROM base as postgres-config

# Configure PostgreSQL for container use
RUN echo "host all all 127.0.0.1/32 md5" >> /etc/postgresql/14/main/pg_hba.conf \
    && echo "listen_addresses = 'localhost'" >> /etc/postgresql/14/main/postgresql.conf

# PostgreSQL optimization for PilotProOS
COPY docker/config/postgresql.conf /etc/postgresql/14/main/conf.d/pilotpros.conf

# ============================================================================
# STAGE 3: Application Build
# ============================================================================
FROM postgres-config as app-build

# Create pilotpros user
RUN useradd -r -s /bin/bash -d /opt/pilotpros -m pilotpros

# Create directory structure
RUN mkdir -p /opt/pilotpros/{backend,frontend,ai-agent,n8n,logs,database,scripts}

# Copy PilotProOS application
COPY backend/ /opt/pilotpros/backend/
COPY frontend/ /opt/pilotpros/frontend/
COPY ai-agent/ /opt/pilotpros/ai-agent/
COPY scripts/ /opt/pilotpros/scripts/
COPY templates/ /opt/pilotpros/templates/

# Install backend dependencies
WORKDIR /opt/pilotpros/backend
RUN npm install --production

# Build frontend
WORKDIR /opt/pilotpros/frontend
RUN npm install && npm run build

# Install AI Agent dependencies
WORKDIR /opt/pilotpros/ai-agent
RUN npm install --production

# ============================================================================
# STAGE 4: Production Configuration
# ============================================================================
FROM app-build as production

# Copy supervisor configuration
COPY docker/config/supervisor/ /etc/supervisor/conf.d/

# Copy nginx configuration template
COPY docker/config/nginx/ /etc/nginx/sites-available/

# Copy database schema
COPY scripts/database/ /opt/pilotpros/database/

# Copy docker entrypoint and scripts
COPY docker/scripts/docker-entrypoint.sh /docker-entrypoint.sh
COPY docker/scripts/health-check.sh /opt/pilotpros/scripts/health-check.sh

# Make scripts executable
RUN chmod +x /docker-entrypoint.sh \
    && chmod +x /opt/pilotpros/scripts/*.sh

# Set proper ownership
RUN chown -R pilotpros:pilotpros /opt/pilotpros

# Copy frontend build to nginx directory
RUN cp -r /opt/pilotpros/frontend/dist/* /var/www/html/

# Create log directories
RUN mkdir -p /var/log/pilotpros \
    && chown pilotpros:pilotpros /var/log/pilotpros

# Expose only public ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD /opt/pilotpros/scripts/health-check.sh

# Set working directory
WORKDIR /opt/pilotpros

# Entrypoint script handles runtime configuration
ENTRYPOINT ["/docker-entrypoint.sh"]

# Start supervisor to manage all services
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf", "-n"]

# Metadata
LABEL maintainer="PilotPro Team"
LABEL description="PilotProOS - Business Process Operating System"
LABEL version="1.0.0"
LABEL vendor="PilotPro"