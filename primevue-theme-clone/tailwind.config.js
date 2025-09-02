// PilotPro AI Command Center - Tailwind Configuration
// Configurazione colori personalizzata compatibile con PrimeVue

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Colori Base
        background: {
          DEFAULT: 'hsl(220, 13%, 8%)',      // #1a1a1d
          secondary: 'hsl(220, 13%, 10%)',   // #1f1f23
        },
        foreground: {
          DEFAULT: 'hsl(0, 0%, 95%)',        // #f2f2f2
          muted: 'hsl(220, 9%, 46%)',        // #6f7071
        },
        
        // Card e Contenitori
        card: {
          DEFAULT: 'hsl(220, 13%, 12%)',     // #25252a
          hover: 'hsl(220, 13%, 14%)',       // #2a2a30
        },
        
        // Bordi
        border: {
          DEFAULT: 'hsl(220, 13%, 15%)',     // #2f2f35
          hover: 'hsl(220, 13%, 18%)',       // #353540
        },
        
        // Primary (Verde Material Design)
        primary: {
          50: 'hsl(122, 39%, 95%)',
          100: 'hsl(122, 39%, 90%)',
          200: 'hsl(122, 39%, 80%)',
          300: 'hsl(122, 39%, 70%)',
          400: 'hsl(122, 39%, 60%)',
          500: 'hsl(122, 39%, 49%)',         // #4CAF50 - Colore principale
          600: 'hsl(122, 39%, 45%)',
          700: 'hsl(122, 39%, 40%)',
          800: 'hsl(122, 39%, 30%)',
          900: 'hsl(122, 39%, 20%)',
          950: 'hsl(122, 39%, 10%)',
          DEFAULT: 'hsl(122, 39%, 49%)',     // #4CAF50
          hover: 'hsl(122, 39%, 55%)',       // #66BB6A
        },
        
        // Colori Syntax Highlighting
        syntax: {
          comment: 'hsl(101, 29%, 47%)',     // #6a9955
          keyword: 'hsl(122, 39%, 49%)',     // #4CAF50
          string: 'hsl(17, 47%, 64%)',       // #ce9178
          number: 'hsl(54, 76%, 68%)',       // #b5cea8
          variable: 'hsl(122, 39%, 65%)',    // #81C784
          type: 'hsl(60, 87%, 73%)',         // #4ec9b0
        },
        
        // Colori di Stato
        success: {
          DEFAULT: 'hsl(123, 38%, 57%)',     // #89d185
          50: 'hsl(123, 38%, 95%)',
          100: 'hsl(123, 38%, 90%)',
          500: 'hsl(123, 38%, 57%)',
          600: 'hsl(123, 38%, 47%)',
          700: 'hsl(123, 38%, 37%)',
          900: 'hsl(123, 38%, 20%)',
        },
        info: {
          DEFAULT: 'hsl(122, 39%, 49%)',     // #4CAF50
          50: 'hsl(122, 39%, 95%)',
          100: 'hsl(122, 39%, 90%)',
          500: 'hsl(122, 39%, 49%)',
          600: 'hsl(122, 39%, 39%)',
          700: 'hsl(122, 39%, 29%)',
          900: 'hsl(122, 39%, 15%)',
        },
        warning: {
          DEFAULT: 'hsl(32, 93%, 66%)',      // #ffcc02
          50: 'hsl(32, 93%, 95%)',
          100: 'hsl(32, 93%, 90%)',
          500: 'hsl(32, 93%, 66%)',
          600: 'hsl(32, 93%, 56%)',
          700: 'hsl(32, 93%, 46%)',
          900: 'hsl(32, 93%, 26%)',
        },
        error: {
          DEFAULT: 'hsl(0, 73%, 41%)',       // #f44747
          50: 'hsl(0, 73%, 95%)',
          100: 'hsl(0, 73%, 90%)',
          500: 'hsl(0, 73%, 41%)',
          600: 'hsl(0, 73%, 35%)',
          700: 'hsl(0, 73%, 29%)',
          900: 'hsl(0, 73%, 15%)',
        },
        danger: {
          DEFAULT: 'hsl(0, 73%, 41%)',       // #f44747 - Alias per error
          50: 'hsl(0, 73%, 95%)',
          100: 'hsl(0, 73%, 90%)',
          500: 'hsl(0, 73%, 41%)',
          600: 'hsl(0, 73%, 35%)',
          700: 'hsl(0, 73%, 29%)',
          900: 'hsl(0, 73%, 15%)',
        },
        
        // Colori Interattivi
        selection: 'hsl(122, 39%, 25%)',     // #2E7D32
        focus: 'hsl(122, 39%, 49%)',         // #4CAF50
        
        // Surface Colors (compatibili con PrimeVue)
        surface: {
          0: 'hsl(220, 13%, 8%)',           // background
          50: 'hsl(220, 13%, 10%)',         // background-secondary
          100: 'hsl(220, 13%, 12%)',        // card
          200: 'hsl(220, 13%, 14%)',        // card-hover
          300: 'hsl(220, 13%, 16%)',
          400: 'hsl(220, 13%, 18%)',        // border-hover
          500: 'hsl(220, 13%, 20%)',
          600: 'hsl(220, 13%, 25%)',
          700: 'hsl(220, 13%, 30%)',
          800: 'hsl(220, 13%, 40%)',
          900: 'hsl(220, 13%, 50%)',
          950: 'hsl(220, 13%, 60%)',
        }
      },
      
      // Typography personalizzata (dimensioni aumentate di 2px)
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],      // 12px → 14px
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],  // 14px → 16px
        'base': ['1rem', { lineHeight: '1.5rem' }],     // 16px → 18px
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],  // 18px → 20px
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],   // 20px → 22px
        '2xl': ['1.5rem', { lineHeight: '2rem' }],      // 24px → 26px
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px → 32px
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],   // 36px → 38px
        '5xl': ['3rem', { lineHeight: '1' }],           // 48px → 50px
        '6xl': ['3.75rem', { lineHeight: '1' }],        // 60px → 62px
      },
      
      // Spacing e Border Radius
      borderRadius: {
        'lg': '0.5rem',
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      
      // Box Shadow personalizzate
      boxShadow: {
        'soft': '0 2px 8px 0 rgba(26, 26, 29, 0.1)',
        'medium': '0 4px 16px 0 rgba(26, 26, 29, 0.15)',
        'strong': '0 8px 32px 0 rgba(26, 26, 29, 0.25)',
      }
    },
  },
  plugins: [],
};