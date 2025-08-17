import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Activity, 
  Play, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Search, 
  RefreshCw,
  Filter,
  Eye,
  RotateCcw
} from 'lucide-react'
import { executionsAPI } from '../../services/api'
import { cn } from '../../lib/utils'

export const ExecutionsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'success' | 'error' | 'running'>('all')
  
  // Carica le esecuzioni in modo sicuro
  const { data: executions, isLoading, error, refetch } = useQuery({
    queryKey: ['executions-list'],
    queryFn: async () => {
      try {
        // Fix: usa endpoint tenant per dati reali
        const response = await fetch('/api/tenant/client_simulation_a/executions', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        })
        const data = await response.json()
        return data.executions || []
      } catch (err) {
        console.error('Error loading executions:', err)
        return []
      }
    },
    refetchInterval: 30000,
    retry: 1,
    retryOnMount: false
  })

  const filteredExecutions = (executions || []).filter((execution: any) => {
    const matchesSearch = execution.workflowName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         execution.id?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || execution.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'success':
        return { icon: CheckCircle, color: 'text-green-400', bgColor: 'bg-green-500/10', label: 'Success' }
      case 'error':
        return { icon: XCircle, color: 'text-red-400', bgColor: 'bg-red-500/10', label: 'Error' }
      case 'running':
        return { icon: Play, color: 'text-blue-400', bgColor: 'bg-blue-500/10', label: 'Running' }
      default:
        return { icon: Clock, color: 'text-gray-400', bgColor: 'bg-gray-500/10', label: 'Unknown' }
    }
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">
            ⚡ Workflow Executions
          </h1>
          <p className="text-gray-500 mt-1">
            Monitora l'esecuzione dei tuoi workflow in tempo reale
          </p>
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
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Executions</p>
              <p className="text-2xl font-bold text-blue-400">
                {isLoading ? '-' : (executions?.length || 0)}
              </p>
            </div>
            <Activity className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Successful</p>
              <p className="text-2xl font-bold text-green-400">
                {isLoading ? '-' : (executions?.filter((e: any) => e.status === 'success').length || 0)}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Failed</p>
              <p className="text-2xl font-bold text-red-400">
                {isLoading ? '-' : (executions?.filter((e: any) => e.status === 'error').length || 0)}
              </p>
            </div>
            <XCircle className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Running</p>
              <p className="text-2xl font-bold text-yellow-400">
                {isLoading ? '-' : (executions?.filter((e: any) => e.status === 'running').length || 0)}
              </p>
            </div>
            <Play className="h-8 w-8 text-yellow-500" />
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
              placeholder="Cerca per workflow o ID esecuzione..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
          >
            <option value="all">Tutti gli stati</option>
            <option value="success">Solo Successi</option>
            <option value="error">Solo Errori</option>
            <option value="running">Solo In Esecuzione</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {error ? (
        <div className="control-card p-6">
          <div className="text-center text-red-400">
            ⚠️ Errore nel caricamento delle esecuzioni. Controlla la connessione al backend.
          </div>
        </div>
      ) : isLoading ? (
        <div className="control-card p-6">
          <div className="text-center text-gray-500">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
            Caricamento esecuzioni...
          </div>
        </div>
      ) : filteredExecutions.length === 0 ? (
        <div className="control-card p-6">
          <div className="text-center text-gray-500">
            {executions?.length === 0 ? 
              '📊 Nessuna esecuzione presente. I workflow verranno visualizzati qui una volta eseguiti.' :
              '🔍 Nessuna esecuzione corrisponde ai filtri selezionati.'
            }
          </div>
        </div>
      ) : (
        <div className="control-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Workflow</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Status</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Durata</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Avviato</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {filteredExecutions.map((execution: any) => {
                  const statusInfo = getStatusInfo(execution.status)
                  const StatusIcon = statusInfo.icon
                  
                  return (
                    <tr 
                      key={execution.id} 
                      className="border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors"
                    >
                      <td className="p-4">
                        <div>
                          <div className="text-white font-medium">{execution.workflowName || 'Unknown Workflow'}</div>
                          <div className="text-xs text-gray-400">ID: {execution.id}</div>
                        </div>
                      </td>
                      
                      <td className="p-4">
                        <span className={cn(
                          'inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium',
                          statusInfo.bgColor,
                          statusInfo.color
                        )}>
                          <StatusIcon className="h-3 w-3" />
                          {statusInfo.label}
                        </span>
                      </td>
                      
                      <td className="p-4">
                        <div className="text-white text-sm">
                          {execution.duration ? formatDuration(execution.duration) : '-'}
                        </div>
                      </td>
                      
                      <td className="p-4">
                        <div className="flex items-center gap-1 text-gray-400 text-sm">
                          <Clock className="h-3 w-3" />
                          {execution.startedAt ? 
                            new Date(execution.startedAt).toLocaleString('it-IT') : 
                            'N/A'
                          }
                        </div>
                      </td>
                      
                      <td className="p-4">
                        <div className="flex items-center gap-1">
                          <button className="p-1 text-gray-400 hover:text-blue-400 transition-colors">
                            <Eye className="h-4 w-4" />
                          </button>
                          <button className="p-1 text-gray-400 hover:text-green-400 transition-colors">
                            <RotateCcw className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}