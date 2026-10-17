"""Strict Python request/result boundaries for the focused lab prototype."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class StartLab(StrictModel):
    model_name: str = Field(min_length=1, max_length=160)
    operator_trial: Literal[True]
    progression_mode: Literal['reviewed', 'screen_guided'] = 'reviewed'


class Revision(StrictModel):
    revision: int = Field(ge=1)


class AttachCapture(Revision):
    capture_session_id: str = Field(min_length=1, max_length=64)


class CheckFrame(Revision):
    frame_id: str = Field(min_length=1, max_length=128)
    view_revision: int = Field(ge=1, le=9_007_199_254_740_991)


class ReviewCriteria(Revision):
    criterion_ids: list[str] = Field(min_length=1, max_length=12)
    review_note: str = Field(min_length=8, max_length=1000)


class StudentResponse(Revision):
    kind: Literal["prediction", "observation", "explanation", "question", "note"]
    text: str = Field(min_length=1, max_length=2000)
    self_confidence: int | None = Field(default=None, ge=1, le=5)


class ContextChange(Revision):
    action: Literal["pause", "resume", "view_changed", "parameters_changed", "condition", "revisit", "enable_guided"]
    view_revision: int | None = Field(default=None, ge=1, le=9_007_199_254_740_991)
    condition: Literal["baseline", "phase_fault", "restored_baseline"] | None = None
    checkpoint_id: str | None = Field(default=None, max_length=64)


class CriterionFinding(StrictModel):
    criterion_id: str = Field(min_length=1, max_length=96)
    status: Literal["match", "mismatch", "unknown"]
    evidence: str = Field(max_length=180)


class ActionFinding(StrictModel):
    action_id: str = Field(min_length=1, max_length=96)
    status: Literal["match", "mismatch", "unknown"]
    evidence: str = Field(max_length=180)


class LabAnalysis(StrictModel):
    summary: str = Field(min_length=1, max_length=220)
    criteria: list[CriterionFinding] = Field(min_length=1, max_length=12)
    uncertainties: list[str] = Field(max_length=3)


    action_findings: list[ActionFinding] = Field(default_factory=list, max_length=8)
