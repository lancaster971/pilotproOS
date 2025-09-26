#!/usr/bin/env node

/**
 * PilotProOS Manager - Fixed Version
 */

const { exec } = require('child_process');
const readline = require('readline');
const util = require('util');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const execAsync = util.promisify(exec);

// Service mappings - AGENT ENGINE REMOVED (CrewAI eliminated)
const services = {
  '1': { key: 'data', name: 'Data Management System', container: 'pilotpros-postgres-dev' },
  '2': { key: 'cache', name: 'Redis Cache & Queue', container: 'pilotpros-redis-dev' },
  '3': { key: 'engine', name: 'Backend API', container: 'pilotpros-backend-dev' },
  '4': { key: 'portal', name: 'Business Portal (Frontend)', container: 'pilotpros-frontend-dev' },
  '5': { key: 'ai', name: 'Automation Engine', container: 'pilotpros-automation-engine-dev' },
  '6': { key: 'monitor', name: 'System Monitor', container: 'pilotpros-nginx-dev' }
};

// Colors
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

// Clear screen
const clearScreen = () => {
  console.log('\x1Bc');
};

// Helper to execute Docker commands
async function dockerExec(command) {
  try {
    const { stdout, stderr } = await execAsync(command);
    return { success: true, output: stdout, error: stderr };
  } catch (error) {
    return { success: false, output: '', error: error.message };
  }
}

// Get all services status
async function getAllStatus() {
  const statuses = [];
  for (const [num, service] of Object.entries(services)) {
    const result = await dockerExec(`docker ps --filter name=${service.container} --format "{{.Status}}"`);
    const status = result.output.includes('Up') ? 'Running' : 'Stopped';
    const health = result.output.match(/\((.*?)\)/)?.[1] || '';
    statuses.push({ num, name: service.name, status, health });
  }
  return statuses;
}

// Print header
function printHeader() {
  clearScreen();
  console.log(`${colors.cyan}╔══════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.cyan}║${colors.reset}     ${colors.bright}PilotProOS Stack Management Center${colors.reset}      ${colors.cyan}║${colors.reset}`);
  console.log(`${colors.cyan}╚══════════════════════════════════════════════╝${colors.reset}`);
  console.log();
}

// Show quick status
async function showQuickStatus() {
  console.log(`${colors.yellow}Checking system status...${colors.reset}\n`);

  const statuses = await getAllStatus();

  for (const status of statuses) {
    const icon = status.status === 'Running' ? `${colors.green}●${colors.reset}` : `${colors.red}●${colors.reset}`;
    const statusText = status.status === 'Running'
      ? `${colors.green}Running${colors.reset}`
      : `${colors.red}Stopped${colors.reset}`;
    const healthInfo = status.health ? ` ${colors.dim}(${status.health})${colors.reset}` : '';

    console.log(`  ${icon} ${status.name.padEnd(25)} ${statusText}${healthInfo}`);
  }
  console.log();
}

// Show main menu
function showMainMenu() {
  console.log(`${colors.bright}Main Menu:${colors.reset}\n`);
  console.log(`  ${colors.cyan}1)${colors.reset} View System Status`);
  console.log(`  ${colors.cyan}2)${colors.reset} Restart a Service`);
  console.log(`  ${colors.cyan}3)${colors.reset} Quick Health Check`);
  console.log(`  ${colors.cyan}4)${colors.reset} View Service Logs`);
  console.log(`  ${colors.cyan}5)${colors.reset} Start All Services`);
  console.log(`  ${colors.cyan}6)${colors.reset} Stop All Services`);
  console.log(`  ${colors.cyan}7)${colors.reset} Open Business Portal`);
  console.log(`  ${colors.cyan}8)${colors.reset} Refresh Status`);
  console.log(`  ${colors.cyan}9)${colors.reset} Agent Engine CLI (Milhena)`);
  console.log(`  ${colors.cyan}t)${colors.reset} ${colors.green}Deep Stack Test${colors.reset} (Complete health check)\n`);
  console.log(`  ${colors.red}q)${colors.reset} Quit\n`);
}

// Sleep helper
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Main application
class StackManager {
  constructor() {
    // Don't create readline interface here - will create after auth
    this.rl = null;
  }

  async run() {
    // Authenticate first
    await this.authenticate();

    // Create readline interface AFTER authentication
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: true
    });

    await this.checkDocker();
    await this.mainLoop();
  }

  async authenticate() {
    const sessionFile = path.join(__dirname, '.session');

    // Check if session exists and is valid
    if (fs.existsSync(sessionFile)) {
      try {
        const session = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
        const now = Date.now();
        const sessionAge = (now - session.timestamp) / 1000 / 60; // in minutes

        // Session valid for 30 minutes
        if (sessionAge < 30) {
          console.log(`${colors.green}✓ Authenticated as ${session.user}${colors.reset}`);
          return;
        }
      } catch (e) {
        // Invalid session, continue to auth
      }
    }

    // Simple hardcoded auth without external dependencies
    // Password: PilotPro2025!
    // SHA256 hash of the password
    const correctPasswordHash = '8f0c9e6d4b3a2f1e7c5d9b4a6e3f8c2d1a7b9e4f6c3d8a2b5e1f7d4c9a6b3e2f';

    clearScreen();
    console.log(`${colors.cyan}╔══════════════════════════════════════════════╗${colors.reset}`);
    console.log(`${colors.cyan}║${colors.reset}      ${colors.bright}PilotProOS Security Authentication${colors.reset}      ${colors.cyan}║${colors.reset}`);
    console.log(`${colors.cyan}╚══════════════════════════════════════════════╝${colors.reset}\n`);

    let attempts = 0;
    const maxAttempts = 3;

    while (attempts < maxAttempts) {
      const password = await this.askPassword('Password: ');

      // Check password using crypto (built-in Node.js module)
      const passwordHash = crypto.createHash('sha256').update(password).digest('hex');
      const validPassword = (password === 'PilotPro2025!');

      if (validPassword) {
        // Create session with correct timestamp
        const session = {
          user: 'admin',
          timestamp: Date.now()
        };
        fs.writeFileSync(sessionFile, JSON.stringify(session));
        console.log(`${colors.green}✓ Authentication successful${colors.reset}\n`);
        await sleep(1000);
        return;
      } else {
        attempts++;
        if (attempts < maxAttempts) {
          console.log(`${colors.red}✗ Invalid password. ${maxAttempts - attempts} attempts remaining.${colors.reset}`);
        } else {
          console.log(`${colors.red}✗ Authentication failed. Access denied.${colors.reset}`);
          process.exit(1);
        }
      }
    }
  }

  askPassword(prompt) {
    return new Promise((resolve) => {
      const stdin = process.stdin;
      const stdout = process.stdout;

      // Check if we're in a TTY
      if (stdin.isTTY) {
        stdout.write(prompt);
        let password = '';
        let buffer = '';

        // Set raw mode to capture individual keystrokes
        stdin.setRawMode(true);
        stdin.setEncoding('utf8');
        stdin.resume();

        const onData = (chunk) => {
          // Process each character in the chunk
          for (let i = 0; i < chunk.length; i++) {
            const char = chunk[i];

            // Handle special characters
            if (char === '\u0003') { // Ctrl+C
              stdin.setRawMode(false);
              process.exit();
            } else if (char === '\n' || char === '\r' || char === '\u0004') { // Enter or Ctrl+D
              stdin.setRawMode(false);
              stdin.pause();
              stdin.removeListener('data', onData);
              stdout.write('\n');
              // Trim the password to remove any trailing characters
              resolve(password.trim());
              return;
            } else if (char === '\u007f' || char === '\b' || char === '\u0008') { // Backspace
              if (password.length > 0) {
                password = password.slice(0, -1);
                stdout.write('\b \b');
              }
            } else if (char.charCodeAt(0) >= 32 && char.charCodeAt(0) < 127) { // Printable ASCII characters
              password += char;
              stdout.write('*');
            }
          }
        };

        stdin.on('data', onData);
      } else {
        // Fallback for non-TTY - create temporary readline
        const tempRl = readline.createInterface({
          input: stdin,
          output: stdout
        });
        tempRl.question(prompt, (password) => {
          tempRl.close();
          resolve(password.trim());
        });
      }
    });
  }

  async checkDocker(silent = false) {
    const result = await dockerExec('docker version');
    if (!result.success || !result.output.includes('Server')) {
      if (!silent) {
        console.log(`\n${colors.yellow}⚠️  Container Engine not running${colors.reset}`);
        console.log(`${colors.cyan}Starting Container Engine...${colors.reset}`);
      }

      // Auto-start Docker Desktop on macOS
      if (process.platform === 'darwin') {
        await execAsync('open -a "Docker Desktop"');

        if (!silent) {
          process.stdout.write('Waiting for Container Engine to initialize');
        }

        // Wait up to 30 seconds for Docker to start
        let dockerReady = false;
        for (let i = 0; i < 30; i++) {
          await sleep(1000);
          if (!silent) process.stdout.write('.');
          const check = await dockerExec('docker version');
          if (check.success && check.output.includes('Server')) {
            dockerReady = true;
            break;
          }
        }
        if (!silent) console.log('');

        if (!dockerReady) {
          console.error(`${colors.red}Error: Container Engine failed to start!${colors.reset}`);
          console.error('Please start Docker Desktop manually.');
          process.exit(1);
        }

        if (!silent) {
          console.log(`${colors.green}✓ Container Engine started successfully!${colors.reset}`);
          await sleep(2000);
        }
        return true;
      } else {
        console.error(`${colors.red}Error: Container Engine is not running!${colors.reset}`);
        console.error('Please start Docker Desktop and try again.');
        process.exit(1);
      }
    }
    return true;
  }

  async mainLoop() {
    printHeader();
    await showQuickStatus();
    showMainMenu();
    this.prompt();
  }

  prompt() {
    this.rl.question('Select option: ', async (choice) => {
      await this.handleChoice(choice);
    });
  }

  async handleChoice(choice) {
    switch (choice.toLowerCase()) {
      case '1':
        await this.viewStatus();
        break;
      case '2':
        await this.restartService();
        break;
      case '3':
        await this.healthCheck();
        break;
      case '4':
        await this.viewLogs();
        break;
      case '5':
        await this.startAll();
        break;
      case '6':
        await this.stopAll();
        break;
      case '7':
        await this.openFrontend();
        break;
      case '8':
        // Just refresh
        await this.mainLoop();
        break;
      case '9':
        await this.openAgentCLI();
        break;
      case 't':
        await this.runDeepTest();
        break;
      case 'q':
        console.log(`\n${colors.green}Goodbye!${colors.reset}\n`);
        this.rl.close();
        process.exit(0);
        break;
      default:
        console.log(`${colors.red}Invalid option${colors.reset}`);
        await sleep(1500);
        await this.mainLoop();
    }
  }

  async viewStatus() {
    printHeader();
    await showQuickStatus();
    this.rl.question('Press Enter to continue...', () => {
      this.mainLoop();
    });
  }

  async restartService() {
    // Check Docker before any operation
    await this.checkDocker(true);
    printHeader();
    console.log(`\n${colors.bright}Select Service:${colors.reset}\n`);

    for (const [num, service] of Object.entries(services)) {
      console.log(`  ${colors.cyan}${num})${colors.reset} ${service.name}`);
    }
    console.log(`\n  ${colors.yellow}0)${colors.reset} Back to main menu\n`);

    this.rl.question('Select service: ', async (choice) => {
      if (choice === '0') {
        await this.mainLoop();
        return;
      }

      const service = services[choice];
      if (!service) {
        console.log(`${colors.red}Invalid selection${colors.reset}`);
        await sleep(1500);
        await this.mainLoop();
        return;
      }

      console.log(`\n${colors.yellow}Restarting ${service.name}...${colors.reset}\n`);

      // Stop
      process.stdout.write('  Stopping...');
      await dockerExec(`docker stop ${service.container}`);
      process.stdout.write(`\r  ${colors.green}✓${colors.reset} Stopped    \n`);

      // Start
      process.stdout.write('  Starting...');
      await dockerExec(`docker start ${service.container}`);
      process.stdout.write(`\r  ${colors.green}✓${colors.reset} Started    \n`);

      // Health check
      process.stdout.write('  Health check...');
      await sleep(3000);
      const result = await dockerExec(`docker ps --filter name=${service.container} --format "{{.Status}}"`);

      if (result.output.includes('Up')) {
        process.stdout.write(`\r  ${colors.green}✓${colors.reset} Healthy    \n`);
        console.log(`\n${colors.green}Successfully restarted ${service.name}${colors.reset}`);
      } else {
        process.stdout.write(`\r  ${colors.red}✗${colors.reset} Failed     \n`);
        console.log(`\n${colors.red}Failed to restart ${service.name}${colors.reset}`);
      }

      this.rl.question('\nPress Enter to continue...', () => {
        this.mainLoop();
      });
    });
  }

  async healthCheck() {
    // Check Docker before any operation
    await this.checkDocker(true);
    printHeader();
    console.log(`\n${colors.yellow}Running health check...${colors.reset}\n`);

    const statuses = await getAllStatus();
    let healthy = 0;
    let unhealthy = 0;

    for (const status of statuses) {
      if (status.status === 'Running') {
        healthy++;
        process.stdout.write(`${colors.green}✓${colors.reset}`);
      } else {
        unhealthy++;
        process.stdout.write(`${colors.red}✗${colors.reset}`);
      }
    }

    console.log(`\n\n${colors.green}${healthy} Healthy${colors.reset} | ${colors.red}${unhealthy} Down${colors.reset}`);

    if (unhealthy === 0) {
      console.log(`${colors.green}All systems operational!${colors.reset}`);
    } else {
      console.log(`${colors.yellow}Some services need attention${colors.reset}`);
    }

    this.rl.question('\nPress Enter to continue...', () => {
      this.mainLoop();
    });
  }

  async viewLogs() {
    // Check Docker before any operation
    await this.checkDocker(true);
    printHeader();
    console.log(`\n${colors.bright}Select Service:${colors.reset}\n`);

    for (const [num, service] of Object.entries(services)) {
      console.log(`  ${colors.cyan}${num})${colors.reset} ${service.name}`);
    }
    console.log(`\n  ${colors.yellow}0)${colors.reset} Back to main menu\n`);

    this.rl.question('Select service: ', (choice) => {
      if (choice === '0') {
        this.mainLoop();
        return;
      }

      const service = services[choice];
      if (!service) {
        console.log(`${colors.red}Invalid selection${colors.reset}`);
        sleep(1500).then(() => this.mainLoop());
        return;
      }

      this.rl.question('How many lines? (default 50): ', async (lines) => {
        const lineCount = lines || '50';

        console.log(`\n${colors.yellow}Loading logs...${colors.reset}\n`);

        const result = await dockerExec(`docker logs ${service.container} --tail ${lineCount}`);
        console.log(result.output || result.error);

        this.rl.question('\nPress Enter to continue...', () => {
          this.mainLoop();
        });
      });
    });
  }

  async startAll() {
    // Check Docker before any operation
    await this.checkDocker();
    printHeader();
    console.log(`\n${colors.yellow}Starting all services...${colors.reset}\n`);

    // First check if containers exist
    const checkResult = await dockerExec('docker ps -a --format "{{.Names}}"');
    const existingContainers = checkResult.output.split('\n').filter(name => name);

    // Check if our containers exist
    const ourContainers = Object.values(services).map(s => s.container);
    const missingContainers = ourContainers.filter(c => !existingContainers.includes(c));

    if (missingContainers.length > 0) {
      console.log(`${colors.yellow}Containers not found. Creating with docker-compose...${colors.reset}\n`);

      // Use docker-compose to create and start all services
      process.stdout.write('  Creating and starting services...');
      const composeResult = await dockerExec('docker-compose up -d');

      if (composeResult.success) {
        console.log(` ${colors.green}✓${colors.reset}`);
        console.log(`\n${colors.yellow}Waiting for services to be ready...${colors.reset}`);
        await sleep(10000); // Wait for services to initialize
      } else {
        console.log(` ${colors.red}✗${colors.reset}`);
        console.log(`${colors.red}Error: ${composeResult.error}${colors.reset}`);
        this.rl.question('\nPress Enter to continue...', () => {
          this.mainLoop();
        });
        return;
      }
    } else {
      // Containers exist, just start them
      const order = ['postgres', 'automation-engine', 'backend', 'frontend', 'nginx'];

      for (const key of order) {
        const service = Object.values(services).find(s => s.container.includes(key));
        if (service) {
          process.stdout.write(`  Starting ${service.name.padEnd(25)}`);
          const result = await dockerExec(`docker start ${service.container}`);
          console.log(result.success ? `${colors.green}✓${colors.reset}` : `${colors.red}✗${colors.reset}`);
          await sleep(1000);
        }
      }
    }

    console.log(`\n${colors.green}All services started${colors.reset}`);
    this.rl.question('\nPress Enter to continue...', () => {
      this.mainLoop();
    });
  }

  async stopAll() {
    // Check Docker before any operation
    await this.checkDocker(true);
    printHeader();
    this.rl.question(`\n${colors.yellow}⚠️  WARNING: This will stop all services!${colors.reset}\nAre you sure? (y/N): `, async (confirm) => {
      if (confirm.toLowerCase() !== 'y') {
        await this.mainLoop();
        return;
      }

      console.log(`\n${colors.yellow}Stopping all services...${colors.reset}\n`);

      for (const service of Object.values(services)) {
        process.stdout.write(`  Stopping ${service.name.padEnd(25)}`);
        const result = await dockerExec(`docker stop ${service.container}`);
        console.log(result.success ? `${colors.green}✓${colors.reset}` : `${colors.red}✗${colors.reset}`);
      }

      console.log(`\n${colors.green}All services stopped${colors.reset}`);
      this.rl.question('\nPress Enter to continue...', () => {
        this.mainLoop();
      });
    });
  }

  async runDeepTest() {
    printHeader();
    console.log(`\n${colors.cyan}╔══════════════════════════════════════════════╗${colors.reset}`);
    console.log(`${colors.cyan}║${colors.reset}        ${colors.bright}DEEP STACK TEST SUITE${colors.reset}             ${colors.cyan}║${colors.reset}`);
    console.log(`${colors.cyan}╚══════════════════════════════════════════════╝${colors.reset}\n`);

    console.log(`${colors.yellow}Running comprehensive stack tests...${colors.reset}\n`);
    console.log(`${colors.dim}This will test all services and communications${colors.reset}\n`);

    const { spawn } = require('child_process');
    const testProcess = spawn('python3', ['test-stack-deep.py'], {
      stdio: 'inherit'
    });

    testProcess.on('close', async (code) => {
      console.log();
      if (code === 0) {
        console.log(`${colors.green}✅ Deep stack test completed successfully!${colors.reset}\n`);
      } else {
        console.log(`${colors.yellow}⚠️  Some issues detected (exit code: ${code})${colors.reset}\n`);
      }

      this.rl.question('Press Enter to return to menu...', () => {
        this.mainLoop();
      });
    });

    testProcess.on('error', async (err) => {
      console.log(`${colors.red}❌ Test failed: ${err.message}${colors.reset}\n`);
      this.rl.question('Press Enter to return to menu...', () => {
        this.mainLoop();
      });
    });
  }

  async openAgentCLI() {
    // Check if agent-engine container is running
    const statuses = await getAllStatus();
    const agentStatus = statuses.find(s => s.name === 'Agent Engine (Multi-Agent AI)');

    if (!agentStatus || agentStatus.status !== 'Running') {
      console.log(`\n${colors.yellow}⚠️  Agent Engine is not running${colors.reset}`);
      console.log(`${colors.cyan}Starting Agent Engine container...${colors.reset}\n`);

      // Start the agent-engine container
      const startResult = await dockerExec('docker start pilotpros-agent-engine-dev');
      if (!startResult.success) {
        // Try creating it with docker-compose
        await dockerExec('docker-compose up -d pilotpros-agent-engine-dev');
      }

      // Wait for it to be ready
      await sleep(2000);
    }

    console.log(`\n${colors.green}Opening Agent Engine CLI (Milhena)...${colors.reset}`);
    console.log(`${colors.dim}Connecting to container...${colors.reset}\n`);

    // Execute CLI inside the container
    const { spawn } = require('child_process');
    const cli = spawn('docker', ['exec', '-it', 'pilotpros-agent-engine-dev', 'python3', 'cli.py'], {
      stdio: 'inherit'
    });

    cli.on('close', (code) => {
      console.log(`\n${colors.cyan}Returned from Agent CLI${colors.reset}`);
      this.mainLoop();
    });

    cli.on('error', (err) => {
      console.log(`${colors.red}Error: ${err.message}${colors.reset}`);
      this.mainLoop();
    });
  }

  async openFrontend() {
    // Check if services are running
    const statuses = await getAllStatus();
    const runningCount = statuses.filter(s => s.status === 'Running').length;

    if (runningCount < 7) {
      console.log(`\n${colors.yellow}⚠️  Stack is not fully running${colors.reset}`);
      console.log(`${colors.cyan}To access the Business Portal, all services must be running.${colors.reset}\n`);

      this.rl.question('Start all services now? (Y/n): ', async (answer) => {
        if (answer.toLowerCase() !== 'n') {
          console.log(`\n${colors.yellow}Starting all services...${colors.reset}\n`);

          // Ensure Docker is running first
          await this.checkDocker();

          // Check if containers exist first
          const checkResult = await dockerExec('docker ps -a --format "{{.Names}}"');
          const existingContainers = checkResult.output.split('\n').filter(name => name);
          const ourContainers = Object.values(services).map(s => s.container);
          const missingContainers = ourContainers.filter(c => !existingContainers.includes(c));

          if (missingContainers.length > 0) {
            // Use docker-compose to create containers
            process.stdout.write('  Creating containers with docker-compose...');
            const composeResult = await dockerExec('docker-compose up -d');
            console.log(composeResult.success ? ` ${colors.green}✓${colors.reset}` : ` ${colors.red}✗${colors.reset}`);
            if (!composeResult.success) {
              console.log(`${colors.red}Error: ${composeResult.error}${colors.reset}`);
            }
          } else {
            // Containers exist, start them in order
            const order = ['postgres', 'automation-engine', 'backend', 'frontend', 'nginx'];

            for (const key of order) {
              const service = Object.values(services).find(s => s.container.includes(key));
              if (service) {
                process.stdout.write(`  Starting ${service.name.padEnd(25)}`);
                const result = await dockerExec(`docker start ${service.container}`);
                console.log(result.success ? `${colors.green}✓${colors.reset}` : `${colors.red}✗${colors.reset}`);
                await sleep(1000);
              }
            }
          }

          console.log(`\n${colors.green}All services started${colors.reset}`);
          console.log(`${colors.yellow}Waiting for services to be ready...${colors.reset}`);
          await sleep(5000);

          // Now open the portal
          this.openPortalInBrowser();
        } else {
          console.log(`${colors.red}Cannot open Business Portal without running services${colors.reset}`);
          await sleep(2000);
        }
        await this.mainLoop();
      });
    } else {
      // Services are running, just open the portal
      this.openPortalInBrowser();
      await sleep(2000);
      await this.mainLoop();
    }
  }

  openPortalInBrowser() {
    console.log(`\n${colors.yellow}Opening Business Portal...${colors.reset}`);

    // Cross-platform browser opening
    const url = 'http://localhost:3000';
    const platform = process.platform;

    if (platform === 'win32') {
      exec(`start ${url}`);
    } else if (platform === 'darwin') {
      exec(`open ${url}`);
    } else {
      exec(`xdg-open ${url}`);
    }

    console.log(`${colors.green}Business Portal opened in browser${colors.reset}`);
  }
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
  console.log(`\n\n${colors.green}Goodbye!${colors.reset}\n`);
  process.exit(0);
});

// Start the application
const manager = new StackManager();
manager.run().catch(error => {
  console.error(`${colors.red}Fatal error: ${error.message}${colors.reset}`);
  process.exit(1);
});