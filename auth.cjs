#!/usr/bin/env node

/**
 * PilotProOS Security Module
 * Handles authentication and authorization
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { promisify } = require('util');

// Paths
const CONFIG_PATH = path.join(__dirname, 'auth-config.json');
const SESSION_PATH = path.join(__dirname, '.session');
const FAILED_ATTEMPTS_PATH = path.join(__dirname, '.failed-attempts.json');

// Load configuration
function loadConfig() {
  try {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  } catch (error) {
    // Default config if file doesn't exist
    return {
      auth: {
        enabled: false,
        method: 'password',
        maxAttempts: 3,
        lockoutMinutes: 15
      }
    };
  }
}

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = promisify(rl.question).bind(rl);

// Hide password input
function hideInput() {
  if (process.platform === 'win32') {
    // Windows
    return;
  }
  // Unix/Linux/Mac
  process.stdin.setRawMode(true);
}

// Restore normal input
function showInput() {
  if (process.platform === 'win32') {
    return;
  }
  process.stdin.setRawMode(false);
}

// Get password with hidden input
async function getPassword(prompt = 'Password: ') {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: true
    });

    // For cross-platform compatibility
    process.stdout.write(prompt);

    let password = '';

    process.stdin.on('data', (char) => {
      char = char.toString('utf8');

      switch (char) {
        case '\n':
        case '\r':
        case '\u0004':
          process.stdin.removeAllListeners('data');
          process.stdout.write('\n');
          rl.close();
          resolve(password);
          break;
        case '\u0003':
          // Handle Ctrl+C
          process.stdout.write('\n');
          process.exit();
          break;
        case '\u007f':
        case '\b':
          // Handle backspace
          if (password.length > 0) {
            password = password.slice(0, -1);
            process.stdout.write('\b \b');
          }
          break;
        default:
          password += char;
          process.stdout.write('*');
          break;
      }
    });

    if (process.stdin.setRawMode) {
      process.stdin.setRawMode(true);
    }
    process.stdin.resume();
  });
}

// Hash password
function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex');
}

// Check failed attempts
function checkLockout() {
  try {
    if (!fs.existsSync(FAILED_ATTEMPTS_PATH)) {
      return { locked: false, attempts: 0 };
    }

    const data = JSON.parse(fs.readFileSync(FAILED_ATTEMPTS_PATH, 'utf8'));
    const config = loadConfig();

    if (data.lockedUntil) {
      const now = Date.now();
      if (now < data.lockedUntil) {
        const remainingMinutes = Math.ceil((data.lockedUntil - now) / 60000);
        return {
          locked: true,
          message: `Account locked. Try again in ${remainingMinutes} minutes.`
        };
      }
    }

    return { locked: false, attempts: data.attempts || 0 };
  } catch (error) {
    return { locked: false, attempts: 0 };
  }
}

// Record failed attempt
function recordFailedAttempt() {
  const config = loadConfig();
  let data = { attempts: 0 };

  try {
    if (fs.existsSync(FAILED_ATTEMPTS_PATH)) {
      data = JSON.parse(fs.readFileSync(FAILED_ATTEMPTS_PATH, 'utf8'));
    }
  } catch (error) {
    // Start fresh if file is corrupted
  }

  data.attempts = (data.attempts || 0) + 1;
  data.lastAttempt = Date.now();

  if (data.attempts >= config.auth.maxAttempts) {
    data.lockedUntil = Date.now() + (config.auth.lockoutMinutes * 60000);
    data.attempts = 0;
  }

  fs.writeFileSync(FAILED_ATTEMPTS_PATH, JSON.stringify(data, null, 2));
}

// Clear failed attempts
function clearFailedAttempts() {
  try {
    fs.unlinkSync(FAILED_ATTEMPTS_PATH);
  } catch (error) {
    // File doesn't exist, that's okay
  }
}

// Create session
function createSession() {
  const sessionId = crypto.randomBytes(32).toString('hex');
  const sessionData = {
    id: sessionId,
    createdAt: Date.now(),
    expiresAt: Date.now() + (30 * 60000) // 30 minutes
  };

  fs.writeFileSync(SESSION_PATH, JSON.stringify(sessionData, null, 2));
  return sessionId;
}

// Validate session
function validateSession() {
  try {
    if (!fs.existsSync(SESSION_PATH)) {
      return false;
    }

    const session = JSON.parse(fs.readFileSync(SESSION_PATH, 'utf8'));
    const now = Date.now();

    if (now > session.expiresAt) {
      fs.unlinkSync(SESSION_PATH);
      return false;
    }

    // Extend session
    session.expiresAt = now + (30 * 60000);
    fs.writeFileSync(SESSION_PATH, JSON.stringify(session, null, 2));

    return true;
  } catch (error) {
    return false;
  }
}

// Authenticate user
async function authenticate() {
  const config = loadConfig();

  // Check if auth is disabled
  if (!config.auth || !config.auth.enabled) {
    return true;
  }

  // Check for existing valid session
  if (validateSession()) {
    return true;
  }

  // Check for lockout
  const lockStatus = checkLockout();
  if (lockStatus.locked) {
    console.error(`\n❌ ${lockStatus.message}`);
    process.exit(1);
  }

  console.log('\n🔐 Authentication Required\n');

  // Default credentials if not configured
  const validPassword = config.defaultPassword || 'PilotPro2025!';

  // Get password from user
  const password = await getPassword('Enter password: ');

  // Verify password
  if (password === validPassword || hashPassword(password) === config.passwordHash) {
    clearFailedAttempts();
    createSession();
    console.log('\n✅ Authentication successful!\n');
    return true;
  } else {
    recordFailedAttempt();
    const remaining = config.auth.maxAttempts - (lockStatus.attempts + 1);

    if (remaining > 0) {
      console.error(`\n❌ Invalid password. ${remaining} attempts remaining.\n`);
    } else {
      console.error(`\n❌ Too many failed attempts. Account locked.\n`);
    }

    process.exit(1);
  }
}

// Logout (clear session)
function logout() {
  try {
    fs.unlinkSync(SESSION_PATH);
    console.log('✅ Logged out successfully');
  } catch (error) {
    // Session doesn't exist
  }
}

// Export functions
module.exports = {
  authenticate,
  validateSession,
  logout,
  createSession,
  hashPassword,
  loadConfig
};

// If run directly, perform authentication
if (require.main === module) {
  authenticate().then(success => {
    if (success) {
      console.log('Access granted!');
      process.exit(0);
    }
  }).catch(error => {
    console.error('Authentication error:', error);
    process.exit(1);
  });
}