# AI Agent Development Dockerfile
FROM node:20-alpine

# Install development dependencies
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    postgresql-client

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with dev dependencies
RUN npm install

# Install development tools
RUN npm install -g nodemon typescript

# Copy source code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "http.get('http://localhost:3002/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })" || exit 1

# Development command
CMD ["npm", "run", "dev"]