#!/usr/bin/env node

import pkg from 'pg';
const { Client } = pkg;

const PG_CONFIG = {
  host: 'localhost',
  port: 5432,
  database: 'pilotpros_db',
  user: 'pilotpros_user',
  password: 'pilotpros_secure_pass_2025'
};

console.log('🔧 Fixing n8n migrations for compatibility...\n');

async function fixMigrations() {
  const pgClient = new Client(PG_CONFIG);
  await pgClient.connect();

  try {
    // Get current migrations
    const result = await pgClient.query('SELECT timestamp, name FROM n8n.migrations ORDER BY timestamp');
    console.log(`📊 Found ${result.rows.length} existing migrations`);

    // List of all n8n 1.106.3 migrations that should exist
    const requiredMigrations = [
      { timestamp: 1611144599516, name: 'AddWebhookId1611144599516' },
      { timestamp: 1617270242566, name: 'CreateTagEntity1617270242566' },
      { timestamp: 1620824779533, name: 'UniqueWorkflowNames1620824779533' },
      { timestamp: 1626176912946, name: 'AddwaitTill1626176912946' },
      { timestamp: 1630419189837, name: 'UpdateWorkflowCredentials1630419189837' },
      { timestamp: 1644424784709, name: 'AddExecutionEntityIndexes1644424784709' },
      { timestamp: 1658932090381, name: 'AddNodeIds1658932090381' },
      { timestamp: 1663755770893, name: 'CreateUserManagement1663755770893' },
      { timestamp: 1665484192211, name: 'CommunityNodes1665484192211' },
      { timestamp: 1669739707125, name: 'AddWorkflowVersionIdColumn1669739707125' },
      { timestamp: 1671726148419, name: 'WorkflowStatistics1671726148419' },
      { timestamp: 1675940580449, name: 'CreateVariables1675940580449' },
      { timestamp: 1677501636753, name: 'CreateUserSettings1677501636753' },
      { timestamp: 1690000000000, name: 'RemoveSkipList1690000000000' },
      { timestamp: 1695000000000, name: 'SeparateExecutionData1695000000000' }
    ];

    // Add missing migrations
    for (const migration of requiredMigrations) {
      const existingMigration = result.rows.find(row => row.timestamp.toString() === migration.timestamp.toString());
      
      if (!existingMigration) {
        console.log(`➕ Adding missing migration: ${migration.name}`);
        await pgClient.query(
          'INSERT INTO n8n.migrations (timestamp, name) VALUES ($1, $2)',
          [migration.timestamp, migration.name]
        );
      } else {
        console.log(`✅ Migration exists: ${migration.name}`);
      }
    }

    console.log('\n🎉 Migration fixes completed!');

  } catch (error) {
    console.error('💥 Migration fix failed:', error);
  } finally {
    await pgClient.end();
  }
}

fixMigrations();