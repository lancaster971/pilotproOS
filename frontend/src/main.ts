import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

// Import pages
import LoginPage from './pages/LoginPage.vue'
import DashboardPage from './pages/DashboardPage.vue'
import WorkflowsPage from './pages/WorkflowsPage.vue'
import ExecutionsPage from './pages/ExecutionsPage.vue'
import StatsPage from './pages/StatsPage.vue'
import DatabasePage from './pages/DatabasePage.vue'
import SecurityPage from './pages/SecurityPage.vue'
import AgentsPage from './pages/AgentsPage.vue'
import AlertsPage from './pages/AlertsPage.vue'
import SchedulerPage from './pages/SchedulerPage.vue'

// Router configuration - same as n8n approach
const routes = [
  { path: '/login', component: LoginPage, name: 'login' },
  { path: '/', redirect: '/login' },
  { path: '/dashboard', component: DashboardPage, name: 'dashboard', meta: { requiresAuth: true } },
  { path: '/workflows', component: WorkflowsPage, name: 'workflows', meta: { requiresAuth: true } },
  { path: '/executions', component: ExecutionsPage, name: 'executions', meta: { requiresAuth: true } },
  { path: '/stats', component: StatsPage, name: 'stats', meta: { requiresAuth: true } },
  { path: '/database', component: DatabasePage, name: 'database', meta: { requiresAuth: true } },
  { path: '/security', component: SecurityPage, name: 'security', meta: { requiresAuth: true } },
  { path: '/agents', component: AgentsPage, name: 'agents', meta: { requiresAuth: true } },
  { path: '/alerts', component: AlertsPage, name: 'alerts', meta: { requiresAuth: true } },
  { path: '/scheduler', component: SchedulerPage, name: 'scheduler', meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard - same pattern as n8n
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('pilotpro_token')
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

// Create app with same structure as n8n
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Initialize auth store
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.initializeAuth()

app.mount('#app')

console.log('🚀 PilotProOS Vue 3 frontend initialized - same stack as n8n!')