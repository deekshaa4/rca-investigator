import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from rca_investigator.schema import RCAReport

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = json.loads((ROOT / "examples" / "example_report.json").read_text())


def test_example_report_is_valid():
    report = RCAReport.model_validate(EXAMPLE)
    assert report.sufficiency.verdict.value == "sufficient"
    assert report.contributing_factors[0].category.value == "deployment"


def test_citing_missing_evidence_is_rejected():
    data = copy.deepcopy(EXAMPLE)
    data["contributing_factors"][0]["evidence_ids"].append("E99")
    with pytest.raises(ValidationError, match="E99"):
        RCAReport.model_validate(data)


def test_duplicate_evidence_ids_are_rejected():
    data = copy.deepcopy(EXAMPLE)
    data["evidence"].append(dict(data["evidence"][0]))
    with pytest.raises(ValidationError, match="unique"):
        RCAReport.model_validate(data)


def test_factor_without_evidence_is_rejected():
    data = copy.deepcopy(EXAMPLE)
    data["contributing_factors"][0]["evidence_ids"] = []
    with pytest.raises(ValidationError):
        RCAReport.model_validate(data)


def test_action_for_unknown_factor_is_rejected():
    data = copy.deepcopy(EXAMPLE)
    data["actions"][0]["addresses_factors"] = [5]
    with pytest.raises(ValidationError, match="unknown factor"):
        RCAReport.model_validate(data)


def test_insufficient_verdict_may_have_no_factors():
    data = copy.deepcopy(EXAMPLE)
    data["contributing_factors"] = []
    data["actions"] = []
    data["sufficiency"]["verdict"] = "insufficient"
    RCAReport.model_validate(data)


def test_sufficient_verdict_needs_a_factor():
    data = copy.deepcopy(EXAMPLE)
    data["contributing_factors"] = []
    data["actions"] = []
    with pytest.raises(ValidationError, match="at least one factor"):
        RCAReport.model_validate(data)


def test_exported_schema_is_up_to_date():
    exported = json.loads((ROOT / "schemas" / "rca_report.schema.json").read_text())
    assert exported == RCAReport.model_json_schema(), "run: rca schema"
