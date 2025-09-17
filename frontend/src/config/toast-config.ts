import type { PluginOptions } from 'vue-toastification'
import { POSITION } from 'vue-toastification'

export const toastOptions: PluginOptions = {
  transition: 'Vue-Toastification__fade',
  maxToasts: 3,
  newestOnTop: true,
  position: POSITION.TOP_RIGHT,
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: false,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false
  // Temporarily removed custom classes to debug
  // toastClassName: 'insights-toast',
  // bodyClassName: 'insights-toast-body',
  // progressBarClassName: 'insights-toast-progress',
  // containerClassName: 'insights-toast-container'
}