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
from collections.abc import Callable
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
    Verdict,
)
from .sufficiency import (
    CAUSE_GRACE_MIN,
    assess,
    credible_candidates,
    engine_factor,
    find_candidate,
    fit_label,
    rivals_of,
)

MAX_FACTORS = 3

SYSTEM_PROMPT = """You are a careful incident investigator doing root cause analysis.
Rules:
- Use ONLY the numbered evidence you are given. Never invent events, numbers or IDs.
- Every contributing factor must cite the evidence IDs (like "E3") that support it.
- A cause must come before, or at the same time as, the change it explains.
  Alerts and error logs after the change are symptoms, not causes.
- If no evidence explains the change, return an empty list of contributing factors.
- Each record has a "fit" note. Prefer records marked "right time and place". A change
  hours earlier or in a different service/region is usually a red herring.
- If two records are both "right time and place", name both: the data may not tell
  them apart.
- Usually there is ONE main cause. Add a second or third factor only if separate
  evidence clearly supports it.
- Categories: deployment = a new release or version; config_change = a changed setting;
  traffic = more users or requests than usual (e.g. a campaign); dependency = an upstream
  or external service the system calls (API, database, provider) failed or slowed;
  infrastructure = our own servers, network or capacity; data = bad or unusual input data;
  unknown = none of these.
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
                         "minutes": h.minutes_from_change, "record_id": rec["id"],
                         "summary": f"{rec['text']} ({where}; {when}; record {rec['id']}; "
                                    f"fit: {fit_label(h)})",
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


def _clean(reply: dict, evidence: list[dict]
           ) -> tuple[list[dict], list[dict], list[dict], dict]:
    """Guardrails: keep only claims backed by real evidence IDs, and count what was removed."""
    known = {e["id"] for e in evidence}
    by_id = {e["id"]: e for e in evidence}
    stats = {"ids_cited": 0, "ids_invented": 0, "factors_dropped": 0}
    for item in reply.get("contributing_factors", []) + reply.get("ruled_out", []):
        cited = item.get("evidence_ids", [])
        stats["ids_cited"] += len(cited)
        stats["ids_invented"] += sum(i not in known for i in cited)
    factors = []
    for f in reply.get("contributing_factors", [])[:MAX_FACTORS]:
        ids = [i for i in f.get("evidence_ids", []) if i in known]
        if not ids or not f.get("description"):
            stats["factors_dropped"] += 1
            continue
        # A cause must come before the change (or within minutes, e.g. an outage alert).
        # Factors resting only on later records are symptoms, not causes.
        cited_records = [by_id[i] for i in ids if by_id[i]["kind"] == "record"]
        if cited_records and all(e["minutes"] > CAUSE_GRACE_MIN for e in cited_records):
            stats["factors_dropped"] += 1
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
    return factors, ruled_out, actions, stats


def _prefer_credible(factors: list[dict], ruled_out: list[dict], actions: list[dict],
                     hits: list[RecordHit], evidence: list[dict], analysis: ChangeAnalysis):
    """Let the engines overrule a weak pick, and name every equally good candidate.

    A factor must rest on a change that is close in time and in the affected place.
    Factors that don't are moved to "ruled out" and replaced by the engines' best
    candidate. If other changes fit just as well, they are added as competing factors.
    """
    creds = credible_candidates(hits, evidence)
    if not creds:
        return factors, ruled_out, actions, False, 0, False
    cred_ids = {c.evidence_id for c in creds}
    kept = [f for f in factors if cred_ids & set(f["evidence_ids"])]
    dropped = [f for f in factors if f not in kept]
    override = bool(factors) and factors[0] in dropped
    if not kept:
        kept = [engine_factor(creds[0], analysis)]
    for f in dropped:
        ruled_out = [*ruled_out, {
            "hypothesis": f["description"],
            "reason": "It rests on a change that is too early, or in a different "
                      "service/region, to explain a sudden change here.",
            "evidence_ids": f["evidence_ids"],
        }]
    old_rank = {id(f): f["rank"] for f in factors}
    best = next(c for c in creds if c.evidence_id in kept[0]["evidence_ids"]) \
        if any(c.evidence_id in kept[0]["evidence_ids"] for c in creds) else creds[0]
    named = {i for f in kept for i in f["evidence_ids"]}
    added = 0
    for rival in rivals_of(best, creds):
        if rival.evidence_id not in named and len(kept) < MAX_FACTORS:
            f = engine_factor(rival, analysis)
            f["description"] = ("Competing change at the same time and place: "
                                + f["description"])
            f["confidence"] = min(f["confidence"], kept[0]["confidence"], 0.5)
            kept.append(f)
            added += 1
    new_rank = {}
    for i, f in enumerate(kept, start=1):
        if id(f) in old_rank:
            new_rank[old_rank[id(f)]] = i
        f["rank"] = i
    if dropped or added:
        actions = [{**a, "addresses_factors": [new_rank[n] for n in a["addresses_factors"]
                                               if n in new_rank]} for a in actions]
        actions = [a for a in actions if a["addresses_factors"]]
    return kept, ruled_out, actions, override, added, not factors


def investigate(incident_id: str, question: str, metric: str, metrics: pd.DataFrame,
                records: list[dict], client: ChatClient | None, top_k: int = 5,
                on_step: Callable[[str, str], None] | None = None) -> RCAReport:
    """Run the whole investigation. `on_step(step, message)` is told about each stage,
    so a caller (e.g. the web page) can show progress live."""
    def step(name: str, message: str) -> None:
        if on_step is not None:
            on_step(name, message)

    step("numbers", "Looking at the graphs for the moment things changed...")
    analysis = analyze_change(metrics, metric)
    if analysis.detected:
        where = ", ".join(f"{k} {v}" for k, v in analysis.segment.items()) or "everywhere"
        step("numbers_done", f"{metric} jumped {analysis.relative_change:+.0%} at "
             f"{analysis.change_start[11:16]}, in {where}.")
    else:
        step("numbers_done", "No clear jump found in the graphs.")
    step("records", f"Reading {len(records)} records for clues...")
    hits = rank_records(records, analysis, top_k=top_k)
    evidence = build_evidence(analysis, hits)
    step("records_done", f"Found {len(hits)} likely clues; best: {hits[0].record['text']}"
         if hits else "No matching records found.")

    factors: list[dict] = []
    ruled_out: list[dict] = []
    actions: list[dict] = []
    guard = {"model_used": client is not None}
    if analysis.detected and client is not None:
        step("model", "Asking the language model to explain the clues...")
        reply = client.chat_json(build_prompt(question, evidence), llm_reply_schema(),
                                 system=SYSTEM_PROMPT)
        factors, ruled_out, actions, stats = _clean(reply, evidence)
        guard.update(stats)
        step("model_done", f"The model suggested {len(factors)} cause(s).")

    if analysis.detected:
        factors, ruled_out, actions, override, added, fallback = _prefer_credible(
            factors, ruled_out, actions, hits, evidence, analysis)
        guard.update(engine_override=override, rivals_added=added)
        guard["engine_fallback"] = fallback and client is not None
    if analysis.detected and not factors:
        # No usable factor from the model: fall back to the engines' best candidate.
        cand = find_candidate(hits, factors, evidence)
        if cand is not None and cand.evidence_id:
            factors = [engine_factor(cand, analysis)]
            guard["engine_fallback"] = True
    if guard.get("ids_invented") or guard.get("factors_dropped"):
        step("fact_check", f"Fact-check: removed {guard.get('ids_invented', 0)} invented "
             f"clue(s) and {guard.get('factors_dropped', 0)} unsupported cause(s).")
    else:
        step("fact_check", "Fact-check: every cause rests on a real clue.")
    step("judge", "Deciding whether the clues are enough...")
    sufficiency = assess(analysis, hits, factors, evidence)
    step("judge_done", f"Verdict: {sufficiency.verdict.value} (score {sufficiency.score:.2f}).")
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
        sufficiency=sufficiency, actions=actions, guardrails=guard,
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
    g = report.guardrails
    if g and g.model_used:
        out += ["", "## Fact-check", (f"- Evidence IDs cited by the model: {g.ids_cited}, "
                f"invented (removed): {g.ids_invented}"),
                f"- Factors dropped (no real evidence, or symptoms only): {g.factors_dropped}"]
        if g.engine_override:
            out.append("- The model's main factor rested on a change that was too early or in "
                       "another place; the engines' candidate was used instead.")
        if g.rivals_added:
            out.append(f"- Competing changes added so every equally good candidate is named: "
                       f"{g.rivals_added}")
        if g.engine_fallback:
            out.append("- The model gave no usable factor; the main factor comes from the engines.")
    out += ["", "## Evidence"]
    out += [f"- **{e.id}** ({e.kind.value}, {e.source}) {e.summary}" for e in report.evidence]
    return "\n".join(out) + "\n"


def save_report(report: RCAReport, path) -> None:
    from pathlib import Path

    Path(path).write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n")
