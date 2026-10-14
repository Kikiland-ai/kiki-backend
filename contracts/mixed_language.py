"""Frontend-admissible prepared-source jobs; provider policy stays server-side."""
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, StrictBool

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class LanguageProfile(StrictModel):
    english_proficiency: FiniteFloat = Field(ge=0, le=10)
    odia_proficiency: FiniteFloat = Field(ge=0, le=10)

class AudioChoice(StrictModel):
    enabled: StrictBool

class CreateMixedLanguageJob(StrictModel):
    source: dict[str, Any] = Field(description='Complete mixed-script-input/v1 prepared English source, glossary and protected literals.')
    profile: LanguageProfile
    audio: AudioChoice

class JobStage(BaseModel):
    status: str

class MixedLanguageJob(BaseModel):
    schema_version: str = Field(alias="schema")
    job_id: str
    revision: int
    status: str
    created_at: str
    updated_at: str
    profile: LanguageProfile
    stages: dict[str, JobStage]
    attempts: int
    error: dict[str, Any] | None
    source_id: str
    source_sha256: str
    text_ready: bool
    audio_ready: bool
    provenance: dict[str, Any]
    review: dict[str, str]
    links: dict[str, str | None]

class MixedLanguageResult(BaseModel):
    schema_version: str = Field(alias="schema")
    job_id: str
    source: dict[str, Any]
    profile: LanguageProfile
    translation: dict[str, Any]
    mixed: dict[str, Any]
    paragraph: str
    speech_script: str
    validation: dict[str, str]
    provenance: dict[str, Any]
    audio: dict[str, Any]
