# 🔌 Team Sync System - API Documentation

**Version**: 1.0.0  
**Type**: Internal Node.js Scripts  
**Authentication**: Local Docker Access Required

## 📋 Overview

The Team Sync System exposes functionality through NPM scripts that wrap Node.js automation scripts. While not a traditional REST API, these scripts provide programmatic interfaces for team synchronization operations.

## 🛠 Script APIs

### `npm run team:export`

**Script**: `scripts/team-export.js`  
**Purpose**: Creates complete environment snapshot for team sharing

#### Input Parameters
- **Environment Variables**: Automatically detected
- **Docker Stack**: Must be running (`docker ps` verification)
- **File System**: Write access to project root

#### Output Structure
```javascript
// Created archive: team-sync-exports/team-export-TIMESTAMP.tar.gz
{
  "archivePath": "team-sync-exports/team-export-2025-01-15T14-30-00.tar.gz",
  "archiveSize": "15MB", 
  "metadata": {
    "exportDate": "2025-01-15T14:30:00.000Z",
    "dockerVersion": "Docker version 20.10.21",
    "pilotproVersion": "1.0.0", 
    "exportedBy": "developer1",
    "hostname": "MacBook-Pro-A.local"
  },
  "contents": {
    "database": "database-complete.sql",
    "workflows": "workflows.json",
    "credentials": "credentials.json", 
    "configs": ["docker-compose.dev.yml", ".env", "database/init-dev/"]
  }
}
```

#### Success Response
```bash
✅ EXPORT COMPLETATO CON SUCCESSO!
📁 Archivio: team-export-2025-01-15T14-30-00.tar.gz (15MB)
📤 Per condividere:
   1. Carica su Google Drive/Dropbox
   2. Condividi link con il collega
   3. Il collega esegue: npm run team:import
```

#### Error Codes
| Code | Description | Resolution |
|------|-------------|------------|
| 1 | Docker stack not active | Run `npm run dev` |
| 1 | Database connection failed | Check PostgreSQL container health |
| 1 | n8n API timeout | Verify n8n container status |
| 1 | Disk space insufficient | Free up disk space |
| 1 | Permission denied | Check file system permissions |

#### API Calls Made
```javascript
// Internal Docker commands
execSync('docker ps --format "table {{.Names}}" | grep pilotpros')
execSync('docker exec pilotpros-postgres-dev pg_dump -U pilotpros_user -d pilotpros_db')
execSync('docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/api/v1/workflows"')
execSync('docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/api/v1/credentials"')
```

---

### `npm run team:import`

**Script**: `scripts/team-import.js`  
**Purpose**: Safely imports team member's environment data

#### Input Parameters
```javascript
// Interactive prompts
{
  "confirmOverwrite": "boolean", // User confirmation required
  "archiveSelection": "string",  // Auto-selects latest or prompts
  "safetyConfirmation": "boolean" // Final confirmation before destructive operation
}
```

#### Archive Discovery
```javascript
// Searches for files matching pattern
const archivePattern = /team-export-.*\.tar\.gz$/;
const searchDirectory = "team-sync-exports/";

// Returns newest by timestamp
const latestArchive = files.sort().reverse()[0];
```

#### Process Flow API
```javascript
// Step-by-step execution
const importProcess = {
  1: "findLatestArchive()",      // Locate import file
  2: "extractArchive()",         // Decompress .tar.gz  
  3: "checkCompatibility()",     // Version verification
  4: "stopDockerStack()",        // Safe shutdown
  5: "cleanDockerVolumes()",     // Data cleanup
  6: "startDockerStack()",       // Fresh start
  7: "importDatabase()",         // PostgreSQL restore
  8: "verifyN8n()",             // Health verification
  9: "cleanup()"                // Temp file removal
};
```

#### Success Response
```bash
✅ IMPORT COMPLETATO CON SUCCESSO!
🚀 Accessi:
   Frontend: http://localhost:3000
   Backend:  http://localhost:3001  
   n8n:      http://localhost:5678 (admin / pilotpros_admin_2025)
   
🎉 Dati sincronizzati con il collega!
💡 Ora hai gli stessi workflows e database del team
```

#### Error Handling
```javascript
const errorHandling = {
  "ARCHIVE_NOT_FOUND": {
    code: 1,
    message: "Nessun archivio trovato. Chiedi al collega di eseguire: npm run team:export",
    recovery: "Wait for team member to export"
  },
  "DOCKER_START_TIMEOUT": {
    code: 1, 
    message: "Timeout avvio database",
    recovery: "Retry import or manual docker reset"
  },
  "IMPORT_CORRUPTION": {
    code: 1,
    message: "Errore import database", 
    recovery: "Verify archive integrity"
  },
  "USER_CANCELLED": {
    code: 0,
    message: "❌ Import annullato",
    recovery: "Normal exit, no changes made"
  }
};
```

---

### `npm run team:sync`

**Script**: Wrapper command  
**Purpose**: Export + coordination instructions

#### Implementation
```javascript
// package.json script
"team:sync": "npm run team:export && echo '\n🔄 Ora chiedi al collega di eseguire: npm run team:import'"
```

#### Output
```bash
# Executes team:export first
[... export output ...]

🔄 Ora chiedi al collega di eseguire: npm run team:import
```

## 🔧 Internal APIs

### Database Export API

#### PostgreSQL Dump
```javascript
const exportDatabase = () => {
  const dumpFile = path.join(EXPORT_FOLDER, 'database-complete.sql');
  const command = `docker exec pilotpros-postgres-dev pg_dump -U pilotpros_user -d pilotpros_db --clean --if-exists`;
  
  execSync(`${command} > "${dumpFile}"`, { stdio: 'pipe' });
  
  // Verification
  const stats = execSync(`wc -l < "${dumpFile}"`, { encoding: 'utf8' }).trim();
  return { file: dumpFile, lines: parseInt(stats) };
};
```

#### n8n Workflow Export  
```javascript
const exportWorkflows = () => {
  const apiBase = "http://localhost:5678/api/v1";
  const auth = "admin:pilotpros_admin_2025";
  
  // Workflows
  const workflowsCmd = `docker exec pilotpros-automation-engine-dev wget -qO- "${apiBase}/workflows" --header "Accept: application/json" --user="${auth}"`;
  const workflowsData = execSync(workflowsCmd, { encoding: 'utf8' });
  
  // Credentials
  const credentialsCmd = `docker exec pilotpros-automation-engine-dev wget -qO- "${apiBase}/credentials" --header "Accept: application/json" --user="${auth}"`;  
  const credentialsData = execSync(credentialsCmd, { encoding: 'utf8' });
  
  return {
    workflows: JSON.parse(workflowsData),
    credentials: JSON.parse(credentialsData)
  };
};
```

### Docker Management API

#### Stack Control
```javascript
const dockerAPI = {
  // Check if stack is running
  isStackRunning: () => {
    try {
      execSync('docker ps --format "table {{.Names}}" | grep pilotpros', { stdio: 'pipe' });
      return true;
    } catch { 
      return false; 
    }
  },
  
  // Stop all PilotPro containers
  stopStack: () => {
    execSync('npm run docker:stop', { stdio: 'pipe' });
  },
  
  // Start development stack
  startStack: () => {
    execSync('npm run dev > /dev/null 2>&1 &', { stdio: 'pipe' });
  },
  
  // Clean volumes
  cleanVolumes: () => {
    const volumes = ['pilotpros_postgres_dev_data', 'pilotpros_n8n_dev_data'];
    volumes.forEach(volume => {
      try {
        execSync(`docker volume rm ${volume}`, { stdio: 'pipe' });
      } catch {
        // Volume doesn't exist - OK
      }
    });
  }
};
```

### Health Check API

#### Database Verification
```javascript
const verifyDatabase = () => {
  const healthCheck = {
    // PostgreSQL ready check
    isPostgreSQLReady: () => {
      try {
        execSync('docker exec pilotpros-postgres-dev pg_isready -U pilotpros_user -d pilotpros_db', { stdio: 'pipe' });
        return true;
      } catch { 
        return false; 
      }
    },
    
    // Workflow count verification  
    getWorkflowCount: () => {
      const result = execSync('docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -t -c "SELECT COUNT(*) FROM n8n.workflow_entity"', { encoding: 'utf8' });
      return parseInt(result.trim());
    }
  };
  
  return healthCheck;
};
```

#### n8n Verification
```javascript  
const verifyN8n = () => {
  // Wait for n8n to be ready
  let attempts = 0;
  const maxAttempts = 20;
  
  while (attempts < maxAttempts) {
    try {
      execSync('docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/healthz"', { stdio: 'pipe' });
      break; // Success
    } catch {
      execSync('sleep 3', { stdio: 'pipe' }); 
      attempts++;
    }
  }
  
  if (attempts >= maxAttempts) {
    throw new Error('n8n health check timeout');
  }
  
  // Verify workflow access
  const workflowsOutput = execSync('docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/api/v1/workflows" --header "Accept: application/json" --user="admin:pilotpros_admin_2025"', { encoding: 'utf8' });
  const workflows = JSON.parse(workflowsOutput);
  
  return {
    healthy: true,
    workflowCount: workflows.data ? workflows.data.length : 0
  };
};
```

## 📊 Data Formats

### Export Metadata Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "exportDate": {
      "type": "string",
      "format": "date-time"
    },
    "dockerVersion": {
      "type": "string",
      "pattern": "Docker version .*"
    },
    "pilotproVersion": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "exportedBy": {
      "type": "string"
    },
    "hostname": {
      "type": "string"
    }
  },
  "required": ["exportDate", "pilotproVersion", "exportedBy"]
}
```

### n8n Workflow Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object", 
  "properties": {
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "active": { "type": "boolean" },
          "nodes": { "type": "array" },
          "connections": { "type": "object" },
          "createdAt": { "type": "string", "format": "date-time" },
          "updatedAt": { "type": "string", "format": "date-time" }
        }
      }
    }
  }
}
```

## 🔒 Security Model

### Access Control
```javascript
const securityModel = {
  "authentication": {
    "method": "local_docker_access",
    "requirements": [
      "Docker daemon access",
      "File system read/write permissions", 
      "Network access to Docker containers"
    ]
  },
  
  "data_protection": {
    "credentials": "n8n_encrypted_format",
    "database": "local_postgresql_access_only", 
    "archives": "local_filesystem_only",
    "git_exclusion": "automatic_via_gitignore"
  },
  
  "audit_trail": {
    "export_metadata": "full_tracking",
    "import_logs": "process_logging",
    "user_confirmations": "interactive_prompts"
  }
};
```

### Data Sensitivity Levels
| Data Type | Sensitivity | Protection | Access |
|-----------|-------------|------------|--------|
| Source Code | Low | Git versioning | Team repository |
| Database Schema | Medium | Export/import only | Local Docker |
| Business Data | High | Local only, no Git | Local Docker |
| n8n Credentials | Critical | Encrypted export | n8n container only |
| Export Archives | Critical | Gitignored, local | Manual sharing only |

## 🚀 Extension Points

### Custom Export Handlers
```javascript
// Add custom exporters
const customExporters = {
  addCustomExporter: (name, handler) => {
    exportHandlers[name] = handler;
  },
  
  // Example: Export custom configs
  exportCustomConfigs: () => {
    // Custom logic here
    return customConfigData;
  }
};
```

### Import Hooks
```javascript  
// Pre/post import hooks
const importHooks = {
  beforeImport: [],
  afterImport: [],
  
  addHook: (timing, handler) => {
    importHooks[timing].push(handler);
  }
};

// Example usage
importHooks.addHook('beforeImport', (metadata) => {
  console.log(`Importing from ${metadata.exportedBy}`);
});
```

### Validation Extensions
```javascript
// Custom validation rules
const validators = {
  addCustomValidator: (name, validator) => {
    customValidators[name] = validator;
  },
  
  // Example: Validate business rules
  validateBusinessRules: (importData) => {
    // Custom business logic validation
    return validationResult;
  }
};
```

## 📈 Performance Monitoring

### Timing APIs
```javascript
const performanceMetrics = {
  // Export timing
  exportTiming: {
    databaseExport: 0,    // milliseconds
    workflowExport: 0,    // milliseconds  
    archiveCreation: 0,   // milliseconds
    totalTime: 0          // milliseconds
  },
  
  // Import timing
  importTiming: {
    archiveExtraction: 0, // milliseconds
    dockerRestart: 0,     // milliseconds
    databaseImport: 0,    // milliseconds
    verification: 0,      // milliseconds
    totalTime: 0          // milliseconds
  },
  
  // Size metrics
  sizeMetrics: {
    databaseSize: 0,      // bytes
    archiveSize: 0,       // bytes
    compressionRatio: 0   // percentage
  }
};
```

### Health Monitoring
```javascript
const healthMonitoring = {
  // System health checks
  checkSystemHealth: () => ({
    dockerRunning: dockerAPI.isStackRunning(),
    diskSpace: getAvailableDiskSpace(),
    memoryUsage: getMemoryUsage(),
    containerHealth: getContainerHealth()
  }),
  
  // Data integrity checks
  checkDataIntegrity: () => ({
    workflowCount: verifyDatabase().getWorkflowCount(),
    schemaVersion: getDatabaseSchemaVersion(),  
    lastExportDate: getLastExportDate(),
    archiveIntegrity: verifyArchiveIntegrity()
  })
};
```

---

## 📚 Related Documentation

- **[team-sync-system.md](./team-sync-system.md)** - Complete technical documentation
- **[../TEAM_WORKFLOW.md](../TEAM_WORKFLOW.md)** - User workflow guide  
- **[troubleshooting-team-sync.md](./troubleshooting-team-sync.md)** - Error resolution guide

---

**API Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**Stability**: Production Ready