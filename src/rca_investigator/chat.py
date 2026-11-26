"""A conversation with CuteBot: gather data, investigate, explain, answer follow-ups.

Data comes from uploads, pasted text, or connected sources (a database or folder, see
`sources.py`). Each message may add data, start an investigation, or ask a follow-up
question about the last report. Progress is reported through `emit` so the web page can
show CuteBot working through each stage.

CuteBot also adapts how it explains: a technical reader gets the "data nerd" version, a
non-technical reader a straight answer, or an "explain like I'm 5" version on request.
"""

from __future__ import annotations

import json
import random
import re
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from .analyze import _aggregate, _select, analyze_change, label, metric_columns
from .documents import (
    Document,
    answer_from_documents,
    document_from_text,
    investigate_documents,
)
from .ingest import IngestError, Parsed, _looks_like_table, read_text, text_to_records
from .investigate import ChatClient, investigate
from .llm import LLMError
from .schema import RCAReport
from .simulate import SCENARIOS, generate_incident

Emit = Callable[[str, dict], None]
STYLES = ("nerd", "simple", "kid")

STAGE_OF_STEP = {
    "numbers": "collect", "numbers_done": "collect",
    "records": "polish", "records_done": "polish",
    "model": "think", "model_done": "think", "fact_check": "think",
    "judge": "weigh", "judge_done": "weigh",
    "doc_read": "collect", "doc_facts": "polish",
}
PASTE_DOC_CHARS = 400  # longer messages are treated as a document to read
GREETING = re.compile(r"^\s*(hi|hello|hey|thanks|thank you|ok|okay|cool|great)\b[\s!.?]*$", re.IGNORECASE)
GENERAL_SYSTEM = """You are CuteBot, a friendly root cause analysis assistant. The user has not
shared any data, so answer from general knowledge in at most 5 sentences, then suggest what
they could share (documents, notes, logs or numbers) for a proper investigation."""
RERUN = re.compile(r"investigat|again|re-?run|start over|analy[sz]e|check (it|this|now)", re.IGNORECASE)
QUESTION_START = re.compile(r"^\s*(why|what|how|when|where|which|who|is|are|did|does|can|could)\b",
                            re.IGNORECASE)
SYNONYMS = {"slow": ("latency", "duration", "response"), "error": ("error", "fail"),
            "fail": ("error", "fail"), "traffic": ("requests", "traffic", "volume")}
TECH_WORDS = re.compile(
    r"\b(p\d{2}|latency|5xx|4xx|50[0-4]|deploy\w*|rollback|config|sql|query|api|endpoint|"
    r"cpu|memory|pod|k8s|kubernetes|cluster|node|thread|pool|timeout|throughput|qps|rps|"
    r"metric|segment|regression|stack ?trace|exception|null ?pointer|schema|index|cache|"
    r"replica|shard|feature flag|canary|sla|slo|percentile|anomaly|baseline|t-?stat)\b", re.IGNORECASE)
KID_WORDS = re.compile(r"like (i'?m|i am) (5|five|a kid|a child)|explain (it )?(simply|to a kid)|"
                       r"eli5|in simple words|not (very )?technical|non-?technical", re.IGNORECASE)
NERD_WORDS = re.compile(r"data nerd|technical (answer|details|version)|all the details|"
                        r"in detail|deep dive|show (me )?the numbers", re.IGNORECASE)
STRAIGHT_WORDS = re.compile(r"straight(forward)? answer|just tell me|short answer|tl;?dr", re.IGNORECASE)

HELP = ("Hi! I'm CuteBot. Share what went wrong and I'll investigate:\n"
        "1. Click ➕ to upload a **table of numbers** (CSV, Excel or PDF) with a time column "
        "and the measures, e.g. error rate or latency.\n"
        "2. Upload or paste **records** like deploys, setting changes, alerts, tickets or "
        "log lines, each with a date and time.\n"
        "3. Ask your question, e.g. *Why did the error rate go up on Tuesday?*\n"
        "No data handy? Click **Try a sample**.")

FOLLOWUP_SYSTEM = """You are CuteBot, a friendly incident investigator.
Answer the user's question using ONLY the investigation below. Cite evidence IDs
like [E3]. If the investigation doesn't answer it, say so and say what data would help.
At most 4 sentences."""
STYLE_INSTRUCTION = {
    "nerd": "The reader is technical: be precise, use the exact numbers, times and IDs.",
    "simple": "The reader is not technical: use plain words, no jargon.",
    "kid": "Explain it like to a 5-year-old: very simple words and a friendly comparison.",
}


def detect_style(message: str) -> str | None:
    """Who is asking? 'nerd', 'simple' or 'kid'; None if it can't tell yet."""
    if KID_WORDS.search(message):
        return "kid"
    if NERD_WORDS.search(message):
        return "nerd"
    if STRAIGHT_WORDS.search(message):
        return "simple"
    hits = len(TECH_WORDS.findall(message))
    if hits >= 2 or (hits == 1 and len(message.split()) <= 8):
        return "nerd"
    return "simple" if len(message.split()) >= 4 else None


@dataclass
class Session:
    metrics: pd.DataFrame | None = None
    records: list[dict] = field(default_factory=list)
    report: RCAReport | None = None
    metric: str | None = None
    changed: bool = False
    uploaded: bool = False  # the user shared data themselves (uploads take priority)
    style: str | None = None
    style_chosen: bool = False  # picked by the user, so don't re-detect
    documents: list[Document] = field(default_factory=list)
    mode: str = "numbers"  # what the last report was based on: "numbers" or "documents"
    last_shared: str = "data"  # "documents" when the latest thing shared was a document

    def add_document(self, doc: Document) -> None:
        self.documents.append(doc)
        self.changed = True
        self.last_shared = "documents"

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
        if parsed.metrics is not None:
            self.last_shared = "data"


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


def _where(report: RCAReport) -> str:
    seg = report.what_changed.segment if report.what_changed else {}
    return ", ".join(v for v in seg.values() if v != "all") or "everywhere"


def summary_for(report: RCAReport, style: str = "simple") -> str:
    """The short answer under the report, written for the reader."""
    if report.what_changed is None and report.summary:
        return _document_summary(report, style)
    v = report.sufficiency.verdict.value
    wc = report.what_changed
    top = report.contributing_factors[0] if report.contributing_factors else None
    fix = next((a.action for a in report.actions if a.type.value == "corrective"),
               report.actions[0].action if report.actions else None)
    if style == "nerd":
        lines = [f"**Verdict: {v}** (score {report.sufficiency.score:.2f})."]
        if wc:
            lines.append(f"{label(wc.metric).capitalize()} in {_where(report)}: "
                         f"{wc.baseline_value:.4g} → {wc.current_value:.4g} "
                         f"({wc.relative_change:+.0%}), change point {wc.change_start}.")
        for f in report.contributing_factors:
            lines.append(f"{f.rank}. {f.description} [{f.category.value}, "
                         f"{f.confidence:.0%}; {', '.join(f.evidence_ids)}]")
        lines += [r for r in report.sufficiency.reasons if r.startswith("✗")]
        if report.sufficiency.missing_data:
            lines.append("Missing data: " + "; ".join(report.sufficiency.missing_data))
        g = report.guardrails
        if g and g.model_used:
            lines.append(f"Fact-check: {g.ids_invented}/{g.ids_cited} cited IDs invented, "
                         f"{g.factors_dropped} factor(s) dropped.")
        return "\n".join(lines)
    if style == "kid":
        sure = {"sufficient": "I'm really sure! 🎯",
                "partial": "I'm a little bit sure, but two things could have done it. 🤔",
                "insufficient": "I don't have enough clues yet, so this is only a guess. 🔍"}[v]
        lines = []
        if wc:
            word = "went up" if wc.relative_change >= 0 else "went down"
            lines.append(f"Something in the computer shop got poorly: the {label(wc.metric)} "
                         f"{word} a lot at {wc.change_start[11:16]}, like a fever "
                         f"suddenly going up. 🤒")
        if top:
            lines.append(f"Just before that, this happened: *{top.description}* "
                         "That's most likely what made it poorly, like eating a bad sweet "
                         "right before a tummy ache. 🍬")
        lines.append(sure)
        if fix:
            lines.append(f"To make it better: {fix} 🩹")
        return "\n".join(lines)
    opener = {"sufficient": "I'm sure about this one!",
              "partial": "I'm partly sure: there's more than one possible answer.",
              "insufficient": "I don't have enough clues to be sure yet."}[v]
    lines = [opener]
    if top:
        lines.append(f"{'Main cause' if v != 'insufficient' else 'Best lead'}: {top.description}")
    if fix:
        lines.append(f"What to do first: {fix}")
    if report.sufficiency.missing_data:
        lines.append("More data that would help: " + "; ".join(report.sufficiency.missing_data))
    lines.append("Ask me anything about it, or share more data and I'll look again.")
    return "\n".join(lines)


def _document_summary(report: RCAReport, style: str) -> str:
    v = report.sufficiency.verdict.value
    top = report.contributing_factors[0] if report.contributing_factors else None
    fix = report.actions[0].action if report.actions else None
    if style == "nerd":
        lines = [f"**Verdict: {v}** (score {report.sufficiency.score:.2f}, documents only).",
                 f"What happened: {report.summary}"]
        lines += [f"{f.rank}. {f.description} [{f.category.value}, {f.confidence:.0%}; "
                  f"{', '.join(f.evidence_ids)}]" for f in report.contributing_factors]
        lines += [r for r in report.sufficiency.reasons if r.startswith("✗")]
        g = report.guardrails
        if g and g.quotes_checked:
            lines.append(f"Quote check: {g.quotes_rejected}/{g.quotes_checked} model quotes "
                         "not found in the text and removed.")
        return "\n".join(lines)
    if style == "kid":
        sure = {"sufficient": "I'm really sure! 🎯",
                "partial": "I'm a little bit sure. 🤔",
                "insufficient": "The story doesn't say for sure, so this is a guess. 🔍"}[v]
        lines = [f"Here's the story: {report.summary} 📖"]
        if top:
            lines.append(f"Why? *{top.description}* That's what started the trouble, like "
                         "the first domino that knocks the others over. 🁢")
        lines.append(sure)
        if fix:
            lines.append(f"To make it better: {fix} 🩹")
        return "\n".join(lines)
    opener = {"sufficient": "I'm sure about this one!",
              "partial": "I'm partly sure: the documents don't settle it completely.",
              "insufficient": "The documents don't say clearly what caused it."}[v]
    lines = [opener, f"What happened: {report.summary}"]
    if top:
        lines.append(f"{'Main cause' if v != 'insufficient' else 'Best lead'}: {top.description}")
    if fix:
        lines.append(f"What to do first: {fix}")
    if report.sufficiency.missing_data:
        lines.append("More that would help: " + "; ".join(report.sufficiency.missing_data))
    lines.append("Ask me anything about the documents, or share more and I'll look again.")
    return "\n".join(lines)


def chart_data(metrics: pd.DataFrame, report: RCAReport, max_points: int = 400) -> dict | None:
    """The changed measure over time for the affected part, plus where each clue sits."""
    wc = report.what_changed
    if wc is None:
        return None
    df = _select(metrics, {k: v for k, v in wc.segment.items() if v != "all"})
    series = _aggregate(df, wc.metric).dropna()
    step = max(1, len(series) // max_points)
    series = series.iloc[::step]
    markers = [{"id": e.id, "time": e.timestamp, "source": e.source,
                "text": e.summary.split(" (")[0][:90]}
               for e in report.evidence if e.kind.value == "record" and e.timestamp]
    return {"metric": label(wc.metric), "where": _where(report),
            "times": [str(t) for t in series.index], "values": [float(v) for v in series],
            "change": wc.change_start, "before": wc.baseline_value, "after": wc.current_value,
            "markers": markers}


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
    def __init__(self, client_factory: Callable[[bool], ChatClient | None], catalog=None):
        self.client_factory = client_factory
        self.catalog = catalog

    def load_sample(self, session: Session, seed: int | None = None) -> dict:
        rng = random.Random(seed)
        scenario = rng.choice([s for s in SCENARIOS if s != "no_clear_cause"])
        inc = generate_incident("SAMPLE", scenario, seed=rng.randint(1, 10_000))
        style = (session.style, session.style_chosen)
        session.__init__()
        session.style, session.style_chosen = style
        session.add(Parsed(metrics=inc.metrics, records=inc.records))
        session.uploaded = True
        return {"summary": f"Sample loaded: a table of {len(inc.metrics):,} rows (requests, "
                           f"error rate, latency by service and region) and "
                           f"{len(inc.records)} records.",
                "question": inc.question}

    def set_style(self, session: Session, style: str) -> str | None:
        session.style, session.style_chosen = style, True
        return summary_for(session.report, style) if session.report else None

    def respond(self, session: Session, message: str, use_llm: bool, emit: Emit) -> None:
        message = message.strip()
        guess = None if session.style_chosen else detect_style(message)
        if guess and guess != session.style:
            session.style = guess
            emit("style", {"style": guess, "detected": True})
        pasted = _pasted_data(message, session.known()) if message else None
        if pasted is not None:
            session.add(pasted)
            session.uploaded = True
            emit("stage", {"stage": "collect", "text": "Collecting the evidence you pasted..."})
            emit("say", {"text": f"Got it! I picked up {pasted.summary} from your message."})

        if len(message) >= PASTE_DOC_CHARS and not _looks_like_table(message):
            session.add_document(document_from_text(
                f"pasted text {len(session.documents) + 1}", message))
            emit("say", {"text": f"Thanks! I'll read the text you pasted "
                                 f"({len(message.split())} words) carefully."})

        connected = bool(self.catalog) and not (session.uploaded and session.metrics is not None)
        if session.documents and (session.last_shared == "documents"
                                  or (session.metrics is None and not connected)):
            self._documents(session, message, use_llm, emit)
            return
        if session.metrics is None and not connected:
            if pasted is None and message and not GREETING.match(message) and len(message) > 12:
                self._general(message, use_llm, emit)
            elif pasted is not None:
                emit("say", {"text": "I've kept those clues. Now I need the numbers: click ➕ "
                                     "and upload a table (CSV, Excel or PDF) with a time column "
                                     "and the measure that went wrong."})
            else:
                emit("say", {"text": HELP})
            return

        wants = session.report is None or session.changed or bool(RERUN.search(message))
        if connected and message and (QUESTION_START.match(message) or "?" in message):
            wants = wants or bool(re.search(r"\d|yesterday|today|last ", message))
        if session.metrics is not None and session.report is not None and message:
            mentioned = choose_metric(session.metrics, message)
            wants = wants or (mentioned != session.metric and any(
                t in message.lower() for t in mentioned.split("_") if len(t) > 2))
        if wants:
            if connected and not self._gather(session, message, emit):
                return
            self._investigate(session, message, use_llm, emit)
        elif message:
            self._follow_up(session, message, use_llm, emit)

    def _documents(self, session: Session, message: str, use_llm: bool, emit: Emit) -> None:
        """Investigate the shared documents, or answer a question about them."""
        style = session.style or "simple"
        rerun = session.report is None or session.mode != "documents" or session.changed \
            or bool(RERUN.search(message))
        if not rerun and message:
            emit("stage", {"stage": "think", "text": "Looking through the documents..."})
            answer = answer_from_documents(message, session.documents,
                                           self.client_factory(use_llm), STYLE_INSTRUCTION[style])
            emit("stage", {"stage": "back", "text": "Here you go!"})
            emit("say", {"text": answer})
            return
        asked = [q.strip() for q in re.findall(r"[^.!?\n]*\?", message)]
        question = (asked[-1] if asked else message if 0 < len(message) < 300
                    else "What happened, and what caused it?")

        def on_step(step: str, text: str) -> None:
            emit("stage", {"stage": STAGE_OF_STEP.get(step, "think"), "text": text})

        report = investigate_documents(question, session.documents, self.client_factory(use_llm),
                                       on_step)
        session.report, session.mode, session.changed = report, "documents", False
        emit("stage", {"stage": "back", "text": "Coming back with the answer!"})
        emit("report", {"report": report.model_dump(mode="json"), "chart": None, "style": style})
        emit("say", {"text": summary_for(report, style), "summary": True})

    def _general(self, message: str, use_llm: bool, emit: Emit) -> None:
        """No data shared yet: answer from general knowledge, clearly labelled."""
        client = self.client_factory(use_llm)
        if client is None or not hasattr(client, "chat"):
            emit("say", {"text": HELP})
            return
        emit("stage", {"stage": "think", "text": "Thinking..."})
        try:
            answer = client.chat(message, system=GENERAL_SYSTEM, temperature=0.3).strip()
        except LLMError:
            emit("say", {"text": HELP})
            return
        emit("stage", {"stage": "back", "text": "Here you go!"})
        emit("say", {"text": "*From general knowledge, not from your data:*\n" + answer})

    def _gather(self, session: Session, message: str, emit: Emit) -> bool:
        emit("stage", {"stage": "collect", "text": "Looking through your connected data..."})
        parsed, used, window = self.catalog.gather(message, session.known())
        if parsed.metrics is None or parsed.metrics.empty:
            emit("say", {"text": "I looked through your connected data but found no numbers for "
                                 "that time. Try another date, or upload a file with ➕."})
            return False
        session.metrics, session.records = None, []
        session.add(parsed)
        lo, hi = (w.strftime("%d %b %H:%M") for w in window)
        emit("stage", {"stage": "collect", "text": f"Read {', '.join(used)} from {lo} to {hi}."})
        return True

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
        session.mode = "numbers"
        emit("stage", {"stage": "back", "text": "Coming back with the answer!"})
        emit("report", {"report": report.model_dump(mode="json"),
                        "chart": chart_data(session.metrics, report),
                        "style": session.style or "simple"})
        emit("say", {"text": summary_for(report, session.style or "simple"), "summary": True})

    def _follow_up(self, session: Session, message: str, use_llm: bool, emit: Emit) -> None:
        client = self.client_factory(use_llm)
        style = session.style or "simple"
        if client is None or not hasattr(client, "chat"):
            emit("say", {"text": "I can answer follow-up questions when the AI model is "
                                 "switched on. Here's the short version:\n"
                                 + summary_for(session.report, style)})
            return
        emit("stage", {"stage": "think", "text": "Thinking about your question..."})
        try:
            answer = client.chat(_followup_prompt(session.report, message),
                                 system=FOLLOWUP_SYSTEM + "\n" + STYLE_INSTRUCTION[style],
                                 temperature=0.2)
        except LLMError as exc:
            answer = (f"I couldn't reach the AI model ({exc}). Here's the short version:\n"
                      + summary_for(session.report, style))
        emit("stage", {"stage": "back", "text": "Here you go!"})
        emit("say", {"text": answer.strip()})
