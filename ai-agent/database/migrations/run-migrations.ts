#!/usr/bin/env node
/**
 * Database Migration Runner
 * 
 * Esegue tutte le migrazioni del database in ordine
 */

import { DatabaseConnection } from '../connection.js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runMigrations() {
  console.log('🔄 Starting database migrations...');
  
  const db = DatabaseConnection.getInstance();
  
  try {
    // Connect to database
    await db.connect();
    console.log('✅ Connected to database');
    
    // Create migrations table if not exists
    await db.query(`
      CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(255) PRIMARY KEY,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Get list of migration files
    const migrationFiles = await fs.readdir(__dirname);
    const sqlFiles = migrationFiles
      .filter(f => f.endsWith('.sql'))
      .sort(); // Ensure they run in order
    
    console.log(`Found ${sqlFiles.length} migration files`);
    
    // Run each migration
    for (const file of sqlFiles) {
      const version = file.replace('.sql', '');
      
      // Check if migration already executed
      const existing = await db.getOne(
        'SELECT version FROM schema_migrations WHERE version = $1',
        [version]
      ).catch(() => null);
      
      if (existing) {
        console.log(`⏭️  Skipping ${file} (already executed)`);
        continue;
      }
      
      console.log(`📝 Running migration: ${file}`);
      
      // Read and execute migration
      const sqlPath = path.join(__dirname, file);
      const sql = await fs.readFile(sqlPath, 'utf-8');
      
      // Start transaction
      await db.query('BEGIN');
      
      try {
        // Execute migration
        await db.query(sql);
        
        // Record migration
        await db.query(
          'INSERT INTO schema_migrations (version) VALUES ($1)',
          [version]
        );
        
        // Commit transaction
        await db.query('COMMIT');
        
        console.log(`✅ Migration ${file} completed`);
      } catch (error) {
        // Rollback on error
        await db.query('ROLLBACK');
        throw error;
      }
    }
    
    console.log('✅ All migrations completed successfully');
    
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  } finally {
    await db.disconnect();
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runMigrations();
}

export { runMigrations };