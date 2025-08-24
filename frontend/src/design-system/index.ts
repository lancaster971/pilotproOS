/**
 * PilotProOS Design System - Main Entry Point
 * Runtime CSS Variables Generator & Theme Management
 */

import { colors, type ColorToken } from './tokens/colors'
import { typography } from './tokens/typography'
import { spacing, borderRadius } from './tokens/spacing'
import { shadows, blur, transitions, animations } from './tokens/effects'

// Theme definitions
export interface Theme {
  name: string
  colors: typeof colors
  typography: typeof typography
  spacing: typeof spacing
  shadows: typeof shadows
}

// Available themes
const themes = {
  default: {
    name: 'Default Dark',
    colors,
    typography,
    spacing,
    shadows
  },
  
  emerald: {
    name: 'Emerald Bright',
    colors: {
      ...colors,
      primary: {
        ...colors.primary,
        500: '#00d26a', // Brighter emerald
        600: '#10b981'
      }
    },
    typography,
    spacing,
    shadows
  },
  
  premium: {
    name: 'Premium Glow',
    colors: {
      ...colors,
      primary: {
        ...colors.primary,
        500: '#10b981',
        glow: 'rgba(16, 185, 129, 0.4)'
      }
    },
    typography,
    spacing,
    shadows: {
      ...shadows,
      DEFAULT: '0 4px 20px rgba(16, 185, 129, 0.1)'
    }
  }
} as const

export type ThemeName = keyof typeof themes

/**
 * Inject CSS Variables into document root
 * This is the core function that makes everything work
 */
export function injectDesignTokens(themeName: ThemeName = 'default'): void {
  const theme = themes[themeName]
  const root = document.documentElement

  // Inject Color Variables - Complete primary scale
  Object.entries(theme.colors.primary).forEach(([key, value]) => {
    root.style.setProperty(`--primary-${key}`, value)
  })

  // Also inject direct primary scale for CSS compatibility
  Object.entries(colors.primary).forEach(([key, value]) => {
    root.style.setProperty(`--primary-${key}`, value)
  })

  Object.entries(theme.colors.neutral).forEach(([key, value]) => {
    root.style.setProperty(`--neutral-${key}`, value)
  })

  Object.entries(theme.colors.semantic).forEach(([key, value]) => {
    root.style.setProperty(`--${key}`, value)
  })

  Object.entries(theme.colors.background).forEach(([key, value]) => {
    root.style.setProperty(`--bg-${key}`, value)
  })

  Object.entries(theme.colors.surface).forEach(([key, value]) => {
    root.style.setProperty(`--surface-${key}`, value)
  })

  Object.entries(theme.colors.border).forEach(([key, value]) => {
    root.style.setProperty(`--border-${key}`, value)
  })

  Object.entries(theme.colors.text).forEach(([key, value]) => {
    root.style.setProperty(`--text-${key}`, value)
  })

  // Inject Typography Variables  
  Object.entries(theme.typography.fontSize).forEach(([key, value]) => {
    root.style.setProperty(`--text-${key}`, value)
  })

  Object.entries(theme.typography.fontWeight).forEach(([key, value]) => {
    root.style.setProperty(`--font-${key}`, value)
  })

  // Inject Spacing Variables
  Object.entries(theme.spacing).forEach(([key, value]) => {
    root.style.setProperty(`--space-${key}`, value)
  })

  Object.entries(borderRadius).forEach(([key, value]) => {
    root.style.setProperty(`--radius-${key}`, value)
  })

  // Inject Effect Variables
  Object.entries(theme.shadows).forEach(([key, value]) => {
    root.style.setProperty(`--shadow-${key}`, value)
  })

  Object.entries(blur).forEach(([key, value]) => {
    root.style.setProperty(`--blur-${key}`, value)
  })

  Object.entries(transitions).forEach(([key, value]) => {
    root.style.setProperty(`--transition-${key}`, value)
  })

  // Inject Animation Variables
  Object.entries(animations).forEach(([key, value]) => {
    root.style.setProperty(`--animation-${key}`, value)
  })

  // Set semantic color mappings (these are the ones we'll use in CSS)
  root.style.setProperty('--color-primary', theme.colors.primary[500])
  root.style.setProperty('--color-primary-hover', theme.colors.primary[600])
  root.style.setProperty('--color-primary-active', theme.colors.primary[700])
  
  root.style.setProperty('--color-background', theme.colors.background.primary)
  root.style.setProperty('--color-background-secondary', theme.colors.background.secondary)
  
  root.style.setProperty('--color-surface', theme.colors.surface.primary)
  root.style.setProperty('--color-surface-hover', theme.colors.surface.secondary)
  
  root.style.setProperty('--color-border', theme.colors.border.primary)
  root.style.setProperty('--color-border-hover', theme.colors.border.secondary)
  root.style.setProperty('--color-border-accent', theme.colors.border.accent)
  
  root.style.setProperty('--color-text', theme.colors.text.primary)
  root.style.setProperty('--color-text-secondary', theme.colors.text.secondary)
  root.style.setProperty('--color-text-muted', theme.colors.text.muted)
  root.style.setProperty('--color-text-accent', theme.colors.text.accent)

  // Set data attribute for theme switching
  root.setAttribute('data-theme', themeName)
  
  console.log(`🎨 Design System: ${theme.name} theme applied`)
}

/**
 * Switch theme at runtime - INSTANT switching without rebuild!
 */
export function switchTheme(themeName: ThemeName): void {
  injectDesignTokens(themeName)
  
  // Save preference to localStorage
  localStorage.setItem('pilotpros-theme', themeName)
  
  // Dispatch theme change event for components that need to react
  window.dispatchEvent(new CustomEvent('theme-changed', { 
    detail: { theme: themeName } 
  }))
}

/**
 * Initialize design system with saved theme or default
 */
export function initializeDesignSystem(): void {
  const savedTheme = localStorage.getItem('pilotpros-theme') as ThemeName || 'default'
  injectDesignTokens(savedTheme)
}

/**
 * Get current active theme
 */
export function getCurrentTheme(): ThemeName {
  return document.documentElement.getAttribute('data-theme') as ThemeName || 'default'
}

/**
 * Helper function to get CSS variable value
 */
export function getCSSVariable(variable: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(`--${variable}`).trim()
}

// Export all tokens for direct use
export * from './tokens/colors'
export * from './tokens/typography'  
export * from './tokens/spacing'
export * from './tokens/effects'

// Export themes object
export { themes }