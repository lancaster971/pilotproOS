import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  GitBranch,
  Play,
  Users,
  Building2,
  BarChart3,
  AlertCircle,
  Settings,
  Database,
  Clock,
  Shield,
  Bot,
  X,
} from 'lucide-react'
import { cn } from '../../lib/utils'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const navItems = [
  {
    title: 'Main',
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
      { icon: GitBranch, label: 'Workflows', path: '/workflows' },
      { icon: Play, label: 'Executions', path: '/executions' },
    ],
  },
  {
    title: 'Management',
    items: [
      { icon: Building2, label: 'Tenants', path: '/tenants' },
      { icon: Users, label: 'Users', path: '/users' },
      { icon: Clock, label: 'Scheduler', path: '/scheduler' },
    ],
  },
  {
    title: 'Monitoring',
    items: [
      { icon: BarChart3, label: 'Statistics', path: '/stats' },
      { icon: AlertCircle, label: 'Alerts', path: '/alerts' },
      { icon: Database, label: 'Database', path: '/database' },
      { icon: Bot, label: 'AI Agents', path: '/agents' },
    ],
  },
  {
    title: 'System',
    items: [
      { icon: Shield, label: 'Security', path: '/security' },
      { icon: Shield, label: 'Compliance & Audit', path: '/security/premium' },
      { icon: Settings, label: 'Settings', path: '/settings' },
    ],
  },
]

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300',
          'bg-black border-r border-gray-900',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Mobile header */}
          <div className="flex items-center justify-between p-4 lg:hidden">
            <h2 className="text-lg font-semibold">Menu</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          
          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4">
            {navItems.map((section) => (
              <div key={section.title} className="mb-6">
                <h3 className="mb-2 px-3 text-xs font-semibold uppercase text-gray-600">
                  {section.title}
                </h3>
                <div className="space-y-1">
                  {section.items.map((item) => (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={({ isActive }) =>
                        cn(
                          'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all',
                          'hover:bg-gray-900 hover:text-green-400',
                          isActive
                            ? 'bg-green-500/10 text-green-400 border-l-2 border-green-500'
                            : 'text-gray-400 border-l-2 border-transparent'
                        )
                      }
                    >
                      <item.icon className="h-4 w-4" />
                      <span className="flex-1">{item.label}</span>
                      {(item as any).premium && (
                        <span className="text-xs px-1.5 py-0.5 bg-green-400/20 text-green-400 rounded-full font-medium">
                          PREMIUM
                        </span>
                      )}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>
          
          {/* Footer */}
          <div className="border-t border-gray-900 p-4">
            <div className="bg-gray-900/50 rounded-md p-3 border border-gray-800">
              <div className="flex items-center gap-2 mb-2">
                <div className="status-dot status-success" />
                <span className="text-xs font-medium text-green-400">Live Execution</span>
              </div>
              <div className="text-xs text-gray-500">
                <div>Uptime: 99.9%</div>
                <div>Version: 1.0.0</div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}