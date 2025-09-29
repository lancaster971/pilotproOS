# 🧠 Multi-LLM Configuration for Intelligence Engine

## 📋 Available Models & Providers

### 🎯 OpenAI Models OFFERTA SPECIALE (Your Current Access)

#### 1M Token Group (250K for usage tiers 1-2):
- `gpt-5-codex`
- `gpt-5-2025-08-07`
- `gpt-5-chat-latest`
- `gpt-4.5-preview-2025-02-27` (deprecated 7/14/25)
- `gpt-4.1-2025-04-14`
- `gpt-4o-2024-05-13`
- `gpt-4o-2024-08-06`
- `gpt-4o-2024-11-20`
- `o3-2025-04-16`
- `o1-preview-2024-09-12`
- `o1-2024-12-17`

#### 10M Token Group (2.5M for usage tiers 1-2):
- `gpt-5-mini-2025-08-07`
- `gpt-5-nano-2025-08-07`
- `gpt-4.1-mini-2025-04-14`
- `gpt-4.1-nano-2025-04-14`
- `gpt-4o-mini-2024-07-18`
- `o4-mini-2025-04-16`
- `o1-mini-2024-09-12`
- `codex-mini-latest`

---

## 🚀 Groq (FREE TIER)

### Models Available (FREE):
- `llama-3.3-70b-versatile` - Best overall
- `llama-3.2-90b-text-preview` - Large context
- `llama-3.2-11b-text-preview` - Fast responses
- `llama-3.2-3b-preview` - Ultra-fast
- `mixtral-8x7b-32768` - Good for coding
- `gemma2-9b-it` - Google's model
- `deepseek-r1-distill-llama-70b` - Reasoning

### Setup:
```bash
# Get API key from: https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxx

# Install
pip install langchain-groq
```

### LangChain Integration:
```python
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=os.getenv("GROQ_API_KEY")
)
```

---

## 🤖 Anthropic Claude (Direct API)

### Models Available:
- `claude-3-5-sonnet-20241022` - Best overall ($3/1M input, $15/1M output)
- `claude-3-5-haiku-20241022` - Fast & cheap ($0.80/1M input, $4/1M output)
- `claude-3-opus-20240229` - Most capable ($15/1M input, $75/1M output)

### Setup:
```bash
# Get API key from: https://console.anthropic.com/api
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx
```

### LangChain Integration:
```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-5-haiku-20241022",  # Cheapest!
    temperature=0.7,
    max_tokens=4096,
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
```

---

## 🌟 Google Gemini (Direct API + FREE tier)

### Models Available:
- `gemini-2.0-flash-exp` - FREE tier (15 RPM, 1M TPM, 1500 RPD)
- `gemini-1.5-flash` - FREE tier (15 RPM, 1M TPM, 1500 RPD)
- `gemini-1.5-flash-8b` - FREE tier (15 RPM, 4M TPM, 1500 RPD)
- `gemini-1.5-pro` - FREE tier (2 RPM, 32K TPM, 50 RPD)

### Setup:
```bash
# Get API key from: https://aistudio.google.com/apikey
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx
```

### LangChain Integration:
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",  # FREE!
    temperature=0.7,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)
```

---

## 🌐 OpenRouter (Pay-per-use, SUPER cheap)

### Top Models (Cost-effective):
- `anthropic/claude-3.5-sonnet` - $3/1M tokens
- `google/gemini-2.0-flash-exp` - $0.15/1M tokens
- `deepseek/deepseek-r1` - $0.14/1M tokens
- `meta-llama/llama-3.3-70b-instruct` - $0.60/1M tokens
- `openai/gpt-4o-mini` - $0.15/1M tokens
- `mistralai/mistral-large` - $3/1M tokens

### Setup:
```bash
# Get API key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
```

### LangChain Integration (usando ChatOpenAI):
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="google/gemini-2.0-flash-exp",  # Super cheap!
    default_headers={
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "PilotProOS Intelligence Engine"
    }
)
```

---

## 📦 Dependencies Required

### Core:
```txt
# Already in requirements-simple.txt
langchain==0.3.27
langchain-community==0.3.29
langchain-openai==0.3.33

# ADD THESE:
langchain-groq==0.3.8  # Official Groq integration
```

### Environment Variables (.env):
```bash
# OpenAI (if you have it)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx

# Groq (FREE)
GROQ_API_KEY=gsk_xxxxxxxxxxxx

# OpenRouter (Pay-per-use)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# Optional: Anthropic direct
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
```

---

## 🎯 Recommended Strategy - ULTIMATE SETUP

### 🆓 **Layer 1 - FREE TIER** (Start here!)
1. **Google Gemini** `gemini-2.0-flash-exp` - 15 req/min FREE
2. **Groq** `llama-3.3-70b-versatile` - 7K req/min FREE
3. **Google Gemini** `gemini-1.5-flash-8b` - 4M tokens/min FREE

### 💰 **Layer 2 - ULTRA CHEAP** ($0.15-0.80/1M tokens)
1. **OpenRouter** `google/gemini-2.0-flash-exp` - $0.15/1M
2. **OpenRouter** `deepseek/deepseek-r1` - $0.14/1M
3. **Anthropic** `claude-3-5-haiku` - $0.80/1M (direct)

### 💎 **Layer 3 - PREMIUM** (Complex tasks)
1. **Anthropic** `claude-3-5-sonnet` - $3/1M
2. **OpenAI** `gpt-4o` - $2.50/1M
3. **Anthropic** `claude-3-opus` - $15/1M

---

## 🔧 Implementation Plan

### Phase 1: Setup Dependencies ✅
```bash
pip install langchain-groq==0.3.8
```

### Phase 2: Multi-LLM Router
```python
class MultiLLMRouter:
    def __init__(self):
        self.groq = ChatGroq(...)  # FREE
        self.openrouter = ChatOpenAI(base_url="...")  # CHEAP
        self.openai = ChatOpenAI(...)  # PREMIUM

    def route(self, query_type):
        if query_type == "simple":
            return self.groq
        elif query_type == "complex":
            return self.openrouter
        else:
            return self.openai
```

### Phase 3: Cost Optimization
- Track token usage per provider
- Auto-switch based on:
  - Query complexity
  - Response time requirements
  - Cost budget
  - Rate limits

---

## 📊 Complete Cost Comparison

| Provider | Model | Input Cost | Output Cost | Notes |
|----------|-------|------------|-------------|-------|
| **Google** | Gemini 2.0 Flash | FREE | FREE | 15 RPM, 1M TPM |
| **Google** | Gemini 1.5 Flash-8B | FREE | FREE | 15 RPM, 4M TPM! |
| **Groq** | Llama 3.3 70B | FREE | FREE | 7K req/min |
| **Groq** | Mixtral 8x7B | FREE | FREE | Rate limited |
| **OpenRouter** | DeepSeek R1 | $0.14/1M | $2.80/1M | Great reasoning |
| **OpenRouter** | Gemini 2.0 Flash | $0.15/1M | $0.30/1M | When free tier exhausted |
| **Anthropic** | Claude 3.5 Haiku | $0.80/1M | $4/1M | Fast & smart |
| **OpenAI** | GPT-4o-mini | $0.15/1M | $0.60/1M | Via OpenRouter |
| **Anthropic** | Claude 3.5 Sonnet | $3/1M | $15/1M | Best quality |
| **OpenAI** | GPT-4o | $2.50/1M | $10/1M | Direct API |

---

## ⚠️ Important Notes

1. **Groq FREE Tier Limits**:
   - 7,000 requests/minute
   - 14,000 tokens/minute
   - Perfect for development!

2. **OpenRouter Advantages**:
   - No monthly fees
   - Access to 200+ models
   - Single API for all providers
   - Auto-fallback on errors

3. **LangSmith Tracking**:
   - All calls are traced
   - Cost tracking per provider
   - Performance comparison

---

## 🚀 Next Steps

1. Get API keys:
   - [ ] Groq: https://console.groq.com
   - [ ] OpenRouter: https://openrouter.ai/keys

2. Add to `.env`:
   - [ ] GROQ_API_KEY
   - [ ] OPENROUTER_API_KEY

3. Test each provider:
   - [ ] Groq free calls
   - [ ] OpenRouter cheap models
   - [ ] Fallback chain