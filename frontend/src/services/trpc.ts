/**
 * tRPC Client Configuration for PilotProOS Frontend
 * Type-safe API calls with end-to-end type inference
 */

import { createTRPCClient, httpLink } from '@trpc/client';
import { API_BASE_URL } from '../utils/api-config';

// Type inference from backend AppRouter (when available)
// Note: AppRouter type will be imported when backend uses TypeScript
type AppRouter = any; // Temporary placeholder

/**
 * tRPC Client - Type-Safe Business API Calls
 * Replaces traditional REST API calls with end-to-end type safety
 */
export const trpc = createTRPCClient<AppRouter>({
  links: [
    httpLink({
      url: `${API_BASE_URL}/api/trpc`,
      
      // Add authentication headers
      headers: () => ({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      }),

      // Handle errors and add logging
      fetch(url, options) {
        console.log('🔄 tRPC call:', url, options?.method);
        return fetch(url, {
          ...options,
          credentials: 'include', // For CORS
        }).then(response => {
          console.log('📡 tRPC response:', response.status, url);
          if (!response.ok) {
            console.error('❌ tRPC response failed:', response.status, response.statusText);
          }
          return response;
        });
      },
    }),
  ],
});

/**
 * Usage Examples (Type-Safe API Calls):
 * 
 * // Toggle workflow (fully typed)
 * const result = await trpc.workflow.toggle.mutate({
 *   workflowId: 'workflow_123',
 *   active: true
 * });
 * 
 * // Execute workflow
 * const execution = await trpc.workflow.execute.mutate({
 *   workflowId: 'workflow_123',
 *   executionData: { param1: 'value' }
 * });
 * 
 * // Stop workflow
 * const stopped = await trpc.workflow.stop.mutate({
 *   workflowId: 'workflow_123',
 *   executionId: 'exec_456'
 * });
 */

// Backward compatibility
export const trpcClient = trpc;

export type { AppRouter };