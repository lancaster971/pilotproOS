# Contributing to PilotProOS

Thank you for your interest in contributing to PilotProOS! This guide will help you understand our development workflow, coding standards, and best practices.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Core Rules](#core-rules)
- [Git Workflow](#git-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Architecture Guidelines](#architecture-guidelines)
- [Debugging](#debugging)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

---

## Quick Start

### Prerequisites

- Docker Desktop (version 4.0+)
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for Intelligence Engine development)
- Git 2.30+
- VS Code (recommended) with extensions:
  - Docker
  - Python
  - Vue Language Features (Volar)
  - ESLint
  - Prettier

### Development Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/PilotProOS.git
cd PilotProOS

# 2. Start the stack
./stack-safe.sh start

# 3. Verify all services are running
./stack-safe.sh status

# 4. Access the platform
# Frontend: http://localhost:3000
# Backend: http://localhost:3001
# Intelligence: http://localhost:8000
# n8n: http://localhost:5678
```

### First Contribution Checklist

- [ ] Read this CONTRIBUTING.md completely
- [ ] Review [CLAUDE.md](../CLAUDE.md) for project context
- [ ] Check [TODO-URGENTE.md](../TODO-URGENTE.md) for current priorities
- [ ] Set up development environment
- [ ] Run all services successfully
- [ ] Make a test change in a feature branch
- [ ] Run tests and linting
- [ ] Submit a small PR for review

---

## Core Rules

### 1. Docker Isolation Policy

**EVERYTHING runs in Docker** except:
- VS Code (host IDE)
- Browser (testing)
- Git (version control)
- Docker Desktop (container management)

**Named volumes ONLY**:
```yaml
# ✅ CORRECT
volumes:
  postgres_data:/var/lib/postgresql/data
  redis_data:/data

# ❌ INCORRECT
volumes:
  - ./data:/var/lib/postgresql/data  # NO host-mounted runtime data
```

**Exception**: Development code can be mounted for hot-reload (frontend/backend source code).

### 2. Business Abstraction Layer

Frontend **NEVER exposes technical terms**:

| Technical Term | Business Term (USE THIS) |
|----------------|--------------------------|
| workflow | Business Process |
| execution | Process Run |
| node | Process Step |
| n8n | Process Automation |
| error | Issue / Problem |
| LLM | AI Assistant |
| checkpointer | Conversation Memory |

**Why?** Non-technical users understand "Business Process" but not "n8n workflow".

**Example**:
```vue
<!-- ❌ BAD -->
<h2>Workflow Execution Results</h2>
<p>The workflow has 15 nodes</p>

<!-- ✅ GOOD -->
<h2>Business Process Results</h2>
<p>This process has 15 steps</p>
```

### 3. Zero Custom Code

Before writing custom code:

1. **Search libraries FIRST** (npm, pip, Docker Hub)
2. **Evaluate**:
   - GitHub stars (>1000 preferred)
   - Maintenance activity (last commit <6 months)
   - TypeScript support (if applicable)
   - Documentation quality
3. **Use library OR document** why custom implementation is necessary

**Example Decision**:
```
Task: Implement cron job scheduling
✅ CORRECT: Use node-cron (v3.0.3, 3.5k stars, active)
❌ INCORRECT: Write custom cron parser
```

If custom code is necessary, document the decision in:
- Code comments (why no library exists)
- Commit message
- PR description

---

## Git Workflow

### Branch Strategy

```
main (production)
├── test (staging/testing)
├── feature/auto-learning-ui (new features)
├── fix/redis-connection-timeout (bug fixes)
└── docs/api-reference-update (documentation)
```

### Branch Naming

- `feature/` - New features (e.g., `feature/learning-dashboard`)
- `fix/` - Bug fixes (e.g., `fix/authentication-timeout`)
- `docs/` - Documentation only (e.g., `docs/contributing-guide`)
- `refactor/` - Code refactoring (e.g., `refactor/consolidate-tools`)
- `test/` - Test additions (e.g., `test/hot-reload-scenarios`)

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature change)
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:

```bash
# ✅ GOOD
feat(intelligence): Add hot-reload pattern system via Redis PubSub

Implements zero-downtime pattern reloading with 2.74ms latency.
- PatternReloader class with async Redis subscriber
- Admin endpoint POST /api/milhena/patterns/reload
- Auto-reload trigger on pattern learning

Closes #142

# ✅ GOOD
fix(auth): Use API_BASE_URL for authentication endpoints

Fixes authentication failing in production due to hardcoded localhost.

Resolves #156

# ❌ BAD
update stuff

# ❌ BAD
fixed bug
```

### Pull Request Workflow

1. **Create feature branch** from `test`:
   ```bash
   git checkout test
   git pull origin test
   git checkout -b feature/my-new-feature
   ```

2. **Make changes** with frequent commits:
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

3. **Keep branch updated**:
   ```bash
   git fetch origin test
   git rebase origin/test
   ```

4. **Push to remote**:
   ```bash
   git push origin feature/my-new-feature
   ```

5. **Create Pull Request** to `test` branch (NOT main)

6. **Address review comments** and push updates

7. **Merge** after approval (squash merge preferred)

---

## Testing

### Test Strategy

**Priority**: Backend > Intelligence Engine > Frontend

#### Backend Tests (Express API)

```bash
# Run all tests
cd backend
npm test

# Run specific test file
npm test -- routes/milhena.test.js

# Run with coverage
npm run test:coverage
```

#### Intelligence Engine Tests (FastAPI + LangGraph)

```bash
# Run pytest
cd intelligence-engine
pytest app/tests/

# Run specific test
pytest app/tests/test_hot_reload.py

# Run with coverage
pytest --cov=app app/tests/
```

#### Frontend Tests (Vue 3 + Vitest)

```bash
# Run Vitest
cd frontend
npm test

# Run specific component test
npm test -- ChatWidget.test.ts

# Run with UI
npm run test:ui
```

### Manual Testing

#### Intelligence Engine

```bash
# Test main chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "quali workflow abbiamo?", "session_id": "test-123"}'

# Test hot-reload
curl -X POST http://localhost:3001/api/milhena/patterns/reload \
  -H "Content-Type: application/json" \
  -d '{}'

# Check Redis checkpoints
docker exec pilotpros-redis-dev redis-cli KEYS "*checkpoint*" | wc -l

# Test auto-learning pattern
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "ci sono problemi oggi?", "session_id": "test-learning"}'
```

#### Frontend

1. Open http://localhost:3000
2. Login (tiziano@gmail.com / Hamlet@108)
3. Test Chat Widget:
   - Send query: "quanti workflow attivi abbiamo?"
   - Verify business terminology (NOT "workflow", but "Business Process")
   - Test follow-up: "spiegami il primo"
4. Test RAG Manager:
   - Upload PDF document
   - Search uploaded content
   - Verify semantic results

---

## Code Style

### TypeScript/JavaScript (Frontend + Backend)

**Linting**: ESLint + Prettier

```bash
# Run ESLint
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Format with Prettier
npm run format
```

**Style Guide**:

```typescript
// ✅ GOOD: Clear variable names
const autoLearnedPatterns = await loadPatterns();
const isHighConfidence = classification.confidence > 0.9;

// ❌ BAD: Unclear names
const data = await load();
const flag = c.conf > 0.9;

// ✅ GOOD: Async/await
async function reloadPatterns(): Promise<void> {
  const patterns = await db.query('SELECT * FROM patterns');
  return processPatterns(patterns);
}

// ❌ BAD: Promise chains
function reloadPatterns() {
  return db.query('SELECT * FROM patterns')
    .then(patterns => processPatterns(patterns));
}

// ✅ GOOD: TypeScript types
interface Pattern {
  id: number;
  normalized: string;
  category: string;
  confidence: number;
}

// ❌ BAD: No types
const pattern = { id: 1, norm: "test", cat: "METRIC" };
```

### Python (Intelligence Engine)

**Linting**: Black + isort + Flake8

```bash
# Format with Black
black app/

# Sort imports
isort app/

# Check style
flake8 app/
```

**Style Guide**:

```python
# ✅ GOOD: Type hints
async def reload_patterns(self) -> None:
    patterns: List[Dict[str, Any]] = await self.db.fetch(
        "SELECT * FROM patterns"
    )
    self._process_patterns(patterns)

# ❌ BAD: No type hints
async def reload_patterns(self):
    patterns = await self.db.fetch("SELECT * FROM patterns")
    self._process_patterns(patterns)

# ✅ GOOD: Descriptive names
auto_learned_pattern_count = len(self.learned_patterns)
is_high_confidence = classification["confidence"] > 0.9

# ❌ BAD: Unclear names
cnt = len(self.patterns)
flag = c["conf"] > 0.9

# ✅ GOOD: Async context managers
async with self.db_pool.acquire() as conn:
    result = await conn.fetchrow("SELECT * FROM users")

# ❌ BAD: Manual connection management
conn = await self.db_pool.acquire()
result = await conn.fetchrow("SELECT * FROM users")
await self.db_pool.release(conn)
```

### Vue 3 (Frontend)

**Style Guide**:

```vue
<!-- ✅ GOOD: Composition API with TypeScript -->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useLearningStore } from '@/stores/learning-store'

interface Message {
  id: string
  text: string
  type: 'user' | 'milhena'
}

const messages = ref<Message[]>([])
const learningStore = useLearningStore()

const hasMessages = computed(() => messages.value.length > 0)

onMounted(async () => {
  await learningStore.fetchMetrics()
})
</script>

<!-- ❌ BAD: Options API without types -->
<script>
export default {
  data() {
    return {
      messages: []
    }
  },
  computed: {
    hasMessages() {
      return this.messages.length > 0
    }
  }
}
</script>
```

---

## Architecture Guidelines

### Intelligence Engine (Milhena v3.1)

**4-Agent Pipeline**:

```
[CLASSIFIER] → [REACT] → [RESPONSE] → [MASKING]
```

**Rules**:
1. **Fast-path FIRST**: Check hardcoded patterns → auto-learned patterns → LLM
2. **Auto-learning**: Save patterns with confidence >0.9
3. **Tool consolidation**: Use smart multi-tools when possible
4. **Business masking**: ALWAYS mask technical terms in responses

**Example**:

```python
# ✅ GOOD: Fast-path → Auto-learned → LLM
def _instant_classify(self, query: str) -> Optional[Dict]:
    # 1. Hardcoded patterns (highest priority)
    if "quanti" in query.lower():
        return {"category": "SIMPLE_METRIC", "confidence": 1.0}

    # 2. Auto-learned patterns (second priority)
    normalized = self._normalize_query(query)
    if normalized in self.learned_patterns:
        return self.learned_patterns[normalized]

    # 3. LLM classification (fallback)
    return None

# ❌ BAD: Always call LLM (expensive!)
async def classify(self, query: str) -> Dict:
    return await self.llm.ainvoke(CLASSIFIER_PROMPT.format(query=query))
```

### Backend (Express API)

**Rules**:
1. **Business translator**: Convert technical terms before sending to frontend
2. **Proxy pattern**: Backend proxies Intelligence Engine (no direct frontend → Intelligence)
3. **JWT auth**: All protected routes use JWT HttpOnly cookies

**Example**:

```javascript
// ✅ GOOD: Business translation
app.get('/api/business-processes', async (req, res) => {
  const workflows = await n8nApi.getWorkflows(); // Technical call

  // Translate to business terms
  const processes = workflows.map(wf => ({
    id: wf.id,
    name: wf.name,
    status: wf.active ? 'Active' : 'Inactive',
    steps: wf.nodes.length, // "steps" not "nodes"
    lastRun: wf.lastRun
  }));

  res.json({ processes }); // "processes" not "workflows"
});

// ❌ BAD: Expose technical terms
app.get('/api/workflows', async (req, res) => {
  const workflows = await n8nApi.getWorkflows();
  res.json({ workflows }); // Technical term exposed!
});
```

### Frontend (Vue 3)

**Rules**:
1. **Composition API**: Use `<script setup>` with TypeScript
2. **Pinia stores**: State management (NOT Vuex)
3. **Business terminology**: NEVER show technical terms
4. **Dark theme**: All components support dark mode

**Example**:

```vue
<!-- ✅ GOOD: Business terminology -->
<template>
  <Card title="Business Processes">
    <DataTable :value="processes">
      <Column field="name" header="Process Name" />
      <Column field="steps" header="Steps" />
      <Column field="lastRun" header="Last Run" />
    </DataTable>
  </Card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProcessStore } from '@/stores/process-store'

const processStore = useProcessStore()
const processes = ref([])

onMounted(async () => {
  processes.value = await processStore.fetchProcesses()
})
</script>

<!-- ❌ BAD: Technical terms exposed -->
<template>
  <Card title="n8n Workflows">
    <DataTable :value="workflows">
      <Column field="name" header="Workflow Name" />
      <Column field="nodes" header="Nodes" />
    </DataTable>
  </Card>
</template>
```

---

## Debugging

### Intelligence Engine

**LangSmith Tracing**:
1. Open https://smith.langchain.com/
2. Navigate to "milhena-v3-production" project
3. Find your session_id trace
4. Inspect tool calls, LLM prompts, outputs

**Local Logs**:
```bash
# Follow logs
docker logs pilotpros-intelligence-engine-dev -f

# Filter by level
docker logs pilotpros-intelligence-engine-dev 2>&1 | grep ERROR

# Search for specific session
docker logs pilotpros-intelligence-engine-dev 2>&1 | grep "test-session-123"
```

**Interactive Debugging**:
```bash
# Enter container
docker exec -it pilotpros-intelligence-engine-dev bash

# Python REPL
python3
>>> from app.milhena.graph import MilhenaGraph
>>> graph = MilhenaGraph()
>>> # Test methods interactively
```

### Backend

**Express Logs**:
```bash
docker logs pilotpros-backend-dev -f
```

**Node.js Inspector**:
Add to `docker-compose.yml`:
```yaml
backend:
  command: node --inspect=0.0.0.0:9229 src/index.js
  ports:
    - "9229:9229"
```

Connect with Chrome DevTools: `chrome://inspect`

### Frontend

**Vue DevTools**:
1. Install [Vue DevTools](https://devtools.vuejs.org/) extension
2. Open http://localhost:3000
3. Open DevTools → Vue tab
4. Inspect components, Pinia stores, router

**Console Logs**:
```javascript
// ✅ GOOD: Structured logging
console.log('[ChatWidget] Sending message:', message);
console.error('[API] Failed to fetch:', error);

// ❌ BAD: Unclear logs
console.log('msg', m);
console.log('error!');
```

---

## Documentation

### When to Document

**ALWAYS document**:
- New features (add to CHANGELOG.md)
- API changes (update API_DOCUMENTATION.md)
- Architecture changes (update CLAUDE.md)
- Breaking changes (update CHANGELOG.md + migration guide)

**Document inline**:
- Complex algorithms (why, not what)
- Business logic decisions
- Workarounds for libraries/bugs

### Documentation Style

**README-style docs**:
- Quick Start (<5 min to first run)
- Clear examples with code
- Links to deep-dive docs

**API docs**:
- OpenAPI/Swagger format preferred
- Request/response examples
- Error codes and descriptions

**Code comments**:
```python
# ✅ GOOD: Explains WHY
# Use exponential backoff to avoid overwhelming Redis during reconnection storms.
# 5 attempts: 2s, 4s, 8s, 16s, 32s (max 62s total).
for attempt in range(5):
    await asyncio.sleep(2 ** attempt)

# ❌ BAD: Explains WHAT (obvious from code)
# Sleep for 2 to the power of attempt
await asyncio.sleep(2 ** attempt)
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guide
- [ ] All tests pass (`npm test` / `pytest`)
- [ ] Linting passes (`npm run lint` / `flake8`)
- [ ] Documentation updated (CHANGELOG.md, API docs)
- [ ] No console.log/print() statements (use logger)
- [ ] Business terminology used in frontend
- [ ] Tested manually in development environment

### PR Template

```markdown
## Description
Brief description of changes (1-2 sentences).

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Manual testing (describe scenarios)
- [ ] Automated tests added/updated
- [ ] Tested with REAL data (no mocks)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex logic
- [ ] Updated documentation
- [ ] No new warnings generated
- [ ] Added tests (if applicable)
- [ ] All tests pass
- [ ] Business abstraction layer respected (frontend)

## Screenshots (if applicable)
Add screenshots for UI changes.

## Related Issues
Closes #123
```

### Review Process

1. **Automated checks** run (linting, tests, build)
2. **Code review** by maintainer (1-2 business days)
3. **Address comments** and push updates
4. **Approval** + **Squash merge** to `test` branch
5. **Production deployment** (manual, after testing in `test`)

---

## Getting Help

- **Documentation**: [CLAUDE.md](../CLAUDE.md) - Complete project guide
- **API Reference**: [API_DOCUMENTATION.md](../API_DOCUMENTATION.md)
- **Architecture**: [docs/IMPLEMENTED/CURRENT_ARCHITECTURE.md](./IMPLEMENTED/CURRENT_ARCHITECTURE.md)
- **Issues**: Check [GitHub Issues](https://github.com/yourusername/PilotProOS/issues)
- **Slack/Discord**: (add your communication channel)

---

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Assume positive intent
- No discrimination, harassment, or trolling
- Help others learn and grow

---

**Thank you for contributing to PilotProOS!**

Maintained by PilotProOS Development Team
Last Updated: 2025-10-12
