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

// Lazy load pages for better performance - reduce bundle from 1.5MB to ~200KB initial
const LoginPage = () => import('./pages/LoginPage.vue')
const InsightsPage = () => import('./pages/InsightsPage.vue')
// Heavy page with VueFlow - lazy load critical!
const WorkflowCommandCenter = () => import('./pages/WorkflowCommandCenter.vue')
const ExecutionsPage = () => import('./pages/ExecutionsPage.vue')
const ExecutionsPagePrime = () => import('./pages/ExecutionsPagePrime.vue')
const SettingsPage = () => import('./pages/SettingsPage.vue')
const DesignSystemTestPage = () => import('./pages/DesignSystemTestPage.vue')

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
  { path: '/settings', component: SettingsPage, name: 'settings', meta: { requiresAuth: true, requiresRole: 'admin' } },
  { path: '/agents', redirect: '/command-center' }, // Agents functionality integrated into command-center
  { path: '/security', redirect: '/command-center' }, // Security functionality not needed
  { path: '/scheduler', redirect: '/command-center' }, // Scheduler handled by n8n internally
  { path: '/design-test', component: DesignSystemTestPage, name: 'design-test' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard with HttpOnly cookies support
router.beforeEach(async (to, from, next) => {
  // Import auth store inside guard to avoid circular imports
  const { useAuthStore } = await import('./stores/auth')
  const authStore = useAuthStore()
  
  // Initialize auth if not already done
  if (!authStore.user && authStore.token !== 'authenticated') {
    try {
      await authStore.initializeAuth()
    } catch (error) {
      console.log('Auth initialization failed:', error)
    }
  }
  
  const isAuthenticated = authStore.isAuthenticated
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' })
    return
  }
  
  if (to.name === 'login' && isAuthenticated) {
    next({ name: 'insights' }) // Redirect authenticated users away from login
    return
  }
  
  // Role-based access control using user object from store
  if (to.meta.requiresRole && isAuthenticated && authStore.user) {
    const userRole = authStore.user.role || 'viewer'
    
    if (to.meta.requiresRole === 'admin' && userRole !== 'admin') {
      next({ name: 'insights' }) // Redirect non-admin users away from admin pages
      return
    }
  }
  
  next()
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

// Setup user activity detection for auto-logout reset
let activityTimer: NodeJS.Timeout | null = null

const resetActivityTimer = () => {
  // Debounce activity detection
  if (activityTimer) clearTimeout(activityTimer)
  
  activityTimer = setTimeout(async () => {
    const { useAuthStore } = await import('./stores/auth')
    const authStore = useAuthStore()
    authStore.resetAutoLogoutTimer()
  }, 1000) // 1 second debounce
}

// Listen for user activity events
const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
activityEvents.forEach(event => {
  document.addEventListener(event, resetActivityTimer, { passive: true })
})

app.mount('#app')