# 📝 GUIDA RINOMINAZIONE - Rimuovere riferimenti CrewAI

## 🎯 REGOLE SEMPLICI

### ✅ RINOMINA QUESTI TERMINI:

| DA | A |
|----|---|
| `crew` / `Crew` | `agent_system` / `AgentSystem` |
| `CrewAI` | `Agent Engine` |
| `crewai` (import) | resta `crewai` (è ok negli import) |
| `my_crew` | `my_agent_system` |
| `create_crew()` | `create_agent_system()` |
| `BusinessAnalysisCrew` | `BusinessAnalysisAgents` |
| `crew.kickoff()` | `agent_system.execute()` |

## 📁 FILE DA AGGIORNARE:

### 1. Rinomina i file:
```bash
# DA                              # A
crews/business_analysis_crew.py → crews/business_analysis_agents.py
crews/simple_crew.py           → crews/simple_agents.py
crews/smart_crew.py            → crews/smart_agents.py
crews/example_multi_model_crew.py → crews/example_multi_model_agents.py
```

### 2. Aggiorna le classi:
```python
# PRIMA
class BusinessAnalysisCrew:
    def create_crew(self):
        crew = Crew(...)
        return crew

# DOPO
class BusinessAnalysisAgents:
    def create_agent_system(self):
        agent_system = Crew(...)  # import ok, variabile rinominata
        return agent_system
```

### 3. Aggiorna i commenti:
```python
# PRIMA
"""CrewAI implementation for business analysis"""

# DOPO
"""Agent system implementation for business analysis"""
```

### 4. Aggiorna documentazione:
```markdown
# PRIMA
## CrewAI Integration
The system uses CrewAI for multi-agent orchestration

# DOPO
## Agent System Integration
The system uses multi-agent orchestration for AI tasks
```

## 🔧 SCRIPT AUTOMATICO RINOMINAZIONE

```bash
#!/bin/bash
# rename_references.sh

cd /Volumes/BK12/Dropbox/Dropbox/TIZIANO/AI/PilotProOS/pilotpros-agent-engine

# 1. Rinomina nei file Python
find . -name "*.py" -exec sed -i '' \
  -e 's/CrewAI/Agent Engine/g' \
  -e 's/crew\.kickoff/agent_system.execute/g' \
  -e 's/my_crew/my_agent_system/g' \
  -e 's/create_crew/create_agent_system/g' \
  -e 's/class \([A-Za-z]*\)Crew:/class \1Agents:/g' \
  {} \;

# 2. Rinomina nei Markdown
find . -name "*.md" -exec sed -i '' \
  -e 's/CrewAI/Agent Engine/g' \
  -e 's/crew system/agent system/g' \
  {} \;

# 3. Rinomina file
mv crews/business_analysis_crew.py crews/business_analysis_agents.py 2>/dev/null
mv crews/simple_crew.py crews/simple_agents.py 2>/dev/null
mv crews/smart_crew.py crews/smart_agents.py 2>/dev/null

echo "✅ Rinominazione completata!"
```

## ✅ COSA NON CAMBIARE:

1. **Import statement**: `from crewai import ...` resta così
2. **requirements.txt**: `crewai==0.193.2` resta così
3. **Funzioni interne**: `Crew()`, `Agent()`, `Task()` restano così

## 📋 ESEMPIO FINALE:

```python
# business_analysis_agents.py (rinominato da crew.py)
from crewai import Agent, Task, Crew  # import OK

class BusinessAnalysisAgents:  # Rinominato da BusinessAnalysisCrew
    """Sistema multi-agent per analisi business"""  # No "CrewAI"

    def create_agent_system(self):  # Rinominato da create_crew
        """Crea sistema di agent per analisi"""

        agents = [...]  # OK
        tasks = [...]   # OK

        # Variabile rinominata, ma usa ancora Crew internamente
        agent_system = Crew(
            agents=agents,
            tasks=tasks
        )

        return agent_system

    def execute_analysis(self, data):
        """Esegue analisi con sistema multi-agent"""
        agent_system = self.create_agent_system()
        result = agent_system.kickoff()  # OK internamente
        return {
            "system": "PilotPro Agent Engine",  # No "CrewAI"
            "result": result
        }
```

## 🎯 RISULTATO:

- ✅ Nessun riferimento visibile a "CrewAI" nell'interfaccia
- ✅ Documentazione parla di "Agent Engine" o "Agent System"
- ✅ Classi rinominate senza "Crew"
- ✅ Import e funzioni interne restano com'erano (non visibili all'utente)