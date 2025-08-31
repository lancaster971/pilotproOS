import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  TrendingUp,
  GitBranch,
  Play,
  CheckCircle,
} from 'lucide-react'
import ApexCharts from 'react-apexcharts'
import { tenantAPI } from '../../services/api'
import { formatNumber, cn } from '../../lib/utils'
import { RecentActivity } from './RecentActivity'
import { SystemHealth } from './SystemHealth'
import { useAuthStore } from '../../store/authStore'

interface StatCard {
  title: string
  value: string | number
  change: number
  icon: React.ElementType
  color: string
}

export const Dashboard: React.FC = () => {
  const { user } = useAuthStore()
  const tenantId = user?.tenantId || 'default_tenant'
  
  
  // USA DATI DEL TUO TENANT, NON AGGREGATI!
  const { data: dashboardData, isLoading: statsLoading } = useQuery({
    queryKey: ['tenant-dashboard', tenantId],
    queryFn: async () => {
      const response = await tenantAPI.dashboard(tenantId)
      return response.data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })
  
  // Dati tenant-specific per stats dettagliate
  const { data: tenantStats } = useQuery({
    queryKey: ['tenant-stats', tenantId],
    queryFn: async () => {
      const response = await tenantAPI.stats(tenantId)
      return response.data
    },
    refetchInterval: 60000,
  })
  
  const stats = dashboardData?.stats
  const isLoading = statsLoading
  
  // Success rate già calcolato dal backend per IL TUO TENANT
  const successRate = stats?.executions?.successRate || 100
  
  const statCards: StatCard[] = [
    {
      title: 'I Tuoi Workflows',
      value: formatNumber(stats?.workflows?.total || 0),
      change: stats?.workflows?.active || 0,
      icon: GitBranch,
      color: 'from-green-400 to-green-500',  // Verde Control Room
    },
    {
      title: 'Workflows Attivi',
      value: stats?.workflows?.active || 0,
      change: 0,
      icon: Play,
      color: 'from-green-500 to-green-600',  // Verde Control Room
    },
    {
      title: 'Esecuzioni (24h)',
      value: formatNumber(stats?.executions?.last24h || 0),
      change: successRate,
      icon: CheckCircle,
      color: 'from-gray-600 to-gray-700',  // Grigio Control Room
    },
    {
      title: 'Success Rate',
      value: `${successRate}%`,
      change: 0,
      icon: TrendingUp,
      color: successRate >= 90 ? 'from-green-400 to-green-500' : 
              successRate >= 70 ? 'from-yellow-400 to-yellow-500' :
              'from-red-400 to-red-500',
    },
  ]
  
  // Chart configuration
  const chartOptions = {
    chart: {
      type: 'area' as const,
      toolbar: { show: false },
      background: 'transparent',
    },
    stroke: {
      curve: 'smooth' as const,
      width: 2,
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.4,
        opacityTo: 0.1,
      },
    },
    colors: ['#0ea5e9', '#d946ef'],
    xaxis: {
      categories: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
      labels: {
        style: {
          colors: '#94a3b8',
        },
      },
    },
    yaxis: {
      labels: {
        style: {
          colors: '#94a3b8',
        },
      },
    },
    grid: {
      borderColor: '#334155',
      strokeDashArray: 4,
    },
    tooltip: {
      theme: 'dark',
    },
  }
  
  // Usa dati reali dal TUO tenant
  const chartSeries = tenantStats?.activity?.hourly ? [
    {
      name: 'Workflows Attivi',
      data: tenantStats.activity.hourly.map((h: any) => h.unique_workflows) || [0, 0, 0, 0, 0, 0, 0],
    },
    {
      name: 'Esecuzioni',
      data: tenantStats.activity.hourly.map((h: any) => h.executions) || [0, 0, 0, 0, 0, 0, 0],
    },
  ] : [
    {
      name: 'Workflows',
      data: [0, 0, 0, 0, 0, 0, 0],
    },
    {
      name: 'Executions',
      data: [0, 0, 0, 0, 0, 0, 0],
    },
  ]
  
  const donutOptions = {
    chart: {
      type: 'donut' as const,
      background: 'transparent',
    },
    labels: ['Success', 'Error', 'Running', 'Waiting'],
    colors: ['#10b981', '#ef4444', '#3b82f6', '#f59e0b'],
    stroke: {
      show: false,
    },
    dataLabels: {
      enabled: false,
    },
    legend: {
      position: 'bottom' as const,
      labels: {
        colors: '#94a3b8',
      },
    },
    tooltip: {
      theme: 'dark',
    },
  }
  
  // Usa dati reali dal TUO tenant per status distribution
  const donutSeries = stats?.statusDistribution 
    ? [
        stats.statusDistribution.success || 0,
        stats.statusDistribution.error || 0,
        stats.statusDistribution.running || 0,
        stats.statusDistribution.waiting || 0,
      ]
    : [0, 0, 0, 0]
  
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="glass-card rounded-xl p-6 h-32 skeleton" />
          ))}
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">Dashboard - {dashboardData?.tenant?.name || tenantId}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            I tuoi dati personali, non aggregati con altri tenant!
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="status-dot status-success" />
          <span className="text-sm">Live</span>
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => (
          <div
            key={stat.title}
            className="control-card p-6 hover:shadow-2xl transition-all duration-300 border-gray-800 hover:border-green-500/30"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-center justify-between mb-4">
              <div
                className={cn(
                  'h-12 w-12 rounded-lg bg-gradient-to-br flex items-center justify-center',
                  stat.color
                )}
              >
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="flex items-center gap-1">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span className="text-xs text-green-500">+{stat.change}%</span>
              </div>
            </div>
            <div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {stat.title}
              </p>
            </div>
          </div>
        ))}
      </div>
      
      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Chart */}
        <div className="lg:col-span-2 control-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Activity Overview</h2>
            <select className="text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1">
              <option>Last 24 Hours</option>
              <option>Last 7 Days</option>
              <option>Last 30 Days</option>
            </select>
          </div>
          <ApexCharts
            options={chartOptions}
            series={chartSeries}
            type="area"
            height={300}
          />
        </div>
        
        {/* Status Distribution */}
        <div className="control-card p-6">
          <h2 className="text-lg font-semibold mb-6">Execution Status</h2>
          <ApexCharts
            options={donutOptions}
            series={donutSeries}
            type="donut"
            height={300}
          />
        </div>
      </div>
      
      {/* Recent Activity & System Health con DATI REALI */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentActivity />
        <SystemHealth />
      </div>
    </div>
  )
}