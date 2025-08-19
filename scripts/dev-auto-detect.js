#!/usr/bin/env node

/**
 * PilotProOS Development Auto-Detection Script
 * Automatically detects the best development environment and starts it
 */

import { execSync, spawn } from 'child_process';
import { existsSync } from 'fs';
import { join } from 'path';
import chalk from 'chalk';
import ora from 'ora';

const ROOT_DIR = process.cwd();

// Logging utilities
const log = {
    info: (msg) => console.log(chalk.blue('ℹ️'), msg),
    success: (msg) => console.log(chalk.green('✅'), msg),
    warning: (msg) => console.log(chalk.yellow('⚠️'), msg),
    error: (msg) => console.log(chalk.red('❌'), msg),
    title: (msg) => console.log(chalk.cyan.bold('🚀'), msg),
};

// Check if Docker is available and running
function checkDockerAvailable() {
    try {
        execSync('docker --version', { stdio: 'ignore' });
        execSync('docker info', { stdio: 'ignore' });
        return true;
    } catch (error) {
        return false;
    }
}

// Check if docker-compose dev file exists
function checkDockerComposeExists() {
    return existsSync(join(ROOT_DIR, 'docker-compose.dev.yml'));
}

// Check if local PostgreSQL is running
function checkPostgreSQLRunning() {
    try {
        // Try to connect to PostgreSQL on default port
        execSync('pg_isready -h localhost -p 5432 -U pilotpros_user', { stdio: 'ignore' });
        return true;
    } catch (error) {
        // Try alternative PostgreSQL installations
        try {
            execSync('brew services list | grep postgresql', { stdio: 'ignore' });
            return true;
        } catch (brewError) {
            return false;
        }
    }
}

// Check if all dependencies are installed
function checkDependenciesInstalled() {
    const dirs = ['backend', 'frontend', 'ai-agent'];
    return dirs.every(dir => existsSync(join(ROOT_DIR, dir, 'node_modules')));
}

// Display environment detection results
function displayEnvironmentInfo(environment) {
    console.log('\n' + chalk.cyan('=' .repeat(60)));
    log.title('PilotProOS Development Environment Auto-Detection');
    console.log(chalk.cyan('=' .repeat(60)));
    
    log.info(`Docker available: ${checkDockerAvailable() ? chalk.green('Yes') : chalk.red('No')}`);
    log.info(`Docker Compose config: ${checkDockerComposeExists() ? chalk.green('Found') : chalk.red('Missing')}`);
    log.info(`Local PostgreSQL: ${checkPostgreSQLRunning() ? chalk.green('Running') : chalk.red('Not running')}`);
    log.info(`Dependencies installed: ${checkDependenciesInstalled() ? chalk.green('Yes') : chalk.red('No')}`);
    
    console.log('\n' + chalk.yellow('Selected Environment:'), chalk.bold(environment.name));
    console.log(chalk.gray(environment.description));
    console.log('');
}

// Install dependencies if missing
async function installDependencies() {
    if (!checkDependenciesInstalled()) {
        const spinner = ora('Installing dependencies...').start();
        try {
            execSync('npm run install:all', { stdio: 'inherit' });
            spinner.succeed('Dependencies installed successfully');
        } catch (error) {
            spinner.fail('Failed to install dependencies');
            process.exit(1);
        }
    }
}

// Start Docker development environment
function startDockerEnvironment() {
    log.info('Starting Docker development stack...');
    console.log(chalk.gray('This will start: PostgreSQL + n8n + Backend + Frontend + AI Agent'));
    console.log('');
    
    const child = spawn('npm', ['run', 'docker:dev'], {
        stdio: 'inherit',
        shell: true
    });
    
    child.on('close', (code) => {
        process.exit(code);
    });
}

// Start local development environment
function startLocalEnvironment() {
    log.info('Starting local development environment...');
    console.log(chalk.gray('This will start: Backend + Frontend + AI Agent + Local n8n'));
    console.log('');
    
    const child = spawn('npm', ['run', 'dev:local'], {
        stdio: 'inherit',
        shell: true
    });
    
    child.on('close', (code) => {
        process.exit(code);
    });
}

// Start SQLite fallback environment
function startSQLiteEnvironment() {
    log.warning('Using SQLite fallback mode (limited features)');
    console.log(chalk.gray('This will start: Backend + Frontend + AI Agent + n8n with SQLite'));
    console.log('');
    
    const child = spawn('npm', ['run', 'dev:sqlite'], {
        stdio: 'inherit',
        shell: true
    });
    
    child.on('close', (code) => {
        process.exit(code);
    });
}

// Main detection and startup logic
async function main() {
    const dockerAvailable = checkDockerAvailable();
    const dockerComposeExists = checkDockerComposeExists();
    const postgresRunning = checkPostgreSQLRunning();
    
    let environment;
    
    // Environment selection logic
    if (dockerAvailable && dockerComposeExists) {
        environment = {
            name: '🐳 Docker Development Stack',
            description: 'Full containerized environment with PostgreSQL (recommended for cross-OS)',
            starter: startDockerEnvironment
        };
    } else if (postgresRunning) {
        environment = {
            name: '🔧 Local PostgreSQL Development',
            description: 'Native development with local PostgreSQL installation',
            starter: startLocalEnvironment
        };
    } else {
        environment = {
            name: '📁 SQLite Portable Mode',
            description: 'Fallback mode with SQLite database (portable but limited features)',
            starter: startSQLiteEnvironment
        };
    }
    
    displayEnvironmentInfo(environment);
    
    // Install dependencies if needed
    await installDependencies();
    
    // Show startup information
    log.info('Development servers will be available at:');
    console.log(chalk.gray('  Frontend:  http://localhost:3000'));
    console.log(chalk.gray('  Backend:   http://localhost:3001'));
    console.log(chalk.gray('  AI Agent:  http://localhost:3002'));
    console.log(chalk.gray('  n8n:       http://localhost:5678 (admin / pilotpros_admin_2025)'));
    console.log('');
    
    log.info('Press Ctrl+C to stop all services');
    console.log('');
    
    // Start the selected environment
    environment.starter();
}

// Handle CLI arguments
if (process.argv.includes('--docker')) {
    displayEnvironmentInfo({
        name: '🐳 Docker Development Stack (Forced)',
        description: 'Forced Docker environment'
    });
    await installDependencies();
    startDockerEnvironment();
} else if (process.argv.includes('--local')) {
    displayEnvironmentInfo({
        name: '🔧 Local Development (Forced)',
        description: 'Forced local environment'
    });
    await installDependencies();
    startLocalEnvironment();
} else if (process.argv.includes('--sqlite')) {
    displayEnvironmentInfo({
        name: '📁 SQLite Mode (Forced)',
        description: 'Forced SQLite environment'
    });
    await installDependencies();
    startSQLiteEnvironment();
} else {
    // Auto-detection mode
    main().catch(error => {
        log.error('Failed to start development environment:');
        console.error(error);
        process.exit(1);
    });
}