import bcrypt from 'bcrypt';
import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'pilotpros_db',
  user: process.env.DB_USER || 'pilotpros_user',
  password: process.env.DB_PASSWORD || 'pilotpros_secure_pass_2025',
});

async function resetPassword() {
  try {
    // Generate hash for 'pilotpros2025'
    const password = 'pilotpros2025';
    const saltRounds = 12;
    const hash = await bcrypt.hash(password, saltRounds);
    
    console.log('Generated hash for pilotpros2025:', hash);
    
    // Update all users with the new password
    const users = [
      'admin@pilotpros.dev',
      'tiziano@gmail.com',
      'admin@test.com',
      'test@example.com'
    ];
    
    for (const email of users) {
      await pool.query(
        'UPDATE pilotpros.users SET password_hash = $1 WHERE email = $2',
        [hash, email]
      );
      console.log(`✅ Password updated for ${email}`);
    }
    
    console.log('\n✅ All passwords reset to: pilotpros2025');
    process.exit(0);
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

resetPassword();