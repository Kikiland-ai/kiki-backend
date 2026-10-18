"""Project the saved signal scene and authored source into a bounded renderer contract."""

import hashlib
import json
import math

from contracts.signal_scene import SignalParametersScene


def signal_vectors():
    base = {"amplitude": 1, "frequency": 100, "phase": 0}
    cases = [
        ({}, "periodSeconds", 0.01),
        ({}, "angularFrequency", 200 * math.pi),
        ({"frequency": 10}, "periodSeconds", 0.1),
        ({"frequency": 1000}, "periodSeconds", 0.001),
        ({"timeSeconds": 0}, "signal", 0),
        ({"timeSeconds": 0.0025}, "signal", 1),
        ({"amplitude": 0.25, "timeSeconds": 0.0025}, "signal", 0.25),
        ({"amplitude": 2, "timeSeconds": 0.0025}, "signal", 2),
        ({"phase": 90, "timeSeconds": 0}, "signal", 1),
        ({"phase": 180, "timeSeconds": 0.0025}, "signal", -1),
        ({"amplitude": 2, "phase": 90, "timeSeconds": 0}, "reference", 0),
        ({"amplitude": 0.25, "phase": 180, "timeSeconds": 0.0025}, "reference", 1),
        ({"frequency": 1000, "timeSeconds": 0.00025}, "signal", 1),
    ]
    return [
        {
            "inputs": {**base, **changes},
            "output": output,
            "expected": round(expected, 12),
            "tolerance": 1e-8,
        }
        for changes, output, expected in cases
    ]


def project_signal(saved, source, lesson, media, library):
    scene = saved["scene"]
    if (
        source["id"] != "C-AM-01"
        or saved["conceptId"] != source["id"]
        or scene["kind"] != "signal"
    ):
        raise ValueError("Unsupported signal source")
    modalities = source["explanation"]["modalities"]
    interactive, visual = modalities["interactive"], modalities["textImage"]["visual"]
    if scene["sourceInteractive"] != interactive or scene["visualBrief"] != visual:
        raise ValueError("Saved signal scene differs from its authored source")
    if (interactive["kind"], visual["kind"]) != ("parameter_sweep", "waveform"):
        raise ValueError("Unsupported signal interaction")
    if [(o["name"], o["unit"], o["formula"]) for o in interactive["outputs"]] != [
        ("T", "s", "1/f"),
        ("omega", "rad/s", "2*pi*f"),
    ]:
        raise ValueError("Unsupported signal readout definition")
    frequency = scene["controls"][1]
    [authored] = interactive["inputs"]
    if authored["name"] != "f" or any(
        authored[k] != frequency[k]
        for k in ("label", "unit", "min", "max", "step", "default")
    ):
        raise ValueError("Frequency control differs from its authored domain")
    # Read bytes through the checksum/path-checked library, not an arbitrary packet path.
    rows = library.connection.execute(
        "SELECT role,asset_id FROM artifacts WHERE concept_id=? AND revision=? AND role IN (?,?)",
        (saved["conceptId"], saved["experienceRevision"], "scene.json", "models.js"),
    ).fetchall()
    if {row["role"] for row in rows} != {"scene.json", "models.js"}:
        raise ValueError("Signal scene/model assets are missing")
    model_bindings = []
    for row in sorted(rows, key=lambda row: row["role"]):
        data, mime = library.asset(row["asset_id"])
        if (
            mime
            != {"scene.json": "application/json", "models.js": "text/javascript"}[
                row["role"]
            ]
        ):
            raise ValueError("Signal asset has the wrong media type")
        if row["role"] == "scene.json" and json.loads(data) != scene:
            raise ValueError("Saved scene does not match its bound asset")
        model_bindings.append(
            {
                "path": f"concept-library/C-AM-01/{saved['experienceRevision']}/{row['role']}",
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return SignalParametersScene(
        artifactId="SCENE-AM-01-signal-parameters",
        renderer="signal-parameters/v1",
        placardIds=media.card_ids(lesson),
        prompt=interactive["prompt"],
        altText=visual["alt"],
        controls=scene["controls"],
        outputs=[
            {
                "name": "periodSeconds",
                "label": interactive["outputs"][0]["label"],
                "unit": "s",
            },
            {
                "name": "angularFrequency",
                "label": interactive["outputs"][1]["label"],
                "unit": "rad/s",
            },
        ],
        timeWindowSeconds=0.02,
        sampleIntervals=900,
        reference="unit_amplitude_zero_phase_same_frequency",
        amplitudeUnit="normalized",
        claim="ideal_teaching_model",
        sources=[visual["from"]],
        bindings=media.scene_bindings(source),
        modelBindings=model_bindings,
        behaviorTests=signal_vectors(),
        review={"scientific": "pending"},
    )
