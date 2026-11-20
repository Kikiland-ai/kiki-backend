"""Pack-driven pre-lab state machine with transactional, owner-scoped sessions."""
import copy
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import HTTPException

from contracts.physical_lab import ExperimentPack
from .behavior import ADAPTERS

ROOT = Path(__file__).parent
PACKS = ROOT / "packs"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def public(value):
    """Question solutions stay server-side; teaching explanations remain readable."""
    if isinstance(value, list):
        return [public(v) for v in value]
    if isinstance(value, dict):
        hidden = {"correct", "explanation"} if "correct" in value else set()
        return {k: public(v) for k, v in value.items() if k not in hidden}
    return value


def procedure_steps(pack, state):
    omitted = set((pack.get('demo') or {}).get('omit_step_ids', [])) if state.get('mode') == 'experiment_demo' else set()
    return [step for step in pack['steps'] if step['id'] not in omitted]


def load_packs(directory=PACKS):
    packs = {}
    for path in sorted(Path(directory).glob("*.json")):
        pack = ExperimentPack.model_validate_json(path.read_text())
        if pack.id in packs or pack.adapter not in ADAPTERS:
            raise ValueError("Duplicate experiment or unsupported adapter")
        asset = (ROOT / "assets" / pack.asset).resolve()
        if asset.parent != (ROOT / "assets").resolve() or not asset.is_file():
            raise ValueError("Experiment asset must exist in the asset catalogue")
        if hashlib.sha256(asset.read_bytes()).hexdigest() != pack.asset_sha256:
            raise ValueError("Apparatus asset hash differs from the pack")
        gltf = json.loads(asset.read_bytes())
        if {n.get('name') for n in gltf['nodes'] if not n.get('extras', {}).get('decorative')} != {p.id for p in pack.parts}:
            raise ValueError("Apparatus semantic targets differ from the pack")
        packs[pack.id] = pack.model_dump()
    return packs


class PreparationService:
    def __init__(self, data_dir, packs=None):
        self.packs = load_packs() if packs is None else {
            p.id: p.model_dump() for p in (ExperimentPack.model_validate(x) for x in packs)
        }
        self.path = Path(data_dir) / "physical-labs.sqlite"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS physical_sessions (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, create_key TEXT NOT NULL,
                    create_hash TEXT NOT NULL, pack TEXT NOT NULL, state TEXT NOT NULL,
                    UNIQUE(owner, create_key)
                );
                CREATE TABLE IF NOT EXISTS physical_events (
                    session_id TEXT NOT NULL, event_id TEXT NOT NULL, body_hash TEXT NOT NULL,
                    response TEXT NOT NULL, PRIMARY KEY(session_id, event_id)
                );
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def catalogue(self):
        return [{"id": p["id"], "version": p["version"], "title": p["title"],
                 "curriculum": p["curriculum"], "equipment": p["equipment"], "review": p["review"]}
                for p in self.packs.values()]

    def pack(self, experiment_id):
        if experiment_id not in self.packs:
            raise HTTPException(404, "Prescribed experiment not found")
        return public(copy.deepcopy(self.packs[experiment_id]))

    @staticmethod
    def initial_apparatus(pack):
        return {"controls": {k: v["initial"] for k, v in pack["controls"].items()},
                "connections": [], "measurements": {}, "selected": []}

    def create(self, owner, key, body):
        pack = self.packs.get(body.experiment_id)
        if pack is None:
            raise HTTPException(404, "Prescribed experiment not found")
        if body.mode == 'experiment_demo' and not pack.get('demo'):
            raise HTTPException(409, "This experiment has no authored demo setup")
        # Keep existing normal-session creation keys compatible with the v1 body.
        body_hash = digest(body.model_dump(exclude={'mode'}) if body.mode == 'guided_preparation' else body.model_dump())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM physical_sessions WHERE owner=? AND create_key=?", (owner, key)).fetchone()
            if row:
                if row["create_hash"] != body_hash:
                    raise HTTPException(409, "Creation key already used for another request")
                return self.project(json.loads(row["state"]), json.loads(row["pack"]))
            state = {"session_id": secrets.token_hex(16), "revision": 0, "stage": "orientation",
                     "mode": body.mode,
                     "language": body.language, "created_at": now(), "updated_at": now(),
                     "pack_sha256": digest(pack), "orientation_seen": [], "concepts": {},
                     "demonstration_index": 0, "step_index": 0, "observation_index": 0, "procedure_index": 0,
                     "faults": {}, "assessment": None, "attempts": [],
                     "apparatus": self.initial_apparatus(pack), "feedback": None}
            if body.mode == 'experiment_demo':
                state['apparatus']['controls'].update(pack['demo']['initial_controls'])
                first = procedure_steps(pack, state)[0]['rule']['kind']
                state['stage'] = 'observations' if first == 'measure' else 'rehearsal'
            db.execute("INSERT INTO physical_sessions VALUES(?,?,?,?,?,?)",
                       (state["session_id"], owner, key, body_hash, json.dumps(pack), json.dumps(state)))
            return self.project(state, pack)

    @staticmethod
    def owned(db, session_id, owner):
        row = db.execute("SELECT * FROM physical_sessions WHERE id=? AND owner=?", (session_id, owner)).fetchone()
        if row is None:
            raise HTTPException(404, "Preparation session not found")
        return json.loads(row["state"]), json.loads(row["pack"])

    def get(self, session_id, owner):
        with self.connect() as db:
            state, pack = self.owned(db, session_id, owner)
        return self.project(state, pack)

    def list_sessions(self, owner):
        with self.connect() as db:
            rows = db.execute("SELECT state,pack FROM physical_sessions WHERE owner=? ORDER BY rowid DESC LIMIT 100", (owner,)).fetchall()
        return [{k: v for k, v in self.project(json.loads(r["state"]), json.loads(r["pack"])).items()
                 if k in ("session_id", "revision", "stage", "experiment_id", "title", "updated_at", "mode")}
                for r in rows]

    @staticmethod
    def project(state, pack):
        result = copy.deepcopy(state)
        result.update({"schema_version": "physical-lab-session/v1", "experiment_id": pack["id"],
                       "pack_version": pack["version"], "title": pack["title"],
                       "review": pack["review"], "equipment": pack["equipment"],
                       "physical_execution": "not_performed", "english_evidence": "not_assessed"})
        result['mode'] = state.get('mode', 'guided_preparation')
        result['prerequisite_policy'] = 'assumed_for_demo' if result['mode'] == 'experiment_demo' else 'concept_checks_required'
        stage = state["stage"]
        if stage == "orientation":
            activity = {"required_targets": pack["orientation"], "instruction": pack["aim"]}
        elif stage == "prerequisites":
            activity = {"concepts": public(pack["concepts"]), "pass_percent": pack["concept_pass_percent"]}
        elif stage == "demonstration":
            activity = {"step": pack["steps"][state["demonstration_index"]], "student_evidence": False}
        elif stage in ("rehearsal", "observations"):
            index = state.get("procedure_index", state["step_index"] + state["observation_index"])
            steps = procedure_steps(pack, state)
            activity = {"step": steps[index], "independent": True, 'number': index + 1, 'total': len(steps)}
        elif stage == "faults":
            activity = {"faults": public(pack["faults"])}
        elif stage == "assessment":
            activity = {"questions": public(pack["assessment"]), "pass_percent": pack["readiness_pass_percent"]}
        elif stage == 'experiment_complete':
            activity = {'result_url': f"/v1/physical-labs/sessions/{state['session_id']}/experiment-result"}
        else:
            activity = {"receipt_url": f"/v1/physical-labs/sessions/{state['session_id']}/receipt"}
        result["activity"] = activity
        result["links"] = {"self": f"/v1/physical-labs/sessions/{state['session_id']}",
                           "pack": f"/v1/physical-labs/sessions/{state['session_id']}/pack",
                           "events": f"/v1/physical-labs/sessions/{state['session_id']}/events",
                           "observations": f"/v1/physical-labs/sessions/{state['session_id']}/observations"}
        return result

    def session_pack(self, session_id, owner):
        with self.connect() as db:
            _, pack = self.owned(db, session_id, owner)
        return public(pack)

    def observations(self, session_id, owner):
        with self.connect() as db:
            state, pack = self.owned(db, session_id, owner)
        return ADAPTERS[pack["adapter"]]().observations(pack, state["apparatus"])

    @staticmethod
    def grade(questions, answers):
        if set(answers) != {q["id"] for q in questions}:
            raise HTTPException(422, "Submit exactly the questions in this activity")
        if any(answers[q["id"]] not in q["options"] for q in questions):
            raise HTTPException(422, "Unknown answer option")
        results = [{"question_id": q["id"], "correct": answers[q["id"]] == q["correct"],
                    "feedback": q["explanation"]} for q in questions]
        return {"percent": round(sum(r["correct"] for r in results) * 100 / len(results), 2), "results": results}

    def event(self, session_id, owner, event):
        body_hash = digest(event.model_dump())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            state, pack = self.owned(db, session_id, owner)
            existing = db.execute("SELECT body_hash,response FROM physical_events WHERE session_id=? AND event_id=?",
                                  (session_id, event.event_id)).fetchone()
            if existing:
                if existing["body_hash"] != body_hash:
                    raise HTTPException(409, "Event ID already used for another request")
                return json.loads(existing["response"])
            if event.revision != state["revision"]:
                raise HTTPException(409, "Stale session revision; reload before retrying")
            if state["revision"] >= 2000:
                raise HTTPException(409, "Session attempt limit reached; start a new preparation")
            self.apply(state, pack, event)
            state["revision"] += 1
            state["updated_at"] = now()
            response = self.project(state, pack)
            db.execute("UPDATE physical_sessions SET state=? WHERE id=?", (json.dumps(state), session_id))
            db.execute("INSERT INTO physical_events VALUES(?,?,?,?)", (session_id, event.event_id, body_hash, json.dumps(response)))
        return response

    def apply(self, state, pack, event):
        state["feedback"] = None
        stage, kind = state["stage"], event.kind
        if kind == "language":
            if event.value not in ("en", "or"):
                raise HTTPException(422, "Unsupported language")
            state["language"] = event.value
            return
        if stage in ("prepared", "experiment_complete"):
            raise HTTPException(409, "Preparation is complete; create another session to practise again")
        if stage == "orientation":
            if kind == "select" and event.target in pack["orientation"]:
                if event.target not in state["orientation_seen"]:
                    state["orientation_seen"].append(event.target)
            elif kind == "advance":
                state["stage"] = "prerequisites"
            else:
                raise HTTPException(409, "Select an apparatus part or start the prerequisite lessons")
        elif stage == "prerequisites":
            if kind == "advance":
                if not all(state["concepts"].get(c["id"], {}).get("passed") for c in pack["concepts"]):
                    raise HTTPException(409, "Pass the required concept checks first")
                state["stage"] = "demonstration"
                return
            concept = next((c for c in pack["concepts"] if c["id"] == event.target), None)
            if kind != "answer" or concept is None:
                raise HTTPException(409, "Answer a required concept check")
            if not all(state["concepts"].get(c, {}).get("passed") for c in concept["depends_on"]):
                raise HTTPException(409, "Complete this concept's prerequisites first")
            result = self.grade(concept["questions"], event.answers)
            result["passed"] = result["percent"] >= pack["concept_pass_percent"]
            state["concepts"][concept["id"]] = result
            state["feedback"] = result
            self.record(state, event, "concept", result["passed"])
        elif stage == "demonstration":
            if kind != "advance":
                raise HTTPException(409, "Advance the demonstration; it does not count as independent practice")
            state["demonstration_index"] += 1
            if state["demonstration_index"] == len(pack["steps"]):
                state["stage"] = "observations" if pack["steps"][0]["rule"]["kind"] == "measure" else "rehearsal"
                state["apparatus"] = self.initial_apparatus(pack)
        elif stage in ("rehearsal", "observations"):
            self.rehearse(state, pack, event)
        elif stage == "faults":
            if kind == "advance" and all(state["faults"].get(f["id"], {}).get("passed") for f in pack["faults"]):
                state["stage"] = "assessment"
                return
            fault = next((f for f in pack["faults"] if f["id"] == event.target), None)
            if kind != "answer" or fault is None:
                raise HTTPException(409, "Resolve the fault scenarios first")
            result = self.grade([fault["question"]], event.answers)
            result["passed"] = result["percent"] == 100
            state["faults"][fault["id"]] = result
            state["feedback"] = result
            self.record(state, event, "practical", result["passed"])
        elif stage == "assessment":
            if kind != "answer" or event.target != "readiness":
                raise HTTPException(409, "Complete the readiness assessment")
            result = self.grade(pack["assessment"], event.answers)
            result["passed"] = result["percent"] >= pack["readiness_pass_percent"] and all(
                event.answers[q["id"]] == q["correct"] for q in pack["assessment"] if q["required"])
            state["assessment"] = result
            state["feedback"] = result
            self.record(state, event, "practical", result["passed"])
            if result["passed"]:
                state["stage"] = "prepared"

    @staticmethod
    def record(state, event, dimension, passed):
        state["attempts"].append({"event_id": event.event_id, "target": event.target,
                                  "dimension": dimension, "passed": passed, "kind": event.kind,
                                  "context": "virtual_experiment_demo" if state.get('mode') == 'experiment_demo' else "virtual_preparation", "at": now()})

    def rehearse(self, state, pack, event):
        observing = state["stage"] == "observations"
        index_key = "observation_index" if observing else "step_index"
        procedure_index = state.get("procedure_index", state["step_index"] + state["observation_index"])
        steps = procedure_steps(pack, state)
        step = steps[procedure_index]
        rule = step["rule"]
        correct = event.kind == rule["kind"] and event.target == rule["target"] and event.other == rule["other"]
        expected = rule["value"]
        if observing:
            try:
                expected = ADAPTERS[pack["adapter"]]().expected_measurement(pack, state["apparatus"], rule)
            except ValueError as error:
                raise HTTPException(409, str(error)) from None
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            correct = correct and type(event.value) in (int, float) and abs(event.value - expected) <= rule["tolerance"]
        else:
            correct = correct and type(event.value) is type(expected) and event.value == expected
        correct = correct and event.unit == rule["unit"]
        self.record(state, event, "practical", correct)
        if not correct:
            state["feedback"] = {"passed": False, "message": "Not yet. Revisit the highlighted part and its purpose.",
                                  "revisit_targets": [rule["target"]], "why": step["why"]}
            return
        apparatus = state["apparatus"]
        if event.kind == "set":
            control = pack["controls"][event.target]
            if type(event.value) in (int, float):
                if control["minimum"] is not None and event.value < control["minimum"]:
                    raise HTTPException(422, "Control below supported range")
                if control["maximum"] is not None and event.value > control["maximum"]:
                    raise HTTPException(422, "Control above supported range")
            if control["choices"] and event.value not in control["choices"]:
                raise HTTPException(422, "Unsupported control setting")
            apparatus["controls"][event.target] = event.value
        elif event.kind == "connect":
            edge = [event.target, event.other]
            # One signal source per input; moving the probe replaces its old source.
            apparatus["connections"] = [e for e in apparatus["connections"] if e[1] != event.other]
            if edge not in apparatus["connections"]:
                apparatus["connections"].append(edge)
        elif event.kind == "select":
            apparatus["selected"].append(event.target)
        elif event.kind == "measure":
            apparatus["measurements"][step["id"]] = {"value": event.value, "unit": event.unit, "virtual": True}
        state["feedback"] = {"passed": True, "step_id": step["id"]}
        state[index_key] += 1
        state["procedure_index"] = procedure_index + 1
        if state["procedure_index"] == len(steps):
            state["stage"] = "experiment_complete" if state.get('mode') == 'experiment_demo' else "faults"
        else:
            following = steps[state["procedure_index"]]["rule"]["kind"]
            state["stage"] = "observations" if following == "measure" else "rehearsal"

    def experiment_result(self, session_id, owner):
        with self.connect() as db:
            state, pack = self.owned(db, session_id, owner)
        if state.get('mode') != 'experiment_demo' or state['stage'] != 'experiment_complete':
            raise HTTPException(409, 'Complete the experiment demo first')
        observations = ADAPTERS[pack['adapter']]().observations(pack, state['apparatus'])
        return {'schema_version': 'physical-experiment-result/v1', 'session_id': session_id,
                'status': 'experiment_complete', 'experiment_id': pack['id'], 'pack_version': pack['version'],
                'prerequisite_policy': 'assumed_for_demo', 'theory_assessed': False,
                'physical_execution': 'not_performed', 'evidence_context': 'virtual_experiment_demo',
                'completed_steps': len(procedure_steps(pack, state)), 'review': pack['review'],
                'measurements': state['apparatus']['measurements'], 'readings': observations['readings'],
                'model_assumptions': observations.get('assumptions', []),
                'preset_controls': pack['demo']['initial_controls'], 'completed_at': state['updated_at']}

    def receipt(self, session_id, owner):
        with self.connect() as db:
            state, pack = self.owned(db, session_id, owner)
        if state["stage"] != "prepared":
            raise HTTPException(409, "Preparation requirements are not complete")
        return {"schema_version": "physical-lab-receipt/v1", "session_id": session_id,
                "experiment_id": pack["id"], "pack_version": pack["version"], "pack_sha256": state["pack_sha256"],
                "status": "prepared", "physical_execution": "not_performed", "review": pack["review"],
                "evidence": {"concepts": state["concepts"], "orientation_targets": state["orientation_seen"],
                             "independent_steps": state["step_index"], "faults": state["faults"],
                             "virtual_measurements": state["apparatus"]["measurements"],
                             "readiness": state["assessment"], "english": "not_assessed", "words": "not_assessed"},
                "revision_card": {"title": pack["title"], "aim": pack["aim"], "equipment": pack["equipment"],
                                  "procedure": [{"instruction": s["instruction"], "why": s["why"]} for s in pack["steps"]],
                                  "precautions": pack["precautions"], "sources": pack["sources"],
                                  "physical_observations": {"columns": pack["observation_columns"], "rows": []}},
                "completed_at": state["updated_at"]}
