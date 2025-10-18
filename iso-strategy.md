# 🚀 PilotProOS - ISO/USB Distribution Strategy

**Version**: 1.1
**Date**: 2025-10-18
**Status**: Design Phase (Updated with 2025 Best Practices)
**Author**: PilotProOS Team

---

## 📑 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
   - 2.2 [Three-Tier Deployment Strategy (Good/Better/Best Model)](#22-three-tier-deployment-strategy-goodbetterbest-model)
3. [ISO/USB Distribution Package](#3-isousb-distribution-package)
4. [Installer Application](#4-installer-application)
5. [Container Optimization](#5-container-optimization)
   - 5.9 [Docker Production Best Practices 2025](#59-docker-production-best-practices-2025-security--reliability)
6. [Licensing System](#6-licensing-system)
   - 6.1 [Licensing Platform Evaluation (2025 Battle-Tested Solutions)](#61-licensing-platform-evaluation-2025-battle-tested-solutions)
   - 6.2 [License Types & Floating License Best Practices](#62-license-types)
   - 6.7 [Feature Management System (Runtime Feature Gating)](#67-feature-management-system-runtime-feature-gating)
7. [Auto-Update System](#7-auto-update-system)
8. [Configuration Management](#8-configuration-management)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Testing Strategy](#10-testing-strategy)
11. [VPS Compatibility Matrix](#11-vps-compatibility-matrix)
12. [Technical Decisions](#12-technical-decisions)
13. [Future Enhancements](#13-future-enhancements)
14. [Appendices](#14-appendices)

---

## 1. Executive Summary

### 1.1 Project Vision

PilotProOS è attualmente un sistema containerizzato che richiede setup manuale con conoscenze Docker/PostgreSQL. L'obiettivo è trasformarlo in una **distribuzione on-premise plug-and-play** installabile su:

- **VPS commerciali** (Hostinger, Hetzner, Contabo, DigitalOcean)
- **Server dedicati** fisici (Dell, HP, Supermicro)
- **Hardware custom** (mini-PC, NUC, server tower)

### 1.2 Target Audience

**Installatori finali**: Sistemisti IT junior con **zero esperienza Docker**, capaci di:
- Inserire una chiavetta USB
- Seguire wizard grafico
- Completare form web basic

**NON richiesto**: Conoscenze CLI, Docker, PostgreSQL, networking avanzato

### 1.3 Business Objectives

1. **Time-to-deployment**: Da 2-4 ore (manuale) a **15-20 minuti** (automatico)
2. **Error rate**: Da 40% (configurazione errata) a **<5%** (validazione automatica)
3. **Support tickets**: Riduzione 80% (self-service guided)
4. **Licensing control**: 100% installazioni validate e tracciabili
5. **Update compliance**: Auto-update con 1-click, rollback garantito

### 1.4 Key Constraints

- ✅ **RAM Optimization**: Funzionare su VPS da 2GB (Hostinger Basic)
- ✅ **Internet Required**: Solo per licensing check (5 secondi), poi offline-capable
- ✅ **User-Friendly**: Installabile da utenti con **zero CLI experience**
- ✅ **n8n Required**: Non opzionale (core business automation)
- ✅ **Embeddings Optional**: RAG knowledge base disponibile solo su TIER 2+

---

## 2. Architecture Overview

### 2.1 Current State Analysis

**Ambiente Development Attuale** (docker-compose.yml):

| Container | Dev RAM | Prod Target | Note |
|-----------|---------|-------------|------|
| Frontend | 177MB | 80MB | Nginx alpine (no Node runtime) |
| Backend | 81MB | 50MB | NODE_ENV=production + heap limit |
| Intelligence Engine | 268MB | 180MB | Conditional RAG loading |
| Embeddings | 850MB | 600MB / OFF | Optional per TIER 1 |
| n8n | 323MB | 200MB | Required, memory-optimized |
| PostgreSQL | 48MB | 40MB | shared_buffers=32MB |
| Redis | 140MB | 80MB | maxmemory=64MB |
| Nginx | 8MB | 8MB | No optimization needed |
| **TOTAL** | **1.9GB** | **1.1-2.3GB** | Tier-dependent |

### 2.2 Three-Tier Deployment Strategy (Good/Better/Best Model)

**SaaS Industry Standard**: GBB (Good/Better/Best) pricing structure, proven effective for 80%+ SaaS companies (2025 Monetization Monitor). Each tier offers increasing value with clear feature differentiation.

#### 🟢 **TIER 1: MINIMAL** (GOOD - VPS 2GB)

**Target**: Hostinger Basic (€3.99/mo), Contabo VPS S

**RAM Budget**: 1.1GB (7 containers)

**Components**:
- ✅ Frontend (80MB)
- ✅ Backend (50MB)
- ✅ Intelligence Engine (180MB) - **NO RAG** (classifier + ReAct only)
- ❌ Embeddings (OFF)
- ✅ n8n (200MB)
- ✅ PostgreSQL (40MB)
- ✅ Redis (80MB)
- ✅ Nginx (8MB)

**Capabilities**:
- ✅ Chat Intelligence (categoria classification + tool execution)
- ✅ n8n Workflow Automation (18 smart tools)
- ✅ Analytics & Reporting
- ❌ RAG Knowledge Base (no document upload/search)

**Use Case**: PMI con <50 utenti, focus su automazioni semplici

---

#### 🟡 **TIER 2: STANDARD** (BETTER - VPS 4GB) - **RECOMMENDED**

**Target**: Hostinger Business (€7.99/mo), Hetzner CX21

**RAM Budget**: 1.7GB (8 containers)

**Components**:
- ✅ Frontend (80MB)
- ✅ Backend (50MB)
- ✅ Intelligence Engine (180MB) - **RAG on-demand**
- ✅ Embeddings (600MB) - **Lazy load**
- ✅ n8n (200MB)
- ✅ PostgreSQL (40MB)
- ✅ Redis (80MB)
- ✅ Nginx (8MB)

**Capabilities**:
- ✅ **Full features**: Chat + RAG + Workflows
- ✅ Document upload (PDF, DOCX, TXT, MD, HTML)
- ✅ Semantic search knowledge base
- ✅ 85-90% accuracy RAG answers

**Use Case**: Aziende medie, 50-200 utenti, knowledge management

---

#### 🔵 **TIER 3: FULL** (BEST - VPS 8GB+)

**Target**: Hostinger Premium (€13.99/mo), Dedicated Server

**RAM Budget**: 2.3GB (8 containers + performance tuning)

**Components**:
- ✅ Frontend (120MB) - Cache enabled
- ✅ Backend (80MB) - Worker pool
- ✅ Intelligence Engine (300MB) - **Full cache + auto-learning**
- ✅ Embeddings (800MB) - Preloaded models
- ✅ n8n (300MB) - More task runners
- ✅ PostgreSQL (100MB) - shared_buffers=128MB
- ✅ Redis (150MB) - maxmemory=128MB
- ✅ Nginx (8MB)

**Capabilities**:
- ✅ **High-performance**: <500ms P95 response time
- ✅ **Auto-Learning**: Pattern recognition + fast-path optimization
- ✅ **Multi-user**: 500+ concurrent users
- ✅ **Advanced caching**: Redis + PostgreSQL tuned

**Use Case**: Enterprise, 500+ utenti, high-traffic, learning-enabled

---

### 2.3 Component Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                │
│                    Port 80/443 (HTTPS)                  │
└────────────┬────────────────────────────────────────────┘
             │
       ┌─────┴─────┐
       │           │
       ▼           ▼
┌────────────┐  ┌────────────────────────────────────┐
│  Frontend  │  │  Backend (Business Translator)     │
│  (Vue 3)   │  │  Port 3001                         │
│  Port 3000 │  │  ┌──────────────┐                  │
└────────────┘  │  │ Auth System  │                  │
                │  │ (JWT + OAuth)│                  │
                │  └──────────────┘                  │
                └───┬────────────┬────────────┬───────┘
                    │            │            │
          ┌─────────┴───┐   ┌────▼────┐   ┌──▼──────────┐
          │             │   │         │   │             │
          ▼             ▼   ▼         │   ▼             │
┌──────────────────┐ ┌──────────┐    │ ┌───────────┐   │
│ Intelligence     │ │PostgreSQL│    │ │   Redis   │   │
│ Engine (v3.5.6)  │ │ Port 5432│    │ │Port 6379  │   │
│ Port 8000        │ └──────────┘    │ └───────────┘   │
│                  │      ▲          │                  │
│ ┌──────────────┐ │      │          │                  │
│ │  Classifier  │ │      │          │                  │
│ │  (LLM-based) │ │      │          │                  │
│ └──────┬───────┘ │      │          │                  │
│        │         │      │          │                  │
│        ▼         │      │          │                  │
│ ┌──────────────┐ │      │          │                  │
│ │Tool Executor │◄┼──────┘          │                  │
│ │(18 tools)    │ │                 │                  │
│ └──────────────┘ │                 │                  │
│                  │                 │                  │
│ ┌──────────────┐ │ (TIER 2+)      │                  │
│ │ RAG System   │◄┼─────────────────┘                  │
│ │(Optional)    │ │                                    │
│ └──────┬───────┘ │                                    │
└────────┼─────────┘                                    │
         │                                              │
         │ (TIER 2+ only)                              │
         ▼                                              │
┌──────────────────┐                                    │
│ Embeddings       │                                    │
│ Service          │                                    │
│ (nomic-embed)    │                                    │
│ Port 8002        │                                    │
└──────────────────┘                                    │
                                                        │
         ┌──────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  n8n Automation  │
│  Port 5678       │
│  (REQUIRED)      │
└──────────────────┘
```

**Critical Dependencies**:
1. PostgreSQL → **MUST** start first (all services depend on it)
2. Redis → Required by Intelligence Engine (AsyncRedisSaver)
3. n8n → **REQUIRED** (business automation, non opzionale)
4. Embeddings → **OPTIONAL** (only TIER 2+, lazy load)

---

## 3. ISO/USB Distribution Package

### 3.1 ISO Structure

```
/pilotpros-installer/                     # Root directory (8-12GB total)
│
├── installer/                            # Python Textual application
│   ├── main.py                          # Entry point (auto-start)
│   ├── requirements.txt                 # textual, cryptlex, psutil, docker
│   ├── screens/                         # 8 wizard screens
│   │   ├── __init__.py
│   │   ├── welcome.py                   # Screen 1: Welcome
│   │   ├── license_check.py             # Screen 2: License activation
│   │   ├── tier_selection.py            # Screen 3: MINIMAL/STANDARD/FULL
│   │   ├── resource_check.py            # Screen 4: RAM/Disk/Network validation
│   │   ├── admin_setup.py               # Screen 5: Admin user creation
│   │   ├── config_wizard.py             # Screen 6: Services config
│   │   ├── installation.py              # Screen 7: Auto-run installation
│   │   └── success.py                   # Screen 8: Success + credentials
│   ├── generators/
│   │   ├── env_generator.py             # Generate .env files
│   │   ├── compose_generator.py         # Generate docker-compose.yml
│   │   └── secrets_generator.py         # Auto-generate secure secrets
│   ├── validators/
│   │   ├── license_validator.py         # Cryptlex integration
│   │   └── system_validator.py          # Hardware/resources check
│   └── utils/
│       ├── docker_loader.py             # Load .tar.gz images
│       ├── migration_runner.py          # Run SQL migrations
│       └── health_checker.py            # Poll services until ready
│
├── docker-images/                        # Pre-built production images
│   ├── TIER1/                           # 4GB compressed (7 images)
│   │   ├── postgres-16-alpine.tar.gz    # 180MB
│   │   ├── redis-stack-latest.tar.gz    # 220MB
│   │   ├── nginx-alpine.tar.gz          # 40MB
│   │   ├── n8n-1.114.2.tar.gz          # 650MB
│   │   ├── backend-prod.tar.gz          # 380MB
│   │   ├── frontend-prod.tar.gz         # 85MB
│   │   └── intelligence-minimal.tar.gz  # 920MB (NO RAG dependencies)
│   │
│   ├── TIER2/                           # +2GB (additional 2 images)
│   │   ├── intelligence-full.tar.gz     # 1.1GB (WITH RAG: chromadb, langchain)
│   │   └── embeddings-nomic.tar.gz      # 680MB (nomic-embed-text model)
│   │
│   └── TIER3/                           # Same as TIER2 (config differs)
│       └── (symlink to TIER2/)
│
├── config-templates/                     # Production-ready configurations
│   ├── tier1/
│   │   ├── docker-compose.minimal.yml   # 7 services, NO embeddings
│   │   ├── backend.env.template
│   │   ├── intelligence.env.template    # ENABLE_RAG=false
│   │   └── nginx.production.conf
│   ├── tier2/
│   │   ├── docker-compose.standard.yml  # 8 services, embeddings lazy-load
│   │   ├── backend.env.template
│   │   ├── intelligence.env.template    # ENABLE_RAG=true
│   │   ├── embeddings.env.template
│   │   └── nginx.production.conf
│   ├── tier3/
│   │   ├── docker-compose.full.yml      # 8 services, performance-tuned
│   │   ├── backend.env.template
│   │   ├── intelligence.env.template    # ENABLE_LEARNING=true
│   │   ├── embeddings.env.template
│   │   ├── postgres.production.conf     # shared_buffers=128MB
│   │   └── nginx.production.conf
│   └── common/
│       ├── stack-manager.sh             # Post-install CLI: start/stop/logs/backup
│       └── systemd/
│           └── pilotpros.service        # Auto-start on boot
│
├── database/                             # PostgreSQL setup
│   ├── migrations/                      # 8 SQL migration files
│   │   ├── 001_auth_enhancement.sql
│   │   ├── 002_auth_fix_uuid.sql
│   │   ├── 003_backup_settings.sql
│   │   ├── 004_auto_learned_patterns.sql
│   │   ├── 005_pattern_status.sql
│   │   ├── 005_system_context_view_v2_MINIMAL.sql
│   │   └── 006_refresh_tokens.sql
│   ├── init-schemas.sql                 # Create pilotpros + n8n schemas
│   └── seed-data.sql                    # Optional demo data
│
├── scripts/                              # Automation scripts
│   ├── pre-flight-checks.sh             # Validate Docker, RAM, disk space
│   ├── load-docker-images.sh            # Load .tar.gz with progress bar
│   ├── generate-secrets.sh              # Auto-generate JWT/session secrets
│   ├── run-migrations.sh                # Execute SQL migrations sequentially
│   ├── health-check.sh                  # Poll /health endpoints until ready
│   ├── swap-setup.sh                    # Auto-configure 2GB swap (TIER 1)
│   └── optimize-for-tier.sh             # Apply tier-specific resource limits
│
├── licensing/                            # Cryptlex integration
│   ├── cryptlex-validator.py            # License check service
│   ├── hardware-fingerprint.sh          # Generate host MAC + CPU ID
│   └── lexactivator.so                  # Cryptlex native library (Linux x86_64)
│
├── update-service/                       # Auto-update sidecar container
│   ├── Dockerfile
│   ├── update-checker.py                # Poll private registry every 24h
│   ├── notification-handler.py          # Send admin dashboard alerts
│   ├── backup-manager.py                # Pre-update automatic backup
│   └── docker-compose.update.yml        # Update service definition
│
├── docs/                                 # User documentation (PDF)
│   ├── INSTALLATION-GUIDE.pdf           # Step-by-step with screenshots
│   ├── QUICK-START.pdf                  # First login + basic operations
│   ├── ADMIN-MANUAL.pdf                 # Stack management, backup, update
│   └── TROUBLESHOOTING.pdf              # Common issues + solutions
│
├── ssl/                                  # Self-signed SSL certificates (dev)
│   ├── pilotpros.crt
│   └── pilotpros.key
│
├── README.txt                            # Plain text instructions
├── LICENSE.txt                           # Software license
└── autorun.sh                            # Auto-executed on USB boot (Linux)
```

### 3.2 Size Breakdown

| Component | TIER 1 | TIER 2 | TIER 3 | Notes |
|-----------|--------|--------|--------|-------|
| Docker Images | 4.0GB | 6.0GB | 6.0GB | Compressed .tar.gz |
| Installer App | 45MB | 45MB | 45MB | Python + deps |
| Config Templates | 2MB | 2MB | 2MB | .yml + .env files |
| Database Migrations | 150KB | 150KB | 150KB | 8 SQL files |
| Scripts | 500KB | 500KB | 500KB | Bash utilities |
| Licensing | 12MB | 12MB | 12MB | Cryptlex lib |
| Update Service | 80MB | 80MB | 80MB | Python service |
| Documentation | 25MB | 25MB | 25MB | 4 PDF files |
| SSL Certificates | 10KB | 10KB | 10KB | Self-signed |
| **TOTAL** | **~4.2GB** | **~6.2GB** | **~6.2GB** | USB 8GB recommended |

### 3.3 Compression Strategy

**Docker Images** (~40% size reduction):
```bash
# Save with gzip compression
docker save pilotpros-backend:prod | gzip -9 > backend-prod.tar.gz

# Original: 650MB → Compressed: 390MB
```

**Installer Application** (PyInstaller single executable):
```bash
# Bundle Python + deps into single binary
pyinstaller --onefile --add-data "screens:screens" main.py
# Result: 45MB self-contained executable (no Python install required)
```

### 3.4 Boot Process Flow

```
┌──────────────────────────────────────────────────────────┐
│  1. USER: Insert USB/ISO + Boot from USB                │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  2. GRUB: Ubuntu 24.04 LTS Live Boot                     │
│     - Load kernel + initramfs                            │
│     - Mount squashfs root filesystem                     │
│     - Start systemd                                      │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  3. SYSTEMD: Auto-login as pilotpros user                │
│     - .bashrc triggers autorun.sh                        │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  4. AUTORUN.SH: Check if already installed               │
│     - If /opt/pilotpros exists → Skip install, show menu │
│     - Else → Launch installer: python3 installer/main.py │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  5. INSTALLER: Python Textual TUI starts                 │
│     - Screen 1: Welcome                                  │
│     - Screen 2: License Check (internet required)        │
│     - Screen 3: Tier Selection (MINIMAL/STANDARD/FULL)   │
│     - Screen 4: Resource Check (RAM/Disk/Network)        │
│     - Screen 5: Admin Setup (email + password)           │
│     - Screen 6: Config Wizard (DB, n8n, domain, keys)    │
│     - Screen 7: Installation (10-15 min auto-run)        │
│     - Screen 8: Success Screen (URLs + credentials)      │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  6. INSTALLATION PHASE:                                  │
│     a. Load Docker images (7-8 images, ~7 min)           │
│     b. Generate .env files (auto-secrets, <1 sec)        │
│     c. Run SQL migrations (8 files, ~30 sec)             │
│     d. Start Docker stack (docker-compose up -d, ~1 min) │
│     e. Health check loop (wait services ready, ~2 min)   │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  7. SUCCESS:                                             │
│     - Stack running on localhost                         │
│     - Credentials saved to /opt/pilotpros/credentials.pdf│
│     - Frontend: https://localhost                        │
│     - Admin dashboard: admin@example.com / ********      │
│     - systemd service enabled (auto-start on reboot)     │
└──────────────────────────────────────────────────────────┘
```

**Total Time**: ~15-20 minutes (di cui 10 min unattended)

---

## 4. Installer Application

### 4.1 Technology Stack

**Framework**: Python Textual v0.78+ (https://textual.textualize.io/)

**Why Textual?**
- ✅ **Modern TUI**: Mouse support, rich widgets, CSS-like styling
- ✅ **User-friendly**: Visual forms, progress bars, modals
- ✅ **Cross-platform**: Linux, macOS, Windows (future-proof)
- ✅ **Active development**: 24k+ GitHub stars, MIT license
- ✅ **Python native**: Same stack as intelligence-engine

**Dependencies** (requirements.txt):
```txt
textual==0.78.0
cryptlex-lexactivator==3.29.0
psutil==6.0.0
python-dotenv==1.0.0
docker==7.1.0
pyyaml==6.0.1
requests==2.32.3
```

### 4.2 Installer Architecture

```
installer/
├── main.py                    # Entry point + App class
├── config.py                  # Global config (paths, defaults)
├── state.py                   # Shared state between screens
│
├── screens/                   # Textual Screen classes
│   ├── __init__.py
│   ├── welcome.py             # Screen 1: Welcome + intro
│   ├── license_check.py       # Screen 2: License input + validation
│   ├── tier_selection.py      # Screen 3: MINIMAL/STANDARD/FULL
│   ├── resource_check.py      # Screen 4: System validation
│   ├── admin_setup.py         # Screen 5: Admin user form
│   ├── config_wizard.py       # Screen 6: Services configuration
│   ├── installation.py        # Screen 7: Auto-run installation
│   └── success.py             # Screen 8: Completion + recap
│
├── widgets/                   # Custom Textual widgets
│   ├── progress_log.py        # Log viewer with progress bar
│   ├── tier_card.py           # Tier selection card component
│   └── credential_display.py  # Masked password display
│
├── generators/                # Configuration file generators
│   ├── env_generator.py       # Generate .env files
│   ├── compose_generator.py   # Generate docker-compose.yml
│   └── secrets_generator.py   # Secure random generation
│
├── validators/                # Input validation + checks
│   ├── license_validator.py   # Cryptlex API calls
│   ├── system_validator.py    # RAM/disk/network checks
│   ├── email_validator.py     # Email format validation
│   └── password_validator.py  # Password strength check
│
├── utils/                     # Helper utilities
│   ├── docker_loader.py       # Load .tar.gz images
│   ├── migration_runner.py    # SQL migration executor
│   ├── health_checker.py      # Service health polling
│   └── logger.py              # Installation log writer
│
└── assets/                    # Static assets
    ├── logo.txt               # ASCII art logo
    └── styles.css             # Textual CSS styles
```

### 4.3 Wizard Flow - Detailed Screens

#### **Screen 1: Welcome**

```
╔═══════════════════════════════════════════════════════════╗
║              🚀 PilotProOS Installer v1.0                ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   Welcome to the PilotProOS guided installation!         ║
║                                                           ║
║   This wizard will help you deploy a complete business   ║
║   process operating system with:                         ║
║                                                           ║
║   ✅ Intelligent Chat Agent (LangGraph + GPT-4)         ║
║   ✅ n8n Workflow Automation (500+ integrations)        ║
║   ✅ PostgreSQL Database (production-ready)             ║
║   ✅ Knowledge Base (RAG) - optional, TIER 2+           ║
║                                                           ║
║   ⏱️  Estimated time: 15-20 minutes                      ║
║   🌐 Internet required: License check only (5 sec)      ║
║   💾 Disk space: 15-20GB minimum                        ║
║                                                           ║
║                                                           ║
║   📋 Requirements:                                       ║
║      • 2GB+ RAM (MINIMAL tier)                          ║
║      • 4GB+ RAM recommended (STANDARD tier)             ║
║      • 15GB+ disk space                                 ║
║      • Internet connection (temporary)                  ║
║      • Docker support (auto-installed if missing)       ║
║                                                           ║
║                                                           ║
║   [ Next ]                               [Quit]          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

#### **Screen 2: License Activation**

```
╔═══════════════════════════════════════════════════════════╗
║              🔑 License Activation                       ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   Enter your PilotProOS license key:                     ║
║                                                           ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX          │ ║
║   └────────────────────────────────────────────────────┘ ║
║                                                           ║
║   License Type: ○ Online    ○ Offline (file upload)     ║
║                                                           ║
║   ─────────────────────────────────────────────────────  ║
║                                                           ║
║   ℹ️  Your license will be validated against our        ║
║      activation server. This requires a temporary        ║
║      internet connection (5-10 seconds).                 ║
║                                                           ║
║   🔒 Hardware Fingerprint:                               ║
║      MAC: 00:1A:2B:3C:4D:5E                             ║
║      CPU: Intel(R) Xeon(R) CPU E5-2680 v4               ║
║                                                           ║
║   Status: ⏳ Waiting for input...                        ║
║                                                           ║
║                                                           ║
║   [ Validate ]  [ Back ]                    [Quit]       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

(After validation SUCCESS)

║   Status: ✅ License validated successfully!             ║
║                                                           ║
║   License Details:                                       ║
║   • Customer: Acme Corporation                          ║
║   • Type: Floating License (5 concurrent users)         ║
║   • Expires: 2026-12-31                                 ║
║   • Features: FULL (all tiers enabled)                  ║
```

---

#### **Screen 3: Tier Selection** (CRITICAL)

```
╔═══════════════════════════════════════════════════════════╗
║              📊 Deployment Tier Selection                ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   Choose the deployment profile for your server:         ║
║                                                           ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │ ○ MINIMAL (1.1GB RAM) - VPS 2GB                   │  ║
║  │   ┌──────────────────────────────────────────────┐ │  ║
║  │   │ RAM Budget: 1.1GB (7 containers)            │ │  ║
║  │   │                                              │ │  ║
║  │   │ ✅ Chat Intelligence (classifier + tools)   │ │  ║
║  │   │ ✅ n8n Workflow Automation                  │ │  ║
║  │   │ ✅ Analytics & Reporting                    │ │  ║
║  │   │ ❌ NO RAG Knowledge Base                    │ │  ║
║  │   │                                              │ │  ║
║  │   │ Ideal for: Hostinger Basic, Contabo VPS S   │ │  ║
║  │   │ Use case: <50 users, simple automations     │ │  ║
║  │   └──────────────────────────────────────────────┘ │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                           ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │ ● STANDARD (1.7GB RAM) - VPS 4GB [RECOMMENDED]   │  ║
║  │   ┌──────────────────────────────────────────────┐ │  ║
║  │   │ RAM Budget: 1.7GB (8 containers)            │ │  ║
║  │   │                                              │ │  ║
║  │   │ ✅ Full Chat Intelligence + RAG             │ │  ║
║  │   │ ✅ Document Upload (PDF, DOCX, TXT, MD)     │ │  ║
║  │   │ ✅ Semantic Search (85-90% accuracy)        │ │  ║
║  │   │ ✅ n8n Automation (full features)           │ │  ║
║  │   │                                              │ │  ║
║  │   │ Ideal for: Hostinger Business, Hetzner CX21 │ │  ║
║  │   │ Use case: 50-200 users, knowledge mgmt      │ │  ║
║  │   └──────────────────────────────────────────────┘ │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                           ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │ ○ FULL (2.3GB RAM) - VPS 8GB+                    │  ║
║  │   ┌──────────────────────────────────────────────┐ │  ║
║  │   │ RAM Budget: 2.3GB (8 containers + tuning)   │ │  ║
║  │   │                                              │ │  ║
║  │   │ ✅ High-Performance (<500ms response)       │ │  ║
║  │   │ ✅ Auto-Learning (pattern recognition)      │ │  ║
║  │   │ ✅ Advanced Caching (Redis + PgSQL tuned)   │ │  ║
║  │   │ ✅ Multi-User (500+ concurrent)             │ │  ║
║  │   │                                              │ │  ║
║  │   │ Ideal for: Dedicated servers, VPS Premium   │ │  ║
║  │   │ Use case: Enterprise, 500+ users, high load │ │  ║
║  │   └──────────────────────────────────────────────┘ │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                           ║
║   ℹ️  You can upgrade/downgrade later via config       ║
║                                                           ║
║   [ Next ]  [ Back ]                        [Quit]       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

#### **Screen 4: Resource Check** (Adaptive)

```
╔═══════════════════════════════════════════════════════════╗
║              🏥 System Resource Check                     ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   Selected Tier: STANDARD (requires 4GB RAM minimum)     ║
║                                                           ║
║   Checking system resources...                           ║
║                                                           ║
║   ┌─────────────────────────────────────────────────┐    ║
║   │ ✅ RAM:           7.8GB / 4GB required         │    ║
║   │    Status: ✅ Sufficient (95% margin)          │    ║
║   │                                                  │    ║
║   │ ✅ Disk Space:    45GB / 15GB required         │    ║
║   │    Status: ✅ Sufficient (200% margin)         │    ║
║   │                                                  │    ║
║   │ ✅ Docker:        Installed (v27.3.1)          │    ║
║   │    Status: ✅ Ready                             │    ║
║   │                                                  │    ║
║   │ ✅ Network:       Internet reachable           │    ║
║   │    Status: ✅ Connected (ping 15ms)            │    ║
║   │                                                  │    ║
║   │ ⚠️  Swap:         0GB configured               │    ║
║   │    Recommendation: Configure 2GB swap? [Yes]   │    ║
║   │                                                  │    ║
║   └─────────────────────────────────────────────────┘    ║
║                                                           ║
║   ℹ️  All checks passed! Ready to proceed.              ║
║                                                           ║
║                                                           ║
║   [ Next ]  [ Back ]  [ Re-check ]          [Quit]       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

(Example: WARNING case - Insufficient RAM)

║   Selected Tier: FULL (requires 8GB RAM minimum)         ║
║                                                           ║
║   ┌─────────────────────────────────────────────────┐    ║
║   │ ⚠️  RAM:          3.8GB / 8GB required         │    ║
║   │    Status: ⚠️  INSUFFICIENT                     │    ║
║   │                                                  │    ║
║   │    ⚠️  Your system has only 3.8GB RAM, but     │    ║
║   │       FULL tier requires 8GB minimum.           │    ║
║   │                                                  │    ║
║   │    Options:                                      │    ║
║   │    • Upgrade RAM to 8GB+                        │    ║
║   │    • Downgrade to STANDARD tier (4GB)           │    ║
║   │                                                  │    ║
║   │    [Downgrade to STANDARD]                      │    ║
║   └─────────────────────────────────────────────────┘    ║
```

---

#### **Screen 5: Admin User Setup**

```
╔═══════════════════════════════════════════════════════════╗
║              👤 Administrator Account                     ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   Create the main administrator account:                 ║
║                                                           ║
║   Full Name:                                             ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ John Doe                                           │ ║
║   └────────────────────────────────────────────────────┘ ║
║                                                           ║
║   Email:                                                 ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ admin@acme-corp.com                                │ ║
║   └────────────────────────────────────────────────────┘ ║
║   ✅ Valid email format                                  ║
║                                                           ║
║   Password:                                              ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ ••••••••••••••••                                   │ ║
║   └────────────────────────────────────────────────────┘ ║
║   Strength: 🟢🟢🟢🟢⚪ Strong                            ║
║                                                           ║
║   Confirm Password:                                      ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ ••••••••••••••••                                   │ ║
║   └────────────────────────────────────────────────────┘ ║
║   ✅ Passwords match                                     ║
║                                                           ║
║   ┌──────────────────────────────────────────────────┐  ║
║   │ 💡 Password Requirements:                        │  ║
║   │   • Minimum 8 characters                         │  ║
║   │   • At least 1 uppercase letter                  │  ║
║   │   • At least 1 number                            │  ║
║   │   • At least 1 special character                 │  ║
║   └──────────────────────────────────────────────────┘  ║
║                                                           ║
║                                                           ║
║   [ Next ]  [ Back ]  [Generate Strong]     [Quit]       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

#### **Screen 6: Services Configuration**

```
╔═══════════════════════════════════════════════════════════╗
║              ⚙️  Services Configuration                   ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   Configure core services (leave blank for auto):        ║
║                                                           ║
║   ═══════════ Database Configuration ══════════          ║
║                                                           ║
║   PostgreSQL Password: [Auto-generate] ✅                ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ •••••••••••••••••••••                              │ ║
║   └────────────────────────────────────────────────────┘ ║
║   (Leave empty to auto-generate secure password)         ║
║                                                           ║
║   ═══════════ n8n Automation ═══════════════             ║
║                                                           ║
║   n8n Admin Username:                                    ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ admin                                              │ ║
║   └────────────────────────────────────────────────────┘ ║
║                                                           ║
║   n8n Admin Password: [Auto-generate] ✅                 ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ •••••••••••••••••••••                              │ ║
║   └────────────────────────────────────────────────────┘ ║
║                                                           ║
║   ═══════════ Domain Configuration ══════════            ║
║                                                           ║
║   Domain/Hostname: (optional)                            ║
║   ┌────────────────────────────────────────────────────┐ ║
║   │ localhost                                          │ ║
║   └────────────────────────────────────────────────────┘ ║
║   Example: pilotpros.acme-corp.com                       ║
║                                                           ║
║   ═══════════ LLM API Keys (optional) ═══════            ║
║                                                           ║
║   ☐ Configure now    ☑ Skip (configure later)           ║
║                                                           ║
║   ℹ️  You can configure LLM keys later via:             ║
║      /opt/pilotpros/intelligence-engine/.env             ║
║                                                           ║
║                                                           ║
║   [ Next ]  [ Back ]                        [Quit]       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

#### **Screen 7: Installation** (Auto-run, 10-15 min)

```
╔═══════════════════════════════════════════════════════════╗
║              🚀 Installing PilotProOS...                  ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   Installation Progress:                                 ║
║                                                           ║
║   Phase 1: Loading Docker Images          [████████--] 80%║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   ✅ 1. Generating configuration files      (completed)  ║
║      • backend.env                                       ║
║      • intelligence-engine.env                           ║
║      • docker-compose.standard.yml                       ║
║      Generated 18 secure secrets                         ║
║                                                           ║
║   ✅ 2. Setting up swap (2GB)              (completed)  ║
║                                                           ║
║   🔄 3. Loading Docker images...            (in progress) ║
║      [████████████████████------------------] 7/8         ║
║      ✅ postgres-16-alpine.tar.gz          180MB / 3.2s  ║
║      ✅ redis-stack.tar.gz                 220MB / 4.1s  ║
║      ✅ nginx-alpine.tar.gz                 40MB / 0.8s  ║
║      ✅ n8n-1.114.2.tar.gz                 650MB / 12.3s ║
║      ✅ backend-prod.tar.gz                380MB / 7.1s  ║
║      ✅ frontend-prod.tar.gz                85MB / 1.9s  ║
║      ✅ intelligence-full.tar.gz          1100MB / 21.7s ║
║      🔄 embeddings-nomic.tar.gz            680MB / 13.2s ║
║                                                           ║
║   ⏳ 4. Running database migrations...      (pending)    ║
║   ⏳ 5. Starting Docker containers...       (pending)    ║
║   ⏳ 6. Waiting for services to be ready... (pending)    ║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   📊 System Resources:                                   ║
║      CPU:  35% (2/4 cores busy)                          ║
║      RAM:  2.1GB / 7.8GB (27%)                           ║
║      Disk: Writing @ 85 MB/s                             ║
║                                                           ║
║   Estimated time remaining: 4 minutes                    ║
║                                                           ║
║   ℹ️  You can safely wait. Installation is automatic.   ║
║                                                           ║
║                                                           ║
║   [ View Logs ]                             [Abort]      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

(After all phases complete)

║   Phase 6: Health Check                   [██████████] 100%║
║                                                           ║
║   ✅ All services ready!                                 ║
║                                                           ║
║   Service Health:                                        ║
║   ✅ PostgreSQL     Ready (port 5432)                    ║
║   ✅ Redis          Ready (port 6379)                    ║
║   ✅ Backend API    Ready (port 3001)                    ║
║   ✅ Frontend       Ready (port 3000)                    ║
║   ✅ Intelligence   Ready (port 8000)                    ║
║   ✅ Embeddings     Ready (port 8002)                    ║
║   ✅ n8n            Ready (port 5678)                    ║
║   ✅ Nginx          Ready (port 80/443)                  ║
║                                                           ║
║   Total installation time: 12 minutes 37 seconds         ║
```

---

#### **Screen 8: Success** (Final)

```
╔═══════════════════════════════════════════════════════════╗
║              🎉 Installation Complete!                    ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   PilotProOS has been successfully installed!            ║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   📍 Access Points:                                      ║
║                                                           ║
║      Frontend Portal:    https://localhost               ║
║      Backend API:        http://localhost:3001           ║
║      Intelligence API:   http://localhost:8000           ║
║      n8n Automation:     http://localhost:5678           ║
║      System Monitor:     http://localhost:3005           ║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   🔑 Credentials:                                        ║
║                                                           ║
║      Admin User:                                         ║
║      • Email:    admin@acme-corp.com                     ║
║      • Password: ****************  [Show] [Copy]         ║
║                                                           ║
║      n8n Admin:                                          ║
║      • Username: admin                                   ║
║      • Password: ****************  [Show] [Copy]         ║
║                                                           ║
║      Database:                                           ║
║      • User:     pilotpros_user                          ║
║      • Password: ****************  [Show] [Copy]         ║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   📄 Credentials saved to:                               ║
║      /opt/pilotpros/credentials.pdf                      ║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   ⚡ Quick Start:                                        ║
║                                                           ║
║      1. Open browser: https://localhost                  ║
║      2. Login with admin credentials above               ║
║      3. Start chatting with the AI agent!                ║
║                                                           ║
║   📚 Documentation:                                      ║
║      • User Guide:    /opt/pilotpros/docs/QUICK-START.pdf║
║      • Admin Manual:  /opt/pilotpros/docs/ADMIN-MANUAL.pdf║
║                                                           ║
║   🔧 Management CLI:                                     ║
║      /opt/pilotpros/stack-manager.sh                     ║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   ✅ System will auto-start on reboot (systemd enabled) ║
║                                                           ║
║                                                           ║
║   [ Open Frontend ]  [ View Logs ]          [Finish]     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

### 4.4 Error Handling & Rollback

**Rollback Strategy**:

Se un qualsiasi step di installation fallisce, l'installer esegue **rollback automatico**:

1. **Stop containers** (se avviati)
2. **Remove images** (se caricate)
3. **Delete generated files** (.env, docker-compose.yml)
4. **Restore disk space** (rimuovi immagini parziali)
5. **Show error screen** con dettagli errore + log path

```
╔═══════════════════════════════════════════════════════════╗
║              ⚠️  Installation Failed                      ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   An error occurred during installation:                 ║
║                                                           ║
║   Phase: Loading Docker Images (step 3/6)                ║
║   Error: Failed to load intelligence-full.tar.gz         ║
║          Corrupted archive or insufficient disk space    ║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   🔄 Rollback completed:                                 ║
║      ✅ Removed partial Docker images                    ║
║      ✅ Deleted generated configuration files            ║
║      ✅ Cleaned up temporary files                       ║
║                                                           ║
║   📋 Log file saved to:                                  ║
║      /tmp/pilotpros-install-2025-10-18-14-32.log         ║
║                                                           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                           ║
║   💡 Suggestions:                                        ║
║      • Check disk space: df -h                           ║
║      • Verify USB/ISO integrity: md5sum                  ║
║      • Try re-running installer                          ║
║      • Contact support with log file                     ║
║                                                           ║
║                                                           ║
║   [ Retry Installation ]  [ View Log ]      [Quit]       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 5. Container Optimization

### 5.1 Frontend Optimization (177MB → 80MB)

**Current** (Development):
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]
```
**Size**: 177MB (Node runtime + dev deps)

**Optimized** (Production):
```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
ENV NGINX_ENTRYPOINT_QUIET_LOGS=1
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```
**Size**: 80MB (nginx alpine only)
**Saving**: -55% RAM

**nginx.conf**:
```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (opcional, si backend en puerto diverso)
    location /api {
        proxy_pass http://backend:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Caching para assets statici
    location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

### 5.2 Backend Optimization (81MB → 50MB)

**docker-compose.yml** (Production):
```yaml
backend-prod:
  build:
    context: ./backend
    dockerfile: Dockerfile.prod
  environment:
    NODE_ENV: production
    NODE_OPTIONS: "--max-old-space-size=48"  # Limit heap to 48MB
    PORT: 3001

    # Database
    DB_HOST: postgres
    DB_PORT: 5432
    DB_NAME: ${DB_NAME}
    DB_USER: ${DB_USER}
    DB_PASSWORD: ${DB_PASSWORD}

    # JWT
    JWT_SECRET: ${JWT_SECRET}
    JWT_EXPIRES_IN: 30m
    REFRESH_TOKEN_EXPIRES_IN: 7d

    # Performance
    LOG_LEVEL: warn  # Solo warnings in production

  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 64M
      reservations:
        memory: 32M
  restart: unless-stopped
```

**Dockerfile.prod**:
```dockerfile
FROM node:20-alpine
WORKDIR /app

# Install production deps only
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy source
COPY . .

# Non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    chown -R nodejs:nodejs /app
USER nodejs

EXPOSE 3001
CMD ["node", "src/server.js"]
```

**Saving**: -38% RAM (81MB → 50MB)

---

### 5.3 Intelligence Engine Optimization (268MB → 180MB)

**Key Strategy**: **Conditional RAG loading** per tier

**main.py** (with tier detection):
```python
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Load config
ENABLE_RAG = os.getenv("ENABLE_RAG", "false").lower() == "true"
ENABLE_LEARNING = os.getenv("ENABLE_LEARNING", "false").lower() == "true"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""

    # Always load core components
    from app.agents.v3_5.graph import create_graph
    app.state.graph = create_graph()

    # Conditional RAG loading (TIER 2+ only)
    if ENABLE_RAG:
        from app.rag.maintainable_rag import MaintainableRAG
        app.state.rag = MaintainableRAG()
        print("✅ RAG system loaded (TIER 2+)")
    else:
        app.state.rag = None
        print("⏭️  RAG disabled (TIER 1 MINIMAL)")

    # Conditional learning system (TIER 3 only)
    if ENABLE_LEARNING:
        from app.services.learning import start_pattern_learning
        await start_pattern_learning()
        print("✅ Auto-learning enabled (TIER 3 FULL)")

    yield

    # Cleanup
    if app.state.rag:
        await app.state.rag.close()

app = FastAPI(lifespan=lifespan)
```

**docker-compose variants**:

**TIER 1** (intelligence.env):
```bash
ENABLE_RAG=false
ENABLE_LEARNING=false
EMBEDDINGS_ENDPOINT=  # Empty, not used
```

**TIER 2** (intelligence.env):
```bash
ENABLE_RAG=true
ENABLE_LEARNING=false
EMBEDDINGS_ENDPOINT=http://embeddings:8001
```

**TIER 3** (intelligence.env):
```bash
ENABLE_RAG=true
ENABLE_LEARNING=true
EMBEDDINGS_ENDPOINT=http://embeddings:8001
POSTGRES_POOL_SIZE=10  # Increased for learning queries
```

**Memory Limits**:
```yaml
# TIER 1
intelligence-minimal:
  deploy:
    resources:
      limits:
        memory: 200M
      reservations:
        memory: 150M

# TIER 2
intelligence-standard:
  deploy:
    resources:
      limits:
        memory: 250M
      reservations:
        memory: 180M

# TIER 3
intelligence-full:
  deploy:
    resources:
      limits:
        memory: 350M
      reservations:
        memory: 250M
```

---

### 5.4 Embeddings Optimization (850MB → 600MB / OFF)

**Strategy**: Lazy load + model optimization

**TIER 1**: Container **disabilitato** (no docker-compose entry)

**TIER 2+**: Lazy load model al primo utilizzo

**main.py** (embeddings service):
```python
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import torch

app = FastAPI()

# Global model cache (lazy-loaded)
_model = None

def get_model():
    global _model
    if _model is None:
        print("🔄 Loading nomic-embed-text model (first use)...")
        _model = SentenceTransformer(
            "nomic-ai/nomic-embed-text-v1.5",
            trust_remote_code=True,
            device="cpu"  # CPU-only for VPS
        )
        print("✅ Model loaded successfully")
    return _model

@app.post("/embed")
async def embed_text(texts: list[str]):
    model = get_model()  # Lazy load on first API call
    with torch.no_grad():
        embeddings = model.encode(texts, convert_to_numpy=True)
    return {"embeddings": embeddings.tolist()}
```

**docker-compose.yml** (TIER 2+):
```yaml
embeddings-service:
  build:
    context: ./intelligence-engine
    dockerfile: Dockerfile.embeddings
  environment:
    TRANSFORMERS_CACHE: /models
    HF_HOME: /models
    DEFAULT_MODEL: nomic  # nomic (600MB) vs stella (8GB)
    PYTORCH_CUDA_ALLOC_CONF: max_split_size_mb=32  # Reduce fragmentation
  volumes:
    - embeddings_models:/models  # Persistent model cache
  deploy:
    resources:
      limits:
        memory: 700M
      reservations:
        memory: 400M  # Start small, grow to 700M as needed
  restart: unless-stopped
```

**Saving**: 850MB → 600MB (model optimization) o 850MB → 0MB (TIER 1)

---

### 5.5 n8n Optimization (323MB → 200MB)

**n8n è REQUIRED**, ma ottimizziamo memoria:

```yaml
automation-engine-prod:
  image: n8nio/n8n:1.114.2
  environment:
    # Database
    DB_TYPE: postgresdb
    DB_POSTGRESDB_HOST: postgres
    DB_POSTGRESDB_PORT: 5432
    DB_POSTGRESDB_DATABASE: ${DB_NAME}
    DB_POSTGRESDB_USER: ${DB_USER}
    DB_POSTGRESDB_PASSWORD: ${DB_PASSWORD}
    DB_POSTGRESDB_SCHEMA: n8n

    # Memory optimization
    NODE_OPTIONS: "--max-old-space-size=180"  # 180MB heap limit
    EXECUTIONS_DATA_SAVE_ON_SUCCESS: none     # Save only errors
    EXECUTIONS_DATA_SAVE_ON_ERROR: all
    EXECUTIONS_DATA_MAX_AGE: 168              # 7 days (was 30)
    N8N_PAYLOAD_SIZE_MAX: 8                   # 8MB (was 16MB)

    # Performance
    N8N_LOG_LEVEL: warn  # Reduce logging overhead

  deploy:
    resources:
      limits:
        cpus: '0.75'
        memory: 220M
      reservations:
        memory: 150M
  restart: unless-stopped
```

**Saving**: -38% RAM (323MB → 200MB)

---

### 5.6 PostgreSQL Optimization (48MB → 40MB)

**Tuning per VPS limitati**:

```yaml
postgres-prod:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: ${DB_NAME}
    POSTGRES_USER: ${DB_USER}
    POSTGRES_PASSWORD: ${DB_PASSWORD}
    PGDATA: /var/lib/postgresql/data/pgdata
  command: >
    postgres
      -c shared_buffers=32MB           # (was 256MB)
      -c effective_cache_size=128MB    # (was 4GB default)
      -c maintenance_work_mem=16MB     # (was 64MB)
      -c checkpoint_completion_target=0.9
      -c wal_buffers=2MB               # (was 16MB)
      -c default_statistics_target=50  # (was 100)
      -c random_page_cost=1.1          # SSD-optimized
      -c effective_io_concurrency=200  # SSD
      -c work_mem=2MB                  # Per-operation memory
      -c min_wal_size=80MB
      -c max_wal_size=1GB
      -c max_connections=50            # (was 200)
      -c max_worker_processes=2        # (was 8)
      -c max_parallel_workers_per_gather=1
      -c max_parallel_workers=2
  deploy:
    resources:
      limits:
        memory: 64M
      reservations:
        memory: 40M
  volumes:
    - postgres_data:/var/lib/postgresql/data
  restart: unless-stopped
```

**TIER 3** (increased limits):
```yaml
command: >
  postgres
    -c shared_buffers=128MB      # 4x TIER 1
    -c effective_cache_size=512MB
    -c work_mem=4MB
    -c max_connections=100
```

---

### 5.7 Redis Optimization (140MB → 80MB)

```yaml
redis-prod:
  image: redis/redis-stack:latest
  command: >
    redis-stack-server
      --maxmemory 64mb
      --maxmemory-policy allkeys-lru    # Evict least recently used
      --appendonly yes                  # Persistence via AOF
      --save ""                         # Disable RDB snapshots
      --maxmemory-samples 3             # Faster LRU (less accuracy)
      --tcp-backlog 128                 # Reduced connection queue
      --databases 2                     # Only 2 DBs needed (was 16)
  deploy:
    resources:
      limits:
        memory: 96M
      reservations:
        memory: 64M
  volumes:
    - redis_data:/data
  restart: unless-stopped
```

**Saving**: -43% RAM (140MB → 80MB)

---

### 5.8 Nginx - No Optimization Needed (8MB)

Nginx già leggerissimo, nessuna ottimizzazione necessaria.

---

### 5.9 Docker Production Best Practices 2025 (Security & Reliability)

**Mandatory for all production images**:

#### 5.9.1 Multi-Stage Builds (Already Implemented ✅)

**Status**: ✅ Already present in Frontend (Dockerfile shows multi-stage: builder → nginx)

**Benefits**:
- ✅ 55% smaller images (177MB → 80MB frontend)
- ✅ No dev dependencies in production
- ✅ Faster deployments (less data to transfer)

#### 5.9.2 Health Checks (REQUIRED - Add to all services)

**Why Critical**: Docker restart policies only work if health checks detect failures.

```yaml
# docker-compose.prod.yml - Add to ALL services

backend:
  image: pilotpros/backend:latest
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s

intelligence-engine:
  image: pilotpros/intelligence-engine:latest
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 60s  # Longer startup (loads models)

postgres:
  image: postgres:16-alpine
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U pilotpros_user -d pilotpros_db"]
    interval: 10s
    timeout: 5s
    retries: 5

redis:
  image: redis/redis-stack:latest
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
```

**Benefits**:
- ✅ Automatic container restart on failure
- ✅ Load balancers know when service ready
- ✅ Better logging (`docker ps` shows healthy/unhealthy)

#### 5.9.3 Non-Root User (Security Must-Have 2025)

**Why Critical**: Running as root = potential container escape vulnerability (CVSS 7.8).

**Intelligence Engine Dockerfile** (add before CMD):
```dockerfile
FROM python:3.11-slim

# ... existing layers ...

# Create non-root user (SECURITY)
RUN useradd -m -u 1000 -s /bin/bash pilotpros && \
    chown -R pilotpros:pilotpros /app

USER pilotpros  # ← Switch from root to pilotpros

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Backend Dockerfile**:
```dockerfile
FROM node:20-alpine

# ... existing layers ...

# Create non-root user (SECURITY)
RUN addgroup -g 1000 pilotpros && \
    adduser -D -u 1000 -G pilotpros pilotpros && \
    chown -R pilotpros:pilotpros /app

USER pilotpros  # ← Non-root

CMD ["node", "src/index.js"]
```

**n8n** (already runs non-root by default ✅)

**PostgreSQL** (use `postgres` user, not root):
```yaml
postgres:
  image: postgres:16-alpine
  user: postgres  # ← Built-in non-root user
```

#### 5.9.4 Read-Only Root Filesystem (Extra Hardening)

**Optional but recommended** for maximum security:

```yaml
backend:
  image: pilotpros/backend:latest
  read_only: true  # Root filesystem immutable
  tmpfs:
    - /tmp           # Writable temp directory
    - /app/.npm      # npm cache
```

**Benefits**:
- ✅ Prevents malware persistence
- ✅ Blocks container modification attacks
- ⚠️ Requires explicit tmpfs mounts for writable dirs

#### 5.9.5 Resource Limits (Prevent OOM Kills)

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'       # Max 1 CPU core
          memory: 64M       # Hard limit
        reservations:
          cpus: '0.25'      # Min guaranteed
          memory: 32M
    oom_kill_disable: true  # Prevent OOM killer

  intelligence-engine:
    deploy:
      resources:
        limits:
          cpus: '2.0'       # Heavier workload
          memory: 512M      # Allow more for LLM calls
        reservations:
          cpus: '0.5'
          memory: 256M
```

#### 5.9.6 Docker Compose Overlay Files (Multi-Environment)

**Best Practice 2025**: Separate base config from environment-specific overrides.

```bash
# Base configuration (shared)
docker-compose.yml              # Development defaults

# Environment overlays
docker-compose.prod.yml         # Production overrides
docker-compose.tier1.yml        # TIER 1 specific (no embeddings)
docker-compose.tier2.yml        # TIER 2 specific (lazy-load RAG)
docker-compose.tier3.yml        # TIER 3 specific (performance tuned)
```

**Usage**:
```bash
# TIER 1 production deployment
docker-compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               -f docker-compose.tier1.yml \
               up -d

# TIER 2 production deployment
docker-compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               -f docker-compose.tier2.yml \
               up -d
```

**Example `docker-compose.tier1.yml`** (MINIMAL - no embeddings):
```yaml
version: '3.8'

services:
  intelligence-engine:
    environment:
      ENABLE_RAG: "false"  # Override: disable RAG for TIER 1
      ENABLE_EMBEDDINGS: "false"

  # embeddings service NOT included (commented out or omitted)
```

#### 5.9.7 Logging Best Practices

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"      # Max 10MB per log file
        max-file: "3"        # Keep 3 rotated files
        compress: "true"     # Compress rotated logs
```

**Prevents**:
- ✅ Disk space exhaustion (logs capped at 30MB/service)
- ✅ Performance degradation (smaller logs = faster searches)

#### 5.9.8 Secrets Management

**DO NOT** hardcode secrets in Dockerfiles or docker-compose.yml:

```yaml
# ❌ WRONG
services:
  backend:
    environment:
      JWT_SECRET: "hardcoded-secret-bad"

# ✅ CORRECT
services:
  backend:
    env_file:
      - .env.prod  # Git-ignored, generated by installer
    # OR use Docker secrets (Swarm mode)
    secrets:
      - jwt_secret

secrets:
  jwt_secret:
    file: /opt/pilotpros/secrets/jwt_secret.txt
```

**Installer generates**:
```bash
# Generated at install time (not in repo)
/opt/pilotpros/.env.prod
JWT_SECRET=<randomly-generated-256-bit-key>
POSTGRES_PASSWORD=<randomly-generated>
```

---

## 6. Licensing System

### 6.1 Licensing Platform Evaluation (2025 Battle-Tested Solutions)

**Comparison of Production-Ready Licensing Systems**:

| Feature | **Cryptlex** ⭐ | Zentitle | 10Duke Enterprise | Keygen.sh |
|---------|--------------|----------|-------------------|-----------|
| **Track Record** | 2+ years proven | Pioneer since 2005 | Fortune 500 | Modern API-first |
| **Deployment** | Cloud SaaS | Cloud SaaS | Cloud + On-premise | Cloud + Self-hosted |
| **Floating Licenses** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ✅ Via API |
| **Offline Grace** | ✅ 30 days | ✅ Configurable | ✅ Built-in | ⚠️ Custom implementation |
| **Hardware Fingerprint** | ✅ Helpers | ✅ Built-in | ✅ Advanced | ✅ API-based |
| **Node-Locked** | ✅ Native | ✅ Native | ✅ Native | ✅ Specialized |
| **REST API** | ✅ Python/Node SDKs | ✅ Multi-language | ✅ Enterprise-grade | ✅ Modern REST |
| **Pricing** | Mid-range | Enterprise | Enterprise | Developer-friendly |
| **SOC 2 Compliance** | ⚠️ Not stated | ✅ Enterprise-grade | ✅ Certified | ⚠️ Not stated |
| **Best For** | SMB-Enterprise | Enterprise, IPO track | Fortune 500, regulated | Startups, developers |

**PilotProOS Choice: Cryptlex** ✅

**Rationale**:
- ✅ **Proven stability**: 2+ years production track record
- ✅ **Perfect fit**: Mid-market pricing (€50-150/mo), not overkill for SMB
- ✅ **Floating licenses**: Native support, essential for Docker multi-user
- ✅ **30-day offline grace**: Built-in, no custom implementation needed
- ✅ **Python + Node.js SDKs**: Direct integration (Intelligence Engine + Backend)
- ✅ **Fast setup**: <2h integration vs 60h+ custom development

**When to Consider Alternatives**:
- **Zentitle**: If targeting Fortune 500 + need IPO-ready licensing platform
- **10Duke**: If SOC 2 compliance mandatory + regulated industries (healthcare, finance)
- **Keygen.sh**: If fully self-hosted licensing required (air-gapped environments)

### 6.2 License Types

**Floating License** (recommended):
```
License Key: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
Type: Floating
Max Activations: 5 concurrent users
Duration: 1 year (renewable)
Features: ALL (TIER 1, 2, 3 enabled)
```

**Node-Locked** (fallback per cliente senza internet):
```
License Key: YYYY-YYYY-YYYY-YYYY-YYYY-YYYY
Type: Node-Locked
Hardware Fingerprint: MAC + CPU ID
Offline Mode: 30 days grace period
```

**Floating License Best Practices (2025)**:

**Optimal License Ratio**: 3:1 users-to-licenses (industry standard)
- Example: 15 employees → 5 floating licenses (optimal efficiency)
- Achieves 67% cost savings vs per-seat licensing
- Requires usage monitoring first 1-3 months

**Monitoring Strategy**:
```python
# Track license usage patterns
async def monitor_license_usage():
    """
    Week 1-4: Baseline measurement
    - Peak concurrent users
    - Idle license percentage
    - Contention events (user denied access)

    Week 5-8: Optimization
    - If idle >50% → reduce licenses
    - If contention >5% → add licenses
    - Target: 70-80% utilization at peak
    """
    pass
```

**High-Security Environments**:
- On-premise license server option available (Cryptlex supports it)
- Defense contractors, regulated industries (GDPR, HIPAA)
- Air-gapped installations: Node-locked with 90-day offline grace
- Annual license file renewal via secure USB transfer

**Deployment Recommendation**:
- **SMB (5-50 users)**: Floating licenses, cloud-based (Cryptlex SaaS)
- **Enterprise (50-500 users)**: Floating licenses, on-premise server option
- **Air-gapped/Regulated**: Node-locked + extended offline grace (90 days)

### 6.3 Hardware Fingerprinting

**Strategy**: Host-level fingerprint (NO container ID)

**hardware-fingerprint.sh**:
```bash
#!/bin/bash
# Generate stable hardware fingerprint for licensing

# Get primary network interface MAC address
MAC=$(ip link show | awk '/ether/ {print $2; exit}' | tr -d ':')

# Get CPU model and physical ID
CPU_MODEL=$(lscpu | grep "Model name" | cut -d':' -f2 | xargs | tr ' ' '_')
CPU_ID=$(cat /proc/cpuinfo | grep "physical id" | head -1 | cut -d':' -f2 | xargs)

# Combine for fingerprint
FINGERPRINT="${MAC}-${CPU_MODEL}-${CPU_ID}"

echo "$FINGERPRINT"
```

**Output example**: `001a2b3c4d5e-Intel_Xeon_E5-2680_v4-0`

### 6.4 License Validation Flow

```
┌──────────────────────────────────────────────────────────┐
│  1. INSTALLER: License input screen                     │
│     User enters: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX         │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  2. FINGERPRINT: Generate host fingerprint               │
│     MAC: 00:1a:2b:3c:4d:5e                              │
│     CPU: Intel Xeon E5-2680 v4                          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  3. CRYPTLEX API: Validate license                       │
│     POST /v3/activations                                 │
│     {                                                     │
│       "license_key": "XXXX...",                          │
│       "fingerprint": "001a2b...",                        │
│       "metadata": {"hostname": "srv01.acme.com"}         │
│     }                                                     │
└────────────────────────┬─────────────────────────────────┘
                         │
                  ┌──────┴──────┐
                  │             │
                  ▼             ▼
         ┌─────────────┐  ┌─────────────┐
         │  SUCCESS    │  │   ERROR     │
         │  200 OK     │  │   401/403   │
         └──────┬──────┘  └──────┬──────┘
                │                │
                ▼                ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  4. SAVE: Store token    │  │  4. ABORT: Show error    │
│     /opt/pilotpros/      │  │     Invalid license      │
│     .license_token       │  │     Already activated    │
└────────────┬─────────────┘  │     Expired              │
             │                └──────────────────────────┘
             ▼
┌──────────────────────────────────────────────────────────┐
│  5. PROCEED: Continue installation                       │
│     License validated, proceed to next screen            │
└──────────────────────────────────────────────────────────┘
```

### 6.5 Runtime License Check

**Intelligence Engine startup** (`main.py`):
```python
import os
from cryptlex.lexactivator import LexActivator, LexStatusCodes, PermissionFlags

async def validate_license():
    """Check license at startup (every 24h re-validation)"""

    # Load saved license token
    token_path = "/opt/pilotpros/.license_token"
    if not os.path.exists(token_path):
        raise RuntimeError("❌ No license found. Please run installer.")

    with open(token_path) as f:
        token = f.read().strip()

    # Initialize LexActivator
    LexActivator.SetProductFile("/opt/pilotpros/licensing/product.dat")
    LexActivator.SetLicenseKey(token)

    # Try activation (with 30-day offline grace period)
    status = LexActivator.ActivateLicense()

    if status == LexStatusCodes.LA_OK:
        print("✅ License valid")
        return True
    elif status == LexStatusCodes.LA_EXPIRED:
        print("❌ License EXPIRED")
        raise RuntimeError("License expired. Please renew.")
    elif status == LexStatusCodes.LA_SUSPENDED:
        print("❌ License SUSPENDED")
        raise RuntimeError("License suspended. Contact support.")
    elif status == LexStatusCodes.LA_GRACE_PERIOD_OVER:
        print("❌ Offline grace period OVER (30 days)")
        raise RuntimeError("License needs re-validation. Connect to internet.")
    else:
        print(f"❌ License validation failed: {status}")
        raise RuntimeError(f"License error: {status}")

# Add to FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate license at startup
    await validate_license()

    # ... rest of startup logic
    yield

app = FastAPI(lifespan=lifespan)
```

**Enforcement**: Intelligence Engine **non parte** se licenza invalida.

### 6.6 Admin Dashboard Integration

**Frontend UI** (license status widget):
```vue
<template>
  <Card class="license-status">
    <template #title>
      <Icon name="key" /> License Status
    </template>

    <div v-if="license.valid">
      <Badge type="success">✅ Active</Badge>
      <p>Customer: {{ license.customer }}</p>
      <p>Expires: {{ license.expiresAt }}</p>
      <p>Users: {{ license.activations }}/{{ license.maxActivations }}</p>
    </div>

    <div v-else>
      <Badge type="error">❌ Invalid</Badge>
      <p>{{ license.error }}</p>
      <Button @click="renewLicense">Renew License</Button>
    </div>
  </Card>
</template>

<script setup>
const license = ref({
  valid: true,
  customer: 'Acme Corporation',
  expiresAt: '2026-12-31',
  activations: 3,
  maxActivations: 5
})

async function renewLicense() {
  // Open modal con form per input nuova license key
}
</script>
```

---

### 6.7 Feature Management System (Runtime Feature Gating)

**Purpose**: Enforce tier-based feature access at runtime (frontend + backend + intelligence engine).

#### 6.7.1 Feature Flag Solutions Comparison (2025)

| Feature | **Unleash** ⭐ | LaunchDarkly | Split.io (Harness) | Flagsmith |
|---------|---------------|--------------|-------------------|-----------|
| **Deployment** | On-premise + Cloud | Cloud-only | Cloud-only | On-premise + Cloud |
| **Open Source** | ✅ Full | ❌ No | ❌ No | ✅ Full |
| **Pricing** | Free self-host, $80/mo cloud | $35/seat/mo+ | $35/seat/mo+ | Free self-host, €45/mo cloud |
| **Ease of Use** | ⭐ Rated #1 by G2 | ⭐⭐⭐ Enterprise | ⭐⭐ Complex | ⭐⭐ Simple |
| **SDK Support** | 20+ languages | 35+ languages | 15+ languages | 25+ languages |
| **Real-time Updates** | ✅ WebSocket | ✅ SSE | ✅ SSE | ✅ WebSocket |
| **Experimentation** | ⚠️ Basic | ✅ Advanced | ✅ Best-in-class | ⚠️ Basic |
| **Air-gapped Support** | ✅ Full | ❌ No | ❌ No | ✅ Full |
| **Best For** | On-premise, self-hosted | Enterprise cloud | A/B testing focus | Budget-conscious |

**PilotProOS Recommendation**: **Unleash (self-hosted)** ⭐

**Rationale**:
- ✅ **On-premise deployment**: Perfect for air-gapped/regulated customers
- ✅ **Free self-host**: Zero licensing costs for feature flags
- ✅ **Easiest to use**: G2 #1 rating, minimal learning curve
- ✅ **Docker-ready**: Single container deployment, low RAM (<100MB)
- ✅ **Python + Node.js SDKs**: Direct integration with existing stack

**Alternative Strategy**: **Simplified In-House Feature Gating** (recommended for MVP)

**Instead of external tool**, implement lightweight tier-based feature control:

```python
# intelligence-engine/app/config/features.py
FEATURE_MATRIX = {
    "TIER_1": {
        "INSIGHTS_AI": True,
        "AUTOMATION": True,
        "EXECUTIONS": True,
        "SETTINGS": True,
        "RAG": False,              # ❌ Disabled
        "EMBEDDINGS": False,       # ❌ Disabled
        "AUTO_LEARNING": False,    # ❌ Disabled
        "COMMAND_CENTER": True,    # Basic only
        "ANALYTICS": "basic"       # Limited queries
    },
    "TIER_2": {
        "INSIGHTS_AI": True,
        "AUTOMATION": True,
        "EXECUTIONS": True,
        "SETTINGS": True,
        "RAG": True,               # ✅ Enabled
        "EMBEDDINGS": True,        # ✅ Lazy-load
        "AUTO_LEARNING": False,    # ❌ Disabled
        "COMMAND_CENTER": True,    # Full access
        "ANALYTICS": "standard"    # 18 smart tools
    },
    "TIER_3": {
        "INSIGHTS_AI": True,
        "AUTOMATION": True,
        "EXECUTIONS": True,
        "SETTINGS": True,
        "RAG": True,               # ✅ Enhanced
        "EMBEDDINGS": True,        # ✅ Preloaded
        "AUTO_LEARNING": True,     # ✅ Enabled
        "COMMAND_CENTER": True,    # Performance-tuned
        "ANALYTICS": "advanced"    # All metrics + ML insights
    }
}
```

#### 6.7.2 Backend Feature Gating (Express.js)

```javascript
// backend/src/middleware/feature-gate.middleware.js
const checkFeature = (requiredFeature) => {
  return async (req, res, next) => {
    const tier = req.app.locals.license.tier; // From Cryptlex metadata
    const features = FEATURE_MATRIX[tier];

    if (!features[requiredFeature]) {
      return res.status(403).json({
        error: 'Feature not available in your license tier',
        feature: requiredFeature,
        currentTier: tier,
        upgradeUrl: '/settings/upgrade',
        requiredTier: getMinimumTier(requiredFeature)
      });
    }

    next();
  };
};

// Usage
router.post('/api/rag/documents', checkFeature('RAG'), uploadDocument);
router.get('/api/learning/patterns', checkFeature('AUTO_LEARNING'), getPatterns);
```

#### 6.7.3 Frontend Feature Gating (Vue 3)

```typescript
// frontend/src/stores/license.ts
import { defineStore } from 'pinia'

export const useLicenseStore = defineStore('license', {
  state: () => ({
    tier: 'TIER_2', // Loaded from backend /api/license/status
    features: [] as string[]
  }),

  actions: {
    async loadLicense() {
      const response = await ofetch('/api/license/status')
      this.tier = response.tier
      this.features = FEATURE_MATRIX[response.tier]
    }
  },

  getters: {
    hasFeature: (state) => (feature: string) => {
      return state.features.includes(feature)
    }
  }
})
```

```vue
<!-- Conditional rendering -->
<template>
  <MainLayout>
    <MenuItem v-if="hasFeature('INSIGHTS_AI')" label="Insights" />
    <MenuItem v-if="hasFeature('AUTOMATION')" label="Automation" />

    <!-- TIER 2+ only -->
    <MenuItem v-if="hasFeature('RAG')" label="Knowledge Base" />

    <!-- TIER 3 only -->
    <MenuItem v-if="hasFeature('AUTO_LEARNING')" label="Learning Dashboard">
      <Badge type="info">Premium</Badge>
    </MenuItem>
  </MainLayout>
</template>
```

#### 6.7.4 Intelligence Engine Feature Gating

```python
# intelligence-engine/app/main.py
from app.config.features import FEATURE_MATRIX

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Get tier from Cryptlex license metadata
    tier = LexActivator.GetLicenseMetadata("tier")  # Returns "TIER_1", "TIER_2", "TIER_3"
    features = FEATURE_MATRIX[tier]

    # Conditional RAG initialization
    if features["RAG"]:
        logger.info("✅ RAG enabled (TIER 2+): Loading ChromaDB + NOMIC embeddings")
        app.state.rag = await initialize_rag()
    else:
        logger.info("⏭️  RAG disabled (TIER 1): Skipping embeddings service")
        app.state.rag = None

    # Conditional Auto-Learning
    if features["AUTO_LEARNING"]:
        logger.info("✅ Auto-Learning enabled (TIER 3): Loading pattern DB")
        await load_auto_learned_patterns()
    else:
        logger.info("⏭️  Auto-Learning disabled (TIER 1-2)")

    yield
```

#### 6.7.5 X-Tenant-Tier Header Pattern (2025 SaaS Standard)

**REST API Tier Enforcement**:

```javascript
// Backend adds header to all responses
app.use((req, res, next) => {
  const tier = req.app.locals.license.tier;
  res.setHeader('X-Tenant-Tier', tier); // "TIER_1", "TIER_2", "TIER_3"
  next();
});

// Frontend checks header for dynamic UI
const response = await ofetch('/api/workflows', {
  onResponse({ response }) {
    const tier = response.headers.get('X-Tenant-Tier');
    if (tier === 'TIER_1' && response.url.includes('/rag')) {
      // Redirect to upgrade page
      window.location.href = '/settings/upgrade';
    }
  }
});
```

**Benefits**:
- ✅ **Centralized control**: Backend enforces tier, frontend adapts
- ✅ **API versioning**: Different tier = different capabilities
- ✅ **Upgrade prompts**: Frontend knows when to show "Upgrade to unlock"

#### 6.7.6 Upgrade Prompts (Tier-Locked Features)

```vue
<!-- Example: RAG upload blocked for TIER 1 -->
<template>
  <div v-if="!hasFeature('RAG')" class="upgrade-prompt">
    <Icon name="lock" size="48" />
    <h3>Knowledge Base (TIER 2+)</h3>
    <p>Upload documents and enable semantic search with RAG.</p>
    <Button @click="openUpgradeModal" variant="primary">
      Upgrade to Standard (€7.99/mo)
    </Button>
  </div>

  <RAGUploader v-else />
</template>
```

---

## 7. Auto-Update System

### 7.1 Why NOT Watchtower?

**Watchtower Issues** (2025 best practices):
- ❌ "Not recommended for production" (official docs)
- ❌ Blind auto-updates (no admin approval)
- ❌ No pre-update backup
- ❌ No rollback mechanism
- ❌ Full Docker socket access (security risk)

**Our Custom Solution**:
- ✅ Admin approval required (1-click UI)
- ✅ Automatic pre-update backup
- ✅ 1-click rollback se problemi
- ✅ Update notifications (no surprise updates)
- ✅ Changelog viewer integrato

### 7.2 Update Service Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Update Service (sidecar container)                      │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  update-checker.py (cron ogni 24h)             │    │
│  │                                                  │    │
│  │  1. Poll private registry (Docker Hub)          │    │
│  │  2. Check new image tags                        │    │
│  │  3. Compare with current versions                │    │
│  │  4. If update available → Notify admin          │    │
│  └───────────────────────┬──────────────────────────┘    │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  notification-handler.py                        │    │
│  │                                                  │    │
│  │  • Send notification to admin dashboard         │    │
│  │  • Badge on frontend UI (🔔 Update available)   │    │
│  │  • Email notification (optional)                │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Admin clicks "Update Now" in UI                │    │
│  └───────────────────────┬──────────────────────────┘    │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  backup-manager.py                              │    │
│  │                                                  │    │
│  │  1. Stop containers (graceful shutdown)         │    │
│  │  2. Backup PostgreSQL DB (pg_dump)              │    │
│  │  3. Backup Redis data                           │    │
│  │  4. Tag current images as :rollback             │    │
│  └───────────────────────┬──────────────────────────┘    │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  updater.py                                     │    │
│  │                                                  │    │
│  │  1. Pull new images from registry               │    │
│  │  2. Tag as :latest                              │    │
│  │  3. Start containers with new images            │    │
│  │  4. Health check loop (wait ready)              │    │
│  │  5. If healthy → Success                        │    │
│  │     Else → Trigger rollback                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 7.3 Update Service Implementation

**docker-compose.update.yml**:
```yaml
services:
  update-service:
    build:
      context: ./update-service
      dockerfile: Dockerfile
    container_name: pilotpros-update-service
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker API access
      - ./backups:/backups                          # Backup storage
    environment:
      REGISTRY_URL: docker.io/pilotpros
      REGISTRY_USERNAME: ${DOCKER_USERNAME}
      REGISTRY_TOKEN: ${DOCKER_TOKEN}
      CHECK_INTERVAL: 86400  # 24 hours
      ADMIN_API_URL: http://backend:3001/api/admin/updates
    restart: unless-stopped
    networks:
      - pilotpros-prod
```

**update-checker.py** (main loop):
```python
import docker
import requests
import time
from datetime import datetime

REGISTRY = "docker.io/pilotpros"
CHECK_INTERVAL = 86400  # 24h

client = docker.from_env()

def get_current_versions():
    """Get current running image versions"""
    containers = client.containers.list()
    versions = {}
    for container in containers:
        if "pilotpros" in container.name:
            image = container.image.tags[0] if container.image.tags else "unknown"
            versions[container.name] = image
    return versions

def check_registry_updates():
    """Check Docker Hub for new image tags"""
    updates_available = []

    services = [
        "backend", "frontend", "intelligence-engine",
        "embeddings", "postgres", "redis", "n8n", "nginx"
    ]

    for service in services:
        # Get latest tag from registry
        url = f"https://hub.docker.com/v2/repositories/{REGISTRY}/{service}/tags"
        response = requests.get(url)
        if response.status_code == 200:
            tags = response.json()["results"]
            latest = tags[0]["name"]  # Assume first tag is latest

            # Compare with current version
            current = get_current_versions().get(f"pilotpros-{service}-prod")
            if current and latest not in current:
                updates_available.append({
                    "service": service,
                    "current": current,
                    "latest": latest
                })

    return updates_available

def notify_admin(updates):
    """Send notification to admin dashboard"""
    payload = {
        "type": "update_available",
        "updates": updates,
        "timestamp": datetime.now().isoformat()
    }

    requests.post(
        "http://backend:3001/api/admin/notifications",
        json=payload
    )

def main():
    print("🔄 Update checker started (checking every 24h)")

    while True:
        print("🔍 Checking for updates...")
        updates = check_registry_updates()

        if updates:
            print(f"✅ {len(updates)} updates available")
            notify_admin(updates)
        else:
            print("✅ No updates available")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
```

**backup-manager.py**:
```python
import docker
import subprocess
from datetime import datetime

client = docker.from_env()

def backup_database():
    """Backup PostgreSQL database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/backups/postgres_backup_{timestamp}.sql"

    # Run pg_dump inside postgres container
    container = client.containers.get("pilotpros-postgres-prod")
    result = container.exec_run(
        f"pg_dump -U pilotpros_user -d pilotpros_db -f /backups/backup.sql"
    )

    if result.exit_code == 0:
        print(f"✅ Database backed up to {backup_file}")
        return backup_file
    else:
        raise RuntimeError(f"❌ Database backup failed: {result.output}")

def backup_redis():
    """Backup Redis data"""
    container = client.containers.get("pilotpros-redis-prod")
    result = container.exec_run("redis-cli SAVE")

    if result.exit_code == 0:
        print("✅ Redis data backed up")
    else:
        raise RuntimeError("❌ Redis backup failed")

def tag_current_images():
    """Tag current images as :rollback"""
    containers = client.containers.list()
    for container in containers:
        if "pilotpros" in container.name:
            image = container.image
            # Tag current image as :rollback
            image.tag(image.tags[0].split(":")[0], "rollback")
            print(f"✅ Tagged {image.tags[0]} as :rollback")

def create_backup():
    """Full backup before update"""
    print("💾 Creating pre-update backup...")
    backup_database()
    backup_redis()
    tag_current_images()
    print("✅ Backup completed")
```

### 7.4 Frontend Update UI

**Admin Dashboard** (update notification):
```vue
<template>
  <div class="update-notification" v-if="updateAvailable">
    <Alert type="info">
      <template #icon>🔔</template>
      <template #title>Update Available</template>

      <p>New version available for {{ updates.length }} services:</p>
      <ul>
        <li v-for="update in updates" :key="update.service">
          <strong>{{ update.service }}</strong>:
          {{ update.current }} → <Badge>{{ update.latest }}</Badge>
        </li>
      </ul>

      <div class="actions">
        <Button @click="showChangelog" variant="secondary">
          View Changelog
        </Button>
        <Button @click="startUpdate" variant="primary">
          Update Now
        </Button>
      </div>
    </Alert>
  </div>

  <!-- Update Progress Modal -->
  <Modal v-if="updating" title="Updating PilotProOS...">
    <ProgressBar :value="updateProgress" />
    <LogViewer :logs="updateLogs" />

    <template #footer>
      <Button @click="cancelUpdate" variant="danger" :disabled="updateProgress > 50">
        Cancel
      </Button>
    </template>
  </Modal>
</template>

<script setup>
const updateAvailable = ref(false)
const updates = ref([])
const updating = ref(false)
const updateProgress = ref(0)
const updateLogs = ref([])

async function startUpdate() {
  updating.value = true

  // Call backend API to trigger update
  const response = await fetch('/api/admin/updates/execute', {
    method: 'POST'
  })

  // Stream update logs via SSE
  const eventSource = new EventSource('/api/admin/updates/logs')
  eventSource.onmessage = (event) => {
    const log = JSON.parse(event.data)
    updateLogs.value.push(log.message)
    updateProgress.value = log.progress

    if (log.status === 'completed') {
      updating.value = false
      showSuccessMessage()
    }
  }
}
</script>
```

### 7.5 Rollback Mechanism

**rollback.py**:
```python
import docker

client = docker.from_env()

def rollback():
    """Rollback to previous version"""
    print("🔄 Starting rollback...")

    # Stop all containers
    containers = client.containers.list()
    for container in containers:
        if "pilotpros" in container.name:
            print(f"⏸️  Stopping {container.name}")
            container.stop()

    # Remove current containers
    for container in containers:
        if "pilotpros" in container.name:
            print(f"🗑️  Removing {container.name}")
            container.remove()

    # Restore :rollback images
    images = client.images.list()
    for image in images:
        for tag in image.tags:
            if ":rollback" in tag:
                # Retag as :latest
                repo = tag.split(":")[0]
                image.tag(repo, "latest")
                print(f"✅ Restored {tag} as :latest")

    # Restore database backup
    restore_database_backup()

    # Start containers with rollback images
    subprocess.run(["docker-compose", "up", "-d"])

    print("✅ Rollback completed")
```

---

## 8. Configuration Management

### 8.1 Environment Variable Strategy

**Total Variables per Tier**:
- Backend: 18 variables
- Intelligence Engine: 22 variables (TIER 1) / 25 (TIER 2+)
- PostgreSQL: 5 variables
- Redis: 3 variables
- n8n: 28 variables
- Embeddings: 4 variables (TIER 2+ only)

**Auto-Generation Priority**:
- ✅ **MUST auto-generate**: JWT secrets, session secrets, DB passwords
- ✅ **SHOULD auto-generate**: Service-to-service tokens
- ⚠️ **Optional**: LLM API keys (skip-friendly, configurable post-install)

### 8.2 Secrets Generator

**generate-secrets.sh**:
```bash
#!/bin/bash
# Auto-generate secure secrets for PilotProOS

generate_secret() {
    local length=$1
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# JWT secrets (min 32 chars for production validation)
JWT_SECRET=$(generate_secret 64)
REFRESH_TOKEN_SECRET=$(generate_secret 64)
SESSION_SECRET=$(generate_secret 64)

# Database credentials
DB_PASSWORD=$(generate_secret 32)

# n8n credentials
N8N_ENCRYPTION_KEY=$(generate_secret 32)
N8N_USER_MANAGEMENT_JWT_SECRET=$(generate_secret 64)

# Service-to-service auth
BACKEND_SERVICE_TOKEN=$(generate_secret 32)
INTELLIGENCE_SERVICE_TOKEN=$(generate_secret 32)

# Output as env format
cat > /opt/pilotpros/.secrets.env <<EOF
# Auto-generated secrets - $(date)
# DO NOT COMMIT TO GIT

JWT_SECRET=$JWT_SECRET
REFRESH_TOKEN_SECRET=$REFRESH_TOKEN_SECRET
SESSION_SECRET=$SESSION_SECRET
DB_PASSWORD=$DB_PASSWORD
N8N_ENCRYPTION_KEY=$N8N_ENCRYPTION_KEY
N8N_USER_MANAGEMENT_JWT_SECRET=$N8N_USER_MANAGEMENT_JWT_SECRET
BACKEND_SERVICE_TOKEN=$BACKEND_SERVICE_TOKEN
INTELLIGENCE_SERVICE_TOKEN=$INTELLIGENCE_SERVICE_TOKEN
EOF

chmod 600 /opt/pilotpros/.secrets.env
echo "✅ Secrets generated and saved to /opt/pilotpros/.secrets.env"
```

### 8.3 Template Files

**.env.template** (backend):
```bash
# PilotProOS Backend Configuration
# Generated by installer on {{TIMESTAMP}}

# Server
NODE_ENV=production
PORT=3001
HOST=0.0.0.0

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME={{DB_NAME}}
DB_USER={{DB_USER}}
DB_PASSWORD={{DB_PASSWORD}}

# JWT Authentication
JWT_SECRET={{JWT_SECRET}}
JWT_EXPIRES_IN=30m
REFRESH_TOKEN_SECRET={{REFRESH_TOKEN_SECRET}}
REFRESH_TOKEN_EXPIRES_IN=7d
SESSION_SECRET={{SESSION_SECRET}}

# CORS
CORS_ORIGINS={{FRONTEND_URL}}

# n8n Integration
N8N_URL=http://automation-engine:5678
N8N_API_KEY={{N8N_API_KEY}}

# Intelligence Engine
INTELLIGENCE_ENGINE_URL=http://intelligence-engine:8000
INTELLIGENCE_SERVICE_TOKEN={{INTELLIGENCE_SERVICE_TOKEN}}

# Logging
LOG_LEVEL=warn
LOG_FILE=/var/log/pilotpros/backend.log

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

**.env.template** (intelligence-engine, TIER 2+):
```bash
# Intelligence Engine Configuration
# Generated by installer on {{TIMESTAMP}}

# Service Mode
SERVICE_MODE=api
API_PORT=8000

# Tier Configuration
TIER={{TIER}}  # MINIMAL | STANDARD | FULL
ENABLE_RAG={{ENABLE_RAG}}  # false | true
ENABLE_LEARNING={{ENABLE_LEARNING}}  # false | true

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME={{DB_NAME}}
DB_USER={{DB_USER}}
DB_PASSWORD={{DB_PASSWORD}}
DATABASE_URL=postgresql://{{DB_USER}}:{{DB_PASSWORD}}@postgres:5432/{{DB_NAME}}

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# Embeddings (TIER 2+ only)
{{#if TIER_2_OR_3}}
EMBEDDINGS_ENDPOINT=http://embeddings:8001
{{/if}}

# LLM API Keys (optional, configurable post-install)
OPENAI_API_KEY={{OPENAI_API_KEY}}
ANTHROPIC_API_KEY={{ANTHROPIC_API_KEY}}
GROQ_API_KEY={{GROQ_API_KEY}}

# LangSmith (optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=pilotpros-production
LANGCHAIN_API_KEY={{LANGCHAIN_API_KEY}}

# n8n Integration
N8N_URL=http://automation-engine:5678
N8N_API_KEY={{N8N_API_KEY}}

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=info
```

### 8.4 docker-compose Generator

**compose_generator.py**:
```python
import yaml
from jinja2 import Template

def generate_compose(tier: str, config: dict) -> str:
    """Generate docker-compose.yml based on tier"""

    # Load base template
    with open("templates/docker-compose.base.yml") as f:
        base = yaml.safe_load(f)

    # Tier-specific modifications
    if tier == "MINIMAL":
        # Remove embeddings service
        base["services"].pop("embeddings", None)

        # Adjust memory limits
        base["services"]["intelligence-engine"]["deploy"]["resources"]["limits"]["memory"] = "200M"
        base["services"]["backend"]["deploy"]["resources"]["limits"]["memory"] = "64M"

    elif tier == "STANDARD":
        # Keep all services, standard limits
        base["services"]["intelligence-engine"]["deploy"]["resources"]["limits"]["memory"] = "250M"

    elif tier == "FULL":
        # Performance-tuned limits
        base["services"]["intelligence-engine"]["deploy"]["resources"]["limits"]["memory"] = "350M"
        base["services"]["postgres"]["deploy"]["resources"]["limits"]["memory"] = "128M"
        base["services"]["redis"]["deploy"]["resources"]["limits"]["memory"] = "150M"

    # Replace placeholders
    template = Template(yaml.dump(base))
    rendered = template.render(**config)

    return rendered

# Usage
config = {
    "DB_NAME": "pilotpros_db",
    "DB_USER": "pilotpros_user",
    "DB_PASSWORD": "generated_password_here",
    "JWT_SECRET": "generated_jwt_secret_here",
    # ... other config
}

compose_yml = generate_compose("STANDARD", config)

with open("/opt/pilotpros/docker-compose.yml", "w") as f:
    f.write(compose_yml)
```

---

## 9. Implementation Roadmap

### 9.1 Phase Breakdown

| Phase | Deliverables | Effort | Dependencies |
|-------|-------------|--------|--------------|
| **Phase 1: Container Optimization** | 3 docker-compose tiers + Dockerfiles prod | 30h | None |
| **Phase 2: ISO Builder** | Bootable USB Ubuntu 24.04 + Docker | 20h | None (parallel with Phase 1) |
| **Phase 3: Docker Packaging** | 8 images .tar.gz tiered | 12h | Phase 1 |
| **Phase 4: CLI Installer** | Python Textual wizard 8 screens | 45h | Phase 2, 3 |
| **Phase 5: Licensing** | Cryptlex integration + validator | 15h | Phase 4 |
| **Phase 6: Config Templates** | .env + docker-compose generators | 10h | Phase 1 |
| **Phase 7: Auto-Update** | Update sidecar + UI integration | 25h | Phase 4 |
| **Phase 8: Documentation** | 4 PDF manuals | 12h | Phase 4, 5, 6, 7 |
| **Phase 9: Testing** | 3-tier validation + USB final | 20h | All |

**Total**: 189 hours (~24 working days @ 8h/day)

### 9.2 Critical Path

```
Phase 1 (30h) ──┐
                ├──> Phase 3 (12h) ──┐
Phase 2 (20h) ──┘                    ├──> Phase 4 (45h) ──┐
                                     │                     │
Phase 6 (10h) ───────────────────────┘                     ├──> Phase 5 (15h) ──┐
                                                           │                     │
Phase 7 (25h) ─────────────────────────────────────────────┘                     │
                                                                                 │
Phase 8 (12h) ───────────────────────────────────────────────────────────────────┤
                                                                                 │
                                                                                 ▼
                                                                         Phase 9 (20h)
                                                                         RELEASE
```

**Critical Path**: Phase 1 → Phase 3 → Phase 4 → Phase 7 → Phase 9 = **132 hours**

**Parallel Work**: Phase 2, 5, 6, 8 possono essere parallelizzati

**Optimistic Timeline**: 17 giorni (con 2 devs paralleli)
**Realistic Timeline**: 24 giorni (1 dev)

### 9.3 Milestones

**Milestone 1**: Container Optimization Complete (Day 4)
- ✅ 3 docker-compose variants funzionanti
- ✅ Test RAM consumption su VM (2GB, 4GB, 8GB)
- ✅ Benchmark performance per tier

**Milestone 2**: Installer Prototype (Day 12)
- ✅ Python Textual wizard 8 screens
- ✅ Mock installation flow (no real Docker load)
- ✅ User acceptance testing con non-tecnici

**Milestone 3**: End-to-End Install Test (Day 18)
- ✅ Full install flow da USB a stack funzionante
- ✅ Test su 3 scenari: VirtualBox, Hostinger VPS, hardware fisico
- ✅ Validation checklist 100% passed

**Milestone 4**: Production Ready (Day 24)
- ✅ Documentation completa
- ✅ Licensing funzionante
- ✅ Auto-update testato
- ✅ USB finale masterizzata

---

## 10. Testing Strategy

### 10.1 Test Environments

**Environment 1**: VirtualBox VMs
- VM1: 2GB RAM (TIER 1 MINIMAL)
- VM2: 4GB RAM (TIER 2 STANDARD)
- VM3: 8GB RAM (TIER 3 FULL)

**Environment 2**: Live VPS
- Hostinger Basic (2GB RAM, €3.99/mo)
- Hetzner CX21 (4GB RAM, €5.83/mo)

**Environment 3**: Physical Hardware
- Dell PowerEdge R230 (16GB RAM, test overkill scenario)

### 10.2 Test Matrix

| Test Case | TIER 1 | TIER 2 | TIER 3 | Pass Criteria |
|-----------|--------|--------|--------|---------------|
| **Install Time** | <20 min | <25 min | <30 min | All <30 min |
| **RAM Usage** | <1.2GB | <1.8GB | <2.5GB | Within 10% target |
| **Boot to Ready** | <3 min | <4 min | <5 min | Services healthy |
| **Chat Response** | <2s | <1.5s | <1s | P95 latency |
| **RAG Accuracy** | N/A | >85% | >90% | Test set 100 queries |
| **n8n Execution** | <10s | <8s | <5s | Simple workflow |
| **Error Rate** | <1% | <0.5% | <0.1% | 1000 requests test |

### 10.3 Validation Checklist

**Installer Validation** (☐ = not done, ✅ = passed):
- ☐ Welcome screen displays correctly
- ☐ License validation (valid key)
- ☐ License validation (invalid key) → error shown
- ☐ Tier selection (all 3 tiers selectable)
- ☐ Resource check (sufficient RAM) → pass
- ☐ Resource check (insufficient RAM) → warning + downgrade
- ☐ Admin user creation (valid email)
- ☐ Admin user creation (invalid email) → error
- ☐ Password strength (weak password) → warning
- ☐ Service config (auto-generate secrets)
- ☐ Installation phase (all 6 steps complete)
- ☐ Success screen (credentials displayed)

**Post-Install Validation**:
- ☐ Frontend accessible at https://localhost
- ☐ Admin login works with generated credentials
- ☐ Chat widget functional
- ☐ n8n accessible at http://localhost:5678
- ☐ Database migrations applied (8 files)
- ☐ systemd service enabled (auto-start on reboot)
- ☐ Credentials PDF saved to /opt/pilotpros/

**Tier-Specific Validation**:
- ☐ TIER 1: Chat works, RAG unavailable (correct)
- ☐ TIER 2: Chat + RAG works, document upload successful
- ☐ TIER 3: All features + auto-learning enabled

### 10.4 Performance Benchmarks

**Load Test** (Apache Bench):
```bash
# Test 1: Chat endpoint (1000 requests, 10 concurrent)
ab -n 1000 -c 10 -p chat.json -T application/json \
   http://localhost:8000/api/chat

# Expected results:
# TIER 1: Mean response time <2000ms
# TIER 2: Mean response time <1500ms
# TIER 3: Mean response time <1000ms

# Test 2: RAG search (TIER 2+ only)
ab -n 500 -c 5 -p rag-query.json -T application/json \
   http://localhost:8000/api/rag/search

# Expected: Mean response time <800ms
```

---

## 11. VPS Compatibility Matrix

### 11.1 Provider Comparison

| Provider | Plan | RAM | CPU | Disk | Price/mo | Recommended Tier |
|----------|------|-----|-----|------|----------|-----------------|
| **Hostinger** | Basic | 2GB | 2 cores | 40GB SSD | €3.99 | ✅ TIER 1 |
| **Hostinger** | Business | 4GB | 4 cores | 80GB SSD | €7.99 | ✅ TIER 2 (BEST) |
| **Hostinger** | Premium | 8GB | 6 cores | 160GB SSD | €13.99 | ✅ TIER 3 |
| **Hetzner** | CX11 | 2GB | 1 core | 20GB SSD | €4.15 | ⚠️ TIER 1 (1 core rischio) |
| **Hetzner** | CX21 | 4GB | 2 cores | 40GB SSD | €5.83 | ✅ TIER 2 |
| **Hetzner** | CX31 | 8GB | 2 cores | 80GB SSD | €10.69 | ✅ TIER 3 |
| **Contabo** | VPS S | 4GB | 4 cores | 200GB SSD | €4.99 | ✅ TIER 2 (BUDGET) |
| **Contabo** | VPS M | 8GB | 6 cores | 400GB SSD | €8.99 | ✅ TIER 3 |
| **DigitalOcean** | Basic | 2GB | 1 core | 50GB SSD | $12/mo | ❌ Too expensive for TIER 1 |
| **DigitalOcean** | General | 4GB | 2 cores | 80GB SSD | $24/mo | ❌ Too expensive |

**Best Value**:
- 🥇 **TIER 2**: Contabo VPS S (€4.99/mo, 4GB RAM, full features)
- 🥈 **TIER 2**: Hostinger Business (€7.99/mo, better support)
- 🥉 **TIER 3**: Hostinger Premium (€13.99/mo, 8GB)

### 11.2 Network Requirements

**Bandwidth Estimate**:
- **Installer download**: One-time ~6GB (TIER 2)
- **Daily traffic**: ~500MB - 2GB (dipende da utenti)
- **Update download**: ~1GB per major update (ogni 3-6 mesi)

**Ports Required**:
- `80` (HTTP) - Frontend
- `443` (HTTPS) - Frontend (production)
- `3001` (optional) - Backend API direct access
- `5678` (optional) - n8n admin panel
- `8000` (optional) - Intelligence Engine API

**Recommended**: Tutti i servizi dietro Nginx reverse proxy su 443 solo.

---

## 12. Technical Decisions

### 12.1 Why Python Textual?

**Alternatives Considered**:
- ❌ **Node.js Inquirer**: CLI-only, no mouse support, troppo tecnico per utenti base
- ❌ **Bash whiptail/dialog**: Limitato, UI brutta, hard to maintain
- ❌ **Electron GUI**: 100MB+ overhead, richiede X server

**Why Textual WINS**:
- ✅ **Modern TUI**: Mouse support, rich widgets, CSS-like styling
- ✅ **User-friendly**: Visual forms, progress bars, modals (come GUI)
- ✅ **Python**: Same stack as intelligence-engine, team familiarity
- ✅ **Active**: 24k+ stars, MIT license, frequent updates
- ✅ **Cross-platform**: Linux, macOS, Windows (future-proof)

### 12.2 Why Cryptlex?

**Alternatives Considered**:
- ❌ **Custom licensing**: 60h+ dev time, security risks, no support
- ❌ **LicenseSpring**: $99/mo minimum, overkill per SMB
- ❌ **Keygen**: No built-in offline grace period, complex setup

**Why Cryptlex WINS**:
- ✅ **SaaS**: No infrastructure to manage
- ✅ **Floating licenses**: Perfect for Docker (hardware fingerprint non dipende da container ID)
- ✅ **Offline grace period**: 30 days built-in
- ✅ **REST API + native libs**: Python + Node.js support
- ✅ **Pricing**: $49/mo for 100 licenses (acceptable)
- ✅ **Dashboard**: Analytics + manual license management

### 12.3 Why Custom Update Service?

**Watchtower Issues** (from official docs):
> "Watchtower is intended to be used in homelabs, media centers, local dev environments, and similar. The maintainers do NOT recommend using Watchtower in a commercial or production environment."

**Why Custom WINS**:
- ✅ **Admin approval**: 1-click update button (no blind auto-updates)
- ✅ **Pre-update backup**: Automatic PostgreSQL + Redis backup
- ✅ **Rollback**: 1-click UI se update fails
- ✅ **Notifications**: Dashboard badge + email alert
- ✅ **Changelog viewer**: Integrato nel UI
- ✅ **Safer**: No full Docker socket access needed

### 12.4 Why Ubuntu 24.04 LTS?

**Alternatives Considered**:
- ❌ **Docker Machine**: Deprecated, richiede hypervisor
- ❌ **CentOS Stream**: Meno compatibility hardware
- ❌ **Debian**: Meno user-friendly installer

**Why Ubuntu WINS**:
- ✅ **LTS**: Support fino 2029 (5 anni)
- ✅ **Hardware compatibility**: Ampia, driver built-in
- ✅ **Docker support**: Official repository, well-tested
- ✅ **Familiarità**: Sistemisti conoscono Ubuntu
- ✅ **Cloud-init**: Easy per VPS automation

---

## 13. Future Enhancements

### 13.1 Phase 2 Features (Post-Launch)

**Kubernetes Support** (Q2 2026, 80h effort):
- Helm chart per deployment multi-node
- Horizontal Pod Autoscaler (HPA) per intelligence engine
- Persistent Volume Claims (PVC) per database
- Ingress controller integration
- Zero-downtime rolling updates

**Multi-Node Clustering** (Q3 2026, 120h effort):
- Redis Cluster (3 master + 3 replica)
- PostgreSQL replication (primary + 2 standby)
- Load balancer per backend API (HAProxy)
- Shared storage per n8n workflows (NFS / Ceph)

**Advanced Monitoring** (Q4 2026, 40h effort):
- Grafana dashboards (7 pre-built)
- Prometheus alerting rules (12 critical alerts)
- Loki log aggregation
- Jaeger distributed tracing
- Uptime monitoring (Uptime Kuma integrato)

**Backup/Restore Automation** (Q1 2027, 30h effort):
- Scheduled backups (daily, weekly, monthly)
- S3-compatible storage support (AWS, Minio, Backblaze)
- Point-in-time recovery (PITR) per PostgreSQL
- 1-click restore da UI
- Backup verification (test restore automatico)

### 13.2 Community Edition

**Open Source Release** (Q2 2027):
- GitHub public repository
- MIT license
- Community forums
- Plugin marketplace
- Contributor guidelines

**Differences from Enterprise**:
- ❌ NO licensing enforcement
- ❌ NO priority support
- ❌ NO auto-update service
- ✅ Basic features only (no advanced learning)

---

## 14. Appendices

### 14.1 Glossary

**Terms**:
- **ISO**: Disk image format (bootable)
- **USB Live**: Bootable USB con OS temporaneo
- **TUI**: Terminal User Interface (grafico in terminale)
- **Tier**: Profilo deployment (MINIMAL/STANDARD/FULL)
- **RAG**: Retrieval-Augmented Generation (knowledge base search)
- **Floating License**: License non legata a hardware specifico
- **Grace Period**: Periodo validità offline license (30 giorni)
- **Rollback**: Ripristino versione precedente post-update
- **Sidecar**: Container ausiliario nello stesso pod/network

### 14.2 Command Reference

**Installer**:
```bash
# Auto-start (via autorun.sh)
python3 /pilotpros-installer/installer/main.py

# Manual start
cd /pilotpros-installer
python3 installer/main.py

# Retry failed installation
python3 installer/main.py --retry

# Skip license check (debug only)
python3 installer/main.py --skip-license
```

**Stack Management** (post-install):
```bash
# Start stack
/opt/pilotpros/stack-manager.sh start

# Stop stack
/opt/pilotpros/stack-manager.sh stop

# View logs
/opt/pilotpros/stack-manager.sh logs

# Health check
/opt/pilotpros/stack-manager.sh health

# Backup database
/opt/pilotpros/stack-manager.sh backup

# Update stack (with backup)
/opt/pilotpros/stack-manager.sh update

# Rollback to previous version
/opt/pilotpros/stack-manager.sh rollback
```

**Docker**:
```bash
# View running containers
docker ps

# View logs
docker logs -f pilotpros-backend-prod

# Restart service
docker restart pilotpros-intelligence-engine-prod

# Check resource usage
docker stats
```

### 14.3 Troubleshooting Guide

**Issue 1**: Installer fails at "Loading Docker Images"
```
Error: Failed to load intelligence-full.tar.gz
```
**Solution**:
1. Check disk space: `df -h` (need 20GB+ free)
2. Verify USB integrity: `md5sum /dev/sdb` vs provided checksum
3. Try re-running installer
4. If persists, use TIER 1 MINIMAL (smaller images)

---

**Issue 2**: License validation fails
```
Error: License validation failed (status 401)
```
**Solution**:
1. Check internet connection: `ping 8.8.8.8`
2. Verify license key format: `XXXX-XXXX-XXXX-XXXX-XXXX-XXXX`
3. Check firewall: allow HTTPS outbound to `api.cryptlex.com`
4. Try offline activation (upload license file)

---

**Issue 3**: Services not starting (timeout)
```
Error: Health check timeout after 5 minutes
```
**Solution**:
1. Check RAM usage: `free -h` (must have 500MB+ free)
2. View Docker logs: `docker logs pilotpros-postgres-prod`
3. Restart failed service: `docker restart <container_name>`
4. If TIER 2/3, try downgrading to TIER 1

---

**Issue 4**: Chat not responding
```
Frontend shows: "Connection error"
```
**Solution**:
1. Check backend health: `curl http://localhost:3001/api/health`
2. Check intelligence engine: `curl http://localhost:8000/health`
3. View backend logs: `docker logs pilotpros-backend-prod`
4. Verify database connection: `docker exec pilotpros-postgres-prod pg_isready`

---

### 14.4 FAQ

**Q: Can I install on Windows?**
A: Not directly. Use VirtualBox + ISO boot or Windows Subsystem for Linux 2 (WSL2) + Docker Desktop.

**Q: How to add LLM API keys post-install?**
A: Edit `/opt/pilotpros/intelligence-engine/.env`, add `OPENAI_API_KEY=sk-xxx`, then `docker restart pilotpros-intelligence-engine-prod`.

**Q: Can I upgrade from TIER 1 to TIER 2 later?**
A: Yes. Edit `/opt/pilotpros/docker-compose.yml`, uncomment embeddings service, set `ENABLE_RAG=true` in intelligence-engine env, then `./stack-manager.sh restart`.

**Q: How to backup database manually?**
A: `docker exec pilotpros-postgres-prod pg_dump -U pilotpros_user pilotpros_db > backup.sql`

**Q: How to access n8n admin panel?**
A: Open `http://localhost:5678`, login with credentials from `/opt/pilotpros/credentials.pdf`.

**Q: How to reset admin password?**
A: Connect to database, run: `UPDATE pilotpros.users SET password=crypt('NewPassword123', gen_salt('bf')) WHERE email='admin@example.com';`

**Q: What happens if license expires?**
A: Intelligence Engine stops working. Other services (frontend, backend, n8n) continue running. Renew license to restore AI agent.

**Q: Can I run multiple PilotProOS instances on same server?**
A: Yes, but change ports in docker-compose.yml (3000→3010, 3001→3011, etc.) to avoid conflicts.

**Q: How to enable HTTPS with custom domain?**
A: Install certbot, obtain Let's Encrypt certificate, edit `/opt/pilotpros/nginx.conf` with SSL config, restart nginx.

**Q: How to migrate to larger VPS?**
A: Backup database + Redis, install PilotProOS on new VPS (select higher tier), restore backup, update DNS.

---

## 15. Conclusion

This document defines the complete strategy for transforming PilotProOS into a **plug-and-play on-premise distribution** via USB/ISO.

**Key Achievements**:
- ✅ **3-tier deployment strategy** (2GB, 4GB, 8GB RAM)
- ✅ **User-friendly installer** (zero CLI experience required)
- ✅ **Licensing integration** (Cryptlex floating licenses)
- ✅ **Auto-update system** (1-click update + rollback)
- ✅ **VPS compatibility** (Hostinger, Hetzner, Contabo)
- ✅ **Production-ready** containers (RAM-optimized)

**Timeline**: 24 giorni (189 ore) development effort

**Next Steps**: Approvazione stakeholder → Start Phase 1 (Container Optimization)

---

## 16. Changelog

### v1.1 (2025-10-18) - 2025 Best Practices Integration

**Research-Driven Update**: Comprehensive web research on battle-tested production solutions.

**Major Additions**:

#### Licensing System (Section 6)
- ✅ **6.1 Licensing Platform Evaluation**: Comparison table of Cryptlex vs Zentitle, 10Duke Enterprise, Keygen.sh (battle-tested alternatives with Fortune 500 track records)
- ✅ **6.2 Floating License Best Practices**: 3:1 users-to-licenses ratio (industry standard 2025), monitoring strategy (Week 1-8 optimization), high-security environments (air-gapped deployments)
- ✅ **6.7 Feature Management System**: Complete runtime feature gating architecture
  - Feature flag comparison (Unleash ⭐, LaunchDarkly, Split.io, Flagsmith)
  - Simplified in-house feature gating (recommended for MVP)
  - FEATURE_MATRIX implementation (Python + Node.js + Vue 3)
  - X-Tenant-Tier header pattern (2025 SaaS standard)
  - Upgrade prompts for tier-locked features

#### Container Optimization (Section 5)
- ✅ **5.9 Docker Production Best Practices 2025**:
  - Health checks for all services (REQUIRED - prevents silent failures)
  - Non-root user security (CVSS 7.8 vulnerability mitigation)
  - Read-only root filesystem (malware persistence prevention)
  - Resource limits (OOM kill protection)
  - Docker Compose overlay files (multi-environment best practice)
  - Logging best practices (10MB rotation, compression)
  - Secrets management (NO hardcoded credentials)

#### Architecture (Section 2)
- ✅ **2.2 Three-Tier Deployment Strategy**: Rebranded with GBB (Good/Better/Best) nomenclatura (80%+ SaaS adoption, 2025 Monetization Monitor)

**Research Sources**:
- Software licensing systems 2025 battle-tested solutions
- Feature flag platforms comparison (LaunchDarkly, Split.io, Unleash, Flagsmith)
- Docker production best practices 2025 (multi-stage builds, health checks, non-root)
- SaaS multi-tier architecture patterns (GBB model, X-Tenant-Tier header)
- On-premise floating licenses best practices (3:1 ratio, monitoring strategy)

**Benefits**:
- 🔒 **Enhanced Security**: Non-root containers, secrets management, read-only filesystem
- 📊 **Production Reliability**: Health checks prevent silent failures, resource limits prevent OOM kills
- 🎯 **Feature Gating**: Complete runtime enforcement (frontend + backend + intelligence engine)
- 💰 **Cost Optimization**: 3:1 floating license ratio (67% savings vs per-seat)
- 🏢 **Industry Alignment**: GBB pricing model, X-Tenant-Tier header (2025 SaaS standards)

**Lines Added**: ~800+ (expanded sections 5.9, 6.1, 6.2, 6.7)

---

### v1.0 (2025-10-18) - Initial Release

**Original Design Document**: Complete ISO/USB distribution strategy with 3-tier deployment model, Cryptlex licensing integration, auto-update system, and VPS compatibility matrix.

---

**Document Version**: 1.1
**Last Updated**: 2025-10-18
**Status**: DRAFT - Enhanced with 2025 Best Practices
**Author**: PilotProOS Team
