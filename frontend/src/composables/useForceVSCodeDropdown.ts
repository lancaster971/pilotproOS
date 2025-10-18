/**
 * Force VS Code theme on PrimeVue Dropdowns via JavaScript
 * CSS alone cannot override PrimeVue Nora runtime styles
 * NUCLEAR OPTION: Continuous polling to override PrimeVue
 */

import { onMounted, onBeforeUnmount } from 'vue'

export function useForceVSCodeDropdown() {
  let interval: NodeJS.Timeout | null = null

  const forceStyles = () => {
    // Force all .p-select dropdowns (PrimeVue v4 uses .p-select not .p-dropdown!)
    const dropdowns = document.querySelectorAll('.p-select')
    dropdowns.forEach((dropdown: Element) => {
      const el = dropdown as HTMLElement
      el.style.background = '#2A2A2A'
      el.style.backgroundColor = '#2A2A2A'
      el.style.borderColor = '#3C3C3C'
      el.style.color = '#E0E0E0'
    })

    // Force dropdown panels (when open)
    const panels = document.querySelectorAll('.p-select-overlay, .p-overlay')
    panels.forEach((panel: Element) => {
      const el = panel as HTMLElement
      el.style.background = '#2A2A2A'
      el.style.backgroundColor = '#2A2A2A'
      el.style.borderColor = '#3C3C3C'
      el.style.color = '#E0E0E0'
    })

    // Force dropdown items
    const items = document.querySelectorAll('.p-select-option, .p-select-item')
    items.forEach((item: Element) => {
      const el = item as HTMLElement
      el.style.color = '#E0E0E0'
    })
  }

  onMounted(() => {
    // Force immediately
    forceStyles()

    // NUCLEAR OPTION: Force every 100ms to override PrimeVue runtime styles
    interval = setInterval(() => {
      forceStyles()
    }, 100)
  })

  onBeforeUnmount(() => {
    if (interval) {
      clearInterval(interval)
    }
  })

  return { forceStyles }
}
