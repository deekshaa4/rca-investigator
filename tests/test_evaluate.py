from test_investigate import GOOD_REPLY, FakeClient

from rca_investigator.cli import main
from rca_investigator.evaluate import breakdown, cited_record_ids, score_report, summarise
from rca_investigator.investigate import investigate
from rca_investigator.simulate import generate_dataset, generate_incident, save_incident


def test_correct_report_scores_well():
    inc = generate_incident("INC-T", "bad_deploy", seed=12)
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records,
                         FakeClient(GOOD_REPLY))
    assert cited_record_ids(report) == set(inc.truth["cause_record_ids"])
    row = score_report(report, inc.truth)
    assert row["verdict_ok"] and row["segment_ok"] and row["category_ok"] and row["cause_cited"]


def test_unexplainable_incident_is_not_scored_on_cause():
    inc = generate_incident("INC-T", "no_clear_cause", seed=5)
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, None)
    row = score_report(report, inc.truth)
    assert row["verdict_ok"] and row["category_ok"] is None
    assert summarise([row])["verdict correct"] == 1


def test_batch_command(tmp_path, capsys):
    for inc in generate_dataset(5, seed=3):
        save_incident(inc, tmp_path)
    assert main(["batch", str(tmp_path), "--no-llm"]) == 0
    assert "verdict correct" in capsys.readouterr().out
    assert (tmp_path / "scores.csv").exists()


def test_invented_ids_are_counted_and_removed():
    inc = generate_incident("INC-T", "bad_deploy", seed=12)
    reply = {**GOOD_REPLY, "contributing_factors": [
        *GOOD_REPLY["contributing_factors"],
        {**GOOD_REPLY["contributing_factors"][0], "evidence_ids": ["E99"]},
    ]}
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records,
                         FakeClient(reply))
    g = report.guardrails
    assert g.model_used and g.ids_invented == 1 and g.factors_dropped == 1
    assert "E99" not in {i for f in report.contributing_factors for i in f.evidence_ids}
    summary = summarise([score_report(report, inc.truth)])
    assert 0 < summary["evidence IDs invented by the model"] < 1


def test_engine_only_reports_have_no_invented_rate():
    inc = generate_incident("INC-T", "bad_deploy", seed=12)
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, None)
    assert "evidence IDs invented by the model" not in summarise([score_report(report, inc.truth)])


def test_breakdown_by_twist():
    rows = []
    for inc in generate_dataset(10, seed=6, hard=True):
        report = investigate("X", inc.question, inc.metric, inc.metrics, inc.records, None)
        rows.append(score_report(report, inc.truth))
    table = breakdown(rows, "twist")
    assert table["incidents"].sum() == 10
    assert all("/" in v or v == "-" for v in table["verdict"])


def test_evaluate_command_scores_saved_reports(tmp_path, capsys):
    for inc in generate_dataset(5, seed=3):
        save_incident(inc, tmp_path)
    main(["batch", str(tmp_path), "--no-llm"])
    capsys.readouterr()
    assert main(["evaluate", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "verdict correct" in out and "By scenario" in out
