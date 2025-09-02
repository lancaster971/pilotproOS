#!/usr/bin/env node

import { execSync } from 'child_process';
import { existsSync, readFileSync, readdirSync } from 'fs';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import readline from 'readline';

const EXPORT_DIR = 'team-sync-exports';

console.log(chalk.blue('📥 PilotProOS Team Import - Sincronizzazione Dati\n'));

// Interfaccia readline per conferme utente
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const askQuestion = (question) => {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer.toLowerCase().trim());
    });
  });
};

// Trova l'archivio più recente
const findLatestArchive = () => {
  const spinner = ora('Cerco archivi disponibili...').start();
  
  if (!existsSync(EXPORT_DIR)) {
    spinner.fail('Nessun archivio trovato. Chiedi al collega di eseguire: npm run team:export');
    process.exit(1);
  }
  
  const files = readdirSync(EXPORT_DIR)
    .filter(file => file.startsWith('team-export-') && file.endsWith('.tar.gz'))
    .sort()
    .reverse();
  
  if (files.length === 0) {
    spinner.fail('Nessun archivio trovato. Chiedi al collega di eseguire: npm run team:export');
    process.exit(1);
  }
  
  const latestArchive = path.join(EXPORT_DIR, files[0]);
  const archiveSize = execSync(`du -h "${latestArchive}" | cut -f1`, { encoding: 'utf8' }).trim();
  
  spinner.succeed(`Archivio trovato: ${files[0]} (${archiveSize})`);
  
  // Mostra tutti gli archivi disponibili
  if (files.length > 1) {
    console.log(chalk.gray('\nArchivi disponibili:'));
    files.forEach((file, index) => {
      const filePath = path.join(EXPORT_DIR, file);
      const size = execSync(`du -h "${filePath}" | cut -f1`, { encoding: 'utf8' }).trim();
      const date = file.match(/team-export-(.+)\.tar\.gz/)[1];
      const isLatest = index === 0 ? chalk.green(' (più recente)') : '';
      console.log(chalk.gray(`   ${index + 1}. ${date} (${size})${isLatest}`));
    });
  }
  
  return latestArchive;
};

// Estrai archivio
const extractArchive = (archivePath) => {
  const spinner = ora('Estraggo archivio...').start();
  try {
    const extractDir = path.join(EXPORT_DIR, 'temp-import');
    
    // Rimuovi directory temporanea se esiste
    if (existsSync(extractDir)) {
      execSync(`rm -rf "${extractDir}"`, { stdio: 'pipe' });
    }
    
    // Estrai archivio
    execSync(`tar -xzf "${archivePath}" -C "${EXPORT_DIR}"`, { stdio: 'pipe' });
    
    // Trova la directory estratta
    const extractedDirs = readdirSync(EXPORT_DIR).filter(name => name.startsWith('export-'));
    if (extractedDirs.length === 0) {
      throw new Error('Directory estratta non trovata');
    }
    
    const extractedDir = path.join(EXPORT_DIR, extractedDirs[0]);
    
    spinner.succeed('Archivio estratto');
    return extractedDir;
  } catch (error) {
    spinner.fail(`Errore estrazione archivio: ${error.message}`);
    process.exit(1);
  }
};

// Verifica compatibilità
const checkCompatibility = (extractedDir) => {
  const spinner = ora('Verifico compatibilità...').start();
  try {
    const metadataPath = path.join(extractedDir, 'export-metadata.json');
    
    if (!existsSync(metadataPath)) {
      spinner.warn('Metadati non trovati, procedo comunque');
      return;
    }
    
    const metadata = JSON.parse(readFileSync(metadataPath, 'utf8'));
    const currentVersion = JSON.parse(readFileSync('package.json', 'utf8')).version;
    
    console.log(chalk.gray(`\n📊 Informazioni Export:`));
    console.log(chalk.gray(`   Data: ${new Date(metadata.exportDate).toLocaleString()}`));
    console.log(chalk.gray(`   Esportato da: ${metadata.exportedBy}@${metadata.hostname}`));
    console.log(chalk.gray(`   Versione: ${metadata.pilotproVersion} → ${currentVersion}`));
    
    if (metadata.pilotproVersion !== currentVersion) {
      spinner.warn(`Versione diversa (${metadata.pilotproVersion} → ${currentVersion})`);
    } else {
      spinner.succeed('Compatibilità verificata');
    }
  } catch (error) {
    spinner.warn(`Errore verifica compatibilità: ${error.message}`);
  }
};

// Ferma Docker stack
const stopDockerStack = () => {
  const spinner = ora('Fermo Docker stack...').start();
  try {
    execSync('npm run docker:stop', { stdio: 'pipe' });
    
    // Aspetta che i container si fermino completamente
    let attempts = 0;
    while (attempts < 10) {
      try {
        execSync('docker ps --format "table {{.Names}}" | grep pilotpros', { stdio: 'pipe' });
        execSync('sleep 2', { stdio: 'pipe' });
        attempts++;
      } catch {
        break; // Nessun container attivo
      }
    }
    
    spinner.succeed('Docker stack fermato');
  } catch (error) {
    spinner.fail(`Errore arresto Docker: ${error.message}`);
    process.exit(1);
  }
};

// Ripulisci volumi Docker
const cleanDockerVolumes = () => {
  const spinner = ora('Pulisco volumi Docker...').start();
  try {
    // Rimuovi volumi esistenti
    const volumes = ['pilotpros_postgres_dev_data', 'pilotpros_n8n_dev_data'];
    volumes.forEach(volume => {
      try {
        execSync(`docker volume rm ${volume}`, { stdio: 'pipe' });
      } catch {
        // Volume non esistente, ok
      }
    });
    
    spinner.succeed('Volumi Docker puliti');
  } catch (error) {
    spinner.warn(`Errore pulizia volumi: ${error.message}`);
  }
};

// Avvia Docker stack
const startDockerStack = () => {
  const spinner = ora('Avvio Docker stack...').start();
  try {
    execSync('npm run dev > /dev/null 2>&1 &', { stdio: 'pipe' });
    
    // Aspetta che i container si avviino
    let ready = false;
    let attempts = 0;
    
    while (!ready && attempts < 30) {
      try {
        execSync('docker exec pilotpros-postgres-dev pg_isready -U pilotpros_user -d pilotpros_db', { stdio: 'pipe' });
        ready = true;
      } catch {
        execSync('sleep 2', { stdio: 'pipe' });
        attempts++;
      }
    }
    
    if (!ready) {
      throw new Error('Timeout avvio database');
    }
    
    spinner.succeed('Docker stack avviato');
  } catch (error) {
    spinner.fail(`Errore avvio Docker: ${error.message}`);
    process.exit(1);
  }
};

// Importa database
const importDatabase = (extractedDir) => {
  const spinner = ora('Importo database...').start();
  try {
    const databaseFile = path.join(extractedDir, 'database-complete.sql');
    
    if (!existsSync(databaseFile)) {
      throw new Error('File database non trovato');
    }
    
    // Importa database
    execSync(`docker exec -i pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db < "${databaseFile}"`, { stdio: 'pipe' });
    
    // Verifica import
    const workflowCount = execSync(`docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -t -c "SELECT COUNT(*) FROM n8n.workflow_entity"`, { encoding: 'utf8' }).trim();
    
    spinner.succeed(`Database importato (${workflowCount} workflows)`);
  } catch (error) {
    spinner.fail(`Errore import database: ${error.message}`);
    process.exit(1);
  }
};

// Verifica n8n
const verifyN8n = () => {
  const spinner = ora('Verifico n8n...').start();
  try {
    // Aspetta che n8n sia pronto
    let attempts = 0;
    while (attempts < 20) {
      try {
        execSync(`docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/healthz"`, { stdio: 'pipe' });
        break;
      } catch {
        execSync('sleep 3', { stdio: 'pipe' });
        attempts++;
      }
    }
    
    // Verifica workflows
    const workflowsOutput = execSync(`docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/api/v1/workflows" --header "Accept: application/json" --user="admin:pilotpros_admin_2025"`, { encoding: 'utf8' });
    const workflows = JSON.parse(workflowsOutput);
    const workflowCount = workflows.data ? workflows.data.length : 0;
    
    spinner.succeed(`n8n verificato (${workflowCount} workflows attivi)`);
  } catch (error) {
    spinner.fail(`Errore verifica n8n: ${error.message}`);
    process.exit(1);
  }
};

// Pulizia
const cleanup = (extractedDir) => {
  const spinner = ora('Pulizia file temporanei...').start();
  try {
    execSync(`rm -rf "${extractedDir}"`, { stdio: 'pipe' });
    spinner.succeed('Pulizia completata');
  } catch (error) {
    spinner.warn(`Errore pulizia: ${error.message}`);
  }
};

// Esecuzione principale
const main = async () => {
  try {
    console.log(chalk.red('⚠️  ATTENZIONE: Questa operazione sovrascriverà tutti i dati attuali!'));
    console.log(chalk.yellow('📋 Verrà eseguito:'));
    console.log(chalk.gray('   1. Stop Docker stack'));
    console.log(chalk.gray('   2. Pulizia database e volumi'));
    console.log(chalk.gray('   3. Import dati dal collega'));
    console.log(chalk.gray('   4. Riavvio completo'));
    
    const confirm = await askQuestion('\n❓ Vuoi continuare? [y/N]: ');
    if (confirm !== 'y' && confirm !== 'yes') {
      console.log(chalk.yellow('❌ Import annullato'));
      rl.close();
      process.exit(0);
    }
    
    const archivePath = findLatestArchive();
    const extractedDir = extractArchive(archivePath);
    checkCompatibility(extractedDir);
    
    console.log(chalk.yellow('\n🔄 Avvio sincronizzazione...'));
    
    stopDockerStack();
    cleanDockerVolumes();
    startDockerStack();
    importDatabase(extractedDir);
    verifyN8n();
    cleanup(extractedDir);
    
    console.log(chalk.green('\n✅ IMPORT COMPLETATO CON SUCCESSO!\n'));
    console.log(chalk.yellow('🚀 Accessi:'));
    console.log(chalk.gray('   Frontend: http://localhost:3000'));
    console.log(chalk.gray('   Backend:  http://localhost:3001'));
    console.log(chalk.gray('   n8n:      http://localhost:5678 (admin / pilotpros_admin_2025)'));
    
    console.log(chalk.green('\n🎉 Dati sincronizzati con il collega!'));
    console.log(chalk.blue('💡 Ora hai gli stessi workflows e database del team\n'));
    
    rl.close();
    
  } catch (error) {
    console.error(chalk.red('❌ Errore durante l\'import:'), error.message);
    rl.close();
    process.exit(1);
  }
};

main();