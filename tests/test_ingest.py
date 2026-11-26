import pandas as pd
import pytest

from rca_investigator.analyze import analyze_change
from rca_investigator.ingest import IngestError, guess_source, read_text, text_to_records
from rca_investigator.investigate import investigate
from rca_investigator.simulate import generate_incident


def own_format_table():
    """A user's export: different column names, no service/region, no request counts."""
    times = pd.date_range("2026-05-01", periods=96, freq="15min")
    errors = [2.0] * 60 + [9.0] * 36
    return pd.DataFrame({"Time": times.strftime("%Y-%m-%d %H:%M"), "Errors %": errors,
                         "Avg Latency": [120.0] * 96})


def test_table_with_own_column_names_is_understood():
    parsed = read_text("export.csv", own_format_table().to_csv(index=False))
    m = parsed.metrics
    assert {"timestamp", "service", "region", "requests", "errors", "avg_latency"} <= set(m.columns)
    assert m["timestamp"].iloc[0] == "2026-05-01T00:00:00Z"
    assert "Table of numbers" in parsed.summary and "errors" in parsed.summary
    analysis = analyze_change(m, "errors")
    assert analysis.detected and analysis.change_start.startswith("2026-05-01T15:00")


def test_records_csv_and_source_guessing():
    text = ("when,what,app\n2026-05-01 14:50,Deployed api v2.4,api\n"
            "2026-05-01 15:10,Customer ticket: checkout broken,api\n")
    parsed = read_text("events.csv", text)
    assert [r["source"] for r in parsed.records] == ["deploys", "tickets"]
    assert parsed.records[0]["service"] == "api"
    assert guess_source("Changed feature flag x to 50%") == "config_changes"
    assert guess_source("ERROR NullPointerException") == "logs"
    assert guess_source("api: ERROR upstream timeout") == "logs"


def test_pasted_log_lines_become_records():
    text = "2026-05-01T14:58:00Z search: ERROR timeout\nno date here\n2026-05-01 15:01 alert fired"
    records = text_to_records(text, {"service": {"search", "all"}})
    assert len(records) == 2 and records[0]["service"] == "search"
    assert records[1]["source"] == "alerts"


@pytest.mark.parametrize("name, message", [
    ("chart.png", "pictures"), ("book.xlsx", "CSV"), ("notes.txt", "date and time"),
])
def test_helpful_errors(name, message):
    with pytest.raises(IngestError, match=message):
        read_text(name, "nothing useful here")


def test_full_investigation_on_uploaded_data():
    inc = generate_incident("X", "bad_deploy", seed=12)
    m = read_text("m.csv", inc.metrics.to_csv(index=False)).metrics
    lines = "\n".join(f"{r['timestamp']} {r.get('service', '')} {r['text']}" for r in inc.records)
    recs = text_to_records(lines, {"service": set(m["service"])})
    recs = [{**r, "id": f"R{i:03d}"} for i, r in enumerate(recs, 1)]
    report = investigate("X", inc.question, inc.metric, m, recs, None)
    assert report.sufficiency.verdict.value in {"sufficient", "partial"}
    assert report.contributing_factors[0].category.value == "deployment"
