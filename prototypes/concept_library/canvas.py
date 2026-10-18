"""Reuse all preserved CAM scenes as one source-bound renderer family."""

import json

from contracts.concept_canvas import CONFORMANCE, POLICIES, ConceptCanvasArtifact


def project_canvas(saved, source, lesson, media, library):
    scene = saved["scene"]
    modalities = source["explanation"]["modalities"]
    if saved["conceptId"] != source["id"] or scene["conceptId"] != saved["conceptId"]:
        raise ValueError("Canvas concept identity differs")
    if (
        scene["sourceInteractive"] != modalities["interactive"]
        or scene["visualBrief"] != modalities["textImage"]["visual"]
    ):
        raise ValueError("Canvas differs from its authored interaction/visual source")
    rows = library.connection.execute(
        "SELECT role,asset_id FROM artifacts WHERE concept_id=? AND revision=? AND role IN (?,?)",
        (saved["conceptId"], saved["experienceRevision"], "scene.json", "models.js"),
    ).fetchall()
    if len(rows) != 2 or {r["role"] for r in rows} != {"scene.json", "models.js"}:
        raise ValueError("Canvas scene/model assets are missing or duplicated")
    bindings = []
    for row in sorted(rows, key=lambda row: row["role"]):
        data, mime = library.asset(row["asset_id"])
        if (
            mime
            != {"scene.json": "application/json", "models.js": "text/javascript"}[
                row["role"]
            ]
        ):
            raise ValueError("Canvas asset media type differs")
        if row["role"] == "scene.json" and json.loads(data) != scene:
            raise ValueError("Canvas does not match its bound scene asset")
        if row["role"] == "models.js" and row["asset_id"] != POLICIES["modelsSha256"]:
            raise ValueError("Canvas uses unrecognised model code")
        bindings.append(
            {
                "path": f"concept-library/{saved['conceptId']}/{saved['experienceRevision']}/{row['role']}",
                "sha256": row["asset_id"],
            }
        )
    return ConceptCanvasArtifact.model_validate(
        {
            "artifactId": saved["conceptId"].replace("C-", "SCENE-") + "-canvas",
            "renderer": "cam-concept-canvas/v1",
            "placardIds": media.card_ids(lesson),
            "scene": scene,
            "sources": [scene["visualBrief"]["from"]],
            "bindings": media.scene_bindings(source),
            "modelBindings": bindings,
            "behaviorTests": CONFORMANCE[saved["conceptId"]],
            "claim": "ideal_teaching_model",
            "review": {"scientific": "pending"},
        }
    )
