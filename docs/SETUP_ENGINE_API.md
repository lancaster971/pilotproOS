# 🔌 PilotProSetUpEngine - API Reference

**Component**: Setup Engine API  
**Version**: 1.0.0  
**Purpose**: Programmatic Installation and Management Interface  

---

## 📋 Overview

The PilotProSetUpEngine API provides RESTful endpoints for programmatic deployment, configuration, and management of PilotProOS instances. This enables automated deployment pipelines, multi-tenant installations, and integration with existing infrastructure management tools.

---

## 🔐 Authentication

All API endpoints require authentication using API keys or JWT tokens.

### API Key Authentication

```http
Authorization: Bearer YOUR_API_KEY
```

### JWT Authentication

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🚀 Installation Endpoints

### POST /api/setup/install

Initiates a new PilotProOS installation.

**Request:**

```http
POST /api/setup/install
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "business": {
    "name": "Acme Corporation",
    "domain": "acme.com",
    "email": "admin@acme.com",
    "admin_name": "John Smith"
  },
  "configuration": {
    "timezone": "America/New_York",
    "language": "en",
    "currency": "USD",
    "backup_schedule": "0 2 * * *"
  },
  "infrastructure": {
    "server_ip": "192.168.1.100",
    "ssh_key": "ssh-rsa AAAAB3NzaC1yc2...",
    "docker_registry": "docker.io",
    "use_ssl": true
  },
  "modules": {
    "ai_agent": true,
    "analytics": true,
    "mobile": false,
    "api_gateway": true
  },
  "advanced": {
    "custom_branding": {
      "logo_url": "https://acme.com/logo.png",
      "primary_color": "#1976D2",
      "secondary_color": "#424242"
    },
    "integrations": [
      {
        "type": "microsoft_365",
        "tenant_id": "xxx-xxx-xxx",
        "client_id": "yyy-yyy-yyy"
      }
    ]
  }
}
```

**Response (Success):**

```json
{
  "status": "success",
  "installation_id": "inst_1234567890",
  "duration": "4m 32s",
  "platform": {
    "url": "https://acme.com",
    "admin_url": "https://acme.com/admin",
    "api_url": "https://acme.com/api",
    "webhook_url": "https://acme.com/webhook"
  },
  "credentials": {
    "admin_email": "admin@acme.com",
    "temporary_password": "TempPass123!",
    "api_key": "pk_live_1234567890abcdef",
    "jwt_secret": "jwt_secret_key_encrypted"
  },
  "services": {
    "database": {
      "status": "healthy",
      "version": "16.1",
      "connection_string": "postgresql://business_admin@business-database:5432/business_platform"
    },
    "automation_engine": {
      "status": "healthy",
      "version": "1.108.1",
      "workflows_enabled": 0
    },
    "api": {
      "status": "healthy",
      "version": "1.0.0",
      "endpoints_available": 47
    },
    "dashboard": {
      "status": "healthy",
      "version": "1.0.0",
      "modules_loaded": ["core", "ai_agent", "analytics"]
    }
  },
  "next_steps": [
    "Login at https://acme.com with temporary password",
    "Change password on first login",
    "Configure email settings",
    "Import existing workflows (optional)",
    "Set up team members"
  ]
}
```

**Response (Error):**

```json
{
  "status": "error",
  "error_code": "INSUFFICIENT_RESOURCES",
  "message": "Server does not meet minimum requirements",
  "details": {
    "required": {
      "cpu_cores": 2,
      "memory_gb": 4,
      "disk_gb": 20
    },
    "available": {
      "cpu_cores": 1,
      "memory_gb": 2,
      "disk_gb": 15
    }
  },
  "suggestions": [
    "Upgrade server resources",
    "Use minimal installation profile",
    "Consider cloud deployment option"
  ]
}
```

---

### GET /api/setup/status/:installation_id

Check the status of an ongoing installation.

**Request:**

```http
GET /api/setup/status/inst_1234567890
Authorization: Bearer YOUR_API_KEY
```

**Response:**

```json
{
  "installation_id": "inst_1234567890",
  "status": "in_progress",
  "progress": 65,
  "current_step": "Configuring automation engine",
  "steps_completed": [
    {
      "name": "System verification",
      "status": "completed",
      "duration": "10s"
    },
    {
      "name": "Docker installation",
      "status": "completed",
      "duration": "45s"
    },
    {
      "name": "Image download",
      "status": "completed",
      "duration": "90s"
    },
    {
      "name": "Database setup",
      "status": "completed",
      "duration": "30s"
    }
  ],
  "steps_remaining": [
    {
      "name": "Automation engine configuration",
      "estimated_duration": "60s"
    },
    {
      "name": "SSL certificate setup",
      "estimated_duration": "30s"
    },
    {
      "name": "Health verification",
      "estimated_duration": "15s"
    }
  ],
  "estimated_completion": "2024-01-15T14:35:00Z",
  "logs_url": "/api/setup/logs/inst_1234567890"
}
```

---

### POST /api/setup/validate

Pre-validate installation requirements before attempting installation.

**Request:**

```http
POST /api/setup/validate
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "server": {
    "ip": "192.168.1.100",
    "ssh_key": "ssh-rsa AAAAB3NzaC1yc2..."
  },
  "requirements": {
    "profile": "standard"
  }
}
```

**Response:**

```json
{
  "valid": true,
  "checks": {
    "connectivity": {
      "status": "pass",
      "latency_ms": 15
    },
    "operating_system": {
      "status": "pass",
      "detected": "Ubuntu 22.04 LTS"
    },
    "resources": {
      "status": "pass",
      "cpu_cores": 4,
      "memory_gb": 8,
      "disk_gb": 100
    },
    "docker": {
      "status": "not_installed",
      "action": "will_install"
    },
    "ports": {
      "status": "pass",
      "available": [80, 443, 3000, 3001, 5432, 5678]
    },
    "dns": {
      "status": "pass",
      "domain_resolves": true
    }
  },
  "warnings": [],
  "estimated_install_time": "4m 30s"
}
```

---

## 🔧 Configuration Endpoints

### PUT /api/config/update

Update configuration for an existing installation.

**Request:**

```http
PUT /api/config/update
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "installation_id": "inst_1234567890",
  "updates": {
    "business": {
      "name": "Acme Corporation Ltd"
    },
    "modules": {
      "mobile": true
    },
    "backup_schedule": "0 3 * * *"
  }
}
```

**Response:**

```json
{
  "status": "success",
  "updated_fields": [
    "business.name",
    "modules.mobile",
    "backup_schedule"
  ],
  "restart_required": false,
  "effective_immediately": true
}
```

---

### GET /api/config/export/:installation_id

Export complete configuration for backup or migration.

**Request:**

```http
GET /api/config/export/inst_1234567890
Authorization: Bearer YOUR_API_KEY
```

**Response:**

```json
{
  "export_id": "exp_9876543210",
  "installation_id": "inst_1234567890",
  "timestamp": "2024-01-15T14:00:00Z",
  "configuration": {
    "business": { /* ... */ },
    "infrastructure": { /* ... */ },
    "modules": { /* ... */ },
    "advanced": { /* ... */ }
  },
  "encrypted_secrets": {
    "database_password": "enc:AES256:...",
    "jwt_secret": "enc:AES256:...",
    "api_keys": "enc:AES256:..."
  },
  "download_url": "/api/config/download/exp_9876543210",
  "expires_at": "2024-01-16T14:00:00Z"
}
```

---

## 🏥 Health & Monitoring Endpoints

### GET /api/health/:installation_id

Get health status of all services.

**Request:**

```http
GET /api/health/inst_1234567890
Authorization: Bearer YOUR_API_KEY
```

**Response:**

```json
{
  "overall_status": "healthy",
  "timestamp": "2024-01-15T14:00:00Z",
  "services": {
    "business_database": {
      "status": "healthy",
      "uptime": "5d 14h 23m",
      "metrics": {
        "connections": 15,
        "size_mb": 1247,
        "queries_per_second": 42
      }
    },
    "automation_engine": {
      "status": "healthy",
      "uptime": "5d 14h 22m",
      "metrics": {
        "workflows_active": 31,
        "executions_today": 1523,
        "success_rate": 0.997
      }
    },
    "business_api": {
      "status": "healthy",
      "uptime": "5d 14h 22m",
      "metrics": {
        "requests_per_minute": 142,
        "response_time_ms": 45,
        "error_rate": 0.001
      }
    },
    "business_dashboard": {
      "status": "healthy",
      "uptime": "5d 14h 22m",
      "metrics": {
        "active_sessions": 12,
        "page_load_time_ms": 230
      }
    }
  },
  "resources": {
    "cpu_usage_percent": 35,
    "memory_usage_percent": 62,
    "disk_usage_percent": 28,
    "network_io_mbps": 2.4
  },
  "alerts": []
}
```

---

### POST /api/health/diagnose

Run diagnostic checks on an installation.

**Request:**

```http
POST /api/health/diagnose
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "installation_id": "inst_1234567890",
  "checks": ["database", "network", "ssl", "performance"],
  "deep_scan": true
}
```

**Response:**

```json
{
  "diagnosis_id": "diag_5555555555",
  "status": "completed",
  "duration": "45s",
  "results": {
    "database": {
      "status": "healthy",
      "checks": {
        "connectivity": "pass",
        "schema_integrity": "pass",
        "index_efficiency": "pass",
        "backup_status": "pass"
      }
    },
    "network": {
      "status": "healthy",
      "checks": {
        "internal_connectivity": "pass",
        "external_connectivity": "pass",
        "dns_resolution": "pass",
        "firewall_rules": "pass"
      }
    },
    "ssl": {
      "status": "warning",
      "checks": {
        "certificate_valid": "pass",
        "certificate_expiry": "warning",
        "cipher_strength": "pass",
        "hsts_enabled": "pass"
      },
      "warnings": [
        "SSL certificate expires in 15 days"
      ]
    },
    "performance": {
      "status": "healthy",
      "metrics": {
        "api_response_p95": "120ms",
        "database_query_p95": "50ms",
        "workflow_execution_p95": "3.2s"
      }
    }
  },
  "recommendations": [
    "Renew SSL certificate before expiry",
    "Consider adding database read replica for better performance"
  ]
}
```

---

## 🔄 Maintenance Endpoints

### POST /api/maintenance/update

Trigger platform update.

**Request:**

```http
POST /api/maintenance/update
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "installation_id": "inst_1234567890",
  "target_version": "1.1.0",
  "strategy": "rolling",
  "backup_first": true,
  "maintenance_window": {
    "start": "2024-01-16T02:00:00Z",
    "duration_minutes": 30
  }
}
```

**Response:**

```json
{
  "update_id": "upd_7777777777",
  "status": "scheduled",
  "current_version": "1.0.0",
  "target_version": "1.1.0",
  "scheduled_at": "2024-01-16T02:00:00Z",
  "estimated_duration": "15m",
  "rollback_available": true,
  "changes": [
    "Security patches",
    "Performance improvements",
    "New AI agent features",
    "Bug fixes"
  ]
}
```

---

### POST /api/maintenance/backup

Create backup of installation.

**Request:**

```http
POST /api/maintenance/backup
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "installation_id": "inst_1234567890",
  "type": "full",
  "encryption": true,
  "destination": "s3://backups/pilotpro/"
}
```

**Response:**

```json
{
  "backup_id": "bkp_8888888888",
  "status": "in_progress",
  "type": "full",
  "size_estimate_mb": 2048,
  "components": [
    "database",
    "workflows",
    "configurations",
    "user_data",
    "files"
  ],
  "encryption": "AES-256",
  "destination": "s3://backups/pilotpro/bkp_8888888888/",
  "estimated_completion": "2024-01-15T14:15:00Z"
}
```

---

### POST /api/maintenance/restore

Restore from backup.

**Request:**

```http
POST /api/maintenance/restore
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "installation_id": "inst_1234567890",
  "backup_id": "bkp_8888888888",
  "components": ["database", "workflows"],
  "verify_integrity": true
}
```

**Response:**

```json
{
  "restore_id": "rst_9999999999",
  "status": "validating",
  "backup_id": "bkp_8888888888",
  "validation": {
    "integrity_check": "pass",
    "compatibility_check": "pass",
    "size_mb": 1536
  },
  "estimated_duration": "10m",
  "service_downtime_required": true,
  "confirmation_required": true,
  "confirmation_token": "confirm_rst_9999999999"
}
```

---

## 🗑️ Decommission Endpoints

### DELETE /api/setup/uninstall

Completely remove an installation.

**Request:**

```http
DELETE /api/setup/uninstall
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "installation_id": "inst_1234567890",
  "create_final_backup": true,
  "remove_all_data": true,
  "confirmation": "DELETE-inst_1234567890"
}
```

**Response:**

```json
{
  "status": "success",
  "uninstall_id": "uni_0000000000",
  "installation_id": "inst_1234567890",
  "final_backup": {
    "created": true,
    "backup_id": "bkp_final_0000",
    "download_url": "/api/backup/download/bkp_final_0000",
    "expires_at": "2024-01-22T14:00:00Z"
  },
  "removed": [
    "Docker containers",
    "Docker images",
    "Docker volumes",
    "Database",
    "Configuration files",
    "SSL certificates",
    "Log files"
  ],
  "duration": "2m 15s"
}
```

---

## 🔔 Webhook Events

The Setup Engine can send webhook notifications for various events.

### Installation Events

```json
{
  "event": "installation.completed",
  "timestamp": "2024-01-15T14:05:00Z",
  "data": {
    "installation_id": "inst_1234567890",
    "domain": "acme.com",
    "duration": "4m 32s",
    "status": "success"
  }
}
```

### Health Events

```json
{
  "event": "health.alert",
  "timestamp": "2024-01-15T15:00:00Z",
  "data": {
    "installation_id": "inst_1234567890",
    "service": "business_database",
    "alert": "High memory usage",
    "severity": "warning",
    "metrics": {
      "memory_usage_percent": 85
    }
  }
}
```

### Update Events

```json
{
  "event": "update.completed",
  "timestamp": "2024-01-16T02:15:00Z",
  "data": {
    "installation_id": "inst_1234567890",
    "update_id": "upd_7777777777",
    "previous_version": "1.0.0",
    "new_version": "1.1.0",
    "duration": "15m",
    "status": "success"
  }
}
```

---

## 🔑 Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `AUTH_INVALID` | Invalid API key or token | Check authentication credentials |
| `INSTALLATION_NOT_FOUND` | Installation ID does not exist | Verify installation ID |
| `INSUFFICIENT_RESOURCES` | Server doesn't meet requirements | Upgrade server or use minimal profile |
| `DOMAIN_CONFLICT` | Domain already in use | Use different domain or remove existing |
| `NETWORK_ERROR` | Cannot connect to server | Check network connectivity and firewall |
| `DOCKER_ERROR` | Docker operation failed | Check Docker daemon status |
| `DATABASE_ERROR` | Database operation failed | Check database connectivity |
| `SSL_ERROR` | SSL certificate issue | Verify domain ownership and DNS |
| `BACKUP_ERROR` | Backup operation failed | Check storage permissions and space |
| `UPDATE_ERROR` | Update operation failed | Check logs and rollback if needed |

---

## 📊 Rate Limits

| Endpoint Type | Rate Limit | Window |
|--------------|------------|--------|
| Installation | 10 requests | 1 hour |
| Configuration | 100 requests | 1 hour |
| Health | 1000 requests | 1 hour |
| Maintenance | 20 requests | 1 hour |
| Decommission | 5 requests | 1 hour |

---

## 🌐 SDKs & Libraries

Official SDKs are available for programmatic access:

### Node.js

```javascript
const PilotProSetup = require('@pilotpro/setup-engine');

const client = new PilotProSetup({
  apiKey: 'YOUR_API_KEY'
});

// Install new instance
const installation = await client.install({
  business: {
    name: 'Acme Corporation',
    domain: 'acme.com',
    email: 'admin@acme.com'
  }
});

// Check health
const health = await client.health(installation.id);
```

### Python

```python
from pilotpro_setup import SetupEngine

client = SetupEngine(api_key='YOUR_API_KEY')

# Install new instance
installation = client.install({
    'business': {
        'name': 'Acme Corporation',
        'domain': 'acme.com',
        'email': 'admin@acme.com'
    }
})

# Check health
health = client.health(installation['id'])
```

### CLI Tool

```bash
# Install PilotPro CLI
npm install -g @pilotpro/cli

# Configure API key
pilotpro config set api_key YOUR_API_KEY

# Install new instance
pilotpro install --domain acme.com --email admin@acme.com

# Check health
pilotpro health --installation inst_1234567890

# Update platform
pilotpro update --installation inst_1234567890 --version 1.1.0
```

---

## 📝 Conclusion

The PilotProSetUpEngine API provides comprehensive programmatic control over the installation, configuration, and management of PilotProOS instances. With its RESTful design, comprehensive error handling, and extensive webhook support, it enables seamless integration into existing DevOps pipelines and infrastructure management systems while maintaining the core principle of complete technology abstraction.