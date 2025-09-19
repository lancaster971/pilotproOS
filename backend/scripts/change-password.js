#!/usr/bin/env node

/**
 * Script to change user password
 * Usage: node change-password.js <email> <new-password>
 */

import bcrypt from 'bcryptjs';
import postgres from 'postgres';
import * as dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(__dirname, '../../.env') });

const connectionString = process.env.DATABASE_URL ||
  `postgresql://${process.env.DB_USER || 'pilotpros_user'}:${process.env.DB_PASSWORD || 'pilotpros_secure_pass_2025'}@${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || '5432'}/${process.env.DB_NAME || 'pilotpros_db'}`;

async function changePassword(email, newPassword) {
  const sql = postgres(connectionString);

  try {
    // Check if user exists
    const users = await sql`
      SELECT id, email FROM pilotpros.users WHERE email = ${email}
    `;

    if (users.length === 0) {
      console.error(`❌ User not found: ${email}`);
      process.exit(1);
    }

    const user = users[0];
    console.log(`✅ Found user: ${user.email} (ID: ${user.id})`);

    // Generate new password hash
    console.log('🔐 Generating new password hash...');
    const saltRounds = 12;
    const newHash = await bcrypt.hash(newPassword, saltRounds);
    console.log(`📝 New hash: ${newHash}`);

    // Update password in database
    console.log('💾 Updating password in database...');
    await sql`
      UPDATE pilotpros.users
      SET password_hash = ${newHash}, updated_at = CURRENT_TIMESTAMP
      WHERE email = ${email}
    `;

    console.log(`✅ Password successfully changed for ${email}`);
    console.log('\n🔑 Login credentials:');
    console.log(`   Email: ${email}`);
    console.log(`   Password: ${newPassword}`);

    // Test the new hash
    console.log('\n🧪 Testing new password hash...');
    const testResult = await bcrypt.compare(newPassword, newHash);
    console.log(`   Hash validation: ${testResult ? '✅ PASSED' : '❌ FAILED'}`);

  } catch (error) {
    console.error('❌ Error changing password:', error);
    process.exit(1);
  } finally {
    await sql.end();
  }
}

// Main execution
const args = process.argv.slice(2);

if (args.length < 2) {
  console.log('Usage: node change-password.js <email> <new-password>');
  console.log('Example: node change-password.js tiziano@gmail.com NewPassword123!');
  process.exit(1);
}

const [email, newPassword] = args;

// Validate password strength
if (newPassword.length < 8) {
  console.error('❌ Password must be at least 8 characters long');
  process.exit(1);
}

console.log('🔄 PilotProOS Password Change Tool');
console.log('==================================');
console.log(`📧 Email: ${email}`);
console.log(`🔑 New Password: ${newPassword}`);
console.log('');

changePassword(email, newPassword).catch(console.error);