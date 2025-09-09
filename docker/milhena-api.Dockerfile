# MILHENA API Container - Claude API Integration
# Fast, reliable, lightweight - no local AI complexity

FROM node:20-alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code - ALL files including n8n-mcp implementation
COPY src/ ./src/

# Create logs directory
RUN mkdir -p logs && chown -R node:node logs

# Switch to non-root user
USER node

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3002/api/health || exit 1

# Expose port
EXPOSE 3002

# Start MILHENA n8n-MCP Server
CMD ["node", "src/milhena-mcp-server.js"]