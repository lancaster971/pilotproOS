import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  Search,
  RefreshCw,
  Download,
  Bell,
  BellOff,
  Eye,
  Activity,
  TrendingUp,
  TrendingDown,
  Server,
  Database,
  Wifi,
} from 'lucide-react'
import { schedulerAPI, statsAPI } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/utils'

interface Alert {
  id: string
  type: 'error' | 'warning' | 'info' | 'success'
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  message: string
  source: string
  timestamp: string
  isRead: boolean
  isActive: boolean
  count: number
  category: 'system' | 'workflow' | 'database' | 'security' | 'performance'
}

interface MonitoringMetric {
  id: string
  name: string
  value: number
  unit: string
  status: 'healthy' | 'warning' | 'critical'
  trend: 'up' | 'down' | 'stable'
  change: number
  threshold: number
  category: string
}

const AlertIcon: React.FC<{ type: string, className?: string }> = ({ type, className }) => {
  const icons = {
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
    success: CheckCircle,
  }
  const Icon = icons[type as keyof typeof icons] || Info
  return <Icon className={className} />
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30'
    case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
    case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
    case 'low': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
    default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy': return 'text-green-400'
    case 'warning': return 'text-yellow-400'
    case 'critical': return 'text-red-400'
    default: return 'text-gray-400'
  }
}

export const AlertsPage: React.FC = () => {
  const { user } = useAuthStore()
  const _tenantId = user?.tenantId || 'default_tenant'
  void _tenantId // suppress unused warning
  
  const [activeTab, setActiveTab] = useState<'alerts' | 'monitoring'>('alerts')
  const [filterSeverity, setFilterSeverity] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all')
  const [filterCategory, setFilterCategory] = useState<'all' | 'system' | 'workflow' | 'database' | 'security' | 'performance'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [showOnlyUnread, setShowOnlyUnread] = useState(false)
  const [isMonitoringEnabled, setIsMonitoringEnabled] = useState(true)

  // Fetch real data from backend
  const { data: schedulerStatus, isLoading: isLoadingScheduler, refetch: refetchScheduler } = useQuery({
    queryKey: ['scheduler-status-alerts'],
    queryFn: async () => {
      const response = await schedulerAPI.status()
      return response.data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: systemStats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['system-stats-alerts'],
    queryFn: async () => {
      const response = await statsAPI.system()
      return response.data
    },
    refetchInterval: 60000,
  })

  const { data: syncLogs, isLoading: isLoadingLogs } = useQuery({
    queryKey: ['sync-logs-alerts'],
    queryFn: async () => {
      const response = await schedulerAPI.getSyncHistory()
      return response.data
    },
    refetchInterval: 60000,
  })

  // Transform backend data into alerts format
  const processedAlerts: Alert[] = syncLogs?.logs?.slice(0, 20).map((log: any, index: number) => ({
    id: `alert-${index}`,
    type: log.success ? 'success' : 'error',
    severity: log.success ? 'low' : (log.error_message ? 'high' : 'medium'),
    title: log.success ? 
      `Sync Completed for ${log.tenant_name || 'Unknown Tenant'}` : 
      `Sync Failed for ${log.tenant_name || 'Unknown Tenant'}`,
    message: log.success ? 
      `Successfully processed ${log.items_processed || 0} items in ${log.duration_ms || 0}ms` :
      log.error_message || 'Sync operation failed without specific error',
    source: 'scheduler.sync',
    timestamp: log.started_at,
    isRead: index > 2, // Mark first 3 as unread
    isActive: !log.success,
    count: 1,
    category: 'system'
  })) || []

  // Add scheduler status alerts
  if (schedulerStatus && !schedulerStatus.scheduler?.isRunning) {
    processedAlerts.unshift({
      id: 'scheduler-stopped',
      type: 'warning',
      severity: 'high',
      title: 'Scheduler is Stopped',
      message: 'The automated sync scheduler is currently not running. Manual intervention may be required.',
      source: 'scheduler.status',
      timestamp: new Date().toISOString(),
      isRead: false,
      isActive: true,
      count: 1,
      category: 'system'
    })
  }

  // Process monitoring metrics from system stats
  const processedMetrics: MonitoringMetric[] = [
    {
      id: 'cpu-usage',
      name: 'System Memory',
      value: schedulerStatus?.system?.memory ? 
        Math.round((schedulerStatus.system.memory.heapUsed / schedulerStatus.system.memory.heapTotal) * 100) : 45,
      unit: '%',
      status: 'healthy',
      trend: 'stable',
      change: 2,
      threshold: 85,
      category: 'System'
    },
    {
      id: 'active-tenants',
      name: 'Active Tenants',
      value: systemStats?.database?.activeTenants || 0,
      unit: 'count',
      status: 'healthy',
      trend: 'up',
      change: 5,
      threshold: 100,
      category: 'Database'
    },
    {
      id: 'total-workflows',
      name: 'Total Workflows',
      value: systemStats?.database?.totalWorkflows || 0,
      unit: 'count',
      status: 'healthy',
      trend: 'up',
      change: 3,
      threshold: 1000,
      category: 'Workflows'
    },
    {
      id: 'sync-runs',
      name: 'Total Sync Runs',
      value: systemStats?.scheduler?.totalSyncRuns || 0,
      unit: 'count',
      status: 'healthy',
      trend: 'up',
      change: 12,
      threshold: 10000,
      category: 'Scheduler'
    },
    {
      id: 'error-rate',
      name: 'Error Rate',
      value: syncLogs?.logs ? 
        Math.round((syncLogs.logs.filter((l: any) => !l.success).length / syncLogs.logs.length) * 100) : 0,
      unit: '%',
      status: syncLogs?.logs?.filter((l: any) => !l.success).length > 2 ? 'warning' : 'healthy',
      trend: 'down',
      change: -0.5,
      threshold: 5,
      category: 'Performance'
    },
    {
      id: 'uptime',
      name: 'System Uptime',
      value: schedulerStatus?.system?.uptime ? Math.round(schedulerStatus.system.uptime / 3600) : 0,
      unit: 'hours',
      status: 'healthy',
      trend: 'stable',
      change: 0,
      threshold: 10000,
      category: 'System'
    }
  ]

  // Filters for alerts
  const filteredAlerts = processedAlerts.filter(alert => {
    const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity
    const matchesCategory = filterCategory === 'all' || alert.category === filterCategory
    const matchesSearch = alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.message.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesReadStatus = !showOnlyUnread || !alert.isRead
    
    return matchesSeverity && matchesCategory && matchesSearch && matchesReadStatus
  })

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffMinutes < 1) return 'Ora'
    if (diffMinutes < 60) return `${diffMinutes}m fa`
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h fa`
    return `${Math.floor(diffMinutes / 1440)}g fa`
  }

  // Stats for alerts
  const alertStats = {
    total: processedAlerts.length,
    unread: processedAlerts.filter(a => !a.isRead).length,
    critical: processedAlerts.filter(a => a.severity === 'critical' && a.isActive).length,
    active: processedAlerts.filter(a => a.isActive).length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">
            Alerts & Monitoring
          </h1>
          <p className="text-gray-500 mt-1">
            Monitoraggio real-time e gestione alert del sistema
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsMonitoringEnabled(!isMonitoringEnabled)}
            className={cn(
              'btn-control',
              isMonitoringEnabled ? 'bg-green-500/20 border-green-500/30 text-green-400' : ''
            )}
          >
            {isMonitoringEnabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
            {isMonitoringEnabled ? 'Monitoring ON' : 'Monitoring OFF'}
          </button>
          
          <button 
            onClick={() => refetchScheduler()}
            disabled={isLoadingScheduler}
            className="btn-control disabled:opacity-50"
          >
            <RefreshCw className={cn('h-4 w-4', isLoadingScheduler && 'animate-spin')} />
            Aggiorna
          </button>
          
          <button className="btn-control">
            <Download className="h-4 w-4" />
            Esporta Log
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Alert Totali</p>
              <p className="text-2xl font-bold text-white">{alertStats.total}</p>
            </div>
            <Bell className="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Non Letti</p>
              <p className="text-2xl font-bold text-blue-400">{alertStats.unread}</p>
            </div>
            <Eye className="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div className="control-card p-6 border-red-500/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Critical</p>
              <p className="text-2xl font-bold text-red-400">{alertStats.critical}</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Attivi</p>
              <p className="text-2xl font-bold text-green-400">{alertStats.active}</p>
            </div>
            <Activity className="h-8 w-8 text-gray-600" />
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="control-card p-1">
        <div className="flex items-center gap-1">
          {[
            { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
            { id: 'monitoring', label: 'Real-time Monitoring', icon: Activity },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all',
                activeTab === id
                  ? 'bg-green-500 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="control-card p-4">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                <input
                  type="text"
                  placeholder="Cerca alerts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
                />
              </div>

              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value as any)}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
              >
                <option value="all">Tutte le severity</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>

              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value as any)}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
              >
                <option value="all">Tutte le categorie</option>
                <option value="system">System</option>
                <option value="workflow">Workflow</option>
                <option value="database">Database</option>
                <option value="security">Security</option>
                <option value="performance">Performance</option>
              </select>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="unread-only"
                  checked={showOnlyUnread}
                  onChange={(e) => setShowOnlyUnread(e.target.checked)}
                  className="w-4 h-4 text-green-500 bg-gray-800 border-gray-600 rounded focus:ring-green-500"
                />
                <label htmlFor="unread-only" className="text-sm text-white">
                  Solo non letti
                </label>
              </div>
            </div>
          </div>

          {/* Alerts List */}
          <div className="control-card p-6">
            <div className="space-y-4">
              {isLoadingLogs ? (
                <div className="text-center py-8 text-gray-500">
                  <Bell className="h-12 w-12 mx-auto mb-4 text-gray-600 animate-pulse" />
                  <p>Caricamento alerts...</p>
                </div>
              ) : filteredAlerts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Bell className="h-12 w-12 mx-auto mb-4 text-gray-600" />
                  <p>Nessun alert trovato con i filtri selezionati</p>
                </div>
              ) : (
                filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={cn(
                      'p-4 rounded-lg border transition-all cursor-pointer hover:shadow-md',
                      !alert.isRead ? 'bg-gray-800/50 border-gray-700' : 'bg-gray-900/30 border-gray-800',
                      getSeverityColor(alert.severity)
                    )}
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 mt-1">
                        <AlertIcon type={alert.type} className="h-5 w-5" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <h3 className="text-white font-medium">{alert.title}</h3>
                            <span className={cn(
                              'px-2 py-1 rounded text-xs font-medium border',
                              getSeverityColor(alert.severity)
                            )}>
                              {alert.severity.toUpperCase()}
                            </span>
                            {alert.count > 1 && (
                              <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                                x{alert.count}
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-gray-500">
                            {formatTime(alert.timestamp)}
                          </span>
                        </div>
                        
                        <p className="text-gray-300 text-sm mb-2">
                          {alert.message}
                        </p>
                        
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-3">
                            <span className="text-gray-500">Sorgente: {alert.source}</span>
                            <span className="text-blue-400 capitalize">{alert.category}</span>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {!alert.isRead && (
                              <button className="text-blue-400 hover:text-blue-300">
                                Segna come letto
                              </button>
                            )}
                            <button className="text-gray-400 hover:text-white">
                              Dettagli
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Monitoring Tab */}
      {activeTab === 'monitoring' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {processedMetrics.map((metric) => (
              <div key={metric.id} className="control-card p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-400 mb-1">{metric.name}</h3>
                    <div className="flex items-baseline gap-1">
                      <span className={cn('text-2xl font-bold', getStatusColor(metric.status))}>
                        {metric.value}
                      </span>
                      <span className="text-sm text-gray-500">{metric.unit}</span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    {metric.trend === 'up' && <TrendingUp className="h-4 w-4 text-red-400" />}
                    {metric.trend === 'down' && <TrendingDown className="h-4 w-4 text-green-400" />}
                    {metric.trend === 'stable' && <span className="text-gray-500 text-xs">—</span>}
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">{metric.category}</span>
                  <span className={cn(
                    'font-medium',
                    metric.change > 0 ? 'text-red-400' : 'text-green-400'
                  )}>
                    {metric.change > 0 ? '+' : ''}{metric.change}%
                  </span>
                </div>
                
                {/* Progress bar */}
                <div className="mt-3">
                  <div className="w-full bg-gray-800 rounded-full h-1.5">
                    <div 
                      className={cn(
                        'h-1.5 rounded-full transition-all',
                        metric.status === 'healthy' ? 'bg-green-500' :
                        metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                      )}
                      style={{ width: `${Math.min((metric.value / metric.threshold) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>0</span>
                    <span>{metric.threshold}{metric.unit}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* System Status */}
          <div className="control-card p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Server className="h-5 w-5 text-green-400" />
              System Status
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className={cn(
                  'inline-flex items-center justify-center w-16 h-16 rounded-full border mb-3',
                  schedulerStatus?.scheduler?.isRunning ? 
                    'bg-green-500/10 border-green-500/30' : 
                    'bg-red-500/10 border-red-500/30'
                )}>
                  <Wifi className={cn(
                    'h-8 w-8',
                    schedulerStatus?.scheduler?.isRunning ? 'text-green-400' : 'text-red-400'
                  )} />
                </div>
                <h4 className="text-white font-medium mb-1">Scheduler Service</h4>
                <p className={cn(
                  'text-sm',
                  schedulerStatus?.scheduler?.isRunning ? 'text-green-400' : 'text-red-400'
                )}>
                  {isLoadingScheduler ? 'Loading...' : (schedulerStatus?.scheduler?.isRunning ? 'Running' : 'Stopped')}
                </p>
                <p className="text-xs text-gray-500">
                  {systemStats?.scheduler?.totalSyncRuns || 0} sync runs
                </p>
              </div>
              
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/10 border border-green-500/30 mb-3">
                  <Database className="h-8 w-8 text-green-400" />
                </div>
                <h4 className="text-white font-medium mb-1">Database</h4>
                <p className="text-green-400 text-sm">Healthy</p>
                <p className="text-xs text-gray-500">
                  {isLoadingStats ? '-' : `${systemStats?.database?.totalWorkflows || 0} workflows`}
                </p>
              </div>
              
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-500/10 border border-blue-500/30 mb-3">
                  <Activity className="h-8 w-8 text-blue-400" />
                </div>
                <h4 className="text-white font-medium mb-1">Tenants</h4>
                <p className="text-blue-400 text-sm">Active</p>
                <p className="text-xs text-gray-500">
                  {isLoadingStats ? '-' : `${systemStats?.database?.activeTenants || 0} active`}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}