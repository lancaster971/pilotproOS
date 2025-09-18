/**
 * Authentication Middleware for Stack Controller
 * Protects web dashboard and API endpoints
 */

const crypto = require('crypto');
const jwt = require('jsonwebtoken');

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'PilotProOS-Secret-Key-2025';
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes

// In-memory session store (in production, use Redis or database)
const sessions = new Map();
const failedAttempts = new Map();

// Default credentials (should be changed in production)
const DEFAULT_CREDENTIALS = {
  username: 'admin',
  password: 'PilotPro2025!'
};

/**
 * Hash password using SHA256
 */
function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex');
}

/**
 * Generate JWT token
 */
function generateToken(username) {
  return jwt.sign(
    {
      username,
      timestamp: Date.now(),
      role: 'admin'
    },
    JWT_SECRET,
    { expiresIn: '24h' }
  );
}

/**
 * Verify JWT token
 */
function verifyToken(token) {
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    return decoded;
  } catch (error) {
    return null;
  }
}

/**
 * Check if IP is locked due to failed attempts
 */
function isLocked(ip) {
  const attempts = failedAttempts.get(ip);
  if (!attempts) return false;

  // Lock for 15 minutes after 5 failed attempts
  if (attempts.count >= 5) {
    const lockTime = 15 * 60 * 1000; // 15 minutes
    const timeSinceLast = Date.now() - attempts.lastAttempt;

    if (timeSinceLast < lockTime) {
      return true;
    } else {
      // Reset after lockout period
      failedAttempts.delete(ip);
      return false;
    }
  }

  return false;
}

/**
 * Record failed login attempt
 */
function recordFailedAttempt(ip) {
  const attempts = failedAttempts.get(ip) || { count: 0, lastAttempt: Date.now() };
  attempts.count++;
  attempts.lastAttempt = Date.now();
  failedAttempts.set(ip, attempts);
}

/**
 * Clear failed attempts for IP
 */
function clearFailedAttempts(ip) {
  failedAttempts.delete(ip);
}

/**
 * Basic authentication check
 */
function checkBasicAuth(authHeader) {
  if (!authHeader || !authHeader.startsWith('Basic ')) {
    return false;
  }

  const base64 = authHeader.substring(6);
  const decoded = Buffer.from(base64, 'base64').toString('utf-8');
  const [username, password] = decoded.split(':');

  return username === DEFAULT_CREDENTIALS.username &&
         password === DEFAULT_CREDENTIALS.password;
}

/**
 * Authentication middleware
 */
function authMiddleware(req, res, next) {
  // Skip auth for health check
  if (req.path === '/health') {
    return next();
  }

  // Skip auth for login endpoint
  if (req.path === '/api/auth/login') {
    return next();
  }

  // Allow static assets without auth (but not the main page)
  if (req.path.match(/\.(css|js|png|jpg|ico)$/)) {
    return next();
  }

  const ip = req.ip || req.connection.remoteAddress;

  // Check if IP is locked
  if (isLocked(ip)) {
    return res.status(429).json({
      error: 'Too many failed attempts. Please try again later.'
    });
  }

  // Check for JWT token in header or cookie
  const token = req.headers.authorization?.replace('Bearer ', '') ||
                req.cookies?.token;

  if (token) {
    const decoded = verifyToken(token);
    if (decoded) {
      req.user = decoded;
      return next();
    }
  }

  // Check for basic auth
  if (checkBasicAuth(req.headers.authorization)) {
    req.user = { username: DEFAULT_CREDENTIALS.username, role: 'admin' };
    return next();
  }

  // Check session
  const sessionId = req.headers['x-session-id'] || req.cookies?.sessionId;
  if (sessionId && sessions.has(sessionId)) {
    const session = sessions.get(sessionId);
    if (Date.now() - session.createdAt < SESSION_TIMEOUT) {
      req.user = session.user;
      // Extend session
      session.createdAt = Date.now();
      return next();
    } else {
      sessions.delete(sessionId);
    }
  }

  // No valid authentication found
  res.status(401).json({
    error: 'Authentication required',
    message: 'Please login to access this resource'
  });
}

/**
 * Login endpoint handler
 */
function loginHandler(req, res) {
  const { username, password } = req.body;
  const ip = req.ip || req.connection.remoteAddress;

  // Check if IP is locked
  if (isLocked(ip)) {
    return res.status(429).json({
      error: 'Too many failed attempts. Please try again later.'
    });
  }

  // Validate credentials
  if (username === DEFAULT_CREDENTIALS.username &&
      password === DEFAULT_CREDENTIALS.password) {

    // Clear failed attempts
    clearFailedAttempts(ip);

    // Generate token
    const token = generateToken(username);

    // Create session
    const sessionId = crypto.randomBytes(32).toString('hex');
    sessions.set(sessionId, {
      user: { username, role: 'admin' },
      createdAt: Date.now()
    });

    // Log successful login
    console.log(`[AUTH] Successful login from ${ip} for user: ${username}`);

    res.json({
      success: true,
      token,
      sessionId,
      user: { username, role: 'admin' }
    });
  } else {
    // Record failed attempt
    recordFailedAttempt(ip);

    // Log failed attempt
    console.warn(`[AUTH] Failed login attempt from ${ip} for user: ${username}`);

    res.status(401).json({
      error: 'Invalid credentials'
    });
  }
}

/**
 * Logout endpoint handler
 */
function logoutHandler(req, res) {
  const sessionId = req.headers['x-session-id'] || req.cookies?.sessionId;

  if (sessionId) {
    sessions.delete(sessionId);
  }

  res.json({
    success: true,
    message: 'Logged out successfully'
  });
}

/**
 * Rate limiting middleware
 */
const rateLimitMap = new Map();

function rateLimit(windowMs = 900000, max = 100) {
  return (req, res, next) => {
    const ip = req.ip || req.connection.remoteAddress;
    const now = Date.now();
    const windowStart = now - windowMs;

    // Get or create rate limit data for this IP
    let requests = rateLimitMap.get(ip) || [];

    // Filter out old requests outside the window
    requests = requests.filter(timestamp => timestamp > windowStart);

    // Check if limit exceeded
    if (requests.length >= max) {
      return res.status(429).json({
        error: 'Rate limit exceeded',
        message: 'Too many requests, please try again later'
      });
    }

    // Add current request
    requests.push(now);
    rateLimitMap.set(ip, requests);

    next();
  };
}

module.exports = {
  authMiddleware,
  loginHandler,
  logoutHandler,
  rateLimit,
  generateToken,
  verifyToken
};