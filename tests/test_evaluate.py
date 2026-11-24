from test_investigate import GOOD_REPLY, FakeClient

from rca_investigator.cli import main
from rca_investigator.evaluate import cited_record_ids, score_report, summarise
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
