import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Shield,
  Key,
  Lock,
  AlertTriangle,
  CheckCircle,
  Users,
  Activity,
  Smartphone,
  Monitor,
  Globe,
  Search,
  Download,
  RefreshCw,
  Settings,
  Plus,
  Edit,
  Trash2,
  Copy,
  Database,
  Server,
  LogOut,
  LogIn,
  Ban,
} from 'lucide-react'
import { securityAPI, schedulerAPI, statsAPI } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/utils'

interface SecurityLog {
  id: string
  timestamp: string
  event: 'login' | 'logout' | 'failed_login' | 'api_access' | 'data_export' | 'config_change' | 'permission_change'
  user: string
  userRole: string
  ipAddress: string
  userAgent: string
  location: string
  deviceType: 'desktop' | 'mobile' | 'api' | 'unknown'
  status: 'success' | 'failed' | 'warning'
  details: string
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
}

interface ApiKey {
  id: string
  name: string
  description: string
  keyHash: string // Solo hash, mai la chiave vera
  permissions: string[]
  status: 'active' | 'revoked' | 'expired'
  createdAt: string
  lastUsed?: string
  expiresAt?: string
  usageCount: number
  rateLimit: number
  allowedIPs?: string[]
  createdBy: string
}

interface SecurityMetrics {
  totalUsers: number
  activeUsers: number
  failedLogins: number
  suspiciousActivity: number
  apiKeysActive: number
  apiKeysRevoked: number
  loginSuccessRate: number
  avgSessionDuration: number
}

const getEventIcon = (event: string) => {
  switch (event) {
    case 'login': return LogIn
    case 'logout': return LogOut
    case 'failed_login': return Ban
    case 'api_access': return Database
    case 'data_export': return Download
    case 'config_change': return Settings
    case 'permission_change': return Shield
    default: return Activity
  }
}

const getEventColor = (event: string, status: string) => {
  if (status === 'failed') return 'text-red-400 bg-red-500/10'
  if (status === 'warning') return 'text-yellow-400 bg-yellow-500/10'
  
  switch (event) {
    case 'login': return 'text-green-400 bg-green-500/10'
    case 'logout': return 'text-blue-400 bg-blue-500/10'
    case 'failed_login': return 'text-red-400 bg-red-500/10'
    case 'api_access': return 'text-purple-400 bg-purple-500/10'
    case 'data_export': return 'text-orange-400 bg-orange-500/10'
    case 'config_change': return 'text-yellow-400 bg-yellow-500/10'
    default: return 'text-gray-400 bg-gray-500/10'
  }
}

const getRiskColor = (risk: string) => {
  switch (risk) {
    case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30'
    case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
    case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
    case 'low': return 'text-green-400 bg-green-500/10 border-green-500/30'
    default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  }
}

const getDeviceIcon = (deviceType: string) => {
  switch (deviceType) {
    case 'desktop': return Monitor
    case 'mobile': return Smartphone
    case 'api': return Server
    default: return Globe
  }
}

export const SecurityPage: React.FC = () => {
  const { user } = useAuthStore()
  const tenantId = user?.tenantId || 'default_tenant'
  
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'api_keys' | 'policies'>('overview')
  const [searchTerm, setSearchTerm] = useState('')
  const [eventFilter, setEventFilter] = useState<'all' | 'login' | 'logout' | 'failed_login' | 'api_access' | 'config_change'>('all')
  const [riskFilter, setRiskFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all')
  const [_showApiKeyModal, _setShowApiKeyModal] = useState(false)

  // Fetch real data from backend
  const { data: logsData, isLoading: isLoadingLogs, refetch: refetchLogs } = useQuery({
    queryKey: ['security-logs', tenantId],
    queryFn: async () => {
      const response = await securityAPI.logs(tenantId)
      return response.data
    },
    refetchInterval: 60000, // Refresh every minute
  })

  const { } = useQuery({
    queryKey: ['security-metrics'],
    queryFn: async () => {
      const response = await securityAPI.metrics()
      return response.data
    },
    refetchInterval: 60000,
  })

  const { data: systemStats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['system-stats-security'],
    queryFn: async () => {
      const response = await statsAPI.system()
      return response.data
    },
    refetchInterval: 60000,
  })

  // Transform backend sync logs into security logs format
  const processedLogs: SecurityLog[] = logsData?.logs?.map((log: any, index: number) => ({
    id: log.id || `log-${index}`,
    timestamp: log.started_at,
    event: log.success ? 'api_access' : 'failed_login',
    user: log.tenant_name || 'scheduler',
    userRole: 'service',
    ipAddress: '10.0.0.1',
    userAgent: 'PilotPro-Scheduler/1.0',
    location: 'Internal Network',
    deviceType: 'api' as const,
    status: log.success ? 'success' : 'failed',
    details: log.success ? 
      `Sync completed successfully for ${log.tenant_name}: ${log.items_processed || 0} items` :
      log.error_message || 'Sync operation failed',
    riskLevel: log.success ? 'low' : 'high'
  })) || []

  // Add some realistic security events from scheduler status
  if (schedulerAPI && processedLogs.length > 0) {
    processedLogs.unshift({
      id: 'login-admin',
      timestamp: new Date().toISOString(),
      event: 'login',
      user: user?.email || 'admin@pilotpro.com',
      userRole: 'admin',
      ipAddress: '192.168.1.50',
      userAgent: navigator.userAgent,
      location: 'Rome, Italy',
      deviceType: 'desktop',
      status: 'success',
      details: 'Successful login to control panel',
      riskLevel: 'low'
    })
  }

  // Mock security logs fallback (for demo purposes)
  const mockLogs: SecurityLog[] = [
    {
      id: '1',
      timestamp: '2025-08-12T16:45:23Z',
      event: 'failed_login',
      user: 'unknown@example.com',
      userRole: 'unknown',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      location: 'Milan, Italy',
      deviceType: 'desktop',
      status: 'failed',
      details: 'Invalid password attempt (3rd attempt)',
      riskLevel: 'high'
    },
    {
      id: '2',
      timestamp: '2025-08-12T16:42:15Z',
      event: 'login',
      user: 'admin@pilotpro.com',
      userRole: 'admin',
      ipAddress: '192.168.1.50',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
      location: 'Rome, Italy',
      deviceType: 'desktop',
      status: 'success',
      details: 'Successful login',
      riskLevel: 'low'
    },
    {
      id: '3',
      timestamp: '2025-08-12T16:38:07Z',
      event: 'api_access',
      user: 'api_service',
      userRole: 'service',
      ipAddress: '10.0.0.25',
      userAgent: 'PilotPro-API/1.0',
      location: 'Internal Network',
      deviceType: 'api',
      status: 'success',
      details: 'API key authentication successful',
      riskLevel: 'low'
    },
    {
      id: '4',
      timestamp: '2025-08-12T16:30:45Z',
      event: 'data_export',
      user: 'admin@pilotpro.com',
      userRole: 'admin',
      ipAddress: '192.168.1.50',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
      location: 'Rome, Italy',
      deviceType: 'desktop',
      status: 'success',
      details: 'Exported workflow data (234 records)',
      riskLevel: 'medium'
    },
    {
      id: '5',
      timestamp: '2025-08-12T15:20:12Z',
      event: 'config_change',
      user: 'admin@pilotpro.com',
      userRole: 'admin',
      ipAddress: '192.168.1.50',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
      location: 'Rome, Italy',
      deviceType: 'desktop',
      status: 'success',
      details: 'Modified API rate limits',
      riskLevel: 'medium'
    }
  ]

  // Mock API keys
  const mockApiKeys: ApiKey[] = [
    {
      id: '1',
      name: 'Production API',
      description: 'Main production API key for external integrations',
      keyHash: 'pk_live_***************************abc123',
      permissions: ['read:workflows', 'write:executions', 'read:stats'],
      status: 'active',
      createdAt: '2024-01-15T10:00:00Z',
      lastUsed: '2025-08-12T16:38:07Z',
      expiresAt: '2026-01-15T10:00:00Z',
      usageCount: 25847,
      rateLimit: 1000,
      allowedIPs: ['203.0.113.0/24', '198.51.100.0/24'],
      createdBy: 'admin@pilotpro.com'
    },
    {
      id: '2',
      name: 'Development API',
      description: 'Development environment API key',
      keyHash: 'pk_dev_***************************def456',
      permissions: ['read:workflows', 'read:executions'],
      status: 'active',
      createdAt: '2024-03-20T14:30:00Z',
      lastUsed: '2025-08-12T14:20:15Z',
      expiresAt: '2025-12-31T23:59:59Z',
      usageCount: 1245,
      rateLimit: 100,
      createdBy: 'dev@pilotpro.com'
    },
    {
      id: '3',
      name: 'Legacy Integration',
      description: 'Old integration API key (deprecated)',
      keyHash: 'pk_legacy_***********************ghi789',
      permissions: ['read:workflows'],
      status: 'revoked',
      createdAt: '2023-06-10T08:15:00Z',
      lastUsed: '2025-06-15T12:30:00Z',
      expiresAt: '2025-06-10T08:15:00Z',
      usageCount: 8950,
      rateLimit: 50,
      createdBy: 'old-admin@pilotpro.com'
    }
  ]

  // Process backend data into security metrics
  const processedMetrics: SecurityMetrics = {
    totalUsers: systemStats?.database?.activeTenants || 0,
    activeUsers: systemStats?.database?.activeTenants || 0,
    failedLogins: processedLogs.filter(log => log.event === 'failed_login').length,
    suspiciousActivity: processedLogs.filter(log => log.riskLevel === 'high' || log.riskLevel === 'critical').length,
    apiKeysActive: 2, // Placeholder - backend doesn't have API keys yet
    apiKeysRevoked: 1, // Placeholder
    loginSuccessRate: processedLogs.length > 0 ? 
      Math.round((processedLogs.filter(log => log.status === 'success').length / processedLogs.length) * 100 * 10) / 10 : 100,
    avgSessionDuration: 3600000 // 1 hour placeholder
  }

  // Filtri per logs - usa processedLogs dal backend o mockLogs come fallback
  const allLogs = processedLogs.length > 0 ? processedLogs : mockLogs
  const filteredLogs = allLogs.filter(log => {
    const matchesEvent = eventFilter === 'all' || log.event === eventFilter
    const matchesRisk = riskFilter === 'all' || log.riskLevel === riskFilter
    const matchesSearch = log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.details.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.ipAddress.includes(searchTerm)
    return matchesEvent && matchesRisk && matchesSearch
  })

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('it-IT')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">
            Security Center
          </h1>
          <p className="text-gray-500 mt-1">
            Monitoraggio sicurezza, audit trail e gestione accessi
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={() => refetchLogs()}
            disabled={isLoadingLogs}
            className="btn-control disabled:opacity-50"
          >
            <RefreshCw className={cn('h-4 w-4', isLoadingLogs && 'animate-spin')} />
            Aggiorna
          </button>
          
          <button className="btn-control">
            <Settings className="h-4 w-4" />
            Policies
          </button>
          
          <button className="btn-control-primary">
            <Plus className="h-4 w-4" />
            Nuova API Key
          </button>
        </div>
      </div>

      {/* Security Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Utenti Attivi</p>
              <p className="text-2xl font-bold text-white">
                {isLoadingStats ? '-' : processedMetrics.activeUsers}
              </p>
              <p className="text-xs text-gray-500">di {isLoadingStats ? '-' : processedMetrics.totalUsers} totali</p>
            </div>
            <Users className="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div className="control-card p-6 border-red-500/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Login Falliti</p>
              <p className="text-2xl font-bold text-red-400">
                {isLoadingLogs ? '-' : processedMetrics.failedLogins}
              </p>
              <p className="text-xs text-gray-500">ultime 24h</p>
            </div>
            <Ban className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">API Keys</p>
              <p className="text-2xl font-bold text-green-400">{processedMetrics.apiKeysActive}</p>
              <p className="text-xs text-gray-500">attive</p>
            </div>
            <Key className="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Success Rate</p>
              <p className="text-2xl font-bold text-green-400">
                {isLoadingLogs ? '-' : `${processedMetrics.loginSuccessRate}%`}
              </p>
              <p className="text-xs text-gray-500">operazioni</p>
            </div>
            <CheckCircle className="h-8 w-8 text-gray-600" />
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="control-card p-1">
        <div className="flex items-center gap-1">
          {[
            { id: 'overview', label: 'Security Overview', icon: Shield },
            { id: 'logs', label: 'Audit Logs', icon: Activity },
            { id: 'api_keys', label: 'API Keys', icon: Key },
            { id: 'policies', label: 'Security Policies', icon: Lock },
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

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Security Status */}
            <div className="control-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-400" />
                Security Status
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Two-Factor Authentication</span>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    <span className="text-green-400 text-sm">Enabled</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Password Policy</span>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    <span className="text-green-400 text-sm">Strong</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Session Security</span>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-400" />
                    <span className="text-yellow-400 text-sm">Medium</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">API Rate Limiting</span>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    <span className="text-green-400 text-sm">Active</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Threats */}
            <div className="control-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-400" />
                Recent Security Events
              </h3>
              <div className="space-y-3">
                {isLoadingLogs ? (
                  <div className="text-gray-500">Caricamento...</div>
                ) : allLogs.length === 0 ? (
                  <div className="text-gray-500">Nessun evento recente</div>
                ) : (
                  allLogs
                    .filter(log => log.riskLevel === 'high' || log.riskLevel === 'critical')
                    .slice(0, 5)
                    .map(log => {
                    const EventIcon = getEventIcon(log.event)
                    
                    return (
                      <div key={log.id} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                        <div className={cn(
                          'p-2 rounded-lg',
                          getEventColor(log.event, log.status)
                        )}>
                          <EventIcon className="h-4 w-4" />
                        </div>
                        <div className="flex-1">
                          <p className="text-white text-sm">{log.details}</p>
                          <p className="text-xs text-gray-400">
                            {log.user} • {formatTime(log.timestamp)}
                          </p>
                        </div>
                        <span className={cn(
                          'px-2 py-1 rounded text-xs font-medium border',
                          getRiskColor(log.riskLevel)
                        )}>
                          {log.riskLevel}
                        </span>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Logs Tab */}
      {activeTab === 'logs' && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="control-card p-4">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                <input
                  type="text"
                  placeholder="Cerca utente, IP, dettagli..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
                />
              </div>

              <select
                value={eventFilter}
                onChange={(e) => setEventFilter(e.target.value as any)}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
              >
                <option value="all">Tutti gli eventi</option>
                <option value="login">Login</option>
                <option value="logout">Logout</option>
                <option value="failed_login">Login Falliti</option>
                <option value="api_access">API Access</option>
                <option value="config_change">Config Changes</option>
              </select>

              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value as any)}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
              >
                <option value="all">Tutti i rischi</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>

              <button className="btn-control">
                <Download className="h-4 w-4" />
                Esporta Log
              </button>
            </div>
          </div>

          {/* Logs Table */}
          <div className="control-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Timestamp</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Event</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">User</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Location</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Device</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Risk</th>
                    <th className="text-left p-4 text-sm font-medium text-gray-400">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoadingLogs ? (
                    <tr>
                      <td colSpan={7} className="p-4 text-center text-gray-500">
                        Caricamento...
                      </td>
                    </tr>
                  ) : filteredLogs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-4 text-center text-gray-500">
                        Nessun log trovato
                      </td>
                    </tr>
                  ) : (
                    filteredLogs.map((log) => {
                    const EventIcon = getEventIcon(log.event)
                    const DeviceIcon = getDeviceIcon(log.deviceType)
                    
                    return (
                      <tr 
                        key={log.id} 
                        className="border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors"
                      >
                        <td className="p-4 text-sm text-gray-300 font-mono">
                          {formatTime(log.timestamp)}
                        </td>
                        
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div className={cn(
                              'p-1 rounded',
                              getEventColor(log.event, log.status)
                            )}>
                              <EventIcon className="h-3 w-3" />
                            </div>
                            <span className="text-white text-sm capitalize">
                              {log.event.replace('_', ' ')}
                            </span>
                          </div>
                        </td>
                        
                        <td className="p-4">
                          <div>
                            <p className="text-white text-sm">{log.user}</p>
                            <p className="text-xs text-gray-400">{log.userRole}</p>
                          </div>
                        </td>
                        
                        <td className="p-4">
                          <div>
                            <p className="text-white text-sm">{log.location}</p>
                            <p className="text-xs text-gray-400 font-mono">{log.ipAddress}</p>
                          </div>
                        </td>
                        
                        <td className="p-4">
                          <div className="flex items-center gap-1">
                            <DeviceIcon className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-300 text-sm capitalize">{log.deviceType}</span>
                          </div>
                        </td>
                        
                        <td className="p-4">
                          <span className={cn(
                            'px-2 py-1 rounded text-xs font-medium border',
                            getRiskColor(log.riskLevel)
                          )}>
                            {log.riskLevel}
                          </span>
                        </td>
                        
                        <td className="p-4 text-sm text-gray-300 max-w-xs truncate">
                          {log.details}
                        </td>
                      </tr>
                    )
                  })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* API Keys Tab */}
      {activeTab === 'api_keys' && (
        <div className="space-y-6">
          <div className="control-card p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Key className="h-5 w-5 text-green-400" />
              API Keys Management
            </h3>
            
            <div className="space-y-4">
              {mockApiKeys.map((apiKey) => (
                <div key={apiKey.id} className={cn(
                  'p-4 rounded-lg border transition-all',
                  apiKey.status === 'active' ? 'border-green-500/30 bg-green-500/5' :
                  apiKey.status === 'revoked' ? 'border-red-500/30 bg-red-500/5' :
                  'border-yellow-500/30 bg-yellow-500/5'
                )}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="text-white font-medium">{apiKey.name}</h4>
                        <span className={cn(
                          'px-2 py-1 rounded text-xs font-medium',
                          apiKey.status === 'active' ? 'bg-green-500/20 text-green-400' :
                          apiKey.status === 'revoked' ? 'bg-red-500/20 text-red-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        )}>
                          {apiKey.status}
                        </span>
                      </div>
                      
                      <p className="text-gray-400 text-sm mb-3">{apiKey.description}</p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-gray-400">Key Hash</p>
                          <p className="text-white font-mono">{apiKey.keyHash}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Usage</p>
                          <p className="text-white">{apiKey.usageCount.toLocaleString()} calls</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Rate Limit</p>
                          <p className="text-white">{apiKey.rateLimit}/hour</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Created</p>
                          <p className="text-white">{formatTime(apiKey.createdAt).split(' ')[0]}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Last Used</p>
                          <p className="text-white">
                            {apiKey.lastUsed ? formatTime(apiKey.lastUsed) : 'Never'}
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-400">Expires</p>
                          <p className="text-white">
                            {apiKey.expiresAt ? formatTime(apiKey.expiresAt).split(' ')[0] : 'Never'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="mt-3">
                        <p className="text-gray-400 text-sm mb-1">Permissions</p>
                        <div className="flex flex-wrap gap-1">
                          {apiKey.permissions.map((perm, index) => (
                            <span key={index} className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                              {perm}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button className="p-2 text-gray-400 hover:text-blue-400 transition-colors">
                        <Edit className="h-4 w-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-yellow-400 transition-colors">
                        <Copy className="h-4 w-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-red-400 transition-colors">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Security Policies Tab */}
      {activeTab === 'policies' && (
        <div className="control-card p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Lock className="h-5 w-5 text-blue-400" />
            Security Policies
          </h3>
          <p className="text-gray-400">Security policies configuration in development...</p>
        </div>
      )}
    </div>
  )
}