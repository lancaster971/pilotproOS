# Test OAuth Setup - Microsoft Outlook

## 🔧 Setup Completato

✅ **HTTPS attivo**: https://localhost (certificato self-signed)  
✅ **n8n accessibile**: https://localhost/dev/n8n/  
✅ **OAuth callback**: https://localhost/rest/oauth2-credential/callback  
✅ **Webhook endpoint**: https://localhost/webhook/  
✅ **n8n variabili**: N8N_EDITOR_BASE_URL=https://localhost ✓  
✅ **Container ricostruito**: Environment variables corretti ✓  

## 🧪 Test OAuth Microsoft

### 1. Accesso n8n HTTPS
- URL: https://localhost/dev/n8n/
- Username: `admin`
- Password: `pilotpros_admin_2025`

### 2. Configurazione Credenziali Microsoft
1. Vai su **Credentials** → **Add credential**
2. Seleziona **Microsoft Outlook** 
3. **Callback URL**: `https://localhost/rest/oauth2-credential/callback`
4. Inserisci Client ID e Client Secret dalla tua Azure App
5. **Autorizza** → deve aprire finestra Microsoft con HTTPS

### 3. Verifica Funzionamento
- Il browser deve navigare a Microsoft login HTTPS
- Dopo autorizzazione, deve fare redirect a `https://localhost/rest/oauth2-credential/callback`
- n8n deve confermare connessione riuscita

## 🚨 Problemi Comuni

### Errore "redirect_uri_mismatch"
- Verifica che Azure App Registration abbia `https://localhost/rest/oauth2-credential/callback` 

### Errore SSL "unsafe connection"
- Nel browser: clicca "Advanced" → "Proceed to localhost (unsafe)"
- Oppure: aggiungi certificato alle trusted root

### Errore "network connection"
- Verifica containers: `docker ps`
- Testa endpoint: `curl -k https://localhost/rest/oauth2-credential/callback`

## ✅ Test Completato con Successo!
1. ✅ Accesso n8n HTTPS senza errori
2. ✅ Creazione credenziale Microsoft senza errori  
3. ✅ OAuth flow completo con redirect HTTPS
4. ✅ Test connection Microsoft riuscito
5. ✅ **Azure App configurata multi-tenant** (risolto AADSTS50194)

## 🎯 Setup HTTPS Development - COMPLETATO ✅

**✅ Funzionante:**
- HTTPS: `https://localhost/` (certificati self-signed con SAN)
- n8n: `https://localhost/dev/n8n/` (admin / pilotpros_admin_2025)
- OAuth callback: `https://localhost/rest/oauth2-credential/callback`
- Webhook: `https://localhost/webhook/`
- **Microsoft Outlook OAuth**: ✅ Testato e funzionante
- **Tutti i provider OAuth**: Pronti per HTTPS

**🔧 Fix Applicati:**
- Container n8n ricostruito con `N8N_EDITOR_BASE_URL=https://localhost`
- Certificati SSL con Subject Alternative Names per tutti gli IP/domini
- Azure App Registration configurata come multi-tenant

## 🚀 Prossimi Passi: HTTPS Produzione
Vedi: [docs/https-production-roadmap.md](docs/https-production-roadmap.md)