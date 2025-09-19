/**
 * Database Connection Compatibility Layer
 * Bridges the gap between old DatabaseConnection and new postgres/drizzle
 */

import { dbPool } from '../db/connection.js'

// Compatibility wrapper for legacy code
export class DatabaseConnection {
  static instance = null

  static getInstance() {
    if (!this.instance) {
      this.instance = new DatabaseConnection()
    }
    return this.instance
  }

  constructor() {
    this.pool = dbPool
  }

  async query(text, params = []) {
    try {
      const result = await this.pool.unsafe(text, params)
      return result
    } catch (error) {
      console.error('Database query error:', error)
      throw error
    }
  }

  async getOne(text, params = []) {
    const result = await this.query(text, params)
    return result[0] || null
  }

  async getMany(text, params = []) {
    return this.query(text, params)
  }
}

// Export singleton instance
export const db = DatabaseConnection.getInstance()