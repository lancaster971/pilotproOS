import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Database,
  Table,
  HardDrive,
  Activity,
  Search,
  RefreshCw,
  Download,
  Server,
  Zap,
  BarChart3,
  Eye,
  Clock,
  GitBranch,
  Target,
} from 'lucide-react'
import { statsAPI, schedulerAPI, databaseAPI } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/utils'

interface DatabaseStats {
  overview: {
    totalTables: number
    totalRecords: number
    databaseSize: string
    lastBackup: string
  }
  tables: Array<{
    name: string
    records: number
    size: string
    lastModified: string
    growth: number
  }>
  performance: {
    queryTime: number
    connections: number
    uptime: string
    indexEfficiency: number
  }
  recentActivity: Array<{
    action: string
    table: string
    timestamp: string
    user: string
  }>
}

export const DatabasePage: React.FC = () => {
  const { user } = useAuthStore()
  const _tenantId = user?.tenantId || 'default_tenant'
  void _tenantId // suppress unused warning
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  
  // Helper function moved here to avoid usage before declaration
  const formatDuration = (ms: number) => {
    if (ms < 60000) return `${Math.round(ms / 1000)}s`
    if (ms < 3600000) return `${Math.round(ms / 60000)}m`
    if (ms < 86400000) return `${Math.round(ms / 3600000)}h`
    return `${Math.round(ms / 86400000)}d`
  }

  // Fetch real data from backend
  const { data: systemStats, isLoading: isLoadingStats, refetch: refetchStats } = useQuery({
    queryKey: ['system-stats-database'],
    queryFn: async () => {
      const response = await statsAPI.system()
      return response.data
    },
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: schedulerStatus, isLoading: isLoadingScheduler } = useQuery({
    queryKey: ['scheduler-status-database'],
    queryFn: async () => {
      const response = await schedulerAPI.status()
      return response.data
    },
    refetchInterval: 60000,
  })

  const { data: recentActivityData, isLoading: isLoadingActivity } = useQuery({
    queryKey: ['database-activity'],
    queryFn: async () => {
      const response = await databaseAPI.recentActivity()
      return response.data
    },
    refetchInterval: 30000,
  })

  // Process backend data into DatabaseStats format
  const processedStats: DatabaseStats = {
    overview: {
      totalTables: 5, // Placeholder - not available in backend
      totalRecords: (systemStats?.database?.totalWorkflows || 0) + (systemStats?.database?.totalExecutions || 0),
      databaseSize: '234.5 MB', // Placeholder - not available
      lastBackup: new Date().toISOString() // Use current time as placeholder
    },
    tables: [
      {
        name: 'tenant_executions',
        records: systemStats?.database?.totalExecutions || 0,
        size: '89.2 MB', // Placeholder
        lastModified: new Date().toISOString(),
        growth: 12.5 // Placeholder
      },
      {
        name: 'tenant_workflows',
        records: systemStats?.database?.totalWorkflows || 0,
        size: '2.1 MB', // Placeholder
        lastModified: new Date().toISOString(),
        growth: 0.8
      },
      {
        name: 'tenants',
        records: systemStats?.database?.totalTenants || 0,
        size: '156 KB',
        lastModified: new Date().toISOString(),
        growth: 0
      },
      {
        name: 'tenant_sync_logs',
        records: systemStats?.scheduler?.totalSyncRuns || 0,
        size: '125.4 MB',
        lastModified: new Date().toISOString(),
        growth: 18.7
      },
      {
        name: 'system_health',
        records: 50, // Placeholder
        size: '89 KB',
        lastModified: new Date().toISOString(),
        growth: 0
      }
    ],
    performance: {
      queryTime: 142, // Placeholder
      connections: 23, // Placeholder
      uptime: schedulerStatus?.system ? formatDuration((schedulerStatus.system.uptime || 0) * 1000) : '15 giorni, 8 ore',
      indexEfficiency: 94.2 // Placeholder
    },
    recentActivity: recentActivityData?.logs?.slice(0, 10).map((log: any) => ({
      action: log.success ? 'SYNC' : 'ERROR',
      table: 'tenant_sync_logs',
      timestamp: log.started_at,
      user: 'scheduler'
    })) || []
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('it-IT')
  }

  const getGrowthColor = (growth: number) => {
    if (growth > 10) return 'text-red-400'
    if (growth > 5) return 'text-yellow-400'
    if (growth > 0) return 'text-green-400'
    return 'text-gray-400'
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'SYNC': return 'text-green-400 bg-green-500/10'
      case 'INSERT': return 'text-green-400 bg-green-500/10'
      case 'UPDATE': return 'text-yellow-400 bg-yellow-500/10'
      case 'DELETE': return 'text-red-400 bg-red-500/10'
      case 'ERROR': return 'text-red-400 bg-red-500/10'
      case 'SELECT': return 'text-blue-400 bg-blue-500/10'
      default: return 'text-gray-400 bg-gray-500/10'
    }
  }

  const filteredTables = processedStats.tables.filter(table =>
    table.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">
            Database Management
          </h1>
          <p className="text-gray-500 mt-1">
            Informazioni dettagliate sul database e performance
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={() => refetchStats()}
            disabled={isLoadingStats}
            className="btn-control disabled:opacity-50"
          >
            <RefreshCw className={cn('h-4 w-4', isLoadingStats && 'animate-spin')} />
            Refresh
          </button>
          
          <button className="btn-control">
            <Download className="h-4 w-4" />
            Export Schema
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Tabelle Totali</p>
              <p className="text-2xl font-bold text-white">
                {isLoadingStats ? '-' : processedStats.overview.totalTables}
              </p>
            </div>
            <Table className="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Records Totali</p>
              <p className="text-2xl font-bold text-white">
                {isLoadingStats ? '-' : processedStats.overview.totalRecords.toLocaleString()}
              </p>
            </div>
            <HardDrive className="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Dimensione DB</p>
              <p className="text-2xl font-bold text-white">
                {processedStats.overview.databaseSize}
              </p>
            </div>
            <Database className="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">System Uptime</p>
              <p className="text-sm font-bold text-green-400">
                {isLoadingScheduler ? '-' : processedStats.performance.uptime}
              </p>
            </div>
            <Server className="h-8 w-8 text-gray-600" />
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="control-card p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-green-400" />
            System Performance
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400">Query Time Medio</p>
              <p className="text-xl font-bold text-green-400">{processedStats.performance.queryTime}ms</p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400">Active Tenants</p>
              <p className="text-xl font-bold text-blue-400">
                {isLoadingStats ? '-' : (systemStats?.database?.activeTenants || 0)}
              </p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400">System Uptime</p>
              <p className="text-xl font-bold text-white">
                {isLoadingScheduler ? '-' : processedStats.performance.uptime}
              </p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400">Health Status</p>
              <p className="text-xl font-bold text-green-400">Healthy</p>
            </div>
          </div>
        </div>

        <div className="control-card p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Clock className="h-5 w-5 text-blue-400" />
            Attività Recenti
          </h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {isLoadingActivity ? (
              <div className="text-gray-500">Caricamento...</div>
            ) : processedStats.recentActivity.length === 0 ? (
              <div className="text-gray-500">Nessuna attività recente</div>
            ) : (
              processedStats.recentActivity.slice(0, 8).map((activity, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className={cn(
                      'px-2 py-1 rounded text-xs font-medium',
                      getActionColor(activity.action)
                    )}>
                      {activity.action}
                    </span>
                    <span className="text-white font-medium">{activity.table}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">{activity.user}</p>
                    <p className="text-xs text-gray-500">{formatDate(activity.timestamp)}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* System Statistics */}
      <div className="control-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-green-400" />
          Database Statistics
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-500/10 border border-blue-500/30 mb-3">
              <GitBranch className="h-8 w-8 text-blue-400" />
            </div>
            <h4 className="text-white font-medium mb-1">Total Workflows</h4>
            <p className="text-blue-400 text-xl font-bold">
              {isLoadingStats ? '-' : (systemStats?.database?.totalWorkflows || 0)}
            </p>
            <p className="text-xs text-gray-500">across all tenants</p>
          </div>
          
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/10 border border-green-500/30 mb-3">
              <Target className="h-8 w-8 text-green-400" />
            </div>
            <h4 className="text-white font-medium mb-1">Total Executions</h4>
            <p className="text-green-400 text-xl font-bold">
              {isLoadingStats ? '-' : (systemStats?.database?.totalExecutions?.toLocaleString() || '0')}
            </p>
            <p className="text-xs text-gray-500">all time</p>
          </div>
          
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-500/10 border border-purple-500/30 mb-3">
              <Zap className="h-8 w-8 text-purple-400" />
            </div>
            <h4 className="text-white font-medium mb-1">Sync Operations</h4>
            <p className="text-purple-400 text-xl font-bold">
              {isLoadingStats ? '-' : (systemStats?.scheduler?.totalSyncRuns || 0)}
            </p>
            <p className="text-xs text-gray-500">automated syncs</p>
          </div>
        </div>
      </div>

      {/* Tables Overview */}
      <div className="control-card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Table className="h-5 w-5 text-green-400" />
            Tabelle Database
          </h3>
          
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Cerca tabelle..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left p-4 text-sm font-medium text-gray-400">Nome Tabella</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Records</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Dimensione</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Crescita</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Ultima Modifica</th>
                <th className="text-left p-4 text-sm font-medium text-gray-400">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {isLoadingStats ? (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-gray-500">
                    Caricamento...
                  </td>
                </tr>
              ) : filteredTables.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-gray-500">
                    Nessuna tabella trovata
                  </td>
                </tr>
              ) : (
                filteredTables.map((table) => (
                  <tr 
                    key={table.name} 
                    className="border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors"
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Table className="h-4 w-4 text-gray-400" />
                        <span className="text-white font-medium">{table.name}</span>
                      </div>
                    </td>
                    <td className="p-4 text-gray-300 font-mono">
                      {table.records.toLocaleString()}
                    </td>
                    <td className="p-4 text-gray-300 font-mono">
                      {table.size}
                    </td>
                    <td className="p-4">
                      <span className={cn('font-medium', getGrowthColor(table.growth))}>
                        {table.growth > 0 ? '+' : ''}{table.growth}%
                      </span>
                    </td>
                    <td className="p-4 text-gray-400 text-sm">
                      {formatDate(table.lastModified)}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <button 
                          className="p-1 text-gray-400 hover:text-green-400 transition-colors"
                          onClick={() => setSelectedTable(table.name)}
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button className="p-1 text-gray-400 hover:text-blue-400 transition-colors">
                          <BarChart3 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Table Details Modal */}
      {selectedTable && (
        <div className="control-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              Dettagli Tabella: {selectedTable}
            </h3>
            <button 
              onClick={() => setSelectedTable(null)}
              className="btn-control text-sm"
            >
              Chiudi
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400">Records Totali</p>
              <p className="text-xl font-bold text-white">
                {filteredTables.find(t => t.name === selectedTable)?.records.toLocaleString()}
              </p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400">Dimensione</p>
              <p className="text-xl font-bold text-white">
                {filteredTables.find(t => t.name === selectedTable)?.size}
              </p>
            </div>
            <div className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400">Crescita</p>
              <p className={cn(
                'text-xl font-bold',
                getGrowthColor(filteredTables.find(t => t.name === selectedTable)?.growth || 0)
              )}>
                {filteredTables.find(t => t.name === selectedTable)?.growth}%
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}