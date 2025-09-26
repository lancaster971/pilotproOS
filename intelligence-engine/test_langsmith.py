#!/usr/bin/env python3
"""Test LangSmith tracing"""

import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "pilotpros-intelligence"

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Create LLM (usa una API key mock per test)
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    api_key="sk-test-mock-key-for-tracing"  # Mock key solo per vedere trace
)

try:
    # Questa chiamata fallirà ma genererà una trace
    response = llm.invoke([HumanMessage(content="Hello LangSmith!")])
    print(f"Response: {response}")
except Exception as e:
    print(f"Expected error (but trace sent): {e}")

print("\n✅ Check LangSmith at: https://smith.langchain.com")
print("You should see a trace in your project 'pilotpros-intelligence'")