# 📚 PilotProOS Intelligence Engine API Documentation

## 🚀 Overview

The Intelligence Engine is a LangChain-powered API service that provides intelligent conversational AI capabilities with direct database access and tool execution.

**Version**: 1.0.0
**Base URL**: `http://localhost:8000` (host) / `http://pilotpros-intelligence-engine-dev:8000` (Docker)

## 🔑 Authentication

Currently no authentication required for development. Production will use JWT tokens.

---

## 📍 Endpoints

### 1. Health Check

**GET** `/health`

Check service status and component health.

**Response:**
```json
{
  "status": "healthy",
  "service": "intelligence-engine",
  "version": "1.0.0",
  "components": {
    "langchain": "active",
    "redis": "connected",
    "postgres": "connected",
    "llm": "ready"
  },
  "timestamp": "2025-09-26T20:00:00.000Z"
}
```

---

### 2. Main Chat Endpoint

**POST** `/api/chat`

Primary chat interface with the ReAct agent.

**Request Body:**
```json
{
  "message": "Quanti utenti ci sono nel sistema?",
  "user_id": "guest",
  "context": {},
  "use_cache": true,
  "stream": false
}
```

**Response:**
```json
{
  "response": "Nel database ci sono attualmente 3 utenti, e tutti risultano attivi.",
  "status": "success",
  "metadata": {
    "model": "gpt-4o-mini",
    "tools_used": ["query_users_tool"],
    "processing_time_ms": 2150
  },
  "sources": ["query_users_tool"],
  "confidence": 0.95
}
```

---

### 3. Process Automation Integration Endpoint

**GET/POST** `/api/n8n/agent/customer-support`

Specialized endpoint for Process Automation workflow integration.

#### GET Method

**Query Parameters:**
- `message` (required): User message
- `customer_id` (optional): Customer identifier
- `session_id` (optional): Session ID for conversation continuity

**Example:**
```
GET /api/n8n/agent/customer-support?message=ciao&session_id=n8n-123
```

#### POST Method

**Request Body:**
```json
{
  "message": "Come posso aiutarti?",
  "customer_id": "customer-123",
  "session_id": "n8n-workflow-session"
}
```

**Response:**
```json
{
  "success": true,
  "agent_response": "Ciao! Come posso aiutarti oggi con PilotProOS?",
  "response_time": 1.5,
  "customer_id": "customer-123",
  "session_id": "n8n-workflow-session",
  "agent_type": "customer_support",
  "database_used": true,
  "timestamp": "2025-09-26T20:00:00.000Z"
}
```

---

### 4. Frontend Widget Webhook

**POST** `/webhook/from-frontend`

Webhook endpoint for Vue frontend widget integration.

**Request Body:**
```json
{
  "message": "Ho un problema con il login",
  "user_id": "widget-user-123"
}
```

**Response:**
```json
{
  "response": "Ti aiuterò a risolvere il problema di login. Puoi dirmi quale errore visualizzi?",
  "status": "success",
  "metadata": {
    "model": "react-agent",
    "tools_used": [],
    "processing_time_ms": 1200
  },
  "confidence": 0.95
}
```

---

### 5. Analysis Endpoint

**POST** `/api/analyze`

Advanced analysis with specialized LangChain chains.

**Request Body:**
```json
{
  "query": "Analyze user growth last 30 days",
  "data_source": "workflows",
  "time_range": "30d"
}
```

**Response:**
```json
{
  "analysis": "User growth analysis results...",
  "insights": ["Key insight 1", "Key insight 2"],
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "visualizations": [],
  "confidence": 0.92
}
```

---

### 6. WebSocket Streaming

**WebSocket** `/ws/chat`

Real-time streaming chat responses.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.send(JSON.stringify({
  message: "Explain the system architecture",
  user_id: "ws-user-123"
}));
```

**Stream Response:**
```json
{
  "type": "stream",
  "content": "The system architecture consists of..."
}
```

---

### 7. Learning System Feedback

**POST** `/api/milhena/feedback`

Submit user feedback (thumbs up/down) for learning system.

**Request Body:**
```json
{
  "session_id": "test-session-123",
  "message_id": "msg-456",
  "feedback_type": "positive",
  "correction_data": null
}
```

**Response:**
```json
{
  "status": "recorded",
  "message": "Feedback recorded successfully"
}
```

---

### 8. Learning Performance Metrics

**GET** `/api/milhena/performance`

Get learning system metrics and accuracy trends.

**Response:**
```json
{
  "total_queries": 15432,
  "accuracy_rate": 0.75,
  "improvement_trend": [0.65, 0.68, 0.72, 0.75],
  "top_patterns": [
    {
      "pattern": "quanti workflow",
      "category": "SIMPLE_METRIC",
      "accuracy": 0.95,
      "usage": 234
    }
  ],
  "failed_patterns": [],
  "auto_learned_count": 64,
  "cache_hit_rate": 0.35
}
```

---

### 9. Hot-Reload Pattern System

**POST** `/api/milhena/patterns/reload`

Manually trigger pattern reload (admin endpoint, development only).

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "success": true,
  "message": "Pattern reload triggered successfully",
  "subscribers": 1,
  "timestamp": "2025-10-11T20:00:00.000Z"
}
```

**Note**: This endpoint triggers Redis PubSub message to reload patterns in Intelligence Engine without container restart.

---

### 10. RAG Document Upload

**POST** `/api/rag/documents`

Upload documents to RAG system for semantic search.

**Request (multipart/form-data):**
- `file`: Document file (PDF, DOCX, TXT, MD, HTML)
- `category`: Document category (optional, 1-8)

**Response:**
```json
{
  "success": true,
  "document_id": "doc-789",
  "filename": "user-guide.pdf",
  "category": "documentation",
  "chunks": 45,
  "timestamp": "2025-10-11T20:00:00.000Z"
}
```

---

### 11. RAG Semantic Search

**POST** `/api/rag/search`

Search documents using semantic similarity.

**Request Body:**
```json
{
  "query": "how to configure workflows",
  "top_k": 5,
  "category": "documentation"
}
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "doc-789",
      "chunk_text": "To configure workflows, navigate to...",
      "similarity": 0.92,
      "metadata": {
        "filename": "user-guide.pdf",
        "category": "documentation"
      }
    }
  ],
  "query_time_ms": 45
}
```

---

### 12. RAG Statistics

**GET** `/api/rag/stats`

Get RAG system statistics.

**Response:**
```json
{
  "total_documents": 127,
  "total_chunks": 3456,
  "categories": {
    "documentation": 45,
    "guides": 32,
    "api_reference": 28,
    "tutorials": 22
  },
  "embeddings_model": "nomic-embed-text-v1.5",
  "dimension": 768
}
```

---

### 13. RAG Delete Document

**DELETE** `/api/rag/documents/{id}`

Delete document from RAG system.

**Response:**
```json
{
  "success": true,
  "message": "Document deleted successfully",
  "document_id": "doc-789"
}
```

---

### 14. Graph Visualization

**GET** `/graph/visualize`

Generate PNG visualization of LangGraph architecture.

**Response:**
- Content-Type: `image/png`
- Size: 4700x2745px
- High-resolution graph diagram

---

### 15. Graph Mermaid Diagram

**GET** `/graph/mermaid`

Get Mermaid diagram code for LangGraph.

**Response:**
```json
{
  "mermaid": "graph TD\n  A[Start] --> B[Classifier]\n  B --> C[ReAct Agent]\n  ...",
  "format": "mermaid"
}
```

---

### 16. Prometheus Metrics

**GET** `/metrics`

Get Prometheus metrics for monitoring.

**Response (text/plain):**
```
# HELP milhena_queries_total Total number of queries processed
# TYPE milhena_queries_total counter
milhena_queries_total{status="success"} 15234.0

# HELP milhena_response_time_seconds Response time distribution
# TYPE milhena_response_time_seconds histogram
milhena_response_time_seconds_bucket{le="1.0"} 12000.0
milhena_response_time_seconds_bucket{le="2.0"} 14500.0
milhena_response_time_seconds_bucket{le="+Inf"} 15234.0

# HELP milhena_fast_path_hits_total Fast-path pattern matches
# TYPE milhena_fast_path_hits_total counter
milhena_fast_path_hits_total{type="hardcoded"} 4570.0
milhena_fast_path_hits_total{type="auto_learned"} 762.0
```

---

### 17. System Statistics

**GET** `/api/stats`

Get system usage statistics.

**Response:**
```json
{
  "system": "intelligence-engine",
  "framework": "langchain",
  "version": "3.3.1",
  "active_sessions": 5,
  "cache_hits": 150,
  "vector_documents": 127,
  "models_available": ["llama-3.3-70b-versatile", "gpt-4.1-nano-2025-04-14"],
  "tools_available": 18,
  "uptime_seconds": 345600,
  "redis_checkpoints": 1214,
  "auto_learned_patterns": 64
}
```

---

## 🛠️ Available Tools

The ReAct agent has access to **18 smart tools** organized in 3 categories:

### 3 Consolidated Multi-Tools

#### 1. **smart_analytics_query_tool**
9 analytics queries in 1:
- User count (active/total)
- Session statistics
- Workflow metrics
- Execution analytics
- Error rate analysis
- Performance trends
- Business KPIs
- System health
- Resource utilization

#### 2. **smart_workflow_query_tool**
3 workflow details in 1:
- Workflow list (all/active/inactive)
- Workflow details by ID
- Workflow status and metadata

#### 3. **smart_executions_query_tool**
4 execution tools in 1:
- Recent executions (last N runs)
- Executions by workflow ID
- Executions by status (success/failed/running)
- Execution details by ID

### 9 Specialized Tools

#### 4. **get_error_details_tool**
Workflow error analysis (auto-enriched with context):
- Error message and stack trace
- Workflow context (name, node)
- Timestamp and execution ID
- Related workflow status

#### 5. **get_all_errors_summary_tool**
Aggregated error statistics:
- Total error count
- Errors by workflow
- Errors by node
- Recent error trends

#### 6. **get_node_execution_details_tool**
Node-level granular execution data:
- Node execution status
- Input/output data
- Execution time
- Node-specific errors

#### 7. **get_chatone_email_details_tool**
Email bot conversation history:
- Email threads
- Conversation context
- Bot responses
- Customer interactions

#### 8. **get_raw_modal_data_tool**
Node-by-node execution timeline:
- Sequential execution flow
- Node input/output
- Timing information
- State transitions

#### 9. **get_live_events_tool**
Real-time event stream monitoring:
- Active workflow events
- System notifications
- Real-time status updates

#### 10. **get_workflows_tool**
Workflow list with metadata:
- Workflow names and IDs
- Active/inactive status
- Creation dates
- Trigger types

#### 11. **get_workflow_cards_tool**
Card-style workflow overview:
- Visual workflow summary
- Execution statistics
- Success/failure rates
- Last run information

#### 12. **execute_workflow_tool** / **toggle_workflow_tool**
Workflow actions:
- Execute workflow by ID
- Enable/disable workflow
- Start/stop workflow runs

### Extra Tools

#### 13. **search_knowledge_base_tool**
RAG semantic search:
- ChromaDB vector search
- NOMIC embeddings (768-dim)
- Top-k similar documents
- Category filtering

#### 14. **get_full_database_dump**
Complete system state export:
- Full database snapshot
- All tables and schemas
- System configuration
- Metadata export

---

## 🔄 Process Automation Integration

**Note**: Internal endpoint paths reference technical implementation details (`/api/n8n/`) but this is backend infrastructure. Frontend and business users interact only through business terminology.

### HTTP Request Integration Setup

**Method**: POST or GET
**URL**: `http://pilotpros-intelligence-engine-dev:8000/api/n8n/agent/customer-support`

**For POST Method:**
```json
{
  "message": "{{ $json.chatInput }}",
  "session_id": "{{ $json.sessionId }}",
  "customer_id": "{{ $json.customerId }}"
}
```

**For GET Method:**
Query Parameters:
- `message`: `{{ $json.chatInput }}`
- `session_id`: `{{ $json.sessionId || "default" }}`

---

## 🎯 Response Models

### ChatResponse
```typescript
interface ChatResponse {
  response: string;
  status: "success" | "error";
  metadata?: {
    model: string;
    tools_used: string[];
    processing_time_ms: number;
  };
  sources?: string[];
  confidence?: number;
}
```

### N8nResponse
```typescript
interface N8nResponse {
  success: boolean;
  agent_response?: string;
  response_time?: number;
  customer_id?: string;
  session_id?: string;
  agent_type?: string;
  database_used?: boolean;
  timestamp?: string;
  error?: string;
}
```

---

## 📝 Example Requests

### Simple Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ciao, come stai?"}'
```

### n8n Integration
```bash
curl -X GET "http://localhost:8000/api/n8n/agent/customer-support?message=Quanti%20utenti%20attivi?"
```

### Database Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Mostrami gli ultimi 5 utenti registrati"}'
```

---

## ⚙️ Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for GPT models
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_HOST`: Redis cache host
- `DEFAULT_LLM_MODEL`: Default language model (gpt-4o-mini)

### Docker Network
- Service name: `pilotpros-intelligence-engine-dev`
- Port: 8000 (API), 8501 (Dashboard)
- Network: `pilotpros-development`

---

## 🚨 Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Error description",
  "status": "error",
  "timestamp": "2025-09-26T20:00:00.000Z"
}
```

Common error codes:
- `400`: Bad Request - Invalid parameters
- `404`: Not Found - Resource not available
- `500`: Internal Server Error - Server issue
- `503`: Service Unavailable - Dependencies offline

---

## 📊 Performance

- Average response time: 2-3 seconds for simple queries
- Complex database queries: 5-8 seconds
- Streaming available for long responses
- Session memory: Last 10 exchanges retained
- Max recursion: 11 (5 tool calls max)

---

## 🔒 Security Notes

**Development Mode:**
- No authentication required
- All queries are read-only (SELECT only)
- SQL injection protection enabled
- Rate limiting not enforced

**Production Recommendations:**
- Enable JWT authentication
- Implement rate limiting
- Use HTTPS only
- Sanitize all inputs
- Log all queries for audit

---

## 📚 Additional Resources

- LangChain Documentation: https://python.langchain.com/
- LangGraph Documentation: https://github.com/langchain-ai/langgraph
- n8n Integration Guide: See INTEGRATION_GUIDE.md
- Project Documentation: See CLAUDE.md

---

## 🆘 Support

For issues or questions:
- Check logs: `docker logs pilotpros-intelligence-engine-dev`
- Test endpoint: `curl http://localhost:8000/health`
- Debug mode: Set `DEBUG=true` in environment

---

*Last Updated: September 26, 2025*