from rca_investigator.cli import main
from rca_investigator.investigate import investigate, llm_reply_schema, to_markdown
from rca_investigator.simulate import generate_incident, save_incident


class FakeClient:
    """Stands in for the language model and records what it was asked."""

    def __init__(self, reply):
        self.reply = reply
        self.prompts = []

    def chat_json(self, prompt, json_schema, system=None):
        self.prompts.append(prompt)
        assert json_schema == llm_reply_schema()
        return self.reply


GOOD_REPLY = {
    "contributing_factors": [{
        "description": "A new release broke request handling.",
        "category": "deployment",
        "confidence": 0.9,
        "why_chain": ["Errors rose.", "Requests crashed.", "The new release has a bug."],
        "evidence_ids": ["E1", "E5"],
    }],
    "ruled_out": [{"hypothesis": "Traffic spike", "reason": "Traffic was flat.",
                   "evidence_ids": ["E3"]}],
    "actions": [
        {"action": "Roll back the release.", "type": "corrective", "priority": "high",
         "factor_number": 1},
        {"action": "Add a canary stage.", "type": "preventive", "priority": "medium",
         "factor_number": 7},
    ],
}


def run(scenario, reply, seed=12):
    inc = generate_incident("INC-T", scenario, seed=seed)
    client = FakeClient(reply)
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, client)
    return inc, client, report


def test_report_is_built_and_valid():
    inc, client, report = run("bad_deploy", GOOD_REPLY)
    assert report.what_changed.segment == inc.truth["segment"]
    assert report.contributing_factors[0].rank == 1
    assert report.sufficiency.verdict.value == "sufficient"
    assert report.actions[1].addresses_factors == [1]  # bad factor number repaired
    assert "E1 [metric" in client.prompts[0]


def test_invented_evidence_ids_are_removed():
    reply = {**GOOD_REPLY, "contributing_factors": [
        {**GOOD_REPLY["contributing_factors"][0], "evidence_ids": ["E1", "E99"]},
        {**GOOD_REPLY["contributing_factors"][0], "evidence_ids": ["E42"]},
    ]}
    _, _, report = run("bad_deploy", reply)
    assert len(report.contributing_factors) == 1
    assert report.contributing_factors[0].evidence_ids == ["E1"]


def test_no_clear_cause_is_insufficient_and_capped():
    _, _, report = run("no_clear_cause", GOOD_REPLY, seed=5)
    assert report.sufficiency.verdict.value == "insufficient"
    assert report.sufficiency.missing_data
    assert all(f.confidence <= 0.3 for f in report.contributing_factors)


def test_no_llm_falls_back_to_engine_factor():
    inc = generate_incident("INC-T", "config_change", seed=3)
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, None)
    assert report.contributing_factors[0].category.value == "config_change"
    assert report.sufficiency.verdict.value == "sufficient"
    assert "## Evidence" in to_markdown(report)


def test_investigate_command_without_llm(tmp_path, capsys):
    folder = save_incident(generate_incident("INC-T", "bad_deploy", seed=2), tmp_path)
    assert main(["investigate", str(folder), "--no-llm", "--save"]) == 0
    assert "## What changed" in capsys.readouterr().out
    assert (folder / "report.json").exists() and (folder / "report.md").exists()


def test_factor_resting_only_on_later_records_is_dropped():
    inc = generate_incident("INC-T", "bad_deploy", seed=12)
    report = investigate("INC-T", inc.question, inc.metric, inc.metrics, inc.records, None)
    later = [e.id for e in report.evidence if e.kind.value == "record"
             and "after the change" in e.summary and "10 min after" in e.summary]
    reply = {**GOOD_REPLY, "contributing_factors": [
        {**GOOD_REPLY["contributing_factors"][0], "evidence_ids": later},
        GOOD_REPLY["contributing_factors"][0],
    ]}
    _, _, report = run("bad_deploy", reply)
    assert len(report.contributing_factors) == 1
    assert report.contributing_factors[0].evidence_ids == ["E1", "E5"]
