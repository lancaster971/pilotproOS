#!/bin/bash

# PilotProOS Developer Access Setup
echo "🔧 Setting up Developer Access to n8n"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create config directory if not exists
mkdir -p config/auth

echo "📋 Creating developer authentication..."

# Generate htpasswd for developers
echo "Enter developer username:"
read -r USERNAME

echo "Enter password for $USERNAME:"
read -rs PASSWORD

# Create htpasswd entry
echo "$PASSWORD" | htpasswd -c -i config/auth/.htpasswd-developers "$USERNAME"

echo -e "${GREEN}✅ Developer credentials created${NC}"

# Create VPN access instructions
cat > config/auth/developer-access-instructions.md << 'EOF'
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
EOF

echo -e "${GREEN}✅ Developer access instructions created${NC}"

# Create development environment setup
cat > config/auth/dev-environment.sh << 'EOF'
#!/bin/bash

# PilotProOS Development Environment Setup
echo "🚀 Starting PilotProOS Development Environment"

# Start all services
echo "📊 Starting PostgreSQL..."
brew services start postgresql@16

echo "🔧 Starting n8n workflow engine..."
npm run n8n:start &

echo "⚙️ Starting backend API..."
npm run dev:backend &

echo "🎨 Starting frontend interface..."
npm run dev:frontend &


echo ""
echo "✅ All services started!"
echo ""
echo "🌐 Access Points:"
echo "   Business Interface: http://localhost:3000"
echo "   Backend API:        http://localhost:3001"
echo "   AI Agent:           http://localhost:3002"
echo "   n8n Workflows:      http://localhost:5678"
echo "   Database:           psql pilotpros_db"
echo ""
echo "🔑 n8n Credentials:"
echo "   Username: admin"
echo "   Password: pilotpros_admin_2025"
EOF

chmod +x config/auth/dev-environment.sh

echo -e "${GREEN}✅ Development environment script created${NC}"
echo ""
echo "📁 Files created:"
echo "   config/auth/.htpasswd-developers"
echo "   config/auth/developer-access-instructions.md"
echo "   config/auth/dev-environment.sh"
echo ""
echo "🎯 Developer access configured!"
echo "   Production: https://client-domain.com/dev/workflows/"
echo "   Development: http://localhost:5678"
echo ""
echo -e "${YELLOW}⚠️  Remember to:${NC}"
echo "   1. Configure VPN access for production"
echo "   2. Add developer IPs to nginx whitelist"
echo "   3. Copy .htpasswd-developers to production server"
