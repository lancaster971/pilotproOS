#!/usr/bin/env node

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import sqlite3 from 'sqlite3';
import pkg from 'pg';
const { Client } = pkg;

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Database configurations
const SQLITE_PATH = join(__dirname, '../BU_Hostinger/database.sqlite');
const PG_CONFIG = {
  host: 'localhost',
  port: 5432,
  database: 'pilotpros_db',
  user: 'pilotpros_user',
  password: 'pilotpros_secure_pass_2025'
};

console.log('🔄 Starting execution data migration from SQLite to PostgreSQL...\n');

async function migratExecutions() {
  // Connect to SQLite
  const sqliteDb = new sqlite3.Database(SQLITE_PATH);
  
  // Connect to PostgreSQL
  const pgClient = new Client(PG_CONFIG);
  await pgClient.connect();

  try {
    // Get execution count from SQLite
    const sqliteCount = await new Promise((resolve, reject) => {
      sqliteDb.get("SELECT COUNT(*) as count FROM execution_entity", (err, row) => {
        if (err) reject(err);
        else resolve(row.count);
      });
    });

    console.log(`📊 Found ${sqliteCount} executions in Hostinger SQLite database`);

    // Get execution data from SQLite (limited to recent ones for performance)
    const executions = await new Promise((resolve, reject) => {
      sqliteDb.all(`
        SELECT 
          id, workflowId, mode, retryOf, startedAt, stoppedAt, 
          finished, status, retrySuccessId, waitTill, deletedAt, createdAt
        FROM execution_entity 
        ORDER BY startedAt DESC 
        LIMIT 1000
      `, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });

    console.log(`📦 Migrating ${executions.length} most recent executions...`);

    let imported = 0;
    let errors = 0;

    for (const execution of executions) {
      try {
        // Check if execution already exists
        const existingResult = await pgClient.query(
          'SELECT id FROM n8n.execution_entity WHERE id = $1',
          [execution.id]
        );

        if (existingResult.rows.length > 0) {
          console.log(`⚠️ Execution ${execution.id} already exists, skipping`);
          continue;
        }

        // Insert execution into PostgreSQL
        await pgClient.query(`
          INSERT INTO n8n.execution_entity (
            id, "workflowId", mode, "retryOf", "startedAt", "stoppedAt",
            finished, status, "retrySuccessId", "waitTill", "deletedAt", "createdAt"
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        `, [
          execution.id,
          execution.workflowId,
          execution.mode,
          execution.retryOf,
          execution.startedAt ? new Date(execution.startedAt) : null,
          execution.stoppedAt ? new Date(execution.stoppedAt) : null,
          execution.finished,
          execution.status,
          execution.retrySuccessId,
          execution.waitTill ? new Date(execution.waitTill) : null,
          execution.deletedAt ? new Date(execution.deletedAt) : null,
          execution.createdAt ? new Date(execution.createdAt) : new Date()
        ]);

        imported++;
        if (imported % 100 === 0) {
          console.log(`✅ Imported ${imported} executions...`);
        }

      } catch (error) {
        errors++;
        console.log(`❌ Failed to import execution ${execution.id}: ${error.message}`);
      }
    }

    console.log(`\n🎉 Migration completed!`);
    console.log(`✅ Successfully imported: ${imported} executions`);
    console.log(`❌ Errors: ${errors}`);

  } catch (error) {
    console.error('💥 Migration failed:', error);
  } finally {
    sqliteDb.close();
    await pgClient.end();
  }
}

// Check if sqlite3 is available
try {
  migratExecutions();
} catch (error) {
  console.log('❌ sqlite3 module not found. Installing...');
  console.log('Please run: npm install sqlite3');
  process.exit(1);
}