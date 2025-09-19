# Stack Controller - Sistema di Monitoraggio e Controllo

## 📊 Panoramica

Lo **Stack Controller** è un sistema indipendente di monitoraggio e gestione che supervisiona tutti i servizi della piattaforma PilotProOS. Offre un controllo centralizzato con terminologia business-friendly, nascondendo completamente i dettagli tecnici dell'infrastruttura.

## 🎯 Caratteristiche Principali

### Monitoraggio in Tempo Reale
- **Dashboard Web Intuitiva**: Interfaccia professionale accessibile su porta 3005
- **WebSocket Updates**: Aggiornamenti live ogni 5 secondi
- **Metriche Performance**: CPU, memoria, uptime per ogni servizio
- **Log Attività**: Cronologia eventi con livelli di severità

### Gestione Automatica
- **Auto-Recovery**: Riavvio automatico servizi in errore
- **Dipendenze Intelligenti**: Gestisce ordine di riavvio corretto
- **Health Checks**: Controlli salute ogni 30 secondi
- **Alert Sistema**: Notifiche per problemi critici

### Terminologia Business
Il sistema traduce automaticamente tutti i termini tecnici:

| Termine Tecnico | Visualizzazione Business |
|-----------------|-------------------------|
| Container Docker | Servizio |
| postgres-dev | Sistema Gestione Dati |
| n8n | AI Automation Engine |
| backend-dev | Automation Engine |
| frontend-dev | Business Portal |
| nginx-dev | Access Manager |
| Running | Operativo |
| Stopped | Fermo |
| Memory Usage | Utilizzo Risorse |

## 🚀 Installazione

### 1. Avvio del Sistema

```bash
# Costruire e avviare lo Stack Controller
docker-compose up -d stack-controller

# Verificare lo stato
docker logs pilotpros-stack-controller
```

### 2. Accesso Dashboard

Aprire il browser su: `http://localhost:3005`

La dashboard mostrerà:
- **Stato Generale**: Tutti i Sistemi Operativi / Servizio Parziale / Servizio Degradato
- **Cards Servizi**: Ogni servizio con metriche e stato
- **Azioni Rapide**: Refresh, Export Report, Visualizza Log
- **Attività Recente**: Eventi sistema in tempo reale

## 📡 API REST

### Endpoints Disponibili

#### Stato Sistema
```http
GET /api/system/status
```
Ritorna stato completo di tutti i servizi

#### Lista Servizi
```http
GET /api/system/services
```
Elenco servizi con metriche performance

#### Dettaglio Servizio
```http
GET /api/system/service/:name
```
Informazioni dettagliate singolo servizio

#### Refresh Servizio
```http
POST /api/system/service/:name/refresh
```
Riavvia un servizio specifico

#### Metriche Performance
```http
GET /api/system/performance
```
Report aggregato utilizzo risorse

#### Eventi Sistema
```http
GET /api/system/events?limit=20
```
Cronologia eventi recenti

#### Overview Widget
```http
GET /api/system/overview
```
Riepilogo compatto per integrazione frontend

## 🔧 Configurazione

### File di Configurazione
`stack-controller/config/services.json`:

```json
{
  "services": {
    "postgres-dev": {
      "displayName": "Database Service",
      "businessName": "Sistema Gestione Dati",
      "critical": true,
      "maxRestarts": 3,
      "restartDelay": 5000,
      "dependencies": []
    },
    "n8n-dev": {
      "displayName": "Automation Engine",
      "businessName": "Motore di Automazione",
      "critical": true,
      "maxRestarts": 3,
      "restartDelay": 10000,
      "dependencies": ["postgres-dev"]
    }
  }
}
```

### Variabili Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| PORT | 3005 | Porta dashboard web |
| MONITOR_INTERVAL | 30 | Secondi tra controlli salute |
| AUTO_RECOVERY | true | Abilita recupero automatico |
| MAX_RESTART_ATTEMPTS | 3 | Tentativi massimi riavvio |

## 🎨 Integrazione Frontend PilotProOS

### Widget Dashboard
Aggiungere al componente Vue principale:

```vue
<template>
  <div class="system-health-widget">
    <h3>Stato Sistema</h3>
    <div class="health-indicator" :class="healthClass">
      {{ healthStatus }}
    </div>
    <div class="service-counts">
      <span class="operational">✅ {{ operational }} Operativi</span>
      <span class="warning" v-if="warning > 0">⚠️ {{ warning }} Avvisi</span>
      <span class="error" v-if="error > 0">❌ {{ error }} Errori</span>
    </div>
    <a href="http://localhost:3005" target="_blank">
      Apri Centro di Controllo
    </a>
  </div>
</template>

<script>
export default {
  data() {
    return {
      healthStatus: 'Verificando...',
      healthClass: 'checking',
      operational: 0,
      warning: 0,
      error: 0
    }
  },

  mounted() {
    this.fetchSystemHealth();
    setInterval(this.fetchSystemHealth, 30000);
  },

  methods: {
    async fetchSystemHealth() {
      try {
        const response = await fetch('http://localhost:3005/api/system/overview');
        const data = await response.json();

        this.healthStatus = data.health;
        this.operational = data.serviceCount.operational;
        this.warning = data.serviceCount.warning;
        this.error = data.serviceCount.error;

        // Imposta classe CSS per colore
        if (data.health === 'Tutti i Sistemi Operativi') {
          this.healthClass = 'healthy';
        } else if (data.health === 'Servizio Parziale') {
          this.healthClass = 'partial';
        } else {
          this.healthClass = 'degraded';
        }
      } catch (error) {
        console.error('Impossibile recuperare stato sistema:', error);
        this.healthStatus = 'Non Disponibile';
        this.healthClass = 'error';
      }
    }
  }
}
</script>
```

## 🛡️ Sicurezza

### Isolamento Container
- Accesso Docker socket in sola lettura
- Nessuna esposizione credenziali database
- Comunicazione solo su network interno

### Best Practices
1. **Non esporre** porta 3005 su internet pubblico
2. **Utilizzare** reverse proxy con autenticazione per produzione
3. **Monitorare** log per attività anomale
4. **Backup regolari** configurazione servizi

## 🚨 Troubleshooting

### Dashboard Non Accessibile
```bash
# Verificare container attivo
docker ps | grep stack-controller

# Controllare log
docker logs pilotpros-stack-controller

# Riavviare servizio
docker-compose restart stack-controller
```

### Servizi Non Visibili
```bash
# Verificare Docker socket montato
docker exec pilotpros-stack-controller ls -la /var/run/docker.sock

# Controllare configurazione
docker exec pilotpros-stack-controller cat /app/config/services.json
```

### WebSocket Non Connesso
1. Verificare firewall/proxy non blocchi WebSocket
2. Controllare console browser per errori
3. Testare connessione diretta: `ws://localhost:3005`

## 📈 Metriche e Performance

### Utilizzo Risorse
- **CPU**: ~2-5% in idle, ~10-15% durante controlli
- **Memoria**: ~50-100MB RAM
- **Network**: Minimo, solo comunicazione Docker API
- **Storage**: Log rotation automatica dopo 10MB

### Scalabilità
- Gestisce fino a 50 servizi simultaneamente
- Update rate configurabile (default 5 secondi)
- Cache intelligente per ridurre carico Docker API

## 🔄 Aggiornamenti

### Aggiornare Stack Controller
```bash
# Fermare servizio
docker-compose stop stack-controller

# Ricostruire immagine
docker-compose build stack-controller

# Riavviare
docker-compose up -d stack-controller
```

### Versionamento
- Versione corrente: **1.0.0**
- Compatibilità: Docker 20.10+, Node.js 18+
- Schema API: v1 (retrocompatibile)

## 📝 Note Implementazione

### Architettura
- **Pattern**: Observer con Event-Driven updates
- **Framework**: Express.js + Socket.io
- **UI**: Vue.js 3 con Composition API
- **Monitoring**: Docker API via Dockerode

### Estensioni Future
- [ ] Notifiche email per eventi critici
- [ ] Grafici storici performance
- [ ] Export report PDF/Excel
- [ ] Integrazione Slack/Teams
- [ ] Dashboard mobile responsive
- [ ] Backup automatico configurazioni

## 🆘 Supporto

Per problemi o domande:
1. Consultare log: `docker logs pilotpros-stack-controller`
2. Verificare configurazione: `/app/config/services.json`
3. Testare API: `curl http://localhost:3005/api/system/status`

---

*Stack Controller v1.0 - Sistema Professionale di Monitoraggio Enterprise*