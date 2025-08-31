# MODAL DEVELOPMENT TODO CHECKLIST
**PilotProOS - Practical Development Tasks**

**Documento**: Todo Operativo per Sviluppo Modal  
**Versione**: 1.0.0  
**Target**: Sviluppatori in sessioni di chat  
**Riferimento**: MODAL_IMPLEMENTATION_GUIDE.md  

---

## 🎯 **QUICK START CHECKLIST**

### **Pre-Development Setup**
- [ ] **Leggi MODAL_IMPLEMENTATION_GUIDE.md** per patterns completi
- [ ] **Verifica CLAUDE.md** per terminologia business
- [ ] **Identifica tipo modal**: Simple/Detail/Timeline
- [ ] **Prepara dati API endpoint** se necessario

---

## 📝 **DEVELOPMENT PHASES**

### **🏗️ PHASE 1: BASE STRUCTURE** *(~30min)*

#### **File Creation**
- [ ] Crea file `[NomeModal].vue` in `frontend/src/components/`
- [ ] Aggiungi import necessari:
  ```javascript
  import { ref, onMounted, watch } from 'vue'
  import { X, [OtherIcons] } from 'lucide-vue-next'
  import { useUIStore } from '../../stores/ui'
  ```

#### **Template Base**
- [ ] **Teleport structure**:
  ```vue
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <!-- Modal content here -->
    </div>
  </Teleport>
  ```
- [ ] **Modal container**: `control-card` o `w-full max-w-6xl` per modal grandi
- [ ] **Header standard**: Title + metadata + close button
- [ ] **Loading state**: Spinner + testo "Caricamento..."
- [ ] **Error state**: Messaggio user-friendly + retry button

#### **Script Setup**
- [ ] **Props interface**:
  ```typescript
  interface Props {
    show: boolean
    [otherProps]: any
  }
  ```
- [ ] **Emits**:
  ```typescript
  const emit = defineEmits<{
    close: []
    [otherEvents]: [data: any]
  }>()
  ```
- [ ] **Reactive state**: `isLoading`, `error`, altri stati necessari

### **🎨 PHASE 2: CONTENT STRUCTURE** *(~45min)*

#### **Per Simple Modal**
- [ ] **Form structure** con validation
- [ ] **Input fields** con classi design system
- [ ] **Footer actions**: Annulla + Submit buttons
- [ ] **Error handling** per form submission

#### **Per Detail/Timeline Modal**  
- [ ] **Tab system**:
  ```vue
  <div class="flex items-center gap-1 p-2 border-b border-border">
    <button v-for="tab in tabs" :class="tabClasses">
      <component :is="tab.icon" class="h-4 w-4" />
      {{ tab.label }}
    </button>
  </div>
  ```
- [ ] **Scrollable content area**: `overflow-y-auto` con max-height
- [ ] **Tab content switching**: `v-if="activeTab === 'tabId'"`

#### **Per Timeline Modal Specifico**
- [ ] **Timeline steps structure**:
  ```vue
  <div v-for="(step, index) in timelineData.timeline" :class="getStepColor(step.status)">
    <!-- Step header expandable -->
    <!-- Step details collapsible -->
  </div>
  ```
- [ ] **Business context section** se applicabile
- [ ] **Raw data tab** per debugging

### **🔌 PHASE 3: API INTEGRATION** *(~30min)*

#### **Data Loading**
- [ ] **API endpoint setup**:
  ```javascript
  const loadData = async () => {
    isLoading.value = true
    error.value = null
    try {
      const response = await fetch('/api/business/[endpoint]')
      // Handle response
    } catch (err) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }
  ```
- [ ] **Error handling** con fallback user-friendly
- [ ] **Loading states** durante API calls
- [ ] **Data transformation** da tecnico a business language

#### **Per Timeline Modal**
- [ ] **Force refresh functionality**:
  ```javascript
  const handleForceRefresh = async () => {
    isRefreshing.value = true
    await loadData()
    uiStore.showToast('Success', 'Dati aggiornati', 'success')
    isRefreshing.value = false
  }
  ```
- [ ] **Business data parsing** con `humanizeStepData()` pattern
- [ ] **Real-time updates** se necessario

### **🎯 PHASE 4: UX POLISH** *(~20min)*

#### **Interactions**
- [ ] **Keyboard support**: ESC per chiudere, Enter per submit
- [ ] **Click outside** per chiudere modal
- [ ] **Focus management** quando modal si apre/chiude
- [ ] **Loading indicators** appropriati

#### **Responsive Design**
- [ ] **Mobile layout**: Stack vertical su small screens
- [ ] **Tablet layout**: Responsive grid/flex
- [ ] **Desktop layout**: Full multi-column quando appropriato

#### **Animations**
- [ ] **Entrance animation**: Modal fade-in + scale
- [ ] **Exit animation**: Smooth fade-out
- [ ] **Micro-interactions**: Hover effects, button states

### **🔗 PHASE 5: INTEGRATION** *(~15min)*

#### **Parent Component Integration**
- [ ] **Import modal** nel component genitore
- [ ] **State management**: `const showModal = ref(false)`
- [ ] **Open/close functions**:
  ```javascript
  const openModal = (data?) => {
    if (data) selectedData.value = data
    showModal.value = true
  }
  ```
- [ ] **Template usage**:
  ```vue
  <NomeModal
    :show="showModal"
    @close="showModal = false"
    @[otherEvents]="handleEvent"
  />
  ```

#### **Store Integration**
- [ ] **Pinia stores** se necessario per state sharing
- [ ] **UI store**: Toast notifications per feedback
- [ ] **Data stores**: Update dopo modifiche

---

## 🧪 **TESTING CHECKLIST**

### **Functional Testing**
- [ ] **Modal opens** correttamente quando triggered
- [ ] **Modal closes** con X, ESC, click outside
- [ ] **Loading states** funzionano durante API calls
- [ ] **Error states** mostrano messaggi appropriati
- [ ] **Form submission** (se applicabile) funziona
- [ ] **Data refresh** (se applicabile) aggiorna contenuto

### **UX Testing**
- [ ] **Responsive behavior** su mobile/tablet/desktop
- [ ] **Keyboard navigation** accessibile
- [ ] **Focus trapping** mantiene focus nel modal
- [ ] **Animations smooth** entrance/exit
- [ ] **Toast notifications** per feedback azioni

### **Business Logic Testing**
- [ ] **Terminologia business** corretta (no terminologia tecnica)
- [ ] **Data parsing** converte correttamente dati tecnici
- [ ] **Error messages** user-friendly (no stack traces)
- [ ] **Business context** appropriato per use case

---

## 🎨 **STYLING QUICK REFERENCE**

### **Modal Container Classes**
```css
/* Simple Modal */
.control-card w-full max-w-md

/* Detail Modal */  
w-full max-w-6xl max-h-[90vh] bg-gray-900 border border-green-500/30 rounded-xl shadow-2xl

/* Timeline Modal */
w-full max-w-6xl max-h-[90vh] bg-gray-900 border border-green-500/30 rounded-xl shadow-2xl premium-modal
```

### **Button Classes**
```css
/* Primary Action */
btn-control-primary

/* Secondary Action */
btn-control

/* Danger Action */
btn-control border-red-500/30 text-red-400 hover:bg-red-500/10
```

### **Status Colors**
```css
/* Success */
border-green-400/30 bg-green-400/5 text-green-400

/* Error */  
border-red-400/30 bg-red-400/5 text-red-400

/* Warning */
border-yellow-400/30 bg-yellow-400/5 text-yellow-400

/* Info */
border-blue-400/30 bg-blue-400/5 text-blue-400
```

---

## 🚨 **COMMON PITFALLS**

### **❌ EVITARE**
- **Mai usare** terminologia tecnica (n8n, PostgreSQL, workflow)
- **Non hardcodare** colori - usare design system classes
- **Non dimenticare** loading/error states
- **Non ignorare** mobile responsiveness
- **Non saltare** keyboard accessibility

### **✅ SEMPRE FARE**
- **Usare business language** in tutti i testi UI
- **Implementare error handling** robusto
- **Testare responsive** su tutti i breakpoints
- **Validare integration** con stores/API
- **Seguire patterns** dei modal esistenti

---

## 📞 **SUPPORT REFERENCE**

### **Files da Consultare**
- `docs/MODAL_IMPLEMENTATION_GUIDE.md` - Guida completa patterns
- `frontend/src/components/workflows/CreateWorkflowModal.vue` - Simple modal
- `frontend/src/components/workflows/WorkflowDetailModal.vue` - Detail modal  
- `frontend/src/components/agents/AgentDetailModal.vue` - Timeline modal
- `CLAUDE.md` - Business terminology guidelines

### **Key Functions da Replicare**
- `humanizeStepData()` - Business data parsing (AgentDetailModal)
- `getStepColor()` - Status color mapping
- `formatDuration()` - Time formatting
- `showTimelineModal` pattern - Modal visibility control

### **Design System Classes**
- `control-card` - Standard container
- `btn-control` / `btn-control-primary` - Button styles
- `text-text` / `text-text-muted` - Text colors
- `bg-surface` / `bg-surface-hover` - Background colors

---

**🎯 Usa questa checklist per implementare modal consistenti con gli standard PilotProOS!**