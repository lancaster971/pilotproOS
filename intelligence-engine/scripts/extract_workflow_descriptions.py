#!/usr/bin/env python3
"""
Extract workflow descriptions from sticky notes and populate RAG knowledge base

This script:
1. Reads all workflows from PostgreSQL n8n.workflow_entity
2. Extracts sticky notes content from nodes JSON
3. Identifies "description" sticky notes (usually first or marked)
4. Populates RAG system (ChromaDB) with business-friendly descriptions

Usage:
    python3 extract_workflow_descriptions.py

Environment variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    INTELLIGENCE_ENGINE_URL (default: http://localhost:8000)
"""

import psycopg2
import json
import re
from typing import List, Dict, Optional
import os
import sys
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import RAG system
from app.rag import get_rag_system
from app.rag.maintainable_rag import DocumentMetadata

# Database connection
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "pilotpros_db"),
    "user": os.getenv("DB_USER", "pilotpros_user"),
    "password": os.getenv("DB_PASSWORD", "pilotpros_secure_pass_2025")
}


def extract_sticky_notes(nodes_json) -> List[Dict]:
    """
    Extract all sticky notes from workflow nodes JSON

    Args:
        nodes_json: JSON string or parsed list of workflow nodes

    Returns:
        List of sticky note dicts with content and metadata
    """
    try:
        # Handle both string and already-parsed list
        if isinstance(nodes_json, str):
            nodes = json.loads(nodes_json)
        else:
            nodes = nodes_json

        sticky_notes = []

        for node in nodes:
            # Check if this is a sticky note node
            if node.get("type") == "n8n-nodes-base.stickyNote":
                content = node.get("parameters", {}).get("content", "")

                # Skip empty or very short notes
                if len(content.strip()) < 20:
                    continue

                sticky_notes.append({
                    "content": content,
                    "name": node.get("name", ""),
                    "position": node.get("position", []),
                    "color": node.get("parameters", {}).get("color", 0)
                })

        return sticky_notes
    except json.JSONDecodeError as e:
        print(f"Error parsing nodes JSON: {e}")
        return []
    except Exception as e:
        print(f"Error extracting sticky notes: {e}")
        return []


def identify_description_note(sticky_notes: List[Dict]) -> Optional[str]:
    """
    Identify the main description sticky note

    Priority:
    1. Note with "DESCRIZIONE:" or "## " (markdown header) at start
    2. Note with "Try It Out!" (common n8n template header)
    3. Longest note (likely main description)
    4. First note

    Args:
        sticky_notes: List of sticky note dicts

    Returns:
        Description text or None
    """
    if not sticky_notes:
        return None

    # Priority 1: Explicit description markers
    for note in sticky_notes:
        content = note["content"].strip()
        if re.match(r"(DESCRIZIONE:|##\s)", content, re.IGNORECASE):
            # Clean markdown and return first paragraph
            return clean_description(content)

    # Priority 2: Try It Out (common template)
    for note in sticky_notes:
        content = note["content"].strip()
        if "Try It Out!" in content or "This workflow" in content:
            return clean_description(content)

    # Priority 3: Longest note (likely main description)
    if sticky_notes:
        longest = max(sticky_notes, key=lambda x: len(x["content"]))
        return clean_description(longest["content"])

    return None


def clean_description(text: str) -> str:
    """
    Clean description text for storage

    - Remove markdown headers
    - Remove excessive newlines
    - Limit to 500 characters
    - Clean special characters
    """
    # Remove markdown headers
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    # Remove markdown bold/italic
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    # Remove bullet points
    text = re.sub(r"^[•\-\*]\s+", "", text, flags=re.MULTILINE)

    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Take first paragraph (before double newline) or first 500 chars
    paragraphs = text.split("\n\n")
    description = paragraphs[0].strip()

    # Limit length
    if len(description) > 500:
        description = description[:497] + "..."

    return description


def extract_category_from_content(content: str, workflow_name: str) -> str:
    """
    Infer category from content and workflow name

    Categories:
    - AI/ML: AI, agent, langchain, chatbot
    - Integration: API, webhook, http
    - Analytics: metrics, dashboard, report
    - Backend: backend, server, database
    - Frontend: frontend, UI, form
    - Automation: automation, task, schedule
    """
    content_lower = (content + " " + workflow_name).lower()

    if any(word in content_lower for word in ["ai", "agent", "langchain", "chatbot", "llm", "gpt"]):
        return "AI/ML"
    elif any(word in content_lower for word in ["api", "webhook", "http", "request", "integration"]):
        return "Integration"
    elif any(word in content_lower for word in ["metrics", "dashboard", "report", "analytics", "insight"]):
        return "Analytics"
    elif any(word in content_lower for word in ["backend", "server", "database", "postgres"]):
        return "Backend"
    elif any(word in content_lower for word in ["frontend", "ui", "form", "user interface"]):
        return "Frontend"
    elif any(word in content_lower for word in ["automation", "task", "schedule", "cron"]):
        return "Automation"
    else:
        return "General"


def extract_all_workflows():
    """
    Extract descriptions from all workflows
    """
    print("🔍 Connecting to PostgreSQL...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Get all workflows (both active and inactive)
        cursor.execute("""
            SELECT id, name, nodes, active
            FROM n8n.workflow_entity
            ORDER BY name
        """)

        workflows = cursor.fetchall()
        print(f"📊 Found {len(workflows)} workflows\n")

        results = []

        for workflow_id, workflow_name, nodes_json, active in workflows:
            print(f"Processing: {workflow_name}")

            # Extract sticky notes
            sticky_notes = extract_sticky_notes(nodes_json)
            print(f"  Found {len(sticky_notes)} sticky notes")

            # Get main description
            description = identify_description_note(sticky_notes)

            if description:
                category = extract_category_from_content(description, workflow_name)

                results.append({
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_name,
                    "description": description,
                    "category": category,
                    "tags": "",  # Can be populated later
                    "sticky_notes_count": len(sticky_notes)
                })

                print(f"  ✅ Description: {description[:100]}...")
                print(f"  📁 Category: {category}\n")
            else:
                print(f"  ⚠️ No description found\n")
                results.append({
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_name,
                    "description": "No description available. Contact IT for details.",
                    "category": "General",
                    "tags": "",
                    "sticky_notes_count": 0
                })

        cursor.close()
        conn.close()

        print(f"\n✅ Extraction complete!")
        print(f"📊 Total workflows: {len(workflows)}")
        print(f"📝 With descriptions: {sum(1 for r in results if r['sticky_notes_count'] > 0)}")
        print(f"⚠️ Without descriptions: {sum(1 for r in results if r['sticky_notes_count'] == 0)}")

        return results

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


async def populate_rag_system_async(workflow_data: List[Dict]) -> int:
    """
    Populate RAG system with workflow descriptions (async)

    Args:
        workflow_data: List of workflow dictionaries with descriptions

    Returns:
        Number of documents successfully ingested
    """
    print("\n" + "=" * 60)
    print("📤 Populating RAG Knowledge Base")
    print("=" * 60)

    success_count = 0

    try:
        rag = get_rag_system()

        for workflow in workflow_data:
            # Create business-friendly content (NO technical terms!)
            content = f"""**Processo: {workflow['workflow_name']}**

**Categoria:** {workflow['category']}

**Descrizione:**
{workflow['description']}

**Note:** Per modifiche o problemi con questo processo, contatta il reparto IT.
"""

            # Prepare metadata
            metadata = DocumentMetadata(
                title=f"Processo: {workflow['workflow_name']}",
                source="workflow_extraction",
                category="workflow-description",
                tags=[workflow['category'].lower()],
                author="automated_extraction"
            )

            try:
                # Add to RAG system
                result = await rag.create_document(
                    content=content,
                    metadata=metadata,
                    auto_chunk=True
                )

                print(f"✅ {workflow['workflow_name']}")
                success_count += 1

            except Exception as e:
                print(f"❌ {workflow['workflow_name']} - Error: {e}")

    except Exception as e:
        print(f"❌ RAG System Error: {e}")

    print(f"\n📊 RAG Population Complete: {success_count}/{len(workflow_data)} documents ingested")
    return success_count


def populate_rag_system(workflow_data: List[Dict]) -> int:
    """Sync wrapper for async RAG population"""
    return asyncio.run(populate_rag_system_async(workflow_data))


if __name__ == "__main__":
    print("=" * 60)
    print("📋 Workflow Description Extractor → RAG System")
    print("=" * 60)
    print()

    results = extract_all_workflows()

    # Print summary table
    if results:
        print("\n" + "=" * 60)
        print("📊 EXTRACTION SUMMARY")
        print("=" * 60)

        for r in results:
            print(f"\n{r['workflow_name']}")
            print(f"  Category: {r['category']}")
            print(f"  Description: {r['description'][:80]}...")

        # Populate RAG
        populate_rag_system(results)

    else:
        print("⚠️ No workflows found to process")
