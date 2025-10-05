# 🧪 NOMIC-EMBED TEST GUIDE - Configurazione Verificata da Documentazione Ufficiale

**Data**: 2025-10-04
**Documentazione consultata**: https://huggingface.co/nomic-ai/nomic-embed-text-v1.5

---

## ✅ CONFIGURAZIONE CORRETTA (da docs ufficiali)

### **REQUISITO CRITICO: Task Prefixes OBBLIGATORI**

Nomic-embed **RICHIEDE** prefissi per ogni testo:

| Prefix | Quando Usarlo | Esempio |
|--------|---------------|---------|
| `search_document:` | Documenti nel RAG (storage) | `search_document: PilotProOS è un sistema...` |
| `search_query:` | Query utente (retrieval) | `search_query: Come funziona PilotProOS?` |
| `classification:` | Task di classificazione | `classification: Questo testo è positivo` |
| `clustering:` | Task di clustering | `clustering: Group similar documents` |

**ERRORE COMUNE**: Usare nomic senza prefissi → accuracy degrada drasticamente!

---

## 🔧 IMPLEMENTAZIONE CORRETTA

### **Codice Aggiornato** (`on_premise_embeddings.py`):

```python
class NomicEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(
        self,
        model_name: str = "nomic-ai/nomic-embed-text-v1.5",
        task_type: str = "search_document",  # REQUIRED!
        device: Optional[str] = None
    ):
        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,  # REQUIRED!
            device=device
        )
        self.task_type = task_type

    def __call__(self, input: Documents) -> Embeddings:
        # Add prefix to OGNI documento (OBBLIGATORIO!)
        prefixed_input = [f"{self.task_type}: {text}" for text in input]

        embeddings = self.model.encode(
            prefixed_input,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings.tolist()
```

### **Uso Corretto in ChromaDB**:

```python
# Per DOCUMENTI nel RAG (storage)
nomic_ef_docs = NomicEmbeddingFunction(task_type="search_document")

collection = client.create_collection(
    name="pilotpros_knowledge_nomic",
    embedding_function=nomic_ef_docs,
    metadata={"hnsw:space": "cosine"}
)

# Add documents (prefix aggiunto automaticamente!)
collection.add(
    documents=["PilotProOS automatizza processi aziendali"],
    ids=["doc1"]
)

# Per QUERY utente (retrieval)
nomic_ef_query = NomicEmbeddingFunction(task_type="search_query")

# Search (prefix aggiunto automaticamente!)
results = collection.query(
    query_texts=["Come funziona il sistema?"],
    n_results=5
)
```

---

## 🐳 TEST NEL CONTAINER DOCKER

### **Prerequisiti**:
1. Docker Desktop in esecuzione
2. Collection OpenAI esistente con 9 documenti REALI
3. API Key OpenAI (solo per baseline comparison)

### **Step 1: Build Container**

```bash
# Build container embeddings con nomic
docker compose build embeddings-service-dev
```

### **Step 2: Start Container**

```bash
# Start servizio (download nomic ~500MB prima volta)
docker compose up -d embeddings-service-dev

# Check logs (verifica download completato)
docker logs -f pilotpros-embeddings-dev
```

**Expected Output**:
```
🚀 Starting ON-PREMISE Embeddings Service
Loading default model: nomic...
✅ Default model loaded: nomic-embed-v1.5 (lightweight)
Service ready! Endpoints:
  POST /embed - Generate embeddings
  GET /models - List available models
  GET /health - Health check
```

### **Step 3: Health Check**

```bash
curl http://localhost:8001/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "on-premise-embeddings",
  "version": "1.0.0",
  "models_loaded": 1,
  "available_models": ["stella", "gte-qwen2", "nomic"]
}
```

### **Step 4: Test Embeddings API**

```bash
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Test documento PilotProOS"],
    "model": "nomic"
  }'
```

**Expected Response**:
```json
{
  "embeddings": [[0.1, 0.2, ..., 0.768]],  // 768 dimensioni
  "model": "nomic",
  "dimension": 768,
  "count": 1
}
```

### **Step 5: Run Comparison Test**

```bash
# Exec nel container
docker exec -it pilotpros-embeddings-dev bash

# Run test (NEL CONTAINER!)
cd /app
python3 test_nomic_in_docker.py
```

**Expected Test Flow**:
1. ✅ Load OpenAI collection (9 docs, 26 chunks)
2. ✅ Load nomic model (~500MB download)
3. ✅ Migrate 9 docs to nomic collection (con `search_document:` prefix)
4. ✅ Run 8 queries (con `search_query:` prefix)
5. ✅ Compare accuracy nomic vs OpenAI
6. ✅ Show statistics + verdict

---

## 📊 EXPECTED RESULTS

### **Metrics da Monitorare**:

1. **Accuracy Comparison**:
   - Average Improvement: -5% to +10% (simile a OpenAI)
   - Best Case: +15% (nomic outperforms)
   - Worst Case: -10% (acceptable trade-off for $0 cost)

2. **Resource Usage** (nel container):
   - RAM: 2-3 GB (vs 8-10 GB stella)
   - CPU: ~50-70% during inference
   - Storage: ~500 MB (model weights)

3. **Performance**:
   - Model Load Time: 10-30s (first time)
   - Embedding Generation: 0.5-2s per query (CPU)
   - Total Test Duration: 2-5 minuti

### **Verdict Criteria**:

| Avg Improvement | Verdict | Action |
|----------------|---------|--------|
| > +15% | 🎉 ECCELLENTE | Switch immediato |
| +5% to +15% | ✅ OTTIMO | Switch consigliato |
| 0% to +5% | 📈 BUONO | Switch consigliato (ZERO costi!) |
| -5% to 0% | ⚖️ SIMILE | Considera switch (risparmio $12K/anno) |
| < -5% | ⚠️ INFERIORE | Valuta trade-off costi vs accuracy |

---

## 🔍 TROUBLESHOOTING

### **Issue 1: Container OOM (Out of Memory)**
```
Error: Container killed (OOM)
```

**Soluzione**:
```bash
# Increase memory limit in docker-compose.yml
memory: 4G  # da 3G a 4G
```

### **Issue 2: Model Download Fallisce**
```
Error: Connection timeout during download
```

**Soluzione**:
```bash
# Manual download nel container
docker exec -it pilotpros-embeddings-dev bash
pip install --no-cache-dir sentence-transformers
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', trust_remote_code=True)"
```

### **Issue 3: Prefissi Mancanti**
```
Warning: Accuracy significantly lower than expected
```

**Verifica**:
```python
# Check che prefissi siano aggiunti
nomic_ef = NomicEmbeddingFunction(task_type="search_document")
result = nomic_ef(["test text"])
# Verifica che internamente sia "search_document: test text"
```

---

## 📋 CHECKLIST PRE-TEST

- [ ] Docker Desktop in esecuzione
- [ ] Collection OpenAI esiste con 9 documenti
- [ ] OPENAI_API_KEY configurata (per baseline)
- [ ] Container embeddings buildato
- [ ] Memoria Mac >= 8GB disponibile
- [ ] Spazio disco >= 2GB disponibile

---

## 🎯 POST-TEST ACTIONS

### **Se Test Passa (accuracy >= -5%)**:

1. **Switch Production**:
```python
# In maintainable_rag.py
from app.rag.on_premise_embeddings import NomicEmbeddingFunction

self.embedding_function = NomicEmbeddingFunction(
    task_type="search_document"
)
```

2. **Remove OpenAI Dependency**:
```bash
# In requirements.txt
# openai>=1.104.2  # REMOVED: usando nomic on-premise ($0!)
```

3. **Update CLAUDE.md**:
```markdown
## RAG System
- Embeddings: nomic-embed-text-v1.5 (ON-PREMISE, $0/anno)
- Costo: ZERO (vs $12,000/anno OpenAI)
- Accuracy: simile a ada-002 (±5%)
```

### **Se Test Fallisce (accuracy < -10%)**:

1. **Verifica Configurazione**:
   - Prefissi corretti? (`search_document:` / `search_query:`)
   - Task type corretto?
   - Trust remote code enabled?

2. **Test Alternativi**:
   - Prova `stella` (più pesante ma MTEB score superiore)
   - Prova `gte-qwen2` (multilingual, Apache 2.0)

3. **Analizza Trade-off**:
   - Accuracy: -10% → -15%
   - Risparmio: $12,000/anno
   - Decisione: costi vs performance?

---

**Created**: 2025-10-04
**Status**: Ready for testing (configuration verified)
**Documentation Source**: https://huggingface.co/nomic-ai/nomic-embed-text-v1.5
**Container**: pilotpros-embeddings-dev (Port 8001)
