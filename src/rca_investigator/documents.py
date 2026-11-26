"""Document mode: investigate incident write-ups, emails, notes or any pasted text.

Not every incident comes with numbers and timestamps. Here CuteBot reads the whole
document in pieces (pages, then sections):

1. **Every piece** is scanned with simple rules for sentences that describe a cause,
   a symptom, an event or an action.
2. The **most relevant pieces** are also read by the language model, which writes down
   the facts with an exact quote from the text.
3. A **quote check** keeps only facts whose quote really appears in the document, so the
   model cannot invent evidence.
4. The model puts the story together from the numbered facts, and **rules** (not the
   model) judge whether the documents are enough to be sure.

Follow-up questions are answered from the most relevant passages, with page references.
"""

from __future__ import annotations

import io
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import PurePath

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .ingest import IngestError
from .investigate import ChatClient, _clean, build_prompt, llm_reply_schema
from .llm import LLMError
from .schema import Guardrails, RCAReport, Sufficiency, Verdict
from .vision import READ_CHARTS, ChartImage, VisionClient, VisionError, find_charts

DOC_TYPES = {".pdf", ".docx", ".txt", ".md", ".log", ".rtf", ".html", ".htm", ".eml"}
CHUNK_CHARS = 1800
MODEL_CHUNKS = 6  # pieces the language model reads closely (all pieces get the rule scan)
MAX_FACTS = 40
FACT_TYPES = ("cause", "symptom", "event", "action", "context", "chart")

CAUSE = re.compile(r"\b(because|due to|caused by|root cause|as a result of|triggered by|led to|"
                   r"resulted in|the cause|was caused|stemmed from|traced (back )?to|"
                   r"originated|introduced|was the reason|responsible for)\b", re.IGNORECASE)
SYMPTOM = re.compile(r"\b(errors?|outage|went down|is down|was down|failed|failing|failures?|"
                     r"slow(er|ness)?|latency|time ?outs?|unavailable|crash(ed|es)?|"
                     r"complain(ed|ts)?|degraded|broken|could not|couldn't|unable|spike[ds]?|"
                     r"dropped|missing|delayed|stuck|declined|returned|reversed|overdrawn|"
                     r"overdraft|charge ?back|insufficient funds|unpaid|bounced|disputed?|"
                     r"fraud\w*|unrecogni[sz]ed|duplicated?|penalty|late (payment|fee)|"
                     r"incorrect|wrong|mistake|faulty|defect\w*|damaged|cancell?ed|"
                     r"breach\w*|incident|issue|problem)\b", re.IGNORECASE)
ACTION = re.compile(r"\b(fixed|rolled back|roll back|rollback|restart(ed)?|revert(ed)?|"
                    r"mitigat\w+|resolved|patch(ed)?|we will|should|plan to|action items?|"
                    r"prevent\w*|follow[- ]up)\b", re.IGNORECASE)
EVENT = re.compile(r"\b(deployed|released|changed|updated|upgraded|migrat\w+|launched|"
                   r"started|enabled|disabled|switched|installed|configured|removed|"
                   r"\d{1,2}:\d{2}|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
                   r"yesterday|this morning|last night)\b", re.IGNORECASE)
CATEGORY_WORDS = [
    ("deployment", r"deploy|release|version|rollout|new build|update[ds]? to v"),
    ("config_change", r"config|setting|feature flag|\bflag\b|parameter|threshold|limit"),
    ("traffic", r"traffic|load|campaign|promotion|spike in (users|requests)|black friday"),
    ("dependency", r"third[- ]party|vendor|provider|upstream|dependency|external|supplier|api"),
    ("infrastructure", (r"server|disk|network|capacity|memory|cpu|hardware|power|database|"
                       r"storage|certificate|dns")),
    ("data", r"\bdata\b|input|file|record|migration|schema|corrupt"),
]
QA_SYSTEM = """You are CuteBot, a friendly incident investigator. Answer the question using
ONLY the passages below and cite pages like [p.2]. If the passages don't answer it, say so.
At most 4 sentences."""
DOC_SYSTEM = """You are a careful incident investigator doing root cause analysis from
documents. The numbered evidence are exact quotes from the user's documents.
Rules:
- Use ONLY the numbered evidence. Cite the IDs (like "E3") behind every factor.
- Separate symptoms (what people saw) from causes (what made it happen).
- A cause must be supported by a quote that states or clearly implies it.
- If the evidence doesn't say what caused it, return an empty list of factors.
- what_happened: one or two plain sentences describing the incident.
- Categories: deployment, config_change, traffic, dependency (an outside service or
  supplier), infrastructure (own servers, network, capacity), data, unknown.
- Be concise and specific."""
FACT_PROMPT = """Read this part of a document and list the facts that matter for finding
out what went wrong. For each fact give its type (cause, symptom, event, action or
context), a short plain statement, and the exact quote copied word for word from the text.
Only use what the text says. Return an empty list if nothing is relevant.

Text (page {page}):
\"\"\"{text}\"\"\""""


def fact_schema() -> dict:
    return {"type": "object", "properties": {"facts": {"type": "array", "maxItems": 8, "items": {
        "type": "object", "properties": {
            "type": {"type": "string", "enum": list(FACT_TYPES)},
            "statement": {"type": "string"}, "quote": {"type": "string"}},
        "required": ["type", "statement", "quote"]}}}, "required": ["facts"]}


@dataclass
class Chunk:
    id: str
    document: str
    page: int
    text: str


@dataclass
class Document:
    name: str
    chunks: list[Chunk] = field(default_factory=list)
    charts: list[ChartImage] = field(default_factory=list)

    @property
    def pages(self) -> int:
        return max((c.page for c in self.chunks), default=0)

    @property
    def words(self) -> int:
        return sum(len(c.text.split()) for c in self.chunks)


def _split(text: str, limit: int = CHUNK_CHARS) -> list[str]:
    """Split text into pieces of about `limit` characters, on paragraph or sentence breaks."""
    pieces, current = [], ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        while len(para) > limit:
            cut = para.rfind(". ", 0, limit)
            cut = cut + 1 if cut > limit // 3 else limit
            pieces.append(para[:cut].strip())
            para = para[cut:].strip()
        if len(current) + len(para) > limit and current:
            pieces.append(current.strip())
            current = ""
        current += para + "\n\n"
    if current.strip():
        pieces.append(current.strip())
    return pieces


def document_from_pages(name: str, pages: list[str], charts: list | None = None) -> Document:
    doc = Document(name, charts=charts or [])
    for number, page in enumerate(pages, start=1):
        for piece in _split(page):
            doc.chunks.append(Chunk(f"{name}#{len(doc.chunks) + 1}", name, number, piece))
    if not doc.chunks and not doc.charts:
        raise IngestError(f"{name} has no readable text. If it's a scan or a picture, I can't "
                          "read it yet; please share the text or the data instead.")
    return doc


def document_from_text(name: str, text: str) -> Document:
    return document_from_pages(name, [text])


def load_document(name: str, data: bytes) -> Document:
    """Text of a PDF (page by page), Word file or text-like file, ready to investigate."""
    suffix = PurePath(name).suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError

        try:
            pages = [_page_text(p) for p in PdfReader(io.BytesIO(data)).pages]
        except (PdfReadError, ValueError) as exc:
            raise IngestError("That PDF couldn't be opened.") from exc
        return document_from_pages(name, pages, find_charts(data, pages))
    if suffix == ".docx":
        import docx

        try:
            d = docx.Document(io.BytesIO(data))
        except Exception as exc:
            raise IngestError("That Word file couldn't be opened.") from exc
        lines = [p.text for p in d.paragraphs]
        for table in d.tables:
            lines += [" | ".join(c.text for c in row.cells) for row in table.rows]
        return document_from_text(name, "\n\n".join(lines))
    text = data.decode("utf-8-sig", errors="replace").replace("﻿", "")
    if suffix in (".html", ".htm"):
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    return document_from_text(name, text)


def _page_text(page) -> str:
    """Page text with table rows kept on one line (falls back to plain extraction)."""
    try:
        text = page.extract_text(extraction_mode="layout") or ""
        text = "\n".join(re.sub(r" {3,}", "   ", ln.rstrip()) for ln in text.splitlines())
        if text.strip():
            return text
    except Exception:  # noqa: BLE001, S110 (older PDFs: plain extraction below)
        pass
    return page.extract_text() or ""


# ---------- what kind of document, and is it about a problem? ----------

KINDS = [
    ("a bank or account statement", (r"statement|balance|sort code|account (number|no)|"
                                    r"transactions?|debit|credit|overdraft|iban")),
    ("an invoice or receipt", r"invoice|receipt|amount due|vat|subtotal|bill to|payment terms"),
    ("an incident report", (r"incident|outage|post[- ]?mortem|root cause|downtime|sev\d|"
                           r"impact|mitigation")),
    ("meeting notes", r"minutes|attendees|agenda|action items?|meeting"),
    ("an email", r"^(from|to|subject|cc):|dear |kind regards|best regards"),
    ("a contract or agreement", r"agreement|contract|party|parties|clause|terms and conditions"),
    ("a report", r"report|summary|findings|analysis"),
]


def document_kind(documents: list[Document]) -> str:
    text = " ".join(c.text for d in documents for c in d.chunks)[:20000]
    best = max((len(re.findall(rule, text, re.IGNORECASE | re.MULTILINE)), kind) for kind, rule in KINDS)
    return best[1] if best[0] >= 2 else "a document"


def describes_problem(documents: list[Document]) -> bool:
    """Does any part say something went wrong, or what caused something?"""
    return any(f["type"] in ("cause", "symptom") for d in documents for c in d.chunks
               for f in rule_facts(c))


MONEY_OR_NUMBER = re.compile(r"[£$€]?\d[\d,]*(?:\.\d+)?%?")
SUMMARY_SYSTEM = """You summarise documents for a busy reader. Use ONLY the document text.
Say what kind of document it is, then give the key points as short bullet points
(important names, dates, amounts and totals, copied exactly). Mention anything unusual.
Do not invent anything. At most 8 bullet points.{hint}"""
SUMMARY_CHARS = 7000


def _unverified_numbers(summary: str, source: str) -> list[str]:
    """Numbers in the summary that don't appear anywhere in the document."""
    plain = re.sub(r"[£$€,\s]", "", source)
    found = []
    for num in MONEY_OR_NUMBER.findall(summary):
        digits = re.sub(r"[£$€,%]", "", num).rstrip(".")
        if len(re.sub(r"\D", "", digits)) >= 2 and digits not in plain:
            found.append(num)
    return found


def summarise_documents(documents: list[Document], client: ChatClient | None,
                        style_hint: str = "", ask: Callable[..., str] | None = None) -> str:
    """A plain summary of the shared documents (numbers checked against the text)."""
    kind = document_kind(documents)
    text = "\n\n".join(f"[{c.document} p.{c.page}]\n{c.text}" for d in documents
                       for c in d.chunks)
    if client is not None and hasattr(client, "chat"):
        try:
            ask = ask or (lambda p, s, t: client.chat(p, system=s, temperature=t))
            summary = ask(f"Document ({kind}):\n{text[:SUMMARY_CHARS]}\n\nSummarise it.",
                          SUMMARY_SYSTEM.format(hint="\n" + style_hint), 0.1).strip()
            missing = _unverified_numbers(summary, text)
            if missing:
                summary += ("\n\n⚠ These numbers aren't written in the document (the AI worked "
                            "them out or misread them), so please double-check: "
                            + ", ".join(dict.fromkeys(missing)))
            if len(text) > SUMMARY_CHARS:
                summary += ("\n\n(It's a long document, so this covers the first part. Ask me "
                            "about any section for details.)")
            return summary
        except LLMError:
            pass
    lines = [ln.strip() for d in documents for c in d.chunks for ln in c.text.splitlines()
             if len(ln.strip()) > 3]
    key = [ln for ln in lines if MONEY_OR_NUMBER.search(ln)][:6] or lines[:6]
    return (f"It looks like {kind}. Key lines:\n"
            + "\n".join(f"• {re.sub(' {2,}', '  ', ln)[:160]}" for ln in key))


# ---------- facts ----------

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[\"'“”‘’`]", "", text)).strip(" .,;:").lower()


def verify_quote(quote: str, text: str) -> bool:
    """True if the quote appears in the text (ignoring spacing, case and quote marks)."""
    q, t = _norm(quote), _norm(text)
    if len(q) < 8:
        return False
    if q in t:
        return True
    match = SequenceMatcher(None, q, t, autojunk=False).find_longest_match(0, len(q), 0, len(t))
    return match.size >= 0.9 * len(q)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip(" -•*\t") for p in parts if len(p.strip()) > 15]


def rule_facts(chunk: Chunk) -> list[dict]:
    """Facts found by simple wording rules (used for every piece, and without the model)."""
    facts = []
    for sentence in _sentences(chunk.text):
        for kind, rule in (("cause", CAUSE), ("action", ACTION), ("symptom", SYMPTOM),
                           ("event", EVENT)):
            if rule.search(sentence):
                facts.append({"type": kind, "statement": sentence, "quote": sentence[:300],
                              "chunk": chunk})
                break
    return facts


def model_facts(chunk: Chunk, client: ChatClient) -> tuple[list[dict], int, int]:
    """Facts the model found in one piece, keeping only quotes found in the text."""
    reply = client.chat_json(FACT_PROMPT.format(page=chunk.page, text=chunk.text), fact_schema())
    kept, checked = [], 0
    for f in reply.get("facts", []):
        if f.get("type") not in FACT_TYPES or not f.get("quote"):
            continue
        checked += 1
        if verify_quote(f["quote"], chunk.text):
            kept.append({**f, "chunk": chunk})
    return kept, checked, checked - len(kept)


def rank_chunks(chunks: list[Chunk], query: str, k: int) -> list[Chunk]:
    """The k pieces most related to the question (and to incident words)."""
    if len(chunks) <= k:
        return chunks
    query = f"{query} cause caused because root error failed outage incident fix"
    matrix = TfidfVectorizer(stop_words="english").fit_transform([query] + [c.text for c in chunks])
    scores = cosine_similarity(matrix[0], matrix[1:]).ravel()
    order = sorted(range(len(chunks)), key=lambda i: -scores[i])[:k]
    return [chunks[i] for i in sorted(order)]


def _dedupe(facts: list[dict]) -> list[dict]:
    seen, out = set(), []
    for f in facts:
        key = _norm(f["quote"])[:120]
        if key not in seen and not any(key in s or s in key for s in seen):
            seen.add(key)
            out.append(f)
    return out


def _category(text: str) -> str:
    for category, words in CATEGORY_WORDS:
        if re.search(words, text, re.IGNORECASE):
            return category
    return "unknown"


# ---------- judging ----------

def assess_documents(evidence: list[dict], factors: list[dict]) -> Sufficiency:
    """Rules for documents: is a cause stated, backed up, and free of competing causes?"""
    reasons: list[str] = []
    missing: list[str] = []
    score = 0.0

    def check(weight: float, value: float, ok: str, bad: str, need: str | None = None):
        nonlocal score
        score += weight * value
        if value >= 0.5:
            reasons.append(f"✓ {ok}")
        else:
            reasons.append(f"✗ {bad}")
            if need:
                missing.append(need)

    by_id = {e["id"]: e for e in evidence}
    cited = [by_id[i] for i in (factors[0]["evidence_ids"] if factors else []) if i in by_id]
    cited_causes = [e for e in cited if e.get("fact_type") == "cause"]
    cited_events = [e for e in cited if e.get("fact_type") == "event"]
    kinds = [e.get("fact_type") for e in evidence]
    if "chart" in kinds:  # a chart shows the problem and when it happened
        kinds += ["symptom", "event"]

    check(0.35, 1.0 if cited_causes else 0.5 if cited_events else 0.0,
          "The documents say what caused it, and the main factor rests on that.",
          "No passage clearly says what caused it.",
          "A statement of what changed or triggered the problem (e.g. from the people who "
          "fixed it)")
    check(0.15, 1.0 if "symptom" in kinds else 0.0,
          f"{kinds.count('symptom')} passage(s) describe the problem itself.",
          "The documents don't describe what went wrong for users or systems.",
          "A description of what users or systems experienced")
    check(0.15, 1.0 if "event" in kinds else 0.0, "The order of events is described.",
          "There is no timeline of what happened when.",
          "A timeline: when it started, what changed, when it was fixed")
    support = {e["chunk_id"] for e in cited if e.get("fact_type") in ("cause", "event", "chart")}
    check(0.15, 1.0 if len(support) >= 2 else 0.5 if support else 0.0,
          "More than one passage backs up the cause." if len(support) >= 2 else
          "One passage backs up the cause.",
          "Nothing backs up the cause.",
          "A second source confirming the cause (logs, a ticket, monitoring data)")
    others = {e["chunk_id"] for e in evidence if e.get("fact_type") == "cause"
              and e not in cited and not (support & {e["chunk_id"]})}
    check(0.10, 1.0 if not others else 0.5 if len(others) == 1 else 0.0,
          "No competing cause is suggested elsewhere." if not others else
          "One other passage suggests a cause too.",
          f"{len(others)} other passages suggest different causes.",
          "Details to rule out the other suggested causes")
    check(0.10, 1.0 if "action" in kinds else 0.0, "Fixes or follow-ups are described.",
          "No fix or follow-up is described.")
    reasons.append("ℹ Based on documents only: no numbers were checked.")

    score = round(min(score, 1.0), 2)
    if not (cited_causes or cited_events):
        score = min(score, 0.4)
    from . import sufficiency as rules

    verdict = (Verdict.SUFFICIENT if score >= rules.SUFFICIENT_AT
               else Verdict.PARTIAL if score >= rules.PARTIAL_AT else Verdict.INSUFFICIENT)
    if verdict != Verdict.INSUFFICIENT and not factors:
        verdict = Verdict.INSUFFICIENT
    return Sufficiency(verdict=verdict, score=score, reasons=reasons,
                       missing_data=list(dict.fromkeys(missing)))


# ---------- the investigation ----------

def _chart_facts(documents: list[Document], vision: VisionClient | None, step) -> tuple[list, int]:
    """Chart captions (always) and, with a vision model, what each chart picture shows."""
    facts, read = [], 0
    for doc in documents:
        for chart in doc.charts:
            if chart.caption:
                facts.append({"type": "chart", "statement": chart.caption, "quote": chart.caption,
                              "chunk": Chunk(f"{doc.name}#chart{chart.page}", doc.name,
                                             chart.page, chart.caption)})
            if vision is None or read >= READ_CHARTS:
                continue
            where = "in the cloud" if vision.where == "cloud" else "on this computer"
            step("doc_chart", f"Looking at the chart on page {chart.page} of {doc.name} "
                              f"({where})...")
            try:
                seen = vision.describe(chart.png, chart.caption)
            except VisionError as exc:
                step("doc_chart", f"I couldn't look at the chart: {exc}. Using its labels only.")
                vision = None
                continue
            read += 1
            facts.append({"type": "chart", "statement": seen, "quote": seen, "seen": True,
                          "chunk": Chunk(f"{doc.name}#chart{chart.page}", doc.name, chart.page,
                                         seen)})
    return facts, read


def investigate_documents(question: str, documents: list[Document], client: ChatClient | None,
                          on_step: Callable[[str, str], None] | None = None,
                          vision: VisionClient | None = None) -> RCAReport:
    def step(name: str, message: str) -> None:
        if on_step is not None:
            on_step(name, message)

    chunks = [c for d in documents for c in d.chunks]
    names = ", ".join(d.name for d in documents)
    step("doc_read", f"Reading every part of {names} ({len(chunks)} pieces)...")
    facts = [f for c in chunks for f in rule_facts(c)]
    checked = rejected = 0
    if client is not None:
        close = rank_chunks(chunks, question, MODEL_CHUNKS)
        for n, chunk in enumerate(close, start=1):
            step("doc_read", f"Reading page {chunk.page} of {chunk.document} closely "
                             f"({n}/{len(close)})...")
            try:
                found, c, r = model_facts(chunk, client)
            except LLMError:
                break
            checked, rejected = checked + c, rejected + r
            facts = found + facts  # the model's facts first, then the rule scan
    found_charts = sum(len(d.charts) for d in documents)
    chart_facts, charts_read = _chart_facts(documents, vision, step) if found_charts else ([], 0)
    facts = _dedupe(chart_facts + facts)
    order = {"cause": 0, "event": 1, "chart": 2, "symptom": 3, "action": 4, "context": 5}
    facts = sorted(facts, key=lambda f: order[f["type"]])[:MAX_FACTS]
    counts = {k: sum(f["type"] == k for f in facts) for k in FACT_TYPES}
    step("doc_facts", f"Found {len(facts)} facts: {counts['cause']} about causes, "
                      f"{counts['symptom']} symptoms, {counts['event']} events, "
                      f"{counts['action']} actions"
                      + (f", {counts['chart']} from charts." if counts["chart"] else "."))
    if checked:
        step("fact_check", f"Fact-check: {checked - rejected} of {checked} quotes were found "
                           f"word for word; {rejected} removed.")

    evidence = [{
        "id": f"E{i}", "kind": "document", "source": f"{f['chunk'].document} p.{f['chunk'].page}",
        "summary": (f"Chart (read from the picture on p.{f['chunk'].page}): {f['quote']}"
                    if f.get("seen") else f"{f['type'].capitalize()}: \"{f['quote']}\""),
        "timestamp": None,
        "fact_type": f["type"], "chunk_id": f["chunk"].id,
    } for i, f in enumerate(facts, start=1)]
    if not evidence:
        evidence = [{"id": "E1", "kind": "document", "source": names, "timestamp": None,
                     "summary": "The documents were read, but no sentence describes a "
                                "problem, cause or action.", "fact_type": "context",
                     "chunk_id": ""}]

    factors, ruled_out, actions, summary = [], [], [], None
    guard = {"model_used": client is not None, "quotes_checked": checked,
             "quotes_rejected": rejected, "charts_found": found_charts,
             "charts_read": charts_read}
    if client is not None and facts:
        step("model", "Putting the story together...")
        schema = llm_reply_schema()
        schema["properties"]["what_happened"] = {"type": "string"}
        schema["required"] = [*schema.get("required", []), "what_happened"]
        try:
            reply = client.chat_json(build_prompt(question, evidence), schema, system=DOC_SYSTEM)
            factors, ruled_out, actions, stats = _clean(reply, evidence)
            guard.update(stats)
            summary = (reply.get("what_happened") or "").strip() or None
        except LLMError as exc:
            step("model_done", f"The language model isn't available ({exc}); using my rules.")
    if not factors:
        best = next((e for e in evidence if e["fact_type"] == "cause"), None)
        if best is not None:
            quote = best["summary"].split(": ", 1)[1].strip('"')
            factors = [{"rank": 1, "description": quote, "category": _category(quote),
                        "confidence": 0.5, "why_chain": [], "evidence_ids": [best["id"]]}]
            guard["engine_fallback"] = client is not None
    if summary is None:
        first = next((e for e in evidence if e["fact_type"] == "symptom"), None)
        summary = first["summary"].split(": ", 1)[1].strip('"') if first else None
    if not actions:
        actions = [{"action": e["summary"].split(": ", 1)[1].strip('"'), "type": "corrective",
                    "priority": "medium", "addresses_factors": [1]}
                   for e in evidence if e["fact_type"] == "action"][:2] if factors else []

    step("judge", "Deciding whether the documents are enough...")
    sufficiency = assess_documents(evidence, factors)
    step("judge_done", f"Verdict: {sufficiency.verdict.value} (score {sufficiency.score:.2f}).")
    if sufficiency.verdict == Verdict.INSUFFICIENT:
        for f in factors:
            f["confidence"] = min(f["confidence"], 0.3)
    return RCAReport(incident_id="DOCS", question=question, summary=summary,
                     contributing_factors=factors, ruled_out=ruled_out, evidence=evidence,
                     sufficiency=sufficiency, actions=actions, guardrails=Guardrails(**guard))


def answer_from_documents(question: str, documents: list[Document], client: ChatClient | None,
                          style_hint: str = "", ask: Callable[..., str] | None = None) -> str:
    """A chat answer about the documents, from the most relevant passages."""
    chunks = rank_chunks([c for d in documents for c in d.chunks], question, 3)
    if client is not None and hasattr(client, "chat"):
        passages = "\n\n".join(f"[p.{c.page} of {c.document}]\n{c.text}" for c in chunks)
        try:
            ask = ask or (lambda p, s, t: client.chat(p, system=s, temperature=t))
            return ask(f"Passages:\n{passages}\n\nQuestion: {question}",
                       QA_SYSTEM + "\n" + style_hint, 0.2).strip()
        except LLMError:
            pass
    words = set(re.findall(r"[a-z]{4,}", question.lower()))
    scored = sorted(((sum(w in s.lower() for w in words), s, c) for c in chunks
                     for s in _sentences(c.text)), key=lambda x: -x[0])
    best = [f"“{s}” [p.{c.page}]" for n, s, c in scored[:2] if n]
    return ("Here's what the documents say:\n" + "\n".join(best)) if best else \
        "I couldn't find anything about that in the documents."
