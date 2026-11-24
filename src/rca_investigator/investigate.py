"""The investigator: turns engine findings into a cited RCA report.

Division of work, so that a small local model is enough:

1. Python gathers the facts: the numerical engine finds what changed and the
   text engine ranks the records. Each fact becomes numbered evidence (E1, E2, ...).
2. The language model only reasons over that evidence: it names the contributing
   factors with a "5 Whys" chain, rules out alternatives and proposes actions,
   citing evidence IDs. Its reply is constrained to a JSON schema.
3. Python checks the reply (guardrails): citations to evidence that does not
   exist are removed, factors left without evidence are dropped, and the final
   report must pass the RCAReport validation.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

import pandas as pd

from .analyze import ChangeAnalysis, analyze_change
from .records import RecordHit, rank_records
from .schema import (
    ActionType,
    ChangeSummary,
    FactorCategory,
    Priority,
    RCAReport,
    Sufficiency,
    Verdict,
)

MAX_FACTORS = 3
CAUSE_GRACE_MIN = 5  # minutes after the change a cause may still be first reported
CHANGE_SOURCES = {"deploys", "config_changes", "tickets", "alerts"}

SYSTEM_PROMPT = """You are a careful incident investigator doing root cause analysis.
Rules:
- Use ONLY the numbered evidence you are given. Never invent events, numbers or IDs.
- Every contributing factor must cite the evidence IDs (like "E3") that support it.
- A cause must come before, or at the same time as, the change it explains.
  Alerts and error logs after the change are symptoms, not causes.
- If no evidence explains the change, return an empty list of contributing factors.
- Be concise and specific."""


class ChatClient(Protocol):
    def chat_json(self, prompt: str, json_schema: dict, system: str | None = None) -> Any: ...


def llm_reply_schema() -> dict:
    """The small JSON shape the model must reply with."""
    ids = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "properties": {
            "contributing_factors": {
                "type": "array",
                "maxItems": MAX_FACTORS,
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "category": {"type": "string", "enum": [c.value for c in FactorCategory]},
                        "confidence": {"type": "number"},
                        "why_chain": {"type": "array", "items": {"type": "string"}},
                        "evidence_ids": ids,
                    },
                    "required": ["description", "category", "confidence", "why_chain",
                                 "evidence_ids"],
                },
            },
            "ruled_out": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "hypothesis": {"type": "string"},
                        "reason": {"type": "string"},
                        "evidence_ids": ids,
                    },
                    "required": ["hypothesis", "reason", "evidence_ids"],
                },
            },
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "type": {"type": "string", "enum": [a.value for a in ActionType]},
                        "priority": {"type": "string", "enum": [p.value for p in Priority]},
                        "factor_number": {"type": "integer"},
                    },
                    "required": ["action", "type", "priority", "factor_number"],
                },
            },
        },
        "required": ["contributing_factors", "ruled_out", "actions"],
    }


def build_evidence(analysis: ChangeAnalysis, hits: list[RecordHit]) -> list[dict]:
    """Number every fact: metric findings first, then ranked records."""
    evidence = []
    for f in analysis.findings:
        evidence.append({"kind": "metric", "source": f["source"], "summary": f["summary"],
                         "timestamp": f["timestamp"]})
    for h in hits:
        rec = h.record
        when = f"{abs(h.minutes_from_change):.0f} min {'before' if h.minutes_from_change <= 0 else 'after'} the change"
        where = ", ".join(v for v in (rec.get("service"), rec.get("region")) if v) or "all"
        evidence.append({"kind": "record", "source": rec["source"],
                         "minutes": h.minutes_from_change,
                         "summary": f"{rec['text']} ({where}; {when}; record {rec['id']})",
                         "timestamp": rec["timestamp"]})
    for i, e in enumerate(evidence, start=1):
        e["id"] = f"E{i}"
    return evidence


def build_prompt(question: str, evidence: list[dict]) -> str:
    lines = [f"Question: {question}", "", "Evidence:"]
    lines += [f"{e['id']} [{e['kind']}, {e['source']}] {e['summary']}" for e in evidence]
    lines += [
        "",
        "Tasks:",
        (f"1. contributing_factors: up to {MAX_FACTORS}, most likely first. For each: a one-sentence "
        "description, a category, a confidence from 0 to 1, a why_chain of 3 to 5 short steps "
        "from the symptom to the root cause, and the evidence_ids that support it."),
        ("2. ruled_out: other plausible explanations the evidence argues against, with the reason "
        "and evidence_ids."),
        ("3. actions: one corrective action (fix it now) and one or two preventive actions "
        "(stop it happening again). factor_number is the 1-based position of the factor it "
        "addresses."),
    ]
    return "\n".join(lines)


def preliminary_sufficiency(analysis: ChangeAnalysis, hits: list[RecordHit],
                            n_factors: int) -> Sufficiency:
    """A simple first version; the full evidence-sufficiency check comes later."""
    if not analysis.detected:
        return Sufficiency(verdict=Verdict.INSUFFICIENT, score=0.0,
                           reasons=["No significant change was found in the data."],
                           missing_data=["A clearer description of what changed and when."])
    causes = [h for h in hits if h.record["source"] in CHANGE_SOURCES and h.score >= 0.3]
    if causes and n_factors:
        return Sufficiency(
            verdict=Verdict.SUFFICIENT, score=round(min(1.0, causes[0].score + 0.3), 2),
            reasons=[(f"A change event ({causes[0].record['source']}) matches the affected "
                     f"segment and timing ({'; '.join(causes[0].reasons[:2])}).")],
        )
    return Sufficiency(
        verdict=Verdict.INSUFFICIENT, score=round(hits[0].score if hits else 0.0, 2),
        reasons=[("No deploy, config change, ticket or alert lines up with the affected "
                 "segment at the time of the change.")],
        missing_data=["Deploy and config history for the affected segment",
                      "Logs or traces from the affected segment around the change"],
    )


def _clean(reply: dict, evidence: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Guardrails: keep only claims backed by real evidence IDs."""
    known = {e["id"] for e in evidence}
    by_id = {e["id"]: e for e in evidence}
    factors = []
    for f in reply.get("contributing_factors", [])[:MAX_FACTORS]:
        ids = [i for i in f.get("evidence_ids", []) if i in known]
        if not ids or not f.get("description"):
            continue
        # A cause must come before the change (or within minutes, e.g. an outage alert).
        # Factors resting only on later records are symptoms, not causes.
        cited_records = [by_id[i] for i in ids if by_id[i]["kind"] == "record"]
        if cited_records and all(e["minutes"] > CAUSE_GRACE_MIN for e in cited_records):
            continue
        category = f.get("category")
        if category not in {c.value for c in FactorCategory}:
            category = FactorCategory.UNKNOWN.value
        factors.append({
            "rank": len(factors) + 1,
            "description": f["description"],
            "category": category,
            "confidence": min(1.0, max(0.0, float(f.get("confidence", 0.5)))),
            "why_chain": [s for s in f.get("why_chain", []) if s][:5],
            "evidence_ids": ids,
        })
    ruled_out = [
        {"hypothesis": r["hypothesis"], "reason": r["reason"],
         "evidence_ids": [i for i in r.get("evidence_ids", []) if i in known]}
        for r in reply.get("ruled_out", []) if r.get("hypothesis") and r.get("reason")
    ]
    ranks = {f["rank"] for f in factors}
    actions = []
    for a in reply.get("actions", []):
        if not a.get("action") or not factors:
            continue
        n = a.get("factor_number", 1)
        actions.append({
            "action": a["action"],
            "type": a.get("type") if a.get("type") in {t.value for t in ActionType} else "preventive",
            "priority": a.get("priority") if a.get("priority") in {p.value for p in Priority} else "medium",
            "addresses_factors": [n] if n in ranks else [1],
        })
    return factors, ruled_out, actions


def investigate(incident_id: str, question: str, metric: str, metrics: pd.DataFrame,
                records: list[dict], client: ChatClient | None, top_k: int = 5) -> RCAReport:
    analysis = analyze_change(metrics, metric)
    hits = rank_records(records, analysis, top_k=top_k)
    evidence = build_evidence(analysis, hits)

    factors: list[dict] = []
    ruled_out: list[dict] = []
    actions: list[dict] = []
    if analysis.detected and client is not None:
        reply = client.chat_json(build_prompt(question, evidence), llm_reply_schema(),
                                 system=SYSTEM_PROMPT)
        factors, ruled_out, actions = _clean(reply, evidence)

    sufficiency = preliminary_sufficiency(analysis, hits, len(factors))
    if sufficiency.verdict == Verdict.INSUFFICIENT:
        # Without enough evidence, present factors as unconfirmed rather than as the answer.
        for f in factors:
            f["confidence"] = min(f["confidence"], 0.3)

    what_changed = None
    if analysis.detected:
        what_changed = ChangeSummary(
            metric=metric, segment=analysis.segment, change_start=analysis.change_start,
            baseline_value=analysis.baseline_value, current_value=analysis.current_value,
            relative_change=round(analysis.relative_change, 4),
            evidence_ids=[e["id"] for e in evidence if e["kind"] == "metric"][:2],
        )
    return RCAReport(
        incident_id=incident_id, question=question, what_changed=what_changed,
        contributing_factors=factors, ruled_out=ruled_out, evidence=evidence,
        sufficiency=sufficiency, actions=actions,
    )


def to_markdown(report: RCAReport) -> str:
    out = [f"# {report.incident_id}: {report.question}", ""]
    wc = report.what_changed
    out.append("## What changed")
    if wc:
        where = ", ".join(f"{k} {v}" for k, v in wc.segment.items()) or "all traffic"
        out.append(f"{wc.metric} for {where} went from {wc.baseline_value:.4g} to "
                   f"{wc.current_value:.4g} ({wc.relative_change:+.0%}) starting "
                   f"{wc.change_start}. [{', '.join(wc.evidence_ids)}]")
    else:
        out.append("No significant change was found.")
    out += ["", (f"## Verdict: {report.sufficiency.verdict.value} "
                f"(score {report.sufficiency.score:.2f})")]
    out += [f"- {r}" for r in report.sufficiency.reasons]
    if report.sufficiency.missing_data:
        out.append("- Data that would help: " + "; ".join(report.sufficiency.missing_data))
    confirmed = report.sufficiency.verdict != Verdict.INSUFFICIENT
    out += ["", "## Why it happened" if confirmed else "## Possible leads (not confirmed)"]
    if not report.contributing_factors:
        out.append("No contributing factor is supported by the evidence.")
    for f in report.contributing_factors:
        out.append(f"{f.rank}. **{f.description}** ({f.category.value}, confidence "
                   f"{f.confidence:.0%}) [{', '.join(f.evidence_ids)}]")
        out += [f"   - Why: {step}" for step in f.why_chain]
    if report.ruled_out:
        out += ["", "## Ruled out"]
        out += [f"- {r.hypothesis}: {r.reason} [{', '.join(r.evidence_ids)}]"
                for r in report.ruled_out]
    if report.actions:
        out += ["", "## Actions"]
        out += [f"- ({a.type.value}, {a.priority.value}) {a.action}" for a in report.actions]
    out += ["", "## Evidence"]
    out += [f"- **{e.id}** ({e.kind.value}, {e.source}) {e.summary}" for e in report.evidence]
    return "\n".join(out) + "\n"


def save_report(report: RCAReport, path) -> None:
    from pathlib import Path

    Path(path).write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n")
