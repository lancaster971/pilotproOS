/**
 * Authentication Rate Limiting Middleware
 *
 * Protegge gli endpoint di autenticazione da attacchi brute force
 * e implementa progressive delays per tentativi falliti
 */

import rateLimit from 'express-rate-limit';

// Per ora usiamo memory store, Redis può essere aggiunto in seguito
// quando necessario per scalare su più istanze

/**
 * Login Rate Limiter - MOLTO RESTRITTIVO
 * Previene attacchi brute force su login
 */
export const loginRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minuti
  max: 5, // max 5 tentativi di login per IP
  message: 'Too many login attempts, please try again later',
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true, // Non conta i login riusciti
  handler: (req, res) => {
    console.error(`🚫 [Rate Limit] Login blocked for IP: ${req.ip}`);
    res.status(429).json({
      success: false,
      error: 'Too Many Attempts',
      message: 'Account temporarily locked due to multiple failed login attempts. Please try again in 15 minutes.',
      retryAfter: 900 // secondi
    });
  },
  // Custom key generator per account-based limiting
  keyGenerator: (req) => {
    // Combina IP + email per limitare per account
    const email = req.body?.email?.toLowerCase() || 'unknown';
    return `${req.ip}:${email}`;
  }
});

/**
 * Password Reset Rate Limiter
 * Previene spam di reset password
 */
export const passwordResetLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 ora
  max: 3, // max 3 richieste di reset per ora
  message: 'Too many password reset requests',
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    console.warn(`⚠️ [Rate Limit] Password reset blocked for: ${req.body?.email}`);
    res.status(429).json({
      success: false,
      error: 'Too Many Requests',
      message: 'Maximum password reset attempts exceeded. Please try again in 1 hour.',
      retryAfter: 3600
    });
  },
  keyGenerator: (req) => {
    const email = req.body?.email?.toLowerCase() || req.ip;
    return email;
  }
});

/**
 * Registration Rate Limiter
 * Previene creazione massiva di account
 */
export const registrationLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 ora
  max: 2, // max 2 registrazioni per IP per ora
  message: 'Too many accounts created from this IP',
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    console.warn(`⚠️ [Rate Limit] Registration blocked for IP: ${req.ip}`);
    res.status(429).json({
      success: false,
      error: 'Too Many Accounts',
      message: 'Maximum account creation limit reached. Please try again later.',
      retryAfter: 3600
    });
  }
});

/**
 * API Key Validation Rate Limiter
 * Per proteggere validazione API keys
 */
export const apiKeyLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minuti
  max: 30, // max 30 validazioni per 15 minuti
  message: 'Too many API key validation attempts',
  standardHeaders: true,
  legacyHeaders: false
});

/**
 * Progressive Delay Middleware
 * Aggiunge delay progressivo dopo tentativi falliti
 */
const failedAttempts = new Map();

export const progressiveDelay = (req, res, next) => {
  const key = `${req.ip}:${req.body?.email || 'unknown'}`;
  const attempts = failedAttempts.get(key) || 0;

  if (attempts > 0) {
    // Delay esponenziale: 0, 1s, 2s, 4s, 8s, 16s...
    const delay = Math.min(Math.pow(2, attempts - 1) * 1000, 30000); // max 30 secondi
    console.log(`⏱️ [Progressive Delay] ${delay}ms for ${key} (attempt ${attempts})`);

    setTimeout(() => {
      next();
    }, delay);
  } else {
    next();
  }
};

/**
 * Record Failed Login Attempt
 */
export const recordFailedLogin = (req) => {
  const key = `${req.ip}:${req.body?.email || 'unknown'}`;
  const attempts = (failedAttempts.get(key) || 0) + 1;
  failedAttempts.set(key, attempts);

  // Cleanup dopo 30 minuti
  setTimeout(() => {
    failedAttempts.delete(key);
  }, 30 * 60 * 1000);

  console.log(`❌ [Auth] Failed login attempt ${attempts} for ${key}`);
};

/**
 * Clear Failed Attempts on Success
 */
export const clearFailedAttempts = (req) => {
  const key = `${req.ip}:${req.body?.email || 'unknown'}`;
  failedAttempts.delete(key);
  console.log(`✅ [Auth] Cleared failed attempts for ${key}`);
};

/**
 * Cleanup on shutdown
 */
export const cleanupRateLimiting = async () => {
  failedAttempts.clear();
  console.log('✅ Rate limiting cleanup complete');
};