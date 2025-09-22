/**
 * PostgreSQL Pool Connection
 * Shared instance for authentication and raw queries
 */

import { Pool } from 'pg';

// PostgreSQL Pool for raw queries and authentication
export const dbPool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  user: process.env.DB_USER || 'pilotpros_user',
  password: process.env.DB_PASSWORD || 'pilotpros_password',
  database: process.env.DB_NAME || 'pilotpros_db',
  max: parseInt(process.env.DB_POOL_SIZE || '20'),
  idleTimeoutMillis: parseInt(process.env.DB_IDLE_TIMEOUT || '30000'),
  connectionTimeoutMillis: parseInt(process.env.DB_CONNECTION_TIMEOUT || '5000'),
});

export default dbPool;