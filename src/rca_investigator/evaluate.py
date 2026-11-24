"""Score investigation reports against the known truth of generated incidents."""

from __future__ import annotations

import re

import pandas as pd

from .schema import RCAReport

RECORD_REF = re.compile(r"record (R\d+)")


def cited_record_ids(report: RCAReport, factor_rank: int = 1) -> set[str]:
    """Record IDs behind the evidence a given factor cites."""
    factor = next((f for f in report.contributing_factors if f.rank == factor_rank), None)
    if factor is None:
        return set()
    by_id = {e.id: e for e in report.evidence}
    ids = set()
    for eid in factor.evidence_ids:
        ids.update(RECORD_REF.findall(by_id[eid].summary))
    return ids


def score_report(report: RCAReport, truth: dict) -> dict:
    top = report.contributing_factors[0] if report.contributing_factors else None
    explainable = bool(truth["cause_record_ids"])
    return {
        "incident": report.incident_id,
        "scenario": truth["scenario"],
        "expected": truth["expected_verdict"],
        "verdict": report.sufficiency.verdict.value,
        "verdict_ok": report.sufficiency.verdict.value == truth["expected_verdict"],
        "segment_ok": bool(report.what_changed)
        and report.what_changed.segment == truth["segment"],
        "top_category": top.category.value if top else "-",
        "category_ok": (top is not None and top.category.value == truth["category"])
        if explainable else None,
        "cause_cited": bool(set(truth["cause_record_ids"]) & cited_record_ids(report))
        if explainable else None,
        "n_factors": len(report.contributing_factors),
    }


def summarise(rows: list[dict]) -> dict[str, float]:
    df = pd.DataFrame(rows)
    expl = df[df["category_ok"].notna()]
    return {
        "verdict correct": df["verdict_ok"].mean(),
        "segment correct": df["segment_ok"].mean(),
        "top cause category correct": expl["category_ok"].astype(bool).mean() if len(expl) else 0,
        "true cause record cited by top factor": expl["cause_cited"].astype(bool).mean()
        if len(expl) else 0,
    }
