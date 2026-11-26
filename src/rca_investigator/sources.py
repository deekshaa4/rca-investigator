"""Connected data: let CuteBot explore a database or a folder of files by itself.

`rca serve --source shop.db --source ./exports` connects the chat to data sources. On
start-up each table (or file) is sampled and classified as a **metrics** table (time +
numbers) or a **records** table (time + text: deploys, alerts, tickets, logs). When the
user asks a question, CuteBot picks the tables that fit, loads only the time window the
question is about, and investigates.

Connections are read-only: only SELECT queries written here are run (never SQL from the
user or the model), and nothing leaves the computer.

Supported: SQLite files (built in), any database SQLAlchemy can reach (Postgres, MySQL,
...; `pip install sqlalchemy` plus the driver), and folders of CSV/Excel/JSON/PDF/text files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from .ingest import IngestError, Parsed, frame_to_parsed, read_file

DATA_WORDS = ("error", "errors", "latency", "slow", "traffic", "requests", "deploy", "deploys",
              "deployment", "alert", "alerts", "ticket", "tickets", "outage", "service",
              "region", "downtime", "metrics", "metric", "website", "site", "app", "api",
              "server", "servers", "checkout", "database")
SAMPLE_ROWS = 500
MAX_ROWS = 500_000
FILE_TYPES = {".csv", ".tsv", ".json", ".jsonl", ".ndjson", ".xlsx", ".xlsm", ".pdf", ".docx",
              ".txt", ".log"}
MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|"
          "december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
ISO_DAY = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
DAY_MONTH = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTHS})\b(?:\s+(\d{{4}}))?", re.IGNORECASE)
MONTH_DAY = re.compile(rf"\b({MONTHS})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b(?:,?\s+(\d{{4}}))?", re.IGNORECASE)
LAST_N = re.compile(r"\blast\s+(\d+)\s+(hour|day)s?\b", re.IGNORECASE)


@dataclass
class Table:
    source: str  # display name of the source, e.g. "shop.db"
    name: str  # table or file name
    kind: str  # "metrics" or "records"
    time_col: str
    rows: int
    columns: list[str]
    first: str | None = None  # earliest timestamp (ISO)
    last: str | None = None  # latest timestamp (ISO)


def _iso(value) -> str | None:
    stamp = pd.to_datetime(value, utc=True, errors="coerce")
    return None if pd.isna(stamp) else stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _classify(df: pd.DataFrame, name: str) -> tuple[str, str] | None:
    """('metrics' | 'records', original time column name) or None if not usable."""
    try:
        parsed = frame_to_parsed(df, context=name)
    except IngestError:
        return None
    from .ingest import _clean_name, _time_column

    cleaned = df.rename(columns=_clean_name)
    time_clean = _time_column(cleaned)
    original = next((c for c in df.columns if _clean_name(c) == time_clean), None)
    if original is None:
        return None
    return ("metrics" if parsed.metrics is not None else "records"), original


class SQLSource:
    """A database. SQLite paths work out of the box; other URLs need SQLAlchemy."""

    def __init__(self, target: str):
        self.target = target
        self.is_sqlite = not re.match(r"^[a-z0-9+]+://", target) or target.startswith("sqlite")
        if self.is_sqlite:
            import sqlite3

            path = re.sub(r"^sqlite:/{2,3}", "", target)
            if not Path(path).exists():
                raise FileNotFoundError(f"No database file at {path}")
            # read-only connection: CuteBot can look but never change anything
            self.conn = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True,
                                        check_same_thread=False)
            self.name = Path(path).name
        else:
            try:
                import sqlalchemy
            except ImportError as exc:
                raise ImportError("Connecting to this database needs SQLAlchemy and its driver: "
                                  "pip install sqlalchemy psycopg2-binary (for Postgres)") from exc
            self.engine = sqlalchemy.create_engine(target)
            self.name = self.engine.url.database or self.engine.url.host or "database"

    def _quote(self, ident: str) -> str:
        if self.is_sqlite:
            return '"' + ident.replace('"', '""') + '"'
        return self.engine.dialect.identifier_preparer.quote(ident)

    def _read(self, sql: str, params: list | dict | None = None) -> pd.DataFrame:
        if self.is_sqlite:
            return pd.read_sql_query(sql, self.conn, params=params)
        import sqlalchemy

        with self.engine.connect() as conn:
            return pd.read_sql_query(sqlalchemy.text(sql), conn, params=params)

    def table_names(self) -> list[str]:
        if self.is_sqlite:
            rows = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
            return [r[0] for r in rows]
        import sqlalchemy

        inspector = sqlalchemy.inspect(self.engine)
        return inspector.get_table_names() + inspector.get_view_names()

    def discover(self) -> list[Table]:
        tables = []
        for name in self.table_names():
            q = self._quote(name)
            try:
                sample = self._read(f"SELECT * FROM {q} LIMIT {SAMPLE_ROWS}")
            except Exception:  # noqa: BLE001, S112 (skip tables we may not read)
                continue
            found = _classify(sample, name) if len(sample) else None
            if found is None:
                continue
            kind, time_col = found
            t = self._quote(time_col)
            stats = self._read(f"SELECT COUNT(*) AS n, MIN({t}) AS lo, MAX({t}) AS hi FROM {q}")
            tables.append(Table(self.name, name, kind, time_col, int(stats["n"][0]),
                                list(sample.columns), _iso(stats["lo"][0]), _iso(stats["hi"][0])))
        return tables

    def load(self, table: Table, start: datetime, end: datetime) -> pd.DataFrame:
        q, t = self._quote(table.name), self._quote(table.time_col)
        try:
            if self.is_sqlite:
                sql = (f"SELECT * FROM {q} WHERE datetime({t}) BETWEEN datetime(?) AND "
                       f"datetime(?) LIMIT {MAX_ROWS}")
                params = [start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")]
            else:
                sql = f"SELECT * FROM {q} WHERE {t} BETWEEN :start AND :end"
                params = {"start": start.replace(tzinfo=None), "end": end.replace(tzinfo=None)}
            return self._read(sql, params)
        except Exception:  # noqa: BLE001 (odd time formats: filter in pandas instead)
            df = self._read(f"SELECT * FROM {q} LIMIT {MAX_ROWS}")
            stamps = pd.to_datetime(df[table.time_col], utc=True, errors="coerce",
                                    format="mixed")
            return df[(stamps >= start) & (stamps <= end)]


class FolderSource:
    """A folder of exported files (CSV, Excel, JSON, PDF, Word, text, logs)."""

    def __init__(self, path: str):
        self.path = Path(path)
        if not self.path.is_dir():
            raise FileNotFoundError(f"No folder at {path}")
        self.name = self.path.name
        self._cache: dict[str, Parsed] = {}

    def discover(self) -> list[Table]:
        tables = []
        for file in sorted(self.path.rglob("*")):
            if file.suffix.lower() not in FILE_TYPES or not file.is_file():
                continue
            try:
                parsed = read_file(file.name, file.read_bytes())
            except IngestError:
                continue
            key = str(file.relative_to(self.path))
            self._cache[key] = parsed
            if parsed.metrics is not None:
                m = parsed.metrics
                tables.append(Table(self.name, key, "metrics", "timestamp", len(m),
                                    list(m.columns), m["timestamp"].min(), m["timestamp"].max()))
            if parsed.records:
                stamps = [r["timestamp"] for r in parsed.records]
                tables.append(Table(self.name, key, "records", "timestamp", len(stamps),
                                    ["timestamp", "source", "text"], min(stamps), max(stamps)))
        return tables

    def load(self, table: Table, start: datetime, end: datetime) -> Parsed:
        parsed = self._cache[table.name]
        lo, hi = start.strftime("%Y-%m-%dT%H:%M:%SZ"), end.strftime("%Y-%m-%dT%H:%M:%SZ")
        if table.kind == "metrics":
            m = parsed.metrics
            return Parsed(metrics=m[(m["timestamp"] >= lo) & (m["timestamp"] <= hi)])
        return Parsed(records=[r for r in parsed.records if lo <= r["timestamp"] <= hi])


def open_source(target: str):
    """A folder becomes a FolderSource; a database file or URL becomes a SQLSource."""
    if Path(target).is_dir():
        return FolderSource(target)
    return SQLSource(target)


def question_window(message: str, latest: datetime, now: datetime | None = None
                    ) -> tuple[datetime, datetime]:
    """The time range a question is about. Without a date: the two days up to `latest`."""
    now = now or datetime.now(timezone.utc)
    text = message.lower()
    day = None
    if m := ISO_DAY.search(text):
        day = pd.Timestamp(m.group(1), tz="UTC")
    elif m := DAY_MONTH.search(text):
        day = pd.to_datetime(f"{m.group(1)} {m.group(2)} {m.group(3) or latest.year}",
                             errors="coerce", utc=True)
    elif m := MONTH_DAY.search(text):
        day = pd.to_datetime(f"{m.group(2)} {m.group(1)} {m.group(3) or latest.year}",
                             errors="coerce", utc=True)
    elif "yesterday" in text:
        day = pd.Timestamp(now.date(), tz="UTC") - pd.Timedelta(days=1)
    elif "today" in text:
        day = pd.Timestamp(now.date(), tz="UTC")
    elif m := LAST_N.search(text):
        size = timedelta(hours=int(m.group(1))) if m.group(2).lower() == "hour" \
            else timedelta(days=int(m.group(1)))
        return latest - max(size, timedelta(hours=6)), latest
    if day is not None and not pd.isna(day):
        start = day.to_pydatetime() - timedelta(days=1)
        return start, start + timedelta(days=3)
    return latest - timedelta(days=2), latest


@dataclass
class Catalog:
    """All connected sources and the tables found in them."""

    sources: list = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)

    @classmethod
    def connect(cls, targets: list[str]) -> Catalog:
        catalog = cls()
        for target in targets:
            source = open_source(target)
            catalog.sources.append(source)
            catalog.tables += [t for t in source.discover()]
        return catalog

    def __bool__(self) -> bool:
        return bool(self.tables)

    def describe(self) -> list[dict]:
        return [{"source": t.source, "table": t.name, "kind": t.kind, "rows": t.rows,
                 "first": t.first, "last": t.last} for t in self.tables]

    def summary(self) -> str:
        metrics = [t.name for t in self.tables if t.kind == "metrics"]
        records = [t.name for t in self.tables if t.kind == "records"]
        names = ", ".join(dict.fromkeys(t.source for t in self.tables))
        return (f"I'm connected to **{names}**: numbers in {', '.join(metrics) or 'none'}; "
                f"records in {', '.join(records) or 'none'}.")

    def relevant(self, message: str) -> bool:
        """Is the question about the connected data (its tables, measures or a time)?"""
        words = set(re.findall(r"[a-z]{3,}", message.lower()))
        vocab = set(DATA_WORDS)
        for t in self.tables:
            vocab |= set(re.findall(r"[a-z]{3,}", f"{t.name} {' '.join(t.columns)}".lower()))
        when = re.search(r"\d|yesterday|today|last (night|week|hour|day)|this morning", message,
                         re.IGNORECASE)
        return bool(words & vocab) or bool(when)

    def _source_of(self, table: Table):
        return next(s for s in self.sources if s.name == table.source)

    def _pick_metrics_table(self, message: str) -> Table | None:
        options = [t for t in self.tables if t.kind == "metrics"]
        words = set(re.findall(r"[a-z0-9]+", message.lower()))

        def score(t: Table) -> int:
            names = " ".join([t.name, *t.columns]).lower()
            return sum(1 for w in words if len(w) > 3 and w in names)

        return max(options, key=lambda t: (score(t), t.rows), default=None)

    def gather(self, message: str, known: dict | None = None
               ) -> tuple[Parsed, list[str], tuple[datetime, datetime] | None]:
        """Load the data a question needs: one metrics table plus all records tables."""
        table = self._pick_metrics_table(message)
        if table is None or table.last is None:
            return Parsed(), [], None
        latest = pd.Timestamp(table.last).to_pydatetime()
        start, end = question_window(message, latest)
        parts, used = [], []
        for t in [table] + [r for r in self.tables if r.kind == "records"]:
            lo = start - timedelta(hours=6) if t.kind == "records" else start
            source = self._source_of(t)
            loaded = source.load(t, lo, end)
            if isinstance(loaded, pd.DataFrame):
                if loaded.empty:
                    continue
                try:
                    loaded = frame_to_parsed(loaded, context=t.name)
                except IngestError:
                    continue
            if loaded.metrics is not None and not loaded.metrics.empty or loaded.records:
                parts.append(loaded)
                used.append(f"{t.name} ({t.kind})")
        metrics = next((p.metrics for p in parts if p.metrics is not None), None)
        records = [r for p in parts for r in p.records]
        return Parsed(metrics=metrics, records=records), used, (start, end)
