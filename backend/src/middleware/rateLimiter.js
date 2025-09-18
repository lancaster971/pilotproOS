/**
 * Rate Limiting Middleware
 * Configurable rate limiting for different endpoints
 * Resolves rate limiting technical debt
 */

import rateLimit from 'express-rate-limit';
import config from '../config/index.js';

/**
 * Create a rate limiter with specific configuration
 * @param {Object} options - Rate limiter options
 * @returns {Function} Rate limiter middleware
 */
const createRateLimiter = (options = {}) => {
  const defaultOptions = {
    windowMs: config.rateLimit.windowMs,
    max: config.rateLimit.maxRequests,
    message: 'Too many requests from this IP, please try again later.',
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
      res.status(429).json({
        error: 'Too Many Requests',
        message: options.message || 'Too many requests from this IP, please try again later.',
        retryAfter: Math.ceil(options.windowMs / 1000),
        limit: options.max,
      });
    },
  };

  return rateLimit({ ...defaultOptions, ...options });
};

/**
 * Global rate limiter for all requests
 */
export const globalRateLimiter = config.rateLimit.enabled
  ? createRateLimiter()
  : (req, res, next) => next(); // Pass-through if disabled

/**
 * Strict rate limiter for authentication endpoints
 */
export const authRateLimiter = config.rateLimit.enabled
  ? createRateLimiter({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 5, // 5 requests per window
      message: 'Too many authentication attempts, please try again later.',
      skipSuccessfulRequests: true, // Don't count successful requests
    })
  : (req, res, next) => next();

/**
 * API rate limiter for general API endpoints
 */
export const apiRateLimiter = config.rateLimit.enabled
  ? createRateLimiter({
      windowMs: config.rateLimit.windowMs,
      max: config.rateLimit.maxRequests,
    })
  : (req, res, next) => next();

/**
 * Heavy operations rate limiter (exports, reports, etc.)
 */
export const heavyOperationRateLimiter = config.rateLimit.enabled
  ? createRateLimiter({
      windowMs: 5 * 60 * 1000, // 5 minutes
      max: 10, // 10 requests per window
      message: 'Too many resource-intensive requests, please try again later.',
    })
  : (req, res, next) => next();

/**
 * WebSocket connection rate limiter
 */
export const wsRateLimiter = config.rateLimit.enabled
  ? createRateLimiter({
      windowMs: 60 * 1000, // 1 minute
      max: 20, // 20 connection attempts per minute
      message: 'Too many WebSocket connection attempts.',
    })
  : (req, res, next) => next();

/**
 * Dynamic rate limiter based on user role
 * Premium users get higher limits
 */
export const dynamicRateLimiter = (multiplier = 1) => {
  if (!config.rateLimit.enabled) {
    return (req, res, next) => next();
  }

  return (req, res, next) => {
    // Check if user is authenticated and get their role
    const userRole = req.user?.role || 'anonymous';

    // Set different limits based on role
    let maxRequests = config.rateLimit.maxRequests;
    switch (userRole) {
      case 'admin':
        maxRequests = maxRequests * 10; // Admins get 10x limit
        break;
      case 'premium':
        maxRequests = maxRequests * 5; // Premium users get 5x limit
        break;
      case 'user':
        maxRequests = maxRequests * 2; // Regular users get 2x limit
        break;
      default:
        // Anonymous users get base limit
        break;
    }

    const limiter = createRateLimiter({
      max: Math.floor(maxRequests * multiplier),
      keyGenerator: (req) => {
        // Use user ID if authenticated, otherwise use IP
        return req.user?.id || req.ip;
      },
    });

    limiter(req, res, next);
  };
};

/**
 * Skip rate limiting for certain conditions
 */
export const skipRateLimit = (condition) => {
  return (req, res, next) => {
    if (condition(req)) {
      return next();
    }
    return apiRateLimiter(req, res, next);
  };
};

/**
 * Rate limiter with Redis store for distributed systems
 * This is a placeholder for future Redis implementation
 */
export const createRedisRateLimiter = (options = {}) => {
  if (!config.redis.enabled) {
    // Fallback to memory store if Redis is not enabled
    return createRateLimiter(options);
  }

  // TODO: Implement Redis store when Redis is configured
  // For now, use memory store
  return createRateLimiter({
    ...options,
    // store: new RedisStore({
    //   client: redisClient,
    //   prefix: 'rl:',
    // }),
  });
};

export default {
  globalRateLimiter,
  authRateLimiter,
  apiRateLimiter,
  heavyOperationRateLimiter,
  wsRateLimiter,
  dynamicRateLimiter,
  skipRateLimit,
  createRateLimiter,
  createRedisRateLimiter,
};