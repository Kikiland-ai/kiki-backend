"""Check kiki-pedagogy-packet/v1 and kiki-chapter-plan/v1 files.

Structural and pedagogy lints, canvas behaviour-case evaluation, and the backend's real
mixed-script `validate_input` on every placard projection. Standard library only.

Usage:
    python -X utf8 -B check_packet.py FILE... [--emit-mixed-inputs DIR] [--json]
Exit code 0 when no errors (warnings allowed), 1 otherwise, 2 for usage problems.
"""

import argparse
import ast
import json
import math
import re
import sys
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
KINDS = ["definition", "concept", "application", "recap"]
BLOOM = {"remember", "understand", "apply", "analyse", "evaluate", "create"}
DIMS = {"concept", "words", "english", "lab"}
QTYPES = {"mcq", "multi_select", "numerical", "term_match", "fill_blank", "order_steps", "label_diagram",
          "short_english", "spoken", "long_written", "diagram", "derivation", "predict", "code"}
MARKS = {"sweep", "marker", "lens", "connect", "circle"}
CLAIM_KINDS = {"definition", "fact", "relation", "condition", "idealisation", "procedure", "convention",
               "misconception_evidence"}
SCENE_UNITS = {"", "normalized", "Hz", "degree"}
EXTRA_UNITS = {"V", "s", "rad"}
INTERACTIONS = {"parameter_sweep", "step_through", "label_parts", "sort_steps", "compare_toggle", "simulation"}
BANNED_OPTIONS = re.compile(r"\b(all|none) of the above\b", re.I)
LITERAL_HINT = re.compile(r"[=^_*/<>]|\b\d")


def find_backend(start):
    for parent in [start, *start.parents]:
        if (parent / "prototypes" / "mixed_script" / "pipeline.py").is_file():
            return parent
    return None


def occurrences(text, phrase):
    # Identical to prototypes/mixed_script/pipeline.py occurrences().
    return len(re.findall(r"(?<![A-Za-z0-9_])" + re.escape(phrase) + r"(?![A-Za-z0-9_])", text))


# ---------------------------------------------------------------- safe formula evaluation
FUNCS = {"exp": math.exp, "log": math.log, "sqrt": math.sqrt, "abs": abs, "min": min, "max": max,
         "sin": math.sin, "cos": math.cos, "tan": math.tan}
TRIG = {"sin", "cos", "tan"}


def evaluate(formula, names):
    tree = ast.parse(formula.replace("^", "**"), mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id == "pi":
                return math.pi
            if node.id in names:
                return float(names[node.id])
            raise ValueError(f"unknown name '{node.id}'")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = ev(node.operand)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp):
            a, b = ev(node.left), ev(node.right)
            ops = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b,
                   ast.Div: lambda: a / b, ast.Pow: lambda: a ** b}
            for op, fn in ops.items():
                if isinstance(node.op, op):
                    return fn()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
            return float(FUNCS[node.func.id](*[ev(a) for a in node.args]))
        raise ValueError("unsupported expression element")

    return ev(tree)


def uses_trig(formula):
    return any(re.search(rf"\b{f}\s*\(", formula) for f in TRIG)


# ---------------------------------------------------------------- reporting
class Report:
    def __init__(self, path):
        self.path, self.errors, self.warnings, self.info = str(path), [], [], []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def need(r, obj, keys, where):
    if not isinstance(obj, dict):
        r.err(where, "expected an object")
        return False
    missing = [k for k in keys if k not in obj]
    if missing:
        r.err(where, f"missing {', '.join(missing)}")
    return not missing


def text(v):
    return isinstance(v, str) and v.strip() != ""


def words(s):
    return len(s.split())


# ---------------------------------------------------------------- packet
def check_packet(p, r, backend_validate, emit_dir):
    top = ["schema", "packetId", "scope", "status", "research", "learner", "objectives", "terms", "usesTerms",
           "teaching", "placards", "visual", "canvas", "handoff"]
    if not need(r, p, top, "packet"):
        return
    scope = p["scope"]
    need(r, scope, ["lessonPlanId", "broadConceptId", "conceptId", "order", "canonicalKey", "title",
                    "subjectProfileId", "hasPractical"], "scope")
    cid = scope.get("conceptId", "?")
    for key in ("packetId",):
        if not ID.fullmatch(str(p.get(key, ""))):
            r.err(key, "invalid id")
    if not re.fullmatch(r"[a-z0-9-]+", str(scope.get("canonicalKey", ""))):
        r.err("scope.canonicalKey", "needs a lowercase slug")
    st = p["status"]
    if st.get("review") not in ("draft", "auto_checked"):
        r.err("status.review", "packets are authored as draft (or auto_checked after validation); never teacher_checked here")
    for k in ("scientific", "nativeOdia", "pronunciation"):
        if st.get(k) != "pending":
            r.warn(f"status.{k}", "should stay 'pending' until a named person reviews it")

    # research
    res = p["research"]
    need(r, res, ["governingQuestion", "sources", "claims", "outOfScope", "openQuestions"], "research")
    sources = {s.get("id"): s for s in res.get("sources", []) if isinstance(s, dict)}
    if not sources:
        r.err("research.sources", "at least one source is required")
    for sid, s in sources.items():
        need(r, s, ["id", "origin", "tier", "label"], f"source {sid}")
        if s.get("url") and not str(s["url"]).startswith("https://"):
            r.err(f"source {sid}", "url must be https")
        if not s.get("url") and not s.get("locator"):
            r.warn(f"source {sid}", "neither url nor locator; a reviewer cannot find it")
    claims = {}
    for c in res.get("claims", []):
        if not need(r, c, ["id", "kind", "text", "sourceIds", "confidence", "check"], f"claim {c.get('id')}"):
            continue
        claims[c["id"]] = c
        if c["kind"] not in CLAIM_KINDS:
            r.err(f"claim {c['id']}", f"unknown kind {c['kind']}")
        if c["confidence"] not in ("high", "moderate", "low"):
            r.err(f"claim {c['id']}", "confidence must be high|moderate|low")
        if not c["sourceIds"] and not str(c["check"]).startswith("derived"):
            r.err(f"claim {c['id']}", "needs a source or a recorded derivation (check: 'derived: ...')")
        for sid in c["sourceIds"]:
            if sid not in sources:
                r.err(f"claim {c['id']}", f"unknown source {sid}")
    if not claims:
        r.err("research.claims", "claim ledger is empty")

    def ref_claims(ids, where, required=True):
        if required and not ids:
            r.err(where, "must cite at least one claim")
        for i in ids or []:
            if i not in claims:
                r.err(where, f"unknown claim {i}")
            elif claims[i]["confidence"] == "low":
                r.err(where, f"uses low-confidence claim {i}; resolve it or move it to openQuestions")

    # learner
    ln = p["learner"]
    need(r, ln, ["prerequisiteIds", "externalPrerequisites", "troublesome", "misconceptions"], "learner")
    mis = {}
    for m in ln.get("misconceptions", []):
        if not need(r, m, ["id", "statement", "correction", "basis"], f"misconception {m.get('id')}"):
            continue
        mis[m["id"]] = m
        if m["basis"] == "documented" and not m.get("sourceIds"):
            r.err(f"misconception {m['id']}", "documented misconceptions need sourceIds")
        if m["basis"] == "inferred" and not text(m.get("reasoning")):
            r.err(f"misconception {m['id']}", "inferred misconceptions need reasoning")
        if m["basis"] not in ("documented", "inferred"):
            r.err(f"misconception {m['id']}", "basis must be documented|inferred")
        for sid in m.get("sourceIds", []):
            if sid not in sources:
                r.err(f"misconception {m['id']}", f"unknown source {sid}")
    if not mis:
        r.err("learner.misconceptions", "at least one misconception is required")

    # objectives
    objs = {}
    for o in p["objectives"]:
        if not need(r, o, ["id", "statement", "bloom", "parentId", "ownerId"], f"objective {o.get('id')}"):
            continue
        objs[o["id"]] = o
        if o["bloom"] not in BLOOM:
            r.err(f"objective {o['id']}", "unknown bloom level")
        if o["ownerId"] != cid:
            r.err(f"objective {o['id']}", "packet objectives must be owned by this concept")
    if not objs:
        r.err("objectives", "at least one owned objective is required")

    # terms
    glossary = {}
    english = {}
    for group, owned in (("terms", True), ("usesTerms", False)):
        for t in p[group]:
            keys = ["id", "term", "definition", "ownerConceptId", "spoken_en", "glosses", "pronunciations", "review_status"]
            if not need(r, t, keys, f"{group} {t.get('id')}"):
                continue
            if t["id"] in glossary or t["term"] in english:
                r.err(f"{group} {t['id']}", "duplicate term id or text")
            glossary[t["id"]], english[t["term"]] = t, t["id"]
            if owned != (t["ownerConceptId"] == cid):
                r.err(f"{group} {t['id']}", "terms must be owned here; usesTerms owned elsewhere")
            for f in ("glosses", "pronunciations"):
                if not text((t.get(f) or {}).get("or")):
                    r.err(f"{group} {t['id']}", f"{f}.or draft is required by the pipeline glossary")
            if t["review_status"] != "pending":
                r.warn(f"{group} {t['id']}", "review_status should be 'pending' for drafts")
            if len(t["term"]) < 3:
                r.warn(f"{group} {t['id']}", "very short terms over-match in sentences")
    if not p["terms"]:
        r.warn("terms", "concept introduces no terms; confirm that is intended")

    # teaching
    tc = p["teaching"]
    need(r, tc, ["canDo", "keyIdea", "explanation", "example", "workedQuestion", "selfExplainPrompt",
                 "checks", "examSignal", "estMinutes"], "teaching")
    ex = tc.get("explanation", {})
    etext = ex.get("text", "")
    n = words(etext)
    if not 60 <= n <= 140:
        r.err("teaching.explanation.text", f"{n} words; ledger wants 60-140")
    steps = ex.get("walkthrough", [])
    if not 3 <= len(steps) <= 8:
        r.err("teaching.explanation.walkthrough", f"{len(steps)} steps; needs 3-8")
    for i, s in enumerate(steps, 1):
        if s.get("target") not in etext:
            r.err(f"walkthrough step {i}", "target not found verbatim in explanation text")
        if s.get("mark") not in MARKS or s.get("dim") not in DIMS:
            r.err(f"walkthrough step {i}", "invalid mark or dim")
        if s.get("dim") == "lab" and not scope.get("hasPractical"):
            r.err(f"walkthrough step {i}", "lab mark without a practical")
        say, target = str(s.get("say", "")), str(s.get("target", ""))
        if not text(say):
            r.err(f"walkthrough step {i}", "no narration")
        elif not any(w.lower() in say.lower() for w in target.split() if len(w) > 3):
            r.warn(f"walkthrough step {i}", "narration does not mention its target; signalling is lost")
    exm = tc.get("example", {})
    if not (text(exm.get("scenario")) and text(exm.get("takeaway"))):
        r.err("teaching.example", "needs scenario and takeaway")
    wq = tc.get("workedQuestion", {})
    if need(r, wq, ["id", "type", "marks", "prompt", "modelAnswer", "rubric", "examVocabulary"], "workedQuestion"):
        if wq["type"] not in QTYPES:
            r.err("workedQuestion", "unknown type")
        if sum(c.get("marks", 0) for c in wq["rubric"]) != wq["marks"]:
            r.err("workedQuestion", "rubric marks do not add up")
        for c in wq["rubric"]:
            if c.get("objectiveId") and c["objectiveId"] not in objs:
                r.err("workedQuestion", f"rubric objective {c['objectiveId']} not owned")
        for tid in wq["examVocabulary"]:
            if tid not in glossary:
                r.err("workedQuestion", f"examVocabulary {tid} is not in terms/usesTerms")
    es = tc.get("examSignal", {})
    if es.get("basis") not in ("past_papers", "estimate", "none"):
        r.err("teaching.examSignal", "basis must be past_papers|estimate|none")

    checks = tc.get("checks", [])
    ids = set()
    covered = set()
    mcq_concept = []
    for q in checks:
        where = f"check {q.get('id')}"
        if not need(r, q, ["id", "type", "dimension", "prompt", "answer", "explanation", "objectiveIds", "difficulty"], where):
            continue
        if q["id"] in ids:
            r.err(where, "duplicate id")
        ids.add(q["id"])
        if q["type"] not in QTYPES or q["dimension"] not in DIMS:
            r.err(where, "unknown type or dimension")
        if q["dimension"] == "lab" and not scope.get("hasPractical"):
            r.err(where, "lab check without a practical")
        for oid in q["objectiveIds"]:
            if oid not in objs:
                r.err(where, f"tests {oid}, which this concept does not own")
            covered.add(oid)
        if q["difficulty"] not in (1, 2, 3):
            r.err(where, "difficulty must be 1, 2 or 3")
        ref_claims(q.get("claimIds", []), where, required=q["dimension"] == "concept")
        if q["type"] in ("mcq", "term_match", "multi_select"):
            opts = q.get("options") or []
            if q["type"] != "multi_select" and q["answer"] not in opts:
                r.err(where, "answer must be one of its options")
            if not 3 <= len(opts) <= 4:
                r.err(where, f"{len(opts)} options; use 3 or 4")
            if len(set(map(str.strip, opts))) != len(opts):
                r.err(where, "duplicate options")
            if any(BANNED_OPTIONS.search(o) for o in opts):
                r.err(where, "no all/none of the above")
            if q["type"] == "mcq":
                rat = q.get("distractorRationale") or {}
                for o in opts:
                    if o == q["answer"]:
                        continue
                    why = rat.get(o)
                    if not text(why):
                        r.err(where, f"distractor '{o}' has no rationale")
                    elif not (why in mis or why.startswith("error:")):
                        r.err(where, f"distractor rationale '{why}' must be a misconception id or 'error: ...'")
                lens = [len(o) for o in opts]
                if len(q["answer"]) == max(lens) and max(lens) > 1.6 * sorted(lens)[-2]:
                    r.warn(where, "correct option is much longer than the others")
        if words(q["explanation"]) < 6:
            r.warn(where, "explanation too thin to teach; say why right and why the tempting option is wrong")
        if q["dimension"] == "concept" and q["type"] == "mcq":
            mcq_concept.append(q)
    if len(mcq_concept) != 5:
        r.err("teaching.checks", f"{len(mcq_concept)} concept MCQs; the concept check needs exactly 5")
    else:
        pos = {q["options"].index(q["answer"]) for q in mcq_concept if q["answer"] in q.get("options", [])}
        if len(pos) < 2:
            r.warn("teaching.checks", "correct answer always in the same position")
        diffs = {q["difficulty"] for q in mcq_concept}
        if not ({1, 3} & diffs) or max(diffs) < 2:
            r.warn("teaching.checks", "difficulty does not progress")
    for need_dim, types in (("words", {"term_match", "fill_blank"}), ("english", {"short_english", "spoken", "long_written"})):
        if not any(q.get("dimension") == need_dim and q.get("type") in types for q in checks):
            r.err("teaching.checks", f"needs a {need_dim} check ({'/'.join(sorted(types))})")
    if scope.get("hasPractical") and not any(q.get("dimension") == "lab" for q in checks):
        r.err("teaching.checks", "concept with a practical needs a lab check")
    for oid in objs:
        if oid not in covered:
            r.err(f"objective {oid}", "no check evidences this objective")

    # placards
    pls = p["placards"]
    kinds = [pl.get("kind") for pl in pls]
    if kinds != KINDS:
        r.err("placards", f"need exactly {KINDS} in order, got {kinds}")
    seen_sent = set()
    refuted = set()
    projections = []
    for pl in pls:
        where = f"placard {pl.get('id')}"
        if not need(r, pl, ["id", "kind", "title", "sentences"], where):
            continue
        if not ID.fullmatch(pl["id"]):
            r.err(where, "invalid id")
        sents = pl["sentences"]
        if not 1 <= len(sents) <= 10:
            r.err(where, f"{len(sents)} sentences; pipeline accepts 1-10")
        lo, hi = {"definition": (1, 3), "concept": (3, 6), "application": (2, 5), "recap": (2, 4)}.get(pl["kind"], (1, 10))
        if not lo <= len(sents) <= hi:
            r.warn(where, f"{len(sents)} sentences; {pl['kind']} placards usually have {lo}-{hi}")
        used_claims = []
        placard_terms = set()
        for s in sents:
            sw = f"{where} {s.get('id')}"
            if not need(r, s, ["id", "english", "term_ids", "literals", "claimIds"], sw):
                continue
            if not ID.fullmatch(s["id"]) or s["id"] in seen_sent:
                r.err(sw, "invalid or duplicate sentence id")
            seen_sent.add(s["id"])
            e = s["english"]
            n = words(e)
            if n > 45:
                r.err(sw, f"{n} words; split it")
            elif n > 32:
                r.warn(sw, f"{n} words; aim for 8-28")
            if re.search(r"[μ≤≥≠πΩ∞→×·]", e):
                r.warn(sw, "Unicode math symbol; use ASCII and put it in a literal")
            expected = {tid for term, tid in english.items() if occurrences(e, term)}
            if set(s["term_ids"]) != expected:
                r.err(sw, f"term_ids {sorted(s['term_ids'])} must equal glossary occurrences {sorted(expected)}")
            placard_terms |= expected
            covered_text = e
            for lit in sorted(s["literals"], key=lambda l: -len(str(l.get("text", "")))):
                if not (text(lit.get("text")) and text(lit.get("spoken"))):
                    r.err(sw, "literal needs text and spoken")
                elif lit["text"] not in e:
                    r.err(sw, f"literal '{lit['text']}' not in sentence")
                else:
                    covered_text = covered_text.replace(lit["text"], " ")
            for t in english:
                covered_text = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])", " ", covered_text)
            lint_pipeline_counts(s, english, glossary, r, sw)
            leftovers = [tok for tok in re.findall(r"\S+", covered_text) if LITERAL_HINT.search(tok.strip(".,;:()"))]
            if leftovers:
                r.warn(sw, f"possible unprotected formula/number/symbol: {leftovers[:4]}")
            ref_claims(s["claimIds"], sw, required=pl["kind"] != "recap")
            used_claims += s["claimIds"]
            for mid in s.get("refutesMisconceptionIds", []):
                if mid not in mis:
                    r.err(sw, f"unknown misconception {mid}")
                refuted.add(mid)
        if not placard_terms:
            r.err(where, "contains no glossary term; the pipeline glossary would be empty")
        if pl.get("canvasState") and not p["canvas"]:
            r.err(where, "canvasState without a canvas")
        projections.append(project(p, pl, placard_terms, used_claims, claims, sources, glossary, r))
    if not refuted:
        r.err("placards", "no sentence refutes a misconception (refutesMisconceptionIds)")

    # visual
    v = p["visual"]
    if not (text(v.get("kind")) and text(v.get("description")) and text(v.get("alt"))):
        r.err("visual", "needs kind, description and alt")

    # canvas
    if p["canvas"] is None:
        if not text(p.get("canvasNullReason")):
            r.err("canvas", "null canvas needs canvasNullReason")
    else:
        check_canvas(p["canvas"], p, objs, mis, r)

    # backend validation and emission
    for proj in projections:
        if proj is None:
            continue
        if backend_validate:
            try:
                backend_validate(proj)
            except Exception as exc:  # PipelineError and anything unexpected
                r.err(f"mixed-script-input {proj['id']}", f"backend validate_input rejected: {exc}")
        if emit_dir:
            emit_dir.mkdir(parents=True, exist_ok=True)
            (emit_dir / f"{proj['id']}.mixed-input.json").write_text(
                json.dumps(proj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    r.info.append(f"{cid}: {len(pls)} placards, {sum(len(pl.get('sentences', [])) for pl in pls)} sentences, "
                  f"{len(checks)} checks, {len(p['terms'])}+{len(p['usesTerms'])} terms, "
                  f"canvas={'yes' if p['canvas'] else 'no'}")


NUM = re.compile(r"(?<![A-Za-z0-9_])[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def lint_pipeline_counts(s, english, glossary, r, sw):
    """Catch inputs that pass validate_input but will fail validate_stage after translation.

    validate_stage counts each literal by raw substring and each term's spoken_en in the speech
    text, and rejects new numbers in speech. Ordinary English words become Odia, so any literal
    hidden inside an ordinary word (or spoken overlap) changes the counts.
    """
    e, lits = s["english"], [l for l in s["literals"] if text(l.get("text")) and text(l.get("spoken"))]
    bounded = []
    for l in lits:
        for m in re.finditer(re.escape(l["text"]), e):
            if not (m.start() > 0 and e[m.start() - 1].isalnum() and l["text"][0].isalnum()) and \
               not (m.end() < len(e) and e[m.end()].isalnum() and l["text"][-1].isalnum()):
                bounded.append((m.start(), m.end()))
    for l in lits:
        for m in re.finditer(re.escape(l["text"]), e):
            if not any(a <= m.start() and m.end() <= b for a, b in bounded):
                r.err(sw, f"literal '{l['text']}' also occurs inside an ordinary word; the translated count will change")
                break
    sentence_numbers = set(NUM.findall(e))
    for l in lits:
        extra = set(NUM.findall(l["spoken"])) - sentence_numbers
        if extra:
            r.err(sw, f"spoken form of '{l['text']}' introduces numbers {sorted(extra)}; write numbers as words")
        for tid, t in glossary.items():
            if occurrences(l["spoken"].casefold(), t["spoken_en"].casefold()):
                r.err(sw, f"spoken form of '{l['text']}' contains term speech '{t['spoken_en']}'; the speech term count will change")
    for a in glossary.values():
        for b in glossary.values():
            if a is b or not (occurrences(e, a["term"]) or occurrences(e, b["term"])):
                continue
            if occurrences(b["spoken_en"].casefold(), a["spoken_en"].casefold()) and not occurrences(b["term"], a["term"]):
                r.err(sw, f"'{a['spoken_en']}' is spoken inside '{b['spoken_en']}' but '{a['term']}' is not inside "
                          f"'{b['term']}'; speech counts will disagree")


def project(p, pl, placard_terms, used_claims, claims, sources, glossary, r):
    refs, seen = [], set()
    for cid in used_claims:
        for sid in claims.get(cid, {}).get("sourceIds", []):
            s = sources.get(sid, {})
            if s.get("url") and s["url"] not in seen:
                seen.add(s["url"])
                refs.append({"title": s["label"], "url": s["url"]})
    if not refs:
        for s in sources.values():  # recap placards cite no claims: fall back to packet sources
            if s.get("url") and s["url"] not in seen:
                seen.add(s["url"])
                refs.append({"title": s["label"], "url": s["url"]})
    if not refs:
        r.err(f"placard {pl['id']}", "no https source to cite; the pipeline requires one reference")
        return None
    return {
        "schema": "mixed-script-input/v1",
        "id": pl["id"],
        "title": f"{p['scope']['title']} — {pl['title'].get('en', pl['kind'])}",
        "source": {"kind": "adapted_reference", "review_status": "pending", "references": refs},
        "mix": {"support_language": "or", "script": "Odia", "level": "odia-led-english-terms"},
        "glossary": [{"id": t["id"], "english": t["term"], "meaning_or": t["glosses"]["or"],
                      "pronunciation_or": t["pronunciations"]["or"], "spoken_en": t["spoken_en"],
                      "review_status": t["review_status"] if t["review_status"] in ("pending", "reviewed") else "pending"}
                     for tid, t in glossary.items() if tid in placard_terms],
        "sentences": [{"id": s["id"], "english": s["english"], "term_ids": s["term_ids"],
                       "literals": [{"text": l["text"], "spoken": l["spoken"]} for l in s["literals"]]}
                      for s in pl["sentences"]],
    }


def check_canvas(cv, p, objs, mis, r):
    w = "canvas"
    keys = ["artifactId", "status", "reusesPinnedScene", "kind", "interaction", "purpose", "controls", "model",
            "behaviorCases", "placardStates", "mustShow", "mustNotImply", "claim", "alt"]
    if not need(r, cv, keys, w):
        return
    if cv["claim"] != "ideal_teaching_model":
        r.err(w, "claim must be ideal_teaching_model")
    if cv["interaction"] not in INTERACTIONS:
        r.err(w, "unknown interaction kind")
    pur = cv["purpose"]
    if not text(pur.get("insight")):
        r.err(w, "purpose.insight is required: what should the student notice?")
    for oid in pur.get("objectiveIds", []):
        if oid not in objs:
            r.err(w, f"purpose objective {oid} not owned")
    for mid in pur.get("misconceptionIds", []):
        if mid not in mis:
            r.err(w, f"purpose misconception {mid} unknown")
    if not pur.get("objectiveIds"):
        r.err(w, "purpose must name the objective(s) the widget serves")
    ctr = cv["controls"]
    if not 1 <= len(ctr) <= 3:
        r.err(w, f"{len(ctr)} controls; widgets take 1-3")
    names = {}
    for c in ctr:
        cw = f"canvas control {c.get('name')}"
        if not need(r, c, ["name", "label", "min", "max", "step", "default", "unit"], cw):
            continue
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*", c["name"]) or c["name"] in names:
            r.err(cw, "invalid or duplicate name")
        if not (c["min"] <= c["default"] <= c["max"]) or c["step"] <= 0:
            r.err(cw, "needs min <= default <= max and step > 0")
        if c["unit"] not in SCENE_UNITS:
            (r.warn if c["unit"] in EXTRA_UNITS else r.err)(cw, f"unit '{c['unit']}' is outside the current scene contract")
        names[c["name"]] = c["default"]
    model = cv["model"]
    if not model.get("assumptions"):
        r.err(w, "model.assumptions required (ideal teaching model)")
    outs = model.get("outputs", [])
    if cv["interaction"] == "parameter_sweep" and not outs:
        r.err(w, "parameter_sweep needs model outputs (readouts)")

    def run(inputs):
        env, vals = dict(inputs), {}
        for o in outs:
            v = evaluate(o["formula"], env)
            if not math.isfinite(v):
                raise ValueError(f"{o['name']} is not finite")
            env[o["name"]] = vals[o["name"]] = v
        return vals

    for o in outs:
        if not need(r, o, ["name", "label", "unit", "formula"], f"canvas output {o.get('name')}"):
            return
        if uses_trig(o["formula"]):
            r.warn(f"canvas output {o['name']}", "uses trigonometry; ledger parameter_sweep formulas cannot, so the factory must implement it")
    try:
        run(names)
    except Exception as exc:
        r.err(w, f"formulas fail at defaults: {exc}")
    cases = cv["behaviorCases"]
    if not 3 <= len(cases) <= 7:
        r.err(w, f"{len(cases)} behaviour cases; needs 3-7")
    has_default = False
    for i, case in enumerate(cases, 1):
        cw = f"canvas case {i}"
        inp = {**names, **case.get("inputs", {})}
        if case.get("inputs", {}) == names or all(case.get("inputs", {}).get(k) == v for k, v in names.items()):
            has_default = True
        for k, val in case.get("inputs", {}).items():
            ctl = next((c for c in ctr if c.get("name") == k), None)
            if not ctl:
                r.err(cw, f"unknown control {k}")
            elif not ctl["min"] <= val <= ctl["max"]:
                r.err(cw, f"{k}={val} outside control range")
        if not text(case.get("observation")):
            r.err(cw, "observation (what the student sees) required")
        try:
            got = run(inp)
        except Exception as exc:
            r.err(cw, f"formula evaluation failed: {exc}")
            continue
        tol = case.get("tolerance", 1e-6)
        for k, want in case.get("expect", {}).items():
            if k not in got:
                r.err(cw, f"expects unknown output {k}")
            elif abs(got[k] - want) > tol:
                r.err(cw, f"{k}: expected {want}, model gives {round(got[k], 6)}")
    if not has_default:
        r.warn(w, "no behaviour case at the default control values")
    pids = {pl.get("id") for pl in p["placards"]}
    for ps in cv["placardStates"]:
        if ps.get("placardId") not in pids:
            r.err(w, f"placardState for unknown placard {ps.get('placardId')}")
        for k, val in (ps.get("controls") or {}).items():
            ctl = next((c for c in ctr if c.get("name") == k), None)
            if not ctl or not ctl["min"] <= val <= ctl["max"]:
                r.err(w, f"placardState control {k}={val} unknown or out of range")
    if pur.get("misconceptionIds") and not any(
            any(m in str(c.get("observation", "")) or c.get("showsMisconception") for m in pur["misconceptionIds"])
            for c in cases):
        r.warn(w, "no behaviour case is marked showsMisconception: true; make the misconception visibly fail")


# ---------------------------------------------------------------- chapter plan
def check_plan(p, r):
    if not need(r, p, ["schema", "lessonPlanId", "scope", "title", "governingQuestion", "canDo", "request", "sources",
                       "mece", "objectives", "broadConcepts", "concepts", "route", "practical", "chapterTest"], "plan"):
        return
    shapes = {"chapter": ((2, 5), (2, 5)), "topic": ((1, 1), (2, 5)), "concept": ((1, 1), (1, 1))}
    if p["scope"] not in shapes:
        r.err("scope", "chapter|topic|concept")
        return
    (b0, b1), (c0, c1) = shapes[p["scope"]]
    bcs, cs = p["broadConcepts"], {c["id"]: c for c in p["concepts"]}
    if not b0 <= len(bcs) <= b1:
        r.err("broadConcepts", f"{p['scope']} needs {b0}-{b1}, has {len(bcs)}")
    for m in [p["mece"]] + [b.get("mece", {}) for b in bcs]:
        if not (text(m.get("dimension")) and text(m.get("rationale"))):
            r.err("mece", "every split states dimension and rationale")
    parent = {}
    for b in bcs:
        if not c0 <= len(b["conceptIds"]) <= c1:
            r.err(b["id"], f"needs {c0}-{c1} concepts")
        for cid in b["conceptIds"]:
            if cid not in cs:
                r.err(b["id"], f"unknown concept {cid}")
            if cid in parent:
                r.err(cid, "has two parents")
            parent[cid] = b["id"]
    for cid, c in cs.items():
        if parent.get(cid) != c.get("broadConceptId"):
            r.err(cid, "broadConceptId disagrees with broad concept lists")
        for pre in c.get("prerequisiteIds", []):
            if pre not in cs:
                r.warn(cid, f"prerequisite {pre} is outside this plan")
    state = {}

    def visit(n, stack):
        if state.get(n) == "done":
            return
        if state.get(n) == "active":
            r.err("prerequisites", "cycle: " + " -> ".join(stack + [n]))
            return
        state[n] = "active"
        for pre in cs.get(n, {}).get("prerequisiteIds", []):
            if pre in cs:
                visit(pre, stack + [n])
        state[n] = "done"

    for n in cs:
        visit(n, [])
    route = p["route"]
    if sorted(route) != sorted(cs):
        r.err("route", "must list every concept exactly once")
    pos = {c: i for i, c in enumerate(route)}
    for cid, c in cs.items():
        for pre in c.get("prerequisiteIds", []):
            if pre in pos and cid in pos and pos[pre] > pos[cid]:
                r.err("route", f"{cid} comes before its prerequisite {pre}")
    pr = p["practical"]
    if pr:
        req = set(pr.get("requiredConceptIds", []))
        closure = set()

        def need_pre(c):
            for pre in cs.get(c, {}).get("prerequisiteIds", []):
                if pre not in closure:
                    closure.add(pre)
                    need_pre(pre)

        for c in req:
            need_pre(c)
        missing = closure - req
        if missing:
            r.err("practical", f"required concepts miss prerequisites {sorted(missing)}")
    test = p["chapterTest"] or []
    if p["scope"] == "chapter" and len(test) != 10:
        r.err("chapterTest", f"needs exactly 10 MCQs, has {len(test)}")
    elif p["scope"] != "chapter" and test and len(test) != 10:
        r.warn("chapterTest", "topic/concept plans need no chapter test; when present it should have 10 items")
    hit = set()
    for q in test:
        if q.get("type") != "mcq" or q.get("answer") not in (q.get("options") or []):
            r.err(f"chapterTest {q.get('id')}", "must be an mcq whose answer is an option")
        if not 3 <= len(q.get("options") or []) <= 4:
            r.err(f"chapterTest {q.get('id')}", "use 3 or 4 options")
        if not text(q.get("explanation")):
            r.err(f"chapterTest {q.get('id')}", "needs an explanation")
        for c in q.get("conceptIds", []):
            if c not in cs:
                r.err(f"chapterTest {q.get('id')}", f"unknown concept {c}")
            hit.add(c)
    if test and len(cs) <= 10 and set(cs) - hit:
        r.err("chapterTest", f"concepts without a test item: {sorted(set(cs) - hit)}")
    r.info.append(f"{p['lessonPlanId']}: {len(bcs)} broad concepts, {len(cs)} concepts, {len(test)} chapter MCQs")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--emit-mixed-inputs", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    backend = find_backend(Path(__file__).resolve()) or find_backend(Path.cwd().resolve())
    validate, note = None, None
    if backend:
        sys.path.insert(0, str(backend))
        try:
            from prototypes.mixed_script.pipeline import validate_input as validate
            note = f"backend validate_input: {backend / 'prototypes/mixed_script/pipeline.py'}"
        except Exception as exc:  # pragma: no cover
            note = f"backend validate_input unavailable ({exc}); projection not checked"
    else:
        note = "kiki-backend not found; projection not checked against validate_input"

    reports, failed = [], False
    for f in a.files:
        r = Report(f)
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            r.err("file", f"cannot read JSON: {exc}")
            doc = None
        if doc is not None:
            schema = doc.get("schema") if isinstance(doc, dict) else None
            if schema == "kiki-pedagogy-packet/v1":
                check_packet(doc, r, validate, a.emit_mixed_inputs)
            elif schema == "kiki-chapter-plan/v1":
                check_plan(doc, r)
            else:
                r.err("schema", f"unsupported schema {schema!r}")
        failed |= bool(r.errors)
        reports.append(r)

    if a.json:
        print(json.dumps({"note": note, "reports": [vars(r) for r in reports]}, ensure_ascii=False, indent=2))
    else:
        print(note)
        for r in reports:
            print(f"\n== {r.path}: {'FAIL' if r.errors else 'PASS'} ({len(r.errors)} errors, {len(r.warnings)} warnings)")
            for line in r.info:
                print("  " + line)
            for e in r.errors:
                print("  ERROR " + e)
            for w in r.warnings:
                print("  WARN  " + w)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
