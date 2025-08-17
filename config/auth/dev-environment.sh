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

echo "🤖 Starting AI agent..."
npm run dev:ai-agent &

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
