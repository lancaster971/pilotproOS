<template>
  <MainLayout>
    <div class="p-6 space-y-4">
      <h1 class="text-2xl font-bold">tRPC Debug Test</h1>
      
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-surface border border-border rounded-lg p-4">
          <h3 class="text-lg font-semibold mb-3">Test Results</h3>
          <div class="space-y-2">
            <div>Status: <span :class="status === 'success' ? 'text-green-500' : status === 'error' ? 'text-red-500' : 'text-yellow-500'">{{ status }}</span></div>
            <div>Workflows: {{ workflowCount }}</div>
            <div>Error: {{ error }}</div>
          </div>
        </div>
        
        <div class="bg-surface border border-border rounded-lg p-4">
          <h3 class="text-lg font-semibold mb-3">Actions</h3>
          <div class="space-y-2">
            <button @click="testTRPC" class="btn-primary">Test tRPC</button>
            <button @click="testREST" class="btn-primary">Test REST (Fallback)</button>
            <button @click="clearResults" class="btn-primary">Clear</button>
          </div>
        </div>
      </div>
      
      <div v-if="rawData" class="bg-surface border border-border rounded-lg p-4">
        <h3 class="text-lg font-semibold mb-3">Raw Data</h3>
        <pre class="text-xs overflow-auto">{{ JSON.stringify(rawData, null, 2) }}</pre>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MainLayout from '../components/layout/MainLayout.vue'
import { trpc } from '../services/trpc'

const status = ref('idle')
const workflowCount = ref(0)
const error = ref('')
const rawData = ref(null)

const testTRPC = async () => {
  status.value = 'loading'
  error.value = ''
  rawData.value = null
  
  try {
    console.log('🔄 Testing tRPC...')
    const result = await trpc.processes.getAll.query()
    console.log('✅ tRPC result:', result)
    
    status.value = 'success'
    workflowCount.value = result?.processes?.length || 0
    rawData.value = result
    
  } catch (err: any) {
    console.error('❌ tRPC error:', err)
    status.value = 'error'
    error.value = err.message || 'Unknown error'
    rawData.value = { error: err }
  }
}

const testREST = async () => {
  status.value = 'loading'
  error.value = ''
  rawData.value = null
  
  try {
    console.log('🔄 Testing REST...')
    const response = await fetch('http://localhost:3001/api/business/processes')
    const result = await response.json()
    console.log('✅ REST result:', result)
    
    status.value = 'success'
    workflowCount.value = result?.data?.length || 0
    rawData.value = result
    
  } catch (err: any) {
    console.error('❌ REST error:', err)
    status.value = 'error'
    error.value = err.message || 'Unknown error'
    rawData.value = { error: err }
  }
}

const clearResults = () => {
  status.value = 'idle'
  workflowCount.value = 0
  error.value = ''
  rawData.value = null
}
</script>