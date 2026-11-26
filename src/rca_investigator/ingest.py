"""Turn uploaded files and pasted text into the shape the engines use.

Two kinds of data:
- a **table of numbers** (CSV/TSV/JSON): a time column plus one or more numeric
  measures, optionally split by service and region columns.
- **records** (CSV/JSON with a text column, or plain text/log lines that start with a
  date and time): deploys, setting changes, alerts, tickets and logs.

Column names are matched loosely ("time", "date", "app", "zone", "message", ...), so
most exports work without editing.
"""

from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field
from pathlib import PurePath

import pandas as pd

TIME_NAMES = ("timestamp", "time", "datetime", "date", "ts", "@timestamp", "created_at",
              "created", "event_time", "when")
SERVICE_NAMES = ("service", "app", "application", "component", "system", "host", "api")
REGION_NAMES = ("region", "zone", "location", "datacenter", "dc", "environment", "env", "site")
COUNT_NAMES = ("requests", "count", "volume", "traffic", "calls", "hits", "transactions")
TEXT_NAMES = ("text", "message", "msg", "description", "summary", "event", "details", "log",
              "title", "note", "notes")
SOURCE_NAMES = ("source", "type", "kind", "category")

STAMP = re.compile(
    r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)")
SOURCE_RULES = [
    ("deploys", re.compile(r"deploy|release|rolled? ?out|rollout|\bv\d+\.\d+", re.IGNORECASE)),
    ("config_changes", re.compile(r"config|setting|feature flag|\bflag\b|parameter|"
                                  r"changed .* (to|from)|timeout set|limit set", re.IGNORECASE)),
    ("alerts", re.compile(r"\balert|alarm|pager|firing|triggered|status page", re.IGNORECASE)),
    ("tickets", re.compile(r"ticket|customer|complain|support|campaign|marketing|promo|"
                           r"newsletter|launch", re.IGNORECASE)),
]


class IngestError(ValueError):
    """The data could not be understood; the message says what is needed."""


@dataclass
class Parsed:
    metrics: pd.DataFrame | None = None
    records: list[dict] = field(default_factory=list)
    summary: str = ""


def guess_source(text: str) -> str:
    for source, rule in SOURCE_RULES:
        if rule.search(text):
            return source
    return "logs"


def _iso(values: pd.Series) -> pd.Series:
    stamps = pd.to_datetime(values, utc=True, errors="coerce", format="mixed")
    return stamps.dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _find(columns: list[str], names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in columns:
            return name
    for col in columns:  # e.g. "service_name", "request_count"
        if any(name in col for name in names):
            return col
    return None


def _time_column(df: pd.DataFrame) -> str | None:
    col = _find(list(df.columns), TIME_NAMES)
    if col is not None:
        return col
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            parsed = pd.to_datetime(df[col], utc=True, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.9:
                return col
    return None


def _text_column(df: pd.DataFrame, skip: set[str]) -> str | None:
    col = _find([c for c in df.columns if c not in skip], TEXT_NAMES)
    if col is not None:
        return col
    texts = [c for c in df.columns if c not in skip and not pd.api.types.is_numeric_dtype(df[c])]
    if not texts:
        return None
    longest = max(texts, key=lambda c: df[c].astype(str).str.len().mean())
    return longest if df[longest].astype(str).str.len().mean() > 20 else None


def _clean_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_") or "value"


def frame_to_parsed(df: pd.DataFrame) -> Parsed:
    df = df.rename(columns=_clean_name)
    df = df.loc[:, ~df.columns.duplicated()]
    time_col = _time_column(df)
    if time_col is None:
        raise IngestError("I couldn't find a date/time column. Please include one, "
                          "for example a column called 'timestamp'.")
    skip = {time_col}
    service = _find([c for c in df.columns if c not in skip], SERVICE_NAMES)
    region = _find([c for c in df.columns if c not in skip | {service}], REGION_NAMES)
    numeric = [c for c in df.columns if c not in skip
               and pd.api.types.is_numeric_dtype(df[c])]
    text = _text_column(df, skip | {service, region} - {None})
    if text is not None and len(numeric) <= 1:
        return _records_from_frame(df, time_col, text, service, region)
    if not numeric:
        raise IngestError("I found a time column but no numbers to measure. A table needs "
                          "at least one numeric column, such as an error rate or latency.")
    return _metrics_from_frame(df, time_col, numeric, service, region)


def _metrics_from_frame(df, time_col, numeric, service, region) -> Parsed:
    count = _find(numeric, COUNT_NAMES)
    out = pd.DataFrame({"timestamp": _iso(df[time_col])})
    out["service"] = df[service].astype(str) if service else "all"
    out["region"] = df[region].astype(str) if region else "all"
    out["requests"] = df[count].astype(float) if count else 1.0
    for col in numeric:
        if col != count and col not in ("service", "region", "requests"):
            out[col] = df[col].astype(float)
    out = out.dropna(subset=["timestamp"])
    if out.empty:
        raise IngestError("None of the dates in the time column could be read.")
    out = (out.groupby(["timestamp", "service", "region"], as_index=False).mean(numeric_only=True)
           .sort_values(["service", "region", "timestamp"]).reset_index(drop=True))
    measures = [c for c in out.columns if c not in ("timestamp", "service", "region")
                and not (c == "requests" and count is None)]
    parts = [(f"{len(out):,} rows from {out['timestamp'].min()[:16]} to "
             f"{out['timestamp'].max()[:16]}"), "measures: " + ", ".join(measures)]
    if service or region:
        parts.append(f"{out.groupby(['service', 'region']).ngroups} service/region groups")
    return Parsed(metrics=out, summary="Table of numbers: " + "; ".join(parts) + ".")


def _records_from_frame(df, time_col, text, service, region) -> Parsed:
    source = _find([c for c in df.columns if c not in {time_col, text}], SOURCE_NAMES)
    stamps = _iso(df[time_col])
    records = []
    for i, row in df.iterrows():
        if pd.isna(stamps[i]) or pd.isna(row[text]):
            continue
        body = str(row[text])
        hint = f"{row[source]} {body}" if source else body
        rec = {"timestamp": stamps[i], "source": guess_source(hint), "text": body}
        if service and pd.notna(row[service]):
            rec["service"] = str(row[service])
        if region and pd.notna(row[region]):
            rec["region"] = str(row[region])
        records.append(rec)
    if not records:
        raise IngestError("I couldn't read any dated records from that file.")
    return Parsed(records=records, summary=_records_summary(records))


def _records_summary(records: list[dict]) -> str:
    counts = pd.Series([r["source"] for r in records]).value_counts()
    kinds = ", ".join(f"{n} {k.replace('_', ' ')}" for k, n in counts.items())
    return f"{len(records)} records ({kinds})."


def text_to_records(text: str, known: dict[str, set[str]] | None = None) -> list[dict]:
    """Lines that contain a date and time become records; other lines are ignored."""
    known = known or {}
    records = []
    for line in text.splitlines():
        match = STAMP.search(line)
        if not match:
            continue
        stamp = _iso(pd.Series([match.group(1)]))[0]
        if pd.isna(stamp):
            continue
        body = (line[:match.start()] + line[match.end():]).strip(" -|:,[]\t") or line.strip()
        rec = {"timestamp": stamp, "source": guess_source(body), "text": body}
        lowered = body.lower()
        for key in ("service", "region"):
            hit = next((v for v in sorted(known.get(key, ()), key=len, reverse=True)
                        if v != "all" and v.lower() in lowered), None)
            if hit:
                rec[key] = hit
        records.append(rec)
    return records


def _looks_like_table(text: str) -> bool:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) < 3:
        return False
    sep = "\t" if "\t" in lines[0] else ","
    width = lines[0].count(sep)
    return width >= 1 and all(ln.count(sep) == width for ln in lines[1:6])


def read_text(name: str, text: str, known: dict[str, set[str]] | None = None) -> Parsed:
    """Read one uploaded file (by its name and text content) or a pasted message."""
    suffix = PurePath(name).suffix.lower()
    if suffix in (".xlsx", ".xls", ".numbers"):
        raise IngestError("Spreadsheet files can't be read directly. Please save it as CSV "
                          "(File > Export or Save As > CSV) and upload that.")
    if suffix in (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".webp"):
        raise IngestError("I can't read pictures or PDFs of charts. Please upload the numbers "
                          "behind the chart as a CSV file (most tools can export one).")
    if suffix in (".json", ".jsonl", ".ndjson"):
        stripped = text.strip()
        try:
            rows = (json.loads(stripped) if stripped.startswith("[")
                    else [json.loads(ln) for ln in stripped.splitlines() if ln.strip()])
        except json.JSONDecodeError as exc:
            raise IngestError(f"That JSON file couldn't be read ({exc.msg}).") from exc
        return frame_to_parsed(pd.DataFrame(rows))
    if suffix in (".csv", ".tsv") or (suffix not in (".txt", ".log", ".md")
                                      and _looks_like_table(text)):
        try:
            df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
        except (pd.errors.ParserError, ValueError) as exc:
            raise IngestError("That table couldn't be read. Is it a CSV file?") from exc
        return frame_to_parsed(df)
    records = text_to_records(text, known)
    if not records:
        raise IngestError("I couldn't find any lines with a date and time. Each record "
                          "line should include one, e.g. '2026-03-02 14:05 Deployed v2.3'.")
    return Parsed(records=records, summary=_records_summary(records))
