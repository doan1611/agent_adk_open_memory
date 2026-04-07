"""
Agent Memory Layer — Always-On ADK Agent with Gauss Model

A lightweight, cost-effective background agent that continuously processes, consolidates, and serves memory. 
Runs 24/7 using Gauss model.

Usage:
    python agent_gauss.py                          # watch ./inbox
    python agent_gauss.py --watch ./docs
    python agent_gauss.py --consolidate-every 15   # consolidate every 15 min

Query:
    python agent_gauss.py --ingest "issue_name"    # ingest issue from inbox
    python agent_gauss.py --search "query"         # search memories
"""

import argparse
import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone
from pathlib import Path

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from openmemory import Memory

# Import our custom Gauss model
from gauss_model import GaussModel

# ─── Config ────────────────────────────────────────────────────

# Init OpenMemory
memory = Memory()
case_path = Path("./inbox")

# Gauss Model Configuration
GAUSS_MODEL_ID = os.getenv("GAUSS_MODEL_ID", "0198f11e-ceab-71c3-8fb1-d077d6331843")

# Create Gauss model instance
MODEL = GaussModel()

# Supported file types for ingestion
TEXT_EXTENSIONS = {".json"}
ALL_SUPPORTED = {".json"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="[%H:%M]",
)
log = logging.getLogger("gauss-memory-agent")

# ─── TOOLS ──────────────────────────────────────────────────

def map_json_to_case(raw_json: dict) -> dict:
    """
    Convert the raw PLM case JSON (as provided in the data folder) to the
    internal schema used by the script.

    The source JSON uses camelCase keys; the internal schema uses snake_case.
    """
    return {
        "defect_code": raw_json.get("defectCode", ""),
        "title": raw_json.get("title", ""),
        "summary": raw_json.get("contentSummary", ""),
        "category": raw_json.get("category", ""),
        "cause": raw_json.get("cause", ""),
        "countermeasure": raw_json.get("countermeasure", ""),
    }

async def store_memory(name_of_issue: str, summary: str, entities_tags: list, importance: float) -> str:
    """
    Store memory with openmemory. Reads the JSON file in the case_path directory
    that matches the given issue name, stores it with additional metadata, and deletes the file.
    """
    log.info(f"\n👋 add memory!")
    if not case_path.is_dir():
        return f"case_path {case_path} is not a directory."
    
    # Ensure the filename ends with a single .json extension
    target_file = case_path / Path(name_of_issue).with_suffix('.json')
    if not target_file.is_file():
        return f"No file found for issue '{name_of_issue}'."
    
    try:
        raw = json.loads(target_file.read_text(encoding="utf-8"))
        case = map_json_to_case(raw)
        # Add additional metadata
        case["summary"] = summary
        case["entities_tags"] = entities_tags
        case["importance"] = importance
        log.info(f"\n👋 add memory!")
        await memory.add(
            content=json.dumps(case, ensure_ascii=False, indent=2),
            tags=["plm_case"],
        )
        target_file.unlink()
        return f"Memory stored for issue '{name_of_issue}'."
    except Exception as e:
        log.error(f"Failed to process {target_file.name}: {e}")
        return f"Error processing issue '{name_of_issue}'."

async def search_memory(query: str) -> str:
    """
    Semantic search
    """
    results = await memory.search(
        query,
        tags=["plm_case"],
        limit=5,
    )

    if not results:
        return "No memory found."

    return "\n".join([r["text"] for r in results])

# ─── ADK Agents ────────────────────────────────────────────────

def build_agents():
    """Build agents with Gauss model integration."""
    
    # Tool để chuyển hướng đến sub-agents
    async def transfer_to_agent(agent_name: str, request: str) -> str:
        """Transfer request to specified sub-agent."""
        return f"Transferring to {agent_name}: {request}"

    ingest_agent = Agent(
        name="ingest_agent",
        model=MODEL,
        description="Store information about the phone issues. Processes raw text into structured memory. Call this when new information arrives.",
        instruction=(
            "You are a Memory Ingest Agent. Your job is to extract high-value information from input and store it.\n"
            "You will extract and store information about the phone issues."
            "You handle json types of input. For any input you receive:\n"
            "1. Create a concise 1-2 sentence summary\n"
            "2. Assign 2-4 topic tags\n"
            "3. Rate importance from 0.0 to 1.0\n"
            "4. Call store_memory with all extracted information\n\n"
            "Use the full description as raw_text in store_memory so the context is preserved.\n"
            "Always call store_memory. Be concise and accurate.\n"
            "After storing, confirm what was stored in one sentence."
        ),
        tools=[store_memory],
    )

    query_agent = Agent(
        name="query_agent",
        model=MODEL,
        description="Answers questions using stored memories.",
        instruction=(
            "You are a Memory Query Agent. When asked a question:\n"
            "1. Call search_memory to access the memory store\n"
            "2. Synthesize an answer based ONLY on stored memories\n"
            "3. Provide information about the most relevant issue to the question.\n"
            "4. If no relevant memories exist, say so honestly\n\n"
            "Be thorough but concise. Always cite sources."
        ),
        tools=[search_memory],
    )

    orchestrator = Agent(
        name="memory_orchestrator",
        model=MODEL,
        description="Routes memory operations to specialist agents.",
        instruction=(
            "You are the Memory Orchestrator for an always-on memory system.\n"
            "Route requests to the right sub-agent:\n"
            "- New information -> ingest_agent\n"
            "- Questions -> query_agent\n"
            "After the sub-agent completes, give a brief summary."
        ),
        sub_agents=[ingest_agent, query_agent],
        tools=[transfer_to_agent],  # Thêm tool để model có thể gọi sub-agents
    )

    return orchestrator

# ─── Agent Runner ──────────────────────────────────────────────

class GaussMemoryAgent:
    def __init__(self):
        self.agent = build_agents()
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name="gauss_memory_layer",
            session_service=self.session_service,
        )

    async def run(self, message: str) -> str:
        """Run the agent with the given message and return the text response."""
        session = await self.session_service.create_session(
            app_name="gauss_memory_layer", user_id="agent",
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=message)])
        return await self._execute(session, content)

    async def _execute(self, session, content: types.Content) -> str:
        """Run the agent with the given content and return the text response."""
        response = ""
        async for event in self.runner.run_async(
            user_id="agent", session_id=session.id, new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response += part.text
        return response

    async def ingest(self, text: str, source: str = "") -> str:
        msg = f"Remember this information (source: {source}):\n\n{text}" if source else f"Remember this information:\n\n{text}"
        return await self.run(msg)

    async def query(self, question: str) -> str:
        return await self.run(f"Based on my memories, answer: {question}")

# ─── File Watcher ──────────────────────────────────────────────

async def watch_folder(agent: GaussMemoryAgent, folder: Path, poll_interval: int = 5):
    """Watch a folder for new files and ingest them."""
    folder.mkdir(parents=True, exist_ok=True)
    log.info(f"👁️  Watching: {folder}/  (supports: json)")

    while True:
        try:
            for f in sorted(folder.iterdir()):
                if f.name.startswith("."):
                    continue  # skip hidden files
                suffix = f.suffix.lower()
                if suffix not in ALL_SUPPORTED:
                    continue

                try:
                    if suffix in TEXT_EXTENSIONS:
                        # Text-based files — read as string
                        log.info(f"📄 New text file: {f.name}")
                        text = f.read_text(encoding="utf-8", errors="replace")[:10000]
                        if text.strip():
                            await agent.ingest(text, source=f.name)
                except Exception as file_err:
                    log.error(f"Error ingesting {f.name}: {file_err}")

        except Exception as e:
            log.error(f"Watch error: {e}")

        await asyncio.sleep(poll_interval)

# ─── Main ──────────────────────────────────────────────────────

async def _cli_ingest_search(args: argparse.Namespace) -> None:
    agent = GaussMemoryAgent()
    if args.ingest_value is not None:
        inbox = Path(args.watch)
        base = Path(args.ingest_value.strip())
        filename = base.name if base.suffix.lower() == ".json" else f"{base.name}.json"
        target = inbox / filename
        if not target.is_file():
            log.error("No file %s (expected issue JSON in %s)", target, inbox)
        else:
            text = target.read_text(encoding="utf-8", errors="replace")
            result = await agent.ingest(text, source=target.name)
            print(result)
    if args.search_value is not None:
        result = await agent.query(args.search_value)
        print(result)

def main():
    parser = argparse.ArgumentParser(description="Agent Memory Layer - Always-On ADK Agent with Gauss Model")
    parser.add_argument("--watch", default="./inbox", help="Folder to watch for new files (default: ./inbox)")
    parser.add_argument("--consolidate-every", type=int, default=30, help="Consolidation interval in minutes (default: 30)")
    parser.add_argument("--ingest", dest="ingest_value", metavar="ISSUE", help="Ingest issue by name (expects JSON file in inbox)")
    parser.add_argument("--search", dest="search_value", metavar="QUERY", help="Search memories with query")
    args = parser.parse_args()

    if args.ingest_value is None and args.search_value is None:
        parser.print_help()
        return

    # Handle graceful shutdown
    loop = asyncio.new_event_loop()

    def shutdown(sig):
        log.info(f"\n👋 Shutting down (signal {sig})...")
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown, sig)

    try:
        loop.run_until_complete(_cli_ingest_search(args))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        loop.close()
        log.info("🧠 Gauss Agent stopped.")

if __name__ == "__main__":
    main()