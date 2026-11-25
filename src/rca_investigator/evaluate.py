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
        "twist": truth.get("twist", "none"),
        **_guardrail_counts(report),
    }


def _guardrail_counts(report: RCAReport) -> dict:
    g = report.guardrails
    if g is None or not g.model_used:
        return {"ids_cited": None, "ids_invented": None, "factors_dropped": None,
                "engine_fallback": None}
    return {"ids_cited": g.ids_cited, "ids_invented": g.ids_invented,
            "factors_dropped": g.factors_dropped, "engine_fallback": g.engine_fallback}


def summarise(rows: list[dict]) -> dict[str, float]:
    df = pd.DataFrame(rows)
    expl = df[df["category_ok"].notna()]
    out = {
        "verdict correct": df["verdict_ok"].mean(),
        "segment correct": df["segment_ok"].mean(),
        "top cause category correct": expl["category_ok"].astype(bool).mean() if len(expl) else 0,
        "true cause record cited by top factor": expl["cause_cited"].astype(bool).mean()
        if len(expl) else 0,
    }
    if "ids_cited" in df and df["ids_cited"].notna().any():
        llm = df[df["ids_cited"].notna()]
        cited = llm["ids_cited"].sum()
        out["evidence IDs invented by the model"] = llm["ids_invented"].sum() / cited if cited else 0
        out["reports with a factor dropped"] = (llm["factors_dropped"] > 0).mean()
        out["reports using the engine fallback"] = llm["engine_fallback"].astype(bool).mean()
    return out


def breakdown(rows: list[dict], by: str) -> pd.DataFrame:
    """Scores per group (e.g. per scenario or twist), as counts like '9/10'."""
    df = pd.DataFrame(rows)

    def frac(col: pd.Series) -> str:
        col = col.dropna().astype(bool)
        return f"{col.sum()}/{len(col)}" if len(col) else "-"

    table = df.groupby(by).agg(
        incidents=("incident", "count"),
        verdict=("verdict_ok", frac),
        segment=("segment_ok", frac),
        category=("category_ok", frac),
        cause_cited=("cause_cited", frac),
    )
    return table
