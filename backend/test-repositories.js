import dotenv from 'dotenv';
import { WorkflowRepository } from './src/repositories/workflow.repository.js';
import { ExecutionRepository } from './src/repositories/execution.repository.js';
import { BusinessRepository } from './src/repositories/business.repository.js';
import { SystemRepository } from './src/repositories/system.repository.js';

// Load environment variables
dotenv.config();

console.log('\n🧪 TESTING DRIZZLE REPOSITORIES WITH FIXED SCHEMA\n');
console.log('Database Config:', {
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'pilotpros_db',
  user: process.env.DB_USER || 'pilotpros_user'
});

async function testRepositories() {
  try {
    // Test WorkflowRepository
    console.log('\n📁 Testing WorkflowRepository...');
    const workflowRepo = new WorkflowRepository();
    
    console.log('  - Getting statistics...');
    const stats = await workflowRepo.getStatistics();
    console.log('  ✅ Statistics:', stats);
    
    console.log('  - Getting active workflows...');
    const activeWorkflows = await workflowRepo.getActiveWithAnalytics();
    console.log('  ✅ Active workflows count:', activeWorkflows.length);
    
    // Test ExecutionRepository
    console.log('\n📊 Testing ExecutionRepository...');
    const executionRepo = new ExecutionRepository();
    
    console.log('  - Getting recent executions...');
    const recentExecutions = await executionRepo.getRecent(5);
    console.log('  ✅ Recent executions count:', recentExecutions.length);
    
    // Test BusinessRepository
    console.log('\n💼 Testing BusinessRepository...');
    const businessRepo = new BusinessRepository();
    
    console.log('  - Getting dashboard overview...');
    const dashboard = await businessRepo.getDashboardOverview();
    console.log('  ✅ Dashboard overview:', dashboard);
    
    // Test SystemRepository
    console.log('\n⚙️ Testing SystemRepository...');
    const systemRepo = new SystemRepository();
    
    console.log('  - Getting health status...');
    const health = await systemRepo.getHealthStatus();
    console.log('  ✅ System health status:', health);
    
    console.log('\n✅ ALL REPOSITORY TESTS PASSED!\n');
    process.exit(0);
    
  } catch (error) {
    console.error('\n❌ REPOSITORY TEST FAILED:', error.message);
    console.error('Stack:', error.stack);
    process.exit(1);
  }
}

// Run tests
testRepositories();