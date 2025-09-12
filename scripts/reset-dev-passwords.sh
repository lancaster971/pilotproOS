#!/bin/bash
# Reset Development Passwords Script
# Fixes the fucking password reset problem once and for all

echo "🔧 Resetting development passwords..."

# Password hash for 'admin123'
ADMIN_HASH='$2b$12$LQv3c1yqBWVHxkd0LQ4YCOWheHfCo1BEv3Qa7dLbNAUbZM4ZJ.Wv.'

# Update all users with the same password
docker-compose -f docker-compose.dev.yml exec postgres-dev psql -U pilotpros_user -d pilotpros_db -c "
UPDATE users SET password_hash = '$ADMIN_HASH' WHERE 1=1;
"

echo "✅ All users now have password: admin123"
echo ""
echo "Login credentials:"
echo "  tiziano@gmail.com / admin123"
echo "  admin@pilotpros.dev / admin123"
echo "  admin@test.com / admin123"
echo ""