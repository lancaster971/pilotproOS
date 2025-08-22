import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Workflow, WorkflowStats } from '../types'
import { apiClient } from '../services/api'

export const useWorkflowsStore = defineStore('workflows', () => {
  // State - same structure as n8n workflow store
  const workflows = ref<Workflow[]>([])
  const selectedWorkflow = ref<Workflow | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastFetch = ref<number>(0)

  // Getters - computed properties like n8n
  const stats = computed((): WorkflowStats => ({
    total: workflows.value.length,
    active: workflows.value.filter(w => w.active && !w.is_archived).length,
    inactive: workflows.value.filter(w => !w.active && !w.is_archived).length,
    archived: workflows.value.filter(w => w.is_archived).length,
  }))

  const activeWorkflows = computed(() => 
    workflows.value.filter(w => w.active && !w.is_archived)
  )

  const recentWorkflows = computed(() => 
    workflows.value
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      .slice(0, 10)
  )

  // Actions - same API approach as n8n
  const fetchWorkflows = async () => {
    isLoading.value = true
    error.value = null

    try {
      // Use our PilotProOS backend API
      const response = await apiClient.get('/api/business/processes')
      const data = response.data

      // Transform backend data to workflow format
      workflows.value = (data.data || []).map((process: any): Workflow => ({
        id: process.process_id,
        name: process.process_name,
        active: process.is_active,
        is_archived: false,
        created_at: process.created_date || new Date().toISOString(),
        updated_at: process.last_modified || new Date().toISOString(),
        node_count: 5, // Default value
        execution_count: parseInt(process.executions_today) || 0,
        has_webhook: false,
        last_execution: process.last_modified,
        tags: [],
        settings: {},
      }))

      lastFetch.value = Date.now()
      console.log('✅ Workflows loaded:', workflows.value.length)
      
    } catch (err: any) {
      error.value = err.message || 'Failed to load workflows'
      console.error('❌ Failed to load workflows:', err)
      
      // Fallback data for demo
      workflows.value = [{
        id: '1',
        name: 'TRY Backend',
        active: true,
        is_archived: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        node_count: 5,
        execution_count: 0,
        has_webhook: false,
        last_execution: null,
        tags: [],
        settings: {},
      }]
    } finally {
      isLoading.value = false
    }
  }

  const selectWorkflow = (workflow: Workflow) => {
    selectedWorkflow.value = workflow
    console.log('✅ Workflow selected:', workflow.name)
  }

  const toggleWorkflow = async (workflow: Workflow) => {
    try {
      // In real implementation, call backend API
      workflow.active = !workflow.active
      console.log(`✅ Workflow ${workflow.active ? 'activated' : 'deactivated'}:`, workflow.name)
    } catch (err: any) {
      console.error('❌ Failed to toggle workflow:', err)
    }
  }

  const createWorkflow = async (workflowData: Partial<Workflow>) => {
    try {
      // In real implementation, call backend API
      const newWorkflow: Workflow = {
        id: 'new-' + Date.now(),
        name: workflowData.name || 'New Workflow',
        active: false,
        is_archived: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        node_count: 0,
        execution_count: 0,
        has_webhook: false,
        last_execution: null,
        tags: workflowData.tags || [],
        settings: workflowData.settings || {},
      }
      
      workflows.value.push(newWorkflow)
      console.log('✅ Workflow created:', newWorkflow.name)
      return newWorkflow
    } catch (err: any) {
      console.error('❌ Failed to create workflow:', err)
      throw err
    }
  }

  return {
    // State
    workflows,
    selectedWorkflow,
    isLoading,
    error,
    lastFetch,
    
    // Getters
    stats,
    activeWorkflows,
    recentWorkflows,
    
    // Actions
    fetchWorkflows,
    selectWorkflow,
    toggleWorkflow,
    createWorkflow,
  }
})