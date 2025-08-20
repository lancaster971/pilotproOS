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

console.log('🧹 Starting CLEAN import from Hostinger SQLite to PostgreSQL...\n');

async function cleanImport() {
  // Extract SQLite first
  console.log('📦 Extracting SQLite database...');
  const { exec } = await import('child_process');
  await new Promise((resolve) => {
    exec(`cd ${join(__dirname, '../BU_Hostinger')} && gunzip -f -k database.sqlite.gz`, resolve);
  });

  // Connect to databases
  const sqliteDb = new sqlite3.Database(SQLITE_PATH);
  const pgClient = new Client(PG_CONFIG);
  await pgClient.connect();

  try {
    console.log('🧹 Cleaning n8n schema in PostgreSQL...');
    
    // Get all n8n tables and clean them
    const tablesResult = await pgClient.query(`
      SELECT tablename FROM pg_tables 
      WHERE schemaname = 'n8n' 
      ORDER BY tablename
    `);
    
    // Disable foreign key checks and truncate all tables
    await pgClient.query('SET session_replication_role = replica;');
    
    for (const table of tablesResult.rows) {
      console.log(`  🗑️ Cleaning n8n.${table.tablename}`);
      await pgClient.query(`TRUNCATE TABLE n8n."${table.tablename}" CASCADE`);
    }
    
    await pgClient.query('SET session_replication_role = DEFAULT;');
    console.log('✅ n8n schema cleaned successfully\n');

    // Import data table by table
    const tables = [
      'migrations',
      'settings', 
      'installed_packages',
      'installed_nodes',
      'event_destinations',
      'auth_identity',
      'auth_provider_sync_history',
      'tag_entity',
      'user',
      'user_api_keys',
      'variables',
      'folder',
      'folder_tag',
      'credentials_entity',
      'workflow_entity',
      'workflows_tags',
      'workflow_statistics',
      'webhook_entity',
      'execution_entity',
      'execution_data',
      'execution_metadata',
      'execution_annotations',
      'execution_annotation_tags',
      'shared_credentials',
      'shared_workflow',
      'project',
      'project_relation',
      'processed_data',
      'insights_metadata',
      'insights_by_period',
      'insights_raw',
      'test_case_execution',
      'test_run',
      'workflow_history',
      'invalid_auth_token'
    ];

    for (const tableName of tables) {
      await importTable(sqliteDb, pgClient, tableName);
    }

    console.log('\n🎉 Clean import completed successfully!');
    
  } catch (error) {
    console.error('💥 Import failed:', error);
  } finally {
    sqliteDb.close();
    await pgClient.end();
    
    // Clean up extracted SQLite file
    exec(`rm -f ${SQLITE_PATH}`);
  }
}

async function importTable(sqliteDb, pgClient, tableName) {
  try {
    // Get table data from SQLite
    const rows = await new Promise((resolve, reject) => {
      sqliteDb.all(`SELECT * FROM "${tableName}"`, (err, rows) => {
        if (err) {
          if (err.message.includes('no such table')) {
            resolve([]);
          } else {
            reject(err);
          }
        } else {
          resolve(rows);
        }
      });
    });

    if (rows.length === 0) {
      console.log(`  ⚪ ${tableName}: No data to import`);
      return;
    }

    // Get PostgreSQL table schema
    const schemaResult = await pgClient.query(`
      SELECT column_name, data_type, column_default
      FROM information_schema.columns
      WHERE table_schema = 'n8n' AND table_name = $1
      ORDER BY ordinal_position
    `, [tableName]);

    if (schemaResult.rows.length === 0) {
      console.log(`  ⚪ ${tableName}: Table not found in PostgreSQL`);
      return;
    }

    const columns = schemaResult.rows.map(row => row.column_name);
    
    // Import each row
    let imported = 0;
    let errors = 0;

    for (const row of rows) {
      try {
        // Filter row data to match PostgreSQL columns
        const filteredRow = {};
        for (const col of columns) {
          if (row[col] !== undefined) {
            filteredRow[col] = row[col];
          }
        }

        if (Object.keys(filteredRow).length === 0) continue;

        // Build INSERT query
        const columnNames = Object.keys(filteredRow).map(col => `"${col}"`).join(', ');
        const placeholders = Object.keys(filteredRow).map((_, i) => `$${i + 1}`).join(', ');
        const values = Object.values(filteredRow);

        await pgClient.query(`
          INSERT INTO n8n."${tableName}" (${columnNames})
          VALUES (${placeholders})
        `, values);

        imported++;
      } catch (error) {
        errors++;
        if (errors <= 3) {
          console.log(`    ❌ Error importing row: ${error.message.substring(0, 100)}...`);
        }
      }
    }

    console.log(`  ✅ ${tableName}: ${imported} rows imported, ${errors} errors`);

  } catch (error) {
    console.log(`  ❌ ${tableName}: Failed - ${error.message}`);
  }
}

cleanImport();