"""Web page: watch CuteBot investigate an incident live.

`rca serve` starts it. The page lists the incidents in a folder; when one is chosen, the
investigation runs in a background thread and each step is streamed to the page as a
server-sent event, followed by the finished report.
"""

from __future__ import annotations

import json
import queue
import threading
from collections.abc import Callable, Iterator
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from .investigate import ChatClient, investigate
from .llm import DEFAULT_MODEL, LLMError, OllamaClient
from .simulate import load_incident

BOT_NAME = "CuteBot"
STATIC = Path(__file__).parent / "static"


def _incident_folders(data_dir: Path) -> dict[str, Path]:
    folders = sorted(p for p in data_dir.iterdir() if (p / "incident.json").exists())
    return {p.name: p for p in folders}


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def create_app(data_dir: str | Path, model: str = DEFAULT_MODEL,
               client_factory: Callable[[bool], ChatClient | None] | None = None) -> FastAPI:
    data_dir = Path(data_dir)
    if client_factory is None:
        def client_factory(use_llm: bool) -> ChatClient | None:
            return OllamaClient(model=model) if use_llm else None

    app = FastAPI(title="RCA Investigator")

    @app.get("/")
    def page() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/api/info")
    def info() -> dict:
        return {"bot_name": BOT_NAME, "model": model}

    @app.get("/api/incidents")
    def incidents() -> list[dict]:
        out = []
        for name, folder in _incident_folders(data_dir).items():
            meta = json.loads((folder / "incident.json").read_text())
            out.append({"id": name, "question": meta["question"]})
        return out

    @app.get("/api/investigate/{incident_id}")
    def run(incident_id: str, llm: bool = True) -> StreamingResponse:
        folder = _incident_folders(data_dir).get(incident_id)
        if folder is None:
            raise HTTPException(404, f"No incident called {incident_id}")
        meta, metrics, records = load_incident(folder)
        events: queue.Queue = queue.Queue()

        def on_step(step: str, message: str) -> None:
            events.put(("step", {"step": step, "message": message}))

        def work() -> None:
            args = (meta["incident_id"], meta["question"], meta["metric"], metrics, records)
            try:
                try:
                    report = investigate(*args, client_factory(llm), on_step=on_step)
                except LLMError as exc:
                    on_step("model_done", f"The language model is not available ({exc}). "
                            "Carrying on with the engines only.")
                    report = investigate(*args, None, on_step=on_step)
                events.put(("report", report.model_dump(mode="json")))
            except Exception as exc:  # noqa: BLE001 (show any failure on the page, never hang)
                events.put(("error", {"message": str(exc)}))
            events.put(None)

        threading.Thread(target=work, daemon=True).start()

        def stream() -> Iterator[str]:
            while (item := events.get()) is not None:
                yield _sse(*item)
            yield _sse("done", {})

        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})

    return app
