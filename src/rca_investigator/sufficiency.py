"""Evidence-sufficiency check: is the evidence enough for a reliable conclusion?

The verdict comes from transparent rules, not from the language model's opinion.
Each check passes, partly passes or fails, and the reasons and missing data are
reported so a reader can see exactly why the verdict was reached.

Checks (weight):
- timing (0.35):        a change event (deploy, config change, ticket, alert) happened just
                        before the change, or names the change time
- segment (0.15):       that event concerns the affected service/region
- symptoms (0.15):      records after the change (errors, alerts) agree with the numbers
- metrics agree (0.10): related metrics fit the explanation (a traffic cause needs a
                        traffic rise; any other cause should not coincide with one)
- distinct (0.10):      no competing change event lines up just as well (if one does,
                        the verdict is at most partial)
- cited (0.15):         the main contributing factor actually rests on that event

Verdict: score >= 0.7 sufficient, >= 0.45 partial, otherwise insufficient. Without a
change event that is close in time AND concerns the affected service/region there is
no credible candidate cause, so the verdict is insufficient whatever the other checks say.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .analyze import ChangeAnalysis
from .records import RecordHit
from .schema import Sufficiency, Verdict

CHANGE_SOURCES = {"deploys", "config_changes", "tickets", "alerts"}
CAUSE_GRACE_MIN = 5  # a cause may first be reported a few minutes after the change
CLOSE_MIN = 30  # a change event within 30 minutes before counts as fully on time
SUFFICIENT_AT = 0.7
PARTIAL_AT = 0.45
MIN_TIMING = 0.5  # below this there is no credible candidate cause

UPSTREAM_WORDS = re.compile(r"upstream|dependency|provider|status page|\b50[234]\b", re.IGNORECASE)
SOURCE_CATEGORY = {"deploys": "deployment", "config_changes": "config_change"}


@dataclass
class Candidate:
    hit: RecordHit
    evidence_id: str | None
    timing: float


def _timing(hit: RecordHit) -> float:
    m = hit.minutes_from_change
    if any("names a time" in r for r in hit.reasons):
        return 1.0
    if m > CAUSE_GRACE_MIN:
        return 0.0
    if m > 0:
        return 0.8  # reported just after the change, e.g. an outage alert
    if m >= -CLOSE_MIN:
        return 1.0
    return math.exp((m + CLOSE_MIN) / 60)  # fades over the hours before


def _could_be_cause(rec: dict) -> bool:
    """Alerts usually report symptoms ("high error rate"); only those naming an
    upstream failure describe a possible cause."""
    if rec["source"] != "alerts":
        return True
    return bool(UPSTREAM_WORDS.search(rec["text"]))


def _candidates(hits: list[RecordHit], evidence: list[dict]) -> list[Candidate]:
    eid_by_record = {e.get("record_id"): e["id"] for e in evidence if e.get("record_id")}
    out = [
        Candidate(h, eid_by_record.get(h.record["id"]), _timing(h))
        for h in hits if h.record["source"] in CHANGE_SOURCES and _could_be_cause(h.record)
    ]
    return [c for c in out if c.timing > 0]


def _segment_ok(hit: RecordHit) -> bool:
    return "matches the affected segment" in hit.reasons


def _traffic_rose(analysis: ChangeAnalysis) -> bool:
    return any(f["source"] == "metrics:requests" and " rose " in f["summary"]
               for f in analysis.findings)


def find_candidate(hits: list[RecordHit], factors: list[dict],
                   evidence: list[dict]) -> Candidate | None:
    """The change event most likely to be the cause; prefer the one the top factor cites."""
    cands = _candidates(hits, evidence)
    if not cands:
        return None
    if factors:
        cited = set(factors[0]["evidence_ids"])
        for c in cands:
            if c.evidence_id in cited:
                return c
    return max(cands, key=lambda c: (c.timing * (1 if _segment_ok(c.hit) else 0.3), c.hit.score))


def engine_factor(candidate: Candidate, analysis: ChangeAnalysis) -> dict:
    """A factor built from the engines alone, used when the model gives none."""
    rec = candidate.hit.record
    category = SOURCE_CATEGORY.get(rec["source"], "unknown")
    text = rec["text"].lower()
    if rec["source"] == "tickets" and _traffic_rose(analysis):
        category = "traffic"
    elif rec["source"] == "alerts" and "upstream" in text:
        category = "dependency"
    m = candidate.hit.minutes_from_change
    when = f"{abs(m):.0f} min {'before' if m <= 0 else 'after'}"
    return {
        "rank": 1,
        "description": f"{rec['text']} ({when} the change, found by the engines).",
        "category": category,
        "confidence": round(candidate.timing * (1 if _segment_ok(candidate.hit) else 0.3), 2),
        "why_chain": [],
        "evidence_ids": [candidate.evidence_id],
    }


def assess(analysis: ChangeAnalysis, hits: list[RecordHit], factors: list[dict],
           evidence: list[dict]) -> Sufficiency:
    if not analysis.detected:
        return Sufficiency(verdict=Verdict.INSUFFICIENT, score=0.0,
                           reasons=["No significant change was found in the data."],
                           missing_data=["A clearer description of what changed and when."])

    cand = find_candidate(hits, factors, evidence)
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

    if cand is None:
        check(0.35, 0, "", "No deploy, config change, ticket or alert lines up with the change.",
              "Deploy and config-change history for the affected segment")
        timing = 0.0
    else:
        timing = cand.timing
        m = cand.hit.minutes_from_change
        when = f"{abs(m):.0f} min {'before' if m <= 0 else 'after'} the change"
        check(0.35, timing, f"A change event ({cand.hit.record['source']}) lines up in time "
              f"({when}).", f"The closest change event is {when}, too far to be convincing.",
              "Change records from the hour before the change")
        check(0.15, 1.0 if _segment_ok(cand.hit) else 0.0,
              "It concerns the affected service/region.",
              "It concerns a different service/region than the one that changed.",
              "Change records for the affected service/region")

    symptoms = [h for h in hits if 0 < h.minutes_from_change <= 60 and _segment_ok(h)
                and h.record["source"] in {"logs", "alerts"}]
    check(0.15, 1.0 if symptoms else 0.0,
          f"{len(symptoms)} log/alert record(s) after the change agree with the numbers.",
          "No logs or alerts from the affected segment confirm the problem.",
          "Error logs or traces from the affected segment after the change")

    top_category = factors[0]["category"] if factors else None
    rose = _traffic_rose(analysis)
    if top_category == "traffic":
        check(0.10, 1.0 if rose else 0.0, "Request volume rose, as a traffic cause requires.",
              "A traffic cause is claimed, but request volume did not rise.")
    else:
        check(0.10, 0.0 if rose else 1.0, "Request volume stayed steady, ruling out a traffic "
              "spike.", "Request volume also rose, so a traffic explanation is still open.",
              "Traffic source breakdown (campaigns, bots, partners)")

    rivals: list[Candidate] = []
    if cand is not None:
        rivals = [c for c in _candidates(hits, evidence)
                  if c is not cand and c.hit.record["id"] != cand.hit.record["id"]
                  and c.timing >= 0.8 * timing and _segment_ok(c.hit)]
        check(0.10, 0.0 if rivals else 1.0, "No competing change event fits as well.",
              f"{len(rivals)} other change event(s) fit about as well.",
              "Details to tell the competing changes apart (e.g. a rollback test)")
        cited = bool(factors) and cand.evidence_id in factors[0]["evidence_ids"]
        check(0.15, 1.0 if cited else 0.0, "The main factor rests on this event.",
              "The main factor does not rest on this event.")

    score = round(min(score, 1.0), 2)
    credible = cand is not None and timing >= MIN_TIMING and _segment_ok(cand.hit)
    if not credible:
        score = min(score, round(PARTIAL_AT - 0.05, 2))
    verdict = (Verdict.SUFFICIENT if score >= SUFFICIENT_AT
               else Verdict.PARTIAL if score >= PARTIAL_AT else Verdict.INSUFFICIENT)
    if verdict == Verdict.SUFFICIENT and rivals:
        verdict = Verdict.PARTIAL
        reasons.append("✗ Two or more changes fit equally well, so the cause cannot be confirmed.")
    if verdict != Verdict.INSUFFICIENT and not factors:
        verdict = Verdict.INSUFFICIENT
        reasons.append("✗ No contributing factor could be stated.")
    return Sufficiency(verdict=verdict, score=score, reasons=reasons,
                       missing_data=list(dict.fromkeys(missing)))
