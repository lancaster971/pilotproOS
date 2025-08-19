# Frontend Development Dockerfile
FROM node:18-alpine

# Install development dependencies
RUN apk add --no-cache git

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Development command with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]