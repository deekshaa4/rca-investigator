import pytest

from rca_investigator.analyze import analyze_change
from rca_investigator.investigate import build_evidence, investigate
from rca_investigator.records import rank_records
from rca_investigator.simulate import SCENARIOS, generate_dataset, generate_incident
from rca_investigator.sufficiency import assess, find_candidate


def engines(inc):
    analysis = analyze_change(inc.metrics, inc.metric)
    hits = rank_records(inc.records, analysis)
    return analysis, hits, build_evidence(analysis, hits)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_verdict_matches_truth_without_llm(scenario):
    inc = generate_incident("INC-T", scenario, seed=17)
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, None)
    assert report.sufficiency.verdict.value == inc.truth["expected_verdict"]
    assert report.sufficiency.reasons


def test_verdicts_on_dataset():
    incidents = generate_dataset(25, seed=4)
    ok = sum(
        investigate("X", i.question, i.metric, i.metrics, i.records, None)
        .sufficiency.verdict.value == i.truth["expected_verdict"]
        for i in incidents
    )
    assert ok / len(incidents) >= 0.9


def test_insufficient_lists_missing_data():
    inc = generate_incident("INC-T", "no_clear_cause", seed=9)
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, None)
    assert report.sufficiency.verdict.value == "insufficient"
    assert report.sufficiency.missing_data


def test_traffic_claim_without_traffic_rise_loses_points():
    inc = generate_incident("INC-T", "bad_deploy", seed=12)
    analysis, hits, evidence = engines(inc)
    cand = find_candidate(hits, [], evidence)
    factor = {"rank": 1, "description": "x", "category": "deployment", "confidence": 0.9,
              "why_chain": [], "evidence_ids": [cand.evidence_id]}
    right = assess(analysis, hits, [factor], evidence)
    wrong = assess(analysis, hits, [{**factor, "category": "traffic"}], evidence)
    assert wrong.score < right.score
    assert any("did not rise" in r for r in wrong.reasons)


def test_factor_not_citing_the_candidate_loses_points():
    inc = generate_incident("INC-T", "bad_deploy", seed=12)
    analysis, hits, evidence = engines(inc)
    cand = find_candidate(hits, [], evidence)
    good = {"rank": 1, "description": "x", "category": "deployment", "confidence": 0.9,
            "why_chain": [], "evidence_ids": [cand.evidence_id]}
    off = {**good, "evidence_ids": ["E1"]}
    assert assess(analysis, hits, [off], evidence).score < assess(
        analysis, hits, [good], evidence).score


def test_verdicts_on_hard_dataset():
    incidents = generate_dataset(25, seed=8, hard=True)
    ok = sum(
        investigate("X", i.question, i.metric, i.metrics, i.records, None)
        .sufficiency.verdict.value == i.truth["expected_verdict"]
        for i in incidents
    )
    assert ok / len(incidents) >= 0.9


def test_symptom_alert_is_not_a_rival_cause():
    inc = generate_incident("INC-T", "bad_deploy", seed=12, twist="red_herring_other")
    report = investigate("X", inc.question, inc.metric, inc.metrics, inc.records, None)
    assert report.sufficiency.verdict.value == "sufficient"
