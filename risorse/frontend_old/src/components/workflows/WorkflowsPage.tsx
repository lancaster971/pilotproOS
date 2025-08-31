import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Search,
  Download,
  Plus,
  Play,
  Pause,
  Archive,
  Clock,
  GitBranch,
  Activity,
  Calendar,
  ChevronRight,
} from 'lucide-react'
import { tenantAPI } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import { formatDate, cn } from '../../lib/utils'
import { WorkflowDetailModal } from './WorkflowDetailModal'

interface Workflow {
  id: string
  name: string
  active: boolean
  has_webhook: boolean
  is_archived: boolean
  created_at: string
  updated_at: string
  node_count: number
  execution_count: number
  last_execution?: string
}

const getStatusInfo = (workflow: Workflow) => {
  if (workflow.is_archived) {
    return {
      status: 'Archiviato',
      color: 'text-gray-500',
      bgColor: 'bg-gray-500/10',
      borderColor: 'border-gray-500/30',
      dotColor: 'bg-gray-500'
    }
  }
  if (workflow.active) {
    return {
      status: 'Attivo',
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/30',
      dotColor: 'bg-green-500'
    }
  }
  return {
    status: 'Inattivo',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    dotColor: 'bg-yellow-500'
  }
}

export const WorkflowsPage: React.FC = () => {
  const { user } = useAuthStore()
  const tenantId = user?.tenantId || 'default_tenant'
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'archived'>('all')
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null)

  // Fetch workflows del tenant
  const { data: workflowsData, isLoading, error } = useQuery({
    queryKey: ['tenant-workflows', tenantId],
    queryFn: async () => {
      const response = await tenantAPI.workflows(tenantId)
      return response.data
    },
    refetchInterval: 30000,
  })

  const workflows = workflowsData?.workflows || []

  // Filtra workflows
  const filteredWorkflows = workflows.filter((workflow: Workflow) => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchTerm.toLowerCase())
    
    if (!matchesSearch) return false

    switch (statusFilter) {
      case 'active':
        return workflow.active && !workflow.is_archived
      case 'inactive':
        return !workflow.active && !workflow.is_archived
      case 'archived':
        return workflow.is_archived
      default:
        return true
    }
  })

  // Statistiche
  const stats = {
    total: workflows.length,
    active: workflows.filter((w: Workflow) => w.active && !w.is_archived).length,
    inactive: workflows.filter((w: Workflow) => !w.active && !w.is_archived).length,
    archived: workflows.filter((w: Workflow) => w.is_archived).length,
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="control-card p-6 h-24 skeleton" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="control-card p-6">
        <p className="text-red-400">Errore nel caricamento dei workflows</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">
            Workflows - {workflowsData?.tenantId}
          </h1>
          <p className="text-gray-500 mt-1">
            Gestisci i tuoi workflow automation
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-control">
            <Download className="h-4 w-4" />
            Esporta
          </button>
          <button className="btn-control-primary">
            <Plus className="h-4 w-4" />
            Nuovo Workflow
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
              <p className="text-sm text-gray-400">Totali</p>
            </div>
            <GitBranch className="h-8 w-8 text-gray-600" />
          </div>
        </div>
        
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold text-green-400">{stats.active}</p>
              <p className="text-sm text-gray-400">Attivi</p>
            </div>
            <Activity className="h-8 w-8 text-green-500" />
          </div>
        </div>
        
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold text-yellow-400">{stats.inactive}</p>
              <p className="text-sm text-gray-400">Inattivi</p>
            </div>
            <Pause className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
        
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold text-gray-400">{stats.archived}</p>
              <p className="text-sm text-gray-400">Archiviati</p>
            </div>
            <Archive className="h-8 w-8 text-gray-500" />
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="control-card p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Cerca workflows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-md text-white focus:border-green-500 focus:outline-none"
            />
          </div>
          
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-4 py-2 bg-gray-900 border border-gray-800 rounded-md text-white focus:border-green-500 focus:outline-none"
          >
            <option value="all">Tutti gli status</option>
            <option value="active">Solo Attivi</option>
            <option value="inactive">Solo Inattivi</option>
            <option value="archived">Solo Archiviati</option>
          </select>
        </div>
      </div>

      {/* Workflows Grid */}
      <div>
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">
            Workflows ({filteredWorkflows.length})
          </h2>
        </div>
        
        {filteredWorkflows.length === 0 ? (
          <div className="control-card p-8 text-center text-gray-500">
            <GitBranch className="h-12 w-12 mx-auto mb-4 text-gray-600" />
            <p>Nessun workflow trovato</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredWorkflows.map((workflow: Workflow) => {
              const statusInfo = getStatusInfo(workflow)
              
              return (
                <div 
                  key={workflow.id} 
                  className="control-card p-6 hover:border-green-500/30 hover:shadow-lg hover:shadow-green-500/10 transition-all duration-200 cursor-pointer"
                  onClick={() => setSelectedWorkflow(workflow)}
                >
                  {/* Header con Status */}
                  <div className="flex items-start justify-between mb-4">
                    <span className={cn(
                      'inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border',
                      statusInfo.bgColor,
                      statusInfo.borderColor,
                      statusInfo.color
                    )}>
                      <div className={cn('w-1.5 h-1.5 rounded-full', statusInfo.dotColor)} />
                      {statusInfo.status}
                    </span>
                    {workflow.has_webhook && (
                      <span className="badge-control">
                        Webhook
                      </span>
                    )}
                  </div>

                  {/* Nome Workflow */}
                  <h3 className="text-lg font-medium text-white mb-4 leading-tight truncate" title={workflow.name}>
                    {workflow.name}
                  </h3>
                  
                  {/* Stats */}
                  <div className="space-y-3 mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400 flex items-center gap-1">
                        <GitBranch className="h-3 w-3" />
                        Nodi
                      </span>
                      <span className="text-white font-medium">{workflow.node_count}</span>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400 flex items-center gap-1">
                        <Play className="h-3 w-3" />
                        Esecuzioni
                      </span>
                      <span className="text-white font-medium">{workflow.execution_count}</span>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400 flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Creato
                      </span>
                      <span className="text-white font-medium">{formatDate(workflow.created_at).split(' ')[0]}</span>
                    </div>
                    
                    {workflow.last_execution && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-400 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Ultima
                        </span>
                        <span className="text-white font-medium">{formatDate(workflow.last_execution).split(' ')[0]}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-4 border-t border-gray-800">
                    <button
                      onClick={(e) => {
                        e.stopPropagation() // Prevent card click
                        // TODO: Add toggle active logic
                      }}
                      className={cn(
                        'flex-1 btn-control text-xs py-2',
                        workflow.is_archived && 'opacity-50 cursor-not-allowed'
                      )}
                      disabled={workflow.is_archived}
                    >
                      {workflow.active ? 'Pausa' : 'Avvia'}
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation() // Prevent card click
                        setSelectedWorkflow(workflow)
                      }}
                      className="p-2 text-gray-400 hover:text-white transition-colors"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
      
      {/* Workflow Detail Modal */}
      {selectedWorkflow && (
        <WorkflowDetailModal
          workflow={selectedWorkflow}
          tenantId={tenantId}
          onClose={() => setSelectedWorkflow(null)}
        />
      )}
    </div>
  )
}