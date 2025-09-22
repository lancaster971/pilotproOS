/**
 * Redis Session Configuration
 *
 * Implements reliable session management with Redis store
 * Replaces custom session handling for better scalability
 */

import session from 'express-session';
import RedisStore from 'connect-redis';
import { createClient } from 'redis';

// Initialize Redis client
const redisClient = createClient({
  socket: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
  },
  password: process.env.REDIS_PASSWORD || undefined,
});

// Handle Redis connection events
redisClient.on('error', (err) => {
  console.error('Redis Client Error:', err);
});

redisClient.on('connect', () => {
  console.log('Connected to Redis successfully');
});

redisClient.on('ready', () => {
  console.log('Redis client ready');
});

// Connect to Redis
await redisClient.connect();

// Create session configuration
export const sessionConfig = {
  store: new RedisStore({
    client: redisClient,
    prefix: 'pilotpros:sess:',
  }),
  secret: process.env.SESSION_SECRET || 'fallback-secret-change-in-production',
  resave: false,
  saveUninitialized: false,
  name: 'pilotpros_session',
  cookie: {
    secure: process.env.NODE_ENV === 'production', // HTTPS only in production
    httpOnly: true, // Prevent XSS attacks
    maxAge: 1000 * 60 * 30, // 30 minutes
    sameSite: 'strict', // CSRF protection
  },
  rolling: true, // Extend session on activity
};

export { redisClient };