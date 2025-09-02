// PilotProOS Design System - Minimal Tailwind Configuration
// Uses CSS Variables from Design System instead of build-time colors
import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Use CSS variables instead of hardcoded colors
      colors: {
        // Primary colors from Design System CSS variables
        primary: 'var(--color-primary)',
        'primary-hover': 'var(--color-primary-hover)',
        'primary-active': 'var(--color-primary-active)',
        
        // Background system
        background: 'var(--color-background)',
        'background-secondary': 'var(--color-background-secondary)',
        
        // Surface system
        surface: 'var(--color-surface)',
        'surface-hover': 'var(--color-surface-hover)',
        
        // Border system
        border: 'var(--color-border)',
        'border-hover': 'var(--color-border-hover)',
        'border-accent': 'var(--color-border-accent)',
        
        // Text system
        text: 'var(--color-text)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-muted': 'var(--color-text-muted)',
        'text-accent': 'var(--color-text-accent)',
        
        // Semantic colors
        success: 'var(--success)',
        error: 'var(--error)', 
        warning: 'var(--warning)',
        info: 'var(--info)'
      },
      
      // Typography from Design System
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      
      // Animations from Design System
      animation: {
        'fade-in': 'fadeIn 0.8s ease-out',
        'slide-up': 'slideUp 0.6s ease-out forwards',
        'scale-in': 'scaleIn 0.5s ease-out forwards',
        'float': 'float 6s ease-in-out infinite',
      },
      
      keyframes: {
        fadeIn: {
          'from': { opacity: '0', transform: 'translateY(20px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          'from': { opacity: '0', transform: 'translateY(30px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          'from': { opacity: '0', transform: 'scale(0.8)' },
          'to': { opacity: '1', transform: 'scale(1)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config