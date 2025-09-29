import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Import clean CSS - Design System initialized in App.vue
import './style.css'
import './design-system/utilities.css'
import './design-system/premium-no-animations.css'
import './design-system/enterprise-theme.css' // Enterprise rebrand - NO GREEN!
import './disable-animations.css'
import './styles/insights-theme.css' // Global Insights theme applied to all pages
import './styles/toast-theme.css' // Toast glassmorphism theme

// Vue Toastification - Battle-tested toast system
import Toast, { POSITION } from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import { toastOptions } from './config/toast-config'

// Vue Advanced Chat
import { register as registerAdvancedChat } from 'vue-advanced-chat'

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
const SettingsPage = () => import('./pages/SettingsPage.vue')
const DesignSystemTestPage = () => import('./pages/DesignSystemTestPage.vue')
const MilhenaChat = () => import('./pages/MilhenaChat.vue')
const RAGManagerPage = () => import('./pages/RAGManagerPage.vue')

// Router configuration - same as n8n approach
const routes = [
  { path: '/login', component: LoginPage, name: 'login' },
  { path: '/', redirect: '/insights' },
  { path: '/insights', component: InsightsPage, name: 'insights', meta: { requiresAuth: true } },
  { path: '/dashboard', redirect: '/insights' }, // Redirect for backward compatibility
  // Removed unused workflow routes - redirect to command-center
  { path: '/workflows', redirect: '/command-center' },
  { path: '/workflows/visual', redirect: '/command-center' },
  { path: '/command-center', component: WorkflowCommandCenter, name: 'command-center', meta: { requiresAuth: true } },
  { path: '/executions', component: ExecutionsPage, name: 'executions', meta: { requiresAuth: true } },
  { path: '/milhena', component: MilhenaChat, name: 'milhena', meta: { requiresAuth: true } },
  { path: '/rag', component: RAGManagerPage, name: 'rag-manager', meta: { requiresAuth: true } },
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

// Auth guard - verifica cookie HttpOnly prima di decidere le route
router.beforeEach(async (to, from, next) => {
  const { useAuthStore } = await import('./stores/auth')
  const authStore = useAuthStore()

  await authStore.ensureInitialized()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'insights' })
    return
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
registerAdvancedChat() // Register Advanced Chat

// Vue Toastification configuration - Insights theme
app.use(Toast, toastOptions)

// Import and register missing PrimeVue components
import Timeline from 'primevue/timeline'
import Splitter from 'primevue/splitter'
import SplitterPanel from 'primevue/splitterpanel'
import Rating from 'primevue/rating'
import Skeleton from 'primevue/skeleton'
import Sidebar from 'primevue/sidebar'
import Textarea from 'primevue/textarea'
import ConfirmDialog from 'primevue/confirmdialog'

app.component('Timeline', Timeline)
app.component('Splitter', Splitter)
app.component('SplitterPanel', SplitterPanel)
app.component('Rating', Rating)
app.component('Skeleton', Skeleton)
app.component('Sidebar', Sidebar)
app.component('Textarea', Textarea)
app.component('ConfirmDialog', ConfirmDialog)

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
