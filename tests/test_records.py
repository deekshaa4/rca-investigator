import pytest

from rca_investigator.analyze import ChangeAnalysis, analyze_change
from rca_investigator.cli import main
from rca_investigator.records import rank_records, timeline
from rca_investigator.simulate import SCENARIOS, generate_dataset, generate_incident, save_incident


def investigate(incident, top_k=5):
    analysis = analyze_change(incident.metrics, incident.metric)
    return analysis, rank_records(incident.records, analysis, top_k=top_k)


@pytest.mark.parametrize("scenario", SCENARIOS[:-1])
def test_cause_record_is_found(scenario):
    incident = generate_incident("INC-T", scenario, seed=31)
    _, hits = investigate(incident)
    ids = [h.record["id"] for h in hits]
    assert incident.truth["cause_record_ids"][0] in ids


def test_cause_rate_on_dataset():
    incidents = [i for i in generate_dataset(25, seed=2) if i.truth["cause_record_ids"]]
    found = sum(
        i.truth["cause_record_ids"][0] in [h.record["id"] for h in investigate(i)[1]]
        for i in incidents
    )
    assert found / len(incidents) >= 0.9


def test_bad_deploy_ranks_the_deploy_first():
    incident = generate_incident("INC-T", "bad_deploy", seed=12)
    _, hits = investigate(incident)
    assert hits[0].record["source"] == "deploys"
    assert hits[0].minutes_from_change <= 0


def test_hits_explain_their_score():
    _, hits = investigate(generate_incident("INC-T", "config_change", seed=6))
    assert all(len(h.reasons) >= 4 for h in hits)
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)


def test_no_detected_change_gives_no_hits():
    incident = generate_incident("INC-T", "bad_deploy", seed=1)
    assert rank_records(incident.records, ChangeAnalysis(metric="error_rate", detected=False)) == []


def test_timeline_is_ordered_and_in_window():
    incident = generate_incident("INC-T", "dependency_outage", seed=4)
    analysis, _ = investigate(incident)
    events = timeline(incident.records, analysis)
    assert events
    assert [e["timestamp"] for e in events] == sorted(e["timestamp"] for e in events)
    assert all(-360 <= e["minutes_from_change"] <= 60 for e in events)


def test_search_command(tmp_path, capsys):
    for inc in generate_dataset(5, seed=3):
        save_incident(inc, tmp_path)
    assert main(["search", str(tmp_path / "INC-001")]) == 0
    assert "1. [" in capsys.readouterr().out
    assert main(["search", str(tmp_path)]) == 0
    assert "Cause record in top 5" in capsys.readouterr().out
