#!/usr/bin/env node

const { exec } = require('child_process');
const readline = require('readline');
const util = require('util');
const execAsync = util.promisify(exec);

// Service mappings
const services = {
  '1': { name: 'PostgreSQL Database', container: 'pilotpros-postgres' },
  '2': { name: 'Backend API', container: 'pilotpros-backend' },
  '3': { name: 'Frontend', container: 'pilotpros-frontend' },
  '4': { name: 'n8n Automation', container: 'pilotpros-n8n' },
  '5': { name: 'Stack Controller', container: 'pilotpros-stack-controller' }
};

// Simple colors
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m'
};

async function getStatus(container) {
  try {
    const { stdout } = await execAsync(`docker ps --filter name=${container} --format "{{.Status}}"`);
    return stdout.includes('Up') ? 'Running' : 'Stopped';
  } catch {
    return 'Error';
  }
}

async function showStatus() {
  console.log('\n=== PilotProOS Status ===\n');

  for (const [num, service] of Object.entries(services)) {
    const status = await getStatus(service.container);
    const color = status === 'Running' ? colors.green : colors.red;
    console.log(`${num}. ${service.name}: ${color}${status}${colors.reset}`);
  }
}

async function restartService(num) {
  const service = services[num];
  if (!service) {
    console.log('Invalid service number');
    return;
  }

  console.log(`\nRestarting ${service.name}...`);

  try {
    await execAsync(`docker restart ${service.container}`);
    console.log(`${colors.green}✓ ${service.name} restarted${colors.reset}`);
  } catch (error) {
    console.log(`${colors.red}✗ Failed to restart ${service.name}${colors.reset}`);
  }
}

async function main() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  function showMenu() {
    console.log('\n=== PilotProOS Manager ===');
    console.log('1. View Status');
    console.log('2. Restart Service');
    console.log('3. Start All');
    console.log('4. Stop All');
    console.log('5. Exit');
    console.log();
  }

  function prompt() {
    rl.question('Select option: ', async (answer) => {
      switch(answer) {
        case '1':
          await showStatus();
          showMenu();
          prompt();
          break;

        case '2':
          await showStatus();
          rl.question('\nWhich service to restart? (1-5): ', async (num) => {
            await restartService(num);
            showMenu();
            prompt();
          });
          break;

        case '3':
          console.log('\nStarting all services...');
          for (const service of Object.values(services)) {
            await execAsync(`docker start ${service.container}`).catch(() => {});
          }
          console.log(`${colors.green}All services started${colors.reset}`);
          showMenu();
          prompt();
          break;

        case '4':
          console.log('\nStopping all services...');
          for (const service of Object.values(services)) {
            await execAsync(`docker stop ${service.container}`).catch(() => {});
          }
          console.log(`${colors.yellow}All services stopped${colors.reset}`);
          showMenu();
          prompt();
          break;

        case '5':
          console.log('\nGoodbye!');
          rl.close();
          process.exit(0);
          break;

        default:
          console.log('Invalid option');
          showMenu();
          prompt();
      }
    });
  }

  // Check Docker
  try {
    await execAsync('docker --version');
  } catch {
    console.error('Docker is not available!');
    process.exit(1);
  }

  showMenu();
  prompt();
}

main().catch(console.error);