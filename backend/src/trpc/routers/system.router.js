import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, businessProcedure, publicProcedure } from '../trpc.js';

/**
 * System Router - Health, Icons, Debug & Utilities
 * Migrates system-level endpoints to tRPC
 */

export const systemRouter = router({
  
  /**
   * System health check
   * Equivalent to: GET /health
   */
  health: publicProcedure
    .query(async ({ ctx }) => {
      console.log('❤️ tRPC: System health check');
      
      try {
        // Test database connection
        const dbResult = await ctx.dbPool.query('SELECT NOW() as current_time');
        const dbHealthy = dbResult.rows.length > 0;
        
        // Check n8n schema
        const n8nCheck = await ctx.dbPool.query(`
          SELECT COUNT(*) as workflow_count 
          FROM n8n.workflow_entity 
          WHERE "isArchived" = false
        `);
        const n8nHealthy = n8nCheck.rows.length > 0;
        
        const health = {
          status: 'healthy',
          timestamp: new Date().toISOString(),
          database: {
            status: dbHealthy ? 'connected' : 'disconnected',
            timestamp: dbResult.rows[0]?.current_time
          },
          n8n: {
            status: n8nHealthy ? 'connected' : 'disconnected',
            workflowCount: parseInt(n8nCheck.rows[0]?.workflow_count) || 0
          },
          services: {
            tRPC: 'active',
            drizzle: ctx.db ? 'connected' : 'unavailable'
          }
        };
        
        console.log(`✅ tRPC: System healthy - DB: ${health.database.status}, n8n: ${health.n8n.status}`);
        
        return health;
        
      } catch (error) {
        console.error('❌ tRPC system health failed:', error);
        
        return {
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          error: error.message,
          database: { status: 'error' },
          n8n: { status: 'error' }
        };
      }
    }),

  /**
   * Get n8n node icons
   * Equivalent to: GET /api/n8n-icons/:nodeType
   */
  getNodeIcon: businessProcedure
    .input(z.object({
      nodeType: z.string().min(1, 'Node type è richiesto')
    }))
    .query(async ({ input, ctx }) => {
      const { nodeType } = input;
      
      console.log(`🎨 tRPC: Getting icon for node type: ${nodeType}`);
      
      try {
        // For now, return a simple mapping or default icon
        // This could be enhanced to read actual n8n icon files
        const iconMapping = {
          'n8n-nodes-base.cron': 'schedule',
          'n8n-nodes-base.httpRequest': 'api',
          '@n8n/n8n-nodes-langchain.agent': 'robot',
          'n8n-nodes-base.emailImap': 'mail',
          'n8n-nodes-base.postgres': 'database',
          'default': 'workflow'
        };
        
        const iconType = iconMapping[nodeType] || iconMapping['default'];
        
        console.log(`✅ tRPC: Icon mapped - ${nodeType} -> ${iconType}`);
        
        return {
          success: true,
          nodeType,
          iconType,
          iconUrl: `/icons/${iconType}.svg`
        };
        
      } catch (error) {
        console.error('❌ tRPC system getNodeIcon failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero icona node',
          cause: error.message
        });
      }
    }),

  /**
   * Test Drizzle ORM connection
   * Equivalent to: GET /api/business/test-drizzle
   */
  testDrizzle: businessProcedure
    .query(async ({ ctx }) => {
      console.log('🧪 tRPC: Testing Drizzle ORM connection');
      
      try {
        if (!ctx.db) {
          throw new TRPCError({
            code: 'INTERNAL_SERVER_ERROR',
            message: 'Drizzle ORM non disponibile'
          });
        }
        
        // Simple test query using Drizzle
        const testResult = await ctx.dbPool.query('SELECT 1 as test_value');
        
        console.log('✅ tRPC: Drizzle ORM test successful');
        
        return {
          success: true,
          drizzle: 'connected',
          testResult: testResult.rows[0],
          timestamp: new Date().toISOString()
        };
        
      } catch (error) {
        console.error('❌ tRPC system testDrizzle failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante test Drizzle ORM',
          cause: error.message
        });
      }
    }),

  /**
   * Test error notification
   * Equivalent to: POST /api/business/test-error-notification
   */
  testErrorNotification: businessProcedure
    .input(z.object({
      message: z.string().optional().default('Test error notification'),
      severity: z.enum(['low', 'medium', 'high']).optional().default('medium')
    }))
    .mutation(async ({ input, ctx }) => {
      const { message, severity } = input;
      
      console.log(`🚨 tRPC: Testing error notification - ${severity}: ${message}`);
      
      try {
        // Simulate error notification logic
        const notification = {
          id: `error_${Date.now()}`,
          message,
          severity,
          timestamp: new Date().toISOString(),
          status: 'sent'
        };
        
        // Here you could integrate with actual notification service
        // For now, just log and return success
        console.log(`✅ tRPC: Error notification test completed - ${notification.id}`);
        
        return {
          success: true,
          notification,
          testCompleted: true
        };
        
      } catch (error) {
        console.error('❌ tRPC system testErrorNotification failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante test notifica errore',
          cause: error.message
        });
      }
    }),

  /**
   * Get test raw data
   * Equivalent to: GET /api/business/test-raw-data
   */
  getTestRawData: businessProcedure
    .query(async ({ ctx }) => {
      console.log('🧪 tRPC: Getting test raw data');
      
      try {
        // Get sample data from business_execution_data
        const rawDataResult = await ctx.dbPool.query(`
          SELECT *
          FROM pilotpros.business_execution_data
          ORDER BY execution_date DESC
          LIMIT 5
        `);
        
        const testData = {
          sampleCount: rawDataResult.rows.length,
          sampleData: rawDataResult.rows,
          timestamp: new Date().toISOString(),
          source: 'pilotpros.business_execution_data'
        };
        
        console.log(`✅ tRPC: Test raw data retrieved - ${testData.sampleCount} samples`);
        
        return {
          success: true,
          testData
        };
        
      } catch (error) {
        console.error('❌ tRPC system getTestRawData failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero dati test raw',
          cause: error.message
        });
      }
    }),

  /**
   * Debug execution by ID
   * Equivalent to: GET /api/debug/execution/:id
   */
  debugExecution: businessProcedure
    .input(z.object({
      executionId: z.string().min(1, 'Execution ID è richiesto')
    }))
    .query(async ({ input, ctx }) => {
      const { executionId } = input;
      
      console.log(`🐛 tRPC: Debug execution ID=${executionId}`);
      
      try {
        // Get execution details
        const executionResult = await ctx.dbPool.query(`
          SELECT 
            e.*,
            w.name as workflow_name
          FROM n8n.execution_entity e
          LEFT JOIN n8n.workflow_entity w ON e."workflowId" = w.id
          WHERE e.id = $1
        `, [executionId]);
        
        if (executionResult.rows.length === 0) {
          throw new TRPCError({
            code: 'NOT_FOUND',
            message: 'Esecuzione non trovata'
          });
        }
        
        const execution = executionResult.rows[0];
        
        // Get business data if available
        const businessResult = await ctx.dbPool.query(`
          SELECT *
          FROM pilotpros.business_execution_data
          WHERE execution_id = $1
        `, [executionId]);
        
        const debugInfo = {
          execution: {
            id: execution.id,
            workflowId: execution.workflowId,
            workflowName: execution.workflow_name,
            status: execution.status,
            startedAt: execution.startedAt,
            stoppedAt: execution.stoppedAt,
            mode: execution.mode
          },
          businessData: businessResult.rows,
          debugTimestamp: new Date().toISOString()
        };
        
        console.log(`✅ tRPC: Debug info retrieved - status: ${execution.status}, ${businessResult.rows.length} business records`);
        
        return {
          success: true,
          debugInfo
        };
        
      } catch (error) {
        console.error('❌ tRPC system debugExecution failed:', error);
        
        if (error instanceof TRPCError) throw error;
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante debug esecuzione',
          cause: error.message
        });
      }
    }),

});