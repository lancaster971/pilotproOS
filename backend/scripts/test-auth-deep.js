#!/usr/bin/env node

/**
 * Deep Authentication Testing Script
 * Tests all authentication scenarios and edge cases
 */

import fetch from 'node-fetch';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import * as dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '../../.env') });

const API_URL = process.env.API_URL || 'http://localhost:3001';

// Color codes for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

// Test result tracking
let testsPassed = 0;
let testsFailed = 0;
const errors = [];

// Helper functions
function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logTest(name) {
  log(`\n📝 Testing: ${name}`, colors.cyan);
}

function logSuccess(message) {
  testsPassed++;
  log(`  ✅ ${message}`, colors.green);
}

function logError(message, details = null) {
  testsFailed++;
  const errorMsg = `  ❌ ${message}`;
  log(errorMsg, colors.red);
  if (details) {
    console.error('     Details:', details);
    errors.push({ test: message, error: details });
  }
}

// Cookie storage for session tests
let cookies = {};

function parseCookies(response) {
  const setCookieHeaders = response.headers.raw()['set-cookie'] || [];
  setCookieHeaders.forEach(cookie => {
    const [nameValue] = cookie.split(';');
    const [name, value] = nameValue.split('=');
    cookies[name] = value;
  });
}

function getCookieString() {
  return Object.entries(cookies).map(([name, value]) => `${name}=${value}`).join('; ');
}

// Test functions
async function testLogin(email, password) {
  logTest('Login with valid credentials');

  try {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });

    parseCookies(response);
    const data = await response.json();

    if (response.ok) {
      logSuccess(`Login successful for ${email}`);

      // Check response structure
      if (data.user?.id) {
        logSuccess('User ID present');
      } else {
        logError('User ID missing in response');
      }

      if (data.user?.permissions?.length > 0) {
        logSuccess(`Permissions loaded: ${data.user.permissions.length} permissions`);
      } else {
        logError('No permissions in response');
      }

      // Check cookies
      if (cookies.access_token) {
        logSuccess('Access token cookie set');
      } else {
        logError('Access token cookie missing');
      }

      if (cookies.refresh_token) {
        logSuccess('Refresh token cookie set');
      } else {
        logError('Refresh token cookie missing');
      }

      return { success: true, data, cookies };
    } else {
      logError(`Login failed: ${data.message || data.error}`);
      return { success: false, error: data };
    }
  } catch (error) {
    logError('Login request failed', error.message);
    return { success: false, error: error.message };
  }
}

async function testInvalidLogin() {
  logTest('Login with invalid credentials');

  try {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: 'invalid@test.com',
        password: 'wrongpassword'
      })
    });

    const data = await response.json();

    if (response.status === 401) {
      logSuccess('Invalid login correctly rejected');
      return true;
    } else {
      logError(`Invalid login not rejected properly: Status ${response.status}`);
      return false;
    }
  } catch (error) {
    logError('Invalid login test failed', error.message);
    return false;
  }
}

async function testProtectedRoute() {
  logTest('Access protected route with token');

  try {
    const response = await fetch(`${API_URL}/api/workflows`, {
      method: 'GET',
      headers: {
        'Cookie': getCookieString()
      }
    });

    if (response.ok) {
      logSuccess('Protected route accessed successfully');
      return true;
    } else {
      logError(`Protected route failed: Status ${response.status}`);
      return false;
    }
  } catch (error) {
    logError('Protected route test failed', error.message);
    return false;
  }
}

async function testProtectedRouteWithoutAuth() {
  logTest('Access protected route without authentication');

  try {
    const response = await fetch(`${API_URL}/api/workflows`, {
      method: 'GET'
    });

    if (response.status === 401) {
      logSuccess('Protected route correctly blocked without auth');
      return true;
    } else {
      logError(`Protected route not blocked: Status ${response.status}`);
      return false;
    }
  } catch (error) {
    logError('Protected route test failed', error.message);
    return false;
  }
}

async function testRefreshToken() {
  logTest('Refresh token flow');

  try {
    const response = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Cookie': `refresh_token=${cookies.refresh_token}`
      }
    });

    if (response.ok) {
      parseCookies(response);
      logSuccess('Token refreshed successfully');

      if (cookies.access_token) {
        logSuccess('New access token received');
      } else {
        logError('New access token not set');
      }

      return true;
    } else {
      logError(`Token refresh failed: Status ${response.status}`);
      return false;
    }
  } catch (error) {
    logError('Token refresh test failed', error.message);
    return false;
  }
}

async function testLogout() {
  logTest('Logout flow');

  try {
    const response = await fetch(`${API_URL}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Cookie': getCookieString()
      }
    });

    if (response.ok) {
      parseCookies(response);
      logSuccess('Logout successful');

      // Check if cookies are cleared
      const clearedCookies = response.headers.raw()['set-cookie'] || [];
      const hasMaxAge0 = clearedCookies.some(c => c.includes('Max-Age=0'));

      if (hasMaxAge0) {
        logSuccess('Auth cookies cleared');
      } else {
        logError('Auth cookies not properly cleared');
      }

      return true;
    } else {
      logError(`Logout failed: Status ${response.status}`);
      return false;
    }
  } catch (error) {
    logError('Logout test failed', error.message);
    return false;
  }
}

async function testCORS() {
  logTest('CORS headers');

  try {
    const response = await fetch(`${API_URL}/api/auth/config`, {
      method: 'GET',
      headers: {
        'Origin': 'http://localhost:3000'
      }
    });

    const corsHeader = response.headers.get('access-control-allow-origin');
    const credentialsHeader = response.headers.get('access-control-allow-credentials');

    if (corsHeader) {
      logSuccess(`CORS origin allowed: ${corsHeader}`);
    } else {
      logError('No CORS headers present');
    }

    if (credentialsHeader === 'true') {
      logSuccess('CORS credentials enabled');
    } else {
      logError('CORS credentials not enabled');
    }

    return true;
  } catch (error) {
    logError('CORS test failed', error.message);
    return false;
  }
}

async function testSecurityHeaders() {
  logTest('Security headers');

  try {
    const response = await fetch(`${API_URL}/api/auth/config`);

    const securityHeaders = {
      'x-content-type-options': 'nosniff',
      'x-frame-options': 'SAMEORIGIN',
      'x-xss-protection': '0',
      'strict-transport-security': 'max-age=15552000'
    };

    let allPresent = true;
    for (const [header, expectedValue] of Object.entries(securityHeaders)) {
      const value = response.headers.get(header);
      if (value) {
        logSuccess(`${header}: ${value}`);
      } else {
        logError(`Missing security header: ${header}`);
        allPresent = false;
      }
    }

    return allPresent;
  } catch (error) {
    logError('Security headers test failed', error.message);
    return false;
  }
}

async function testRateLimit() {
  logTest('Rate limiting');

  try {
    // Make multiple rapid requests
    const promises = [];
    for (let i = 0; i < 5; i++) {
      promises.push(
        fetch(`${API_URL}/api/auth/config`)
      );
    }

    const responses = await Promise.all(promises);
    const lastResponse = responses[responses.length - 1];

    const limitHeader = lastResponse.headers.get('ratelimit-limit');
    const remainingHeader = lastResponse.headers.get('ratelimit-remaining');

    if (limitHeader) {
      logSuccess(`Rate limit configured: ${limitHeader} requests`);
    } else {
      logError('No rate limit headers found');
    }

    if (remainingHeader) {
      logSuccess(`Remaining requests: ${remainingHeader}`);
    }

    return true;
  } catch (error) {
    logError('Rate limit test failed', error.message);
    return false;
  }
}

async function testSessionPersistence() {
  logTest('Session persistence across requests');

  const cookieString = getCookieString();

  try {
    // Test multiple protected endpoints
    const endpoints = [
      '/api/workflows',
      '/api/executions',
      '/api/auth/profile'
    ];

    let allPassed = true;
    for (const endpoint of endpoints) {
      const response = await fetch(`${API_URL}${endpoint}`, {
        headers: {
          'Cookie': cookieString
        }
      });

      if (response.ok || response.status === 404) {
        logSuccess(`Session valid for ${endpoint}`);
      } else if (response.status === 401) {
        logError(`Session invalid for ${endpoint}`);
        allPassed = false;
      }
    }

    return allPassed;
  } catch (error) {
    logError('Session persistence test failed', error.message);
    return false;
  }
}

// Main test runner
async function runTests() {
  log('\n🔍 DEEP AUTHENTICATION TESTING', colors.blue);
  log('=' .repeat(50), colors.blue);

  // Get test credentials
  const email = process.argv[2] || 'tiziano@gmail.com';
  const password = process.argv[3] || 'PilotPro2025!';

  log(`\n📧 Testing with: ${email}`, colors.yellow);

  // Run tests in sequence

  // 1. Invalid login test
  await testInvalidLogin();

  // 2. Valid login test
  const loginResult = await testLogin(email, password);

  if (loginResult.success) {
    // 3. Protected routes
    await testProtectedRouteWithoutAuth();
    await testProtectedRoute();

    // 4. Session tests
    await testSessionPersistence();

    // 5. Token refresh
    await testRefreshToken();

    // 6. Logout
    await testLogout();

    // 7. Verify logout worked
    await testProtectedRoute(); // Should fail after logout
  }

  // 8. Security tests
  await testCORS();
  await testSecurityHeaders();
  await testRateLimit();

  // Summary
  log('\n' + '=' .repeat(50), colors.blue);
  log('📊 TEST SUMMARY', colors.blue);
  log('=' .repeat(50), colors.blue);

  log(`✅ Passed: ${testsPassed}`, colors.green);
  log(`❌ Failed: ${testsFailed}`, colors.red);

  if (errors.length > 0) {
    log('\n⚠️  ERRORS FOUND:', colors.yellow);
    errors.forEach(err => {
      log(`  - ${err.test}`, colors.red);
    });
  }

  const successRate = Math.round((testsPassed / (testsPassed + testsFailed)) * 100);
  log(`\n📈 Success Rate: ${successRate}%`, successRate >= 80 ? colors.green : colors.red);

  process.exit(testsFailed > 0 ? 1 : 0);
}

// Run tests
runTests().catch(console.error);