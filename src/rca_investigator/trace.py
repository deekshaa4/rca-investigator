"""Traces for the control centre: what CuteBot decided for each message, and why.

Every chat message gets a Trace. Code calls `decide(...)` at each decision point; the
file, line and function that made the decision are recorded automatically, so the
control centre can say exactly where to change the behaviour. Calls to the language
model (prompt, reply, time taken) and the messages sent back are recorded too.

Traces are kept in memory only (the last 100), never written to disk.
"""

from __future__ import annotations

import inspect
import time
from collections import deque
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).parent
REPO = PACKAGE.parent.parent
TRACES: deque = deque(maxlen=100)
current: ContextVar[Trace | None] = ContextVar("current_trace", default=None)


def where(depth: int = 2) -> dict:
    """File, line and function of the code `depth` frames up."""
    frame = inspect.stack()[depth]
    path = Path(frame.filename).resolve()
    rel = path.relative_to(REPO) if path.is_relative_to(REPO) else path
    return {"file": str(rel), "abs": str(path), "line": frame.lineno, "function": frame.function}


@dataclass
class Trace:
    id: int
    session: str
    message: str
    started: float = field(default_factory=time.time)
    decisions: list[dict] = field(default_factory=list)
    llm_calls: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    seconds: float | None = None

    def as_dict(self) -> dict:
        return {"id": self.id, "session": self.session[:8], "message": self.message[:2000],
                "time": time.strftime("%H:%M:%S", time.localtime(self.started)),
                "route": self.decisions[-1]["route"] if self.decisions else "(no decision)",
                "decisions": self.decisions, "llm_calls": self.llm_calls,
                "events": self.events, "seconds": self.seconds}


def start(session: str, message: str) -> Trace:
    trace = Trace(len(TRACES) and TRACES[-1].id + 1 or 1, session, message)
    TRACES.append(trace)
    current.set(trace)
    return trace


def finish(trace: Trace) -> None:
    trace.seconds = round(time.time() - trace.started, 1)


def decide(route: str, reason: str) -> None:
    """Record a decision, with the code location that made it."""
    trace = current.get()
    if trace is not None:
        trace.decisions.append({"route": route, "reason": reason, **where()})


def note_event(kind: str, data: dict) -> None:
    trace = current.get()
    if trace is None:
        return
    if kind == "report":
        report = data.get("report", {})
        text = (f"report: verdict {report.get('sufficiency', {}).get('verdict')}, "
                f"{len(report.get('contributing_factors', []))} factor(s), "
                f"{len(report.get('evidence', []))} clue(s)")
    else:
        text = str(data.get("text") or data.get("message") or data.get("style") or "")
    trace.events.append({"kind": kind, "text": text[:600],
                         "at": round(time.time() - trace.started, 1)})


class TracingClient:
    """Wraps a language model client and records every call in the current trace."""

    def __init__(self, client: Any):
        self.client = client

    def _record(self, kind: str, prompt: str, system: str | None, call) -> Any:
        started = time.time()
        error = None
        try:
            reply = call()
            return reply
        except Exception as exc:
            error, reply = str(exc), None
            raise
        finally:
            trace = current.get()
            if trace is not None:
                trace.llm_calls.append({
                    "kind": kind, "system": (system or "")[:3000], "prompt": prompt[:6000],
                    "reply": reply if isinstance(reply, (dict, list)) else str(reply)[:4000],
                    "error": error, "seconds": round(time.time() - started, 1),
                    "called_from": where(3)})

    @property
    def chat_json(self):
        if not hasattr(self.client, "chat_json"):
            raise AttributeError("chat_json")
        return lambda prompt, json_schema, system=None: self._record(
            "chat_json", prompt, system,
            lambda: self.client.chat_json(prompt, json_schema, system=system))

    @property
    def chat(self):
        """Only present if the wrapped client can chat (code checks with hasattr)."""
        if not hasattr(self.client, "chat"):
            raise AttributeError("chat")
        return lambda prompt, system=None, json_schema=None, temperature=0.1: self._record(
            "chat", prompt, system,
            lambda: self.client.chat(prompt, system=system, json_schema=json_schema,
                                     temperature=temperature))

    @property
    def chat_stream(self):
        if not hasattr(self.client, "chat_stream"):
            raise AttributeError("chat_stream")

        def stream(prompt, system=None, temperature=0.1):
            parts: list[str] = []

            def run():
                for piece in self.client.chat_stream(prompt, system=system,
                                                     temperature=temperature):
                    parts.append(piece)
                    yield piece

            started, error = time.time(), None
            try:
                yield from run()
            except Exception as exc:
                error = str(exc)
                raise
            finally:
                trace = current.get()
                if trace is not None:
                    trace.llm_calls.append({
                        "kind": "chat (streamed)", "system": (system or "")[:3000],
                        "prompt": prompt[:6000], "reply": "".join(parts)[:4000], "error": error,
                        "seconds": round(time.time() - started, 1), "called_from": where(3)})
        return stream

    def __getattr__(self, name: str) -> Any:
        return getattr(self.client, name)
