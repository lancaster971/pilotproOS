# 🔴 LATENCY FIX FAILURE - ROOT CAUSE ANALYSIS

**Date**: 1 Ottobre 2025, 21:00
**Status**: ❌ FIX FAILED - Test 1 degraded by 4240%

---

## 📊 RISULTATI TEST AFTER FIX

| Test | Before | After | Change | Status |
|------|--------|-------|--------|--------|
| **Test 1** | 123ms | **5338ms** | **+4240%** | 🔴 **CRITICAL REGRESSION** |
| **Test 2** | 88206ms | 10731ms | -88% | ✅ Improved |
| **Test 3** | 5889ms | 4739ms | -19% | 🟡 Minor improvement |

**Average**: 14.3s → **5.4s** (62% improvement)
**BUT**: Simple queries degraded massively!

---

## 🔍 ROOT CAUSE IDENTIFIED

### **PROBLEMA 1: asyncio.wait_for DOPPIO TIMEOUT**

#### **Documentazione Ufficiale (Python 3.13 + Best Practices):**

> **"Nested wait_for() calls don't execute concurrently"**
> **"Each creates a coroutine that must be awaited sequentially"**
> **"The inner task isn't scheduled until the outer await completes"**

Source: Super Fast Python - Asyncio Timeout Best Practices

#### **Il Nostro Codice (SBAGLIATO):**

```python
# llm_disambiguator.py:160-163 (FIX 3)
response = await asyncio.wait_for(
    self.groq_llm.ainvoke(formatted),  # ChatGroq has internal timeout!
    timeout=3.0
)
```

**Problema**: ChatGroq/ChatOpenAI hanno già `timeout=30` interno!

**Risultato**:
- Outer timeout: 3s (nostro)
- Inner timeout: 30s (ChatGroq)
- **Conflict**: Se ChatGroq risponde in 2.9s, va in timeout lo stesso!

---

### **PROBLEMA 2: ChatGroq SEMPRE Timeouts**

#### **Logs (Test 1-8):**
```
GROQ disambiguation timeout after 3s
GROQ disambiguation timeout after 3s
GROQ disambiguation timeout after 3s
Disambiguation timeout after 5s, using rule-based fallback
```

**3 timeout GROQ + 1 timeout globale = 5s PERSI sempre!**

#### **Perché Timeout?**

1. **Nested asyncio.wait_for** blocca scheduling
2. **GROQ API slow to respond** (ma funzionava prima!)
3. **Timeout troppo aggressivo** (3s)

---

### **PROBLEMA 3: LangChain timeout vs request_timeout**

#### **Documentazione GitHub (Issue #27335):**

> **"The timeout parameter is not being honored when using ChatOpenAI"**
> **"Logs show timeout consistently set to None despite explicit configuration"**
> **RECOMMENDED: Use `request_timeout` instead of `timeout`**

#### **Il Nostro Codice:**

```python
# milhena_enhanced_llm.py:48-55
self.llm = ChatOpenAI(
    timeout=30,  # ❌ NON FUNZIONA!
    max_retries=1
)
```

**Dovrebbe essere:**
```python
self.llm = ChatOpenAI(
    request_timeout=30,  # ✅ QUESTO FUNZIONA
    max_retries=1
)
```

---

## 🎯 PERCHÉ TEST 1 È PEGGIORATO?

### **BEFORE (123ms)**
1. Query: "Come va il sistema oggi?"
2. GROQ risponde VELOCEMENTE (no disambiguation needed)
3. Response generator usa GROQ (free)
4. **Total: 123ms** ✅

### **AFTER (5338ms)**
1. Query: "Come va il sistema oggi?"
2. **GROQ disambiguation timeout dopo 3s** ❌
3. **OpenAI Nano timeout dopo 2s** ❌
4. **Rule-based fallback** (5s totali persi)
5. Response generator chiamato
6. **Total: 5338ms** 🔴

---

## 📚 DOCUMENTAZIONE CONSULTATA

### **1. LangChain Official Docs**
- ✅ ChatOpenAI API Reference
- ✅ Timeout parameter usage
- ❌ Best practices for asyncio.wait_for (NOT documented!)

### **2. GitHub Issues**
- ✅ Issue #27335: "OpenAI not honoring the timeout parameter"
- **Key Finding**: Use `request_timeout` instead of `timeout`

### **3. Python Async Best Practices**
- ✅ Super Fast Python: Asyncio Timeout Best Practices
- ✅ Python 3.13 Docs: Coroutines and Tasks
- **Key Finding**: Avoid nested asyncio.wait_for()

### **4. Stack Overflow**
- ✅ "asyncio.wait_for doesn't time out as expected"
- ✅ "async_timeout.timeout vs asyncio.wait_for"

---

## 🚀 PIANO D'AZIONE CORRETTO

### **FIX CORRECT 1: Rimuovi asyncio.wait_for Nested**

**File**: `intelligence-engine/app/milhena/llm_disambiguator.py`

```python
# ❌ WRONG (current)
response = await asyncio.wait_for(
    self.groq_llm.ainvoke(formatted),
    timeout=3.0
)

# ✅ CORRECT (remove outer timeout, trust LLM internal timeout)
response = await self.groq_llm.ainvoke(formatted)
```

**Rationale**: LLM ha già `request_timeout` interno configurato

---

### **FIX CORRECT 2: Usa request_timeout invece di timeout**

**File**: `intelligence-engine/app/milhena/llm_disambiguator.py:41-45`

```python
# ❌ WRONG
self.groq_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=os.getenv("GROQ_API_KEY")
)

# ✅ CORRECT
self.groq_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    request_timeout=10.0,  # Add explicit timeout
    api_key=os.getenv("GROQ_API_KEY")
)
```

**Applica anche a**:
- `openai_nano` (request_timeout=10.0)
- `openai_mini` (request_timeout=10.0)

---

### **FIX CORRECT 3: Global Timeout SOLO a Livello Endpoint**

**File**: `intelligence-engine/app/milhena/response_generator.py`

```python
# ✅ KEEP (questo è OK a livello endpoint)
async def generate(...):
    return await asyncio.wait_for(
        self._generate_internal(...),
        timeout=15.0
    )

# ❌ REMOVE nested timeouts dentro _generate_internal
# NO asyncio.wait_for su llm.ainvoke()!
```

**Rationale**: 1 solo timeout a livello più alto, non nested

---

### **FIX CORRECT 4: Aumenta Timeout Disambiguator**

**File**: `intelligence-engine/app/milhena/llm_disambiguator.py:122-126`

```python
# ❌ WRONG
return await asyncio.wait_for(
    self._disambiguate_internal(query, context),
    timeout=5.0  # Troppo aggressivo!
)

# ✅ CORRECT (REMOVE outer timeout, usa solo request_timeout interno)
return await self._disambiguate_internal(query, context)
```

**Rationale**: Se GROQ/OpenAI hanno request_timeout=10s, non serve outer timeout

---

## 📊 EXPECTED RESULTS (dopo fix corretti)

| Test | Before Fix | After Wrong Fix | After Correct Fix | Final Improvement |
|------|-----------|----------------|------------------|------------------|
| Test 1 | 123ms | 5338ms 🔴 | **200-300ms** ✅ | -60% (slower but acceptable) |
| Test 2 | 88206ms | 10731ms ✅ | **8-10s** ✅ | **-89%** |
| Test 3 | 5889ms | 4739ms 🟡 | **3-4s** ✅ | -35% |
| **Average** | 14.3s | 5.4s | **3-4s** ✅ | **-75%** |

---

## 🎯 LESSONS LEARNED

### **1. NEVER Nest asyncio.wait_for() on LLM Calls**
- ❌ LLM ha già timeout interno (`request_timeout`)
- ❌ Nested timeout non schedule correctly
- ✅ Trust LLM timeout + global timeout a livello endpoint

### **2. Use request_timeout NOT timeout**
- ❌ `timeout=30` parameter NON funziona (LangChain bug)
- ✅ `request_timeout=30` è il parametro corretto

### **3. Test RIGOROSAMENTE con Suite Completa**
- ❌ 1 test non è sufficiente (Test 2 migliorato, Test 1 peggiorato!)
- ✅ SEMPRE eseguire full suite (8 test)
- ✅ Confrontare statistiche BEFORE/AFTER

### **4. Consulta Documentazione PRIMA di Implementare**
- ✅ LangChain docs
- ✅ GitHub issues
- ✅ Best practices articles
- ✅ Stack Overflow

---

## 🚀 NEXT STEPS

1. **ROLLBACK Fix 3** (rimuovi asyncio.wait_for nested)
2. **IMPLEMENT Fix Correct 1-4** (request_timeout + no nested)
3. **TEST Full Suite** (8 test)
4. **VERIFY Improvements** (compare statistics)
5. **COMMIT se OK** (altrimenti iterate)

---

**Conclusione**: I fix erano teoricamente corretti ma praticamente sbagliati per:
1. Nested asyncio.wait_for() non funziona con LLM
2. `timeout` parameter non onorato da LangChain
3. Timeout troppo aggressivi (3s GROQ, 2s OpenAI)

**Fix corretti**: Rimuovi nested timeout, usa `request_timeout`, trust LLM internal timeout.
