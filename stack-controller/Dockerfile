FROM node:18-alpine

WORKDIR /app

# Install Docker CLI for container management
RUN apk add --no-cache docker-cli

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy application files
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3005/health || exit 1

EXPOSE 3005

CMD ["node", "src/index.js"]