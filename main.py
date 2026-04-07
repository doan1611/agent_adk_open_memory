"""
Main application for the issue tracking system.

  python main.py                    # HTTP server + inbox watcher (30 min)
  python main.py --ingest issue.json
  python main.py --search "query"
  python main.py --port 8081 --poll-interval 1800
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from aiohttp import web

from agents.ingest_agent import create_ingest_agent
from agents.orchestrator import create_orchestrator
from agents.runner_util import run_agent_text_response
from models.gauss_model import GaussModel
from server.http_server import _write_issue_to_inbox, create_app
from watcher.file_watcher import watch_folder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="[%H:%M]",
)
log = logging.getLogger("main")

DEFAULT_POLL_INTERVAL = 1800


def build_agents(model: GaussModel):
    """Build ingest + query + orchestrator once at startup (shared model)."""
    ingest_agent = create_ingest_agent(model)
    orchestrator = create_orchestrator(model, ingest_agent=ingest_agent)
    return ingest_agent, orchestrator


async def cli_ingest(model: GaussModel, ingest_agent, path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    _write_issue_to_inbox(data)
    msg = f"Process this issue file: {path.name}\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
    out = await run_agent_text_response(
        ingest_agent,
        app_name="cli_ingest",
        user_id="cli",
        message=msg,
    )
    print(out)


async def cli_search(model: GaussModel, orchestrator, query: str) -> None:
    out = await run_agent_text_response(
        orchestrator,
        app_name="cli_search",
        user_id="cli",
        message=f"Search for issues related to: {query}",
    )
    print(out)


async def run_server_and_watcher(
    model: GaussModel,
    ingest_agent,
    orchestrator,
    inbox_path: Path,
    host: str,
    port: int,
    poll_interval: int,
) -> None:
    log.info("Starting Issue Tracking System")
    app = create_app(model=model, orchestrator=orchestrator)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    log.info("HTTP server on http://%s:%s", host, port)

    watcher_task = asyncio.create_task(
        watch_folder(ingest_agent, inbox_path, poll_interval=poll_interval)
    )
    log.info("File watcher on %s every %s s", inbox_path, poll_interval)

    try:
        await watcher_task
    except asyncio.CancelledError:
        pass
    finally:
        watcher_task.cancel()
        await runner.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue memory system (OpenMemory + Gauss + ADK)")
    parser.add_argument("--ingest", metavar="FILE", help="Ingest one issue JSON file (writes to inbox then runs ingest agent)")
    parser.add_argument("--search", metavar="QUERY", help="Search stored issues (orchestrator → query agent)")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP bind address (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8081, help="HTTP port (default 8081)")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Inbox scan interval in seconds (default {DEFAULT_POLL_INTERVAL})",
    )
    args = parser.parse_args()

    model = GaussModel()
    ingest_agent, orchestrator = build_agents(model)
    inbox_path = Path("./inbox")

    if args.ingest:
        p = Path(args.ingest)
        if not p.is_file():
            log.error("File not found: %s", p)
            sys.exit(1)
        asyncio.run(cli_ingest(model, ingest_agent, p))
        return

    if args.search:
        asyncio.run(cli_search(model, orchestrator, args.search))
        return

    asyncio.run(
        run_server_and_watcher(
            model,
            ingest_agent,
            orchestrator,
            inbox_path,
            args.host,
            args.port,
            args.poll_interval,
        )
    )


if __name__ == "__main__":
    main()
