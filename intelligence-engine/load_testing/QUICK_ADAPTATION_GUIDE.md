# ⚡ Quick Adaptation Guide per Load Testing Framework

**Tempo di setup**: 15-30 minuti
**Skill level**: Intermediate Python
**Prerequisites**: Docker, Python 3.11+, Load testing framework installato

---

## 🚀 Setup Rapido (5 minuti)

### 1. **Copia Template**
```bash
# Naviga nella directory load_testing
cd intelligence-engine/load_testing

# Copia template per il tuo progetto
cp templates/locustfile_template.py locustfile_[YOUR_PROJECT].py
cp templates/config_template.conf [YOUR_PROJECT]_config.conf
```

### 2. **Install Dependencies**
```bash
pip install locust==2.31.8 prometheus-client==0.22.1 pandas==2.2.3 matplotlib==3.9.2
```

### 3. **Quick Test**
```bash
# Test basic connectivity
python locustfile_[YOUR_PROJECT].py

# Run validation test
python run_enterprise_load_test.py --users 5 --duration 1m
```

---

## 🎯 Adattamento per Dominio (10 minuti)

### **Step 1: Aggiorna Target System**

```python
# In locustfile_[YOUR_PROJECT].py
class YourProjectLoadTester(FastHttpUser):
    host = "http://your-system:8000"  # ✅ UPDATE THIS
```

### **Step 2: Configura Endpoint Principali**

```python
@task(10)
def test_main_endpoint(self):
    payload = {
        "query": "your query format",     # ✅ UPDATE FORMAT
        "user_id": self.session_id       # ✅ UPDATE FIELDS
    }

    with self.client.post("/your/api/endpoint", json=payload, catch_response=True) as response:  # ✅ UPDATE URL
        # Add your validation logic
        pass
```

### **Step 3: Domain-Specific Queries**

Sostituisci `_get_realistic_queries()` con query del tuo dominio:

**E-commerce**:
```python
return [
    "Search for laptops under $1000",
    "Add product to cart",
    "Check shipping options",
    "Apply discount code",
    "Process checkout"
]
```

**Finance**:
```python
return [
    "Check account balance",
    "Transfer $500 to savings",
    "Show transaction history",
    "Set up automatic payment",
    "Investment portfolio status"
]
```

**Healthcare**:
```python
return [
    "Schedule appointment with Dr. Smith",
    "Check lab results",
    "Request prescription refill",
    "View medical history",
    "Update insurance information"
]
```

---

## 📊 Configurazione Performance Targets (5 minuti)

### **Aggiorna Soglie nel Config**

```conf
# In [YOUR_PROJECT]_config.conf

# Single tenant (typical case)
[single_tenant]
users = 10
p95_threshold_ms = 5000    # ✅ UPDATE based on your SLA
p99_threshold_ms = 8000    # ✅ UPDATE based on your SLA
error_threshold_percent = 1.0

# Enterprise (if needed)
[enterprise]
users = 100
p95_threshold_ms = 2000    # ✅ UPDATE for enterprise SLA
p99_threshold_ms = 3000    # ✅ UPDATE for enterprise SLA
error_threshold_percent = 0.1
```

### **Performance Benchmarks per Dominio**

| Dominio | P95 Target | P99 Target | Error Rate | Note |
|---------|------------|------------|------------|------|
| **E-commerce** | 3s | 5s | 0.2% | Product search tolerance |
| **Finance** | 1s | 2s | 0.05% | Financial accuracy critical |
| **Healthcare** | 4s | 7s | 0.1% | Patient data reliability |
| **AI/LLM** | 6s | 10s | 1% | Complex processing acceptable |
| **Real-time** | 500ms | 1s | 0.01% | Trading/gaming systems |

---

## 🔧 Customization Patterns

### **Pattern 1: REST API Testing**
```python
@task(10)
def test_rest_api(self):
    # GET request
    response = self.client.get("/api/resource/123")

    # POST with JSON
    payload = {"name": "test", "value": 123}
    response = self.client.post("/api/resource", json=payload)

    # PUT update
    response = self.client.put("/api/resource/123", json={"status": "updated"})
```

### **Pattern 2: GraphQL Testing**
```python
@task(5)
def test_graphql(self):
    query = """
    query GetUser($id: ID!) {
        user(id: $id) {
            name
            email
            status
        }
    }
    """
    payload = {
        "query": query,
        "variables": {"id": "123"}
    }
    response = self.client.post("/graphql", json=payload)
```

### **Pattern 3: WebSocket Testing**
```python
def on_start(self):
    # Connect WebSocket
    self.ws = websocket.WebSocket()
    self.ws.connect("ws://localhost:8000/ws")

@task(3)
def test_websocket(self):
    message = {"type": "ping", "data": "test"}
    self.ws.send(json.dumps(message))
    response = self.ws.recv()
```

### **Pattern 4: File Upload Testing**
```python
@task(2)
def test_file_upload(self):
    files = {'file': ('test.txt', 'file content', 'text/plain')}
    response = self.client.post("/api/upload", files=files)
```

---

## 📈 Monitoring Setup (5 minuti)

### **Aggiorna Metriche Custom**

```python
# In locustfile_[YOUR_PROJECT].py
your_project_requests = Counter(
    'your_project_requests_total',  # ✅ CHANGE PROJECT NAME
    'Total requests for your project',
    ['endpoint', 'status']
)

your_project_business_metric = Gauge(
    'your_project_conversion_rate',  # ✅ ADD BUSINESS METRICS
    'Conversion rate for your project'
)
```

### **Business Metrics Examples**

**E-commerce**:
```python
ecommerce_cart_conversion = Gauge('ecommerce_cart_conversion_rate', 'Cart to checkout conversion')
ecommerce_revenue_per_user = Histogram('ecommerce_revenue_per_user', 'Revenue per user')
```

**Finance**:
```python
finance_transaction_success = Counter('finance_successful_transactions', 'Successful transactions')
finance_fraud_detection = Counter('finance_fraud_detected', 'Fraud cases detected')
```

---

## 🎮 Quick Test Scenarios

### **Scenario 1: Smoke Test (Daily)**
```bash
python run_enterprise_load_test.py \
  --users 5 \
  --duration 1m \
  --ramp-up 1
```

### **Scenario 2: Load Test (Weekly)**
```bash
python run_enterprise_load_test.py \
  --users 50 \
  --duration 10m \
  --ramp-up 10
```

### **Scenario 3: Stress Test (Monthly)**
```bash
python run_enterprise_load_test.py \
  --users 200 \
  --duration 20m \
  --ramp-up 20
```

---

## 🚨 Common Adaptations

### **Authentication Required**
```python
def on_start(self):
    # Login and get token
    login_response = self.client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    self.token = login_response.json()["token"]

@task
def authenticated_request(self):
    headers = {"Authorization": f"Bearer {self.token}"}
    response = self.client.get("/api/protected", headers=headers)
```

### **Database Testing**
```python
@task
def test_database_intensive(self):
    # Simulate database-heavy operations
    payload = {"query": "complex database query", "limit": 1000}
    response = self.client.post("/api/search", json=payload)
```

### **Multi-Step Workflows**
```python
@task
def test_complete_workflow(self):
    # Step 1: Create resource
    create_response = self.client.post("/api/resource", json={"name": "test"})
    resource_id = create_response.json()["id"]

    # Step 2: Update resource
    self.client.put(f"/api/resource/{resource_id}", json={"status": "active"})

    # Step 3: Get resource
    self.client.get(f"/api/resource/{resource_id}")

    # Step 4: Delete resource
    self.client.delete(f"/api/resource/{resource_id}")
```

---

## ✅ Validation Checklist

Completa questa checklist prima di considerare l'adattamento finito:

### **Configuration**
- [ ] Target host aggiornato
- [ ] Endpoint principali configurati
- [ ] Performance targets definiti
- [ ] Metriche custom aggiunte

### **Test Scenarios**
- [ ] Query realistiche per il dominio
- [ ] Workflow completi testati
- [ ] Error handling validato
- [ ] Authentication funzionante (se necessario)

### **Monitoring**
- [ ] Metriche business configurate
- [ ] Alert thresholds definiti
- [ ] Report generation funzionante
- [ ] Dashboard configurato (se disponibile)

### **Performance**
- [ ] Smoke test passa (5 users, 1 min)
- [ ] Load test passa (50 users, 10 min)
- [ ] Performance targets raggiunti
- [ ] Resource usage accettabile

---

## 🆘 Troubleshooting Rapido

### **Problema: Connection Refused**
```bash
# Verifica che il target system sia attivo
curl http://your-system:8000/health
```

### **Problema: High Error Rate**
```python
# Aggiungi debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Problema: Slow Performance**
```python
# Verifica timeout settings
with self.client.post("/api/endpoint", json=payload, timeout=30) as response:
    pass
```

### **Problema: Memory Issues**
```python
# Riduci batch size
@task
def memory_optimized_test(self):
    # Process smaller batches
    for batch in small_batches:
        self.client.post("/api/batch", json=batch)
```

---

## 📞 Support

- **Framework Documentation**: `LOAD_TESTING_FRAMEWORK.md`
- **Template Files**: `templates/` directory
- **Example Configurations**: `scenarios/` directory
- **Original Implementation**: `locustfile_enterprise.py` (PilotProOS)

**Success Pattern**: Copy → Modify → Test → Deploy