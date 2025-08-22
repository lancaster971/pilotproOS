# Frontend Development Dockerfile - Vue 3 + TypeScript
FROM node:20-alpine

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

# Set environment variables for Vue 3 + Vite in Docker
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true
ENV VITE_HOST=0.0.0.0
ENV VITE_PORT=3000

# Expose port
EXPOSE 3000

# Health check for Vue/Vite
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Development command - Vue 3 with Vite
CMD ["npm", "run", "dev"]