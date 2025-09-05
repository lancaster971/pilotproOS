/**
 * API Configuration for Docker + Local Development
 * Automatically detects environment and uses correct backend URL
 */

// Detect if running in Docker container vs local browser
const isDocker = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'

// API base URL configuration
export const API_BASE_URL = isDocker 
  ? 'http://pilotpros-backend-dev:3001'  // Docker container network
  : 'http://localhost:3001'              // Local development

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
}

console.log(`🔧 API Config: ${isDocker ? 'Docker' : 'Local'} environment detected`)
console.log(`📡 Backend URL: ${API_BASE_URL}`)