"""Load the pinned, authored demo definition without importing synthetic users."""

import hashlib
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "docs/architecture/examples/dsb-sc.demo-definition.json"
DEFINITION = json.loads(PATH.read_text())
# Same canonical encoding used by the proposed lab-tracking contract.
DEFINITION_HASH = hashlib.sha256(json.dumps(DEFINITION, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
CHECKPOINTS = {cp["id"]: cp for cp in DEFINITION["checkpoints"]}
ORDER = list(CHECKPOINTS)


def expected_condition(checkpoint_id):
    return {"CP-DSB-11": "phase_fault", "CP-DSB-12": "restored_baseline"}.get(checkpoint_id, "baseline")
