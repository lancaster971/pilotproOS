/**
 * Emerald Theme - Bright Green Focus
 * Optimized for the current PilotProOS bright emerald design
 */

import { colors as baseColors } from '../tokens/colors'

export const emeraldTheme = {
  name: 'Emerald Bright',
  colors: {
    ...baseColors,
    primary: {
      50: '#ecfdf5',
      100: '#d1fae5', 
      200: '#a7f3d0',
      300: '#6ee7b7',
      400: '#34d399',
      500: '#00d26a',  // Brighter, more vibrant emerald
      600: '#10b981',  // Standard emerald
      700: '#047857',
      800: '#065f46', 
      900: '#064e3b',
      950: '#022c22'
    },
    semantic: {
      ...baseColors.semantic,
      success: '#00d26a',
      info: '#10b981'
    }
  }
} as const