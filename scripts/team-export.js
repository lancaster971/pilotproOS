#!/usr/bin/env node

import { execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';

const EXPORT_DIR = 'team-sync-exports';
const TIMESTAMP = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
const EXPORT_FOLDER = `${EXPORT_DIR}/export-${TIMESTAMP}`;

console.log(chalk.blue('🚀 PilotProOS Team Export - Sincronizzazione Dati\n'));

// Verifica che Docker sia in esecuzione
const checkDocker = () => {
  const spinner = ora('Verifico Docker stack...').start();
  try {
    execSync('docker ps --format "table {{.Names}}" | grep pilotpros', { stdio: 'pipe' });
    spinner.succeed('Docker stack attivo');
  } catch (error) {
    spinner.fail('Docker stack non attivo. Esegui: npm run dev');
    process.exit(1);
  }
};

// Crea directory di export
const createExportDir = () => {
  const spinner = ora('Creo directory di export...').start();
  try {
    if (!existsSync(EXPORT_DIR)) {
      mkdirSync(EXPORT_DIR, { recursive: true });
    }
    mkdirSync(EXPORT_FOLDER, { recursive: true });
    spinner.succeed(`Directory creata: ${EXPORT_FOLDER}`);
  } catch (error) {
    spinner.fail(`Errore creazione directory: ${error.message}`);
    process.exit(1);
  }
};

// Export completo database PostgreSQL
const exportDatabase = () => {
  const spinner = ora('Export database PostgreSQL...').start();
  try {
    const dumpFile = path.join(EXPORT_FOLDER, 'database-complete.sql');
    execSync(`docker exec pilotpros-postgres-dev pg_dump -U pilotpros_user -d pilotpros_db --clean --if-exists > "${dumpFile}"`, { stdio: 'pipe' });
    
    const stats = execSync(`wc -l < "${dumpFile}"`, { encoding: 'utf8' }).trim();
    spinner.succeed(`Database esportato (${stats} righe): database-complete.sql`);
  } catch (error) {
    spinner.fail(`Errore export database: ${error.message}`);
    process.exit(1);
  }
};

// Export workflows n8n via API
const exportWorkflows = () => {
  const spinner = ora('Export workflows n8n...').start();
  try {
    // Esporta tutti i workflows (con autenticazione basic admin)
    const workflowsOutput = execSync(`docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/api/v1/workflows" --header "Accept: application/json" --user="admin:pilotpros_admin_2025"`, { encoding: 'utf8' });
    const workflowsFile = path.join(EXPORT_FOLDER, 'workflows.json');
    writeFileSync(workflowsFile, workflowsOutput);
    
    // Conta workflows
    const workflows = JSON.parse(workflowsOutput);
    const workflowCount = workflows.data ? workflows.data.length : 0;
    
    // Esporta credenziali (con autenticazione basic admin)
    const credentialsOutput = execSync(`docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/api/v1/credentials" --header "Accept: application/json" --user="admin:pilotpros_admin_2025"`, { encoding: 'utf8' });
    const credentialsFile = path.join(EXPORT_FOLDER, 'credentials.json');
    writeFileSync(credentialsFile, credentialsOutput);
    
    const credentials = JSON.parse(credentialsOutput);
    const credentialCount = credentials.data ? credentials.data.length : 0;
    
    spinner.succeed(`Workflows esportati: ${workflowCount} workflows, ${credentialCount} credenziali`);
  } catch (error) {
    spinner.fail(`Errore export workflows: ${error.message}`);
    process.exit(1);
  }
};

// Export configurazioni Docker
const exportDockerConfig = () => {
  const spinner = ora('Export configurazioni...').start();
  try {
    // Copia file di configurazione importanti
    const configFiles = [
      'docker-compose.dev.yml',
      '.env',
      'database/init-dev'
    ];
    
    configFiles.forEach(file => {
      if (existsSync(file)) {
        execSync(`cp -r "${file}" "${EXPORT_FOLDER}/"`, { stdio: 'pipe' });
      }
    });
    
    // Crea metadati export
    const metadata = {
      exportDate: new Date().toISOString(),
      dockerVersion: execSync('docker --version', { encoding: 'utf8' }).trim(),
      pilotproVersion: JSON.parse(readFileSync('package.json', 'utf8')).version,
      exportedBy: execSync('whoami', { encoding: 'utf8' }).trim(),
      hostname: execSync('hostname', { encoding: 'utf8' }).trim()
    };
    
    writeFileSync(path.join(EXPORT_FOLDER, 'export-metadata.json'), JSON.stringify(metadata, null, 2));
    
    spinner.succeed('Configurazioni esportate');
  } catch (error) {
    spinner.fail(`Errore export configurazioni: ${error.message}`);
    process.exit(1);
  }
};

// Crea archivio compresso
const createArchive = () => {
  const spinner = ora('Creo archivio compresso...').start();
  try {
    const archiveName = `team-export-${TIMESTAMP}.tar.gz`;
    const archivePath = path.join(EXPORT_DIR, archiveName);
    
    execSync(`tar -czf "${archivePath}" -C "${EXPORT_DIR}" "export-${TIMESTAMP}"`, { stdio: 'pipe' });
    
    const archiveSize = execSync(`du -h "${archivePath}" | cut -f1`, { encoding: 'utf8' }).trim();
    
    // Rimuovi cartella temporanea
    execSync(`rm -rf "${EXPORT_FOLDER}"`, { stdio: 'pipe' });
    
    spinner.succeed(`Archivio creato: ${archiveName} (${archiveSize})`);
    
    console.log(chalk.green('\n✅ EXPORT COMPLETATO CON SUCCESSO!\n'));
    console.log(chalk.yellow('📁 Archivio:'), chalk.bold(archivePath));
    console.log(chalk.yellow('📤 Per condividere:'));
    console.log(chalk.gray(`   1. Carica su Google Drive/Dropbox`));
    console.log(chalk.gray(`   2. Condividi link con il collega`));
    console.log(chalk.gray(`   3. Il collega esegue: npm run team:import`));
    
    return archivePath;
  } catch (error) {
    spinner.fail(`Errore creazione archivio: ${error.message}`);
    process.exit(1);
  }
};

// Esecuzione principale
const main = async () => {
  try {
    checkDocker();
    createExportDir();
    exportDatabase();
    exportWorkflows();
    exportDockerConfig();
    const archivePath = createArchive();
    
    console.log(chalk.green('\n🎉 Dati pronti per la sincronizzazione team!'));
    console.log(chalk.blue('💡 Tip: Aggiungi l\'archivio a .gitignore per evitare commit accidentali\n'));
    
  } catch (error) {
    console.error(chalk.red('❌ Errore durante l\'export:'), error.message);
    process.exit(1);
  }
};

main();