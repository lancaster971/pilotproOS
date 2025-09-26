"""
Test Agent - Verifica completa del sistema
Tests:
1. Multi-LLM routing
2. Stack communication (PostgreSQL, Redis)
3. LangSmith tracing
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import time
import asyncio
from loguru import logger

# LangChain imports
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import SQLDatabase
import redis
import psycopg2

# Import our managers
from .llm_manager import get_llm_manager
from .performance_tracker import get_tracker

router = APIRouter(prefix="/api/test", tags=["test"])

class TestRequest(BaseModel):
    """Test request model"""
    message: str = "Test the system"
    model_id: Optional[str] = None
    test_stack: bool = True
    test_langsmith: bool = True

class TestResponse(BaseModel):
    """Test response with all info"""
    success: bool
    model_used: str
    response: str
    stack_status: Dict[str, Any]
    langsmith_status: Dict[str, Any]
    performance: Dict[str, Any]
    errors: list

# Simple tools for testing
def test_database() -> str:
    """Test PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres-dev"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "pilotpros_db"),
            user=os.getenv("DB_USER", "pilotpros_user"),
            password=os.getenv("DB_PASSWORD", "pilotpros_secure_pass_2025")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return f"✅ PostgreSQL connected: {version[:30]}..."
    except Exception as e:
        return f"❌ PostgreSQL error: {str(e)}"

def test_redis() -> str:
    """Test Redis connection"""
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis-dev"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True
        )
        r.ping()
        r.set("test_key", "test_value", ex=10)
        value = r.get("test_key")
        return f"✅ Redis connected: stored and retrieved '{value}'"
    except Exception as e:
        return f"❌ Redis error: {str(e)}"

def test_n8n() -> str:
    """Test n8n connection"""
    try:
        import httpx
        n8n_url = os.getenv("N8N_URL", "http://automation-engine-dev:5678")
        with httpx.Client() as client:
            response = client.get(f"{n8n_url}/healthz", timeout=2)
            if response.status_code == 200:
                return f"✅ n8n connected at {n8n_url}"
            else:
                return f"⚠️ n8n returned status {response.status_code}"
    except Exception as e:
        return f"❌ n8n error: {str(e)}"

def check_langsmith() -> str:
    """Check if LangSmith is configured"""
    try:
        tracing = os.getenv("LANGCHAIN_TRACING_V2", "false")
        api_key = os.getenv("LANGCHAIN_API_KEY", "")
        project = os.getenv("LANGCHAIN_PROJECT", "")

        if tracing.lower() == "true" and api_key:
            return f"✅ LangSmith ACTIVE - Project: {project}"
        else:
            return "⚠️ LangSmith NOT configured (missing API key or disabled)"
    except Exception as e:
        return f"❌ LangSmith check error: {str(e)}"

@router.post("/agent", response_model=TestResponse)
async def test_agent_endpoint(request: TestRequest):
    """
    Complete system test with a simple agent
    Tests: LLM, Tools, Stack, LangSmith
    """
    start_time = time.time()
    errors = []
    stack_status = {}
    langsmith_status = {}

    try:
        # 1. Get LLM
        manager = get_llm_manager()
        llm = manager.get_model(request.model_id)

        if not llm:
            # Try fallback
            fallback = manager.get_fallback_chain()
            if fallback:
                llm = fallback[0]
                model_id = manager.config.get('default_model', 'unknown')
            else:
                raise HTTPException(status_code=404, detail="No LLM models available")
        else:
            model_id = request.model_id or manager.config.get('default_model', 'unknown')

        logger.info(f"🤖 Using model: {model_id}")

        # 2. Create tools
        tools = []

        if request.test_stack:
            tools.extend([
                Tool(
                    name="test_database",
                    func=test_database,
                    description="Test PostgreSQL database connection"
                ),
                Tool(
                    name="test_redis",
                    func=test_redis,
                    description="Test Redis cache connection"
                ),
                Tool(
                    name="test_n8n",
                    func=test_n8n,
                    description="Test n8n automation engine connection"
                )
            ])

        if request.test_langsmith:
            tools.append(
                Tool(
                    name="check_langsmith",
                    func=check_langsmith,
                    description="Check LangSmith tracing configuration"
                )
            )

        # 3. Create agent prompt
        template = """You are a system test agent. Your job is to test all components.

Available tools:
{tools}

Tool Names: {tool_names}

Use this format:
Question: the input question
Thought: think about what to test
Action: the action to take (must be one of {tool_names})
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: summary of all test results

Question: {input}
{agent_scratchpad}"""

        prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
            template=template
        )

        # 4. Create agent
        agent = create_react_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )

        # 5. Create executor with memory
        memory = ConversationBufferMemory(memory_key="chat_history")

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )

        # 6. Run agent
        logger.info("🚀 Running test agent...")
        result = agent_executor.invoke({
            "input": f"{request.message}. Test all available components and report status."
        })

        # 7. Collect results
        response_text = result.get("output", "No output")

        # Parse stack status from response
        if request.test_stack:
            stack_status = {
                "postgresql": "✅" if "PostgreSQL connected" in response_text else "❌",
                "redis": "✅" if "Redis connected" in response_text else "❌",
                "n8n": "✅" if "n8n connected" in response_text else "⚠️"
            }

        # Check LangSmith
        if request.test_langsmith:
            langsmith_check = check_langsmith()
            langsmith_status = {
                "enabled": "✅" if "ACTIVE" in langsmith_check else "❌",
                "details": langsmith_check
            }

        # Calculate performance
        elapsed = (time.time() - start_time) * 1000

        # Track in performance tracker
        tracker = get_tracker()
        provider = manager.config['models'].get(model_id, {}).get('provider', 'unknown')
        tracker.track_call(
            model_id=model_id,
            provider=provider,
            start_time=start_time,
            input_tokens=len(request.message.split()) * 3,
            output_tokens=len(response_text.split()) * 3,
            success=True
        )

        return TestResponse(
            success=True,
            model_used=model_id,
            response=response_text,
            stack_status=stack_status,
            langsmith_status=langsmith_status,
            performance={
                "response_time_ms": round(elapsed, 2),
                "iterations": result.get("iterations", 0)
            },
            errors=errors
        )

    except Exception as e:
        logger.error(f"❌ Test agent error: {str(e)}")
        errors.append(str(e))

        return TestResponse(
            success=False,
            model_used="none",
            response=f"Test failed: {str(e)}",
            stack_status=stack_status,
            langsmith_status=langsmith_status,
            performance={"response_time_ms": 0},
            errors=errors
        )

@router.get("/quick")
async def quick_test():
    """
    Quick test - just check if everything is reachable
    """
    results = {
        "llm": "❌",
        "database": "❌",
        "redis": "❌",
        "n8n": "❌",
        "langsmith": "❌"
    }

    # Test LLM
    try:
        manager = get_llm_manager()
        if manager.get_fallback_chain():
            results["llm"] = "✅"
    except:
        pass

    # Test Stack
    results["database"] = "✅" if "connected" in test_database() else "❌"
    results["redis"] = "✅" if "connected" in test_redis() else "❌"
    results["n8n"] = "✅" if "connected" in test_n8n() else "⚠️"

    # Test LangSmith
    results["langsmith"] = "✅" if "ACTIVE" in check_langsmith() else "⚠️"

    # Overall status
    all_ok = all(v == "✅" for v in results.values())

    return {
        "status": "healthy" if all_ok else "degraded",
        "components": results,
        "message": "All systems operational! 🚀" if all_ok else "Some components need attention"
    }