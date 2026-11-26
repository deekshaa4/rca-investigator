"""A demo database for trying connected mode: `rca demo-db`, then `rca serve --source demo.db`.

The tables look like a small company's own data: one metrics table and separate tables
for deploys, config changes, alerts, tickets and application logs.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .simulate import generate_incident

TABLE_OF = {"deploys": "deploys", "config_changes": "config_changes", "alerts": "alerts",
            "tickets": "support_tickets", "logs": "app_logs"}


def write_demo_db(path: str | Path, scenario: str = "bad_deploy", seed: int = 12) -> dict:
    inc = generate_incident("DEMO", scenario, seed=seed)
    path = Path(path)
    path.unlink(missing_ok=True)
    with sqlite3.connect(path) as conn:
        metrics = inc.metrics.rename(columns={"timestamp": "ts"})
        metrics.to_sql("service_metrics_5min", conn, index=False)
        records = pd.DataFrame(inc.records)
        for source, table in TABLE_OF.items():
            rows = records[records["source"] == source]
            if rows.empty:
                continue
            out = rows.rename(columns={"timestamp": "created_at", "text": "description"})
            out[["created_at", "service", "region", "description"]].to_sql(table, conn,
                                                                           index=False)
    return {"question": inc.question}
