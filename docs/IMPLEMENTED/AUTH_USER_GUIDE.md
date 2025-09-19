# 🔐 GUIDA AUTENTICAZIONE PILOTPROOS

**Sistema di Autenticazione**: ✅ **COMPLETAMENTE FUNZIONANTE**

---

## 🎯 **ACCESSO RAPIDO**

### **Business Portal** (Frontend principale)
1. Apri: **http://localhost:3000**
2. Credenziali:
   - **Email**: `tiziano@gmail.com`
   - **Password**: `testtest123`
3. Click "Login" → Sei dentro! 🎉

### **CLI Stack Manager** (Gestione Container)
1. Esegui: `./stack`
2. Password: `PilotPro2025!`
3. Menu interattivo disponibile

### **Stack Controller** (Monitoring)
1. Apri: **http://localhost:3005**
2. Credenziali:
   - **User**: `admin`
   - **Password**: `PilotPro2025!`

### **n8n Automation Engine**
1. Apri: **http://localhost:5678**
2. Credenziali:
   - **Email**: `admin`
   - **Password**: `pilotpros_admin_2025`

---

## 🔒 **SICUREZZA IMPLEMENTATA**

### **Backend Authentication**
- ✅ **JWT Tokens**: HttpOnly cookies sicuri
- ✅ **Password Hashing**: bcrypt con salt
- ✅ **Session Management**: 30 minuti timeout
- ✅ **Route Protection**: Tutte le API protette

### **Frontend Security**
- ✅ **Auth Guard**: Router protection completa
- ✅ **Token Validation**: Auto-logout su token scaduto
- ✅ **Password Confirmation**: Doppia immissione nei modal
- ✅ **CSRF Protection**: Token validation

### **Database Security**
- ✅ **Credential Storage**: PostgreSQL `pilotpros.users`
- ✅ **Password Encryption**: bcrypt 12 rounds
- ✅ **Connection Pooling**: Robust timeout handling
- ✅ **Schema Isolation**: Separazione n8n/pilotpros

---

## 👥 **GESTIONE UTENTI**

### **Utenti Esistenti**
```sql
-- Database: pilotpros.users
tiziano@gmail.com  | admin  | active
```

### **Creazione Nuovi Utenti**
1. Accedi al Business Portal come admin
2. Vai in Settings → User Management
3. Click "Nuovo Utente"
4. Compila:
   - Email
   - Password (minimo 8 caratteri, maiuscola, carattere speciale)
   - Conferma Password
   - Ruolo (admin/viewer)
5. Click "Crea Utente"

### **Modifica Password Esistente**
1. Settings → User Management
2. Click utente da modificare
3. Spunta "Cambia password"
4. Inserisci:
   - Nuova Password
   - Conferma Password
5. Click "Aggiorna Utente"

---

## 🛡️ **REQUISITI PASSWORD**

### **Criteri di Sicurezza**
- ✅ Minimo 8 caratteri
- ✅ Almeno una maiuscola (A-Z)
- ✅ Almeno un carattere speciale (!@#$%^&*)

### **Esempi Password Valide**
- `PilotPro2025!`
- `SecurePass123@`
- `MyPassword2024#`

---

## 🔄 **SESSIONE E LOGOUT**

### **Durata Sessione**
- **Frontend**: 30 minuti di inattività
- **CLI Manager**: 30 minuti dalla login
- **Stack Controller**: Basato su browser session

### **Logout Automatico**
- Token scaduto → Redirect a login
- Inattività prolungata → Session expired
- Browser chiuso → Logout automatico

### **Logout Manuale**
- Frontend: Click avatar → Logout
- CLI: Opzione 'q' (Quit)
- Stack Controller: Button logout

---

## 🚀 **QUICK START WORKFLOW**

### **Primo Accesso**
1. **Avvia Stack**: `./stack` → Password: `PilotPro2025!`
2. **Start All Services**: Opzione 5
3. **Open Business Portal**: Opzione 7 (auto-start stack)
4. **Login**: tiziano@gmail.com / testtest123
5. **Ready!** Sistema completo operativo

### **Uso Quotidiano**
1. **Check Status**: `./stack` → Opzione 1
2. **Open Portal**: `./stack` → Opzione 7
3. **Monitor System**: http://localhost:3005

---

## 🔧 **TROUBLESHOOTING**

### **Login Non Funziona**
1. Verifica credenziali (case-sensitive)
2. Check container status: `./stack` → Opzione 1
3. Restart backend: `./stack` → Opzione 2 → Backend API

### **CLI Password Non Accettata**
1. Verifica: `PilotPro2025!` (exact case)
2. Se bloccato: Ctrl+C e riprova
3. Docker non attivo: CLI auto-start Container Engine

### **Session Scaduta Frequentemente**
- Normale dopo 30 minuti inattività
- Re-login automatico richiesto
- Dati non persi (salvati nel database)

---

**🎯 CONCLUSION**: Sistema di autenticazione enterprise-grade completamente funzionante e sicuro per uso in produzione.