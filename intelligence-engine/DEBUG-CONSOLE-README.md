# 🔍 Milhena Debug Console

**Universal LangGraph Agent Inspector** - Standalone debugging tool for LangGraph agents with AsyncRedisSaver

## ✨ Features

1. **List Active Sessions** - View all conversations stored in Redis
2. **Inspect Session State** - Deep dive into conversation state (messages, intent, decisions)
3. **Real-time Monitor** - Watch agent events live using Redis PubSub
4. **Node Performance Stats** - Analyze latency per node (requires custom metadata)

## 📋 Requirements

```bash
pip install rich redis
```

**Redis Configuration** (for real-time monitoring):
```bash
redis-cli CONFIG SET notify-keyspace-events KEA
```

## 🚀 Usage

### Start Debug Console
```bash
cd intelligence-engine
python debug-console.py
```

### Interactive Menu
```
╔════════════════════════════════════════╗
║  Milhena Debug Console - v1.0          ║
║  Universal LangGraph Agent Inspector   ║
╚════════════════════════════════════════╝

Available Commands:
  1. List Active Sessions
  2. Inspect Session State
  3. Real-time Monitor
  4. Node Performance Stats
  0. Exit

Select option:
```

## 📊 Examples

### 1. List Active Sessions
Shows all checkpoint keys in Redis:
```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Session ID          ┃ Thread ID  ┃ Messages ┃ Last Update         ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ test-v4-classifier  │ test-123   │        8 │ 2025-10-08 14:30:45 │
│ web-abc123-def456   │ web-uuid   │       12 │ 2025-10-08 15:42:12 │
└─────────────────────┴────────────┴──────────┴─────────────────────┘
```

### 2. Inspect Session State
Deep dive into a specific conversation:
```
Session: test-v4-classifier

Query: quanti errori oggi?
Intent: ERROR_ANALYSIS
Response: Oggi ci sono 126 errori totali distribuiti su 6 processi...

Messages (5):
  1. [human] quanti errori oggi?
  2. [ai] [1 tool calls]
  3. [tool] {"total_errors": 126, "workflows": [...]}
  4. [ai] Oggi ci sono 126 errori totali...
  5. [human] quali sono i più gravi?

Supervisor Decision:
  Action: ROUTE_TO_REACT
  Category: ERROR_ANALYSIS
  Confidence: 0.95
  Direct Response: False

Tools Used (2):
  - get_all_errors_summary_tool
  - get_error_details_tool

Show full state JSON? (y/n) [n]:
```

### 3. Real-time Monitor
Watch checkpoint updates live:
```
📡 Real-time Event Monitor
Monitoring Redis events... (Ctrl+C to stop)

✅ Subscribed to checkpoint events

[14:30:45] ✨ UPDATE Session: test-v4-classifier
[14:30:47] ✨ UPDATE Session: test-v4-classifier
[14:31:02] ✨ UPDATE Session: web-abc123-def456
[14:31:15] 🗑️  DELETE Session: old-session-xyz
```

### 4. Node Performance Stats
Analyze node execution times:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃ Node                      ┃ Calls ┃ Avg (ms) ┃ Min (ms)┃ Max (ms)┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│ [AI] Classifier           │    45 │   120.50 │   80.00 │  250.00 │
│ [AI] ReAct Call Model     │    38 │   450.30 │  200.00 │ 1200.00 │
│ [TOOL] Execute Tools      │    38 │  1500.20 │  300.00 │ 4500.00 │
│ [AI] Responder            │    38 │   350.80 │  150.00 │  800.00 │
│ [LIB] Mask Response       │    38 │    15.40 │   10.00 │   30.00 │
│ [DB] Record Feedback      │    38 │    45.20 │   20.00 │  100.00 │
└───────────────────────────┴───────┴──────────┴─────────┴─────────┘
```

## 🔧 Configuration

### Custom Redis URL
Edit `debug-console.py` line 27:
```python
REDIS_URL = "redis://your-redis-host:6379/0"
```

### Custom Checkpoint Prefix
Edit line 28:
```python
CHECKPOINT_PREFIX = "your_prefix:"
```

## 🌍 Universal Compatibility

**Works with ANY LangGraph project that uses AsyncRedisSaver:**
- ✅ Milhena v3.1 (this project)
- ✅ Any LangGraph 0.6.7+ agent
- ✅ Custom LangGraph implementations
- ✅ Multi-agent systems

**No project dependencies required** - standalone tool!

## 📝 Notes

### Real-time Monitor Requirements
Redis must have keyspace notifications enabled:
```bash
# Temporary (until restart)
redis-cli CONFIG SET notify-keyspace-events KEA

# Permanent (add to redis.conf)
notify-keyspace-events KEA
```

### Node Performance Stats
Requires custom metadata tracking in your LangGraph implementation. Add to your nodes:
```python
# In your node function
start_time = time.time()
# ... node logic ...
duration = (time.time() - start_time) * 1000

# Store in metadata
state["metadata"]["node_durations"][node_name] = duration
```

## 🐛 Troubleshooting

### "Redis connection failed"
- Check Redis is running: `redis-cli ping`
- Verify Redis URL in script
- Check firewall/network access

### "No active sessions found"
- Ensure AsyncRedisSaver is configured in your graph
- Verify checkpoint prefix matches
- Check Redis database number (default: 0)

### "No performance data found"
- Node stats require custom metadata tracking
- Use other features (list/inspect/monitor) for basic debugging

## 📚 Learn More

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **AsyncRedisSaver**: https://langchain-ai.github.io/langgraph/reference/checkpoints/
- **Rich Library**: https://rich.readthedocs.io/

## 📄 License

Same as parent project (PilotProOS)

---

**Created**: 2025-10-08
**Version**: 1.0
**Author**: PilotProOS Development Team
