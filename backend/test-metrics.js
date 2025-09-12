/**
 * Test Script per verificare le metriche di performance
 * PERF-001 e PERF-002
 */

import { db } from './src/db/connection.js';
import { BusinessRepository } from './src/repositories/business.repository.js';
import { ExecutionRepository } from './src/repositories/execution.repository.js';

async function testMetrics() {
  console.log('🧪 Test delle metriche di performance...\n');
  
  try {
    // Test BusinessRepository
    const businessRepo = new BusinessRepository();
    
    console.log('📊 Test getPerformanceMetrics (ultimi 30 giorni)...');
    const perfMetrics = await businessRepo.getPerformanceMetrics(30);
    console.log('Risultati Performance Metrics:');
    console.log('- Total Executions:', perfMetrics.totalExecutions);
    console.log('- Success Rate:', perfMetrics.successRate + '%');
    console.log('- Avg Duration:', perfMetrics.avgDuration + 'ms');
    console.log('- Peak Concurrent:', perfMetrics.peakConcurrent);
    console.log('- System Load:', perfMetrics.systemLoad + '%');
    console.log('');
    
    console.log('📈 Test getDashboardOverview...');
    const dashboard = await businessRepo.getDashboardOverview();
    console.log('Dashboard Overview:');
    console.log('- Total Workflows:', dashboard.workflows.total);
    console.log('- Active Workflows:', dashboard.workflows.active);
    console.log('- Total Executions:', dashboard.executions.total);
    console.log('- Recent Executions (24h):', dashboard.executions.recent);
    console.log('- Success Rate:', dashboard.executions.successRate + '%');
    console.log('- System Health:', dashboard.systemHealth);
    console.log('');
    
    // Test ExecutionRepository
    const execRepo = new ExecutionRepository();
    
    console.log('🔄 Test getSystemStats...');
    const systemStats = await execRepo.getSystemStats(30);
    console.log('System Stats:');
    console.log('- Total Executions:', systemStats.totalExecutions);
    console.log('- Successful:', systemStats.successfulExecutions);
    console.log('- Failed:', systemStats.failedExecutions);
    console.log('- Running:', systemStats.runningExecutions);
    console.log('- Success Rate:', systemStats.successRate + '%');
    console.log('- Unique Workflows:', systemStats.uniqueWorkflows);
    console.log('');
    
    // Test per workflow specifico (se ce ne sono)
    console.log('🎯 Test metriche per workflow specifico...');
    const workflows = await db.query`
      SELECT id, name 
      FROM n8n.workflow_entity 
      WHERE active = true 
      LIMIT 1
    `;
    
    if (workflows.length > 0) {
      const workflowId = workflows[0].id;
      const workflowName = workflows[0].name;
      
      console.log(`Testing workflow: ${workflowName} (${workflowId})`);
      
      const workflowStats = await execRepo.getStatsByWorkflowId(workflowId, 30);
      console.log('Workflow Stats:');
      console.log('- Total Executions:', workflowStats.totalExecutions);
      console.log('- Success Rate:', workflowStats.successRate + '%');
      console.log('- Avg Duration:', workflowStats.avgDuration + 'ms');
      console.log('- Peak Concurrent:', workflowStats.peakConcurrent);
    }
    
    console.log('\n✅ Test completati con successo!');
    
  } catch (error) {
    console.error('❌ Errore durante i test:', error);
    console.error('Stack:', error.stack);
  } finally {
    await db.end();
  }
}

// Esegui i test
testMetrics();