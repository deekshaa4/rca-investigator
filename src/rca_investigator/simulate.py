"""Synthetic incident generator.

Creates software-service incidents with a known, injected root cause, so the
investigator can be scored against the truth. Each incident has:

- metrics.csv    requests, error rate and p95 latency per service and region, every 5 minutes
- records.jsonl  deploy notes, config changes, alerts, tickets and log lines
- incident.json  the question to investigate (what the investigator sees)
- truth.json     the real cause (hidden from the investigator, used for scoring)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

STEP_MINUTES = 5
HOURS = 48

# service: (base requests per 5 minutes, base p95 latency in ms, upstream dependency)
SERVICES = {
    "checkout": (300, 220, "payments-api"),
    "search": (900, 140, "search-cluster"),
    "catalog": (600, 120, "catalog-db"),
    "auth": (400, 90, "identity-db"),
}
REGIONS = {"eu-west": 1.0, "us-east": 1.3, "ap-south": 0.6}
BASE_ERROR_RATE = 0.004

TWISTS = ("red_herring_other", "red_herring_early", "missing_cause", "rival_change", "none")
SCENARIOS = ("bad_deploy", "config_change", "traffic_spike", "dependency_outage", "no_clear_cause")
METRIC_LABELS = {"error_rate": "error rate", "latency_p95_ms": "p95 latency"}

ROUTINE_TICKETS = [
    "Customer asks how to download an invoice.",
    "Request to add a new admin user to the dashboard.",
    "Question about API rate limits for a partner integration.",
    "Feature request: dark mode for the account page.",
    "Customer reports a typo on the help page.",
]
ROUTINE_LOGS = [
    "INFO cache warmed in 1.8s",
    "INFO nightly backup completed",
    "INFO certificate check passed",
    "WARN slow query 1.2s on report endpoint (single occurrence)",
    "INFO autoscaler: no change",
]


@dataclass
class Incident:
    incident_id: str
    question: str
    metric: str
    metrics: pd.DataFrame
    records: list[dict]
    truth: dict


class _Builder:
    """Holds baseline traffic and the effects injected on top of it."""

    def __init__(self, rng: np.random.Generator, start: datetime):
        self.rng = rng
        n = HOURS * 60 // STEP_MINUTES
        self.times = pd.date_range(start, periods=n, freq=f"{STEP_MINUTES}min")
        hours = (self.times.hour + self.times.minute / 60).to_numpy()
        daily = 1 + 0.35 * np.sin(2 * np.pi * (hours - 9) / 24)
        self.segments = {}
        for service, (requests, _, _) in SERVICES.items():
            for region, factor in REGIONS.items():
                self.segments[(service, region)] = {
                    "load": requests * factor * daily,
                    "err": np.full(n, BASE_ERROR_RATE * rng.uniform(0.7, 1.3)),
                    "lat": np.ones(n),
                }
        self._records: list[tuple[datetime, dict, bool]] = []
        self.drop_causes = False  # "missing_cause" twist: the cause was never recorded
        self.noise = 1.0

    def inject(self, t0, services, regions, load=1.0, err=1.0, lat=1.0):
        after = (self.times >= t0).astype(float)
        for (s, r), seg in self.segments.items():
            if s in services and r in regions:
                seg["load"] = seg["load"] * (1 + (load - 1) * after)
                seg["err"] = seg["err"] * (1 + (err - 1) * after)
                seg["lat"] = seg["lat"] * (1 + (lat - 1) * after)

    def record(self, ts, source, text, service=None, region=None, cause=False):
        if cause and self.drop_causes:
            return
        rec = {"source": source, "service": service, "region": region, "text": text}
        self._records.append((ts, rec, cause))

    def records(self) -> tuple[list[dict], list[str]]:
        ordered = sorted(self._records, key=lambda x: x[0])
        out, cause_ids = [], []
        for i, (ts, rec, cause) in enumerate(ordered, start=1):
            rid = f"R{i:03d}"
            out.append({"id": rid, "timestamp": _iso(ts), **rec})
            if cause:
                cause_ids.append(rid)
        return out, cause_ids

    def metrics(self) -> pd.DataFrame:
        frames = []
        for (service, region), seg in self.segments.items():
            requests = self.rng.poisson(seg["load"])
            rate = np.clip(seg["err"] * self.rng.lognormal(0, 0.15 * self.noise, len(requests)), 0, 1)
            errors = self.rng.binomial(requests, rate)
            base_latency = SERVICES[service][1]
            latency = base_latency * seg["lat"] * self.rng.lognormal(0, 0.06 * self.noise, len(requests))
            frames.append(
                pd.DataFrame(
                    {
                        "timestamp": [_iso(t) for t in self.times],
                        "service": service,
                        "region": region,
                        "requests": requests,
                        "error_rate": np.round(errors / np.maximum(requests, 1), 5),
                        "latency_p95_ms": np.round(latency, 1),
                    }
                )
            )
        return pd.concat(frames).sort_values(["timestamp", "service", "region"], ignore_index=True)


def _iso(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")


def _minutes(m: float) -> timedelta:
    return timedelta(minutes=float(m))


def _add_routine_noise(b: _Builder, t0: datetime, start: datetime) -> None:
    """Everyday records unrelated to the incident, kept away from the change time."""
    rng = b.rng
    count = int(rng.integers(12, 20))
    added = 0
    while added < count:
        ts = start + _minutes(rng.uniform(0, HOURS * 60))
        if abs((ts - t0).total_seconds()) < 45 * 60:
            continue
        service = str(rng.choice(list(SERVICES)))
        region = str(rng.choice(list(REGIONS)))
        kind = rng.integers(3)
        if kind == 0:
            version = f"v{rng.integers(1, 5)}.{rng.integers(0, 30)}"
            b.record(ts, "deploys", f"Deployed {service} {version} to {region} (routine release)",
                     service, region)
        elif kind == 1:
            b.record(ts, "tickets", str(rng.choice(ROUTINE_TICKETS)), service, region)
        else:
            b.record(ts, "logs", f"{service}: {rng.choice(ROUTINE_LOGS)}", service, region)
        added += 1


def _apply_twist(b: _Builder, twist: str, scenario: str, t0: datetime, service: str,
                 region: str, segment: dict[str, str]) -> None:
    """Add a misleading or competing change event."""
    rng = b.rng
    version = f"v{rng.integers(1, 9)}.{rng.integers(0, 30)}"
    same_s = segment.get("service") or str(rng.choice(list(SERVICES)))
    same_r = segment.get("region") or str(rng.choice(list(REGIONS)))
    if twist == "red_herring_other":
        # A change elsewhere at almost the same time: tempting, but the wrong place.
        other_s = str(rng.choice([s for s in SERVICES if s != service]))
        other_r = str(rng.choice([r for r in REGIONS if r != region]))
        b.record(t0 - _minutes(rng.uniform(1, 5)), "deploys",
                 f"Deployed {other_s} {version} to {other_r}", other_s, other_r)
    elif twist == "red_herring_early":
        # A change in the right place, but hours too early to explain a sudden shift.
        b.record(t0 - _minutes(rng.uniform(150, 300)), "deploys",
                 f"Deployed {same_s} {version} to {same_r}", same_s, same_r)
    elif twist == "rival_change":
        # A second change in the same place at the same time: the data cannot tell them apart.
        if scenario == "config_change":
            b.record(t0 - _minutes(rng.uniform(1, 3)), "deploys",
                     f"Deployed {same_s} {version} to {same_r}", same_s, same_r)
        else:
            b.record(t0 - _minutes(rng.uniform(1, 3)), "config_changes",
                     f"Changed {same_s} feature flag new_ui_flow to 50% in {same_r}",
                     same_s, same_r)


def generate_incident(incident_id: str, scenario: str, seed: int, twist: str = "none",
                      noise: float = 1.0) -> Incident:
    """One incident. `twist` makes it harder (see TWISTS); `noise` scales metric noise."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}; choose from {SCENARIOS}")
    if twist not in TWISTS:
        raise ValueError(f"unknown twist {twist!r}; choose from {TWISTS}")
    if scenario == "no_clear_cause" and twist in ("missing_cause", "rival_change"):
        twist = "red_herring_other" if twist == "missing_cause" else "red_herring_early"
    rng = np.random.default_rng(seed)
    start = datetime(2026, 3, 1, tzinfo=timezone.utc) + timedelta(days=int(rng.integers(0, 25)))
    t0 = start + _minutes(STEP_MINUTES * int(rng.integers(26 * 12, 40 * 12)))
    b = _Builder(rng, start)
    b.noise = noise
    b.drop_causes = twist == "missing_cause"
    service = str(rng.choice(list(SERVICES)))
    region = str(rng.choice(list(REGIONS)))
    all_regions = list(REGIONS)
    dependency = SERVICES[service][2]

    if scenario == "bad_deploy":
        metric, category, verdict = "error_rate", "deployment", "sufficient"
        segment = {"service": service, "region": region}
        b.inject(t0, [service], [region], err=rng.uniform(5, 10))
        version = f"v{rng.integers(2, 6)}.{rng.integers(0, 30)}"
        b.record(t0 - _minutes(rng.uniform(1, 4)), "deploys",
                 f"Deployed {service} {version} to {region}", service, region, cause=True)
        for _ in range(3):
            b.record(t0 + _minutes(rng.uniform(1, 40)), "logs",
                     f"{service}: ERROR NullPointerException in RequestHandler.serialize "
                     f"({version})", service, region)
        b.record(t0 + _minutes(10), "alerts", f"High error rate on {service} in {region}",
                 service, region)

    elif scenario == "config_change":
        metric, category, verdict = "latency_p95_ms", "config_change", "sufficient"
        segment = {"service": service}
        b.inject(t0, [service], all_regions, lat=rng.uniform(2, 3.5), err=1.5)
        b.record(t0 - _minutes(rng.uniform(1, 3)), "config_changes",
                 f"Changed {service} db.pool_size from 50 to 5 (all regions)", service, None,
                 cause=True)
        for r in all_regions:
            b.record(t0 + _minutes(rng.uniform(2, 30)), "logs",
                     f"{service}: WARN connection pool exhausted, waiting for a free connection",
                     service, r)
        b.record(t0 + _minutes(15), "alerts", f"p95 latency above SLO on {service}", service, None)

    elif scenario == "traffic_spike":
        metric, category, verdict = "latency_p95_ms", "traffic", "sufficient"
        segment = {"region": region}
        b.inject(t0, list(SERVICES), [region], load=rng.uniform(2.5, 4), lat=rng.uniform(1.6, 2.2),
                 err=2)
        b.record(t0 - _minutes(rng.uniform(120, 300)), "tickets",
                 f"Marketing: flash sale campaign goes live in {region} at {t0:%H:%M} UTC",
                 None, region, cause=True)
        b.record(t0 + _minutes(12), "alerts", f"Request volume 3x normal in {region}", None, region)
        b.record(t0 + _minutes(20), "logs", "autoscaler: scaling out, 4 new instances requested",
                 None, region)

    elif scenario == "dependency_outage":
        metric, category, verdict = "error_rate", "dependency", "sufficient"
        segment = {"service": service}
        b.inject(t0, [service], all_regions, err=rng.uniform(8, 15), lat=1.8)
        b.record(t0 + _minutes(rng.uniform(1, 5)), "alerts",
                 f"Upstream {dependency} returning HTTP 503 for {service}", service, None,
                 cause=True)
        for r in all_regions:
            b.record(t0 + _minutes(rng.uniform(1, 25)), "logs",
                     f"{service}: ERROR upstream {dependency} timeout after 3 retries", service, r)
        b.record(t0 + _minutes(30), "tickets",
                 f"{dependency} status page: investigating degraded performance", service, None)

    else:  # no_clear_cause
        metric, category, verdict = "error_rate", "unknown", "insufficient"
        segment = {"service": service, "region": region}
        b.inject(t0, [service], [region], err=rng.uniform(1.8, 2.5))

    if twist != "none":
        _apply_twist(b, twist, scenario, t0, service, region, segment)
        if twist == "missing_cause":
            verdict = "insufficient"
        elif twist == "rival_change":
            verdict = "partial"
    _add_routine_noise(b, t0, start)
    records, cause_ids = b.records()
    question = f"Why did the {METRIC_LABELS[metric]} go up on {t0:%d %B %Y}?"
    truth = {
        "scenario": scenario,
        "category": category,
        "metric": metric,
        "segment": segment,
        "change_start": _iso(t0),
        "cause_record_ids": cause_ids,
        "expected_verdict": verdict,
        "twist": twist,
    }
    return Incident(incident_id, question, metric, b.metrics(), records, truth)


def generate_dataset(n: int, seed: int = 42, hard: bool = False) -> list[Incident]:
    """n incidents, cycling through the scenarios so each is equally represented.

    With hard=True every scenario also cycles through the twists, and metric noise is higher.
    """
    out = []
    for i in range(n):
        scenario = SCENARIOS[i % len(SCENARIOS)]
        twist = TWISTS[(i // len(SCENARIOS)) % len(TWISTS)] if hard else "none"
        out.append(generate_incident(f"INC-{i + 1:03d}", scenario, seed * 1000 + i, twist=twist,
                                     noise=1.6 if hard else 1.0))
    return out


def save_incident(incident: Incident, out_dir: str | Path) -> Path:
    folder = Path(out_dir) / incident.incident_id
    folder.mkdir(parents=True, exist_ok=True)
    incident.metrics.to_csv(folder / "metrics.csv", index=False)
    with open(folder / "records.jsonl", "w") as f:
        f.writelines(json.dumps(rec) + "\n" for rec in incident.records)
    meta = {
        "incident_id": incident.incident_id,
        "question": incident.question,
        "metric": incident.metric,
        "window_start": incident.metrics["timestamp"].iloc[0],
        "window_end": incident.metrics["timestamp"].iloc[-1],
    }
    (folder / "incident.json").write_text(json.dumps(meta, indent=2) + "\n")
    (folder / "truth.json").write_text(json.dumps(incident.truth, indent=2) + "\n")
    return folder


def load_incident(folder: str | Path) -> tuple[dict, pd.DataFrame, list[dict]]:
    """Load what the investigator may see: question, metrics and records (not the truth)."""
    folder = Path(folder)
    meta = json.loads((folder / "incident.json").read_text())
    metrics = pd.read_csv(folder / "metrics.csv")
    with open(folder / "records.jsonl") as f:
        records = [json.loads(line) for line in f if line.strip()]
    return meta, metrics, records
