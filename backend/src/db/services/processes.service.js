/**
 * Processes Service - Drizzle ORM Implementation
 * Migrates business process queries from raw SQL to type-safe ORM
 */

import { db } from '../connection.js'
import { workflowEntity, executionEntity } from '../schema.js'
import { eq, desc, sql } from 'drizzle-orm'

/**
 * Get all business processes - Drizzle version
 * Replaces raw SQL query in processes.router.js
 */
export async function getAllBusinessProcesses() {
  console.log('🗄️ Drizzle: Getting all business processes');
  
  try {
    const processes = await db
      .select({
        id: workflowEntity.id,
        process_name: workflowEntity.name,
        is_active: workflowEntity.active,
        nodes: workflowEntity.nodes,
        connections: workflowEntity.connections,
        created_at: workflowEntity.createdAt,
        updated_at: workflowEntity.updatedAt,
      })
      .from(workflowEntity)
      .orderBy(desc(workflowEntity.updatedAt))

    console.log(`✅ Drizzle: Found ${processes.length} business processes`);
    return processes;

  } catch (error) {
    console.error('❌ Drizzle: Error getting processes:', error);
    throw new Error('Failed to retrieve business processes');
  }
}

/**
 * Get single business process by ID - Type-safe version
 */
export async function getBusinessProcessById(workflowId) {
  try {
    const process = await db
      .select()
      .from(workflowEntity)
      .where(eq(workflowEntity.id, parseInt(workflowId)))
      .limit(1)

    return process[0] || null;

  } catch (error) {
    console.error(`❌ Drizzle: Error getting process ${workflowId}:`, error);
    throw new Error('Failed to retrieve business process');
  }
}

/**
 * Toggle process active status - Type-safe mutation
 */
export async function toggleProcessStatus(workflowId, active) {
  try {
    const result = await db
      .update(workflowEntity)
      .set({ 
        active: active,
        updatedAt: sql`NOW()`
      })
      .where(eq(workflowEntity.id, parseInt(workflowId)))
      .returning({
        id: workflowEntity.id,
        name: workflowEntity.name,
        active: workflowEntity.active
      })

    return result[0];

  } catch (error) {
    console.error(`❌ Drizzle: Error toggling process ${workflowId}:`, error);
    throw new Error('Failed to toggle process status');
  }
}

/**
 * Get process execution stats - Complex join query
 */
export async function getProcessExecutionStats(workflowId) {
  try {
    // Complex query with aggregation - shows Drizzle power
    const stats = await db
      .select({
        workflow_id: workflowEntity.id,
        workflow_name: workflowEntity.name,
        total_executions: sql<number>`COUNT(${executionEntity.id})`,
        successful_executions: sql<number>`COUNT(CASE WHEN ${executionEntity.finished} = true THEN 1 END)`,
        failed_executions: sql<number>`COUNT(CASE WHEN ${executionEntity.finished} = false THEN 1 END)`,
        last_execution: sql<Date>`MAX(${executionEntity.startedAt})`,
        avg_execution_time: sql<number>`AVG(EXTRACT(epoch FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})))`,
      })
      .from(workflowEntity)
      .leftJoin(executionEntity, eq(workflowEntity.id, sql`CAST(${executionEntity.workflowId} AS INTEGER)`))
      .where(eq(workflowEntity.id, parseInt(workflowId)))
      .groupBy(workflowEntity.id, workflowEntity.name)

    return stats[0] || null;

  } catch (error) {
    console.error(`❌ Drizzle: Error getting execution stats for ${workflowId}:`, error);
    throw new Error('Failed to get process execution statistics');
  }
}