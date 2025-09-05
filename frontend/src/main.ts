import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Import clean CSS - Design System initialized in App.vue
import './style.css'
import './design-system/utilities.css'
import './design-system/premium.css'

// Vue Toastification - Battle-tested toast system  
import Toast, { POSITION } from 'vue-toastification'
import 'vue-toastification/dist/index.css'

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
import InsightsPage from './pages/InsightsPage.vue'
// Removed unused workflow pages
import WorkflowCommandCenter from './pages/WorkflowCommandCenter.vue'
import ExecutionsPage from './pages/ExecutionsPage.vue'
import ExecutionsPagePrime from './pages/ExecutionsPagePrime.vue'
// Removed SecurityPage and SchedulerPage - functionality not needed for business system
import DesignSystemTestPage from './pages/DesignSystemTestPage.vue'

// Router configuration - same as n8n approach
const routes = [
  { path: '/login', component: LoginPage, name: 'login' },
  { path: '/', redirect: '/login' },
  { path: '/insights', component: InsightsPage, name: 'insights', meta: { requiresAuth: true } },
  { path: '/dashboard', redirect: '/insights' }, // Redirect for backward compatibility
  // Removed unused workflow routes - redirect to command-center
  { path: '/workflows', redirect: '/command-center' },
  { path: '/workflows/visual', redirect: '/command-center' },
  { path: '/command-center', component: WorkflowCommandCenter, name: 'command-center', meta: { requiresAuth: true } },
  { path: '/executions', component: ExecutionsPagePrime, name: 'executions', meta: { requiresAuth: true } },
  { path: '/executions-old', component: ExecutionsPage, name: 'executions-old', meta: { requiresAuth: true } },
  { path: '/agents', redirect: '/command-center' }, // Agents functionality integrated into command-center
  { path: '/security', redirect: '/command-center' }, // Security functionality not needed
  { path: '/scheduler', redirect: '/command-center' }, // Scheduler handled by n8n internally
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
    next({ name: 'insights' })
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

// Vue Toastification configuration - Battle-tested accessibility & mobile support
app.use(Toast, {
  position: POSITION.TOP_RIGHT,
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: "button",
  icon: true,
  rtl: false
})

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