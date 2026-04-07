"""
Orchestrator agent for routing requests to appropriate sub-agents.
"""

from google.adk.agents import Agent
from agents.ingest_agent import create_ingest_agent
from agents.query_agent import create_query_agent


def create_orchestrator(model, ingest_agent=None, query_agent=None):
    """
    Create orchestrator agent for routing requests.
    Optional ingest_agent / query_agent reuse the same instances (e.g. watcher + HTTP).
    """
    ingest_agent = ingest_agent or create_ingest_agent(model)
    query_agent = query_agent or create_query_agent(model)
    
    # Create orchestrator
    orchestrator = Agent(
        name="memory_orchestrator",
        model=model,
        description="Routes memory operations to specialist agents.",
        instruction=(
            "You are the Memory Orchestrator for an always-on memory system.\n"
            "Route requests to the right sub-agent:\n"
            "- New information -> ingest_agent\n"
            "- Questions -> query_agent\n"
            "After the sub-agent completes, give a brief summary."
        ),
        sub_agents=[ingest_agent, query_agent],
    )
    
    return orchestrator