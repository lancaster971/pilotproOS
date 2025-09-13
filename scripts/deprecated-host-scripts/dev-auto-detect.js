#!/usr/bin/env node

/**
 * PilotProOS Docker-First Development Auto-Setup
 * Ensures Docker is installed and starts the complete development stack
 */

import { execSync, spawn } from 'child_process';
import { existsSync } from 'fs';
import { join } from 'path';
import { platform } from 'os';
import chalk from 'chalk';
import ora from 'ora';

const ROOT_DIR = process.cwd();
const OS = platform();

// Logging utilities
const log = {
    info: (msg) => console.log(chalk.blue('ℹ️'), msg),
    success: (msg) => console.log(chalk.green('✅'), msg),
    warning: (msg) => console.log(chalk.yellow('⚠️'), msg),
    error: (msg) => console.log(chalk.red('❌'), msg),
    title: (msg) => console.log(chalk.cyan.bold('🚀'), msg),
};

// Check if Docker is installed
function isDockerInstalled() {
    try {
        execSync('docker --version', { stdio: 'ignore' });
        return true;
    } catch (error) {
        return false;
    }
}

// Check if Docker is running
function isDockerRunning() {
    try {
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

// Check if all dependencies are installed
function checkDependenciesInstalled() {
    const dirs = ['backend', 'frontend', 'ai-agent'];
    return dirs.every(dir => existsSync(join(ROOT_DIR, dir, 'node_modules')));
}

// Install Docker based on OS
async function installDocker() {
    const spinner = ora('Installing Docker...').start();
    
    try {
        switch (OS) {
            case 'darwin': // macOS
                spinner.text = 'Installing Docker Desktop for macOS...';
                log.info('Installing Docker Desktop for macOS via Homebrew...');
                execSync('brew install --cask docker', { stdio: 'inherit' });
                break;
                
            case 'win32': // Windows
                spinner.text = 'Installing Docker Desktop for Windows...';
                log.error('Please install Docker Desktop manually from: https://docs.docker.com/desktop/install/windows-install/');
                spinner.fail('Manual installation required for Windows');
                process.exit(1);
                
            case 'linux': // Linux
                spinner.text = 'Installing Docker for Linux...';
                log.info('Installing Docker via official script...');
                execSync('curl -fsSL https://get.docker.com | sh', { stdio: 'inherit' });
                execSync('sudo usermod -aG docker $USER', { stdio: 'inherit' });
                log.warning('Please logout and login again for Docker permissions to take effect');
                break;
                
            default:
                spinner.fail(`Unsupported operating system: ${OS}`);
                process.exit(1);
        }
        
        spinner.succeed('Docker installation completed');
        
        // Start Docker if on macOS
        if (OS === 'darwin') {
            const startSpinner = ora('Starting Docker Desktop...').start();
            try {
                execSync('open -a Docker', { stdio: 'ignore' });
                startSpinner.text = 'Waiting for Docker to start...';
                
                // Wait for Docker to be ready (max 2 minutes)
                let attempts = 24;
                while (attempts > 0 && !isDockerRunning()) {
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    attempts--;
                }
                
                if (isDockerRunning()) {
                    startSpinner.succeed('Docker Desktop started successfully');
                } else {
                    startSpinner.fail('Docker Desktop failed to start - please start it manually');
                    process.exit(1);
                }
            } catch (error) {
                startSpinner.fail('Failed to start Docker Desktop');
                log.error('Please start Docker Desktop manually');
                process.exit(1);
            }
        }
        
    } catch (error) {
        spinner.fail('Docker installation failed');
        log.error('Please install Docker manually:');
        log.info('macOS: https://docs.docker.com/desktop/install/mac-install/');
        log.info('Windows: https://docs.docker.com/desktop/install/windows-install/');
        log.info('Linux: https://docs.docker.com/engine/install/');
        process.exit(1);
    }
}

// Ensure Docker is ready
async function ensureDockerReady() {
    log.title('PilotProOS Docker-First Development Setup');
    console.log(chalk.cyan('=' .repeat(60)));
    
    // Check if Docker is installed
    if (!isDockerInstalled()) {
        log.warning('Docker not found - installing automatically...');
        await installDocker();
    } else {
        log.success('Docker is installed');
    }
    
    // Check if Docker is running
    if (!isDockerRunning()) {
        log.warning('Docker is not running - starting...');
        
        const spinner = ora('Starting Docker...').start();
        try {
            if (OS === 'darwin') {
                execSync('open -a Docker', { stdio: 'ignore' });
            } else if (OS === 'linux') {
                execSync('sudo systemctl start docker', { stdio: 'ignore' });
            }
            
            // Wait for Docker to be ready
            let attempts = 24;
            while (attempts > 0 && !isDockerRunning()) {
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts--;
            }
            
            if (isDockerRunning()) {
                spinner.succeed('Docker started successfully');
            } else {
                spinner.fail('Failed to start Docker');
                log.error('Please start Docker manually and try again');
                process.exit(1);
            }
        } catch (error) {
            spinner.fail('Failed to start Docker');
            log.error('Please start Docker manually and try again');
            process.exit(1);
        }
    } else {
        log.success('Docker is running');
    }
    
    // Check docker-compose file
    if (!checkDockerComposeExists()) {
        log.error('docker-compose.dev.yml not found!');
        process.exit(1);
    }
    log.success('Docker Compose configuration found');
}

// Install dependencies if missing
async function installDependencies() {
    if (!checkDependenciesInstalled()) {
        const spinner = ora('Installing Node.js dependencies...').start();
        try {
            execSync('npm run install:all', { stdio: 'inherit' });
            spinner.succeed('Dependencies installed successfully');
        } catch (error) {
            spinner.fail('Failed to install dependencies');
            process.exit(1);
        }
    } else {
        log.success('Dependencies are installed');
    }
}

// Start Docker development environment
function startDockerEnvironment() {
    console.log('');
    log.info('Starting PilotProOS Docker Development Stack...');
    console.log(chalk.gray('🐳 PostgreSQL + n8n + Backend + Frontend + AI Agent'));
    console.log('');
    
    log.info('Development servers will be available at:');
    console.log(chalk.gray('  Frontend:  http://localhost:3000'));
    console.log(chalk.gray('  Backend:   http://localhost:3001'));
    console.log(chalk.gray('  AI Agent:  http://localhost:3002'));
    console.log(chalk.gray('  n8n:       http://localhost:5678 (admin / pilotpros_admin_2025)'));
    console.log(chalk.gray('  Database:  localhost:5432 (PostgreSQL)'));
    console.log(chalk.gray('  PgAdmin:   http://localhost:5050 (optional)'));
    console.log('');
    
    log.info('Press Ctrl+C to stop all services');
    console.log('');
    log.success('Starting containers...');
    console.log('');
    
    const child = spawn('docker-compose', ['-f', 'docker-compose.dev.yml', 'up', '--build'], {
        stdio: 'inherit',
        shell: true
    });
    
    child.on('close', (code) => {
        console.log('');
        if (code === 0) {
            log.success('Development environment stopped cleanly');
        } else {
            log.error(`Development environment exited with code ${code}`);
        }
        process.exit(code);
    });
    
    // Handle Ctrl+C gracefully
    process.on('SIGINT', () => {
        console.log('');
        log.info('Stopping development environment...');
        child.kill('SIGTERM');
    });
}

// Main setup and startup logic
async function main() {
    try {
        // Ensure Docker is ready
        await ensureDockerReady();
        
        // Install dependencies
        await installDependencies();
        
        // Start Docker environment
        startDockerEnvironment();
        
    } catch (error) {
        log.error('Setup failed:');
        console.error(error);
        process.exit(1);
    }
}

// Handle CLI arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
    console.log(chalk.cyan.bold('PilotProOS Docker-First Development'));
    console.log('');
    console.log('This script ensures Docker is installed and starts the complete development stack.');
    console.log('');
    console.log('Usage: npm run dev [options]');
    console.log('');
    console.log('Options:');
    console.log('  --help, -h     Show this help message');
    console.log('');
    console.log('What this script does:');
    console.log('  1. Checks if Docker is installed (installs if missing)');
    console.log('  2. Ensures Docker is running');
    console.log('  3. Installs Node.js dependencies');
    console.log('  4. Starts the complete Docker development stack');
    console.log('');
    console.log('Services started:');
    console.log('  - PostgreSQL database (port 5432)');
    console.log('  - n8n workflow engine (port 5678)');
    console.log('  - Backend API (port 3001)');
    console.log('  - Frontend (port 3000)');
    console.log('  - AI Agent (port 3002)');
    process.exit(0);
}

// Run the setup
main();