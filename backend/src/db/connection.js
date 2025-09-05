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

// Create postgres connection
const client = postgres(connectionString, { 
  prepare: false,
  max: 10 // Connection pool size
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

console.log('✅ Drizzle ORM connected successfully')