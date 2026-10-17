"""Validated metadata; the corresponding image travels as a binary message."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrameEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: str = Field(pattern="^frame$")
    capture_epoch: int = Field(ge=1, le=1)
    # Legacy capture clients have one fixed view; writing clients send this explicitly.
    view_revision: int = Field(default=1, ge=1, le=9_007_199_254_740_991)
    sequence: int = Field(ge=1, le=9_007_199_254_740_991)
    captured_elapsed_ms: int = Field(ge=0, le=9_007_199_254_740_991)
    width: int = Field(ge=1, le=1600)
    height: int = Field(ge=1, le=1600)
    source_width: int = Field(ge=1, le=16384)
    source_height: int = Field(ge=1, le=16384)
    byte_count: int = Field(ge=1, le=1_000_000)
    mime_type: str = Field(pattern="^image/jpeg$")

    @model_validator(mode="after")
    def aspect_ratio(self):
        if abs(self.width / self.height - self.source_width / self.source_height) > 0.02:
            raise ValueError("Capture must preserve the source aspect ratio")
        return self
