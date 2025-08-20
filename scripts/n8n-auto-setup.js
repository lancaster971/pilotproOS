#!/usr/bin/env node

/**
 * PilotProOS n8n Auto-Setup Script
 * Automatically configures n8n owner account to avoid client-visible setup screens
 */

import { readFileSync } from 'fs';
import { join } from 'path';
import chalk from 'chalk';
import ora from 'ora';

// Configuration
const N8N_URL = process.env.N8N_URL || 'http://localhost:5678';
const OWNER_EMAIL = process.env.N8N_OWNER_EMAIL || 'admin@pilotpros.local';
const OWNER_FIRST_NAME = process.env.N8N_OWNER_FIRST_NAME || 'PilotPro';
const OWNER_LAST_NAME = process.env.N8N_OWNER_LAST_NAME || 'Admin';
const OWNER_PASSWORD = process.env.N8N_OWNER_PASSWORD || 'pilotpros_admin_2025';

// Logging utilities
const log = {
    info: (msg) => console.log(chalk.blue('ℹ️'), msg),
    success: (msg) => console.log(chalk.green('✅'), msg),
    warning: (msg) => console.log(chalk.yellow('⚠️'), msg),
    error: (msg) => console.log(chalk.red('❌'), msg),
    title: (msg) => console.log(chalk.cyan.bold('🔧'), msg),
};

// Wait for n8n to be ready
async function waitForN8n(maxAttempts = 30) {
    const spinner = ora('Waiting for n8n to be ready...').start();
    
    for (let i = 0; i < maxAttempts; i++) {
        try {
            const response = await fetch(`${N8N_URL}/healthz`);
            if (response.ok) {
                spinner.succeed('n8n is ready');
                return true;
            }
        } catch (error) {
            // n8n not ready yet
        }
        
        spinner.text = `Waiting for n8n... (${i + 1}/${maxAttempts})`;
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    spinner.fail('n8n failed to start within timeout');
    return false;
}

// Check if n8n already has an owner
async function checkOwnerExists() {
    try {
        const response = await fetch(`${N8N_URL}/api/v1/owner`);
        if (response.status === 200) {
            const data = await response.json();
            return data.hasOwner || false;
        }
        return false;
    } catch (error) {
        return false;
    }
}

// Setup n8n owner account automatically
async function setupOwnerAccount() {
    const spinner = ora('Setting up n8n owner account...').start();
    
    try {
        const response = await fetch(`${N8N_URL}/api/v1/owner/setup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: OWNER_EMAIL,
                firstName: OWNER_FIRST_NAME,
                lastName: OWNER_LAST_NAME,
                password: OWNER_PASSWORD,
                skipInstanceOwnerSetup: false
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            spinner.succeed('n8n owner account created successfully');
            return data;
        } else {
            const error = await response.text();
            spinner.fail(`Failed to setup owner account: ${error}`);
            return null;
        }
    } catch (error) {
        spinner.fail(`Error setting up owner account: ${error.message}`);
        return null;
    }
}

// Login and get API key
async function loginAndGetApiKey() {
    const spinner = ora('Logging in and obtaining API access...').start();
    
    try {
        // Login to get cookie
        const loginResponse = await fetch(`${N8N_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: OWNER_EMAIL,
                password: OWNER_PASSWORD
            })
        });
        
        if (!loginResponse.ok) {
            const error = await loginResponse.text();
            spinner.fail(`Login failed: ${error}`);
            return null;
        }
        
        // Extract cookies
        const cookies = loginResponse.headers.get('set-cookie');
        
        spinner.succeed('Successfully authenticated with n8n');
        return cookies;
        
    } catch (error) {
        spinner.fail(`Authentication error: ${error.message}`);
        return null;
    }
}

// Import credentials from backup
async function importCredentials(cookies) {
    const credentialsPath = join(process.cwd(), 'BU_Hostinger', 'credentials.json');
    
    try {
        const credentialsData = JSON.parse(readFileSync(credentialsPath, 'utf8'));
        const spinner = ora(`Importing ${credentialsData.length} credentials...`).start();
        
        let imported = 0;
        let skipped = 0;
        
        for (const credential of credentialsData) {
            try {
                // Remove ID to let n8n assign new one
                const credData = { ...credential };
                delete credData.id;
                
                const response = await fetch(`${N8N_URL}/api/v1/credentials`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cookie': cookies
                    },
                    body: JSON.stringify(credData)
                });
                
                if (response.ok) {
                    imported++;
                } else {
                    const error = await response.text();
                    if (error.includes('already exists')) {
                        skipped++;
                    }
                }
            } catch (error) {
                // Skip individual credential errors
            }
        }
        
        spinner.succeed(`Credentials imported: ${imported} new, ${skipped} skipped`);
        return true;
        
    } catch (error) {
        log.error(`Failed to import credentials: ${error.message}`);
        return false;
    }
}

// Import workflows from backup  
async function importWorkflows(cookies) {
    const workflowsPath = join(process.cwd(), 'BU_Hostinger', 'workflows.json');
    
    try {
        const workflowsData = JSON.parse(readFileSync(workflowsPath, 'utf8'));
        const spinner = ora(`Importing ${workflowsData.length} workflows...`).start();
        
        let imported = 0;
        let activated = 0;
        
        for (const workflow of workflowsData) {
            try {
                // Remove ID to let n8n assign new one
                const workflowData = { ...workflow };
                delete workflowData.id;
                
                const response = await fetch(`${N8N_URL}/api/v1/workflows`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cookie': cookies
                    },
                    body: JSON.stringify(workflowData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    imported++;
                    
                    // Activate workflow if it was active in backup
                    if (workflow.active) {
                        try {
                            await fetch(`${N8N_URL}/api/v1/workflows/${result.id}/activate`, {
                                method: 'POST',
                                headers: {
                                    'Cookie': cookies
                                }
                            });
                            activated++;
                        } catch (activateError) {
                            // Skip activation errors
                        }
                    }
                }
            } catch (error) {
                // Skip individual workflow errors
            }
        }
        
        spinner.succeed(`Workflows imported: ${imported} created, ${activated} activated`);
        return true;
        
    } catch (error) {
        log.error(`Failed to import workflows: ${error.message}`);
        return false;
    }
}

// Main setup function
async function main() {
    console.log('\n' + chalk.cyan('=' .repeat(60)));
    log.title('PilotProOS n8n Auto-Setup (Sanitization)');
    console.log(chalk.cyan('=' .repeat(60)));
    
    log.info('Ensuring n8n is completely configured without client interaction...');
    console.log('');
    
    // Wait for n8n to be ready
    const isReady = await waitForN8n();
    if (!isReady) {
        log.error('n8n failed to start - cannot proceed with auto-setup');
        process.exit(1);
    }
    
    // Check if owner already exists
    const ownerExists = await checkOwnerExists();
    if (ownerExists) {
        log.success('n8n owner account already configured');
    } else {
        log.info('Setting up n8n owner account automatically...');
        const setupResult = await setupOwnerAccount();
        if (!setupResult) {
            log.error('Failed to setup owner account');
            process.exit(1);
        }
    }
    
    // Login and get authentication
    const cookies = await loginAndGetApiKey();
    if (!cookies) {
        log.error('Failed to authenticate with n8n');
        process.exit(1);
    }
    
    // Import backup data
    log.info('Importing backup data from BU_Hostinger...');
    await importCredentials(cookies);
    await importWorkflows(cookies);
    
    console.log('');
    log.success('n8n Auto-Setup Complete!');
    log.info('n8n is now fully configured and ready for business use');
    log.info(`Access: ${N8N_URL} (${OWNER_EMAIL} / [configured])`);
    console.log('');
    log.success('✅ Client will NEVER see n8n setup screens');
    log.success('✅ Complete automation and sanitization achieved');
    console.log('');
}

// Handle CLI arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
    console.log(chalk.cyan.bold('PilotProOS n8n Auto-Setup'));
    console.log('');
    console.log('Automatically configures n8n to prevent client-visible setup screens.');
    console.log('');
    console.log('Usage: npm run n8n:auto-setup');
    console.log('');
    console.log('Environment variables:');
    console.log('  N8N_URL              n8n server URL (default: http://localhost:5678)');
    console.log('  N8N_OWNER_EMAIL      Owner email (default: admin@pilotpros.local)');
    console.log('  N8N_OWNER_FIRST_NAME First name (default: PilotPro)');
    console.log('  N8N_OWNER_LAST_NAME  Last name (default: Admin)');
    console.log('  N8N_OWNER_PASSWORD   Password (default: pilotpros_admin_2025)');
    console.log('');
    console.log('This script:');
    console.log('  1. Waits for n8n to be ready');
    console.log('  2. Creates owner account automatically');
    console.log('  3. Imports BU_Hostinger backup data');
    console.log('  4. Ensures no client-visible setup screens');
    process.exit(0);
}

// Run auto-setup
main().catch(error => {
    log.error('Auto-setup failed:');
    console.error(error);
    process.exit(1);
});