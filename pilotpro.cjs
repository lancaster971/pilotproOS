#!/usr/bin/env node

/**
 * PilotProOS CLI - Secure Interactive Menu
 * Simply run: ./pilotpro
 */

const path = require('path');
const auth = require('./auth.cjs');

// Main function
async function main() {
  try {
    // Authenticate user first
    const authenticated = await auth.authenticate();

    if (!authenticated) {
      console.error('❌ Authentication failed');
      process.exit(1);
    }

    // Launch the interactive menu after successful authentication
    const SCRIPT_DIR = __dirname;
    const menuScript = path.join(SCRIPT_DIR, 'stack-manager.cjs');
    require(menuScript);

  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

// Run
main();