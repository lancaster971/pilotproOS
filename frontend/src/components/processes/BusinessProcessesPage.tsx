import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  GitBranch, 
  Play, 
  Pause, 
  Settings, 
  Search, 
  RefreshCw,
  Plus,
  Filter,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  Activity
} from 'lucide-react'
import { workflowsAPI } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/utils'
import AgentDetailModal from '../agents/AgentDetailModal'

export const WorkflowsPage: React.FC = () => {
  const { user } = useAuthStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null)
  const [timelineWorkflow, setTimelineWorkflow] = useState<any>(null)
  
  // Carica i workflow in modo sicuro
  const { data: workflows, isLoading, error, refetch } = useQuery({
    queryKey: ['workflows-list'],
    queryFn: async () => {
      try {
        const response = await workflowsAPI.list()
        return response.data.workflows || []
      } catch (err) {
        console.error('Error loading workflows:', err)
        return []
      }
    },
    refetchInterval: 60000,
    retry: 1,
    retryOnMount: false
  })

  const filteredWorkflows = (workflows || []).filter((workflow: any) => {
    const matchesSearch = workflow.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         workflow.tags?.some((tag: string) => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && workflow.active) ||
                         (statusFilter === 'inactive' && !workflow.active)
    return matchesSearch && matchesStatus
  })

  const getStatusColor = (active: boolean) => {
    return active 
      ? 'text-green-400 bg-green-500/10 border-green-500/30'
      : 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  }

  return (
    <div className="space-y-8">
      {/* Enhanced Header */}
      <div className="bg-gradient-to-r from-blue-900/30 to-green-900/30 rounded-2xl p-8 border border-green-500/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <GitBranch className="h-8 w-8 text-green-400" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gradient">
                🔄 Workflow Manager
              </h1>
              <p className="text-xl text-gray-300 mt-2">
                Gestisci e monitora tutti i tuoi workflow automatizzati con 
                <strong className="text-green-400 ml-1">trasparenza totale</strong>
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={() => refetch()}
              disabled={isLoading}
              className="btn-control disabled:opacity-50"
            >
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
              Aggiorna
            </button>
            
            <button className="btn-control-primary">
              <Plus className="h-4 w-4" />
              Nuovo Workflow
            </button>
          </div>
        </div>
        
        {/* Features Highlight */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <Eye className="h-6 w-6 text-green-400 mx-auto mb-2" />
            <h3 className="font-semibold text-white mb-1 text-center">Trasparenza Totale</h3>
            <p className="text-sm text-gray-400 text-center">Vedi ogni step dei workflow in tempo reale</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <GitBranch className="h-6 w-6 text-blue-400 mx-auto mb-2" />
            <h3 className="font-semibold text-white mb-1 text-center">Gestione Completa</h3>
            <p className="text-sm text-gray-400 text-center">Controlla tutti i workflow da un'unica dashboard</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <Activity className="h-6 w-6 text-purple-400 mx-auto mb-2" />
            <h3 className="font-semibold text-white mb-1 text-center">Monitoring Live</h3>
            <p className="text-sm text-gray-400 text-center">Performance e stato in tempo reale</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Workflows</p>
              <p className="text-2xl font-bold text-blue-400">
                {isLoading ? '-' : (workflows?.length || 0)}
              </p>
            </div>
            <GitBranch className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Workflows Attivi</p>
              <p className="text-2xl font-bold text-green-400">
                {isLoading ? '-' : (workflows?.filter((w: any) => w.active).length || 0)}
              </p>
            </div>
            <Play className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Workflows Inattivi</p>
              <p className="text-2xl font-bold text-gray-400">
                {isLoading ? '-' : (workflows?.filter((w: any) => !w.active).length || 0)}
              </p>
            </div>
            <Pause className="h-8 w-8 text-gray-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Tags Univoci</p>
              <p className="text-2xl font-bold text-purple-400">
                {isLoading ? '-' : 
                  new Set(workflows?.flatMap((w: any) => w.tags || [])).size || 0
                }
              </p>
            </div>
            <Filter className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="control-card p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Cerca workflows per nome o tag..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="btn-control h-10"
          >
            <option value="all">Tutti i status</option>
            <option value="active">Solo Attivi</option>
            <option value="inactive">Solo Inattivi</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {error ? (
        <div className="control-card p-6">
          <div className="text-center text-red-400">
            ⚠️ Errore nel caricamento dei workflow. Controlla la connessione al backend.
          </div>
        </div>
      ) : isLoading ? (
        <div className="control-card p-6">
          <div className="text-center text-gray-500">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
            Caricamento workflows...
          </div>
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <div className="control-card p-6">
          <div className="text-center text-gray-500">
            {workflows?.length === 0 ? 
              '📝 Nessun workflow presente. Inizia creando il tuo primo workflow!' :
              '🔍 Nessun workflow corrisponde ai filtri selezionati.'
            }
          </div>
        </div>
      ) : (
        <>
          {/* Enhanced Workflow Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredWorkflows.map((workflow: any) => (
              <div 
                key={workflow.id} 
                className="control-card p-6 cursor-pointer hover:border-green-500/50 transition-all hover:scale-105"
                onClick={() => setSelectedWorkflow(workflow)}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-500/10 border border-green-500/30 rounded-lg">
                      <GitBranch className="h-6 w-6 text-green-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">{workflow.name || 'Untitled'}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <CheckCircle className={cn('h-3 w-3', workflow.active ? 'text-green-400' : 'text-gray-400')} />
                        <span className={cn('text-xs font-medium', workflow.active ? 'text-green-400' : 'text-gray-400')}>
                          {workflow.active ? 'Attivo' : 'Inattivo'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <Activity className="h-5 w-5 text-blue-400" />
                </div>

                {/* Workflow Info */}
                <div className="space-y-3 mb-4">
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Settings className="h-4 w-4 text-blue-400" />
                      <span className="text-sm font-medium text-white">Workflow Stats</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-400">Nodi:</span>
                        <span className="text-white ml-1">{workflow.node_count || 0}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Esecuzioni:</span>
                        <span className="text-green-400 ml-1">{workflow.execution_count || 0}</span>
                      </div>
                    </div>
                  </div>

                  {/* Business Context */}
                  <div className="bg-blue-900/20 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <GitBranch className="h-4 w-4 text-blue-400" />
                      <span className="text-sm font-medium text-white">Workflow Type</span>
                    </div>
                    <p className="text-xs text-blue-300">
                      {workflow.has_webhook ? 'Webhook-triggered automation' : 'Manual/scheduled workflow'}
                    </p>
                  </div>

                  {/* Tags Section */}
                  {(workflow.tags && workflow.tags.length > 0) && (
                    <div className="bg-purple-900/20 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Filter className="h-4 w-4 text-purple-400" />
                        <span className="text-sm font-medium text-white">Tags</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {workflow.tags.slice(0, 3).map((tag: string, index: number) => (
                          <span 
                            key={index}
                            className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs"
                          >
                            {tag}
                          </span>
                        ))}
                        {workflow.tags.length > 3 && (
                          <span className="text-purple-400 text-xs">+{workflow.tags.length - 3}</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="border-t border-gray-700 pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-400">Killer Features</p>
                      <p className="text-sm font-medium text-white">
                        Full transparency & AI timeline
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button 
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs flex items-center gap-1"
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedWorkflow(workflow)
                        }}
                      >
                        <Settings className="h-3 w-3" />
                        Dettagli
                      </button>
                      <button 
                        className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs flex items-center gap-1"
                        onClick={(e) => {
                          e.stopPropagation()
                          setTimelineWorkflow(workflow)
                        }}
                      >
                        <Activity className="h-3 w-3" />
                        Timeline
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Table View Alternative (Toggle) */}
          <div className="control-card overflow-hidden">
            <div className="p-4 border-b border-gray-800">
              <h3 className="text-white font-medium">Tabella Workflows</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Nome Workflow</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Status</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Tags</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Ultima Modifica</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredWorkflows.map((workflow: any) => (
                    <tr 
                      key={workflow.id} 
                      className="border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors cursor-pointer"
                      onClick={() => setSelectedWorkflow(workflow)}
                    >
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <GitBranch className="h-4 w-4 text-blue-400" />
                          <span className="text-white font-medium">{workflow.name || 'Untitled'}</span>
                        </div>
                      </td>
                      
                      <td className="p-4">
                        <span className={cn(
                          'inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border',
                          getStatusColor(workflow.active)
                        )}>
                          {workflow.active ? (
                            <>
                              <CheckCircle className="h-3 w-3" />
                              Attivo
                            </>
                          ) : (
                            <>
                              <XCircle className="h-3 w-3" />
                              Inattivo
                            </>
                          )}
                        </span>
                      </td>
                      
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1">
                          {(workflow.tags || []).slice(0, 3).map((tag: string, index: number) => (
                            <span 
                              key={index}
                              className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded text-xs border border-blue-500/30"
                            >
                              {tag}
                            </span>
                          ))}
                          {(workflow.tags || []).length > 3 && (
                            <span className="text-gray-400 text-xs">+{workflow.tags.length - 3}</span>
                          )}
                        </div>
                      </td>
                      
                      <td className="p-4">
                        <div className="flex items-center gap-1 text-gray-400 text-sm">
                          <Clock className="h-3 w-3" />
                          {workflow.updatedAt ? 
                            new Date(workflow.updatedAt).toLocaleDateString('it-IT') : 
                            'N/A'
                          }
                        </div>
                      </td>
                      
                      <td className="p-4">
                        <div className="flex items-center gap-1">
                          <button 
                            className="p-1 text-gray-400 hover:text-blue-400 transition-colors"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedWorkflow(workflow)
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button 
                            className="p-1 text-gray-400 hover:text-yellow-400 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Settings className="h-4 w-4" />
                          </button>
                          <button 
                            className="p-1 text-gray-400 hover:text-green-400 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {workflow.active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Workflow Detail Modal */}
      {selectedWorkflow && (
        <AgentDetailModal
          workflow={selectedWorkflow}
          workflowId={selectedWorkflow.id}
          tenantId={user?.tenantId || 'client_simulation_a'}
          isOpen={!!selectedWorkflow}
          onClose={() => setSelectedWorkflow(null)}
          isWorkflowMode={true}
        />
      )}

      {/* Timeline Modal - KILLER FEATURE */}
      {timelineWorkflow && (
        <AgentDetailModal
          workflow={timelineWorkflow}
          workflowId={timelineWorkflow.id}
          tenantId={user?.tenantId || 'client_simulation_a'}
          isOpen={!!timelineWorkflow}
          onClose={() => setTimelineWorkflow(null)}
          isWorkflowMode={false} // AI Mode per la timeline!
        />
      )}
    </div>
  )
}