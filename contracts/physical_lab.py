"""Versioned, data-driven pre-lab packs and untrusted student commands."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Question(Model):
    id: str
    prompt: str
    options: dict[str, str]
    correct: str
    explanation: str
    required: bool = False

    @model_validator(mode="after")
    def valid_answer(self):
        if self.correct not in self.options or len(self.options) < 2:
            raise ValueError("Question must have a valid answer and alternatives")
        return self


class Concept(Model):
    id: str
    title: str
    depends_on: list[str] = Field(default_factory=list)
    targets: list[str]
    explanation: dict[str, str]
    questions: list[Question] = Field(min_length=5, max_length=5)


class Part(Model):
    id: str
    label: str
    kind: Literal["body", "output", "input", "control", "display"]
    position: list[FiniteFloat] = Field(min_length=3, max_length=3)
    size: list[FiniteFloat] = Field(min_length=3, max_length=3)
    description: dict[str, str]


class Rule(Model):
    kind: Literal["select", "connect", "set", "measure"]
    target: str
    other: str | None = None
    value: str | bool | FiniteFloat | None = None
    unit: str | None = None
    tolerance: FiniteFloat = Field(default=0.0, ge=0)


class Step(Model):
    id: str
    instruction: dict[str, str]
    why: dict[str, str]
    rule: Rule


class Control(Model):
    initial: str | bool | FiniteFloat
    minimum: FiniteFloat | None = None
    maximum: FiniteFloat | None = None
    choices: list[str] = Field(default_factory=list)
    unit: str | None = None


class Fault(Model):
    id: str
    target: str
    question: Question


class ExperimentDemo(Model):
    initial_controls: dict[str, str | bool | FiniteFloat]
    omit_step_ids: list[str]


class ExperimentPack(Model):
    schema_version: Literal["physical-lab-pack/v1"]
    id: str
    version: str
    title: str
    aim: dict[str, str]
    curriculum: dict[str, str]
    equipment: dict[str, str]
    sources: list[dict[str, str]]
    review: dict[str, str]
    adapter: str
    asset: str = Field(pattern=r"^[A-Za-z0-9_-]+\.gltf$")
    asset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    visual_design: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]+\.json$")
    demo: ExperimentDemo | None = None
    parts: list[Part]
    orientation: list[str] = Field(min_length=1)
    concepts: list[Concept] = Field(min_length=1)
    controls: dict[str, Control]
    connections: list[list[str]]
    steps: list[Step] = Field(min_length=1)
    faults: list[Fault] = Field(min_length=1)
    assessment: list[Question] = Field(min_length=5)
    precautions: list[str]
    observation_columns: list[dict[str, str]]
    concept_pass_percent: FiniteFloat = Field(default=60.0, gt=0, le=100)
    readiness_pass_percent: FiniteFloat = Field(default=80.0, gt=0, le=100)

    @model_validator(mode="after")
    def references(self):
        parts = {p.id: p for p in self.parts}
        if len(parts) != len(self.parts):
            raise ValueError("Duplicate part")
        seen = set()
        for concept in self.concepts:
            if concept.id in seen or not set(concept.depends_on) <= seen:
                raise ValueError("Concepts must be unique and in dependency order")
            seen.add(concept.id)
        targets = self.orientation + list(self.controls)
        targets += [t for c in self.concepts for t in c.targets]
        targets += [s.rule.target for s in self.steps] + [f.target for f in self.faults]
        if not set(targets) <= parts.keys():
            raise ValueError("Unknown semantic target")
        for edge in self.connections:
            if len(edge) != 2 or any(t not in parts for t in edge):
                raise ValueError("Unknown connection target")
            if parts[edge[0]].kind != "output" or parts[edge[1]].kind != "input":
                raise ValueError("Connections must run from output to input")
        for step in self.steps:
            r = step.rule
            if r.kind == "connect" and [r.target, r.other] not in self.connections:
                raise ValueError("Unsupported procedure connection")
            if r.kind == "set" and r.target not in self.controls:
                raise ValueError("Unknown procedure control")
        questions = [q.id for c in self.concepts for q in c.questions]
        questions += [f.question.id for f in self.faults] + [q.id for q in self.assessment]
        if len(questions) != len(set(questions)):
            raise ValueError("Duplicate question")
        if len({s.id for s in self.steps}) != len(self.steps):
            raise ValueError("Duplicate step")
        if len({f.id for f in self.faults}) != len(self.faults):
            raise ValueError("Duplicate fault")
        if len(set(self.orientation)) != len(self.orientation):
            raise ValueError("Duplicate orientation target")
        if not any(s.rule.kind != "measure" for s in self.steps):
            raise ValueError("At least one apparatus rehearsal action is required")
        if any(n <= 0 for p in self.parts for n in p.size):
            raise ValueError("Part dimensions must be positive")
        for key, control in self.controls.items():
            if control.minimum is not None and control.maximum is not None and control.minimum > control.maximum:
                raise ValueError("Invalid control range")
            if control.choices and control.initial not in control.choices:
                raise ValueError("Initial control choice is unsupported")
            for step in self.steps:
                r = step.rule
                if r.kind != "set" or r.target != key:
                    continue
                if control.choices and r.value not in control.choices:
                    raise ValueError("Procedure requests an unsupported setting")
                if isinstance(r.value, (int, float)) and not isinstance(r.value, bool):
                    if control.minimum is not None and r.value < control.minimum:
                        raise ValueError("Procedure setting below control range")
                    if control.maximum is not None and r.value > control.maximum:
                        raise ValueError("Procedure setting above control range")
        if self.demo:
            if not set(self.demo.initial_controls) <= self.controls.keys():
                raise ValueError("Unknown demo control")
            ids = {s.id for s in self.steps}
            omitted = set(self.demo.omit_step_ids)
            if not omitted <= ids or len(omitted) == len(ids):
                raise ValueError("Invalid demo procedure selection")
            for step in self.steps:
                if step.id not in omitted:
                    continue
                r = step.rule
                if r.kind not in ('select', 'set'):
                    raise ValueError("Demo setup cannot complete connections or measurements")
                if r.kind == 'set' and self.demo.initial_controls.get(r.target) != r.value:
                    raise ValueError("Demo setup must explicitly supply omitted control settings")
            for key, value in self.demo.initial_controls.items():
                control = self.controls[key]
                if isinstance(control.initial, bool) and type(value) is not bool:
                    raise ValueError("Demo switch must be boolean")
                if type(control.initial) in (int, float) and type(value) not in (int, float):
                    raise ValueError("Demo numeric control must be numeric")
                if control.choices and value not in control.choices:
                    raise ValueError("Unsupported demo setting")
                if type(value) in (int, float):
                    if control.minimum is not None and value < control.minimum:
                        raise ValueError("Demo setting below range")
                    if control.maximum is not None and value > control.maximum:
                        raise ValueError("Demo setting above range")
        return self


class CreatePreparation(Model):
    experiment_id: str = Field(min_length=1, max_length=100)
    language: Literal["en", "or"] = "or"
    mode: Literal["guided_preparation", "experiment_demo"] = "guided_preparation"


class PreparationEvent(Model):
    event_id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,100}$")
    revision: int = Field(ge=0)
    kind: Literal["select", "advance", "answer", "connect", "set", "measure", "language"]
    target: str = Field(default="", max_length=100)
    other: str | None = Field(default=None, max_length=100)
    value: str | bool | FiniteFloat | None = None
    unit: str | None = Field(default=None, max_length=30)
    answers: dict[str, str] = Field(default_factory=dict, max_length=30)

    @model_validator(mode="after")
    def bounded(self):
        if isinstance(self.value, str) and len(self.value) > 300:
            raise ValueError("Value too long")
        if any(len(k) > 100 or len(v) > 100 for k, v in self.answers.items()):
            raise ValueError("Answer too long")
        return self
