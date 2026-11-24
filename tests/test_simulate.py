import pandas as pd
import pytest

from rca_investigator.cli import main
from rca_investigator.simulate import (
    SCENARIOS,
    generate_dataset,
    generate_incident,
    load_incident,
    save_incident,
)


def segment_ratio(incident):
    """Mean of the question's metric after vs before the change, in the affected segment."""
    df = incident.metrics
    for key, value in incident.truth["segment"].items():
        df = df[df[key] == value]
    after = df["timestamp"] >= incident.truth["change_start"]
    metric = incident.truth["metric"]
    return df.loc[after, metric].mean() / df.loc[~after, metric].mean()


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_injected_change_is_visible(scenario):
    incident = generate_incident("INC-T", scenario, seed=7)
    assert segment_ratio(incident) > 1.5


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_records_are_ordered_with_unique_ids(scenario):
    records = generate_incident("INC-T", scenario, seed=3).records
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))
    assert [r["timestamp"] for r in records] == sorted(r["timestamp"] for r in records)


@pytest.mark.parametrize("scenario", SCENARIOS[:-1])
def test_explainable_incidents_have_a_cause_record_near_the_change(scenario):
    incident = generate_incident("INC-T", scenario, seed=11)
    causes = [r for r in incident.records if r["id"] in incident.truth["cause_record_ids"]]
    assert len(causes) == 1
    gap = pd.Timestamp(incident.truth["change_start"]) - pd.Timestamp(causes[0]["timestamp"])
    assert abs(gap) < pd.Timedelta(hours=6)
    assert incident.truth["expected_verdict"] == "sufficient"


def test_no_clear_cause_has_no_cause_record():
    incident = generate_incident("INC-T", "no_clear_cause", seed=5)
    assert incident.truth["cause_record_ids"] == []
    assert incident.truth["expected_verdict"] == "insufficient"


def test_same_seed_gives_same_incident():
    a = generate_incident("INC-T", "bad_deploy", seed=9)
    b = generate_incident("INC-T", "bad_deploy", seed=9)
    pd.testing.assert_frame_equal(a.metrics, b.metrics)
    assert a.records == b.records


def test_dataset_covers_all_scenarios():
    scenarios = [i.truth["scenario"] for i in generate_dataset(10)]
    assert sorted(scenarios) == sorted(SCENARIOS * 2)


def test_save_and_load_hide_the_truth(tmp_path):
    incident = generate_incident("INC-T", "config_change", seed=2)
    folder = save_incident(incident, tmp_path)
    meta, metrics, records = load_incident(folder)
    assert meta["question"] == incident.question
    assert len(metrics) == len(incident.metrics)
    assert records == incident.records
    assert "truth" not in meta and (folder / "truth.json").exists()


def test_simulate_command(tmp_path, capsys):
    assert main(["simulate", "--n", "5", "--out", str(tmp_path)]) == 0
    assert len(list(tmp_path.iterdir())) == 5
    assert "Wrote 5 incidents" in capsys.readouterr().out
