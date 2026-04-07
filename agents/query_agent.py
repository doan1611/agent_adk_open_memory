"""
Query agent for searching issue information.
"""

from google.adk.agents import Agent
from agents.prompts import FUNCTION_CALLING_INSTRUCTIONS
from tools.memory_tools import search_memory


def create_query_agent(model):
    """
    Create query agent for searching issue information.
    """
    query_agent = Agent(
        name="query_agent",
        model=model,
        description="Answers questions using stored memories.",
        instruction=(
            "You are a Memory Query Agent. When asked a question:\n"
            "1. Call search_memory to access the memory store\n"
            "2. Synthesize an answer based ONLY on stored memories\n"
            "3. Provide information about the most relevant issue to the question.\n"
            "4. If no relevant memories exist, say so honestly\n\n"
            "Be thorough but concise. Always cite sources.\n\n"
            + FUNCTION_CALLING_INSTRUCTIONS
        ),
        tools=[search_memory],
    )
    
    return query_agent