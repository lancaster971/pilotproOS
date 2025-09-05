<!--
  tRPC Integration Test Component
  Demonstrates type-safe API calls to backend
-->
<template>
  <div class="p-6 bg-white rounded-lg shadow-md max-w-md mx-auto">
    <h3 class="text-lg font-semibold mb-4 text-gray-800">
      🔧 tRPC Integration Test
    </h3>
    
    <!-- Loading State -->
    <div v-if="loading" class="text-blue-600 flex items-center gap-2 mb-4">
      <div class="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
      Processing tRPC request...
    </div>
    
    <!-- Error State -->
    <div v-if="error" class="text-red-600 bg-red-50 p-3 rounded mb-4">
      ❌ {{ error }}
    </div>
    
    <!-- Test Buttons -->
    <div class="space-y-3">
      <!-- Workflow Router Tests -->
      <button 
        @click="testToggleWorkflow"
        :disabled="loading"
        class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white px-4 py-2 rounded transition-colors"
      >
        Test workflow.toggle (tRPC)
      </button>
      
      <!-- Processes Router Tests -->
      <button 
        @click="testGetProcesses"
        :disabled="loading"
        class="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white px-4 py-2 rounded transition-colors"
      >
        Test processes.getAll (tRPC)
      </button>
      
      <!-- Analytics Router Tests -->
      <button 
        @click="testGetAnalytics"
        :disabled="loading"
        class="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white px-4 py-2 rounded transition-colors"
      >
        Test analytics.getOverview (tRPC)
      </button>
      
      <!-- Executions Router Tests -->
      <button 
        @click="testGetExecutions"
        :disabled="loading"
        class="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-orange-300 text-white px-4 py-2 rounded transition-colors"
      >
        Test executions.getProcessRuns (tRPC)
      </button>
      
      <!-- System Router Tests -->
      <button 
        @click="testSystemHealth"
        :disabled="loading"
        class="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white px-4 py-2 rounded transition-colors"
      >
        Test system.health (tRPC)
      </button>
    </div>
    
    <!-- Success Response -->
    <div v-if="lastResponse" class="mt-4 bg-green-50 p-3 rounded">
      <p class="text-sm text-green-800 font-semibold">✅ tRPC Response:</p>
      <pre class="text-xs text-green-700 mt-1 overflow-x-auto">{{ JSON.stringify(lastResponse, null, 2) }}</pre>
    </div>
    
    <p class="text-xs text-gray-500 mt-4">
      🎯 This component tests end-to-end type safety between Vue 3 frontend and tRPC backend.
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useTrpcWorkflow } from '../composables/useTrpc';
import { trpcClient } from '../services/trpc';

const { loading, error, toggleWorkflow, executeWorkflow, stopWorkflow } = useTrpcWorkflow();
const lastResponse = ref(null);

// Test workflow toggle with dummy data
const testToggleWorkflow = async () => {
  try {
    const result = await toggleWorkflow('test_workflow_123', true);
    lastResponse.value = result;
  } catch (err) {
    // Error already handled by composable
    console.log('Toggle failed (expected for test ID)');
  }
};

// Test workflow execution with dummy data  
const testExecuteWorkflow = async () => {
  try {
    const result = await executeWorkflow('test_workflow_123', { testParam: 'value' });
    lastResponse.value = result;
  } catch (err) {
    // Error already handled by composable
    console.log('Execute failed (expected for test ID)');
  }
};

// Test workflow stop with dummy data
const testStopWorkflow = async () => {
  try {
    const result = await stopWorkflow('test_workflow_123', 'test_execution_456');
    lastResponse.value = result;
  } catch (err) {
    // Error already handled by composable
    console.log('Stop failed (expected for test ID)');
  }
};

// Test processes.getAll
const testGetProcesses = async () => {
  try {
    const result = await trpcClient.processes.getAll.query();
    lastResponse.value = result;
    console.log('✅ processes.getAll success:', result);
  } catch (err) {
    console.error('❌ processes.getAll failed:', err);
    lastResponse.value = { error: err.message };
  }
};

// Test analytics.getOverview
const testGetAnalytics = async () => {
  try {
    const result = await trpcClient.analytics.getOverview.query();
    lastResponse.value = result;
    console.log('✅ analytics.getOverview success:', result);
  } catch (err) {
    console.error('❌ analytics.getOverview failed:', err);
    lastResponse.value = { error: err.message };
  }
};

// Test executions.getProcessRuns
const testGetExecutions = async () => {
  try {
    const result = await trpcClient.executions.getProcessRuns.query({ limit: 10 });
    lastResponse.value = result;
    console.log('✅ executions.getProcessRuns success:', result);
  } catch (err) {
    console.error('❌ executions.getProcessRuns failed:', err);
    lastResponse.value = { error: err.message };
  }
};

// Test system.health
const testSystemHealth = async () => {
  try {
    const result = await trpcClient.system.health.query();
    lastResponse.value = result;
    console.log('✅ system.health success:', result);
  } catch (err) {
    console.error('❌ system.health failed:', err);
    lastResponse.value = { error: err.message };
  }
};
</script>