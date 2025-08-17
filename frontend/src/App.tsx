import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { Toaster as UIToaster } from './components/ui/toaster'
import { Layout } from './components/layout/Layout'
import { Dashboard } from './components/dashboard/Dashboard'
import { BusinessProcessesPage } from './components/processes/BusinessProcessesPage'
import { ProcessRunsPage } from './components/process-runs/ProcessRunsPage'
import { AnalyticsPage } from './components/analytics/AnalyticsPage'
import { DatabasePage } from './components/database/DatabasePage'
import { SchedulerPage } from './components/scheduler/SchedulerPage'
import { AIAssistantPage } from './components/ai-assistant/AIAssistantPage'
import { SettingsPage } from './components/settings/SettingsPage'
import { LoginPage } from './components/auth/LoginPage'
import { useAuthStore } from './store/authStore'

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Auth guard component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}


// Placeholder components for routes
const TenantsPage = () => <div className="control-card p-6 text-white">Tenants Management (Coming Soon)</div>
const UsersPage = () => <div className="control-card p-6 text-white">Users Management (Coming Soon)</div>

function App() {
  useEffect(() => {
    // Set dark mode by default
    document.documentElement.classList.add('dark')
  }, [])
  
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="workflows" element={<WorkflowsPage />} />
            <Route path="executions" element={<ExecutionsPage />} />
            <Route path="tenants" element={<TenantsPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="scheduler" element={<SchedulerPage />} />
            <Route path="stats" element={<StatsPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="database" element={<DatabasePage />} />
            <Route path="security" element={<SecurityPage />} />
            <Route path="security/premium" element={<SecurityPremiumPage />} />
            <Route path="agents" element={<AgentsPageEnhanced />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'glass-card',
            duration: 4000,
          }}
        />
        <UIToaster />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
