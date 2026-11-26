import pandas as pd
import pytest

from rca_investigator.analyze import analyze_change
from rca_investigator.ingest import (
    IngestError,
    guess_source,
    read_file,
    read_text,
    text_to_records,
)
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
    ("chart.png", "pictures"), ("old.xls", "xlsx"), ("notes.txt", "date and time"),
    ("scan.pdf", "PDF"), ("broken.xlsx", "Excel"),
])
def test_helpful_errors(name, message):
    with pytest.raises(IngestError, match=message):
        read_file(name, b"nothing useful here")


def tiny_pdf(lines: list[str]) -> bytes:
    """A minimal one-page PDF with the given text lines (no PDF library needed)."""
    ops = ["BT /F1 9 Tf 20 800 Td 11 TL"] + [
        "(" + ln.replace("(", "[").replace(")", "]") + ") Tj T*" for ln in lines] + ["ET"]
    stream = "\n".join(ops).encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>"),
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer << /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, xref)
    return bytes(out)


def test_pdf_with_a_table_and_records():
    times = pd.date_range("2026-05-01", periods=40, freq="15min")
    rows = [f"{t:%Y-%m-%d %H:%M}  {2.0 if i < 25 else 9.0}" for i, t in enumerate(times)]
    lines = ["Incident report", "Time  Errors", *rows,
             "2026-05-01 06:00 Deployed api v3.1", "2026-05-01 06:20 Customer ticket: errors"]
    parsed = read_file("report.pdf", tiny_pdf(lines))
    assert parsed.metrics is not None and "errors" in parsed.metrics.columns
    assert len(parsed.metrics) == 40
    assert [r["source"] for r in parsed.records] == ["deploys", "tickets"]
    records = [{**r, "id": f"R{i}"} for i, r in enumerate(parsed.records)]
    report = investigate("X", "What went wrong?", "errors", parsed.metrics, records, None)
    # the complaint ticket comes after the jump, so it is a symptom, not a rival cause
    assert report.sufficiency.verdict.value == "sufficient"


def test_excel_upload(tmp_path):
    path = tmp_path / "book.xlsx"
    own_format_table().to_excel(path, index=False)
    parsed = read_file("book.xlsx", path.read_bytes())
    assert parsed.metrics is not None and "errors" in parsed.metrics.columns


def test_word_upload(tmp_path):
    import docx

    doc = docx.Document()
    doc.add_paragraph("2026-05-01 14:50 Changed api feature flag fast_path to 100%")
    doc.add_paragraph("Notes without a date are ignored.")
    path = tmp_path / "notes.docx"
    doc.save(path)
    parsed = read_file("notes.docx", path.read_bytes())
    assert [r["source"] for r in parsed.records] == ["config_changes"]


def test_text_file_bytes_with_bom():
    parsed = read_file("events.txt", "\ufeff2026-05-01 14:50 Deployed api v2".encode("utf-8-sig"))
    assert parsed.records[0]["text"] == "Deployed api v2"


def test_full_investigation_on_uploaded_data():
    inc = generate_incident("X", "bad_deploy", seed=12)
    m = read_text("m.csv", inc.metrics.to_csv(index=False)).metrics
    lines = "\n".join(f"{r['timestamp']} {r.get('service', '')} {r['text']}" for r in inc.records)
    recs = text_to_records(lines, {"service": set(m["service"])})
    recs = [{**r, "id": f"R{i:03d}"} for i, r in enumerate(recs, 1)]
    report = investigate("X", inc.question, inc.metric, m, recs, None)
    assert report.sufficiency.verdict.value in {"sufficient", "partial"}
    assert report.contributing_factors[0].category.value == "deployment"
