# Login Page - Pacchetto Completo

Questa cartella contiene tutti i file necessari per implementare la pagina di login IDENTICA al progetto originale in qualsiasi altro progetto.

## 📁 Struttura Files

```
loginPage/
├── AuthPage.tsx                 # Componente principale della pagina di login
├── components/
│   ├── Header.tsx              # Header con navigazione completa
│   ├── BackToTopButton.tsx     # Bottone "torna su" flottante
│   └── ui/
│       ├── button.tsx          # Componente Button shadcn/ui
│       ├── input.tsx           # Componente Input shadcn/ui
│       ├── label.tsx           # Componente Label shadcn/ui
│       ├── card.tsx            # Componente Card shadcn/ui
│       └── toast.tsx           # Componente Toast shadcn/ui
├── hooks/
│   └── use-toast.ts            # Hook per gestione toast
├── lib/
│   └── utils.ts                # Utility per classi CSS (cn function)
└── README.md                   # Questo file
```

## 🚀 Installazione

### 1. Dipendenze richieste

Installa le seguenti dipendenze NPM nel tuo progetto:

```bash
npm install @radix-ui/react-slot @radix-ui/react-label @radix-ui/react-toast
npm install class-variance-authority clsx tailwind-merge
npm install lucide-react
npm install next react react-dom
```

### 2. DevDependencies (se necessarie)

```bash
npm install -D typescript @types/react @types/react-dom @types/node
```

### 3. Configurazione Tailwind CSS

Assicurati che il tuo `tailwind.config.js` includa:

```javascript
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Se hai personalizzazioni specifiche, aggiungile qui
    },
  },
  plugins: [],
}
```

### 4. CSS Globale necessario

Aggiungi queste regole CSS al tuo file globale (es. `globals.css`):

```css
/* Font Weight Globale - CRITICO per il design */
* {
  font-weight: 300 !important;
}

/* Animazione neon per i badge */
@keyframes neonGlow {
  0% {
    box-shadow: 0 0 15px rgba(34, 197, 94, 0.3), 0 0 30px rgba(34, 197, 94, 0.1);
  }
  100% {
    box-shadow: 0 0 40px rgba(34, 197, 94, 0.8), 0 0 80px rgba(34, 197, 94, 0.5), 0 0 120px rgba(34, 197, 94, 0.3);
  }
}

/* Importa il font DM Sans da Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&display=swap');

body {
  font-family: 'DM Sans', sans-serif;
}
```

## 🎯 Implementazione

### Opzione 1: Next.js App Router

1. Copia `AuthPage.tsx` nella tua directory `app/auth/page.tsx`
2. Adatta il path degli import se necessario:
   ```typescript
   // Da:
   import { Button } from './components/ui/button';
   // A:
   import { Button } from '@/components/ui/button';
   ```

### Opzione 2: Componente Standalone

1. Usa `AuthPage.tsx` come componente indipendente
2. Importalo dove serve:
   ```typescript
   import AuthPage from './path/to/AuthPage';
   
   function MyApp() {
     return <AuthPage />;
   }
   ```

## ⚙️ Personalizzazione

### Testi e Branding

Modifica le costanti all'inizio di `AuthPage.tsx`:

```typescript
const LOGIN_TITLE = "Il tuo titolo";
const LOGIN_DESCRIPTION = "La tua descrizione";
const BRAND_TITLE = "Il tuo brand";
const BRAND_DESCRIPTION = "La tua descrizione brand";
```

### Collegamenti

Aggiorna i link nel componente:
- `/prenota-demo` → il tuo endpoint di registrazione
- `/terms-of-service` → i tuoi termini di servizio
- `/privacy-policy` → la tua privacy policy

### Header Navigation

Modifica gli elementi di navigazione in `Header.tsx`:
- `aiProducts` → i tuoi prodotti AI
- `companyItems` → le tue pagine aziendali
- `resourcesItems` → le tue risorse

## 🎨 Stile e Design

### Palette Colori

Il design usa:
- **Sfondo principale**: `bg-black`
- **Gradiente sinistro**: `from-yellow-400/30 via-lime-400/25 to-green-400/30`
- **Accent verde**: `text-green-400`, `bg-green-600`
- **Cards scure**: `bg-gray-900` con bordi `border-gray-700`
- **Testi**: `text-white`, `text-gray-300`, `text-gray-400`

### Typography

- **Font**: DM Sans (Google Fonts)
- **Weight globale**: 300 (Light) - FORZATO via CSS
- **Weight testi secondari**: 200 (Extra Light)
- **Responsive**: Da `text-base` a `text-7xl`

## 🔧 Funzionalità

### Form di Login

- **Validazione**: Email e password richiesti
- **Toggle password**: Mostra/nascondi password
- **Stati**: Loading durante il submit
- **Switch**: Toggle tra login e registrazione

### Comportamento

- **Login**: Mostra toast "Funzionalità in arrivo"
- **Registrazione**: Reindirizza a `/prenota-demo`
- **Responsive**: Layout mobile-first
- **Animazioni**: Hover effects e transizioni smooth

### Toast System

Sistema di notifiche completo con:
- Auto-dismiss
- Animazioni slide-in/out
- Varianti (default, destructive)
- Gestione stato globale

## 📱 Responsive

Il design è completamente responsive:
- **Mobile**: Form full-width, gradiente nascosto
- **Tablet**: Layout bilanciato
- **Desktop**: Split 50/50 con gradiente laterale

## 🚨 Note Importanti

1. **Font Weight**: La regola CSS globale `* { font-weight: 300 !important; }` è CRITICA
2. **Tailwind**: Usa classes standard, no personalizzazioni particolari
3. **Next.js**: Compatibile con App Router e Pages Router
4. **TypeScript**: Tutti i componenti sono tipizzati
5. **Accessibilità**: ARIA labels e semantic HTML

## 🔗 Dipendenze Principali

- **React 18+**
- **Next.js 13+ (opzionale)**
- **Tailwind CSS 3+**
- **Radix UI Primitives**
- **Lucide React (icone)**
- **TypeScript**

## 📄 Licenza

Questo codice è fornito "as-is" per uso interno. Adatta secondo le tue necessità.