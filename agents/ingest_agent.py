"""
Ingest agent for processing issue files.
"""

from google.adk.agents import Agent
from agents.prompts import FUNCTION_CALLING_INSTRUCTIONS
from tools.memory_tools import store_memory


def create_ingest_agent(model):
    """
    Create ingest agent for processing issue files.
    """
    ingest_agent = Agent(
        name="ingest_agent",
        model=model,
        description="Store information about the phone issues. Processes raw text into structured memory. Call this when new information arrives.",
        instruction=(
            "You are a Memory Ingest Agent. Your job is to extract high-value information from input and store it.\n"
            "You will extract and store information about the phone issues.\n"
            "You handle JSON issue payloads (defectCode, title, contentSummary, category, cause, countermeasure).\n"
            "For any input you receive:\n"
            "1. Create a concise 1-2 sentence summary\n"
            "2. Assign 2-4 topic tags\n"
            "3. Rate importance from 0.0 to 1.0\n"
            "4. Call store_memory with name_of_issue equal to defectCode from the JSON\n\n"
            "Use the full description in the summary so context is preserved.\n"
            "Always call store_memory exactly once when the payload is valid.\n"
            "After the tool succeeds, confirm what was stored in one short sentence.\n\n"
            + FUNCTION_CALLING_INSTRUCTIONS
        ),
        tools=[store_memory],
    )
    
    return ingest_agent