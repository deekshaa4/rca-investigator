"""Web page: chat with CuteBot, share data, and watch it investigate.

`rca serve` starts it. People type or paste into the chat, or click ➕ to upload files
(a table of numbers and records). While CuteBot works, each stage is streamed to the
page as a server-sent event, followed by the report and a short answer.

Everything stays on this computer: uploads are kept in memory for the session only.
"""

from __future__ import annotations

import base64
import binascii
import json
import queue
import re
import threading
from collections import OrderedDict
from collections.abc import Callable, Iterator
from pathlib import Path, PurePath

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

from .chat import Conversation, Session
from .documents import DOC_TYPES, load_document
from .ingest import IngestError, read_file
from .investigate import ChatClient, to_markdown
from .llm import DEFAULT_MODEL, OllamaClient
from .simulate import generate_incident
from .sources import Catalog

BOT_NAME = "CuteBot"
STATIC = Path(__file__).parent / "static"
MAX_SESSIONS = 200
MAX_UPLOAD_CHARS = 20_000_000  # about 20 MB of text
SESSION_ID = r"^[A-Za-z0-9-]{8,64}$"


class Upload(BaseModel):
    session: str = Field(pattern=SESSION_ID)
    name: str = Field(max_length=200)
    data_base64: str = Field(max_length=MAX_UPLOAD_CHARS * 4 // 3 + 4)


class Message(BaseModel):
    session: str = Field(pattern=SESSION_ID)
    message: str = Field(default="", max_length=200_000)
    llm: bool = True


class SessionOnly(BaseModel):
    session: str = Field(pattern=SESSION_ID)


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _sample_files() -> dict[str, str]:
    inc = generate_incident("SAMPLE", "bad_deploy", seed=12)
    records = inc.records
    lines = ["timestamp,source,service,region,text"] + [
        ",".join([r["timestamp"], r["source"], r.get("service", ""), r.get("region", ""),
                  '"' + r["text"].replace('"', "'") + '"']) for r in records]
    return {"metrics.csv": inc.metrics.to_csv(index=False), "records.csv": "\n".join(lines) + "\n"}


class StyleChoice(BaseModel):
    session: str = Field(pattern=SESSION_ID)
    style: str = Field(pattern="^(nerd|simple|kid)$")


def create_app(model: str = DEFAULT_MODEL,
               client_factory: Callable[[bool], ChatClient | None] | None = None,
               sources: list[str] | None = None) -> FastAPI:
    """`sources`: databases (SQLite path or SQLAlchemy URL) or folders to connect, read-only."""
    if client_factory is None:
        def client_factory(use_llm: bool) -> ChatClient | None:
            return OllamaClient(model=model) if use_llm else None

    app = FastAPI(title="RCA Investigator")
    catalog = Catalog.connect(sources) if sources else None
    conversation = Conversation(client_factory, catalog)
    sessions: OrderedDict[str, Session] = OrderedDict()
    lock = threading.Lock()

    def session_for(sid: str) -> Session:
        with lock:
            if sid not in sessions:
                sessions[sid] = Session()
                while len(sessions) > MAX_SESSIONS:
                    sessions.popitem(last=False)
            sessions.move_to_end(sid)
            return sessions[sid]

    @app.get("/")
    def page() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/api/info")
    def info() -> dict:
        return {"bot_name": BOT_NAME, "model": model,
                "connected": catalog.summary() if catalog else None,
                "tables": catalog.describe() if catalog else []}

    @app.post("/api/upload")
    def upload(body: Upload) -> dict:
        session = session_for(body.session)
        try:
            data = base64.b64decode(body.data_base64, validate=True)
        except binascii.Error as exc:
            raise HTTPException(400, "The file didn't arrive in one piece. Please try again.") from exc
        doc, doc_error = None, None
        if PurePath(body.name).suffix.lower() in DOC_TYPES:
            try:
                doc = load_document(body.name, data)
            except IngestError as exc:
                doc_error = exc
        try:
            parsed = read_file(body.name, data, session.known())
        except IngestError as exc:
            if doc is None:
                raise HTTPException(400, str(doc_error or exc)) from exc
            parsed = None
        parts = []
        if doc is not None:
            session.add_document(doc)
            parts.append(f"I'll read all of it ({doc.pages} page(s), {doc.words:,} words) when "
                         "you ask me what happened.")
        if parsed is not None and (parsed.metrics is not None or parsed.records):
            session.add(parsed)
            session.uploaded = True
            parts.append(f"I also found {parsed.summary[0].lower()}{parsed.summary[1:]}")
        elif parsed is not None:
            parts.append(parsed.summary)
        if session.metrics is None and not session.documents:
            parts.append("I still need a table of numbers or a document to read.")
        else:
            parts.append("Ask me what went wrong whenever you're ready!")
        return {"summary": " ".join(parts), "has_numbers": session.metrics is not None,
                "message": f"Got **{body.name}**. " + "\n".join(parts)}

    @app.post("/api/sample")
    def sample(body: SessionOnly) -> dict:
        return conversation.load_sample(session_for(body.session))

    @app.get("/api/sample-file/{name}")
    def sample_file(name: str) -> PlainTextResponse:
        files = _sample_files()
        if name not in files:
            raise HTTPException(404, "No such sample file")
        return PlainTextResponse(files[name], media_type="text/csv", headers={
            "Content-Disposition": f'attachment; filename="sample-{re.sub("[^a-z.]", "", name)}"'})

    @app.post("/api/style")
    def style(body: StyleChoice) -> dict:
        return {"summary": conversation.set_style(session_for(body.session), body.style)}

    @app.get("/api/report/{sid}.md")
    def download(sid: str) -> PlainTextResponse:
        session = sessions.get(sid) if re.match(SESSION_ID, sid) else None
        if session is None or session.report is None:
            raise HTTPException(404, "No report yet")
        return PlainTextResponse(to_markdown(session.report), media_type="text/markdown",
                                 headers={"Content-Disposition":
                                          'attachment; filename="rca-report.md"'})

    @app.post("/api/reset")
    def reset(body: SessionOnly) -> dict:
        with lock:
            sessions.pop(body.session, None)
        return {"ok": True}

    @app.post("/api/chat")
    def chat(body: Message) -> StreamingResponse:
        session = session_for(body.session)
        events: queue.Queue = queue.Queue()

        def emit(kind: str, data: dict) -> None:
            events.put((kind, data))

        def work() -> None:
            try:
                conversation.respond(session, body.message, body.llm, emit)
            except IngestError as exc:
                emit("say", {"text": str(exc)})
            except Exception as exc:  # noqa: BLE001 (show any failure in the chat, never hang)
                emit("error", {"message": f"Something went wrong: {exc}"})
            events.put(None)

        threading.Thread(target=work, daemon=True).start()

        def stream() -> Iterator[str]:
            while (item := events.get()) is not None:
                yield _sse(*item)
            yield _sse("done", {})

        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})

    return app
