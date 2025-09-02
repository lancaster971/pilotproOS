# 🚨 Team Sync Troubleshooting Guide

**Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**Support Level**: Production

## 📋 Quick Reference

### Emergency Commands
```bash
# Complete system reset
npm run docker:clean && npm run dev

# Force container restart
docker restart $(docker ps -q --filter "name=pilotpros")

# Manual database recovery  
npm run docker:psql
\c pilotpros_db
SELECT COUNT(*) FROM n8n.workflow_entity;

# Check system health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Common Issues Quick Fix
| Issue | Quick Fix | Time |
|-------|-----------|------|
| Docker not running | `npm run dev` | 30s |
| Archive not found | Ask team for `team:export` | 5min |
| Import timeout | Retry import | 3min |
| n8n not responding | `docker restart pilotpros-automation-engine-dev` | 30s |
| Database corrupted | `npm run docker:reset` | 5min |

## 🔍 Export Issues

### Issue: Docker Stack Not Running

**Symptoms:**
```bash
❌ Docker stack non attivo. Esegui: npm run dev
```

**Diagnosis:**
```bash
# Check Docker daemon
docker ps
# If fails: Docker not running

# Check PilotPro containers  
docker ps --filter "name=pilotpros"
# If empty: Stack not started
```

**Resolution:**
```bash
# Start Docker Desktop (macOS)
open -a Docker

# Wait for Docker to be ready
docker ps

# Start PilotPro stack
npm run dev

# Verify all containers healthy
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Expected Result:**
```bash
NAMES                               STATUS
pilotpros-frontend-dev             Up X hours (healthy)
pilotpros-backend-dev              Up X hours (healthy)  
pilotpros-ai-agent-dev             Up X hours (healthy)
pilotpros-nginx-dev                Up X hours
pilotpros-automation-engine-dev    Up X hours (healthy)
pilotpros-postgres-dev             Up X hours (healthy)
```

---

### Issue: Database Connection Failed

**Symptoms:**
```bash
❌ Errore export database: connection refused
❌ psql: error: connection to server on socket failed
```

**Diagnosis:**
```bash
# Check PostgreSQL container
docker exec pilotpros-postgres-dev pg_isready -U pilotpros_user -d pilotpros_db

# Check container logs
docker logs pilotpros-postgres-dev --tail 50
```

**Resolution:**
```bash
# Restart PostgreSQL container
docker restart pilotpros-postgres-dev

# Wait for health check
sleep 10

# Verify database connection
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "SELECT 1"

# If still failing, reset database
npm run docker:reset
```

**Advanced Diagnosis:**
```bash
# Check database disk space
docker exec pilotpros-postgres-dev df -h /var/lib/postgresql/data

# Check database logs for corruption
docker exec pilotpros-postgres-dev tail -100 /var/log/postgresql/postgresql-*.log

# Manual database recovery
docker exec -it pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db
\dt n8n.*  -- Check tables exist
SELECT COUNT(*) FROM n8n.workflow_entity;  -- Check data
```

---

### Issue: n8n API Timeout

**Symptoms:**
```bash  
❌ Errore export workflows: timeout
❌ wget: connection timed out
```

**Diagnosis:**
```bash
# Check n8n container health
docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/healthz"

# Check n8n logs
docker logs pilotpros-automation-engine-dev --tail 50

# Test manual API access
curl -u admin:pilotpros_admin_2025 http://localhost:5678/api/v1/workflows
```

**Resolution:**
```bash
# Restart n8n container
docker restart pilotpros-automation-engine-dev

# Wait for n8n startup (can take 60+ seconds)
sleep 30

# Verify n8n API
docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/healthz"

# Test workflow access
docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/api/v1/workflows" --user="admin:pilotpros_admin_2025"
```

**If n8n won't start:**
```bash
# Check n8n data volume
docker volume inspect pilotpros_n8n_dev_data

# Reset n8n completely
docker stop pilotpros-automation-engine-dev
docker volume rm pilotpros_n8n_dev_data  
npm run dev

# Reconfigure n8n
npm run n8n:auto-setup
```

---

### Issue: Disk Space Insufficient

**Symptoms:**
```bash
❌ No space left on device  
❌ Errore creazione archivio: ENOSPC
```

**Diagnosis:**
```bash
# Check available disk space
df -h .

# Check Docker space usage
docker system df

# Check export directory size
du -sh team-sync-exports/
```

**Resolution:**
```bash
# Clean old exports (keep latest 5)
cd team-sync-exports/
ls -t *.tar.gz | tail -n +6 | xargs rm -f

# Clean Docker system
docker system prune -f

# Clean Docker volumes (DANGER: loses data)
docker volume prune -f

# Clean build caches
npm run clean 2>/dev/null || true
cd frontend && npm run clean 2>/dev/null || true
cd ../backend && npm run clean 2>/dev/null || true
```

**Prevent recurrence:**
```bash
# Add to crontab for weekly cleanup
echo "0 2 * * 0 cd $(pwd) && find team-sync-exports/ -name '*.tar.gz' -mtime +7 -delete" | crontab -
```

## 🔍 Import Issues

### Issue: Archive Not Found

**Symptoms:**
```bash
❌ Nessun archivio trovato. Chiedi al collega di eseguire: npm run team:export
```

**Diagnosis:**
```bash
# Check export directory exists
ls -la team-sync-exports/

# Check for archives
ls -la team-sync-exports/*.tar.gz 2>/dev/null || echo "No archives found"

# Check file patterns
ls -la team-sync-exports/team-export-*.tar.gz 2>/dev/null || echo "No matching archives"
```

**Resolution:**
```bash
# Create directory if missing
mkdir -p team-sync-exports

# Obtain archive from team member
# Option 1: Direct file transfer
scp colleague@hostname:/path/to/pilotproOS/team-sync-exports/team-export-*.tar.gz team-sync-exports/

# Option 2: Manual download (Google Drive, Slack, etc.)
# Place downloaded file in team-sync-exports/

# Verify archive integrity
tar -tzf team-sync-exports/team-export-*.tar.gz > /dev/null && echo "Archive OK"
```

**If archive is corrupted:**
```bash
# Verify archive
tar -tzf team-sync-exports/team-export-*.tar.gz

# If corrupted, re-download
rm team-sync-exports/team-export-*.tar.gz
# Ask team member to re-export
```

---

### Issue: Docker Start Timeout

**Symptoms:**
```bash
❌ Timeout avvio database
❌ Errore avvio Docker: Timeout
```

**Diagnosis:**
```bash
# Check Docker daemon status
docker info

# Check system resources
top | head -20

# Check container status
docker ps -a --filter "name=pilotpros"

# Check Docker logs
docker logs pilotpros-postgres-dev --tail 20
```

**Resolution:**
```bash
# Increase system resources (Docker Desktop)
# Settings > Resources > Memory: 8GB+, CPUs: 4+

# Manual container startup with extended timeout
docker-compose -f docker-compose.dev.yml up -d postgres-dev
sleep 30
docker-compose -f docker-compose.dev.yml up -d

# Check health status
docker ps --format "table {{.Names}}\t{{.Status}}"

# If still failing, complete reset
npm run docker:clean
sleep 10
npm run dev
```

**System performance optimization:**
```bash
# Close unnecessary applications
killall -9 "Google Chrome" "Slack" "VS Code" 2>/dev/null || true

# Check memory usage
vm_stat | head -10

# Free up memory (macOS)
sudo purge
```

---

### Issue: Database Import Failed

**Symptoms:**
```bash
❌ Errore import database: syntax error
❌ psql: FATAL: database does not exist
```

**Diagnosis:**
```bash
# Check database exists
docker exec pilotpros-postgres-dev psql -U pilotpros_user -l | grep pilotpros_db

# Check SQL file integrity
head -20 team-sync-exports/export-*/database-complete.sql
tail -20 team-sync-exports/export-*/database-complete.sql

# Check for SQL syntax issues
docker exec -i pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db --dry-run < team-sync-exports/export-*/database-complete.sql
```

**Resolution:**
```bash
# Recreate database from scratch
docker exec pilotpros-postgres-dev psql -U pilotpros_user -c "DROP DATABASE IF EXISTS pilotpros_db"
docker exec pilotpros-postgres-dev psql -U pilotpros_user -c "CREATE DATABASE pilotpros_db"

# Manual import with error handling
docker exec -i pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -v ON_ERROR_STOP=1 < team-sync-exports/export-*/database-complete.sql

# Verify import success
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "SELECT COUNT(*) FROM n8n.workflow_entity"
```

**If import keeps failing:**
```bash
# Reset entire PostgreSQL container
docker stop pilotpros-postgres-dev
docker rm pilotpros-postgres-dev
docker volume rm pilotpros_postgres_dev_data

# Restart stack
npm run dev

# Wait for initialization
sleep 60

# Retry import
npm run team:import
```

---

### Issue: Version Compatibility Warning

**Symptoms:**
```bash
⚠️ Versione diversa (1.0.0 → 1.1.0)
⚠️ Errore verifica compatibilità
```

**Diagnosis:**
```bash
# Check current version
cat package.json | grep '"version"'

# Check export metadata
cat team-sync-exports/export-*/export-metadata.json | grep version

# Compare Git commits
git log --oneline -10
```

**Resolution:**

**Forward Compatibility** (newer import into older system):
```bash
# Usually safe, but verify after import
npm run team:import
# Answer 'y' to version warning

# Verify functionality
curl http://localhost:3001/health
curl http://localhost:5678/healthz

# Test key workflows
open http://localhost:5678
# Login and test a workflow execution
```

**Backward Compatibility** (older import into newer system):
```bash
# May require database migrations
npm run team:import
# Answer 'y' to version warning

# Check for migration errors
docker logs pilotpros-backend-dev --tail 50
docker logs pilotpros-automation-engine-dev --tail 50

# Manual migration if needed
npm run db:migrate 2>/dev/null || echo "No migration script"
```

**If incompatible:**
```bash
# Checkout matching version
git checkout v1.0.0  # Match export version

# Reset environment
npm run docker:clean
npm run dev

# Retry import
npm run team:import

# Upgrade after import
git checkout main
npm run docker:reset  # Rebuilds with new version
```

## 🔍 Runtime Issues

### Issue: n8n Not Responding After Import

**Symptoms:**
```bash
❌ Errore verifica n8n: connection refused
🌐 n8n: http://localhost:5678 not accessible
```

**Diagnosis:**
```bash
# Check n8n container
docker exec pilotpros-automation-engine-dev ps aux | grep n8n

# Check n8n startup logs
docker logs pilotpros-automation-engine-dev --tail 100

# Test internal connectivity
docker exec pilotpros-automation-engine-dev curl -I http://localhost:5678/healthz
```

**Resolution:**
```bash
# Give n8n more time (can take 2+ minutes)
sleep 120

# Check again
curl -I http://localhost:5678/healthz

# If still failing, restart n8n
docker restart pilotpros-automation-engine-dev

# Monitor n8n startup
docker logs -f pilotpros-automation-engine-dev &
sleep 120
pkill -f "docker logs"

# Test n8n functionality
open http://localhost:5678
# Login: admin / pilotpros_admin_2025
```

**Advanced n8n debugging:**
```bash
# Enter n8n container
docker exec -it pilotpros-automation-engine-dev /bin/sh

# Check n8n process
ps aux | grep n8n

# Check n8n configuration
ls -la /home/node/.n8n/

# Check database connection from n8n
n8n user-management:list  # Should show admin user

# Exit container
exit

# Reset n8n data if corrupted
docker stop pilotpros-automation-engine-dev
docker volume rm pilotpros_n8n_dev_data
npm run dev
npm run n8n:auto-setup
```

---

### Issue: Data Inconsistency After Import

**Symptoms:**
```bash
✅ Import completed but workflows missing in UI
✅ Database count OK but n8n shows empty
```

**Diagnosis:**
```bash
# Check database directly
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "SELECT id, name FROM n8n.workflow_entity LIMIT 5"

# Check n8n API
curl -u admin:pilotpros_admin_2025 http://localhost:5678/api/v1/workflows | jq '.data | length'

# Check n8n cache/UI
open http://localhost:5678
# F5 to refresh browser cache
```

**Resolution:**
```bash
# Clear n8n cache
docker restart pilotpros-automation-engine-dev

# Clear browser cache
# Chrome: Cmd+Shift+R (hard refresh)
# Safari: Cmd+Option+R

# Verify API vs Database consistency
DB_COUNT=$(docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -t -c "SELECT COUNT(*) FROM n8n.workflow_entity" | tr -d ' ')
API_COUNT=$(curl -s -u admin:pilotpros_admin_2025 http://localhost:5678/api/v1/workflows | jq '.data | length')

echo "Database: $DB_COUNT, API: $API_COUNT"

# If mismatch, restart entire stack
if [ "$DB_COUNT" != "$API_COUNT" ]; then
    npm run docker:reset
fi
```

**Force data refresh:**
```bash
# Complete environment reset
npm run docker:stop
sleep 10
npm run dev
sleep 60

# Verify data consistency
curl -u admin:pilotpros_admin_2025 http://localhost:5678/api/v1/workflows | jq '.data | length'
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -t -c "SELECT COUNT(*) FROM n8n.workflow_entity"
```

## 🔍 Performance Issues

### Issue: Slow Export/Import Operations

**Symptoms:**
```bash
⏳ Export taking > 5 minutes
⏳ Import taking > 10 minutes
```

**Diagnosis:**
```bash
# Check system load
top | head -10

# Check Docker resource usage
docker stats --no-stream

# Check disk I/O
iostat -d 2 5 2>/dev/null || echo "Install iostat for disk metrics"

# Check available memory
vm_stat | grep "Pages free\|Pages active\|Pages inactive"
```

**Resolution:**
```bash
# Close resource-heavy applications
pkill -f "Google Chrome"
pkill -f "Slack"  
pkill -f "VS Code"

# Increase Docker resources
# Docker Desktop > Settings > Resources
# Memory: 8GB+, CPUs: 4+, Disk: 100GB+

# Clean up disk space
docker system prune -f
find team-sync-exports/ -name "*.tar.gz" -mtime +7 -delete

# Restart Docker Desktop
osascript -e 'quit app "Docker Desktop"'
sleep 10
open -a Docker
sleep 30
```

**Optimize export/import:**
```bash
# Use faster compression
export GZIP=-1  # Fastest compression
npm run team:export

# Parallel operations (future enhancement)
# Currently sequential for data integrity
```

### Issue: Large Archive Sizes

**Symptoms:**
```bash
📁 Archive: 500MB+ (expected: 10-50MB)
💾 Taking too long to transfer
```

**Diagnosis:**
```bash
# Check database size
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "SELECT pg_size_pretty(pg_database_size('pilotpros_db'))"

# Check execution history
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "SELECT COUNT(*) FROM n8n.execution_entity"

# Check large tables
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname IN ('n8n','pilotpros') ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10"
```

**Resolution:**
```bash
# Clean execution history (safe)
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "DELETE FROM n8n.execution_entity WHERE \"stoppedAt\" < NOW() - INTERVAL '7 days'"

# Clean binary data (DANGER: may break workflows)
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "DELETE FROM n8n.binary_data_entity WHERE \"createdAt\" < NOW() - INTERVAL '7 days'"

# Vacuum database
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "VACUUM FULL"

# Re-export after cleanup
npm run team:export
```

## 📊 Monitoring and Diagnostics

### Health Check Script

Create `scripts/health-check.js`:
```bash
cat > scripts/health-check.js << 'EOF'
#!/usr/bin/env node

import { execSync } from 'child_process';
import chalk from 'chalk';

const checks = {
  docker: () => {
    try {
      execSync('docker ps', { stdio: 'pipe' });
      return { status: '✅', message: 'Docker running' };
    } catch {
      return { status: '❌', message: 'Docker not running' };
    }
  },
  
  containers: () => {
    try {
      const output = execSync('docker ps --filter "name=pilotpros" --format "{{.Names}}"', { encoding: 'utf8' });
      const containers = output.trim().split('\n').filter(Boolean);
      return { status: '✅', message: `${containers.length} containers running` };
    } catch {
      return { status: '❌', message: 'No PilotPro containers' };
    }
  },
  
  database: () => {
    try {
      execSync('docker exec pilotpros-postgres-dev pg_isready -U pilotpros_user -d pilotpros_db', { stdio: 'pipe' });
      return { status: '✅', message: 'Database ready' };
    } catch {
      return { status: '❌', message: 'Database not ready' };
    }
  },
  
  n8n: () => {
    try {
      execSync('docker exec pilotpros-automation-engine-dev wget -qO- "http://localhost:5678/healthz"', { stdio: 'pipe' });
      return { status: '✅', message: 'n8n healthy' };
    } catch {
      return { status: '❌', message: 'n8n not responding' };
    }
  }
};

console.log(chalk.blue('🔍 PilotProOS Health Check\n'));

for (const [name, check] of Object.entries(checks)) {
  const result = check();
  console.log(`${result.status} ${name.padEnd(12)} ${result.message}`);
}
EOF

chmod +x scripts/health-check.js
```

**Usage:**
```bash
# Run health check
node scripts/health-check.js

# Add to package.json
npm pkg set scripts.health="node scripts/health-check.js"

# Use it
npm run health
```

### Log Analysis

**Comprehensive log viewing:**
```bash
# View all service logs
docker-compose -f docker-compose.dev.yml logs --tail 100

# Follow specific service logs
docker logs -f pilotpros-postgres-dev
docker logs -f pilotpros-automation-engine-dev  
docker logs -f pilotpros-backend-dev

# Search logs for errors
docker-compose -f docker-compose.dev.yml logs 2>&1 | grep -i error

# Export logs for analysis
docker-compose -f docker-compose.dev.yml logs > system-logs-$(date +%Y%m%d-%H%M%S).txt
```

**n8n specific debugging:**
```bash
# Enable n8n debug logging
docker exec pilotpros-automation-engine-dev sh -c 'echo "N8N_LOG_LEVEL=debug" >> /home/node/.n8n/.env'
docker restart pilotpros-automation-engine-dev

# View n8n internal logs
docker exec pilotpros-automation-engine-dev find /home/node/.n8n -name "*.log" -exec cat {} \;
```

## 🆘 Emergency Recovery

### Complete System Reset

**When all else fails:**
```bash
#!/bin/bash
echo "🚨 Emergency Recovery - Complete System Reset"

# Stop all PilotPro containers
docker stop $(docker ps -q --filter "name=pilotpros") 2>/dev/null || true

# Remove all PilotPro containers
docker rm $(docker ps -aq --filter "name=pilotpros") 2>/dev/null || true

# Remove all PilotPro volumes (DANGER: all data lost)
docker volume rm $(docker volume ls -q | grep pilotpros) 2>/dev/null || true

# Clean Docker system
docker system prune -f

# Remove node_modules for fresh install
rm -rf node_modules frontend/node_modules backend/node_modules ai-agent/node_modules

# Fresh install
npm run setup

# Start system
npm run dev

echo "✅ Emergency recovery completed"
echo "🔄 System will be ready in ~2 minutes"
echo "⚠️  All previous data lost - restore from team export if needed"
```

### Data Recovery from Backup

**If you have team export archive:**
```bash
# After emergency reset, restore data
npm run team:import

# If archive corrupted, ask team for fresh export
# Team member runs:
# npm run team:export
```

### Manual Database Recovery

**Advanced database recovery:**
```bash
# Create manual backup before recovery
docker exec pilotpros-postgres-dev pg_dump -U pilotpros_user -d pilotpros_db > emergency-backup.sql

# Drop corrupted database
docker exec pilotpros-postgres-dev psql -U pilotpros_user -c "DROP DATABASE pilotpros_db"

# Recreate database
docker exec pilotpros-postgres-dev psql -U pilotpros_user -c "CREATE DATABASE pilotpros_db"

# Restore from team export
docker exec -i pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db < team-sync-exports/export-*/database-complete.sql

# Verify recovery
docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "SELECT COUNT(*) FROM n8n.workflow_entity"
```

## 📞 Support Escalation

### When to Escalate

**Escalate if:**
- System reset doesn't resolve issue
- Data corruption persists after multiple recovery attempts
- Docker/system-level issues beyond application scope
- Performance issues persist after resource optimization
- Security concerns with data exports

### Information to Collect

**Before escalating, collect:**
```bash
# System information
uname -a > system-info.txt
docker version >> system-info.txt
docker info >> system-info.txt

# Application information  
cat package.json | grep version >> system-info.txt
git log --oneline -5 >> system-info.txt
git status >> system-info.txt

# Logs
docker-compose -f docker-compose.dev.yml logs --tail 500 > application-logs.txt
docker ps -a > container-status.txt

# Health check
npm run health > health-check.txt 2>&1 || echo "Health check failed" > health-check.txt
```

### Contact Information

**Internal Support:**
- Development Team: Slack #pilotpros-dev
- DevOps Team: Slack #pilotpros-infra  
- Emergency: development-team@pilotpro.com

**External Support:**
- Docker: https://docs.docker.com/support/
- n8n Community: https://community.n8n.io/
- PostgreSQL: https://www.postgresql.org/support/

---

## 📚 Related Documentation

- **[team-sync-system.md](./team-sync-system.md)** - Complete technical documentation
- **[team-sync-api.md](./team-sync-api.md)** - API reference  
- **[../TEAM_WORKFLOW.md](../TEAM_WORKFLOW.md)** - User workflow guide
- **[../CLAUDE.md](../CLAUDE.md)** - Project overview and commands

---

**Troubleshooting Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**Support Level**: Production Ready