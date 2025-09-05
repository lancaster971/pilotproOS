<!--
  tRPC Integration Test Page
  Full-featured test environment for tRPC end-to-end type safety
-->
<template>
  <MainLayout>
    <div class="p-6 space-y-6 max-w-4xl mx-auto">
      <!-- Page Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gradient mb-2">🔧 tRPC Integration Test</h1>
        <p class="text-text-muted">
          End-to-end type safety test between Vue 3 frontend and tRPC backend
        </p>
      </div>
      
      <!-- Integration Status -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card class="premium-glass">
          <template #content>
            <div class="p-4 text-center">
              <div class="w-12 h-12 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-3">
                ✅
              </div>
              <h3 class="font-semibold text-green-800">Backend tRPC</h3>
              <p class="text-sm text-green-600">Server active on :3001</p>
            </div>
          </template>
        </Card>
        
        <Card class="premium-glass">
          <template #content>
            <div class="p-4 text-center">
              <div class="w-12 h-12 mx-auto bg-blue-100 rounded-full flex items-center justify-center mb-3">
                🔄
              </div>
              <h3 class="font-semibold text-blue-800">Vue 3 Client</h3>
              <p class="text-sm text-blue-600">tRPC client configured</p>
            </div>
          </template>
        </Card>
        
        <Card class="premium-glass">
          <template #content>
            <div class="p-4 text-center">
              <div class="w-12 h-12 mx-auto bg-purple-100 rounded-full flex items-center justify-center mb-3">
                🎯
              </div>
              <h3 class="font-semibold text-purple-800">Type Safety</h3>
              <p class="text-sm text-purple-600">End-to-end validation</p>
            </div>
          </template>
        </Card>
      </div>
      
      <!-- Test Component -->
      <div class="flex justify-center">
        <TrpcTest />
      </div>
      
      <!-- API Documentation -->
      <Card class="premium-glass mt-8">
        <template #header>
          <div class="p-6 pb-0">
            <h3 class="text-xl font-bold">📚 tRPC API Endpoints</h3>
            <p class="text-sm text-text-muted mt-1">Available type-safe procedures</p>
          </div>
        </template>
        <template #content>
          <div class="p-6 space-y-4">
            <!-- Toggle Endpoint -->
            <div class="bg-surface/30 p-4 rounded-lg">
              <div class="flex items-center gap-2 mb-2">
                <Badge value="MUTATION" severity="warning" />
                <code class="text-sm font-mono">workflow.toggle</code>
              </div>
              <p class="text-sm text-text-muted mb-2">Toggle workflow active status</p>
              <div class="bg-background p-3 rounded text-xs font-mono">
                <span class="text-green-600">// Input Schema</span><br>
                {<br>
                &nbsp;&nbsp;workflowId: string,<br>
                &nbsp;&nbsp;active: boolean<br>
                }<br><br>
                <span class="text-blue-600">// Response Type</span><br>
                {<br>
                &nbsp;&nbsp;success: boolean,<br>
                &nbsp;&nbsp;workflow: WorkflowData,<br>
                &nbsp;&nbsp;n8nSync: SyncResult<br>
                }
              </div>
            </div>
            
            <!-- Execute Endpoint -->
            <div class="bg-surface/30 p-4 rounded-lg">
              <div class="flex items-center gap-2 mb-2">
                <Badge value="MUTATION" severity="warning" />
                <code class="text-sm font-mono">workflow.execute</code>
              </div>
              <p class="text-sm text-text-muted mb-2">Execute workflow with optional data</p>
              <div class="bg-background p-3 rounded text-xs font-mono">
                <span class="text-green-600">// Input Schema</span><br>
                {<br>
                &nbsp;&nbsp;workflowId: string,<br>
                &nbsp;&nbsp;executionData?: any<br>
                }<br><br>
                <span class="text-blue-600">// Response Type</span><br>
                {<br>
                &nbsp;&nbsp;success: boolean,<br>
                &nbsp;&nbsp;execution: ExecutionData,<br>
                &nbsp;&nbsp;n8nData: any<br>
                }
              </div>
            </div>
            
            <!-- Stop Endpoint -->
            <div class="bg-surface/30 p-4 rounded-lg">
              <div class="flex items-center gap-2 mb-2">
                <Badge value="MUTATION" severity="warning" />
                <code class="text-sm font-mono">workflow.stop</code>
              </div>
              <p class="text-sm text-text-muted mb-2">Stop running workflow execution</p>
              <div class="bg-background p-3 rounded text-xs font-mono">
                <span class="text-green-600">// Input Schema</span><br>
                {<br>
                &nbsp;&nbsp;workflowId: string,<br>
                &nbsp;&nbsp;executionId: string<br>
                }<br><br>
                <span class="text-blue-600">// Response Type</span><br>
                {<br>
                &nbsp;&nbsp;success: boolean,<br>
                &nbsp;&nbsp;execution: ExecutionData,<br>
                &nbsp;&nbsp;n8nData: any<br>
                }
              </div>
            </div>
          </div>
        </template>
      </Card>
      
      <!-- Benefits Card -->
      <Card class="premium-glass premium-glow">
        <template #header>
          <div class="p-6 pb-0">
            <h3 class="text-xl font-bold">🚀 tRPC Benefits</h3>
            <p class="text-sm text-text-muted mt-1">Why tRPC improves development</p>
          </div>
        </template>
        <template #content>
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  ✅
                </div>
                <div>
                  <h4 class="font-semibold text-green-800 mb-1">Type Safety</h4>
                  <p class="text-sm text-text-muted">End-to-end TypeScript types automatically synced</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  🔄
                </div>
                <div>
                  <h4 class="font-semibold text-blue-800 mb-1">Auto-Completion</h4>
                  <p class="text-sm text-text-muted">IDE suggestions for API calls and responses</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  ⚡
                </div>
                <div>
                  <h4 class="font-semibold text-purple-800 mb-1">Request Batching</h4>
                  <p class="text-sm text-text-muted">Multiple API calls automatically batched</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  🛡️
                </div>
                <div>
                  <h4 class="font-semibold text-orange-800 mb-1">Runtime Validation</h4>
                  <p class="text-sm text-text-muted">Zod schema validation on requests/responses</p>
                </div>
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import MainLayout from '../components/layout/MainLayout.vue'
import TrpcTest from '../components/TrpcTest.vue'
import Card from 'primevue/card'
import Badge from 'primevue/badge'
</script>