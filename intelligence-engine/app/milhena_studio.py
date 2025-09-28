"""
Milhena LangGraph Studio Integration
This file exports the Milhena graph for LangGraph Studio
"""
import os
import sys

# Add app directory to path
sys.path.insert(0, '/app')

# Configure environment
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "milhena-v3-studio"
os.environ["LANGSMITH_TRACING"] = "true"

# Import and initialize Milhena
from app.milhena.graph import get_milhena_graph

# Get the compiled graph for Studio
graph = get_milhena_graph().compiled_graph

# Make it available for LangGraph Studio
__all__ = ['graph']

print("✅ Milhena graph loaded for LangGraph Studio")