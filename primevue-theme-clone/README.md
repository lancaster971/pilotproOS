# PilotPro AI Command Center - Theme Clone per PrimeVue

Questa cartella contiene tutti i file necessari per clonare l'aspetto grafico del progetto PilotPro AI Command Center in un nuovo progetto PrimeVue.

## 🎨 Dark Theme basato su VS Code Style

Il tema utilizza una palette scura ispirata a VS Code con verde Material Design come colore primario (#4CAF50).

## 📁 Contenuto della cartella

### 1. `css-variables.css`
Variabili CSS complete con mappatura per PrimeVue Design Tokens:
- Colori base (background, foreground, card, border)
- Syntax highlighting colors (VS Code style)
- Colori di stato (success, info, warning, error)
- Colori interattivi (primary, hover, focus, selection)
- Mappatura automatica per PrimeVue (`--p-*` variables)

### 2. `primevue-preset.js`
Preset completo per PrimeVue con configurazione semantic:
- Scala cromatica primary (50-950) in verde Material Design
- Configurazione dark theme completa
- Surface colors mappati
- Navigation, forms, e componenti UI configurati
- Focus ring e stati interattivi

### 3. `tailwind.config.js`
Configurazione Tailwind CSS con:
- Tutti i colori personalizzati organizzati
- Typography con dimensioni aumentate di 2px
- Surface colors per PrimeVue
- Box shadows e border radius custom
- Colori di syntax highlighting

## 🚀 Come utilizzare

### 1. Installazione dipendenze
```bash
npm install primevue@^3.x tailwindcss
```

### 2. Configurazione PrimeVue
```javascript
// main.js o main.ts
import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import preset from './primevue-preset.js'

const app = createApp(App)
app.use(PrimeVue, {
    theme: {
        preset: preset,
        options: {
            darkModeSelector: '.dark'
        }
    }
})
```

### 3. Import CSS
```css
/* styles/main.css */
@import './css-variables.css';
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 4. Configurazione Tailwind
Sostituisci il tuo `tailwind.config.js` con quello fornito.

## 🎯 Caratteristiche principali

### Colori Base
- **Background**: `hsl(220, 13%, 8%)` - #1a1a1d
- **Foreground**: `hsl(0, 0%, 95%)` - #f2f2f2
- **Primary**: `hsl(122, 39%, 49%)` - #4CAF50 (Verde Material Design)
- **Card**: `hsl(220, 13%, 12%)` - #25252a

### Typography
- Font sizes aumentate di 2px per migliore leggibilità
- Antialiasing ottimizzato
- Line heights bilanciati

### Componenti
- Form fields con stile dark
- Navigation con colori VS Code
- Buttons e stati interattivi
- Focus ring verde Material Design

## 🔧 Personalizzazione

Per modificare il colore primario, cambia i valori HSL in tutti e tre i file:
- `css-variables.css` → variabili `--primary*`
- `primevue-preset.js` → oggetto `primary` e colori correlati  
- `tailwind.config.js` → oggetto `primary` in colors

## 📋 Compatibilità

- ✅ PrimeVue 3.x
- ✅ Vue 3
- ✅ Tailwind CSS 3.x
- ✅ Vite/Nuxt
- ✅ Dark/Light mode

## 🎨 Syntax Highlighting Colors

Se hai un editor di codice nel tuo progetto:
- **Comments**: `hsl(101, 29%, 47%)` - #6a9955
- **Keywords**: `hsl(122, 39%, 49%)` - #4CAF50  
- **Strings**: `hsl(17, 47%, 64%)` - #ce9178
- **Numbers**: `hsl(54, 76%, 68%)` - #b5cea8
- **Variables**: `hsl(122, 39%, 65%)` - #81C784
- **Types**: `hsl(60, 87%, 73%)` - #4ec9b0

Utilizza le classi Tailwind corrispondenti:
```html
<span class="text-syntax-keyword">function</span>
<span class="text-syntax-string">"Hello World"</span>
<span class="text-syntax-comment">// commento</span>
```

---

Tutti i colori utilizzano il formato HSL per coerenza e facilità di personalizzazione. Il tema è ottimizzato per la leggibilità e l'usabilità in ambienti di sviluppo.