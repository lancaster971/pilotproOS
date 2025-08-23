import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

// PrimeVue imports
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'

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

// Configure PrimeVue with custom dark theme
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      prefix: 'p',
      darkModeSelector: 'system',
      cssLayer: false
    }
  },
  ripple: true,
  pt: {
    global: {
      css: `
        .p-component {
          font-family: inherit;
        }
        .p-inputtext {
          background: rgb(31 41 55) !important;
          border-color: rgb(55 65 81) !important;
          color: white !important;
        }
        .p-inputtext::placeholder {
          color: rgb(156 163 175);
        }
        .p-datatable {
          background: transparent !important;
        }
        .p-datatable .p-datatable-header {
          background: transparent !important;
          border: none !important;
          padding: 0 !important;
        }
        .p-datatable .p-datatable-thead > tr > th {
          background: rgb(31 41 55) !important;
          border-color: rgb(55 65 81) !important;
          color: rgb(156 163 175) !important;
        }
        .p-datatable .p-datatable-tbody > tr {
          background: transparent !important;
          color: white !important;
        }
        .p-datatable .p-datatable-tbody > tr:hover {
          background: rgb(31 41 55) !important;
        }
        .p-datatable .p-datatable-tbody > tr > td {
          border-color: rgb(55 65 81) !important;
        }
        .p-paginator {
          background: rgb(17 24 39) !important;
          border: none !important;
          color: rgb(156 163 175) !important;
        }
        .p-paginator .p-paginator-element:hover {
          background: rgb(31 41 55) !important;
        }
        .p-paginator .p-paginator-element.p-highlight {
          background: rgb(34 197 94) !important;
          color: white !important;
        }
        .p-tag {
          font-size: 0.75rem;
        }
        .p-tag.p-tag-success {
          background: rgb(34 197 94);
        }
        .p-tag.p-tag-danger {
          background: rgb(239 68 68);
        }
        .p-tag.p-tag-info {
          background: rgb(59 130 246);
        }
        .p-tag.p-tag-warn {
          background: rgb(251 191 36);
        }
        .p-button {
          font-size: 0.875rem;
        }
        .p-card {
          background: rgb(17 24 39) !important;
          border: 1px solid rgb(55 65 81) !important;
          color: white !important;
        }
        .p-select {
          background: rgb(31 41 55) !important;
          border-color: rgb(55 65 81) !important;
          color: white !important;
        }
        .p-select-option {
          background: rgb(31 41 55) !important;
          color: white !important;
        }
        .p-select-option:hover {
          background: rgb(55 65 81) !important;
        }
        .p-inputswitch.p-inputswitch-checked .p-inputswitch-slider {
          background: rgb(34 197 94) !important;
        }
      `
    }
  }
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

console.log('🚀 PilotProOS Vue 3 frontend initialized - same stack as n8n!')