/**
 * Premium Theme - Glassmorphism & Glow Effects
 * Enhanced with premium visual effects
 */

import { colors as baseColors } from '../tokens/colors'
import { shadows as baseShadows } from '../tokens/effects'

export const premiumTheme = {
  name: 'Premium Glow',
  colors: {
    ...baseColors,
    primary: {
      ...baseColors.primary,
      glow: 'rgba(16, 185, 129, 0.4)',
      'glow-intense': 'rgba(16, 185, 129, 0.6)'
    },
    background: {
      ...baseColors.background,
      glass: 'rgba(26, 26, 26, 0.8)',
      'glass-intense': 'rgba(26, 26, 26, 0.95)'
    }
  },
  shadows: {
    ...baseShadows,
    DEFAULT: '0 4px 20px rgba(16, 185, 129, 0.1)',
    glow: '0 0 15px rgba(16, 185, 129, 0.3)',
    'glow-intense': '0 0 25px rgba(16, 185, 129, 0.5)',
    'success-glow': '0 0 15px rgba(16, 185, 129, 0.4)',
    'premium-card': `
      0 20px 40px rgba(0, 0, 0, 0.1),
      0 1px 0 rgba(255, 255, 255, 0.05) inset,
      0 0 15px rgba(16, 185, 129, 0.2)
    `
  }
} as const