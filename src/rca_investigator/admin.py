"""The control centre (`/admin`): for the person running CuteBot, on their own computer.

- Inspector: every message with what CuteBot decided, why, and the code that decided it.
- Replies: edit replies.md, and try a message to see which reply it gets.
- Settings and look: behaviour and appearance, saved to a settings file.
- Health: run the tests and the accuracy check.
- Where to change what: common changes mapped to files and lines.

Only requests from this computer (localhost) are allowed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .settings import FIELDS, Settings
from .smalltalk import match_intent, matched_phrase, read_sections, write_sections
from .trace import REPO, TRACES

STATIC = Path(__file__).parent / "static"
LOCAL = {"127.0.0.1", "::1", "localhost", "testclient"}
WHERE_TO_CHANGE = [
    ("Friendly replies and their trigger words", "src/rca_investigator/replies.md", "## privacy"),
    ("How CuteBot decides what to do with a message", "src/rca_investigator/chat.py",
     "def respond"),
    ("Words that mean 'summarise'", "src/rca_investigator/chat.py", "SUMMARY_ASK ="),
    ("Words that mean 'investigate'", "src/rca_investigator/chat.py", "INVESTIGATIVE ="),
    ("Spotting a file that hasn't been shared yet", "src/rca_investigator/chat.py",
     "UNSHARED ="),
    ("Words that count as a problem in documents", "src/rca_investigator/documents.py",
     "SYMPTOM ="),
    ("Words that count as a cause in documents", "src/rca_investigator/documents.py", "CAUSE ="),
    ("Guessing what kind of document it is", "src/rca_investigator/documents.py", "KINDS = ["),
    ("Summary instructions for the AI", "src/rca_investigator/documents.py", "SUMMARY_SYSTEM ="),
    ("Investigation instructions for the AI (documents)", "src/rca_investigator/documents.py",
     "DOC_SYSTEM ="),
    ("Investigation instructions for the AI (numbers)", "src/rca_investigator/investigate.py",
     "SYSTEM_PROMPT ="),
    ("The judge's rules (numbers)", "src/rca_investigator/sufficiency.py", "def assess("),
    ("The judge's rules (documents)", "src/rca_investigator/documents.py",
     "def assess_documents"),
    ("The three explanation styles", "src/rca_investigator/chat.py", "def summary_for"),
    ("Reading uploaded files", "src/rca_investigator/ingest.py", "def read_file"),
    ("Charts in PDFs", "src/rca_investigator/vision.py", "def find_charts"),
    ("Memory (case notes)", "src/rca_investigator/memory.py", "class CaseNotes"),
    ("The chat page: look and behaviour", "src/rca_investigator/static/index.html", "<style>"),
]


def local_only(request: Request) -> None:
    if (request.client.host if request.client else "") not in LOCAL:
        raise HTTPException(403, "The control centre only opens on the computer running CuteBot.")


class RepliesBody(BaseModel):
    sections: list[dict]


class TryBody(BaseModel):
    message: str = Field(max_length=2000)


def _line_of(path: Path, needle: str) -> int:
    try:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if needle in line:
                return number
    except OSError:
        pass
    return 1


def _accuracy() -> dict:
    from .evaluate import score_report, summarise
    from .investigate import investigate
    from .simulate import generate_dataset

    out = {}
    for name, hard, n in (("standard", False, 20), ("hard", True, 25)):
        rows = [score_report(investigate("X", i.question, i.metric, i.metrics, i.records, None),
                             i.truth) for i in generate_dataset(n, seed=7, hard=hard)]
        out[f"{name} ({n} practice incidents, engines only)"] = {
            k: round(float(v) * 100) for k, v in summarise(rows).items()}
    return out


def add_admin_routes(app: FastAPI, settings: Settings) -> None:
    guard = [Depends(local_only)]

    @app.get("/admin", dependencies=guard)
    def page() -> FileResponse:
        return FileResponse(STATIC / "admin.html")

    @app.get("/api/admin/traces", dependencies=guard)
    def traces() -> list[dict]:
        return [t.as_dict() for t in reversed(TRACES)]

    @app.get("/api/admin/replies", dependencies=guard)
    def replies() -> dict:
        return {"sections": read_sections()[1]}

    @app.put("/api/admin/replies", dependencies=guard)
    def save_replies(body: RepliesBody) -> dict:
        head, _ = read_sections()
        try:
            write_sections(head, body.sections)
        except (ValueError, KeyError) as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"saved": len(body.sections)}

    @app.post("/api/admin/try", dependencies=guard)
    def try_message(body: TryBody) -> dict:
        intent = match_intent(body.message)
        if intent is None:
            return {"intent": None, "note": "No small-talk match: CuteBot would treat this as a "
                                            "question, a summary or an investigation."}
        return {"intent": intent.name, "phrase": matched_phrase(intent, body.message),
                "replies": intent.replies}

    @app.get("/api/admin/settings", dependencies=guard)
    def get_settings() -> dict:
        return {"fields": FIELDS, "values": settings.values,
                "file": str(settings.path) if settings.path else None}

    @app.put("/api/admin/settings", dependencies=guard)
    def put_settings(changes: dict) -> dict:
        try:
            return {"values": settings.update(changes)}
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/admin/settings/reset", dependencies=guard)
    def reset_settings() -> dict:
        return {"values": settings.reset()}

    @app.post("/api/admin/health/{check}", dependencies=guard)
    def health(check: str) -> dict:
        if check == "accuracy":
            return {"ok": True, "result": _accuracy()}
        if check != "tests":
            raise HTTPException(404, "Unknown check")
        if not (REPO / "tests").is_dir():
            return {"ok": False, "output": "The tests folder isn't available in this install."}
        run = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                             check=False, cwd=REPO, capture_output=True, text=True,
                             timeout=600)
        return {"ok": run.returncode == 0, "output": (run.stdout + run.stderr)[-6000:]}

    @app.get("/api/admin/map", dependencies=guard)
    def where_to_change() -> list[dict]:
        out = []
        for task, rel, needle in WHERE_TO_CHANGE:
            path = (REPO / rel).resolve()
            out.append({"task": task, "file": rel, "abs": str(path),
                        "line": _line_of(path, needle)})
        return out
