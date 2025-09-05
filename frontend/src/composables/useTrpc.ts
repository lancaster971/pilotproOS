/**
 * Vue 3 Composable for tRPC Integration
 * Reactive wrapper around tRPC client calls
 */

import { ref, reactive } from 'vue';
import { trpc } from '../services/trpc';
import { useToast } from 'vue-toastification';

/**
 * tRPC Workflow Operations Composable
 * Provides reactive state management for business process operations
 */
export function useTrpcWorkflow() {
  const toast = useToast();
  
  // Reactive state for workflow operations
  const state = reactive({
    loading: false,
    error: null as string | null,
  });

  // Toggle workflow active status
  const toggleWorkflow = async (workflowId: string, active: boolean) => {
    state.loading = true;
    state.error = null;

    try {
      const result = await trpc.workflow.toggle.mutate({
        workflowId,
        active
      });

      toast.success(
        active 
          ? `✅ Business Process "${result.workflow.name}" attivato`
          : `⏸️ Business Process "${result.workflow.name}" disattivato`
      );

      state.loading = false;
      return result;

    } catch (error: any) {
      state.error = error.message || 'Errore durante toggle del Business Process';
      toast.error(state.error);
      state.loading = false;
      throw error;
    }
  };

  // Execute workflow manually
  const executeWorkflow = async (workflowId: string, executionData?: any) => {
    state.loading = true;
    state.error = null;

    try {
      const result = await trpc.workflow.execute.mutate({
        workflowId,
        executionData
      });

      toast.success(
        `🚀 Business Process "${result.execution.workflowName}" avviato`
      );

      state.loading = false;
      return result;

    } catch (error: any) {
      state.error = error.message || 'Errore durante esecuzione del Business Process';
      toast.error(state.error);
      state.loading = false;
      throw error;
    }
  };

  // Stop workflow execution
  const stopWorkflow = async (workflowId: string, executionId: string) => {
    state.loading = true;
    state.error = null;

    try {
      const result = await trpc.workflow.stop.mutate({
        workflowId,
        executionId
      });

      toast.success(
        `🛑 Business Process "${result.execution.workflowName}" fermato`
      );

      state.loading = false;
      return result;

    } catch (error: any) {
      state.error = error.message || 'Errore durante stop del Business Process';
      toast.error(state.error);
      state.loading = false;
      throw error;
    }
  };

  return {
    // Reactive state
    ...state,
    
    // Actions
    toggleWorkflow,
    executeWorkflow,
    stopWorkflow,
  };
}

/**
 * Usage in Vue Components:
 * 
 * <script setup>
 * import { useTrpcWorkflow } from '@/composables/useTrpc';
 * 
 * const { loading, error, toggleWorkflow, executeWorkflow } = useTrpcWorkflow();
 * 
 * // Toggle workflow
 * const handleToggle = () => {
 *   toggleWorkflow('workflow_123', true);
 * };
 * 
 * // Execute workflow  
 * const handleExecute = () => {
 *   executeWorkflow('workflow_123', { param: 'value' });
 * };
 * </script>
 * 
 * <template>
 *   <button @click="handleToggle" :disabled="loading">
 *     {{ loading ? 'Processing...' : 'Toggle Workflow' }}
 *   </button>
 *   
 *   <div v-if="error" class="error">{{ error }}</div>
 * </template>
 */