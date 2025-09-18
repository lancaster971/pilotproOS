# Stack Controller Security Documentation

## Overview

PilotProOS Stack Controller now includes enterprise-grade security features to protect system access and management operations. This document details the security implementation and usage guidelines.

## 🔐 Security Features

### 1. Authentication Systems

#### CLI Authentication (`./pilotpro`)
- **Purpose**: Protects command-line access to system management
- **Default Password**: `PilotPro2025!`
- **Features**:
  - Password masking during input
  - Session management (30-minute timeout)
  - Failed attempt tracking
  - Account lockout after 3 failed attempts (15 minutes)
  - Persistent sessions across commands

#### Web Dashboard Authentication
- **URL**: `http://localhost:3005`
- **Default Credentials**:
  - Username: `admin`
  - Password: `PilotPro2025!`
- **Features**:
  - JWT token-based authentication
  - Secure login page with professional UI
  - Session persistence
  - Automatic logout on inactivity

### 2. Security Mechanisms

#### Rate Limiting
- **Global Limit**: 100 requests per 15 minutes per IP
- **Purpose**: Prevent brute force attacks and API abuse
- **Applies to**: All API endpoints and web routes

#### Account Lockout
- **CLI**: 3 failed attempts = 15-minute lockout
- **Web**: 5 failed attempts = 15-minute lockout
- **Reset**: Automatic after lockout period expires

#### Session Management
- **Duration**: 30 minutes of inactivity
- **Storage**:
  - CLI: File-based session (`.session` file)
  - Web: JWT tokens with localStorage
- **Extension**: Sessions auto-extend on activity

### 3. Access Logging

All authentication attempts and system access are logged with:
- Timestamp
- IP address
- Username (if provided)
- Success/failure status
- Action performed

## 📁 File Structure

```
PilotProOS/
├── auth.cjs                    # CLI authentication module
├── auth-config.json            # Security configuration
├── .session                    # CLI session storage (auto-generated)
├── .failed-attempts.json       # Failed login tracking (auto-generated)
├── pilotpro.cjs               # Main CLI entry with auth
└── stack-controller/
    ├── src/
    │   ├── auth-middleware.js # Web authentication middleware
    │   └── index.js           # Express app with auth integration
    └── web/
        ├── login.html         # Secure login page
        └── index.html         # Protected dashboard

```

## 🚀 Usage Guide

### First Time Setup

1. **CLI Access**:
   ```bash
   ./pilotpro
   # Enter password: PilotPro2025!
   ```

2. **Web Dashboard Access**:
   - Navigate to `http://localhost:3005`
   - Enter username: `admin`
   - Enter password: `PilotPro2025!`

### Configuration

#### Changing Default Password

1. **Edit `auth-config.json`**:
   ```json
   {
     "defaultPassword": "YourNewPassword",
     "auth": {
       "enabled": true,
       "maxAttempts": 3,
       "lockoutMinutes": 15
     }
   }
   ```

2. **Update Web Dashboard Password**:
   Edit `stack-controller/src/auth-middleware.js`:
   ```javascript
   const DEFAULT_CREDENTIALS = {
     username: 'admin',
     password: 'YourNewPassword'
   };
   ```

#### Disabling Authentication (Development Only)

**CLI**: Set `auth.enabled` to `false` in `auth-config.json`

**Web**: Comment out auth middleware in `stack-controller/src/index.js`:
```javascript
// app.use(authMiddleware);
```

## 🔒 Security Best Practices

### For Production Deployment

1. **Change Default Credentials**
   - MUST change default password before production
   - Use strong passwords (min 12 characters, mixed case, numbers, symbols)

2. **Enable HTTPS**
   - Use SSL certificates for web dashboard
   - Configure nginx reverse proxy with SSL

3. **Restrict Access**
   - Firewall rules to limit access to trusted IPs
   - VPN for remote access
   - Separate credentials for each admin user

4. **Regular Updates**
   - Update dependencies regularly
   - Review access logs weekly
   - Rotate passwords quarterly

### Password Requirements

Recommended password policy:
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- No dictionary words
- No personal information

## 🛠️ API Endpoints

### Authentication Endpoints

#### Login
- **POST** `/api/auth/login`
- **Body**:
  ```json
  {
    "username": "admin",
    "password": "PilotPro2025!"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "token": "jwt-token-here",
    "sessionId": "session-id",
    "user": {
      "username": "admin",
      "role": "admin"
    }
  }
  ```

#### Logout
- **POST** `/api/auth/logout`
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
  ```json
  {
    "success": true,
    "message": "Logged out successfully"
  }
  ```

### Protected Endpoints

All other endpoints require authentication:
- **Headers**: `Authorization: Bearer <token>`
- Or: `X-Session-Id: <sessionId>`

## 🚨 Troubleshooting

### Account Locked

**Problem**: Too many failed login attempts

**Solution**:
1. Wait 15 minutes for automatic unlock
2. Or delete `.failed-attempts.json` (CLI)
3. Or restart Stack Controller container (Web)

### Session Expired

**Problem**: "Authentication required" error

**Solution**:
1. Log in again with credentials
2. Sessions expire after 30 minutes of inactivity

### Forgotten Password

**Problem**: Cannot remember password

**Solution**:
1. Stop the service
2. Edit configuration files (see Configuration section)
3. Restart the service
4. Use new password

### Token Invalid

**Problem**: JWT token rejected

**Solution**:
1. Clear browser localStorage
2. Log in again to get new token
3. Check system time is synchronized

## 🔍 Monitoring & Audit

### Access Logs Location

- **CLI Logs**: Console output with `[AUTH]` prefix
- **Web Logs**: Stack Controller container logs
  ```bash
  docker logs pilotpros-stack-controller
  ```

### Log Format

```
[AUTH] Successful login from 192.168.1.100 for user: admin
[AUTH] Failed login attempt from 192.168.1.101 for user: admin
[AUTH] Account locked for IP: 192.168.1.101
```

### Security Metrics to Monitor

1. **Failed Login Attempts**: Track patterns and potential attacks
2. **Unusual Access Times**: Logins outside business hours
3. **IP Addresses**: New or unexpected locations
4. **Session Duration**: Unusually long sessions
5. **API Request Patterns**: Unusual spike in requests

## 🎯 Quick Reference

### Default Credentials

| System | Username | Password |
|--------|----------|----------|
| CLI | N/A | PilotPro2025! |
| Web Dashboard | admin | PilotPro2025! |
| n8n (internal) | admin | pilotpros_admin_2025 |

### Important Files

| File | Purpose |
|------|---------|
| `auth-config.json` | Main security configuration |
| `.session` | Current CLI session |
| `.failed-attempts.json` | Login attempt tracking |
| `auth-middleware.js` | Web authentication logic |

### Security Checklist

- [ ] Changed default passwords
- [ ] Enabled HTTPS in production
- [ ] Configured firewall rules
- [ ] Set up log monitoring
- [ ] Documented custom credentials securely
- [ ] Tested account lockout
- [ ] Verified rate limiting works
- [ ] Scheduled password rotation

## 📞 Support

For security-related issues:
1. Check this documentation first
2. Review logs for error messages
3. Ensure configuration files are correct
4. Contact system administrator if issues persist

---

**Last Updated**: 2025-09-18
**Version**: 1.0.0
**Security Level**: Enterprise Grade