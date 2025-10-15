#!/bin/bash

# ============================================================================
# EXPORT CLAUDE CODE CONFIGURATION
# ============================================================================
# Esporta TUTTA la configurazione Claude Code per replicarla su altro Mac
#
# Esporta:
# - ~/.claude/mcp_settings.json (MCP servers globali)
# - ~/.claude/CLAUDE.md (policy globali)
# - ~/.claude/commands/ (workflow commands: resume-session, finalize-smart, checkpoint)
# - ~/Library/Application Support/Claude/claude_desktop_config.json (Claude Desktop config)
# - .openmemory/ (database memoria persistente)
# - intelligence-engine/chroma_db/ (ChromaDB vector store)
#
# Output: claude-code-config-YYYYMMDD-HHMMSS.tar.gz
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 CLAUDE CODE CONFIGURATION EXPORT                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Timestamp for backup
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
EXPORT_DIR="claude-code-config-$TIMESTAMP"
ARCHIVE_NAME="$EXPORT_DIR.tar.gz"

# Create temporary export directory
echo -e "${YELLOW}📁 Creating export directory: $EXPORT_DIR${NC}"
mkdir -p "$EXPORT_DIR"

# ============================================================================
# 1. EXPORT MCP SETTINGS (Global)
# ============================================================================
echo ""
echo -e "${BLUE}[1/7] Exporting MCP Settings...${NC}"

if [ -f "$HOME/.claude/mcp_settings.json" ]; then
    mkdir -p "$EXPORT_DIR/.claude"
    cp "$HOME/.claude/mcp_settings.json" "$EXPORT_DIR/.claude/"
    echo -e "${GREEN}  ✓ MCP settings exported${NC}"

    # Show configured servers
    if command -v jq &> /dev/null; then
        SERVER_COUNT=$(jq '.mcpServers | length' "$HOME/.claude/mcp_settings.json")
        echo -e "    ${YELLOW}Servers found: $SERVER_COUNT${NC}"
        jq -r '.mcpServers | keys[]' "$HOME/.claude/mcp_settings.json" | while read server; do
            echo -e "    - $server"
        done
    fi
else
    echo -e "${RED}  ✗ MCP settings not found at ~/.claude/mcp_settings.json${NC}"
fi

# ============================================================================
# 2. EXPORT GLOBAL CLAUDE.MD
# ============================================================================
echo ""
echo -e "${BLUE}[2/7] Exporting Global CLAUDE.md...${NC}"

if [ -f "$HOME/.claude/CLAUDE.md" ]; then
    cp "$HOME/.claude/CLAUDE.md" "$EXPORT_DIR/.claude/"
    LINES=$(wc -l < "$HOME/.claude/CLAUDE.md")
    echo -e "${GREEN}  ✓ CLAUDE.md exported ($LINES lines)${NC}"
else
    echo -e "${RED}  ✗ CLAUDE.md not found at ~/.claude/CLAUDE.md${NC}"
fi

# ============================================================================
# 3. EXPORT WORKFLOW COMMANDS
# ============================================================================
echo ""
echo -e "${BLUE}[3/7] Exporting Workflow Commands...${NC}"

if [ -d "$HOME/.claude/commands" ]; then
    mkdir -p "$EXPORT_DIR/.claude/commands"
    cp -r "$HOME/.claude/commands/"* "$EXPORT_DIR/.claude/commands/" 2>/dev/null || true

    COMMAND_COUNT=$(find "$HOME/.claude/commands" -name "*.md" | wc -l | tr -d ' ')
    echo -e "${GREEN}  ✓ Commands exported: $COMMAND_COUNT${NC}"

    find "$HOME/.claude/commands" -name "*.md" | while read cmd; do
        echo -e "    - $(basename "$cmd" .md)"
    done
else
    echo -e "${YELLOW}  ⚠ No commands directory found${NC}"
fi

# ============================================================================
# 4. EXPORT CLAUDE DESKTOP CONFIG
# ============================================================================
echo ""
echo -e "${BLUE}[4/7] Exporting Claude Desktop Config...${NC}"

CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [ -f "$CLAUDE_DESKTOP_CONFIG" ]; then
    mkdir -p "$EXPORT_DIR/claude-desktop"
    cp "$CLAUDE_DESKTOP_CONFIG" "$EXPORT_DIR/claude-desktop/"
    echo -e "${GREEN}  ✓ Claude Desktop config exported${NC}"

    # Show configured MCP servers
    if command -v jq &> /dev/null; then
        SERVER_COUNT=$(jq '.mcpServers | length' "$CLAUDE_DESKTOP_CONFIG" 2>/dev/null || echo "0")
        echo -e "    ${YELLOW}Desktop MCP Servers: $SERVER_COUNT${NC}"
        jq -r '.mcpServers | keys[]' "$CLAUDE_DESKTOP_CONFIG" 2>/dev/null | while read server; do
            echo -e "    - $server"
        done
    fi
else
    echo -e "${YELLOW}  ⚠ Claude Desktop config not found${NC}"
fi

# ============================================================================
# 5. EXPORT OPENMEMORY DATABASE (if exists)
# ============================================================================
echo ""
echo -e "${BLUE}[5/7] Exporting OpenMemory Database...${NC}"

# Check current directory for .openmemory
if [ -d ".openmemory" ]; then
    mkdir -p "$EXPORT_DIR/openmemory"
    cp -r .openmemory/* "$EXPORT_DIR/openmemory/" 2>/dev/null || true

    if [ -f ".openmemory/pilotpros-memory.sqlite" ]; then
        SIZE=$(du -h ".openmemory/pilotpros-memory.sqlite" | cut -f1)
        echo -e "${GREEN}  ✓ OpenMemory database exported ($SIZE)${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ No .openmemory directory found in current path${NC}"
fi

# ============================================================================
# 6. EXPORT CHROMADB DATABASE (if exists)
# ============================================================================
echo ""
echo -e "${BLUE}[6/7] Exporting ChromaDB Database...${NC}"

# Check for ChromaDB data directory in intelligence-engine
if [ -d "intelligence-engine/chroma_db" ]; then
    mkdir -p "$EXPORT_DIR/chromadb"
    cp -r intelligence-engine/chroma_db/* "$EXPORT_DIR/chromadb/" 2>/dev/null || true

    if [ -f "intelligence-engine/chroma_db/chroma.sqlite3" ]; then
        SIZE=$(du -h "intelligence-engine/chroma_db/chroma.sqlite3" | cut -f1)
        TOTAL_SIZE=$(du -sh "intelligence-engine/chroma_db" | cut -f1)
        echo -e "${GREEN}  ✓ ChromaDB database exported${NC}"
        echo -e "    Database: chroma.sqlite3 ($SIZE)"
        echo -e "    Total size: $TOTAL_SIZE"

        # Count collections
        if command -v sqlite3 &> /dev/null; then
            COLLECTION_COUNT=$(sqlite3 intelligence-engine/chroma_db/chroma.sqlite3 "SELECT COUNT(*) FROM collections;" 2>/dev/null || echo "0")
            echo -e "    Collections: $COLLECTION_COUNT"
        fi
    fi
else
    echo -e "${YELLOW}  ⚠ No ChromaDB data found in intelligence-engine/chroma_db/${NC}"
fi

# ============================================================================
# 7. CREATE IMPORT SCRIPT
# ============================================================================
echo ""
echo -e "${BLUE}[7/7] Creating Import Script...${NC}"

cat > "$EXPORT_DIR/import-config.sh" << 'IMPORT_SCRIPT'
#!/bin/bash

# ============================================================================
# IMPORT CLAUDE CODE CONFIGURATION
# ============================================================================
# Importa configurazione Claude Code esportata da altro Mac
#
# Usage: ./import-config.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 CLAUDE CODE CONFIGURATION IMPORT                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Backup timestamp
BACKUP_TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

echo -e "${YELLOW}⚠️  WARNING: This will overwrite existing Claude Code configuration${NC}"
echo -e "${YELLOW}   Backups will be created with timestamp: $BACKUP_TIMESTAMP${NC}"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Import cancelled${NC}"
    exit 1
fi

# ============================================================================
# 1. IMPORT MCP SETTINGS
# ============================================================================
echo ""
echo -e "${BLUE}[1/6] Importing MCP Settings...${NC}"

if [ -f "$SCRIPT_DIR/.claude/mcp_settings.json" ]; then
    # Backup existing
    if [ -f "$HOME/.claude/mcp_settings.json" ]; then
        cp "$HOME/.claude/mcp_settings.json" "$HOME/.claude/mcp_settings.json.backup-$BACKUP_TIMESTAMP"
        echo -e "${YELLOW}  📦 Backup created: mcp_settings.json.backup-$BACKUP_TIMESTAMP${NC}"
    fi

    # Import
    mkdir -p "$HOME/.claude"
    cp "$SCRIPT_DIR/.claude/mcp_settings.json" "$HOME/.claude/"
    echo -e "${GREEN}  ✓ MCP settings imported${NC}"
else
    echo -e "${YELLOW}  ⚠ No MCP settings to import${NC}"
fi

# ============================================================================
# 2. IMPORT GLOBAL CLAUDE.MD
# ============================================================================
echo ""
echo -e "${BLUE}[2/6] Importing Global CLAUDE.md...${NC}"

if [ -f "$SCRIPT_DIR/.claude/CLAUDE.md" ]; then
    # Backup existing
    if [ -f "$HOME/.claude/CLAUDE.md" ]; then
        cp "$HOME/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md.backup-$BACKUP_TIMESTAMP"
        echo -e "${YELLOW}  📦 Backup created: CLAUDE.md.backup-$BACKUP_TIMESTAMP${NC}"
    fi

    # Import
    cp "$SCRIPT_DIR/.claude/CLAUDE.md" "$HOME/.claude/"
    echo -e "${GREEN}  ✓ CLAUDE.md imported${NC}"
else
    echo -e "${YELLOW}  ⚠ No CLAUDE.md to import${NC}"
fi

# ============================================================================
# 3. IMPORT WORKFLOW COMMANDS
# ============================================================================
echo ""
echo -e "${BLUE}[3/6] Importing Workflow Commands...${NC}"

if [ -d "$SCRIPT_DIR/.claude/commands" ]; then
    # Backup existing
    if [ -d "$HOME/.claude/commands" ]; then
        mv "$HOME/.claude/commands" "$HOME/.claude/commands.backup-$BACKUP_TIMESTAMP"
        echo -e "${YELLOW}  📦 Backup created: commands.backup-$BACKUP_TIMESTAMP${NC}"
    fi

    # Import
    mkdir -p "$HOME/.claude/commands"
    cp -r "$SCRIPT_DIR/.claude/commands/"* "$HOME/.claude/commands/" 2>/dev/null || true

    COMMAND_COUNT=$(find "$HOME/.claude/commands" -name "*.md" | wc -l | tr -d ' ')
    echo -e "${GREEN}  ✓ Commands imported: $COMMAND_COUNT${NC}"
else
    echo -e "${YELLOW}  ⚠ No commands to import${NC}"
fi

# ============================================================================
# 4. IMPORT CLAUDE DESKTOP CONFIG
# ============================================================================
echo ""
echo -e "${BLUE}[4/6] Importing Claude Desktop Config...${NC}"

CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [ -f "$SCRIPT_DIR/claude-desktop/claude_desktop_config.json" ]; then
    # Backup existing
    if [ -f "$CLAUDE_DESKTOP_CONFIG" ]; then
        cp "$CLAUDE_DESKTOP_CONFIG" "$CLAUDE_DESKTOP_CONFIG.backup-$BACKUP_TIMESTAMP"
        echo -e "${YELLOW}  📦 Backup created: claude_desktop_config.json.backup-$BACKUP_TIMESTAMP${NC}"
    fi

    # Import
    mkdir -p "$HOME/Library/Application Support/Claude"
    cp "$SCRIPT_DIR/claude-desktop/claude_desktop_config.json" "$CLAUDE_DESKTOP_CONFIG"
    echo -e "${GREEN}  ✓ Claude Desktop config imported${NC}"
else
    echo -e "${YELLOW}  ⚠ No Claude Desktop config to import${NC}"
fi

# ============================================================================
# 5. IMPORT OPENMEMORY DATABASE
# ============================================================================
echo ""
echo -e "${BLUE}[5/6] Importing OpenMemory Database...${NC}"

if [ -d "$SCRIPT_DIR/openmemory" ]; then
    echo -e "${YELLOW}  ⚠ OpenMemory database found${NC}"
    echo -e "${YELLOW}     Manual import required for project-specific location${NC}"
    echo -e "${YELLOW}     Source: $SCRIPT_DIR/openmemory/${NC}"
    echo ""
    echo -e "  To import manually:"
    echo -e "  ${BLUE}cd /path/to/your/project${NC}"
    echo -e "  ${BLUE}cp -r $SCRIPT_DIR/openmemory .openmemory${NC}"
else
    echo -e "${YELLOW}  ⚠ No OpenMemory database to import${NC}"
fi

# ============================================================================
# 6. IMPORT CHROMADB DATABASE
# ============================================================================
echo ""
echo -e "${BLUE}[6/6] Importing ChromaDB Database...${NC}"

if [ -d "$SCRIPT_DIR/chromadb" ]; then
    echo -e "${YELLOW}  ⚠ ChromaDB database found${NC}"
    echo -e "${YELLOW}     Manual import required for project-specific location${NC}"
    echo -e "${YELLOW}     Source: $SCRIPT_DIR/chromadb/${NC}"
    echo ""
    echo -e "  To import manually:"
    echo -e "  ${BLUE}cd /path/to/your/project${NC}"
    echo -e "  ${BLUE}mkdir -p intelligence-engine/chroma_db${NC}"
    echo -e "  ${BLUE}cp -r $SCRIPT_DIR/chromadb/* intelligence-engine/chroma_db/${NC}"
    echo ""

    # Show database info
    if [ -f "$SCRIPT_DIR/chromadb/chroma.sqlite3" ]; then
        SIZE=$(du -h "$SCRIPT_DIR/chromadb/chroma.sqlite3" | cut -f1)
        echo -e "  Database size: $SIZE"

        if command -v sqlite3 &> /dev/null; then
            COLLECTION_COUNT=$(sqlite3 "$SCRIPT_DIR/chromadb/chroma.sqlite3" "SELECT COUNT(*) FROM collections;" 2>/dev/null || echo "0")
            echo -e "  Collections: $COLLECTION_COUNT"
        fi
    fi
else
    echo -e "${YELLOW}  ⚠ No ChromaDB database to import${NC}"
fi

# ============================================================================
# FINAL STEPS
# ============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ IMPORT COMPLETE                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
echo ""
echo -e "1. ${BLUE}Restart Claude Desktop app${NC}"
echo -e "   - Quit Claude Desktop completely"
echo -e "   - Reopen to load new MCP servers"
echo ""
echo -e "2. ${BLUE}Verify MCP servers in Claude Code${NC}"
echo -e "   - Type: ${GREEN}claude mcp list${NC}"
echo -e "   - Check all servers are 'Connected'"
echo ""
echo -e "3. ${BLUE}Test workflow commands${NC}"
echo -e "   - ${GREEN}/resume-session${NC} - Start new session"
echo -e "   - ${GREEN}/checkpoint${NC} - Quick savepoint"
echo -e "   - ${GREEN}/finalize-smart${NC} - Close session"
echo ""
echo -e "4. ${BLUE}Import OpenMemory database (if needed)${NC}"
echo -e "   - Navigate to project directory"
echo -e "   - Copy: ${GREEN}cp -r $SCRIPT_DIR/openmemory .openmemory${NC}"
echo ""
echo -e "5. ${BLUE}Import ChromaDB database (if needed)${NC}"
echo -e "   - Navigate to project directory"
echo -e "   - Copy: ${GREEN}cp -r $SCRIPT_DIR/chromadb/* intelligence-engine/chroma_db/${NC}"
echo ""
echo -e "${GREEN}🎉 Your Claude Code configuration is now identical!${NC}"
echo ""

IMPORT_SCRIPT

chmod +x "$EXPORT_DIR/import-config.sh"
echo -e "${GREEN}  ✓ Import script created${NC}"

# ============================================================================
# CREATE ARCHIVE
# ============================================================================
echo ""
echo -e "${BLUE}📦 Creating Archive...${NC}"

tar -czf "$ARCHIVE_NAME" "$EXPORT_DIR"
echo -e "${GREEN}  ✓ Archive created: $ARCHIVE_NAME${NC}"

# Calculate size
SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
echo -e "    Size: $SIZE"

# Cleanup temporary directory
rm -rf "$EXPORT_DIR"

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ EXPORT COMPLETE                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📦 Archive Created:${NC} $ARCHIVE_NAME ($SIZE)"
echo ""
echo -e "${YELLOW}📋 TO IMPORT ON NEW MAC:${NC}"
echo ""
echo -e "1. ${BLUE}Transfer archive to new Mac${NC}"
echo -e "   - Via AirDrop, USB, or Dropbox"
echo ""
echo -e "2. ${BLUE}Extract and run import${NC}"
echo -e "   ${GREEN}tar -xzf $ARCHIVE_NAME${NC}"
echo -e "   ${GREEN}cd $EXPORT_DIR${NC}"
echo -e "   ${GREEN}./import-config.sh${NC}"
echo ""
echo -e "3. ${BLUE}Restart Claude Desktop${NC}"
echo ""
echo -e "${GREEN}🎉 Done! Your configuration will be replicated.${NC}"
echo ""
