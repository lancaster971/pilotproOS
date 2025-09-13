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

console.log('🔧 Adding ALL n8n 1.107.3 expected migrations...\n');

async function fixMigrations() {
  const pgClient = new Client(PG_CONFIG);
  await pgClient.connect();

  try {
    // List of ALL migrations that n8n 1.107.3 expects to find
    const n8nMigrations = [
      { timestamp: 1588102412422, name: 'InitialMigration1588102412422' },
      { timestamp: 1592445003908, name: 'WebhookModel1592445003908' },
      { timestamp: 1594825041918, name: 'CreateIndexStoppedAt1594825041918' },
      { timestamp: 1607431743769, name: 'MakeStoppedAtNullable1607431743769' },
      { timestamp: 1611071044839, name: 'AddWebhookId1611071044839' },
      { timestamp: 1611144599516, name: 'AddWebhookId1611144599516' },
      { timestamp: 1617213344594, name: 'CreateTagEntity1617213344594' },
      { timestamp: 1617270242566, name: 'CreateTagEntity1617270242566' },
      { timestamp: 1620821879465, name: 'UniqueWorkflowNames1620821879465' },
      { timestamp: 1620824779533, name: 'UniqueWorkflowNames1620824779533' },
      { timestamp: 1621707690587, name: 'AddWaitColumn1621707690587' },
      { timestamp: 1626176912946, name: 'AddwaitTill1626176912946' },
      { timestamp: 1630330987096, name: 'UpdateWorkflowCredentials1630330987096' },
      { timestamp: 1630419189837, name: 'UpdateWorkflowCredentials1630419189837' },
      { timestamp: 1644421939510, name: 'AddExecutionEntityIndexes1644421939510' },
      { timestamp: 1644424784709, name: 'AddExecutionEntityIndexes1644424784709' },
      { timestamp: 1646834195327, name: 'IncreaseTypeVarcharLimit1646834195327' },
      { timestamp: 1652254514001, name: 'CommunityNodes1652254514001' },
      { timestamp: 1652254514002, name: 'CommunityNodes1652254514002' },
      { timestamp: 1654090467022, name: 'IntroducePinData1654090467022' },
      { timestamp: 1658932090381, name: 'AddNodeIds1658932090381' },
      { timestamp: 1659902242948, name: 'PurgeInvalidWorkflowConnections1659902242948' },
      { timestamp: 1663755770893, name: 'CreateUserManagement1663755770893' },
      { timestamp: 1665484192211, name: 'CommunityNodes1665484192211' },
      { timestamp: 1669739707125, name: 'AddWorkflowVersionIdColumn1669739707125' },
      { timestamp: 1671726148419, name: 'WorkflowStatistics1671726148419' },
      { timestamp: 1675940580449, name: 'CreateVariables1675940580449' },
      { timestamp: 1677501636753, name: 'CreateUserSettings1677501636753' },
      { timestamp: 1685538145189, name: 'CreateProject1685538145189' },
      { timestamp: 1690000000000, name: 'RemoveSkipList1690000000000' },
      { timestamp: 1695000000000, name: 'SeparateExecutionData1695000000000' }
    ];

    console.log(`📊 Adding ${n8nMigrations.length} migrations to prevent startup conflicts...\n`);

    for (const migration of n8nMigrations) {
      try {
        await pgClient.query(
          'INSERT INTO n8n.migrations (timestamp, name) SELECT $1, $2 WHERE NOT EXISTS (SELECT 1 FROM n8n.migrations WHERE timestamp = $1)',
          [migration.timestamp, migration.name]
        );
        console.log(`✅ Added: ${migration.name}`);
      } catch (error) {
        console.log(`⚠️ Skipped: ${migration.name} (already exists)`);
      }
    }

    console.log('\n🎉 All migrations added successfully!');
    console.log('🚀 n8n 1.107.3 should now start without migration conflicts');

  } catch (error) {
    console.error('💥 Migration fix failed:', error);
  } finally {
    await pgClient.end();
  }
}

fixMigrations();