"""Text engine: find the records that best explain a detected change.

Each record gets a score from four simple, explainable signals:

- text:    TF-IDF similarity between the record and a query built from the change
           (metric words, affected service/region, and traffic words if traffic rose)
- time:    causes usually come shortly before a change (up to a few hours);
           symptoms and alerts come shortly after
- segment: records about the affected service/region (or about everything) count more
- source:  change events (deploys, config changes) are likelier causes than log lines,
           which are usually symptoms
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .analyze import ChangeAnalysis

METRIC_WORDS = {
    "error_rate": "error errors exception fail failed failing 503 5xx upstream crash",
    "latency_p95_ms": "latency slow timeout pool exhausted waiting connection",
    "requests": "traffic volume requests load",
}
TRAFFIC_WORDS = "traffic volume campaign sale load spike marketing scaling"
SOURCE_WEIGHT = {
    "deploys": 1.0,
    "config_changes": 1.0,
    "alerts": 0.8,
    "tickets": 0.7,
    "logs": 0.4,
}
LOOK_BACK_MIN = 6 * 60  # causes can come up to 6 hours before the change
LOOK_AHEAD_MIN = 60  # symptoms and alerts up to 1 hour after
DECAY_BEFORE_MIN = 180
DECAY_AFTER_MIN = 30


@dataclass
class RecordHit:
    record: dict
    score: float
    minutes_from_change: float
    reasons: list[str] = field(default_factory=list)


def _record_text(rec: dict) -> str:
    return " ".join(str(rec.get(k) or "") for k in ("source", "service", "region", "text"))


def build_query(analysis: ChangeAnalysis) -> str:
    parts = [METRIC_WORDS.get(analysis.metric, analysis.metric)]
    for value in analysis.segment.values():
        parts.append(value.replace(",", " "))
    traffic = next((f for f in analysis.findings if f["source"] == "metrics:requests"), None)
    if traffic and " rose " in traffic["summary"]:
        parts.append(TRAFFIC_WORDS)
    return " ".join(parts)


def _segment_match(rec: dict, segment: dict[str, str]) -> float:
    """1.0 if the record concerns the affected segment (or everything), else low."""
    for key, value in segment.items():
        rec_value = rec.get(key)
        if rec_value is not None and rec_value not in value.split(","):
            return 0.2
    return 1.0


def _time_score(minutes: float) -> float:
    """minutes = record time minus change time (negative means before the change)."""
    if minutes < -LOOK_BACK_MIN or minutes > LOOK_AHEAD_MIN:
        return 0.0
    if minutes <= 0:
        return math.exp(minutes / DECAY_BEFORE_MIN)
    return math.exp(-minutes / DECAY_AFTER_MIN)


def _mentions_time_near(text: str, t0: pd.Timestamp, tolerance_min: int = 15) -> bool:
    """True if the text names a clock time (HH:MM) within tolerance of the change."""
    change = t0.hour * 60 + t0.minute
    for hh, mm in re.findall(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text):
        diff = abs(int(hh) * 60 + int(mm) - change)
        if min(diff, 1440 - diff) <= tolerance_min:
            return True
    return False


def rank_records(records: list[dict], analysis: ChangeAnalysis, top_k: int = 5) -> list[RecordHit]:
    """Records most likely to explain the change, best first."""
    if not analysis.detected or not records:
        return []
    texts = [_record_text(r) for r in records]
    query = build_query(analysis)
    tfidf = TfidfVectorizer().fit(texts + [query])
    sims = cosine_similarity(tfidf.transform([query]), tfidf.transform(texts))[0]
    t0 = pd.Timestamp(analysis.change_start)

    hits = []
    for rec, sim in zip(records, sims):
        minutes = (pd.Timestamp(rec["timestamp"]) - t0).total_seconds() / 60
        time_s = _time_score(minutes)
        if time_s == 0:
            continue
        announces = _mentions_time_near(rec["text"], t0)
        if announces:
            time_s = 1.0  # e.g. "campaign goes live at 10:25", announced hours ahead
        seg_s = _segment_match(rec, analysis.segment)
        src_s = SOURCE_WEIGHT.get(rec["source"], 0.5)
        score = time_s * seg_s * src_s * (0.5 + float(sim))
        reasons = [
            f"{abs(minutes):.0f} min {'before' if minutes <= 0 else 'after'} the change",
            "matches the affected segment" if seg_s == 1 else "different service/region",
            f"source '{rec['source']}'",
            f"text similarity {sim:.2f}",
        ]
        if announces:
            reasons.append("names a time within 15 min of the change")
        hits.append(RecordHit(rec, round(score, 4), round(minutes, 1), reasons))
    return sorted(hits, key=lambda h: h.score, reverse=True)[:top_k]


def timeline(records: list[dict], analysis: ChangeAnalysis) -> list[dict]:
    """Records about the affected segment in the window around the change, in time order."""
    if not analysis.detected:
        return []
    t0 = pd.Timestamp(analysis.change_start)
    out = []
    for rec in records:
        minutes = (pd.Timestamp(rec["timestamp"]) - t0).total_seconds() / 60
        if -LOOK_BACK_MIN <= minutes <= LOOK_AHEAD_MIN and _segment_match(rec, analysis.segment) == 1:
            out.append({**rec, "minutes_from_change": round(minutes, 1)})
    return out
