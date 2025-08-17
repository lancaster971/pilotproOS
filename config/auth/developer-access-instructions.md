# PilotProOS Developer Access

## 🔧 Workflow Configuration Access

### Production Access
- **URL**: https://client-domain.com/dev/workflows/
- **Auth**: Developer credentials (htpasswd)
- **Network**: VPN or office network required

### Development Access  
- **URL**: http://localhost:5678
- **Auth**: admin / pilotpros_admin_2025
- **Network**: Local development only

## 🛡️ Security Layers

1. **IP Whitelist**: Only developer networks
2. **Authentication**: Username/password required  
3. **Hidden from Client**: Never exposed in business interface
4. **Encrypted**: HTTPS only in production

## 🚀 Usage Workflow

1. **Connect VPN** (production) or **start local dev**
2. **Access n8n editor** via developer URL
3. **Configure workflows** using business terminology
4. **Test execution** via business API endpoints
5. **Deploy** through automated scripts

## 📝 Important Notes

- **Always use business terminology** in workflow names
- **Never expose technical details** to client interface
- **Test workflows** through backend API translation layer
- **Document business logic** in process templates table

## 🔌 API Integration

Workflows created in n8n are accessed by backend via:
- Database queries to `n8n.workflow_entity`
- REST API calls to `http://localhost:5678/api/v1/`
- Webhook triggers at `http://localhost:5678/webhook/[id]`

All technical details are translated to business language by backend middleware.
