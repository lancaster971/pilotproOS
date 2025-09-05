/**
 * Processes Router - Drizzle ORM Version
 * Side-by-side comparison with raw SQL version
 * Safe migration testing without breaking existing functionality
 */

import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, businessProcedure } from '../trpc.js';
import { 
  getAllBusinessProcesses, 
  getBusinessProcessById, 
  toggleProcessStatus,
  getProcessExecutionStats 
} from '../../db/services/processes.service.js';

export const processesRouterDrizzle = router({
  
  /**
   * Get all business processes - Drizzle ORM version
   * Compare with raw SQL version in processes.router.js
   */
  getAllDrizzle: businessProcedure
    .query(async ({ ctx }) => {
      try {
        const processes = await getAllBusinessProcesses();
        
        return {
          success: true,
          data: processes,
          method: 'drizzle-orm',
          count: processes.length
        };

      } catch (error) {
        console.error('❌ tRPC Drizzle: Error in getAllDrizzle:', error);
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Failed to retrieve business processes via Drizzle'
        });
      }
    }),

  /**
   * Get single process - Type-safe parameters
   */
  getByIdDrizzle: businessProcedure
    .input(z.object({
      workflowId: z.string()
    }))
    .query(async ({ input }) => {
      try {
        const process = await getBusinessProcessById(input.workflowId);
        
        if (!process) {
          throw new TRPCError({
            code: 'NOT_FOUND',
            message: 'Business process not found'
          });
        }

        return {
          success: true,
          data: process,
          method: 'drizzle-orm'
        };

      } catch (error) {
        console.error('❌ tRPC Drizzle: Error in getByIdDrizzle:', error);
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Failed to retrieve business process'
        });
      }
    }),

  /**
   * Toggle process status - Type-safe mutation
   */
  toggleDrizzle: businessProcedure
    .input(z.object({
      workflowId: z.string(),
      active: z.boolean()
    }))
    .mutation(async ({ input }) => {
      try {
        const result = await toggleProcessStatus(input.workflowId, input.active);
        
        console.log(`✅ Process ${result.name} ${result.active ? 'activated' : 'deactivated'} via Drizzle`);

        return {
          success: true,
          data: result,
          message: `Business Process "${result.name}" ${result.active ? 'attivato' : 'disattivato'}`,
          method: 'drizzle-orm'
        };

      } catch (error) {
        console.error('❌ tRPC Drizzle: Error in toggleDrizzle:', error);
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Failed to toggle process status via Drizzle'
        });
      }
    }),

  /**
   * Get execution statistics - Complex aggregated query
   */
  getStatsDrizzle: businessProcedure
    .input(z.object({
      workflowId: z.string()
    }))
    .query(async ({ input }) => {
      try {
        const stats = await getProcessExecutionStats(input.workflowId);
        
        if (!stats) {
          throw new TRPCError({
            code: 'NOT_FOUND',
            message: 'Process statistics not found'
          });
        }

        // Calculate success rate
        const successRate = stats.total_executions > 0 
          ? (stats.successful_executions / stats.total_executions * 100).toFixed(2)
          : 0;

        return {
          success: true,
          data: {
            ...stats,
            success_rate: parseFloat(successRate),
            avg_execution_time_seconds: stats.avg_execution_time ? Math.round(stats.avg_execution_time) : null
          },
          method: 'drizzle-orm'
        };

      } catch (error) {
        console.error('❌ tRPC Drizzle: Error in getStatsDrizzle:', error);
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Failed to get process statistics via Drizzle'
        });
      }
    }),

});