"""
HTTP server for the issue tracking system.
"""

import json
import logging
from pathlib import Path

from aiohttp import web

from agents.orchestrator import create_orchestrator
from agents.runner_util import run_agent_text_response
from models.gauss_model import GaussModel

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("http_server")


def _write_issue_to_inbox(data: dict) -> Path:
    """Persist API payload so store_memory can read ./inbox/<defectCode>.json."""
    defect = data.get("defectCode")
    if not defect or not isinstance(defect, str):
        raise ValueError("JSON must include string field 'defectCode'")
    inbox = Path("./inbox")
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / f"{defect.strip()}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


async def handle_ingest(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)

    try:
        _write_issue_to_inbox(data)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)

    orchestrator = request.app["orchestrator"]
    content_text = f"Process this new issue information:\n\n{json.dumps(data, indent=2)}"
    try:
        response_text = await run_agent_text_response(
            orchestrator,
            app_name="http_server",
            user_id="api",
            message=content_text,
        )
    except Exception as ex:
        log.exception("ingest failed")
        return web.json_response({"error": str(ex)}, status=500)

    return web.json_response({"status": "ingested", "response": response_text})


async def handle_search(request):
    query = request.query.get("q", "").strip()
    if not query:
        return web.json_response({"error": "missing ?q= parameter"}, status=400)

    orchestrator = request.app["orchestrator"]
    try:
        response_text = await run_agent_text_response(
            orchestrator,
            app_name="http_server",
            user_id="api",
            message=f"Search for issues related to: {query}",
        )
    except Exception as ex:
        log.exception("search failed")
        return web.json_response({"error": str(ex)}, status=500)

    return web.json_response({"query": query, "response": response_text})


def create_app(model=None, orchestrator=None):
    """
    Create the HTTP application. Pass shared model/orchestrator from main for reuse.
    """
    app = web.Application()
    app["model"] = model if model is not None else GaussModel()
    app["orchestrator"] = (
        orchestrator
        if orchestrator is not None
        else create_orchestrator(app["model"])
    )
    app.router.add_post("/ingest", handle_ingest)
    app.router.add_get("/search", handle_search)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8081)
