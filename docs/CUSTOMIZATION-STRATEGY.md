# Documento Tecnico: Personalizzazione e Sicurezza n8n in Stack Aziendale

## **Obiettivo**

Integrare n8n in uno stack tecnologico a 3 livelli (Database, Backend, Frontend) su Docker, con **completa anonimizzazione** per il cliente finale e **accesso dev semplificato**.

### **Requisiti Obbligatori:**
1. **Privacy del prodotto**: Cliente non deve mai sapere che usa n8n
2. **Personalizzazione dinamica**: Branding personalizzato ad ogni deployment cliente
3. **Aggiornamenti automatici**: n8n si aggiorna normalmente senza perdere customizzazioni
4. **Sicurezza**: Zero scoperta via port scanning o fingerprinting
5. **Accesso dev**: Team dev accede facilmente per sviluppo e manutenzione

### **Stack Attuale:**
- **Architettura**: 3-tier (PostgreSQL + Express Backend + Vue Frontend)
- **Containerizzazione**: Docker con network isolation
- **Configurazione**: Reverse proxy nginx con branding injection

## **Architettura della Soluzione**

### **Schema Generale: "Casa con Due Porte"**
```
🌐 INTERNET
    ↓
┌─────────────────────────────────────────────────┐
│  🔒 NGINX REVERSE PROXY (Container)            │
│  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   🎭 PORTA CLIENTE   │  │   🔧 PORTA DEV      │ │
│  │                     │  │                     │ │
│  │ / → Business UI     │  │ /dev-panel → n8n    │ │
│  │ Logo personalizzato │  │ Auth: dev/password  │ │
│  │ Branding dinamico   │  │ Rate limiting       │ │
│  └─────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  🐳 RETE INTERNA ISOLATA (No External Access)  │
│                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │    n8n Container    │  │  PostgreSQL + App   │ │
│  │                     │  │                     │ │
│  │  • Versione stock   │  │  • Dual schema      │ │
│  │  • Zero modifiche   │  │  • n8n + business   │ │
│  │  • Auto-updates ✅   │  │  • Isolation rete   │ │
│  └─────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## **Implementazione Tecnica**

### **1. Network Isolation Completa**

#### Docker Compose Configuration
```yaml
version: '3.8'

networks:
  # Rete interna - ZERO accesso esterno
  internal:
    driver: bridge
    internal: true
    
  # DMZ per reverse proxy
  dmz:
    driver: bridge

services:
  # n8n completamente isolato
  n8n:
    image: n8nio/n8n:latest
    networks:
      - internal
    expose:
      - "5678"  # Solo interno, NO ports esterni
    volumes:
      - n8n_data:/home/node/.n8n
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
    # NESSUNA personalizzazione sui sorgenti

  # PostgreSQL isolato
  postgres:
    image: postgres:16
    networks:
      - internal
    expose:
      - "5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=pilotpros_db
      - POSTGRES_USER=pilotpros
      - POSTGRES_PASSWORD=secure_password

  # Reverse proxy - unico accesso esterno
  nginx:
    image: nginx:alpine
    networks:
      - dmz
      - internal
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/branding:/etc/nginx/branding
      - ./nginx/.htpasswd:/etc/nginx/.htpasswd
    depends_on:
      - n8n

volumes:
  n8n_data:
  postgres_data:
```

### **2. Reverse Proxy con Branding Injection**

#### nginx.conf
```nginx
upstream n8n_backend {
    server n8n:5678;
}

# Rate limiting per dev panel
limit_req_zone $binary_remote_addr zone=admin:10m rate=10r/m;

server {
    listen 80;
    server_name _;

    # Nascondere headers tecnici
    proxy_hide_header X-Powered-By;
    proxy_hide_header Server;
    more_set_headers "Server: Business Platform";

    # PORTA CLIENTE - Interfaccia personalizzata
    location / {
        proxy_pass http://n8n_backend;
        
        # Injection CSS/JS personalizzato
        sub_filter '<head>' '<head>
            <link rel="stylesheet" href="/custom-branding.css">
            <script src="/custom-branding.js"></script>';
        sub_filter '<title>n8n</title>' '<title>Business Automation Platform</title>';
        sub_filter 'n8n' 'Automation Hub';
        sub_filter_once off;
        
        # Headers proxy standard
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # PORTA DEV - Accesso team sviluppo
    location /dev-panel {
        auth_basic "Team Development Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        # Rate limiting
        limit_req zone=admin burst=5 delay=2;
        
        # Rewrite per accesso diretto a n8n
        rewrite ^/dev-panel/(.*)$ /$1 break;
        proxy_pass http://n8n_backend;
        
        # Headers per identificare accesso dev
        proxy_set_header X-Dev-Access "true";
        proxy_set_header X-Original-URI $request_uri;
        
        # Headers proxy standard
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Logging accessi dev
        access_log /var/log/nginx/dev-access.log combined;
    }

    # Asset personalizzati
    location /custom-branding.css {
        alias /etc/nginx/branding/dynamic-style.css;
        expires 1h;
    }
    
    location /custom-branding.js {
        alias /etc/nginx/branding/dynamic-script.js;
        expires 1h;
    }

    # Bloccare accessi diretti n8n
    location ~* \.(n8n|workflow) {
        deny all;
    }
}
```

### **3. Sistema Personalizzazione Dinamica**

#### Script Generazione Branding
```bash
#!/bin/bash
# generate-branding.sh - Eseguito ad ogni deployment cliente

generate_client_branding() {
    local CLIENT_NAME="$1"
    local PRIMARY_COLOR="${2:-#$(openssl rand -hex 3)}"
    local COMPANY_DOMAIN="$3"
    
    # Genera CSS personalizzato
    cat > /etc/nginx/branding/dynamic-style.css << EOF
/* Branding dinamico per $CLIENT_NAME */
:root {
    --primary-color: $PRIMARY_COLOR;
    --brand-name: "$CLIENT_NAME";
    --company-domain: "$COMPANY_DOMAIN";
}

/* Nascondere riferimenti n8n */
.n8n-logo, [data-test-id="n8n-logo"] {
    display: none !important;
}

/* Logo personalizzato */
.logo:before {
    content: var(--brand-name);
    color: var(--primary-color);
    font-size: 24px;
    font-weight: bold;
}

/* Styling personalizzato login */
.auth-view {
    background: linear-gradient(135deg, var(--primary-color), #f8fafc);
}

.auth-view h1:after {
    content: " - " var(--brand-name);
}

/* Nascondere footer n8n */
footer, .footer, [class*="footer"] {
    display: none !important;
}
EOF

    # Genera JavaScript personalizzato
    cat > /etc/nginx/branding/dynamic-script.js << EOF
// Personalizzazione dinamica runtime
(function() {
    // Replace document title
    document.title = '$CLIENT_NAME Business Platform';
    
    // Replace any remaining n8n references
    function replaceTextContent() {
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let node;
        while (node = walker.nextNode()) {
            node.textContent = node.textContent
                .replace(/n8n/gi, 'Automation Hub')
                .replace(/workflow/gi, 'Business Process');
        }
    }
    
    // Execute on DOM ready and mutations
    document.addEventListener('DOMContentLoaded', replaceTextContent);
    
    // Observer per SPA changes
    const observer = new MutationObserver(replaceTextContent);
    observer.observe(document.body, { childList: true, subtree: true });
})();
EOF

    echo "✅ Branding generato per $CLIENT_NAME"
    echo "   - Colore primario: $PRIMARY_COLOR"
    echo "   - Dominio: $COMPANY_DOMAIN"
    echo "   - CSS: /etc/nginx/branding/dynamic-style.css"
    echo "   - JS:  /etc/nginx/branding/dynamic-script.js"
}

# Esempio uso
# generate_client_branding "Azienda SpA" "#2563eb" "azienda.com"
```

### **4. Gestione Credenziali Dev Team**

#### Setup .htpasswd
```bash
#!/bin/bash
# setup-dev-access.sh

# Crea credenziali dev team
htpasswd -cb /etc/nginx/.htpasswd dev-team "pilotpros_dev_2025"
htpasswd -b /etc/nginx/.htpasswd developer "dev_secure_pass"
htpasswd -b /etc/nginx/.htpasswd support "support_temp_pass"

echo "✅ Credenziali dev team create:"
echo "   URL: https://cliente.com/dev-panel"
echo "   dev-team / pilotpros_dev_2025"
echo "   developer / dev_secure_pass"
echo "   support / support_temp_pass"
```

## **Accesso Team Sviluppo**

### **URL Fisso + Credenziali Permanenti**

**Per sviluppatori interni:**
```
URL: https://cliente-domain.com/dev-panel
Username: dev-team
Password: pilotpros_dev_2025
```

**Per assistenza esterna:**
```
URL: https://cliente-domain.com/dev-panel  
Username: support
Password: [password temporanea generata]
```

### **Caratteristiche Accesso Dev:**
- ✅ **URL fisso**: Facile da ricordare e comunicare
- ✅ **Rate limiting**: Protezione brute force (10 req/min)
- ✅ **Logging completo**: Tutti gli accessi tracciati
- ✅ **n8n completo**: Accesso a tutte le funzionalità
- ✅ **Multi-utente**: Diverse credenziali per team/support

## **Vantaggi della Soluzione**

### **Per il Cliente:**
- ✅ **Zero knowledge n8n**: Non sa mai cosa c'è sotto il cofano
- ✅ **Interfaccia branded**: Logo e colori aziendali
- ✅ **Performance**: Nessun overhead per personalizzazioni
- ✅ **Sicurezza**: n8n completamente nascosto da internet

### **Per il Team Dev:**
- ✅ **Accesso semplice**: URL fisso + credenziali permanenti
- ✅ **n8n originale**: Tutte le funzioni di sviluppo disponibili
- ✅ **Hot reload**: Modifiche in tempo reale durante sviluppo
- ✅ **Debugging**: Logs e monitoring completi

### **Per gli Aggiornamenti:**
- ✅ **Auto-update n8n**: Immagine Docker standard si aggiorna
- ✅ **Customizzazioni preserved**: CSS/JS esterni non toccati
- ✅ **Zero downtime**: Update container senza perdita personalizzazioni
- ✅ **Rollback sicuro**: Possibilità ritorno versione precedente

## **Implementazione Step-by-Step**

### **Fase 1: Setup Infrastructure (1 giorno)**
1. Creare network isolation Docker
2. Configurare nginx reverse proxy
3. Setup volume per branding personalizzato
4. Test connettività interna

### **Fase 2: Branding System (1 giorno)**  
1. Script generazione CSS/JS dinamico
2. Template personalizzazione per cliente
3. Test injection e replacement testi
4. Validazione zero riferimenti n8n

### **Fase 3: Dev Access Setup (0.5 giorni)**
1. Configurare .htpasswd con credenziali team
2. Setup logging accessi dev
3. Test rate limiting e security
4. Documentazione URL e credenziali

### **Fase 4: Testing & Hardening (0.5 giorni)**
1. Port scanning test (verificare zero discovery n8n)
2. Penetration testing accesso non autorizzato  
3. Test aggiornamento n8n con customizzazioni
4. Load testing reverse proxy performance

## **Deployment e Manutenzione**

### **Comando Deploy Cliente**
```bash
#!/bin/bash
# deploy-client.sh

CLIENT_NAME="$1"
PRIMARY_COLOR="$2" 
DOMAIN="$3"

echo "🚀 Deploy PilotProOS per $CLIENT_NAME"

# Genera branding personalizzato
./generate-branding.sh "$CLIENT_NAME" "$PRIMARY_COLOR" "$DOMAIN"

# Deploy stack Docker
docker-compose up -d

# Verifica deployment
curl -s https://$DOMAIN/health || echo "❌ Deploy failed"
curl -s https://$DOMAIN/dev-panel -u dev-team:pilotpros_dev_2025 || echo "❌ Dev access failed"

echo "✅ Deploy completato!"
echo "   - Cliente: https://$DOMAIN"
echo "   - Dev panel: https://$DOMAIN/dev-panel"
```

### **Aggiornamento n8n**
```bash
#!/bin/bash
# update-n8n.sh

echo "🔄 Aggiornamento n8n..."

# Backup stato corrente
docker-compose exec postgres pg_dump pilotpros_db > backup_$(date +%Y%m%d).sql

# Pull ultima versione n8n
docker-compose pull n8n

# Restart con nuova versione
docker-compose up -d n8n

# Verifica funzionamento
sleep 10
curl -s http://localhost/dev-panel -u dev-team:pilotpros_dev_2025 | grep -q "sign in" && echo "✅ Update successful"

echo "✅ n8n aggiornato - customizzazioni preserved"
```

## **Monitoraggio e Logging**

### **Log Files Essenziali:**
```
/var/log/nginx/access.log          # Accessi cliente
/var/log/nginx/dev-access.log      # Accessi team dev  
/var/log/nginx/error.log           # Errori nginx
/var/log/docker/n8n.log           # Log n8n interno
```

### **Metriche da Monitorare:**
- Accessi non autorizzati a /dev-panel
- Tentativi port scanning su porte n8n
- Performance reverse proxy
- Uptime n8n e personalizzazioni

## **Stato Implementazione**

### **✅ Completato:**
- Analisi architettura e requisiti
- Design network isolation
- Strategia branding injection  
- Sistema accesso dev semplificato

### **📋 Prossimi Step:**
1. Implementare docker-compose.yml con network isolation
2. Configurare nginx.conf con dual-path access
3. Creare script generazione branding dinamico
4. Setup credenziali dev team e testing completo
5. Validazione security e performance

## **Conclusioni**

La soluzione **Hybrid Approach con URL fisso dev** risolve tutti i requisiti:

- **🎭 Cliente**: Vede solo interfaccia personalizzata, zero knowledge n8n
- **🔧 Dev Team**: Accesso facile e permanente per sviluppo/manutenzione  
- **🔄 Aggiornamenti**: n8n si aggiorna normalmente, customizzazioni preserved
- **🔒 Sicurezza**: Network isolation completa + rate limiting
- **⚡ Performance**: Zero overhead per personalizzazioni

**Raccomandazione**: Procedere con implementazione immediata per validazione pratica della soluzione.

---

*Documento aggiornato: 2025-09-05*  
*Versione n8n target: 1.108.1+*  
*Prossimo step: Implementazione docker-compose e nginx config*