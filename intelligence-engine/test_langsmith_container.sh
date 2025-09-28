#!/bin/bash
# Test LangSmith nel container

echo "Testing LangSmith in container..."

# Verifica variabili
echo "LANGCHAIN_API_KEY: ${LANGCHAIN_API_KEY:0:20}...${LANGCHAIN_API_KEY: -10}"
echo "LANGCHAIN_TRACING_V2: $LANGCHAIN_TRACING_V2"
echo "LANGCHAIN_PROJECT: $LANGCHAIN_PROJECT"

# Test Python
python3 -c "
import os
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_PROJECT'] = 'milhena-container-test'

from langsmith import Client
client = Client()
print('✅ LangSmith Client created successfully')

from langsmith.run_trees import RunTree
run = RunTree(
    name='Container Test',
    run_type='chain',
    inputs={'test': 'container'},
    project_name='milhena-container-test'
)
run.end(outputs={'result': 'success'})
run.post()
print(f'✅ Trace created: https://smith.langchain.com/public/{run.id}')
"
