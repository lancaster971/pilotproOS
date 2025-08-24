/**
 * PilotProOS Design System - Color Tokens
 * Single Source of Truth for all colors
 * Type-safe color management with TypeScript
 */

export const colors = {
  // Primary Emerald Scale (Bright Green Theme)
  primary: {
    50: '#ecfdf5',
    100: '#d1fae5', 
    200: '#a7f3d0',
    300: '#6ee7b7',
    400: '#34d399',
    500: '#10b981',  // Main primary color
    600: '#059669',
    700: '#047857',
    800: '#065f46',
    900: '#064e3b',
    950: '#022c22'
  },

  // Neutral Grays (Dark Theme Base)
  neutral: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
    950: '#0f0f12'
  },

  // Semantic Colors
  semantic: {
    success: '#10b981',
    error: '#ef4444', 
    warning: '#f59e0b',
    info: '#3b82f6'
  },

  // Background System
  background: {
    primary: '#111827',    // Main dark background
    secondary: '#1f2937',  // Secondary darker
    tertiary: '#374151'    // Lightest dark
  },

  // Surface System  
  surface: {
    primary: '#1f2937',
    secondary: '#374151', 
    tertiary: '#4b5563'
  },

  // Border System
  border: {
    primary: '#374151',
    secondary: '#4b5563',
    accent: '#10b981'
  },

  // Text System
  text: {
    primary: '#f9fafb',
    secondary: '#d1d5db',
    muted: '#9ca3af',
    accent: '#10b981'
  }
} as const

// Type definitions for type safety
export type ColorScale = keyof typeof colors.primary
export type SemanticColor = keyof typeof colors.semantic
export type ColorToken = keyof typeof colors

// Helper to get color value with type safety
export function getColor(
  category: ColorToken,
  shade?: ColorScale | keyof typeof colors.semantic
): string {
  if (category === 'primary' && shade && shade in colors.primary) {
    return colors.primary[shade as ColorScale]
  }
  
  if (category === 'semantic' && shade && shade in colors.semantic) {
    return colors.semantic[shade as SemanticColor]
  }
  
  // Fallback for other categories
  const colorGroup = colors[category] as any
  if (typeof colorGroup === 'object' && shade) {
    return colorGroup[shade] || colorGroup[500] || colorGroup.primary
  }
  
  return colorGroup || colors.primary[500]
}

// Export individual color systems for convenience
export const {
  primary,
  neutral, 
  semantic,
  background,
  surface,
  border,
  text
} = colors