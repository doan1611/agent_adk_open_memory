"""
File watcher for monitoring the inbox directory.
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from agents.runner_util import run_agent_text_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="[%H:%M]",
)
log = logging.getLogger("file_watcher")

# Supported file types for ingestion
TEXT_EXTENSIONS = {".json"}
ALL_SUPPORTED = {".json"}

async def watch_folder(ingest_agent, folder: Path, poll_interval: int = 5):
    """
    Watch a folder for new files and ingest them.

    Args:
        ingest_agent: Pre-built ingest ADK agent (same model as orchestrator).
        folder: Path to the folder to watch
        poll_interval: How often to check for new files (in seconds)
    """
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
                            msg = f"Process this issue file: {f.name}\n\n{text}"
                            response = await run_agent_text_response(
                                ingest_agent,
                                app_name="file_watcher",
                                user_id="watcher",
                                message=msg,
                            )
                            log.info(f"Processed file {f.name}: {response}")
                except Exception as file_err:
                    log.error(f"Error ingesting {f.name}: {file_err}")

        except Exception as e:
            log.error(f"Watch error: {e}")

        await asyncio.sleep(poll_interval)