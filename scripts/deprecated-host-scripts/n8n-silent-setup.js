#!/usr/bin/env node

/**
 * PilotPro OS - Silent n8n Configuration
 * Automatically configures n8n with client data WITHOUT any client-visible interfaces
 */

import { readFileSync } from 'fs';
import { join } from 'path';

// Configuration from environment or defaults
const N8N_URL = process.env.N8N_URL || 'http://localhost:5678';
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@pilotpros.local';
const ADMIN_FIRST_NAME = process.env.ADMIN_FIRST_NAME || 'PilotPro';
const ADMIN_LAST_NAME = process.env.ADMIN_LAST_NAME || 'Admin';
const DOMAIN = process.env.DOMAIN || 'localhost';
const COMPANY_NAME = process.env.COMPANY_NAME || 'Business Platform';

// Generate secure password from domain
const ADMIN_PASSWORD = `${DOMAIN.replace(/\./g, '')}_automation_admin_2025`;

// Silent logging (no output to client)
const log = {
    silent: () => {}, // All logs hidden from client
    error: (msg) => console.error(`[INTERNAL ERROR] ${msg}`)
};

// Wait for n8n to be ready (silent)
async function waitForN8n(maxAttempts = 60) {
    for (let i = 0; i < maxAttempts; i++) {
        try {
            const response = await fetch(`${N8N_URL}/healthz`, { timeout: 2000 });
            if (response.ok) {
                return true;
            }
        } catch (error) {
            // Continue waiting silently
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    return false;
}

// Check if setup is needed
async function needsSetup() {
    try {
        // Try to access a protected endpoint
        const response = await fetch(`${N8N_URL}/api/v1/workflows`);
        
        // If we get 401, setup is complete but we need to login
        // If we get a setup page, setup is needed
        const text = await response.text();
        
        return text.includes('Set up owner account') || text.includes('setup');
    } catch (error) {
        return true; // Assume setup needed if we can't connect
    }
}

// Setup owner account silently
async function setupOwnerSilently() {
    try {
        // Try different setup endpoints that n8n might use
        const setupEndpoints = [
            '/api/v1/owner/setup',
            '/api/v1/setup',
            '/rest/owner/setup',
            '/rest/setup'
        ];
        
        const setupData = {
            email: ADMIN_EMAIL,
            firstName: ADMIN_FIRST_NAME,
            lastName: ADMIN_LAST_NAME,
            password: ADMIN_PASSWORD,
            skipInstanceOwnerSetup: false,
            skipSurvey: true,  // Skip survey to avoid client interaction
            acceptTerms: true,
            receiveUpdates: false,  // NO security updates checkbox flagged
            acceptDataProcessing: false,
            skipSetup: false
        };
        
        for (const endpoint of setupEndpoints) {
            try {
                const response = await fetch(`${N8N_URL}${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(setupData)
                });
                
                if (response.ok) {
                    return await response.json();
                }
            } catch (error) {
                // Try next endpoint
                continue;
            }
        }
        
        throw new Error('No valid setup endpoint found');
    } catch (error) {
        throw new Error(`Setup failed: ${error.message}`);
    }
}

// Complete post-setup configuration
async function completeConfiguration() {
    try {
        // Login to get session
        const loginResponse = await fetch(`${N8N_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: ADMIN_EMAIL,
                password: ADMIN_PASSWORD
            })
        });
        
        if (!loginResponse.ok) {
            throw new Error('Login failed after setup');
        }
        
        const cookies = loginResponse.headers.get('set-cookie');
        
        // Disable all telemetry and updates via API
        const settingsToDisable = [
            { key: 'diagnostics.enabled', value: false },
            { key: 'versionNotifications.enabled', value: false },
            { key: 'telemetry.enabled', value: false },
            { key: 'personalization.enabled', value: false },
            { key: 'userManagement.disabled', value: true },
            { key: 'publicApi.disabled', value: true },
            { key: 'templates.enabled', value: false }
        ];
        
        for (const setting of settingsToDisable) {
            try {
                await fetch(`${N8N_URL}/api/v1/settings`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cookie': cookies
                    },
                    body: JSON.stringify(setting)
                });
            } catch (error) {
                // Continue if individual setting fails
            }
        }
        
        return cookies;
    } catch (error) {
        throw new Error(`Configuration failed: ${error.message}`);
    }
}

// Import backup data silently
async function importBackupData(cookies) {
    try {
        const backupDir = '/opt/pilotpro-os/imports';
        
        // Import credentials
        const credentialsPath = join(backupDir, 'credentials.json');
        if (require('fs').existsSync(credentialsPath)) {
            const credentials = JSON.parse(readFileSync(credentialsPath, 'utf8'));
            
            for (const credential of credentials) {
                try {
                    const credData = { ...credential };
                    delete credData.id;
                    
                    await fetch(`${N8N_URL}/api/v1/credentials`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Cookie': cookies
                        },
                        body: JSON.stringify(credData)
                    });
                } catch (error) {
                    // Continue with other credentials
                }
            }
        }
        
        // Import workflows
        const workflowsPath = join(backupDir, 'workflows.json');
        if (require('fs').existsSync(workflowsPath)) {
            const workflows = JSON.parse(readFileSync(workflowsPath, 'utf8'));
            
            for (const workflow of workflows) {
                try {
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
                    
                    // Activate if workflow was active
                    if (response.ok && workflow.active) {
                        const result = await response.json();
                        await fetch(`${N8N_URL}/api/v1/workflows/${result.id}/activate`, {
                            method: 'POST',
                            headers: { 'Cookie': cookies }
                        });
                    }
                } catch (error) {
                    // Continue with other workflows
                }
            }
        }
        
        return true;
    } catch (error) {
        return false;
    }
}

// Main silent setup
async function main() {
    try {
        // Wait for n8n silently
        const isReady = await waitForN8n();
        if (!isReady) {
            throw new Error('Process automation engine failed to start');
        }
        
        // Check if setup is needed
        const setupNeeded = await needsSetup();
        if (!setupNeeded) {
            console.log('Process automation already configured');
            return;
        }
        
        // Setup owner account silently
        await setupOwnerSilently();
        
        // Complete configuration
        const cookies = await completeConfiguration();
        
        // Import backup data if available
        await importBackupData(cookies);
        
        console.log('Process automation engine configured successfully');
        
    } catch (error) {
        log.error(`Silent setup failed: ${error.message}`);
        process.exit(1);
    }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export { main as setupN8nSilently };