/**
 * PilotProOS Design System - Effects Tokens  
 * Shadows, blur effects, transitions, and animations
 */

export const shadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  
  // Custom PilotProOS shadows
  glow: '0 0 15px rgb(16 185 129 / 0.3)',
  'glow-sm': '0 0 10px rgb(16 185 129 / 0.2)',
  'glow-lg': '0 0 25px rgb(16 185 129 / 0.4)',
  'success-glow': '0 0 15px rgb(16 185 129 / 0.4)',
  'error-glow': '0 0 15px rgb(239 68 68 / 0.4)',
  'warning-glow': '0 0 15px rgb(245 158 11 / 0.4)',
  'info-glow': '0 0 15px rgb(59 130 246 / 0.4)'
} as const

export const blur = {
  none: '0',
  sm: '4px',
  DEFAULT: '8px', 
  md: '12px',
  lg: '16px',
  xl: '24px',
  '2xl': '40px',
  '3xl': '64px'
} as const

export const transitions = {
  none: 'none',
  all: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  DEFAULT: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  colors: 'color 150ms cubic-bezier(0.4, 0, 0.2, 1), background-color 150ms cubic-bezier(0.4, 0, 0.2, 1), border-color 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  opacity: 'opacity 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  shadow: 'box-shadow 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  transform: 'transform 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  
  // Custom durations
  fast: 'all 100ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)'
} as const

export const animations = {
  // Fade animations
  'fade-in': 'fadeIn 0.8s ease-out',
  'fade-out': 'fadeOut 0.3s ease-in',
  
  // Slide animations  
  'slide-up': 'slideUp 0.6s ease-out forwards',
  'slide-down': 'slideDown 0.6s ease-out forwards',
  'slide-in-left': 'slideInLeft 0.5s ease-out forwards',
  'slide-in-right': 'slideInRight 0.5s ease-out forwards',
  
  // Scale animations
  'scale-in': 'scaleIn 0.5s ease-out forwards',
  'scale-out': 'scaleOut 0.3s ease-in forwards',
  
  // Bounce and float
  'bounce': 'bounce 1s infinite',
  'float': 'float 6s ease-in-out infinite',
  
  // Pulse and glow effects
  'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  'glow-pulse': 'glowPulse 2s ease-in-out infinite',
  
  // Loading states
  'spin': 'spin 1s linear infinite',
  'ping': 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
  'skeleton': 'skeleton 1.5s ease-in-out infinite'
} as const

export const keyframes = {
  fadeIn: {
    'from': { opacity: '0', transform: 'translateY(20px)' },
    'to': { opacity: '1', transform: 'translateY(0)' }
  },
  fadeOut: {
    'from': { opacity: '1' },
    'to': { opacity: '0' }
  },
  slideUp: {
    'from': { opacity: '0', transform: 'translateY(30px)' },
    'to': { opacity: '1', transform: 'translateY(0)' }
  },
  slideDown: {
    'from': { opacity: '0', transform: 'translateY(-30px)' },
    'to': { opacity: '1', transform: 'translateY(0)' }
  },
  slideInLeft: {
    'from': { opacity: '0', transform: 'translateX(-20px)' },
    'to': { opacity: '1', transform: 'translateX(0)' }
  },
  slideInRight: {
    'from': { opacity: '0', transform: 'translateX(20px)' },
    'to': { opacity: '1', transform: 'translateX(0)' }
  },
  scaleIn: {
    'from': { opacity: '0', transform: 'scale(0.8)' },
    'to': { opacity: '1', transform: 'scale(1)' }
  },
  scaleOut: {
    'from': { opacity: '1', transform: 'scale(1)' },
    'to': { opacity: '0', transform: 'scale(0.8)' }
  },
  float: {
    '0%, 100%': { transform: 'translateY(0px)' },
    '50%': { transform: 'translateY(-20px)' }
  },
  glowPulse: {
    '0%, 100%': { 
      opacity: '1', 
      boxShadow: '0 0 10px rgb(16 185 129 / 0.3)'
    },
    '50%': { 
      opacity: '0.7', 
      boxShadow: '0 0 20px rgb(16 185 129 / 0.6)'
    }
  },
  skeleton: {
    '0%': { backgroundPosition: '-200px 0' },
    '100%': { backgroundPosition: 'calc(200px + 100%) 0' }
  }
} as const

export type Shadow = keyof typeof shadows
export type Blur = keyof typeof blur
export type Transition = keyof typeof transitions
export type Animation = keyof typeof animations