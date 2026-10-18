"""Explicit candidate envelope reusing the current web's narration and legacy scene types.

Not a second publisher. The current API scene union needs extension and React marks this renderer unsupported; the export CLI must never apply it to cloud storage.
"""

from copy import deepcopy
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, create_model, model_validator

from contracts.concept_canvas import ConceptCanvasArtifact
from contracts.signal_scene import SignalParametersScene


@lru_cache
def concept_narration_model(web_models):
    @model_validator(mode="after")
    def identity(self):
        if (
            self.assetId != self.audioSha256
            or self.renditionId != f"{self.conceptId}.concept.{self.lang}"
        ):
            raise ValueError(
                "Concept rendition identity must follow its concept, language and asset"
            )
        if len(set(self.placardIds)) != len(self.placardIds):
            raise ValueError("Concept audio placards must be unique")
        checks = (
            self.review.pronunciation,
            self.review.nativeOdia,
            self.review.spokenFidelity,
            self.review.audioQuality,
        )
        if (self.review.status == "reviewed") != all(c == "accepted" for c in checks):
            raise ValueError("Reviewed narration needs all checks accepted")
        return self

    common = {
        name: (field.annotation, deepcopy(field))
        for name, field in web_models.NarrationRendition.model_fields.items()
        if name not in ("renditionId", "placardId")
    }
    return create_model(
        "ConceptNarrationRendition",
        __base__=web_models.WireModel,
        __validators__={"identity": identity},
        **common,
        scope=(Literal["concept"], ...),
        conceptId=(str, Field(pattern=r"^C-AM-(0[1-9]|10)$")),
        renditionId=(str, Field(pattern=r"^C-AM-(0[1-9]|10)\.concept\.(en|or)$")),
        placardIds=(list[str], Field(min_length=1, max_length=4)),
    )


@lru_cache
def candidate_manifest_model(web_models, *, signal=False):
    scene = Annotated[
        (SignalParametersScene if signal else ConceptCanvasArtifact)
        | web_models.PhaseRecoveryScene,
        Field(discriminator="renderer"),
    ]
    return create_model(
        "CandidateMediaManifest",
        __base__=web_models.MediaManifest,
        narration=(
            list[web_models.NarrationRendition | concept_narration_model(web_models)],
            ...,
        ),
        artifacts=(list[scene], ...),
    )
