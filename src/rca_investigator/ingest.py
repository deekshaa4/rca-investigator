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


def frame_to_parsed(df: pd.DataFrame, context: str = "") -> Parsed:
    """`context` (e.g. a table name like "deploy_log") helps sort records into kinds."""
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
        return _records_from_frame(df, time_col, text, service, region, context)
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


def _records_from_frame(df, time_col, text, service, region, context="") -> Parsed:
    by_name = guess_source(context.replace("_", " ")) if context else "logs"
    source = _find([c for c in df.columns if c not in {time_col, text}], SOURCE_NAMES)
    stamps = _iso(df[time_col])
    records = []
    for i, row in df.iterrows():
        if pd.isna(stamps[i]) or pd.isna(row[text]):
            continue
        body = str(row[text])
        hint = f"{row[source]} {body}" if source else body
        kind = by_name if by_name != "logs" else guess_source(hint)
        rec = {"timestamp": stamps[i], "source": kind, "text": body}
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


IMAGE_HELP = ("I can't read pictures of charts yet. Please upload the numbers behind the chart "
              "(most tools can export them as CSV or Excel).")
BINARY_ONLY = {
    ".png": IMAGE_HELP, ".jpg": IMAGE_HELP, ".jpeg": IMAGE_HELP, ".gif": IMAGE_HELP,
    ".webp": IMAGE_HELP, ".heic": IMAGE_HELP, ".svg": IMAGE_HELP,
    ".xls": "Old-style .xls files can't be read. Please save it as .xlsx or CSV.",
    ".numbers": "Numbers files can't be read. Please export it as CSV or Excel (.xlsx).",
    ".doc": "Old-style .doc files can't be read. Please save it as .docx, PDF or text.",
    ".zip": "Please unzip the folder and upload the files inside it.",
}
NUMBER = re.compile(r"^-?\d+(?:[.,]\d+)?%?$")


def _combine(parts: list[Parsed]) -> Parsed:
    tables = [p.metrics for p in parts if p.metrics is not None]
    metrics = None
    if tables:
        metrics = (pd.concat(tables, ignore_index=True)
                   .groupby(["timestamp", "service", "region"], as_index=False)
                   .mean(numeric_only=True))
    records = [r for p in parts for r in p.records]
    return Parsed(metrics=metrics, records=records,
                  summary=" ".join(p.summary for p in parts if p.summary))


def _table_from_text(text: str) -> pd.DataFrame | None:
    """Rows like '2026-05-01 14:00  2.1  120' (e.g. a table inside a PDF) as a DataFrame."""
    rows, header = [], None
    for line in text.splitlines():
        match = STAMP.match(line.strip())
        rest = line.strip()[match.end():] if match else ""
        cells = [c for c in re.split(r"[\s,;|]+", rest) if c]
        if match and cells and all(NUMBER.match(c) for c in cells):
            rows.append([match.group(1)] + [float(c.rstrip("%").replace(",", ".")) for c in cells])
        elif not rows and line.strip():
            header = [c for c in re.split(r"[\s,;|]{2,}|\t|,|;|\|", line.strip()) if c]
    if len(rows) < 24 or len({len(r) for r in rows}) != 1:
        return None
    width = len(rows[0]) - 1
    names = header[-width:] if header and len(header) >= width else [
        f"value_{i}" for i in range(1, width + 1)]
    return pd.DataFrame(rows, columns=["timestamp", *names])


def _read_document_text(text: str, known: dict | None) -> Parsed:
    """Text from a PDF or Word file: a table of numbers and/or dated record lines."""
    parts = []
    table = _table_from_text(text)
    if table is not None:
        parts.append(frame_to_parsed(table))
    numeric_rows = {ln for ln in text.splitlines()
                    if table is not None and STAMP.match(ln.strip())
                    and all(NUMBER.match(c) for c in re.split(r"[\s,;|]+",
                            ln.strip()[STAMP.match(ln.strip()).end():]) if c)}
    records = text_to_records("\n".join(ln for ln in text.splitlines()
                                        if ln not in numeric_rows), known)
    if records:
        parts.append(Parsed(records=records, summary=_records_summary(records)))
    if not parts:
        raise IngestError("I read the document but found no table of numbers and no lines with "
                          "a date and time. Records need a date and time on each line.")
    return _combine(parts)


def read_file(name: str, data: bytes, known: dict[str, set[str]] | None = None) -> Parsed:
    """Read any uploaded file: CSV/TSV/JSON/text, Excel (.xlsx), PDF or Word (.docx)."""
    suffix = PurePath(name).suffix.lower()
    if suffix in BINARY_ONLY:
        raise IngestError(BINARY_ONLY[suffix])
    if suffix in (".xlsx", ".xlsm"):
        try:
            sheets = pd.read_excel(io.BytesIO(data), sheet_name=None)
        except Exception as exc:
            raise IngestError("That Excel file couldn't be opened.") from exc
        parts, first_error = [], None
        for sheet in sheets.values():
            if sheet.dropna(how="all").empty:
                continue
            try:
                parts.append(frame_to_parsed(sheet))
            except IngestError as exc:
                first_error = first_error or exc
        if not parts:
            raise first_error or IngestError("That Excel file is empty.")
        return _combine(parts)
    if suffix == ".pdf":
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError

        try:
            pages = PdfReader(io.BytesIO(data)).pages
            text = "\n".join(page.extract_text() or "" for page in pages)
        except (PdfReadError, ValueError) as exc:
            raise IngestError("That PDF couldn't be opened.") from exc
        if not text.strip():
            raise IngestError("That PDF has no readable text (it may be a scanned image). "
                              "Please upload the data as CSV, Excel or text instead.")
        return _read_document_text(text, known)
    if suffix == ".docx":
        import docx

        try:
            doc = docx.Document(io.BytesIO(data))
        except Exception as exc:
            raise IngestError("That Word file couldn't be opened.") from exc
        lines = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            lines += ["\t".join(cell.text for cell in row.cells) for row in table.rows]
        return _read_document_text("\n".join(lines), known)
    if data[:4] in (b"%PDF", b"PK\x03\x04"):
        raise IngestError("That file looks like a PDF or Office file but its name doesn't say "
                          "so. Please keep the .pdf, .xlsx or .docx ending.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = data.decode("latin-1")
        except UnicodeDecodeError as exc:  # pragma: no cover
            raise IngestError("I couldn't read that file as text.") from exc
    text = text.replace("\ufeff", "")
    if "\x00" in text:
        raise IngestError("I can't read that kind of file. Try CSV, Excel, PDF, Word or text.")
    return read_text(name or "upload.txt", text, known)


def read_text(name: str, text: str, known: dict[str, set[str]] | None = None) -> Parsed:
    """Read one uploaded file (by its name and text content) or a pasted message."""
    suffix = PurePath(name).suffix.lower()
    if suffix in BINARY_ONLY:
        raise IngestError(BINARY_ONLY[suffix])
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
