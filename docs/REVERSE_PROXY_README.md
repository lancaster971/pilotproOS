# PilotProOS Reverse Proxy System

Sistema di **reverse proxy con network isolation** che nasconde completamente lo stack tecnico (n8n, PostgreSQL, Express) dal cliente finale, offrendo due interfacce distinte:

- **👥 Interfaccia Cliente**: Business-friendly con terminologia aziendale
- **🔧 Interfaccia Dev Team**: Accesso diretto a n8n per sviluppo e manutenzione

## 🎯 Obiettivo

**Una sola pagina n8n, vista in modi diversi** attraverso nginx reverse proxy che applica:
- **Branding injection dinamico** per i clienti  
- **Accesso diretto n8n** per il team di sviluppo
- **Network isolation completa** per sicurezza enterprise

## 🏗️ Architettura

```
🌐 INTERNET
    ↓
┌─────────────────────────────────────────────────────┐
│  🔒 NGINX REVERSE PROXY (unico accesso esterno)    │
│                                                     │
│  📱 Cliente:              🔧 Dev Team:             │
│  domain.com/             domain.com/dev-panel       │
│       │                        │                   │
│       ▼                        ▼                   │
│  ┌─────────────────┐      ┌─────────────────┐       │
│  │ BRANDING        │      │ n8n ORIGINALE   │       │
│  │ INJECTION       │      │                 │       │
│  │                 │      │ • Admin panel   │       │
│  │ • CSS dinamico  │      │ • Debug tools   │       │
│  │ • JS replacement│      │ • Full features │       │
│  │ • Logo aziendale│      │ • Logs access   │       │
│  │ • Terminologia  │      │                 │       │
│  │   business      │      │                 │       │
│  └─────────────────┘      └─────────────────┘       │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  🌐 RETE INTERNA ISOLATA (NO external access)      │
│                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ Frontend    │ │ Backend     │ │ n8n + DB    │    │
│  │ Vue 3       │ │ Express     │ │ PostgreSQL  │    │
│  │ :3000       │ │ :3001       │ │ :5678/:5432 │    │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
nginx/
├── nginx.conf                 # Configurazione reverse proxy principale
├── .htpasswd                 # Credenziali dev team  
└── branding/
    ├── dynamic-style.css     # CSS branding universale
    └── dynamic-script.js     # JavaScript branding universale

docker-compose.reverseproxy.yml # Stack isolato con nginx proxy
scripts/
├── setup-reverse-proxy.sh    # Setup automatico completo
├── test-reverse-proxy.sh     # Test funzionamento sistema  
└── generate-client-branding.sh # Generazione branding cliente
```

## 🚀 Quick Start

### 1. Setup Sistema Reverse Proxy

```bash
# Esegui setup completo
./scripts/setup-reverse-proxy.sh

# Verifica funzionamento
./scripts/test-reverse-proxy.sh
```

### 2. Accesso Sistema

**Cliente** (Business Interface):
- **URL**: http://localhost
- **Interfaccia**: Branding aziendale, terminologia business
- **Funzionalità**: Gestione processi business, analytics, monitoring

**Dev Team** (n8n Admin):  
- **URL**: http://localhost/dev-panel
- **Credenziali**: `dev-team` / `pilotpros_dev_2025`
- **Interfaccia**: n8n originale completo
- **Funzionalità**: Workflow editor, debug, logs, admin

## 🎨 Branding per Cliente

### Generazione Branding Personalizzato

```bash
# Genera branding per cliente specifico
./scripts/generate-client-branding.sh \
  --company-name "Azienda SpA" \
  --brand-name "Business Hub" \
  --primary-color "#2563EB" \
  --secondary-color "#7C3AED" \
  --domain "azienda.com"
```

### Cosa Vede il Cliente

- **Logo aziendale** al posto del logo n8n
- **Terminologia business**: "Business Process" invece di "workflow"  
- **Colori brand**: Schema colori personalizzato
- **Zero riferimenti tecnici**: n8n, PostgreSQL, Docker completamente nascosti
- **Interface pulita**: Focus su business value, non tecnologia

### Cosa Vede il Dev Team

- **n8n originale**: Interfaccia completa senza modifiche
- **Funzionalità complete**: Workflow editor, debug, monitoring
- **Accesso dati**: Database, logs, configurazioni
- **Shortcuts dev**: Ctrl+Shift+D per debug mode

## 🔒 Security & Network Isolation

### Porte Esposte

| Porta | Servizio | Accesso |
|-------|----------|---------|
| 80    | nginx HTTP | 🌐 Pubblico |  
| 443   | nginx HTTPS | 🌐 Pubblico |
| 3001  | Backend API | 🔒 **BLOCCATO** |
| 5678  | n8n Server | 🔒 **BLOCCATO** |
| 5432  | PostgreSQL | 🔒 **BLOCCATO** |

### Funzionalità Security

- ✅ **Network isolation**: Backend services in rete interna isolata
- ✅ **Rate limiting**: Protezione DDoS su API e dev panel
- ✅ **Basic auth**: Dev panel protetto con credenziali
- ✅ **Security headers**: OWASP compliance headers
- ✅ **SSL/TLS**: Certificati auto-generati per development  
- ✅ **Technology hiding**: Zero fingerprinting possibile

## 🧪 Testing

### Test Automatico

```bash
# Esegui tutti i test
./scripts/test-reverse-proxy.sh

# Output atteso:
# ✅ Tests Passed: 12/12
# 📈 Success Rate: 100%
# 🎉 ALL TESTS PASSED!
```

### Test Manuali

**Cliente Access**:
```bash
# Frontend business
curl -k http://localhost/
# Dovrebbe mostrare HTML con terminologia business

# API business  
curl -k http://localhost/api/health
# Dovrebbe rispondere {"status":"healthy"}
```

**Dev Team Access**:
```bash  
# n8n admin (dovrebbe richiedere auth)
curl -k http://localhost/dev-panel
# Dovrebbe richiedere HTTP Basic Auth

# Con credenziali
curl -u dev-team:pilotpros_dev_2025 -k http://localhost/dev-panel
# Dovrebbe mostrare interfaccia n8n login
```

**Security Tests**:
```bash
# Porte backend (dovrebbero essere bloccate)
nc -zv localhost 3001  # Dovrebbe fallire
nc -zv localhost 5678  # Dovrebbe fallire  
nc -zv localhost 5432  # Dovrebbe fallire

# Solo nginx dovrebbe rispondere
nc -zv localhost 80    # Dovrebbe funzionare
nc -zv localhost 443   # Dovrebbe funzionare
```

## ⚙️ Configurazione

### Variabili Ambiente (.env)

```bash
# Database
DB_PASSWORD=pilotpros_dev_password_randomhex

# n8n Admin  
N8N_ADMIN_USER=admin
N8N_ADMIN_PASSWORD=pilotpros_admin_2025

# Security
JWT_SECRET=random_base64_secret

# SSL
SSL_ENABLED=true
```

### Credenziali Dev Team

| Username | Password | Ruolo |
|----------|----------|-------|
| dev-team | pilotpros_dev_2025 | Development Team |
| developer | dev_secure_pass | Individual Developer |
| support | support_temp_2025 | External Support |

### Personalizzazione Branding

```css
/* nginx/branding/dynamic-style.css */
:root {
    --primary-color: #10B981;    /* Verde personalizzabile */
    --secondary-color: #3B82F6;  /* Blu personalizzabile */
    --brand-name: "Your Company"; /* Nome brand */
    --company-name: "Business Platform"; /* Nome interfaccia */
}
```

## 🔄 Workflow

### Development Workflow

1. **Sviluppo**: Dev team lavora su http://localhost/dev-panel
2. **Test**: Verifica che funzioni su http://localhost (vista cliente)  
3. **Branding**: Genera branding cliente con script
4. **Deploy**: Cliente riceve URL con branding personalizzato

### Client Onboarding

1. **Generazione branding** specifico per cliente
2. **Deploy personalizzato** con colori e logo aziendali
3. **Training cliente** solo su interfaccia business
4. **Support dev team** tramite dev-panel

## 🚨 Troubleshooting

### Container non si avvia

```bash
# Check container status
docker-compose -f docker-compose.reverseproxy.yml ps

# Check logs
docker-compose -f docker-compose.reverseproxy.yml logs nginx
docker-compose -f docker-compose.reverseproxy.yml logs n8n
```

### Nginx errori configurazione

```bash
# Test nginx config
docker exec pilotpros-nginx-proxy nginx -t

# Reload nginx
docker exec pilotpros-nginx-proxy nginx -s reload
```

### Porte non accessibili

```bash
# Verifica network
docker network inspect pilotproos_internal
docker network inspect pilotproos_dmz

# Check firewall
sudo ufw status
```

### Branding non applicato

```bash
# Verifica volume branding
docker exec pilotpros-nginx-proxy ls -la /etc/nginx/branding/

# Check nginx logs
docker exec pilotpros-nginx-proxy tail -f /var/log/nginx/access.log
```

## 🔄 Upgrade e Manutenzione

### Backup prima degli upgrade

```bash  
# Backup configurazione
tar -czf nginx-config-backup.tar.gz nginx/

# Backup SSL certificati
tar -czf ssl-backup.tar.gz ssl/
```

### Upgrade nginx o branding

```bash
# Stop sistema
docker-compose -f docker-compose.reverseproxy.yml down

# Update files
# ... modifiche ...

# Restart
./scripts/setup-reverse-proxy.sh
```

## 📚 Note Tecniche

### Compatibilità

- ✅ **Database**: Zero impatto - stesse tabelle, stessi dati
- ✅ **Backend**: Zero impatto - stesse API, stessa logica  
- ✅ **Frontend**: Zero impatto - stesso Vue, stessi component
- ✅ **n8n**: Zero impatto - versione stock, auto-updates preservati

### Performance

- **Overhead nginx**: ~1-2ms latency
- **CSS/JS injection**: Runtime processing, zero build impact
- **Network isolation**: Zero performance penalty
- **Benefits**: SSL termination, static caching, rate limiting

### Limitations  

- **Single domain**: Un branding per dominio (configurabile)
- **HTTP only**: HTTPS richiede certificati reali (Let's Encrypt consigliato)
- **Basic auth dev**: Per sicurezza advanced considerare OAuth/SSO

## 🎯 Risultati Finali

### Per il Cliente
- ✅ **Interfaccia branded** con logo e colori aziendali
- ✅ **Terminologia business** - zero tecnicismi
- ✅ **Zero knowledge n8n** - impossibile scoprire tecnologie sottostanti
- ✅ **Experience premium** - look&feel enterprise

### Per il Dev Team  
- ✅ **n8n completo** - tutte le funzionalità disponibili
- ✅ **Accesso sicuro** - protetto ma facile
- ✅ **Debug tools** - logs, monitoring, development
- ✅ **Workflow normale** - stesso environment di sviluppo

### Per il Business
- ✅ **Client satisfaction** - professional branded experience
- ✅ **Technology hiding** - competitive advantage protected  
- ✅ **Maintenance easy** - una sola infrastruttura, due viste
- ✅ **Scalability** - stesso pattern per tutti i clienti

---

**🎉 Sistema pronto per production deployment!**