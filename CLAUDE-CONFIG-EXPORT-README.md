# 🚀 Claude Code Configuration Export/Import

Scripts per replicare la configurazione completa di Claude Code su un altro Mac.

---

## 📦 Cosa Viene Esportato

### 1. **MCP Settings** (`~/.claude/mcp_settings.json`)
- MCP servers globali (postgres, github, docker, chromadb, sequential-thinking, TestSprite, openmemory)
- Configurazione connessioni database
- Environment variables MCP

### 2. **Global CLAUDE.md** (`~/.claude/CLAUDE.md`)
- Policy globali (tutti i progetti)
- Agent Orchestration Policy (5-step workflow)
- Zero Custom Code policy
- MCP Servers documentation
- OpenMemory Usage Policy

### 3. **Workflow Commands** (`~/.claude/commands/`)
- `/resume-session` - Inizio sessione (con Step 5.5 VERIFICATION)
- `/finalize-smart` - Chiusura completa (OpenMemory + PROGRESS.md + Git)
- `/checkpoint` - Savepoint rapido (no git commit)

### 4. **Claude Desktop Config** (`~/Library/Application Support/Claude/claude_desktop_config.json`)
- MCP servers per Claude Desktop app
- Project-specific MCP (se configurati)

### 5. **OpenMemory Database** (`.openmemory/`)
- Database SQLite con memoria persistente
- Session history e abstracts
- ⚠️ Richiede import manuale per path progetto specifico

---

## 🔧 Uso

### **STEP 1: Esporta Configurazione (Mac Sorgente)**

```bash
cd /path/to/project  # Importante: essere nella directory con .openmemory se vuoi esportarla

./export-claude-config.sh
```

**Output**: `claude-code-config-YYYYMMDD-HHMMSS.tar.gz`

Lo script:
- ✅ Esporta tutta la configurazione
- ✅ Crea archivio compresso
- ✅ Include script di import automatico
- ✅ Mostra summary dettagliato

**Esempio Output**:
```
╔════════════════════════════════════════════════════════════════╗
║  🚀 CLAUDE CODE CONFIGURATION EXPORT                          ║
╚════════════════════════════════════════════════════════════════╝

[1/6] Exporting MCP Settings...
  ✓ MCP settings exported
    Servers found: 8
    - postgres
    - github
    - docker
    - chromadb
    - sequential-thinking
    - TestSprite
    - openmemory
    - ide

[2/6] Exporting Global CLAUDE.md...
  ✓ CLAUDE.md exported (450 lines)

[3/6] Exporting Workflow Commands...
  ✓ Commands exported: 3
    - resume-session
    - finalize-smart
    - checkpoint

[4/6] Exporting Claude Desktop Config...
  ✓ Claude Desktop config exported
    Desktop MCP Servers: 1
    - testsprite

[5/6] Exporting OpenMemory Database...
  ✓ OpenMemory database exported (24K)

[6/6] Creating Import Script...
  ✓ Import script created

📦 Creating Archive...
  ✓ Archive created: claude-code-config-20251014-005500.tar.gz
    Size: 128K

╔════════════════════════════════════════════════════════════════╗
║  ✅ EXPORT COMPLETE                                            ║
╚════════════════════════════════════════════════════════════════╝

📦 Archive Created: claude-code-config-20251014-005500.tar.gz (128K)
```

---

### **STEP 2: Trasferisci Archivio al Nuovo Mac**

Opzioni:
1. **AirDrop** (più veloce)
2. **USB drive**
3. **Dropbox/iCloud** (se già sincronizzato)
4. **Email** (se archivio <25MB)

---

### **STEP 3: Importa Configurazione (Mac Destinazione)**

```bash
# Extract archive
tar -xzf claude-code-config-YYYYMMDD-HHMMSS.tar.gz

# Navigate to extracted directory
cd claude-code-config-YYYYMMDD-HHMMSS

# Run import script
./import-config.sh
```

**Lo script chiederà conferma**:
```
⚠️  WARNING: This will overwrite existing Claude Code configuration
   Backups will be created with timestamp: 20251014-010000

Continue? (y/N)
```

**Cosa fa l'import**:
- ✅ Crea backup automatici (`.backup-YYYYMMDD-HHMMSS`)
- ✅ Importa MCP settings
- ✅ Importa CLAUDE.md globale
- ✅ Importa workflow commands
- ✅ Importa Claude Desktop config
- ⚠️ OpenMemory database richiede import manuale

**Esempio Output**:
```
╔════════════════════════════════════════════════════════════════╗
║  🚀 CLAUDE CODE CONFIGURATION IMPORT                          ║
╚════════════════════════════════════════════════════════════════╝

[1/5] Importing MCP Settings...
  📦 Backup created: mcp_settings.json.backup-20251014-010000
  ✓ MCP settings imported

[2/5] Importing Global CLAUDE.md...
  📦 Backup created: CLAUDE.md.backup-20251014-010000
  ✓ CLAUDE.md imported

[3/5] Importing Workflow Commands...
  📦 Backup created: commands.backup-20251014-010000
  ✓ Commands imported: 3

[4/5] Importing Claude Desktop Config...
  📦 Backup created: claude_desktop_config.json.backup-20251014-010000
  ✓ Claude Desktop config imported

[5/5] Importing OpenMemory Database...
  ⚠ OpenMemory database found
     Manual import required for project-specific location
     Source: /path/to/extracted/openmemory/

╔════════════════════════════════════════════════════════════════╗
║  ✅ IMPORT COMPLETE                                            ║
╚════════════════════════════════════════════════════════════════╝
```

---

### **STEP 4: Post-Import (Mac Destinazione)**

#### **4.1 Restart Claude Desktop**
```bash
# Chiudi completamente Claude Desktop
# Cmd+Q per quit (non solo chiudere finestra)

# Riapri Claude Desktop
# I nuovi MCP servers verranno caricati
```

#### **4.2 Verifica MCP Servers**
```bash
# In terminale
claude mcp list

# Expected output:
# postgres: Connected
# github: Connected
# docker: Connected
# chromadb: Connected
# sequential-thinking: Connected
# TestSprite: Connected
# openmemory: Connected
# ide: Connected
```

#### **4.3 Test Workflow Commands (Opzionale)**
```bash
# In Claude Code, prova:
/resume-session    # Deve mostrare Step 5.5 VERIFICATION
/checkpoint        # Deve salvare in OpenMemory
/finalize-smart    # Deve eseguire triple redundancy save
```

#### **4.4 Import OpenMemory Database (Se Necessario)**
```bash
# Naviga alla directory del progetto
cd /path/to/your/project

# Copia database OpenMemory
cp -r /path/to/extracted/claude-code-config-YYYYMMDD-HHMMSS/openmemory .openmemory

# Verifica
ls -lh .openmemory/pilotpros-memory.sqlite
# Expected: file esistente con dimensione > 0
```

---

## 🔍 Troubleshooting

### **Problema 1: MCP Server non si connette**

**Sintomi**:
```bash
claude mcp list
# postgres: Failed
```

**Soluzione**:
1. Verifica path assoluti in `mcp_settings.json`:
   ```bash
   cat ~/.claude/mcp_settings.json | jq '.mcpServers.postgres'
   ```
2. Aggiorna path per il nuovo Mac (se diversi):
   ```json
   {
     "command": "npx",
     "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://..."]
   }
   ```
3. Restart Claude Desktop

---

### **Problema 2: Workflow Commands non trovati**

**Sintomi**:
```
/resume-session
# Command not found
```

**Soluzione**:
1. Verifica files:
   ```bash
   ls -lh ~/.claude/commands/
   # Deve mostrare: resume-session.md, finalize-smart.md, checkpoint.md
   ```
2. Verifica permessi:
   ```bash
   chmod 644 ~/.claude/commands/*.md
   ```
3. Restart Claude Code

---

### **Problema 3: Claude Desktop Config non caricato**

**Sintomi**:
- MCP servers non visibili in Claude Desktop app
- Solo Claude Code CLI funziona

**Soluzione**:
1. Verifica path:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
2. Quit Claude Desktop (Cmd+Q)
3. Delete cache:
   ```bash
   rm -rf ~/Library/Caches/Claude
   ```
4. Reopen Claude Desktop

---

### **Problema 4: OpenMemory database corrotto dopo import**

**Sintomi**:
```
mcp__openmemory__recall_memory_abstract
# Error: database disk image is malformed
```

**Soluzione**:
1. Verifica integrity:
   ```bash
   sqlite3 .openmemory/pilotpros-memory.sqlite "PRAGMA integrity_check;"
   # Expected: ok
   ```
2. Se corrotto, ripristina da export:
   ```bash
   rm -rf .openmemory
   cp -r /path/to/extracted/openmemory .openmemory
   ```

---

## 📝 Note Importanti

### **Path Differences Between Macs**

Se i path assoluti differiscono tra Mac sorgente e destinazione:

**MCP Servers che potrebbero avere path assoluti**:
- `postgres` - Connection string con path socket
- `TestSprite` - Project path
- `openmemory` - Database path

**Come aggiornare**:
1. Apri `~/.claude/mcp_settings.json`
2. Cerca path assoluti (es: `/Users/username/...`)
3. Sostituisci con path nuovo Mac
4. Restart Claude Desktop

**Esempio**:
```json
// Mac Sorgente
"postgres": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres",
           "postgresql://user@/var/run/postgresql:5432/dbname"]
}

// Mac Destinazione (se socket path diverso)
"postgres": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres",
           "postgresql://user@localhost:5432/dbname"]
}
```

---

### **Backup Safety**

L'import script crea automaticamente backup con timestamp:
- `mcp_settings.json.backup-YYYYMMDD-HHMMSS`
- `CLAUDE.md.backup-YYYYMMDD-HHMMSS`
- `commands.backup-YYYYMMDD-HHMMSS/`
- `claude_desktop_config.json.backup-YYYYMMDD-HHMMSS`

**Per ripristinare backup**:
```bash
# Esempio: ripristina MCP settings
cp ~/.claude/mcp_settings.json.backup-20251014-010000 ~/.claude/mcp_settings.json

# Restart Claude Desktop
```

---

### **OpenMemory Project-Specific**

⚠️ **IMPORTANTE**: OpenMemory database è project-specific, NON globale.

**Implicazioni**:
1. Ogni progetto ha il suo database (`.openmemory/`)
2. Non esiste un database globale shared
3. Import manuale necessario per ogni progetto

**Best Practice**:
- Esporta configurazione dalla root del progetto principale
- Importa database nella root del nuovo progetto
- Verifica path con `ls .openmemory/`

---

## ✅ Checklist Post-Import

Dopo l'import, verifica:

- [ ] Claude Desktop riavviato
- [ ] `claude mcp list` mostra tutti server "Connected"
- [ ] `~/.claude/CLAUDE.md` esiste e ha policy corrette
- [ ] `~/.claude/commands/` contiene 3 workflow commands
- [ ] `/resume-session` funziona e mostra Step 5.5 VERIFICATION
- [ ] `/finalize-smart` funziona e salva su OpenMemory + PROGRESS.md + Git
- [ ] `/checkpoint` funziona e salva su OpenMemory
- [ ] OpenMemory database importato (se necessario): `.openmemory/pilotpros-memory.sqlite` esiste
- [ ] `mcp__openmemory__recall_memory_abstract` ritorna abstract corretto

---

## 🎯 Use Cases

### **Use Case 1: Setup Nuovo Mac per Sviluppo**
1. Export configurazione da Mac principale
2. Setup nuovo Mac (install Homebrew, Node, etc.)
3. Install Claude Code CLI
4. Import configurazione
5. **Risultato**: Ambiente identico in 5 minuti

### **Use Case 2: Backup Configurazione Prima di Update**
1. Export configurazione corrente
2. Store archivio in Dropbox/iCloud
3. Esegui system update/upgrade
4. Se problemi → Import da backup
5. **Risultato**: Rollback immediato

### **Use Case 3: Sync Configurazione tra Mac Lavoro/Casa**
1. Export da Mac lavoro (venerdì sera)
2. Import su Mac casa (weekend)
3. Develop su Mac casa
4. Export da Mac casa (domenica)
5. Import su Mac lavoro (lunedì)
6. **Risultato**: Zero friction context switching

### **Use Case 4: Team Onboarding**
1. Senior developer esporta configurazione ottimale
2. Condivide archivio con nuovo developer
3. New developer importa in 2 minuti
4. **Risultato**: Team configuration standardization

---

## 📚 Related Documentation

- **Global CLAUDE.md**: Policy globali tutti i progetti
- **Project CLAUDE.md**: Policy specifiche PilotProOS
- **Workflow Commands**: `~/.claude/commands/*.md`
- **MCP Servers**: https://modelcontextprotocol.io/introduction
- **OpenMemory**: https://github.com/baryhuang/mcp-openmemory

---

## 🆘 Support

**Problemi?**

1. Verifica log Claude Desktop:
   ```bash
   tail -f ~/Library/Logs/Claude/claude.log
   ```

2. Test MCP connection manuale:
   ```bash
   npx @modelcontextprotocol/server-postgres postgresql://...
   ```

3. Verifica OpenMemory database:
   ```bash
   sqlite3 .openmemory/pilotpros-memory.sqlite ".tables"
   ```

**Se tutto fallisce**:
- Restore da backup automatico
- Re-export da Mac sorgente
- Verifica path assoluti in config files

---

**Created**: 2025-10-14
**Version**: 1.0.0
**Tested on**: macOS Sonoma 14.x+
