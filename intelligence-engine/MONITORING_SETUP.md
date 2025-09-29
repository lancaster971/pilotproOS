# 📊 MONITORING PRODUZIONE - GUIDA SETUP

**STATUS**: ✅ **PRONTO PER PRODUZIONE**

## 📈 Sistema Monitoring Implementato

### ✅ COMPONENTI ATTIVI

1. **Prometheus Metrics** - Port 8000/metrics
   - 24 metriche custom PilotProOS
   - Metriche sistema (Python, processo)
   - Auto-tracking API calls e agent execution

2. **Dashboard Grafana** - `/monitoring/grafana-dashboard.json`
   - 14 pannelli professionali
   - Monitoraggio real-time
   - Alert system integrato

3. **Sistema Alerting** - Regole Prometheus predefinite
   - High error rate
   - Slow response time
   - Low system health
   - High token usage

---

## 🚀 GUIDA DEPLOY

### 1. Verifica Stato Attuale

```bash
# Controlla che Intelligence Engine sia attivo
curl http://localhost:8000/health

# Verifica metriche Prometheus
curl http://localhost:8000/metrics | grep pilotpros_

# Test chiamata API
echo '{"message": "Test", "user_id": "monitoring"}' | \
curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d @-
```

### 2. Setup Prometheus Server

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'pilotpros-intelligence'
    static_configs:
      - targets: ['pilotpros-intelligence-engine-dev:8000']
    metrics_path: /metrics
    scrape_interval: 10s
```

### 3. Import Dashboard Grafana

1. Accedi a Grafana UI
2. Import Dashboard
3. Carica file: `monitoring/grafana-dashboard.json`
4. Configura Data Source: Prometheus URL

### 4. Attiva Alert Rules

```bash
# Copia alert rules
cp monitoring/alert-rules.yml /prometheus/
```

---

## 📊 METRICHE DISPONIBILI

### **Agent & LangGraph**
- `pilotpros_agent_requests_total` - Richieste per agent
- `pilotpros_agent_response_seconds` - Tempo risposta
- `pilotpros_langgraph_nodes_executed_total` - Nodi eseguiti
- `pilotpros_langgraph_duration_seconds` - Durata esecuzione grafo

### **Router & Cost Savings**
- `pilotpros_router_decisions_total` - Decisioni routing
- `pilotpros_router_savings_dollars_total` - Risparmi Groq

### **N8N & RAG**
- `pilotpros_n8n_workflows_queried_total` - Query workflow
- `pilotpros_rag_searches_total` - Ricerche RAG
- `pilotpros_embedding_cache_hits_total` - Hit cache embeddings

### **System Health**
- `pilotpros_system_health` - Score salute sistema (0-100)
- `pilotpros_active_sessions` - Sessioni attive
- `pilotpros_api_requests_total` - Richieste API
- `pilotpros_errors_total` - Errori per tipo

### **Business Value**
- `pilotpros_business_value_dollars_total` - Valore business generato
- `pilotpros_agent_cost_dollars_total` - Costi per agent

---

## 🎯 DASHBOARD GRAFANA

### Pannelli Principali

1. **Agent Request Rate** - Rate richieste per agent
2. **Agent Response Time (95th percentile)** - Latency performance
3. **System Health Score** - Salute sistema
4. **Cost Savings Today (Groq)** - Risparmi giornalieri
5. **Active Sessions** - Sessioni utente attive
6. **Error Rate** - Tasso errori per minuto
7. **Token Usage by Model** - Utilizzo token per modello
8. **Router Decision Distribution** - Distribuzione decisioni router
9. **LangGraph Node Execution** - Esecuzioni nodi grafo
10. **API Endpoint Latency (p95)** - Latency endpoint
11. **N8N Workflow Operations** - Operazioni workflow
12. **Cache Hit Rate** - Percentuale hit cache
13. **Business Value Generated** - Valore business per ora
14. **Active Alerts** - Alert attivi

---

## 🚨 ALERT RULES

### Alert Critici

```yaml
- alert: HighErrorRate
  expr: rate(pilotpros_errors_total[5m]) > 0.1
  for: 5m
  annotations:
    summary: "Tasso errori elevato rilevato"

- alert: SlowAgentResponse
  expr: histogram_quantile(0.95, rate(pilotpros_agent_response_seconds_bucket[5m])) > 10
  for: 5m
  annotations:
    summary: "Tempo risposta agent degradato"

- alert: LowSystemHealth
  expr: pilotpros_system_health < 80
  for: 10m
  annotations:
    summary: "Score salute sistema sotto soglia"
```

---

## 📈 METRICHE TEST RISULTATI

### Ultimo Test Eseguito

```
✅ Metriche API: 5 chiamate tracciate
✅ System Health: 100%
✅ Agent Latency: 2-8 secondi (normale per multi-agent)
✅ Cost Savings: Metriche attive
✅ Database Pool: 20 connessioni configurate
✅ Agents Registered: 3 (Milhena, N8N Expert, Data Analyst)
```

### Performance

- **API Calls Tracked**: ✅ pilotpros_api_requests_total
- **Response Time**: ✅ Histogram con bucket 0.01s - +Inf
- **Agent Routing**: ✅ Tracking per agent
- **Cost Tracking**: ✅ Dollars per agent/model
- **Health Monitoring**: ✅ Score 0-100

---

## 🛠️ COMMANDS UTILI

### Debug Metriche

```bash
# Verifica tutte le metriche PilotProOS
curl -s http://localhost:8000/metrics | grep "pilotpros_" | grep -v "^#"

# Conta metriche attive
curl -s http://localhost:8000/metrics | grep "pilotpros_.*[0-9]" | wc -l

# Verifica specific metric
curl -s http://localhost:8000/metrics | grep "pilotpros_api_requests_total"

# Test load con 5 chiamate
for i in {1..5}; do
  echo "Test $i"
  echo '{"message": "Test '$i'", "user_id": "load-test"}' | \
  curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d @- -m 30
done
```

### Monitoring Status

```bash
# Container health
docker ps | grep intelligence

# Logs monitoring
docker logs pilotpros-intelligence-engine-dev | grep -i monitoring

# Memory usage
docker stats pilotpros-intelligence-engine-dev --no-stream
```

---

## 🎉 CONCLUSIONI

### ✅ PRONTO PER GO-LIVE

Il sistema di monitoring è **completamente funzionale** e pronto per la produzione:

1. **Metriche Real-time** - Tutte attive e tracciano dati reali
2. **Dashboard Professionale** - 14 pannelli per monitoring completo
3. **Alert System** - Regole predefinite per incident detection
4. **Performance Tracking** - Latency, throughput, errors
5. **Cost Monitoring** - Tracking risparmi Groq e costi per agent
6. **Business Value** - Metriche valore business generato

### Prossimi Step Opzionali

- [ ] Setup Grafana Cloud per monitoring remoto
- [ ] Integrazione Slack/Teams per alert
- [ ] Retention policy per metriche storiche
- [ ] Dashboard mobile per monitoring mobile

**Il monitoring è enterprise-ready per ambiente di produzione!** 🚀