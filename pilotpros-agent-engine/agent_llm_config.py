#!/usr/bin/env python3
"""
Sistema di Assegnazione LLM Ottimizzato per Agenti Milhena
Ogni agente usa il modello MIGLIORE per il suo compito specifico
"""

# MAPPATURA AGENTI → MODELLI OTTIMALI
AGENT_LLM_MAPPING = {
    # 🔥 AGENTI CRITICI - GPT-4o (1M token, massima intelligenza)
    "technology_masking": {
        "primary": "gpt-4o-2024-11-20",  # Capisce contesti tecnici complessi
        "fallback": "groq/llama-3.3-70b-versatile",
        "reason": "Technology masking richiede comprensione perfetta dei contesti tecnici"
    },
    
    "business_analyzer": {
        "primary": "gpt-4o-2024-11-20",  # Analisi strategiche complesse
        "fallback": "groq/llama-3.3-70b-versatile", 
        "reason": "Analisi business strategiche richiedono ragionamento superiore"
    },
    
    "conversation": {
        "primary": "gpt-4o-2024-11-20",  # Faccia dell'azienda, deve essere perfetto
        "fallback": "groq/llama-3.3-70b-versatile",
        "reason": "Conversazione principale, rappresenta l'azienda - qualità suprema"
    },
    
    # ⚡ AGENTI SEMPLICI - GPT-4o-mini (10M token, veloce ed economico)
    "classifier": {
        "primary": "gpt-4o-mini-2024-07-18",  # Classificazione semplice
        "fallback": "groq/llama-3.3-70b-versatile",
        "reason": "Classificazione semplice, 10M token per volume altissimo"
    },
    
    "security_filter": {
        "primary": "gpt-4o-mini-2024-07-18",  # Controlli binari veloci
        "fallback": "groq/llama-3.3-70b-versatile",
        "reason": "Controlli sicurezza veloci e semplici"
    },
    
    "coordinator": {
        "primary": "gpt-4o-mini-2024-07-18",  # Orchestrazione semplice
        "fallback": "groq/llama-3.3-70b-versatile",
        "reason": "Coordinamento semplice tra agenti"
    },
    
    # 📊 AGENTE RAGIONAMENTO - o1-mini (10M token, ragionamento matematico)
    "data_analyst": {
        "primary": "o1-mini-2024-09-12",  # Ragionamento e analisi dati
        "fallback": "groq/llama-3.3-70b-versatile",
        "reason": "Analisi dati complesse richiedono ragionamento matematico avanzato"
    }
}

# TOKEN LIMITS PER PROVIDER
TOKEN_LIMITS = {
    "gpt-4o-2024-11-20": {
        "monthly": 900000,   # 1M conservativo
        "daily": 30000,
        "hourly": 2000
    },
    "gpt-4o-mini-2024-07-18": {
        "monthly": 9000000,  # 10M conservativo  
        "daily": 300000,
        "hourly": 15000
    },
    "o1-mini-2024-09-12": {
        "monthly": 9000000,  # 10M conservativo
        "daily": 300000,
        "hourly": 15000
    },
    "groq/llama-3.3-70b-versatile": {
        "daily": 14000,
        "hourly": 1000
    }
}

def get_agent_llm(agent_type: str, task_complexity: str = "normal") -> dict:
    """
    Ottieni il modello ottimale per un agente
    
    Args:
        agent_type: Tipo di agente (es. 'classifier', 'conversation')
        task_complexity: 'simple', 'normal', 'complex'
    
    Returns:
        Dict con primary e fallback LLM
    """
    
    # Mappa agent names alle configurazioni
    agent_mapping = {
        "question_analyzer": "classifier",
        "milhena_conversation": "conversation", 
        "data_analyst": "data_analyst",
        "security_filter": "security_filter",
        "technology_masking": "technology_masking",
        "business_analyzer": "business_analyzer",
        "coordinator": "coordinator"
    }
    
    # Risolvi il nome agente
    config_key = agent_mapping.get(agent_type, agent_type)
    
    if config_key not in AGENT_LLM_MAPPING:
        # Fallback default per agenti sconosciuti
        return {
            "primary": "gpt-4o-mini-2024-07-18",
            "fallback": "groq/llama-3.3-70b-versatile",
            "reason": "Agente sconosciuto, uso GPT-4o-mini per sicurezza"
        }
    
    config = AGENT_LLM_MAPPING[config_key].copy()
    
    # Override per task complessi - usa sempre il migliore
    if task_complexity == "complex":
        if config["primary"].startswith("gpt-4o-mini"):
            config["primary"] = "gpt-4o-2024-11-20"
            config["reason"] += " (upgraded to GPT-4o for complex task)"
    
    return config

def get_llm_for_crewai(agent_type: str) -> str:
    """
    Formato LLM per CrewAI (semplificato)
    """
    config = get_agent_llm(agent_type)
    
    # Converti in formato CrewAI
    model = config["primary"]
    
    if model.startswith("gpt-"):
        return f"openai/{model}"
    elif model.startswith("o1-"):
        return f"openai/{model}" 
    else:
        return model  # già in formato provider/model

# Test del sistema
if __name__ == "__main__":
    print("🧪 TEST AGENT LLM ASSIGNMENT")
    print("=" * 50)
    
    test_agents = [
        "classifier", 
        "conversation",
        "data_analyst", 
        "technology_masking",
        "business_analyzer"
    ]
    
    for agent in test_agents:
        config = get_agent_llm(agent)
        crewai_llm = get_llm_for_crewai(agent)
        
        print(f"\n🤖 {agent.upper()}")
        print(f"   Primary: {config['primary']}")
        print(f"   Fallback: {config['fallback']}")
        print(f"   CrewAI: {crewai_llm}")
        print(f"   Reason: {config['reason']}")
    
    print("\n" + "=" * 50)
    print("✅ Sistema configurato correttamente!")
