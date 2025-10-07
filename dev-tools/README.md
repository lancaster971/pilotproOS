# 🔍 PilotProOS Development Tools

**Developer-only utilities for debugging and analyzing agentic workflows**

⚠️ **IMPORTANT**: These tools are **NOT distributed to customers**. Development/debugging only.

---

## 📋 Table of Contents

- [Visual Debugging Tools](#-visual-debugging-tools)
- [Quick Start](#-quick-start)
- [VS Code Integration](#-vs-code-integration)
- [Available Scripts](#-available-scripts)
- [Report Analysis](#-report-analysis)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Visual Debugging Tools

### **Agentic Radar** (splx.ai)

**Purpose**: Scan LangGraph agents and n8n workflows for:
- 🔐 Security vulnerabilities (prompt injection, data leaks)
- 🗺️ Visual workflow mapping (interactive graphs)
- 🛠️ Tool identification and dependencies
- 📊 MCP server detection

**Supported Frameworks**:
- ✅ **LangGraph** (Milhena ReAct Agent)
- ✅ **n8n** (Automation workflows)
- ✅ CrewAI, OpenAI Agents, AutoGen

---

## 🚀 Quick Start

### **1. Scan Milhena Agent (1-click)**

**CLI:**
```bash
./dev-tools/scan-milhena.sh
```

**VS Code:**
1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type: `Tasks: Run Task`
3. Select: `🔍 Visual Debug: Scan Milhena Agent`
4. Report opens automatically in browser

**Output**: `dev-tools/reports/milhena-YYYYMMDD-HHMMSS.html` (interactive graph)

---

### **2. Scan n8n Workflows**

**First**: Export n8n workflows to JSON
1. Open n8n: http://localhost:5678
2. Export workflows → Save to `n8n_workflows_export/`

**Then run:**
```bash
./dev-tools/scan-n8n.sh
# OR with custom path:
./dev-tools/scan-n8n.sh /path/to/workflows
```

---

## 💻 VS Code Integration

### **Available Tasks** (Cmd+Shift+P → Run Task)

| Task | Description | Output |
|------|-------------|--------|
| 🔍 Visual Debug: Scan Milhena Agent | Full security + graph scan | HTML report |
| 🔍 Visual Debug: Scan n8n Workflows | n8n workflow analysis | HTML report |
| 🗂️ Open Latest Milhena Report | Open most recent report | Browser |
| 📊 List All Scan Reports | Show all reports | Terminal |

### **Keyboard Shortcuts** (optional)

Add to `.vscode/keybindings.json`:
```json
[
  {
    "key": "cmd+shift+d",
    "command": "workbench.action.tasks.runTask",
    "args": "🔍 Visual Debug: Scan Milhena Agent"
  }
]
```

---

## 📜 Available Scripts

### **`scan-milhena.sh`**

Scan Milhena ReAct Agent (LangGraph)

**Usage:**
```bash
./dev-tools/scan-milhena.sh
```

**What it scans:**
- `intelligence-engine/app/milhena/graph.py` - Main graph
- `intelligence-engine/app/milhena/business_tools.py` - 12 smart tools
- `intelligence-engine/app/milhena/*.py` - All Milhena components

**Output:**
- Interactive workflow graph (D3.js force-directed)
- Security vulnerability report
- Tool dependency tree
- MCP server detection

---

### **`scan-n8n.sh`**

Scan n8n workflows

**Usage:**
```bash
./dev-tools/scan-n8n.sh [workflow-export-path]
```

**Default path**: `n8n_workflows_export/`

**What it scans:**
- Workflow JSON files
- Webhook endpoints (security risks)
- Credentials usage
- Integration vulnerabilities

---

## 📊 Report Analysis

### **Understanding the HTML Report**

**Sections:**

1. **Workflow Graph** (top)
   - Interactive D3.js visualization
   - Nodes = Agents/Tools
   - Edges = Data flow
   - Colors = Risk level (green/yellow/red)

2. **Vulnerability Summary** (left panel)
   - 🔴 **CRITICAL**: Immediate action required
   - 🟡 **HIGH**: Security risk
   - 🟢 **MEDIUM**: Best practice violation
   - ⚪ **LOW**: Info only

3. **Tool Inventory** (right panel)
   - All detected tools
   - Dependencies
   - MCP servers

4. **Detailed Findings** (bottom)
   - Specific vulnerabilities
   - Code snippets
   - Remediation steps

### **Common Findings (Milhena)**

✅ **Expected** (safe):
- Tool usage in ReAct loop
- LangGraph checkpoint usage
- Redis memory storage

⚠️ **Review Required**:
- Database credentials in tools
- External API calls without validation
- Prompt injection vectors

🔴 **Fix Immediately**:
- Hardcoded secrets
- SQL injection risks
- Unvalidated user input

---

## 🔧 Troubleshooting

### **Error: `agentic-radar: command not found`**

**Solution**: Install manually
```bash
cd intelligence-engine
python3 -m pip install agentic-radar
agentic-radar --version  # Verify
```

---

### **Error: `Report not generated`**

**Causes**:
1. Invalid LangGraph syntax in `graph.py`
2. Missing dependencies
3. Permission issues

**Debug**:
```bash
cd intelligence-engine
agentic-radar scan langgraph -i app/milhena -o /tmp/test.html
# Check output for specific errors
```

---

### **Report doesn't open automatically**

**Manual open**:
```bash
# macOS
open dev-tools/reports/milhena-YYYYMMDD-HHMMSS.html

# Linux
xdg-open dev-tools/reports/milhena-YYYYMMDD-HHMMSS.html

# Windows (Git Bash)
start dev-tools/reports/milhena-YYYYMMDD-HHMMSS.html
```

---

## 🗂️ Directory Structure

```
dev-tools/
├── README.md                 # This file
├── scan-milhena.sh          # Milhena scanner CLI
├── scan-n8n.sh              # n8n scanner CLI
├── reports/                 # Scan output (git-ignored)
│   ├── milhena-*.html       # Milhena reports
│   └── n8n-*.html           # n8n reports
└── scripts/                 # Future utilities
```

---

## 📚 Additional Resources

- **Agentic Radar Docs**: https://docs.probe.splx.ai/
- **GitHub**: https://github.com/splx-ai/agentic-radar
- **LangGraph Security**: https://langchain-ai.github.io/langgraph/security/

---

## ⚙️ Configuration

### **Custom Scan Options**

Edit scripts to add options:

```bash
# scan-milhena.sh
agentic-radar scan langgraph \
    -i app/milhena \
    -o "../${REPORT_PATH}" \
    --include-tests \          # Scan test files
    --verbose                  # Detailed output
```

**Available flags**: Run `agentic-radar scan --help`

---

## 🔒 Security Notes

1. **Reports contain sensitive info**
   - Workflow logic
   - Tool configurations
   - Database queries
   - **→ Do NOT commit to Git** (already in `.gitignore`)

2. **Customer deployment**
   - `dev-tools/` NOT included in production builds
   - Docker images exclude this directory
   - Safe for on-premise installations

---

## 🆘 Support

**Issues with Agentic Radar**:
- GitHub Issues: https://github.com/splx-ai/agentic-radar/issues

**PilotProOS-specific questions**:
- Check CLAUDE.md
- Review Intelligence Engine docs

---

**Last Updated**: 2025-10-06
**Agentic Radar Version**: 0.13.0
**Maintained By**: PilotProOS Development Team
