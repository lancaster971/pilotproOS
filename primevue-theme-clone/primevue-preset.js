// PilotPro AI Command Center - PrimeVue Preset
// Dark Theme basato su VS Code Style

export default {
  semantic: {
    primary: {
      50: 'hsl(122, 39%, 95%)',   // Verde molto chiaro
      100: 'hsl(122, 39%, 90%)',  // Verde chiaro
      200: 'hsl(122, 39%, 80%)',  // Verde chiaro-medio
      300: 'hsl(122, 39%, 70%)',  // Verde medio-chiaro
      400: 'hsl(122, 39%, 60%)',  // Verde medio
      500: 'hsl(122, 39%, 49%)',  // #4CAF50 - Primary color
      600: 'hsl(122, 39%, 45%)',  // Verde medio-scuro
      700: 'hsl(122, 39%, 40%)',  // Verde scuro
      800: 'hsl(122, 39%, 30%)',  // Verde molto scuro
      900: 'hsl(122, 39%, 20%)',  // Verde scurissimo
      950: 'hsl(122, 39%, 10%)'   // Verde quasi nero
    },
    colorScheme: {
      light: {
        primary: {
          color: 'hsl(122, 39%, 49%)',
          contrastColor: 'hsl(0, 0%, 100%)',
          hoverColor: 'hsl(122, 39%, 55%)',
          activeColor: 'hsl(122, 39%, 45%)'
        },
        highlight: {
          background: 'hsl(122, 39%, 25%)',
          focusBackground: 'hsl(122, 39%, 30%)',
          color: 'hsl(0, 0%, 95%)',
          focusColor: 'hsl(0, 0%, 100%)'
        },
      },
      dark: {
        // Surface Colors
        surface: {
          0: 'hsl(220, 13%, 8%)',     // --background
          50: 'hsl(220, 13%, 10%)',   // --background-secondary  
          100: 'hsl(220, 13%, 12%)',  // --card
          200: 'hsl(220, 13%, 14%)',  // --card-hover
          300: 'hsl(220, 13%, 16%)',
          400: 'hsl(220, 13%, 18%)',  // --border-hover
          500: 'hsl(220, 13%, 20%)',
          600: 'hsl(220, 13%, 25%)',
          700: 'hsl(220, 13%, 30%)',
          800: 'hsl(220, 13%, 40%)',
          900: 'hsl(220, 13%, 50%)',
          950: 'hsl(220, 13%, 60%)'
        },
        
        // Primary Colors (Verde Material Design)
        primary: {
          color: 'hsl(122, 39%, 49%)',        // #4CAF50
          contrastColor: 'hsl(0, 0%, 95%)',   // --foreground
          hoverColor: 'hsl(122, 39%, 55%)',   // --primary-hover
          activeColor: 'hsl(122, 39%, 45%)'
        },

        // Content Colors
        content: {
          color: 'hsl(0, 0%, 95%)',           // --foreground
          hoverColor: 'hsl(0, 0%, 100%)',
          mutedColor: 'hsl(220, 9%, 46%)'     // --foreground-muted
        },

        // Border Colors  
        border: {
          color: 'hsl(220, 13%, 15%)',        // --border
          hoverColor: 'hsl(220, 13%, 18%)'    // --border-hover
        },

        // Navigation
        navigation: {
          item: {
            color: 'hsl(0, 0%, 95%)',         // --foreground
            hoverColor: 'hsl(0, 0%, 100%)',
            activeColor: 'hsl(122, 39%, 49%)', // --primary
            icon: {
              color: 'hsl(220, 9%, 46%)',     // --foreground-muted
              hoverColor: 'hsl(0, 0%, 95%)',
              activeColor: 'hsl(122, 39%, 49%)'
            }
          }
        },

        // Highlight Colors
        highlight: {
          background: 'hsl(122, 39%, 25%)',   // --selection
          focusBackground: 'hsl(122, 39%, 30%)',
          color: 'hsl(0, 0%, 95%)',
          focusColor: 'hsl(0, 0%, 100%)'
        },

        // Mask (Overlays)
        mask: {
          background: 'rgba(26, 26, 29, 0.8)', // --background with opacity
          color: 'hsl(0, 0%, 95%)'
        },

        // Focus Ring
        focusRing: {
          width: '2px',
          style: 'solid',
          color: 'hsl(122, 39%, 49%)',        // --focus
          offset: '2px'
        },

        // State Colors
        formField: {
          background: 'hsl(220, 13%, 12%)',   // --card
          disabledBackground: 'hsl(220, 13%, 8%)', // --background
          filledBackground: 'hsl(220, 13%, 14%)',  // --card-hover
          filledHoverBackground: 'hsl(220, 13%, 16%)',
          borderColor: 'hsl(220, 13%, 15%)',  // --border
          hoverBorderColor: 'hsl(220, 13%, 18%)', // --border-hover
          focusBorderColor: 'hsl(122, 39%, 49%)',  // --primary
          invalidBorderColor: 'hsl(0, 73%, 41%)',  // --error
          color: 'hsl(0, 0%, 95%)',           // --foreground
          disabledColor: 'hsl(220, 9%, 46%)', // --foreground-muted
          placeholderColor: 'hsl(220, 9%, 46%)', // --foreground-muted
          floatLabelColor: 'hsl(220, 9%, 46%)', // --foreground-muted
          floatLabelFocusColor: 'hsl(122, 39%, 49%)' // --primary
        }
      }
    }
  }
};