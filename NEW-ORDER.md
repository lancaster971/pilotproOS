# NEW ORDER - Agent Versioning Architecture

**Date**: 2025-10-16
**Status**: PROPOSAL
**Problem**: 2960-line monolithic `graph.py` + impossible parallel development

---

## PROBLEMA

```
graph.py: 2960 righe (123KB) - UNMAINTAINABLE
├─ 39 metodi in MilhenaGraph
├─ 3 backup files (confusion)
└─ Sviluppo v4.0 = BREAKING v3.5 production
```

**Impossibile**:
- Sviluppare v4.0 senza rompere v3.5
- Testare versioni in parallelo
- Rollback rapido
- Team collaboration

---

## SOLUZIONE: Version-Based Agents

```
intelligence-engine/app/milhena/
├── agents/
│   ├── v3_5/                # PRODUCTION (current)
│   │   ├── classifier.py
│   │   ├── tool_executor.py
│   │   ├── responder.py
│   │   └── masking.py
│   │
│   ├── v4_0/                # DEVELOPMENT (new)
│   │   ├── classifier.py    # NEW logic
│   │   ├── tool_executor.py # NEW optimization
│   │   └── ...
│   │
│   └── v4_1/                # EXPERIMENTAL (future)
│
├── graph_v3_5.py           # Graph using agents.v3_5
├── graph_v4_0.py           # Graph using agents.v4_0
├── graph.py                # Active (imports current version)
│
└── utils/                  # SHARED (no versioning)
    ├── state.py            # Pydantic models
    ├── tools.py            # 18 business tools
    └── prompts_v3_5.py     # Prompt templates
```

---

## PRINCIPI

### 1. **Separation of Concerns**
- `agents/vX_Y/` = Agent logic (versioned)
- `utils/` = Shared components (stable)
- `graph_vX_Y.py` = Orchestration per version

### 2. **Parallel Development**
```bash
# Developer A: Production maintenance
vim agents/v3_5/classifier.py

# Developer B: New architecture
vim agents/v4_0/classifier.py

# NO CONFLICTS!
```

### 3. **Zero-Risk Rollback**
```python
# graph.py
from app.milhena.agents.v4_0 import classifier  # Current
# from app.milhena.agents.v3_5 import classifier  # Rollback (1 line change)
```

---

## VANTAGGI

| Feature | Before | After |
|---------|--------|-------|
| **File Size** | 2960 righe | ~400 righe/agent |
| **Parallel Dev** | ❌ Breaking | ✅ Isolated |
| **A/B Testing** | ❌ Impossible | ✅ Easy switch |
| **Rollback** | ❌ Git revert | ✅ 1 import change |
| **Team Work** | ❌ Conflicts | ✅ Parallel files |
| **Maintenance** | ❌ Monolith hell | ✅ Modular clean |

---

## WORKFLOW

### Development
```bash
# Create new version
mkdir agents/v4_0
cp -r agents/v3_5/* agents/v4_0/

# Develop in isolation
vim agents/v4_0/classifier.py

# Test new version
python -c "from agents.v4_0 import classifier; ..."
```

### Deployment
```python
# graph.py - Switch version
from app.milhena.agents.v4_0 import (  # ← Change this
    classifier, tool_executor, responder, masking
)
```

### Rollback
```python
# graph.py - Revert version
from app.milhena.agents.v3_5 import (  # ← One line fix
    classifier, tool_executor, responder, masking
)
```

---

## MIGRATION PLAN (3-4h)

### Phase 1: Extract Current (v3.5)
1. Create `agents/v3_5/`
2. Extract from `graph.py`:
   - `classifier.py` (supervisor_orchestrator + helpers)
   - `tool_executor.py` (execute_tools_direct + map_category_to_tools)
   - `responder.py` (generate_final_response)
   - `masking.py` (mask_response)

### Phase 2: Create Shared Utils
3. Create `utils/state.py` (SupervisorDecision, MilhenaState)
4. Create `utils/tools.py` (18 business tools)
5. Create `utils/prompts_v3_5.py` (CLASSIFIER_PROMPT)

### Phase 3: Slim graph.py
6. Update `graph.py` imports (use agents.v3_5)
7. Remove extracted code
8. Keep ONLY StateGraph orchestration
9. Target: ≤ 500 righe

### Phase 4: Test & Commit
10. Run `./stack start`
11. Run integration tests
12. Commit to `new-order` branch

---

## STANDARDS FOLLOWED

✅ **LangGraph Official Pattern**: utils/ structure
✅ **Production Template**: agents/ separation
✅ **Version Control**: v3_5/, v4_0/ isolation
✅ **Zero Downtime**: Switch imports, no rewrites

---

## REFERENCES

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/concepts/application_structure/
- **Production Template**: github.com/wassim249/fastapi-langgraph-agent-production-ready-template
- **Multi-Agent Patterns**: https://langchain-ai.github.io/langgraph/concepts/multi_agent/

---

**Next Step**: Execute migration → Test → Deploy v3.5 → Develop v4.0 in parallel
