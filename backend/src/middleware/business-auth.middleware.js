/**
 * Business API Authentication Middleware
 *
 * Protegge tutte le route /api/business/* con autenticazione JWT
 * e controlli di autorizzazione basati su ruoli
 */

import { getAuthService } from '../auth/jwt-auth.js';
import rateLimit from 'express-rate-limit';

const authService = getAuthService();

/**
 * Route pubbliche che NON richiedono autenticazione
 * (per future implementazioni se necessario)
 */
const PUBLIC_ROUTES = [
  // SSE endpoints for execution tracking - secured by execution verification
  '/api/business/processes/*/execution-stream',
];

/**
 * Route che richiedono ruolo admin
 */
const ADMIN_ONLY_ROUTES = [
  '/api/business/execute-workflow',
  '/api/business/toggle-workflow',
  '/api/business/stop-workflow',
  '/api/business/test-error-notification',
];

/**
 * Route che richiedono permessi di scrittura
 */
const WRITE_PERMISSION_ROUTES = [
  '/api/business/execute-workflow',
  '/api/business/toggle-workflow',
  '/api/business/stop-workflow',
];

/**
 * Rate limiting per operazioni critiche
 */
export const criticalOperationLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minuto
  max: 10, // max 10 richieste per finestra
  message: 'Too many requests for critical operations',
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    console.error(`⚠️ Rate limit exceeded for ${req.ip} on ${req.path}`);
    res.status(429).json({
      success: false,
      error: 'Too Many Requests',
      message: 'Please wait before performing more operations',
      retryAfter: 60
    });
  }
});

/**
 * Rate limiting standard per letture
 */
export const standardRateLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minuto
  max: 100, // max 100 richieste per finestra
  message: 'Too many requests',
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Middleware principale di autenticazione per Business API
 */
export const businessAuthMiddleware = async (req, res, next) => {
  try {
    // Extract the actual path from baseUrl and path
    const fullPath = req.baseUrl + (req.path === '/' ? '' : req.path);
    const relativePath = fullPath.replace(/^\/api\/business/, '/api/business');

    console.log(`🔐 [Business Auth] Checking: ${req.method} ${relativePath}`);

    // 1. Check if route is public (with wildcard support)
    const isPublicRoute = PUBLIC_ROUTES.some(route => {
      // Convert wildcard pattern to regex
      if (route.includes('*')) {
        const pattern = route.replace(/\*/g, '.*');
        const regex = new RegExp(`^${pattern}$`);
        return regex.test(relativePath);
      }
      return relativePath.startsWith(route);
    });

    if (isPublicRoute) {
      console.log(`✅ [Business Auth] Public route, skipping auth`);
      return next();
    }

    // 2. Extract and verify token
    const authHeader = req.headers.authorization;
    const cookieToken = req.cookies?.access_token;

    let token = null;

    // Priority: Bearer token > Cookie token
    if (authHeader?.startsWith('Bearer ')) {
      token = authHeader.substring(7);
    } else if (cookieToken) {
      token = cookieToken;
    }

    if (!token) {
      console.log(`❌ [Business Auth] No token provided`);
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required to access business resources'
      });
    }

    // 3. Verify token and get user
    let user;
    try {
      const decoded = authService.verifyToken(token);

      // For access tokens, get full user data
      if (decoded.type === 'access') {
        user = {
          id: decoded.userId,
          role: decoded.role,
          permissions: decoded.permissions || []
        };
      } else {
        throw new Error('Invalid token type for API access');
      }
    } catch (error) {
      console.log(`❌ [Business Auth] Token verification failed: ${error.message}`);

      // Check if token is expired and we have refresh token
      if (error.message.includes('expired') && req.cookies?.refresh_token) {
        // Try to auto-refresh
        try {
          const refreshResult = await authService.refreshAccessToken(req.cookies.refresh_token);
          authService.setAuthCookies(res, refreshResult.accessToken, refreshResult.refreshToken);
          user = refreshResult.user;
          console.log(`✅ [Business Auth] Token auto-refreshed for user ${user.id}`);
        } catch (refreshError) {
          console.log(`❌ [Business Auth] Auto-refresh failed: ${refreshError.message}`);
          return res.status(401).json({
            success: false,
            error: 'Unauthorized',
            message: 'Session expired. Please login again.'
          });
        }
      } else {
        return res.status(401).json({
          success: false,
          error: 'Unauthorized',
          message: 'Invalid or expired token'
        });
      }
    }

    // 4. Check admin-only routes
    const isAdminRoute = ADMIN_ONLY_ROUTES.some(route =>
      relativePath.startsWith(route)
    );

    if (isAdminRoute && user.role !== 'admin') {
      console.log(`❌ [Business Auth] Admin access required for ${relativePath}`);
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'Administrator privileges required'
      });
    }

    // 5. Check write permissions for POST/PUT/DELETE
    const isWriteOperation = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(req.method);
    const needsWritePermission = isWriteOperation || WRITE_PERMISSION_ROUTES.some(route =>
      relativePath.startsWith(route)
    );

    if (needsWritePermission) {
      const hasWritePermission =
        user.role === 'admin' ||
        user.permissions?.includes('workflows:write') ||
        user.permissions?.includes('*');

      if (!hasWritePermission) {
        console.log(`❌ [Business Auth] Write permission denied for ${user.id}`);
        return res.status(403).json({
          success: false,
          error: 'Forbidden',
          message: 'Write permissions required for this operation'
        });
      }
    }

    // 6. Attach user to request
    req.user = user;

    // 7. Log successful auth
    console.log(`✅ [Business Auth] Authorized: User ${user.id} (${user.role}) -> ${req.method} ${relativePath}`);

    // 8. Apply rate limiting based on operation type
    if (ADMIN_ONLY_ROUTES.some(route => relativePath.startsWith(route))) {
      criticalOperationLimiter(req, res, next);
    } else {
      standardRateLimiter(req, res, next);
    }

  } catch (error) {
    console.error('❌ [Business Auth] Unexpected error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: 'Authentication processing failed'
    });
  }
};

/**
 * Middleware per verificare specifici permessi
 */
export const requirePermission = (permission) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized',
        message: 'Authentication required'
      });
    }

    const hasPermission =
      req.user.role === 'admin' ||
      req.user.permissions?.includes(permission) ||
      req.user.permissions?.includes('*');

    if (!hasPermission) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: `Permission required: ${permission}`
      });
    }

    next();
  };
};

/**
 * Middleware per verificare ruolo admin
 */
export const requireAdmin = (req, res, next) => {
  if (!req.user) {
    return res.status(401).json({
      success: false,
      error: 'Unauthorized',
      message: 'Authentication required'
    });
  }

  if (req.user.role !== 'admin') {
    return res.status(403).json({
      success: false,
      error: 'Forbidden',
      message: 'Administrator privileges required'
    });
  }

  next();
};