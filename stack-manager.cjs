#!/usr/bin/env node

/**
 * PilotProOS Manager - Cross-Platform Interactive Menu
 * Works on Windows, macOS, and Linux
 */

const { exec, spawn } = require('child_process');
const readline = require('readline');
const util = require('util');
const execAsync = util.promisify(exec);

// Service mappings - business-friendly names
const services = {
  '1': { key: 'data', name: 'Data Management System', container: 'pilotpros-postgres-dev' },
  '2': { key: 'engine', name: 'Automation Engine', container: 'pilotpros-backend-dev' },
  '3': { key: 'portal', name: 'Business Portal', container: 'pilotpros-frontend-dev' },
  '4': { key: 'ai', name: 'AI Automation Engine', container: 'pilotpros-automation-engine-dev' },
  '5': { key: 'access', name: 'Access Manager', container: 'pilotpros-nginx-dev' },
  '6': { key: 'monitor', name: 'System Monitor', container: 'pilotpros-stack-controller' }
};

// Cross-platform clear screen
const clearScreen = () => {
  if (process.platform === 'win32') {
    console.clear();
  } else {
    console.log('\x1Bc');
  }
};

// Cross-platform colors (works in most terminals)
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

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Promisify readline question
const question = (query) => new Promise((resolve) => rl.question(query, resolve));

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
  console.log(`  ${colors.cyan}7)${colors.reset} Open Web Dashboard`);
  console.log(`  ${colors.cyan}8)${colors.reset} Refresh Status\n`);
  console.log(`  ${colors.red}q)${colors.reset} Quit\n`);
}

// Show service menu
async function selectService(action) {
  console.log(`\n${colors.bright}Select Service:${colors.reset}\n`);

  for (const [num, service] of Object.entries(services)) {
    console.log(`  ${colors.cyan}${num})${colors.reset} ${service.name}`);
  }
  console.log(`\n  ${colors.yellow}0)${colors.reset} Back to main menu\n`);

  const choice = await question('Select service: ');

  if (choice === '0') return null;
  if (services[choice]) return services[choice];

  console.log(`${colors.red}Invalid selection${colors.reset}`);
  await sleep(1500);
  return null;
}

// Sleep helper
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Restart service
async function restartService() {
  const service = await selectService('restart');
  if (!service) return;

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

  await question('\nPress Enter to continue...');
}

// View logs
async function viewLogs() {
  const service = await selectService('logs');
  if (!service) return;

  const lines = await question('How many lines? (default 50): ') || '50';

  console.log(`\n${colors.yellow}Loading logs...${colors.reset}\n`);

  const result = await dockerExec(`docker logs ${service.container} --tail ${lines}`);
  console.log(result.output || result.error);

  await question('\nPress Enter to continue...');
}

// Quick health check
async function healthCheck() {
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

  await question('\nPress Enter to continue...');
}

// Start all services
async function startAll() {
  console.log(`\n${colors.yellow}Starting all services...${colors.reset}\n`);

  const order = ['postgres', 'n8n', 'backend', 'frontend', 'nginx', 'stack'];

  for (const key of order) {
    const service = Object.values(services).find(s => s.key === key);
    if (service) {
      process.stdout.write(`  Starting ${service.name.padEnd(25)}`);
      const result = await dockerExec(`docker start ${service.container}`);
      console.log(result.success ? `${colors.green}✓${colors.reset}` : `${colors.red}✗${colors.reset}`);
      await sleep(1000);
    }
  }

  console.log(`\n${colors.green}All services started${colors.reset}`);
  await question('\nPress Enter to continue...');
}

// Stop all services
async function stopAll() {
  const confirm = await question(`\n${colors.yellow}⚠️  WARNING: This will stop all services!${colors.reset}\nAre you sure? (y/N): `);

  if (confirm.toLowerCase() !== 'y') return;

  console.log(`\n${colors.yellow}Stopping all services...${colors.reset}\n`);

  for (const service of Object.values(services)) {
    process.stdout.write(`  Stopping ${service.name.padEnd(25)}`);
    const result = await dockerExec(`docker stop ${service.container}`);
    console.log(result.success ? `${colors.green}✓${colors.reset}` : `${colors.red}✗${colors.reset}`);
  }

  console.log(`\n${colors.green}All services stopped${colors.reset}`);
  await question('\nPress Enter to continue...');
}

// Open dashboard
async function openDashboard() {
  console.log(`\n${colors.yellow}Opening web dashboard...${colors.reset}`);

  // Cross-platform browser opening
  const url = 'http://localhost:3005';
  const platform = process.platform;

  if (platform === 'win32') {
    exec(`start ${url}`);
  } else if (platform === 'darwin') {
    exec(`open ${url}`);
  } else {
    exec(`xdg-open ${url}`);
  }

  console.log(`${colors.green}Dashboard opened in browser${colors.reset}`);
  await sleep(2000);
}

// Main loop
async function main() {
  while (true) {
    printHeader();
    await showQuickStatus();
    showMainMenu();

    const choice = await question('Select option: ');

    switch (choice.toLowerCase()) {
      case '1':
        printHeader();
        await showQuickStatus();
        await question('Press Enter to continue...');
        break;
      case '2':
        printHeader();
        await restartService();
        break;
      case '3':
        printHeader();
        await healthCheck();
        break;
      case '4':
        printHeader();
        await viewLogs();
        break;
      case '5':
        printHeader();
        await startAll();
        break;
      case '6':
        printHeader();
        await stopAll();
        break;
      case '7':
        await openDashboard();
        break;
      case '8':
        // Just refresh
        continue;
      case 'q':
        console.log(`\n${colors.green}Goodbye!${colors.reset}\n`);
        rl.close();
        process.exit(0);
        break;
      default:
        console.log(`${colors.red}Invalid option${colors.reset}`);
        await sleep(1500);
    }
  }
}

// Check Docker availability
async function checkDocker() {
  const result = await dockerExec('docker --version');
  if (!result.success) {
    console.error(`${colors.red}Error: Docker is not available!${colors.reset}`);
    console.error('Please ensure Docker is installed and running.');
    process.exit(1);
  }
}

// Entry point
async function start() {
  await checkDocker();
  await main();
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
  console.log(`\n\n${colors.green}Goodbye!${colors.reset}\n`);
  rl.close();
  process.exit(0);
});

// Start the application
start().catch(error => {
  console.error(`${colors.red}Fatal error: ${error.message}${colors.reset}`);
  process.exit(1);
});