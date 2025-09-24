# 🤖 Configurazione Modelli AI - Agent Engine

## 📋 Provider Supportati e Modelli Disponibili (2025)

### 🆓 **GRATIS / Low Cost**

#### **Groq (GRATIS e VELOCISSIMO!)**
```bash
export GROQ_API_KEY="gsk-..."  # Ottieni gratis su groq.com
```
Modelli:
- `llama-3.2-90b-vision-preview` - Llama 3.2 con vision
- `llama-3.2-70b-versatile` - Velocissimo
- `llama-3.1-70b-versatile` - Stabile
- `mixtral-8x7b-32768` - Ottimo per coding
- `gemma2-9b-it` - Leggero e veloce

#### **DeepInfra (Economico)**
```bash
export DEEPINFRA_API_KEY="..."
```
Modelli:
- `meta-llama/Meta-Llama-3.1-405B-Instruct` - Potentissimo
- `meta-llama/Meta-Llama-3.1-70B-Instruct`
- `Qwen/Qwen2.5-72B-Instruct`

### 💰 **Premium**

#### **OpenAI**
```bash
export OPENAI_API_KEY="sk-..."
```
Modelli 2025:
- `gpt-4o` - Ultimo multimodale
- `gpt-4o-mini` - Economico ma potente
- `gpt-4-turbo` - Bilanciato
- `gpt-3.5-turbo` - Veloce ed economico

#### **OpenRouter (Accesso a TUTTI i modelli)**
```bash
export OPENROUTER_API_KEY="sk-or-..."
```
Modelli TOP:
- `anthropic/claude-3.5-sonnet` - Migliore per ragionamento
- `google/gemini-2.0-flash-exp` - Gemini 2.0
- `qwen/qwen-2.5-72b-instruct` - GRATIS via OpenRouter!
- `x-ai/grok-2-1212` - Grok 2 di X.AI
- `deepseek/deepseek-chat` - Economico e buono

## 🚀 Come Usare i Modelli

### 1. **SimpleAssistant - Selezione Automatica**

```python
from simple_assistant import SimpleAssistant

assistant = SimpleAssistant()

# Usa automaticamente il modello gratis migliore disponibile
result = assistant.answer_question("Ciao", prefer_free=True)

# Forza un modello specifico
result = assistant.answer_question(
    "Analizza questo codice",
    provider="groq",
    model="mixtral-8x7b-32768"
)

# Usa GPT-4o per task complessi
result = assistant.answer_question(
    "Progetta architettura microservizi",
    provider="openai",
    model="gpt-4o",
    prefer_free=False
)
```

### 2. **CrewAI - Multi-Agent con Modelli Diversi**

```python
from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

# Agent 1: GPT-4o per strategia
strategic_agent = Agent(
    role="Stratega",
    llm=ChatOpenAI(model_name="gpt-4o")
)

# Agent 2: Groq per analisi veloce (GRATIS!)
data_agent = Agent(
    role="Analista Dati",
    llm=ChatGroq(model_name="llama-3.2-90b-vision-preview")
)

# Agent 3: Claude per creatività
creative_agent = Agent(
    role="Creativo",
    llm=ChatOpenAI(
        model_name="anthropic/claude-3.5-sonnet",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
)
```

### 3. **Selezione Modello per Task**

| Task | Provider Consigliato | Modello | Costo |
|------|---------------------|---------|-------|
| Chat veloce | Groq | llama-3.2-70b | GRATIS |
| Analisi codice | Groq | mixtral-8x7b | GRATIS |
| Strategia business | OpenAI | gpt-4o | Premium |
| Creatività | OpenRouter | claude-3.5-sonnet | Premium |
| Analisi dati | Groq | llama-3.2-90b | GRATIS |
| Vision/Immagini | OpenAI | gpt-4o | Premium |
| Traduzione | DeepInfra | qwen-2.5-72b | Low cost |

## 🎯 Best Practices

1. **Inizia SEMPRE con modelli gratis** (Groq) per development
2. **Usa GPT-4o solo per task che richiedono massima intelligenza**
3. **Claude è migliore per task creativi e di scrittura**
4. **Llama 3.2 via Groq è ottimo per analisi veloce**
5. **Mixtral è eccellente per coding**

## 🔧 Setup Veloce

```bash
# Minimo per iniziare (GRATIS!)
export GROQ_API_KEY="gsk-..."  # Registrati su groq.com

# Ottimale (mix gratis e premium)
export GROQ_API_KEY="gsk-..."
export OPENAI_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-or-..."

# Test
python -c "
from simple_assistant import SimpleAssistant
a = SimpleAssistant()
print(a.get_available_models())
"
```

## 📊 Confronto Velocità

| Provider | Modello | Token/sec | Latenza |
|----------|---------|-----------|---------|
| Groq | llama-3.2-70b | 500+ | <1s |
| OpenAI | gpt-4o | 50-100 | 2-3s |
| OpenRouter | claude-3.5 | 30-50 | 3-4s |
| DeepInfra | llama-405b | 20-30 | 4-5s |

## 💡 Trucchi

1. **Risparmia soldi**: Usa Groq per il 90% dei task
2. **Multi-agent**: Mescola modelli gratis e premium
3. **Fallback**: Configura sempre almeno 2 provider
4. **Cache**: Riusa risposte quando possibile
5. **Batch**: Raggruppa richieste simili