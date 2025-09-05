import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, businessProcedure } from '../trpc.js';

/**
 * Processes Router - Business Process Management
 * Migrates all business process endpoints to tRPC
 */

export const processesRouter = router({
  
  /**
   * Get all business processes
   * Equivalent to: GET /api/business/processes
   */
  getAll: businessProcedure
    .query(async ({ ctx }) => {
      console.log('🔍 tRPC: Getting all business processes');
      
      try {
        const result = await ctx.dbPool.query(`
          SELECT 
            w.id,
            w.name as process_name,
            w.active as is_active,
            w.nodes,
            w.connections,
            w."createdAt" as created_at,
            w."updatedAt" as updated_at
          FROM n8n.workflow_entity w
          WHERE w."isArchived" = false
          ORDER BY w."updatedAt" DESC
        `);
        
        // Process nodes to add labels for frontend
        const processedData = (result.rows || []).map(workflow => {
          let processedNodes = [];
          
          try {
            const nodes = typeof workflow.nodes === 'string' ? JSON.parse(workflow.nodes) : workflow.nodes || [];
            processedNodes = nodes.map(node => ({
              ...node,
              label: node.name || null, // Set label = name for frontend
              nodeType: node.type || null
            }));
          } catch (error) {
            console.error('Error processing nodes for workflow:', workflow.id, error);
            processedNodes = [];
          }
          
          return {
            id: workflow.id,
            name: workflow.process_name,
            active: workflow.is_active,
            nodes: processedNodes,
            connections: workflow.connections || {},
            createdAt: workflow.created_at,
            updatedAt: workflow.updated_at
          };
        });
        
        console.log(`✅ tRPC: Found ${processedData.length} business processes`);
        
        return {
          success: true,
          processes: processedData,
          count: processedData.length
        };
        
      } catch (error) {
        console.error('❌ tRPC processes getAll failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero processi business',
          cause: error.message
        });
      }
    }),

  /**
   * Get specific business process details  
   * Equivalent to: GET /api/business/process-details/:processId
   */
  getDetails: businessProcedure
    .input(z.object({
      processId: z.string().min(1, 'Process ID è richiesto')
    }))
    .query(async ({ input, ctx }) => {
      const { processId } = input;
      
      console.log(`🔍 tRPC: Getting process details for ID=${processId}`);
      
      try {
        const workflowResult = await ctx.dbPool.query(`
          SELECT 
            w.id,
            w.name as process_name,
            w.active as is_active,
            w.nodes,
            w.connections,
            w."createdAt" as created_at,
            w."updatedAt" as updated_at
          FROM n8n.workflow_entity w
          WHERE w.id = $1 AND w."isArchived" = false
        `, [processId]);
        
        if (workflowResult.rows.length === 0) {
          throw new TRPCError({
            code: 'NOT_FOUND',
            message: 'Business Process non trovato',
            cause: `Process ID ${processId} not found`
          });
        }
        
        const workflow = workflowResult.rows[0];
        const nodes = workflow.nodes || [];
        const connections = workflow.connections || {};
        
        // Count executions for this workflow
        const executionsResult = await ctx.dbPool.query(`
          SELECT COUNT(*) as execution_count
          FROM n8n.execution_entity 
          WHERE "workflowId" = $1
        `, [processId]);
        
        const executionCount = parseInt(executionsResult.rows[0]?.execution_count) || 0;
        
        const businessProcessDetails = {
          processId: workflow.id,
          name: workflow.process_name,
          active: workflow.is_active,
          nodes: nodes,
          connections: connections,
          createdAt: workflow.created_at,
          updatedAt: workflow.updated_at,
          executionCount: executionCount,
          nodeCount: Array.isArray(nodes) ? nodes.length : 0
        };
        
        console.log(`✅ tRPC: Process details retrieved for ${workflow.process_name}`);
        
        return {
          success: true,
          process: businessProcessDetails
        };
        
      } catch (error) {
        console.error('❌ tRPC process getDetails failed:', error);
        
        if (error instanceof TRPCError) throw error;
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero dettagli processo',
          cause: error.message
        });
      }
    }),

});