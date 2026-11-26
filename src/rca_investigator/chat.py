"""A conversation with CuteBot: collect the user's data, investigate, answer follow-ups.

A session holds what the user has shared so far (a table of numbers and records). Each
message may add data (pasted records or a pasted table), start an investigation, or ask
a follow-up question about the last report. Progress is reported through `emit` so the
web page can show CuteBot working through each stage.
"""

from __future__ import annotations

import json
import random
import re
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from .analyze import analyze_change, label, metric_columns
from .ingest import IngestError, Parsed, _looks_like_table, read_text, text_to_records
from .investigate import ChatClient, investigate
from .llm import LLMError
from .schema import RCAReport
from .simulate import SCENARIOS, generate_incident

Emit = Callable[[str, dict], None]

STAGE_OF_STEP = {
    "numbers": "collect", "numbers_done": "collect",
    "records": "polish", "records_done": "polish",
    "model": "think", "model_done": "think", "fact_check": "think",
    "judge": "weigh", "judge_done": "weigh",
}
RERUN = re.compile(r"investigat|again|re-?run|start over|analy[sz]e|check (it|this|now)", re.IGNORECASE)
QUESTION_START = re.compile(r"^\s*(why|what|how|when|where|which|who|is|are|did|does|can|could)\b",
                            re.IGNORECASE)
SYNONYMS = {"slow": ("latency", "duration", "response"), "error": ("error", "fail"),
            "fail": ("error", "fail"), "traffic": ("requests", "traffic", "volume")}

HELP = ("Hi! I'm CuteBot. Share what went wrong and I'll investigate:\n"
        "1. Click ➕ to upload a **table of numbers** (CSV) with a time column and the "
        "measures, e.g. error rate or latency (optional: service and region columns).\n"
        "2. Upload or paste **records** like deploys, setting changes, alerts, tickets or "
        "log lines, each with a date and time.\n"
        "3. Ask your question, e.g. *Why did the error rate go up on Tuesday?*\n"
        "No data handy? Click **Try a sample**.")

FOLLOWUP_SYSTEM = """You are CuteBot, a friendly incident investigator.
Answer the user's question using ONLY the investigation below. Cite evidence IDs
like [E3]. If the investigation doesn't answer it, say so and say what data would help.
Use plain, friendly words and at most 4 sentences."""


@dataclass
class Session:
    metrics: pd.DataFrame | None = None
    records: list[dict] = field(default_factory=list)
    report: RCAReport | None = None
    metric: str | None = None
    changed: bool = False

    def known(self) -> dict[str, set[str]]:
        if self.metrics is None:
            return {}
        return {k: set(self.metrics[k].astype(str)) for k in ("service", "region")}

    def add(self, parsed: Parsed) -> None:
        if parsed.metrics is not None:
            if self.metrics is None:
                self.metrics = parsed.metrics
            else:
                both = pd.concat([self.metrics, parsed.metrics], ignore_index=True)
                self.metrics = (both.groupby(["timestamp", "service", "region"], as_index=False)
                                .mean(numeric_only=True))
        if parsed.records:
            merged = sorted([*self.records, *parsed.records], key=lambda r: r["timestamp"])
            self.records = [{**r, "id": f"R{i:03d}"} for i, r in enumerate(merged, start=1)]
        self.changed = True


def choose_metric(metrics: pd.DataFrame, message: str) -> str:
    """The measure the question is about, or else the one that changed the most."""
    cols = metric_columns(metrics)
    candidates = [c for c in cols if c != "requests"] or cols
    text = message.lower()
    for word, parts in SYNONYMS.items():
        if word in text:
            hit = next((c for c in candidates if any(p in c for p in parts)), None)
            if hit:
                return hit
    for col in candidates:
        if any(len(tok) > 2 and tok in text for tok in col.split("_")):
            return col
    best, best_change = candidates[0], -1.0
    for col in candidates:
        analysis = analyze_change(metrics, col)
        if analysis.detected and abs(analysis.relative_change) > best_change:
            best, best_change = col, abs(analysis.relative_change)
    return best


def _pasted_data(message: str, known: dict) -> Parsed | None:
    """Records or a table pasted into the chat, if any (a lone dated question is not data)."""
    if _looks_like_table(message):
        try:
            return read_text("pasted.csv", message, known)
        except IngestError:
            pass
    records = text_to_records(message, known)
    if len(records) == 1 and ("?" in message or QUESTION_START.match(message)):
        return None
    return Parsed(records=records, summary=f"{len(records)} records") if records else None


def _short_summary(report: RCAReport) -> str:
    v = report.sufficiency.verdict.value
    opener = {"sufficient": "I'm sure about this one!",
              "partial": "I'm partly sure: there's more than one possible answer.",
              "insufficient": "I don't have enough clues to be sure yet."}[v]
    top = report.contributing_factors[0].description if report.contributing_factors else None
    lines = [opener]
    if top:
        lines.append(f"{'Main cause' if v != 'insufficient' else 'Best lead'}: {top}")
    if report.sufficiency.missing_data:
        lines.append("More data that would help: " + "; ".join(report.sufficiency.missing_data))
    lines.append("Ask me anything about it, or share more data and I'll look again.")
    return "\n".join(lines)


def _followup_prompt(report: RCAReport, question: str) -> str:
    facts = {
        "verdict": report.sufficiency.verdict.value,
        "reasons": report.sufficiency.reasons,
        "contributing_factors": [f.model_dump(mode="json") for f in report.contributing_factors],
        "ruled_out": [r.model_dump(mode="json") for r in report.ruled_out],
        "actions": [a.action for a in report.actions],
        "evidence": {e.id: e.summary for e in report.evidence},
    }
    return f"Investigation:\n{json.dumps(facts, indent=1)}\n\nQuestion: {question}"


class Conversation:
    def __init__(self, client_factory: Callable[[bool], ChatClient | None]):
        self.client_factory = client_factory

    def load_sample(self, session: Session, seed: int | None = None) -> dict:
        rng = random.Random(seed)
        scenario = rng.choice([s for s in SCENARIOS if s != "no_clear_cause"])
        inc = generate_incident("SAMPLE", scenario, seed=rng.randint(1, 10_000))
        session.__init__()
        session.add(Parsed(metrics=inc.metrics, records=inc.records))
        return {"summary": f"Sample loaded: a table of {len(inc.metrics):,} rows (requests, "
                           f"error rate, latency by service and region) and "
                           f"{len(inc.records)} records.",
                "question": inc.question}

    def respond(self, session: Session, message: str, use_llm: bool, emit: Emit) -> None:
        message = message.strip()
        pasted = _pasted_data(message, session.known()) if message else None
        if pasted is not None:
            session.add(pasted)
            emit("stage", {"stage": "collect", "text": "Collecting the evidence you pasted..."})
            emit("say", {"text": f"Got it! I picked up {pasted.summary} from your message."})

        if session.metrics is None:
            if pasted is not None:
                emit("say", {"text": "I've kept those clues. Now I need the numbers: click ➕ "
                                     "and upload a table (CSV) with a time column and the "
                                     "measure that went wrong."})
            else:
                emit("say", {"text": HELP})
            return

        mentioned = choose_metric(session.metrics, message) if message else session.metric
        new_metric = session.report is not None and message and mentioned != session.metric \
            and any(t in message.lower() for t in mentioned.split("_") if len(t) > 2)
        if session.report is None or session.changed or RERUN.search(message) or new_metric:
            self._investigate(session, message, use_llm, emit)
        elif message:
            self._follow_up(session, message, use_llm, emit)

    def _investigate(self, session: Session, message: str, use_llm: bool, emit: Emit) -> None:
        metric = choose_metric(session.metrics, message)
        question = (message if message and ("?" in message or QUESTION_START.match(message))
                    and len(message) < 300 else f"Why did the {label(metric)} change?")

        def on_step(step: str, text: str) -> None:
            emit("stage", {"stage": STAGE_OF_STEP.get(step, "think"), "text": text})

        args = ("CHAT", question, metric, session.metrics, session.records)
        try:
            report = investigate(*args, self.client_factory(use_llm), on_step=on_step)
        except LLMError as exc:
            on_step("model_done", f"The language model isn't available ({exc}), so I'll "
                                  "use my maths helpers only.")
            report = investigate(*args, None, on_step=on_step)
        session.report, session.metric, session.changed = report, metric, False
        emit("stage", {"stage": "back", "text": "Coming back with the answer!"})
        emit("report", report.model_dump(mode="json"))
        emit("say", {"text": _short_summary(report)})

    def _follow_up(self, session: Session, message: str, use_llm: bool, emit: Emit) -> None:
        client = self.client_factory(use_llm)
        if client is None or not hasattr(client, "chat"):
            emit("say", {"text": "I can answer follow-up questions when the language model is "
                                 "switched on. Here's the short version:\n"
                                 + _short_summary(session.report)})
            return
        emit("stage", {"stage": "think", "text": "Thinking about your question..."})
        try:
            answer = client.chat(_followup_prompt(session.report, message),
                                 system=FOLLOWUP_SYSTEM, temperature=0.2)
        except LLMError as exc:
            answer = (f"I couldn't reach the language model ({exc}). Here's the short "
                      "version:\n" + _short_summary(session.report))
        emit("stage", {"stage": "back", "text": "Here you go!"})
        emit("say", {"text": answer.strip()})
