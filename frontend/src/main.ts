import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Import clean CSS - Design System initialized in App.vue
import './style.css'
import './design-system/utilities.css'

// PrimeVue imports - CLEAN configuration
import PrimeVue from 'primevue/config'
import Nora from '@primevue/themes/nora'

// Chart.js configuration for PrimeVue
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale
)

// Import pages
import LoginPage from './pages/LoginPage.vue'
import DashboardPage from './pages/DashboardPage.vue'
import WorkflowsPage from './pages/WorkflowsPage.vue'
import WorkflowVisualizationPage from './pages/WorkflowVisualizationPage.vue'
import ExecutionsPage from './pages/ExecutionsPage.vue'
import ExecutionsPagePrime from './pages/ExecutionsPagePrime.vue'
import SecurityPage from './pages/SecurityPage.vue'
import AgentsPage from './pages/AgentsPage.vue'
import SchedulerPage from './pages/SchedulerPage.vue'
import DesignSystemTestPage from './pages/DesignSystemTestPage.vue'

// Router configuration - same as n8n approach
const routes = [
  { path: '/login', component: LoginPage, name: 'login' },
  { path: '/', redirect: '/login' },
  { path: '/dashboard', component: DashboardPage, name: 'dashboard', meta: { requiresAuth: true } },
  { path: '/workflows', component: WorkflowsPage, name: 'workflows', meta: { requiresAuth: true } },
  { path: '/workflows/visual', component: WorkflowVisualizationPage, name: 'workflow-visualization', meta: { requiresAuth: true } },
  { path: '/executions', component: ExecutionsPagePrime, name: 'executions', meta: { requiresAuth: true } },
  { path: '/executions-old', component: ExecutionsPage, name: 'executions-old', meta: { requiresAuth: true } },
  { path: '/security', component: SecurityPage, name: 'security', meta: { requiresAuth: true } },
  { path: '/agents', component: AgentsPage, name: 'agents', meta: { requiresAuth: true } },
  { path: '/scheduler', component: SchedulerPage, name: 'scheduler', meta: { requiresAuth: true } },
  { path: '/design-test', component: DesignSystemTestPage, name: 'design-test' },
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

// CLEAN PrimeVue Configuration - No more inline CSS chaos!
app.use(PrimeVue, {
  theme: {
    preset: Nora,
    options: {
      prefix: 'p',
      darkModeSelector: 'system',
      cssLayer: {
        name: 'primevue',
        order: 'design-system, primevue, tailwind'
      }
    }
  },
  ripple: true
  // NO MORE PT STYLES! Design system handles everything
})

app.use(pinia)
app.use(router)

// Import and register missing PrimeVue components
import Timeline from 'primevue/timeline'
import Splitter from 'primevue/splitter'
import SplitterPanel from 'primevue/splitterpanel'
import Rating from 'primevue/rating'
import Skeleton from 'primevue/skeleton'

app.component('Timeline', Timeline)
app.component('Splitter', Splitter)
app.component('SplitterPanel', SplitterPanel)
app.component('Rating', Rating)
app.component('Skeleton', Skeleton)

// Initialize auth store
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.initializeAuth()

app.mount('#app')

console.log('🎨 PilotProOS Design System initialized!')
console.log('🚀 Vue 3 frontend ready - clean CSS architecture!')