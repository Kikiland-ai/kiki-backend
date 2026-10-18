"""Data-only C-AM-01 renderer contract; never evaluates packet formulas or JavaScript."""

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


DOMAINS = {
    "amplitude": ("normalized", 0.25, 2.0, 0.25, 1.0),
    "frequency": ("Hz", 10.0, 1000.0, 10.0, 100.0),
    "phase": ("degree", 0.0, 180.0, 15.0, 0.0),
}


class SignalControl(StrictModel):
    name: Literal["amplitude", "frequency", "phase"]
    label: str = Field(min_length=1, max_length=100)
    unit: Literal["normalized", "Hz", "degree"]
    min: float
    max: float
    step: float
    default: float

    @model_validator(mode="after")
    def supported_domain(self):
        if (self.unit, self.min, self.max, self.step, self.default) != DOMAINS[
            self.name
        ]:
            raise ValueError("Control differs from the signal-parameters/v1 domain")
        return self


class SignalOutput(StrictModel):
    name: Literal["periodSeconds", "angularFrequency"]
    label: str = Field(min_length=1, max_length=100)
    unit: Literal["s", "rad/s"]

    @model_validator(mode="after")
    def correct_unit(self):
        if self.unit != {"periodSeconds": "s", "angularFrequency": "rad/s"}[self.name]:
            raise ValueError("Signal output has the wrong unit")
        return self


def evaluate_signal(inputs, output):
    """Fixed allowlisted behavior used to check producer/consumer conformance vectors."""
    required = set(DOMAINS) | (
        {"timeSeconds"} if output in ("signal", "reference") else set()
    )
    if set(inputs) != required:
        raise ValueError(
            "Expected exactly the signal controls and, for a trace, timeSeconds"
        )
    for name, (_, low, high, step, _) in DOMAINS.items():
        value = inputs[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("Signal inputs must be finite numbers")
        if (
            not low <= value <= high
            or abs((value - low) / step - round((value - low) / step)) > 1e-8
        ):
            raise ValueError("Signal input is outside its bounds or step")
    frequency = inputs["frequency"]
    if output == "periodSeconds":
        return 1 / frequency
    if output == "angularFrequency":
        return 2 * math.pi * frequency
    if output not in ("signal", "reference"):
        raise ValueError("Unsupported signal output")
    time = inputs["timeSeconds"]
    if (
        isinstance(time, bool)
        or not isinstance(time, (int, float))
        or not math.isfinite(time)
        or not 0 <= time <= 0.02
    ):
        raise ValueError("Trace sample must be inside the 20 ms window")
    amplitude = inputs["amplitude"] if output == "signal" else 1
    phase = math.radians(inputs["phase"]) if output == "signal" else 0
    return amplitude * math.sin(2 * math.pi * frequency * time + phase)


class SignalBehaviorTest(StrictModel):
    inputs: dict[str, float]
    output: Literal["periodSeconds", "angularFrequency", "signal", "reference"]
    expected: float
    tolerance: float = Field(gt=0, le=1e-6)

    @model_validator(mode="after")
    def correct_result(self):
        if (
            abs(evaluate_signal(self.inputs, self.output) - self.expected)
            > self.tolerance
        ):
            raise ValueError("Behavior vector disagrees with the signal model")
        return self


class SourceBinding(StrictModel):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SceneSource(StrictModel):
    origin: str
    label: str = Field(min_length=1)
    url: str | None = None


class SceneReview(StrictModel):
    scientific: Literal["pending", "accepted", "rejected"]


class SignalParametersScene(StrictModel):
    artifactId: Literal["SCENE-AM-01-signal-parameters"]
    renderer: Literal["signal-parameters/v1"]
    placardIds: list[str] = Field(min_length=1, max_length=4)
    prompt: str = Field(min_length=1)
    altText: str = Field(min_length=1)
    controls: list[SignalControl] = Field(min_length=3, max_length=3)
    outputs: list[SignalOutput] = Field(min_length=2, max_length=2)
    timeWindowSeconds: Literal[0.02]
    sampleIntervals: Literal[900]
    reference: Literal["unit_amplitude_zero_phase_same_frequency"]
    amplitudeUnit: Literal["normalized"]
    claim: Literal["ideal_teaching_model"]
    sources: list[SceneSource] = Field(min_length=1)
    bindings: list[SourceBinding] = Field(min_length=2, max_length=2)
    modelBindings: list[SourceBinding] = Field(min_length=2, max_length=2)
    behaviorTests: list[SignalBehaviorTest] = Field(min_length=4)
    review: SceneReview

    @model_validator(mode="after")
    def complete_contract(self):
        if [c.name for c in self.controls] != list(DOMAINS):
            raise ValueError(
                "Signal controls must be amplitude, frequency, phase, in order"
            )
        if [o.name for o in self.outputs] != ["periodSeconds", "angularFrequency"]:
            raise ValueError(
                "Signal readouts must be period and angular frequency, in order"
            )
        if len(set(self.placardIds)) != len(self.placardIds):
            raise ValueError("Scene placard slots must be unique")
        if {t.output for t in self.behaviorTests} != {
            "periodSeconds",
            "angularFrequency",
            "signal",
            "reference",
        }:
            raise ValueError(
                "Conformance vectors must cover both readouts and both traces"
            )
        for group in (self.bindings, self.modelBindings):
            if len({b.path for b in group}) != len(group):
                raise ValueError("Source bindings must be unique")
        return self
