import numpy as np
import pandas as pd
import pytest

from rca_investigator.analyze import analyze_change, best_split
from rca_investigator.cli import main
from rca_investigator.simulate import SCENARIOS, generate_dataset, generate_incident, save_incident


def test_best_split_finds_a_step():
    rng = np.random.default_rng(0)
    x = np.concatenate([rng.normal(10, 1, 200), rng.normal(15, 1, 100)])
    assert abs(best_split(x) - 200) <= 2


def test_best_split_needs_enough_points():
    assert best_split(np.ones(10)) is None


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_finds_segment_and_time(scenario):
    incident = generate_incident("INC-T", scenario, seed=21)
    result = analyze_change(incident.metrics, incident.metric)
    assert result.detected
    assert result.segment == incident.truth["segment"]
    gap = abs(pd.Timestamp(result.change_start) - pd.Timestamp(incident.truth["change_start"]))
    assert gap <= pd.Timedelta(minutes=15)
    assert result.relative_change > 0.3
    assert result.findings and all(f["summary"] for f in result.findings)


def test_no_change_when_data_is_flat():
    incident = generate_incident("INC-T", "bad_deploy", seed=4)
    before = incident.metrics[incident.metrics["timestamp"] < incident.truth["change_start"]]
    result = analyze_change(before, "error_rate")
    assert not result.detected
    assert "No significant increase" in result.findings[0]["summary"]


def test_traffic_spike_evidence_mentions_request_volume():
    incident = generate_incident("INC-T", "traffic_spike", seed=8)
    result = analyze_change(incident.metrics, incident.metric)
    assert any("request volume" in f["summary"] and "rose" in f["summary"]
               for f in result.findings)


def test_accuracy_on_dataset():
    incidents = generate_dataset(20, seed=1)
    hits = 0
    for inc in incidents:
        result = analyze_change(inc.metrics, inc.metric)
        gap = abs(pd.Timestamp(result.change_start) - pd.Timestamp(inc.truth["change_start"]))
        hits += result.segment == inc.truth["segment"] and gap <= pd.Timedelta(minutes=15)
    assert hits / len(incidents) >= 0.9


def test_analyze_command(tmp_path, capsys):
    for inc in generate_dataset(5, seed=3):
        save_incident(inc, tmp_path)
    assert main(["analyze", str(tmp_path / "INC-001")]) == 0
    assert "rose from" in capsys.readouterr().out
    assert main(["analyze", str(tmp_path)]) == 0
    assert "Right segment" in capsys.readouterr().out
