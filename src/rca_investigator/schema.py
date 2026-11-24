"""The RCA report format.

Every finding in a report must cite evidence by ID (for example "E3"), and every
cited ID must exist in the report's evidence list. A report that breaks this
rule fails validation, so unsupported claims cannot slip through.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

EVIDENCE_ID_PATTERN = r"^E\d+$"


class EvidenceKind(str, Enum):
    METRIC = "metric"  # a finding from the numerical data
    RECORD = "record"  # a log line, ticket, deploy note or other text record


class FactorCategory(str, Enum):
    DEPLOYMENT = "deployment"
    CONFIG_CHANGE = "config_change"
    TRAFFIC = "traffic"
    DEPENDENCY = "dependency"
    INFRASTRUCTURE = "infrastructure"
    DATA = "data"
    UNKNOWN = "unknown"


class Verdict(str, Enum):
    SUFFICIENT = "sufficient"  # the evidence supports a reliable conclusion
    PARTIAL = "partial"  # a likely cause, but important gaps remain
    INSUFFICIENT = "insufficient"  # not enough evidence to name a cause


class ActionType(str, Enum):
    CORRECTIVE = "corrective"  # fixes this incident
    PREVENTIVE = "preventive"  # stops it from happening again


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    id: str = Field(pattern=EVIDENCE_ID_PATTERN, description="Evidence ID, e.g. 'E1'")
    kind: EvidenceKind
    source: str = Field(description="Where it came from, e.g. 'metrics:error_rate' or 'deploys'")
    summary: str = Field(min_length=1)
    timestamp: str | None = Field(default=None, description="ISO 8601 time, if known")


class ChangeSummary(BaseModel):
    metric: str
    segment: dict[str, str] = Field(
        default_factory=dict, description="Where the change is concentrated, e.g. {'service': 'checkout'}"
    )
    change_start: str = Field(description="ISO 8601 time the change began")
    baseline_value: float
    current_value: float
    relative_change: float = Field(description="(current - baseline) / baseline")
    evidence_ids: list[str] = Field(min_length=1)


class ContributingFactor(BaseModel):
    rank: int = Field(ge=1)
    description: str = Field(min_length=1)
    category: FactorCategory
    confidence: float = Field(ge=0, le=1)
    why_chain: list[str] = Field(
        default_factory=list, description="'5 Whys' chain from symptom to root cause"
    )
    evidence_ids: list[str] = Field(min_length=1)


class RuledOutHypothesis(BaseModel):
    hypothesis: str
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)


class Sufficiency(BaseModel):
    verdict: Verdict
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(min_length=1)
    missing_data: list[str] = Field(
        default_factory=list, description="Data that would make the conclusion more reliable"
    )


class Action(BaseModel):
    action: str = Field(min_length=1)
    type: ActionType
    priority: Priority
    addresses_factors: list[int] = Field(
        default_factory=list, description="Ranks of the contributing factors this action addresses"
    )


class RCAReport(BaseModel):
    incident_id: str
    question: str
    what_changed: ChangeSummary | None = None  # None when no significant change was found
    contributing_factors: list[ContributingFactor]
    ruled_out: list[RuledOutHypothesis] = Field(default_factory=list)
    evidence: list[Evidence] = Field(min_length=1)
    sufficiency: Sufficiency
    actions: list[Action] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_consistency(self) -> RCAReport:
        known = [e.id for e in self.evidence]
        if len(known) != len(set(known)):
            raise ValueError("evidence IDs must be unique")
        known_ids = set(known)

        cited: list[str] = list(self.what_changed.evidence_ids) if self.what_changed else []
        for factor in self.contributing_factors:
            cited.extend(factor.evidence_ids)
        for hypothesis in self.ruled_out:
            cited.extend(hypothesis.evidence_ids)
        missing = sorted(set(cited) - known_ids)
        if missing:
            raise ValueError(f"cited evidence not found in the evidence list: {missing}")

        ranks = [f.rank for f in self.contributing_factors]
        if len(ranks) != len(set(ranks)):
            raise ValueError("contributing factor ranks must be unique")
        unknown_ranks = sorted(
            {r for a in self.actions for r in a.addresses_factors} - set(ranks)
        )
        if unknown_ranks:
            raise ValueError(f"actions refer to unknown factor ranks: {unknown_ranks}")

        if self.sufficiency.verdict != Verdict.INSUFFICIENT and not self.contributing_factors:
            raise ValueError("a 'sufficient' or 'partial' verdict needs at least one factor")
        return self


def export_json_schema(path: str | Path) -> None:
    """Write the report format as a JSON Schema file."""
    Path(path).write_text(json.dumps(RCAReport.model_json_schema(), indent=2) + "\n")
