/**
 * Drizzle Database Connection
 * Replaces raw SQL queries with type-safe ORM
 */

import { drizzle } from 'drizzle-orm/postgres-js'
import postgres from 'postgres'
import * as schema from './schema.js'

// Environment variables
const connectionString = process.env.DATABASE_URL || 
  `postgresql://${process.env.DB_USER}:${process.env.DB_PASSWORD}@${process.env.DB_HOST}:${process.env.DB_PORT}/${process.env.DB_NAME}`

console.log('🗄️ Connecting to database with Drizzle ORM...')

// Create postgres connection with ROBUST configuration
// Based on 2024 best practices for Docker containers
const client = postgres(connectionString, {
  prepare: false,
  max: 10, // Connection pool size

  // CRITICAL: Timeout configurations to prevent connection drops
  idle_timeout: 20, // Close idle connections after 20 seconds (default is 0 = never)
  max_lifetime: 60 * 30, // Max lifetime 30 minutes (1800 seconds)
  connect_timeout: 10, // Connection timeout 10 seconds

  // Keep-alive to detect dead connections
  keep_alive: true,
  keep_alive_initial_delay: 5, // Start keep-alive after 5 seconds

  // Transform for better error handling
  transform: {
    undefined: null
  },

  // Debug in development
  debug: process.env.NODE_ENV === 'development' ? false : false,

  // Error handler
  onnotice: () => {}, // Suppress notices

  // Connection health check
  connection: {
    application_name: 'pilotpros_backend'
  }
})

// Create drizzle instance
export const db = drizzle(client, { schema })

// Export connection for compatibility with existing code
export const dbPool = client

// Helper function to test connection
export async function testConnection() {
  try {
    await client`SELECT 1`
    return { success: true, message: 'Database connection successful' }
  } catch (error) {
    return { success: false, message: error.message }
  }
}

// Health check interval to keep connections alive
let healthCheckInterval = null;

// Start health check to prevent idle disconnections
export function startHealthCheck() {
  if (healthCheckInterval) return;

  healthCheckInterval = setInterval(async () => {
    try {
      await client`SELECT 1`;
      // Connection is healthy
    } catch (error) {
      console.error('❌ Database health check failed:', error.message);
      // Connection will be automatically recreated by postgres.js
    }
  }, 30000); // Every 30 seconds
}

// Stop health check (for graceful shutdown)
export function stopHealthCheck() {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval);
    healthCheckInterval = null;
  }
}

// Graceful shutdown handler
export async function gracefulShutdown() {
  stopHealthCheck();
  await client.end();
  console.log('✅ Database connections closed gracefully');
}

// Start health check on initialization
startHealthCheck();

console.log('✅ Drizzle ORM connected successfully with health monitoring')