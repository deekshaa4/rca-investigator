"""Numerical engine: find what changed, when, by how much and where.

Method (deliberately simple and explainable):
1. For every segment (service x region), find the single most likely change point
   in the metric: the split that best separates the series into two flat levels
   (least squared error).
2. Score each split with a two-sample t statistic and the before/after ratio.
3. The segments that changed significantly, at about the same time as the
   strongest one, are the affected segments. Their pattern tells us whether the
   change belongs to one service, one region, or a single service in one region.
4. Related metrics (traffic, errors, latency) are compared before and after the
   same moment, which gives evidence for or against explanations such as a
   traffic spike.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

METRICS = ("requests", "error_rate", "latency_p95_ms")
LABELS = {"requests": "request volume", "error_rate": "error rate", "latency_p95_ms": "p95 latency"}
MIN_SIDE = 12  # at least 1 hour of 5-minute points on each side of a change
MIN_T = 6.0  # minimum t statistic for a significant change
MIN_RATIO = 1.3  # minimum after/before ratio for a significant change
SAME_TIME = pd.Timedelta(minutes=30)  # changes this close together count as one event


@dataclass
class SegmentChange:
    service: str
    region: str
    change_start: pd.Timestamp
    before: float
    after: float
    ratio: float
    t_stat: float


@dataclass
class ChangeAnalysis:
    metric: str
    detected: bool
    change_start: str | None = None
    segment: dict[str, str] = field(default_factory=dict)
    baseline_value: float | None = None
    current_value: float | None = None
    relative_change: float | None = None
    affected: list[SegmentChange] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)


def best_split(x: np.ndarray, min_side: int = MIN_SIDE) -> int | None:
    """Index of the first point after the most likely mean shift, or None if too short."""
    n = len(x)
    if n < 2 * min_side:
        return None
    cs = np.concatenate([[0.0], np.cumsum(x)])
    cs2 = np.concatenate([[0.0], np.cumsum(x * x)])
    k = np.arange(min_side, n - min_side + 1)
    left_sse = cs2[k] - cs[k] ** 2 / k
    right_n = n - k
    right_sse = (cs2[n] - cs2[k]) - (cs[n] - cs[k]) ** 2 / right_n
    return int(k[np.argmin(left_sse + right_sse)])


def _t_stat(before: np.ndarray, after: np.ndarray) -> float:
    se = np.sqrt(before.var(ddof=1) / len(before) + after.var(ddof=1) / len(after))
    return float((after.mean() - before.mean()) / se) if se > 0 else 0.0


def segment_changes(metrics: pd.DataFrame, metric: str) -> list[SegmentChange]:
    """The most likely change point in every segment, strongest first."""
    out = []
    for (service, region), df in metrics.groupby(["service", "region"]):
        df = df.sort_values("timestamp")
        x = df[metric].to_numpy(dtype=float)
        k = best_split(x)
        if k is None:
            continue
        before, after = x[:k], x[k:]
        ratio = after.mean() / before.mean() if before.mean() > 0 else float("inf")
        out.append(
            SegmentChange(
                service=service,
                region=region,
                change_start=pd.Timestamp(df["timestamp"].iloc[k]),
                before=float(before.mean()),
                after=float(after.mean()),
                ratio=float(ratio),
                t_stat=_t_stat(before, after),
            )
        )
    return sorted(out, key=lambda c: c.t_stat, reverse=True)


def _aggregate(df: pd.DataFrame, metric: str) -> pd.Series:
    """Combine segments into one series per timestamp (request-weighted where it matters)."""
    g = df.groupby("timestamp")
    if metric == "requests":
        return g["requests"].sum()
    weighted = (df[metric] * df["requests"]).groupby(df["timestamp"]).sum()
    return weighted / g["requests"].sum()


def _fmt(metric: str, value: float) -> str:
    if metric == "error_rate":
        return f"{value * 100:.2f}%"
    if metric == "latency_p95_ms":
        return f"{value:.0f} ms"
    return f"{value:.0f} per 5 min"


def _describe(segment: dict[str, str]) -> str:
    parts = []
    if "service" in segment:
        parts.append(f"service {segment['service']}")
    if "region" in segment:
        parts.append(f"region {segment['region']}")
    return " in ".join(parts) if parts else "all traffic"


def _summarise_segment(affected: list[SegmentChange], metrics: pd.DataFrame) -> dict[str, str]:
    services = {c.service for c in affected}
    regions = {c.region for c in affected}
    all_services = set(metrics["service"].unique())
    all_regions = set(metrics["region"].unique())
    if len(affected) == 1:
        return {"service": affected[0].service, "region": affected[0].region}
    if len(services) == 1 and regions == all_regions:
        return {"service": next(iter(services))}
    if len(regions) == 1 and services == all_services:
        return {"region": next(iter(regions))}
    return {"service": ",".join(sorted(services)), "region": ",".join(sorted(regions))}


def _select(metrics: pd.DataFrame, segment: dict[str, str]) -> pd.DataFrame:
    df = metrics
    for key, value in segment.items():
        df = df[df[key].isin(value.split(","))]
    return df


def analyze_change(metrics: pd.DataFrame, metric: str) -> ChangeAnalysis:
    """Find the main upward change in `metric` and describe it with evidence."""
    all_changes = segment_changes(metrics, metric)
    changes = [c for c in all_changes if c.ratio > 1]
    if not changes or changes[0].t_stat < MIN_T or changes[0].ratio < MIN_RATIO:
        strongest = f" (strongest ratio {changes[0].ratio:.2f})" if changes else ""
        return ChangeAnalysis(
            metric=metric,
            detected=False,
            findings=[{
                "source": f"metrics:{metric}",
                "summary": f"No significant increase in {LABELS[metric]} in any segment"
                f"{strongest}.",
                "timestamp": None,
            }],
        )

    top = changes[0]
    affected = [
        c for c in changes
        if c.t_stat >= MIN_T and c.ratio >= MIN_RATIO
        and abs(c.change_start - top.change_start) <= SAME_TIME
    ]
    change_start = pd.Series([c.change_start for c in affected]).median().floor("5min")
    t0 = change_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    segment = _summarise_segment(affected, metrics)

    group = _select(metrics, segment)
    series = {m: _aggregate(group, m) for m in METRICS}
    is_after = {m: s.index >= t0 for m, s in series.items()}
    before_v = {m: float(s[~is_after[m]].mean()) for m, s in series.items()}
    after_v = {m: float(s[is_after[m]].mean()) for m, s in series.items()}
    rel = (after_v[metric] - before_v[metric]) / before_v[metric]

    desc = _describe(segment)
    findings = [{
        "source": f"metrics:{metric}",
        "summary": f"{LABELS[metric].capitalize()} for {desc} rose from "
        f"{_fmt(metric, before_v[metric])} to {_fmt(metric, after_v[metric])} "
        f"({rel:+.0%}), with a change point at {t0}.",
        "timestamp": t0,
    }]

    if len(all_changes) > len(affected):
        others = metrics[~metrics.index.isin(group.index)]
        o_after = others["timestamp"] >= t0
        o_ratio = (others.loc[o_after].groupby(["service", "region"])[metric].mean()
                   / others.loc[~o_after].groupby(["service", "region"])[metric].mean())
        findings.append({
            "source": f"metrics:{metric}",
            "summary": f"The change is concentrated in {desc}: {len(affected)} of "
            f"{len(all_changes)} service/region segments changed; the other "
            f"segments stayed flat (largest after/before ratio {o_ratio.max():.2f}).",
            "timestamp": t0,
        })

    for other in METRICS:
        if other == metric:
            continue
        r = (after_v[other] - before_v[other]) / before_v[other]
        verb = "rose" if r > 0.15 else "fell" if r < -0.15 else "stayed about the same"
        findings.append({
            "source": f"metrics:{other}",
            "summary": f"At the same time, {LABELS[other]} for {desc} {verb} "
            f"({_fmt(other, before_v[other])} before, {_fmt(other, after_v[other])} after, "
            f"{r:+.0%}).",
            "timestamp": t0,
        })

    return ChangeAnalysis(
        metric=metric,
        detected=True,
        change_start=t0,
        segment=segment,
        baseline_value=before_v[metric],
        current_value=after_v[metric],
        relative_change=rel,
        affected=affected,
        findings=findings,
    )
