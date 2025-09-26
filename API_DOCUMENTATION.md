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

### 7. System Statistics

**GET** `/api/stats`

Get system usage statistics.

**Response:**
```json
{
  "system": "intelligence-engine",
  "framework": "langchain",
  "active_sessions": 5,
  "cache_hits": 150,
  "vector_documents": 0,
  "models_available": ["gpt-4o", "gpt-4o-mini", "claude-3"],
  "tools_available": ["business_data", "workflows", "metrics", "rag"],
  "uptime": "2025-09-26T20:00:00.000Z"
}
```

---

## 🛠️ Available Tools

The ReAct agent has access to these database tools:

### 1. **get_database_schema_tool**
Returns PostgreSQL database schema information.

### 2. **query_users_tool**
Query user data with filters:
- Active users count
- User search by email
- Recent registrations

### 3. **query_sessions_tool**
Get active session information:
- Active sessions count
- Session details by user
- Session analytics

### 4. **query_business_data_tool**
Access business metrics and analytics:
- Performance metrics
- Business KPIs
- Workflow statistics

### 5. **query_system_status_tool**
Check system health:
- Service status
- Database health
- Performance metrics

### 6. **execute_sql_query_tool**
Execute custom SQL queries (SELECT only):
- Safe query execution
- Result formatting
- Query validation

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