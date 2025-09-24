#!/bin/bash
# Script per rinominare tutti i riferimenti crew → agent_system

echo "🔄 Rinominando riferimenti CrewAI..."

# Files to update
FILES=(
    "worker.py"
    "crews/pilotpro_assistant_crew.py"
    "crews/simple_crew.py"
    "crews/smart_crew.py"
    "crews/business_analysis_crew.py"
    "crews/example_multi_model_crew.py"
    "crews/process_analysis_crew.py"
    "tools/simple_tool.py"
    "tools/business_tools.py"
    "tools/database_tools.py"
    "tools/backend_api_tools.py"
    "config/settings.py"
    "example_usage.py"
    "cli_demo.py"
    "api/routes.py"
    "agent_engine.py"
    "n8n_integration.py"
    "services/agent_orchestrator.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "📝 Processing $file..."

        # Backup original
        cp "$file" "${file}.backup"

        # Replace crew references (but not imports)
        sed -i '' \
            -e 's/from crews\./from agents\./g' \
            -e 's/SimpleAssistantCrew/SimpleAssistantAgents/g' \
            -e 's/BusinessAnalysisCrew/BusinessAnalysisAgents/g' \
            -e 's/PilotProAssistantCrew/PilotProAssistantAgents/g' \
            -e 's/ProcessAnalysisCrew/ProcessAnalysisAgents/g' \
            -e 's/SmartCrew/SmartAgents/g' \
            -e 's/my_crew/my_agent_system/g' \
            -e 's/create_crew/create_agent_system/g' \
            -e 's/\.crew\(\)/\.agent_system()/g' \
            -e 's/crew\.kickoff/agent_system.execute/g' \
            -e 's/# Create crew$/# Create agent system/g' \
            -e 's/# Create single-agent crew$/# Create single-agent system/g' \
            -e 's/"crew"/"agent_system"/g' \
            -e 's/Analysis crew/Analysis agents/g' \
            -e 's/Report crew/Report agents/g' \
            -e 's/multi-agent crew/multi-agent system/g' \
            -e 's/Crew -/Agent System -/g' \
            -e 's/Assistant Crew/Assistant Agents/g' \
            -e 's/class \([A-Za-z]*\)Crew:/class \1Agents:/g' \
            "$file"

        # Check if file was modified
        if ! diff -q "$file" "${file}.backup" > /dev/null; then
            echo "✅ Updated $file"
            rm "${file}.backup"
        else
            echo "⏭️  No changes needed in $file"
            rm "${file}.backup"
        fi
    fi
done

# Rename crew files to agents
echo ""
echo "📁 Rinominando file crew → agents..."
if [ -d "crews" ]; then
    for file in crews/*_crew.py; do
        if [ -f "$file" ]; then
            newname="${file/_crew.py/_agents.py}"
            mv "$file" "$newname" 2>/dev/null && echo "✅ Renamed $(basename $file) → $(basename $newname)"
        fi
    done

    # Rename directory
    mv crews agents 2>/dev/null && echo "✅ Directory 'crews' → 'agents'"
fi

echo ""
echo "🎯 Mascheramento completato!"
echo "ℹ️  Gli import 'from crewai' sono stati mantenuti intatti per compatibilità"