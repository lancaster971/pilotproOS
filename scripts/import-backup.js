#!/usr/bin/env node

/**
 * PilotProOS Backup Import Script
 * Imports workflows and credentials from BU_Hostinger backup files
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { config } from 'dotenv';
import chalk from 'chalk';
import ora from 'ora';

// Load environment variables from .env
config();

const ROOT_DIR = process.cwd();
const BACKUP_DIR = join(ROOT_DIR, 'BU_Hostinger');
const WORKFLOWS_FILE = join(BACKUP_DIR, 'workflows.json');
const CREDENTIALS_FILE = join(BACKUP_DIR, 'credentials.json');

// n8n API configuration from .env
const N8N_URL = process.env.N8N_URL || 'http://localhost:5678';
const N8N_API_KEY = process.env.N8N_API_KEY;
const N8N_USER = process.env.N8N_ADMIN_USER || 'admin';
const N8N_PASSWORD = process.env.N8N_ADMIN_PASSWORD || 'pilotpros_admin_2025';

// Logging utilities
const log = {
    info: (msg) => console.log(chalk.blue('ℹ️'), msg),
    success: (msg) => console.log(chalk.green('✅'), msg),
    warning: (msg) => console.log(chalk.yellow('⚠️'), msg),
    error: (msg) => console.log(chalk.red('❌'), msg),
    title: (msg) => console.log(chalk.cyan.bold('🚀'), msg),
};

// Check if n8n is running and accessible
async function checkN8nConnection() {
    try {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Use API key if available, otherwise fall back to basic auth
        if (N8N_API_KEY) {
            headers['X-N8N-API-KEY'] = N8N_API_KEY;
        } else {
            headers['Authorization'] = `Basic ${Buffer.from(`${N8N_USER}:${N8N_PASSWORD}`).toString('base64')}`;
        }
        
        const response = await fetch(`${N8N_URL}/api/v1/workflows`, {
            method: 'GET',
            headers
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return true;
    } catch (error) {
        log.error(`Cannot connect to n8n at ${N8N_URL}`);
        log.error(`Error: ${error.message}`);
        return false;
    }
}

// Check if backup files exist
function checkBackupFiles() {
    const checks = {
        workflows: existsSync(WORKFLOWS_FILE),
        credentials: existsSync(CREDENTIALS_FILE)
    };
    
    log.info('Checking backup files:');
    console.log(`  Workflows: ${checks.workflows ? chalk.green('Found') : chalk.red('Missing')} (${WORKFLOWS_FILE})`);
    console.log(`  Credentials: ${checks.credentials ? chalk.green('Found') : chalk.red('Missing')} (${CREDENTIALS_FILE})`);
    
    return checks;
}

// Parse JSON file safely
function parseJsonFile(filePath, name) {
    try {
        const content = readFileSync(filePath, 'utf8');
        const data = JSON.parse(content);
        log.success(`${name} file parsed successfully (${Array.isArray(data) ? data.length : 'object'} items)`);
        return data;
    } catch (error) {
        log.error(`Failed to parse ${name} file: ${error.message}`);
        return null;
    }
}

// Import credentials to n8n
async function importCredentials(credentials) {
    if (!Array.isArray(credentials)) {
        log.error('Credentials data is not an array');
        return false;
    }
    
    const spinner = ora(`Importing ${credentials.length} credentials...`).start();
    let imported = 0;
    let skipped = 0;
    let errors = 0;
    
    // Prepare headers with API key
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (N8N_API_KEY) {
        headers['X-N8N-API-KEY'] = N8N_API_KEY;
    } else {
        headers['Authorization'] = `Basic ${Buffer.from(`${N8N_USER}:${N8N_PASSWORD}`).toString('base64')}`;
    }
    
    for (const credential of credentials) {
        try {
            // Clean credential data - remove read-only fields
            const credentialData = { ...credential };
            delete credentialData.id;
            delete credentialData.createdAt;
            delete credentialData.updatedAt;
            
            const response = await fetch(`${N8N_URL}/api/v1/credentials`, {
                method: 'POST',
                headers,
                body: JSON.stringify(credentialData)
            });
            
            if (response.ok) {
                imported++;
                spinner.text = `Importing credentials... ${imported}/${credentials.length}`;
            } else {
                const errorText = await response.text();
                if (errorText.includes('already exists')) {
                    skipped++;
                } else {
                    console.error(`\nFailed to import credential "${credential.name}": ${errorText}`);
                    errors++;
                }
            }
        } catch (error) {
            console.error(`\nError importing credential "${credential.name}": ${error.message}`);
            errors++;
        }
    }
    
    spinner.succeed(`Credentials import complete: ${imported} imported, ${skipped} skipped, ${errors} errors`);
    return errors === 0;
}

// Import workflows to n8n
async function importWorkflows(workflows) {
    if (!Array.isArray(workflows)) {
        log.error('Workflows data is not an array');
        return false;
    }
    
    const spinner = ora(`Importing ${workflows.length} workflows...`).start();
    let imported = 0;
    let skipped = 0;
    let errors = 0;
    
    // Prepare headers with API key
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (N8N_API_KEY) {
        headers['X-N8N-API-KEY'] = N8N_API_KEY;
    } else {
        headers['Authorization'] = `Basic ${Buffer.from(`${N8N_USER}:${N8N_PASSWORD}`).toString('base64')}`;
    }
    
    for (const workflow of workflows) {
        try {
            // Map to exact n8n 1.106.3 schema (only required fields)
            const workflowData = {
                name: workflow.name,
                nodes: workflow.nodes || [],
                connections: workflow.connections || {},
                settings: workflow.settings || {}
            };
            
            // Add optional fields only if they exist and are not null/empty
            if (workflow.staticData && Object.keys(workflow.staticData).length > 0) {
                workflowData.staticData = workflow.staticData;
            }
            if (workflow.pinData && Object.keys(workflow.pinData).length > 0) {
                workflowData.pinData = workflow.pinData;
            }
            if (workflow.meta && Object.keys(workflow.meta).length > 0) {
                workflowData.meta = workflow.meta;
            }
            
            const response = await fetch(`${N8N_URL}/api/v1/workflows`, {
                method: 'POST',
                headers,
                body: JSON.stringify(workflowData)
            });
            
            if (response.ok) {
                const result = await response.json();
                imported++;
                spinner.text = `Importing workflows... ${imported}/${workflows.length}`;
                
                // Activate the workflow if it was active in the backup
                if (workflow.active) {
                    try {
                        await fetch(`${N8N_URL}/api/v1/workflows/${result.id}/activate`, {
                            method: 'POST',
                            headers
                        });
                    } catch (activateError) {
                        console.error(`\nFailed to activate workflow "${workflow.name}": ${activateError.message}`);
                    }
                }
            } else {
                const errorText = await response.text();
                if (errorText.includes('already exists')) {
                    skipped++;
                } else {
                    console.error(`\nFailed to import workflow "${workflow.name}": ${errorText}`);
                    errors++;
                }
            }
        } catch (error) {
            console.error(`\nError importing workflow "${workflow.name}": ${error.message}`);
            errors++;
        }
    }
    
    spinner.succeed(`Workflows import complete: ${imported} imported, ${skipped} skipped, ${errors} errors`);
    return errors === 0;
}

// Main import function
async function main() {
    console.log('\n' + chalk.cyan('=' .repeat(60)));
    log.title('PilotProOS Backup Import from BU_Hostinger');
    console.log(chalk.cyan('=' .repeat(60)));
    
    // Check backup files
    const backupChecks = checkBackupFiles();
    if (!backupChecks.workflows && !backupChecks.credentials) {
        log.error('No backup files found in BU_Hostinger directory');
        process.exit(1);
    }
    
    // Check n8n connection
    log.info('Testing n8n connection...');
    const n8nConnected = await checkN8nConnection();
    if (!n8nConnected) {
        log.error('Cannot connect to n8n. Make sure n8n is running and accessible.');
        log.info('Try: npm run dev:docker or npm run dev:local');
        process.exit(1);
    }
    log.success('n8n connection successful');
    
    // Import credentials first (workflows may depend on them)
    if (backupChecks.credentials) {
        log.info('Loading credentials backup...');
        const credentials = parseJsonFile(CREDENTIALS_FILE, 'Credentials');
        if (credentials) {
            await importCredentials(credentials);
        }
    }
    
    // Import workflows
    if (backupChecks.workflows) {
        log.info('Loading workflows backup...');
        const workflows = parseJsonFile(WORKFLOWS_FILE, 'Workflows');
        if (workflows) {
            await importWorkflows(workflows);
        }
    }
    
    console.log('');
    log.success('Backup import process completed!');
    log.info('You can now access n8n at: ' + chalk.underline(N8N_URL));
    log.info(`Login credentials: ${N8N_USER} / ${N8N_PASSWORD}`);
    console.log('');
}

// Handle CLI arguments
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
    console.log(chalk.cyan.bold('PilotProOS Backup Import'));
    console.log('');
    console.log('Usage: npm run import:backup [options]');
    console.log('');
    console.log('Options:');
    console.log('  --help, -h     Show this help message');
    console.log('');
    console.log('Environment variables:');
    console.log('  N8N_URL        n8n server URL (default: http://localhost:5678)');
    console.log('  N8N_ADMIN_USER n8n username (default: admin)');
    console.log('  N8N_ADMIN_PASSWORD n8n password (default: pilotpros_admin_2025)');
    console.log('');
    console.log('Backup files expected:');
    console.log('  BU_Hostinger/workflows.json    - Workflow definitions');
    console.log('  BU_Hostinger/credentials.json  - Credential configurations');
    process.exit(0);
}

// Run the import
main().catch(error => {
    log.error('Import failed:');
    console.error(error);
    process.exit(1);
});