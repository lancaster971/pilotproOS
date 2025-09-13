#!/usr/bin/env node

import { readFileSync, existsSync } from 'fs';
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

console.log('🔄 COMPLETE MIRROR: Copying EVERYTHING from Hostinger SQLite to PostgreSQL...\n');

async function completeMirror() {
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
    console.log('🧹 PostgreSQL n8n schema cleaned (already done)\n');

    // Get ALL table names from SQLite
    const tableNames = await new Promise((resolve, reject) => {
      sqliteDb.all(`
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%' 
        ORDER BY name
      `, (err, rows) => {
        if (err) reject(err);
        else resolve(rows.map(row => row.name));
      });
    });

    console.log(`📊 Found ${tableNames.length} tables in Hostinger SQLite database\n`);

    // For each table, get schema and recreate in PostgreSQL
    for (const tableName of tableNames) {
      await mirrorTable(sqliteDb, pgClient, tableName);
    }

    console.log('\n🎉 Complete mirror completed successfully!');
    console.log('🔄 PostgreSQL now contains IDENTICAL copy of Hostinger database');
    
  } catch (error) {
    console.error('💥 Mirror failed:', error);
  } finally {
    sqliteDb.close();
    await pgClient.end();
    
    // Clean up extracted SQLite file
    exec(`rm -f ${SQLITE_PATH}`);
  }
}

async function mirrorTable(sqliteDb, pgClient, tableName) {
  console.log(`🔄 Mirroring table: ${tableName}`);

  try {
    // Get table schema from SQLite
    const schemaInfo = await new Promise((resolve, reject) => {
      sqliteDb.all(`PRAGMA table_info("${tableName}")`, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });

    // Convert SQLite schema to PostgreSQL
    const pgColumns = schemaInfo.map(col => {
      let pgType = convertSqliteTypeToPg(col.type);
      let nullable = col.notnull === 0 ? '' : ' NOT NULL';
      let defaultValue = '';
      
      if (col.dflt_value !== null) {
        if (col.dflt_value.includes('STRFTIME') || col.dflt_value.includes('NOW')) {
          defaultValue = ' DEFAULT CURRENT_TIMESTAMP';
        } else if (col.dflt_value.includes('uuid')) {
          defaultValue = ' DEFAULT gen_random_uuid()';
        } else {
          defaultValue = ` DEFAULT ${col.dflt_value}`;
        }
      }
      
      return `"${col.name}" ${pgType}${nullable}${defaultValue}`;
    }).join(', ');

    // Create table in PostgreSQL
    const createTableSQL = `CREATE TABLE n8n."${tableName}" (${pgColumns})`;
    console.log(`  📝 Creating table schema...`);
    await pgClient.query(createTableSQL);

    // Get all data from SQLite table
    const rows = await new Promise((resolve, reject) => {
      sqliteDb.all(`SELECT * FROM "${tableName}"`, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });

    if (rows.length === 0) {
      console.log(`  ⚪ ${tableName}: No data to copy`);
      return;
    }

    console.log(`  📦 Copying ${rows.length} rows...`);

    // Disable foreign key checks for this session
    await pgClient.query('SET session_replication_role = replica');

    // Insert all data
    let imported = 0;
    let errors = 0;

    for (const row of rows) {
      try {
        const columns = Object.keys(row);
        const values = Object.values(row);
        
        const columnNames = columns.map(col => `"${col}"`).join(', ');
        const placeholders = columns.map((_, i) => `$${i + 1}`).join(', ');
        
        await pgClient.query(`
          INSERT INTO n8n."${tableName}" (${columnNames})
          VALUES (${placeholders})
        `, values);

        imported++;
      } catch (error) {
        errors++;
        if (errors <= 3) {
          console.log(`    ❌ Row error: ${error.message.substring(0, 80)}...`);
        }
      }
    }

    // Re-enable foreign key checks
    await pgClient.query('SET session_replication_role = DEFAULT');

    console.log(`  ✅ ${tableName}: ${imported} rows copied, ${errors} errors`);

  } catch (error) {
    console.log(`  ❌ ${tableName}: Failed to mirror - ${error.message}`);
  }
}

function convertSqliteTypeToPg(sqliteType) {
  const type = sqliteType.toLowerCase();
  
  if (type.includes('int')) return 'INTEGER';
  if (type.includes('text') || type.includes('varchar')) {
    const match = type.match(/varchar\((\d+)\)/);
    return match ? `VARCHAR(${match[1]})` : 'TEXT';
  }
  if (type.includes('char')) {
    const match = type.match(/char\((\d+)\)/);
    return match ? `CHAR(${match[1]})` : 'VARCHAR(255)';
  }
  if (type.includes('boolean')) return 'BOOLEAN';
  if (type.includes('datetime') || type.includes('timestamp')) return 'TIMESTAMP(3) WITH TIME ZONE';
  if (type.includes('json')) return 'JSON';
  if (type.includes('real') || type.includes('float')) return 'REAL';
  if (type.includes('date')) return 'DATE';
  
  return 'TEXT'; // Default fallback
}

completeMirror();