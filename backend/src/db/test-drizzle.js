/**
 * Test Drizzle ORM Connection
 * Verify database schema mapping and query execution
 */

import { db, testConnection } from './connection.js';
import { workflowEntity } from './schema.js';
import { getAllBusinessProcesses } from './services/processes.service.js';

async function testDrizzle() {
  console.log('🧪 Testing Drizzle ORM Setup...\n');

  // Test 1: Basic connection
  console.log('1. Testing database connection...');
  const connectionResult = await testConnection();
  console.log(`   ${connectionResult.success ? '✅' : '❌'} ${connectionResult.message}\n`);

  if (!connectionResult.success) {
    process.exit(1);
  }

  // Test 2: Schema mapping
  console.log('2. Testing schema mapping with simple query...');
  try {
    const count = await db.select().from(workflowEntity).limit(1);
    console.log(`   ✅ Schema mapping working - found ${count.length} workflow(s)\n`);
  } catch (error) {
    console.log(`   ❌ Schema mapping failed: ${error.message}\n`);
    return;
  }

  // Test 3: Service layer
  console.log('3. Testing service layer...');
  try {
    const processes = await getAllBusinessProcesses();
    console.log(`   ✅ Service layer working - retrieved ${processes.length} processes\n`);
    
    if (processes.length > 0) {
      const sample = processes[0];
      console.log('   📋 Sample process:');
      console.log(`      ID: ${sample.id}`);
      console.log(`      Name: ${sample.process_name}`);
      console.log(`      Active: ${sample.is_active}`);
      console.log(`      Nodes: ${Array.isArray(sample.nodes) ? sample.nodes.length : 'N/A'}`);
    }
  } catch (error) {
    console.log(`   ❌ Service layer failed: ${error.message}\n`);
    return;
  }

  console.log('\n🎉 Drizzle ORM setup completed successfully!');
  console.log('📋 Ready for gradual migration from raw SQL queries.');
  
  process.exit(0);
}

// Run test if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testDrizzle().catch(console.error);
}

export { testDrizzle };