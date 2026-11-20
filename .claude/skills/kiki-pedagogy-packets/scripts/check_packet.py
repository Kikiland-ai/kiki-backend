"""Check kiki-pedagogy-packet/v1 and kiki-chapter-plan/v1 files for any domain and corner.

Structural, domain and corner rules, pedagogy lints, canvas checks (widget behaviour cases are
evaluated; scene-template parameters are validated against kiki contracts v0), cue targets,
the kiki-pack/v0 concept projection and, for Odia targets, the backend's real mixed-script
`validate_input` on every placard projection. Standard library only.

Usage:
    python -X utf8 -B check_packet.py FILE... [--emit DIR] [--json]
Exit code 0 when there are no errors (warnings allowed), 1 otherwise, 2 for usage problems.
"""

import argparse
import ast
import json
import math
import re
import sys
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
KINDS = {"definition", "concept", "example", "application", "recap"}
CASE_KINDS = ["definition", "concept", "application", "recap"]
CORNERS = {"laws", "odds", "audiences"}
CONSUMERS = {"kiki-pack/v0", "learning-case/v1", "lesson-ledger/v2", "mixed-script-input/v1"}
BLOOM = {"remember", "understand", "apply", "analyse", "evaluate", "create"}
DIMS = {"concept", "words", "english", "lab"}
QTYPES = {"mcq", "multi_select", "numerical", "term_match", "fill_blank", "order_steps", "label_diagram",
          "short_english", "spoken", "long_written", "diagram", "derivation", "predict", "code"}
EVALUATES = {"fact", "calculation", "procedure", "process", "diagnosis", "judgement", "recall"}
REASONING = {"process", "diagnosis", "judgement"}
MARKS = {"sweep", "marker", "lens", "connect", "circle"}
CLAIM_KINDS = {"definition", "fact", "relation", "condition", "idealisation", "procedure", "convention",
               "org_rule", "heuristic", "illustrative_data", "misconception_evidence"}
ORG_ORIGINS = {"org_playbook", "org_sop", "org_case", "org_recording", "lecture_notes", "syllabus", "student_notes",
               "experiment_sheet", "past_paper", "teacher"}
ORIGINS = ORG_ORIGINS | {"textbook", "standard", "regulator", "vendor_doc", "research", "curated"}
SCENE_UNITS = {"", "normalized", "Hz", "degree"}
INTERACTIONS = {"parameter_sweep", "step_through", "label_parts", "sort_steps", "compare_toggle", "simulation"}
TEMPLATES = {"candles", "payoff", "line", "flow", "ece"}
ECE_RENDERERS = {"coherent-phase-recovery/v1", "dsb-sc-visual/v1", "cam-concept-canvas/v1"}
PATCH_KEYS = {"show", "hide", "highlight", "focus", "values"}
BANNED_OPTIONS = re.compile(r"\b(all|none) of the above\b", re.I)
LIVE_ADVICE = re.compile(r"\b(you should|we recommend|i recommend|go long|go short)\b|\b(buy|sell) (now|today|this)\b", re.I)
LITERAL_HINT = re.compile(r"[=^_*/<>₹$€£%]|\b\d")
NUM = re.compile(r"(?<![A-Za-z0-9_])[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


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
            for op, fn in ((ast.Add, lambda: a + b), (ast.Sub, lambda: a - b), (ast.Mult, lambda: a * b),
                           (ast.Div, lambda: a / b), (ast.Pow, lambda: a ** b)):
                if isinstance(node.op, op):
                    return fn()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
            return float(FUNCS[node.func.id](*[ev(a) for a in node.args]))
        raise ValueError("unsupported expression element")

    return ev(tree)


# ---------------------------------------------------------------- reporting helpers
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


# ---------------------------------------------------------------- domain
def check_domain(d, r, where="domain"):
    if not need(r, d, ["packId", "corner", "learner", "languages", "dimensionLabels", "assessmentPolicy",
                       "practical", "guardrails", "consumers"], where):
        return None
    if d["corner"] not in CORNERS:
        r.err(where, f"corner must be one of {sorted(CORNERS)}")
    lang = d["languages"]
    if not need(r, lang, ["source", "targets", "workingLanguage"], f"{where}.languages"):
        return None
    if lang["source"] in lang["targets"]:
        r.err(f"{where}.languages", "targets must not include the source language")
    if set(d["dimensionLabels"]) != DIMS:
        r.err(f"{where}.dimensionLabels", "label all four dimension keys: concept, words, english, lab")
    pol = d["assessmentPolicy"]
    if not (isinstance(pol.get("conceptChecks"), int) and 3 <= pol["conceptChecks"] <= 10):
        r.err(f"{where}.assessmentPolicy", "conceptChecks must be an integer 3-10")
    if pol.get("options", 4) not in (3, 4):
        r.err(f"{where}.assessmentPolicy", "options must be 3 or 4")
    if not need(r, d["learner"], ["role"], f"{where}.learner"):
        pass
    if not isinstance(d["practical"], dict) or "applies" not in d["practical"]:
        r.err(f"{where}.practical", "needs applies (true/false)")
    if d["corner"] in ("odds", "audiences") and not d["guardrails"]:
        r.err(f"{where}.guardrails", f"{d['corner']} domains need explicit guardrails (for example 'process, not picks')")
    bad = set(d["consumers"]) - CONSUMERS
    if bad or not d["consumers"]:
        r.err(f"{where}.consumers", f"unknown or empty consumers {sorted(bad)}")
    if "mixed-script-input/v1" in d["consumers"] and (lang["source"] != "en" or "or" not in lang["targets"]):
        r.err(f"{where}.consumers", "mixed-script-input/v1 is Odia-only today: needs source 'en' and target 'or'")
    return d


# ---------------------------------------------------------------- packet
def check_packet(p, r, backend_validate, emit_dir):
    top = ["schema", "packetId", "domain", "scope", "status", "research", "learner", "objectives", "terms",
           "usesTerms", "teaching", "placards", "visual", "canvas", "reflect", "handoff"]
    if not need(r, p, top, "packet"):
        return
    d = check_domain(p["domain"], r)
    if d is None:
        return
    corner, targets = d["corner"], d["languages"]["targets"]
    consumers = set(d["consumers"])
    pol = d["assessmentPolicy"]
    practical = bool(d["practical"].get("applies"))
    scope = p["scope"]
    need(r, scope, ["planId", "groupId", "conceptId", "order", "canonicalKey", "title"], "scope")
    cid = scope.get("conceptId", "?")
    if not ID.fullmatch(str(p.get("packetId", ""))) or not ID.fullmatch(str(cid)):
        r.err("ids", "invalid packetId or conceptId")
    if not re.fullmatch(r"[a-z0-9-]+", str(scope.get("canonicalKey", ""))):
        r.err("scope.canonicalKey", "needs a lowercase slug")
    st = p["status"]
    if st.get("review") != "draft":
        r.err("status.review", "packets are authored as draft; review happens downstream")
    for k in ("domainReview", "pronunciation"):
        if st.get(k) != "pending":
            r.warn(f"status.{k}", "should stay 'pending' until a named person reviews it")
    for lang in targets:
        if (st.get("languages") or {}).get(lang) != "machine_draft":
            r.err("status.languages", f"target '{lang}' must be 'machine_draft' until native review")

    # research
    res = p["research"]
    need(r, res, ["governingQuestion", "sources", "claims", "outOfScope", "openQuestions"], "research")
    sources = {s.get("id"): s for s in res.get("sources", []) if isinstance(s, dict)}
    if not sources:
        r.err("research.sources", "at least one source is required")
    for sid, s in sources.items():
        if not need(r, s, ["id", "origin", "tier", "label"], f"source {sid}"):
            continue
        if s["origin"] not in ORIGINS:
            r.err(f"source {sid}", f"unknown origin {s['origin']}")
        if s.get("url") and not str(s["url"]).startswith("https://"):
            r.err(f"source {sid}", "url must be https")
        if not s.get("url") and not s.get("locator"):
            r.warn(f"source {sid}", "neither url nor locator; a reviewer cannot find it")
    claims = {}
    for c in res.get("claims", []):
        if not need(r, c, ["id", "kind", "text", "sourceIds", "confidence", "check"], f"claim {c.get('id')}"):
            continue
        claims[c["id"]] = c
        cw = f"claim {c['id']}"
        if c["kind"] not in CLAIM_KINDS:
            r.err(cw, f"unknown kind {c['kind']}")
        if c["confidence"] not in ("high", "moderate", "low"):
            r.err(cw, "confidence must be high|moderate|low")
        if not c["sourceIds"] and not str(c["check"]).startswith("derived"):
            r.err(cw, "needs a source or a recorded derivation (check: 'derived: ...')")
        srcs = [sources.get(sid) for sid in c["sourceIds"]]
        for sid, s in zip(c["sourceIds"], srcs):
            if s is None:
                r.err(cw, f"unknown source {sid}")
        if c["kind"] in ("org_rule", "heuristic") and not any(s and s.get("origin") in ORG_ORIGINS for s in srcs):
            r.err(cw, f"{c['kind']} claims must cite an organisation source ({', '.join(sorted(ORG_ORIGINS))})")
        if c["kind"] == "illustrative_data" and not any(s and s.get("illustrative") for s in srcs):
            r.err(cw, "illustrative_data must cite a source marked illustrative: true")
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
        mw = f"misconception {m.get('id')}"
        if not need(r, m, ["id", "statement", "correction", "basis"], mw):
            continue
        mis[m["id"]] = m
        if m["basis"] not in ("documented", "inferred"):
            r.err(mw, "basis must be documented|inferred")
        if m["basis"] == "documented" and not m.get("sourceIds"):
            r.err(mw, "documented misconceptions need sourceIds")
        if m["basis"] == "inferred" and not text(m.get("reasoning")):
            r.err(mw, "inferred misconceptions need reasoning")
        for sid in m.get("sourceIds", []):
            if sid not in sources:
                r.err(mw, f"unknown source {sid}")
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
    glossary, english = {}, {}
    for group, owned in (("terms", True), ("usesTerms", False)):
        for t in p[group]:
            tw = f"{group} {t.get('id')}"
            if not need(r, t, ["id", "term", "definition", "ownerConceptId", "spoken", "glosses", "pronunciations",
                               "review_status"], tw):
                continue
            if t["id"] in glossary or t["term"] in english:
                r.err(tw, "duplicate term id or text")
            glossary[t["id"]], english[t["term"]] = t, t["id"]
            if owned != (t["ownerConceptId"] == cid):
                r.err(tw, "terms must be owned here; usesTerms owned elsewhere")
            for lang in targets:
                if not text((t.get("glosses") or {}).get(lang)):
                    r.err(tw, f"glosses.{lang} draft is required for every target language")
                if not text((t.get("pronunciations") or {}).get(lang)):
                    (r.err if lang == "or" else r.warn)(tw, f"pronunciations.{lang} draft missing")
            if t["review_status"] != "pending":
                r.warn(tw, "review_status should be 'pending' for drafts")
            if len(t["term"]) < 3:
                r.warn(tw, "very short terms over-match; use the full term and put the acronym in aliases")
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
        r.err("teaching.explanation.text", f"{n} words; needs 60-140")
    steps = ex.get("walkthrough", [])
    if not 3 <= len(steps) <= 8:
        r.err("teaching.explanation.walkthrough", f"{len(steps)} steps; needs 3-8")
    for i, s in enumerate(steps, 1):
        sw = f"walkthrough step {i}"
        if s.get("target") not in etext:
            r.err(sw, "target not found verbatim in explanation text")
        if s.get("mark") not in MARKS or s.get("dim") not in DIMS:
            r.err(sw, "invalid mark or dim")
        if s.get("dim") == "lab" and not practical:
            r.err(sw, "practice mark in a domain without a practical")
        say, target = str(s.get("say", "")), str(s.get("target", ""))
        if not text(say):
            r.err(sw, "no narration")
        elif not any(w.lower() in say.lower() for w in target.split() if len(w) > 3) and target not in say:
            r.warn(sw, "narration does not mention its target; signalling is lost")
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
    if (tc.get("examSignal") or {}).get("basis") not in ("past_papers", "estimate", "none"):
        r.err("teaching.examSignal", "basis must be past_papers|estimate|none")
    check_checks(tc.get("checks", []), r, objs, mis, claims, ref_claims, corner, pol, practical, scope)

    # placards
    pls = p["placards"]
    kinds = [pl.get("kind") for pl in pls]
    if not 1 <= len(pls) <= 6:
        r.err("placards", f"{len(pls)} placards; 1-6 per concept")
    if any(k not in KINDS for k in kinds):
        r.err("placards", f"unknown kinds in {kinds}")
    if "concept" not in kinds:
        r.err("placards", "needs at least one concept placard")
    for k, pos in (("definition", 0), ("recap", len(kinds) - 1)):
        if kinds.count(k) > 1 or (k in kinds and kinds.index(k) != pos):
            r.err("placards", f"at most one {k}, placed {'first' if pos == 0 else 'last'}")
    if consumers & {"learning-case/v1", "lesson-ledger/v2"} and kinds != CASE_KINDS:
        r.err("placards", f"learning-case/v1 needs exactly {CASE_KINDS}, got {kinds}")
    canvas = p["canvas"]
    seen, refuted, projections, pack_placards = set(), set(), [], []
    for pl in pls:
        pw = f"placard {pl.get('id')}"
        if not need(r, pl, ["id", "kind", "title", "sentences"], pw):
            continue
        if not ID.fullmatch(pl["id"]):
            r.err(pw, "invalid id")
        sents = pl["sentences"]
        if not 1 <= len(sents) <= 10:
            r.err(pw, f"{len(sents)} sentences; 1-10")
        lo, hi = {"definition": (1, 3), "concept": (3, 6), "example": (2, 5), "application": (2, 5),
                  "recap": (2, 4)}.get(pl["kind"], (1, 10))
        if not lo <= len(sents) <= hi:
            r.warn(pw, f"{len(sents)} sentences; {pl['kind']} placards usually have {lo}-{hi}")
        used_claims, placard_terms = [], set()
        for s in sents:
            sw = f"{pw} {s.get('id')}"
            if not need(r, s, ["id", "english", "term_ids", "literals", "claimIds"], sw):
                continue
            if not ID.fullmatch(s["id"]) or s["id"] in seen:
                r.err(sw, "invalid or duplicate sentence id")
            seen.add(s["id"])
            check_sentence(s, english, glossary, r, sw, corner)
            placard_terms |= set(s["term_ids"])
            ref_claims(s["claimIds"], sw, required=pl["kind"] != "recap")
            used_claims += s["claimIds"]
            for mid in s.get("refutesMisconceptionIds", []):
                if mid not in mis:
                    r.err(sw, f"unknown misconception {mid}")
                refuted.add(mid)
            if "cue" in s:
                check_cue(s["cue"], canvas, r, sw)
        if not placard_terms:
            r.err(pw, "contains no glossary term")
        if "mixed-script-input/v1" in consumers:
            projections.append(project_mixed(p, pl, placard_terms, used_claims, claims, sources, glossary, r))
        pack_placards.append(pack_placard(pl, glossary, used_claims, claims, sources, canvas))
    if not refuted:
        r.err("placards", "no sentence refutes a misconception (refutesMisconceptionIds)")

    v = p["visual"]
    if not (text(v.get("kind")) and text(v.get("description")) and text(v.get("alt"))):
        r.err("visual", "needs kind, description and alt")
    if canvas is None:
        if not text(p.get("canvasNullReason")):
            r.err("canvas", "null canvas needs canvasNullReason")
    else:
        check_canvas(canvas, p, objs, mis, r, corner)
    check_reflect(p["reflect"], mis, r)

    for proj in projections:
        if proj is None:
            continue
        if backend_validate:
            try:
                backend_validate(proj)
            except Exception as exc:
                r.err(f"mixed-script-input {proj['id']}", f"backend validate_input rejected: {exc}")
        else:
            r.warn(f"mixed-script-input {proj['id']}", "backend validate_input unavailable; projection not checked")
    if emit_dir:
        emit_dir.mkdir(parents=True, exist_ok=True)
        pack = {"concept": {"id": cid, "title": {d["languages"]["source"]: scope.get("title", "")},
                            "goal": {d["languages"]["source"]: tc.get("canDo", "")}, "placards": pack_placards},
                "terms": [pack_term(t, d) for t in p["terms"]],
                "scenes": [canvas["scene"]] if canvas and canvas.get("form") == "scene" else []}
        (emit_dir / f"{cid}.pack-concept.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n",
                                                           encoding="utf-8")
        for proj in projections:
            if proj:
                (emit_dir / f"{proj['id']}.mixed-input.json").write_text(
                    json.dumps(proj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    r.info.append(f"{cid} [{corner}; {d['languages']['source']}→{','.join(targets) or '-'}; "
                  f"{','.join(sorted(consumers))}]: {len(pls)} placards, "
                  f"{sum(len(pl.get('sentences', [])) for pl in pls)} sentences, {len(tc.get('checks', []))} checks, "
                  f"{len(p['terms'])}+{len(p['usesTerms'])} terms, canvas={canvas.get('form') if canvas else 'none'}, "
                  f"reflect={'yes' if p['reflect'] else 'no'}")


def check_checks(checks, r, objs, mis, claims, ref_claims, corner, pol, practical, scope):
    ids, covered, concept_mcq = set(), set(), []
    nopt = pol.get("options", 4)
    for q in checks:
        qw = f"check {q.get('id')}"
        if not need(r, q, ["id", "type", "dimension", "evaluates", "prompt", "answer", "explanation", "objectiveIds",
                           "difficulty"], qw):
            continue
        if q["id"] in ids:
            r.err(qw, "duplicate id")
        ids.add(q["id"])
        if q["type"] not in QTYPES or q["dimension"] not in DIMS or q["evaluates"] not in EVALUATES:
            r.err(qw, "unknown type, dimension or evaluates")
        if q["dimension"] == "lab" and not practical:
            r.err(qw, "practice check in a domain without a practical")
        for oid in q["objectiveIds"]:
            if oid not in objs:
                r.err(qw, f"tests {oid}, which this concept does not own")
            covered.add(oid)
        if q["difficulty"] not in (1, 2, 3):
            r.err(qw, "difficulty must be 1, 2 or 3")
        ref_claims(q.get("claimIds", []), qw, required=q["dimension"] == "concept")
        if q["evaluates"] in REASONING and corner != "laws":
            kinds = {claims[c]["kind"] for c in q.get("claimIds", []) if c in claims}
            if not kinds & {"org_rule", "heuristic", "misconception_evidence", "procedure"}:
                r.err(qw, f"a {q['evaluates']} item must cite the rule or heuristic it is judged against")
        if q["type"] in ("mcq", "term_match", "multi_select"):
            opts = q.get("options") or []
            if q["type"] != "multi_select" and q["answer"] not in opts:
                r.err(qw, "answer must be one of its options")
            if not 3 <= len(opts) <= 4:
                r.err(qw, f"{len(opts)} options; use 3 or 4")
            elif len(opts) != nopt:
                r.warn(qw, f"{len(opts)} options; the domain policy says {nopt}")
            if len(set(map(str.strip, opts))) != len(opts):
                r.err(qw, "duplicate options")
            if any(BANNED_OPTIONS.search(o) for o in opts):
                r.err(qw, "no all/none of the above")
            if q["type"] == "mcq":
                rat = q.get("distractorRationale") or {}
                for o in opts:
                    if o == q["answer"]:
                        continue
                    why = rat.get(o)
                    if not text(why):
                        r.err(qw, f"distractor '{o}' has no rationale")
                    elif not (why in mis or why.startswith("error:")):
                        r.err(qw, f"distractor rationale '{why}' must be a misconception id or 'error: ...'")
                lens = sorted(len(o) for o in opts)
                if len(opts) > 1 and len(q["answer"]) == lens[-1] and lens[-1] > 1.6 * lens[-2]:
                    r.warn(qw, "correct option is much longer than the others")
        if words(q["explanation"]) < 6:
            r.warn(qw, "explanation too thin to teach")
        if q["dimension"] == "concept" and q["type"] == "mcq":
            concept_mcq.append(q)
    want = pol.get("conceptChecks", 5)
    if len(concept_mcq) != want:
        r.err("teaching.checks", f"{len(concept_mcq)} concept MCQs; the domain policy needs {want}")
    if concept_mcq:
        pos = {q["options"].index(q["answer"]) for q in concept_mcq if q["answer"] in q.get("options", [])}
        if len(concept_mcq) >= 3 and len(pos) < 2:
            r.warn("teaching.checks", "correct answer always in the same position")
        diffs = {q["difficulty"] for q in concept_mcq}
        if max(diffs) < 2 or len(diffs) < 2:
            r.warn("teaching.checks", "difficulty does not progress")
        reasoning = sum(q["evaluates"] in REASONING for q in concept_mcq)
        if corner in ("odds", "audiences") and reasoning < min(3, len(concept_mcq)):
            r.err("teaching.checks", f"{corner}: {reasoning} concept MCQs judge process/diagnosis/judgement; need at least 3")
    for dim, types in (("words", {"term_match", "fill_blank"}), ("english", {"short_english", "spoken", "long_written"})):
        if not any(q.get("dimension") == dim and q.get("type") in types for q in checks):
            r.err("teaching.checks", f"needs a {dim} check ({'/'.join(sorted(types))})")
    if practical and scope.get("practiceTaskId") and not any(q.get("dimension") == "lab" for q in checks):
        r.err("teaching.checks", "concept linked to a practice task needs a practice (lab) check")
    for oid in objs:
        if oid not in covered:
            r.err(f"objective {oid}", "no check evidences this objective")


def check_sentence(s, english, glossary, r, sw, corner):
    e = s["english"]
    n = words(e)
    if n > 45:
        r.err(sw, f"{n} words; split it")
    elif n > 32:
        r.warn(sw, f"{n} words; aim for 8-28")
    if re.search(r"[μ≤≥≠πΩ∞→×·−]", e):
        r.warn(sw, "Unicode math symbol or minus; use ASCII and put it in a literal")
    expected = {tid for term, tid in english.items() if occurrences(e, term)}
    if set(s["term_ids"]) != expected:
        r.err(sw, f"term_ids {sorted(s['term_ids'])} must equal glossary occurrences {sorted(expected)}")
    if corner == "odds" and LIVE_ADVICE.search(e):
        r.warn(sw, "reads like a live recommendation; state the organisation's process rule instead")
    lits = [l for l in s["literals"] if isinstance(l, dict)]
    covered = e
    for lit in sorted(lits, key=lambda l: -len(str(l.get("text", "")))):
        if not (text(lit.get("text")) and text(lit.get("spoken"))):
            r.err(sw, "literal needs text and spoken")
        elif lit["text"] not in e:
            r.err(sw, f"literal '{lit['text']}' not in sentence")
        else:
            covered = covered.replace(lit["text"], " ")
    for t in sorted(english, key=len, reverse=True):
        covered = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])", " ", covered)
    leftovers = [tok for tok in re.findall(r"\S+", covered) if LITERAL_HINT.search(tok.strip(".,;:()"))]
    if leftovers:
        r.warn(sw, f"possible unprotected formula/number/symbol: {leftovers[:4]}")
    lits = [l for l in lits if text(l.get("text")) and text(l.get("spoken"))]
    bounded = []
    for l in lits:
        for m in re.finditer(re.escape(l["text"]), e):
            left_ok = not (m.start() > 0 and e[m.start() - 1].isalnum() and l["text"][0].isalnum())
            right_ok = not (m.end() < len(e) and e[m.end()].isalnum() and l["text"][-1].isalnum())
            if left_ok and right_ok:
                bounded.append((m.start(), m.end()))
    for l in lits:
        for m in re.finditer(re.escape(l["text"]), e):
            if not any(a <= m.start() and m.end() <= b for a, b in bounded):
                r.err(sw, f"literal '{l['text']}' also occurs inside an ordinary word; the translated count will change")
                break
    nums = set(NUM.findall(e))
    for l in lits:
        extra = set(NUM.findall(l["spoken"])) - nums
        if extra:
            r.err(sw, f"spoken form of '{l['text']}' introduces numbers {sorted(extra)}; write numbers as words")
        for t in glossary.values():
            if occurrences(l["spoken"].casefold(), t["spoken"].casefold()):
                r.err(sw, f"spoken form of '{l['text']}' contains term speech '{t['spoken']}'")
    present = [t for t in glossary.values() if occurrences(e, t["term"])]
    for a in present:
        for b in present:
            if a is not b and occurrences(b["spoken"].casefold(), a["spoken"].casefold()) and not occurrences(b["term"], a["term"]):
                r.err(sw, f"'{a['spoken']}' is spoken inside '{b['spoken']}' but the terms do not nest")


def check_cue(cue, canvas, r, sw):
    if not canvas:
        r.err(sw, "cue without a canvas")
        return
    st = cue.get("state")
    if canvas.get("form") == "scene":
        states = (canvas.get("scene") or {}).get("states") or {}
        if st is not None and st not in states:
            r.err(sw, f"cue state '{st}' is not one of the scene states {sorted(states)}")
        ids = scene_ids(canvas.get("scene") or {})
        for h in cue.get("highlight", []):
            if h not in ids:
                r.err(sw, f"cue highlight '{h}' is not an id in the scene")
    else:
        ctr = {c.get("name"): c for c in canvas.get("controls", [])}
        if st is not None:
            if not isinstance(st, dict):
                r.err(sw, "widget cue state must be control values, for example {\"mu\": 1.2}")
            else:
                for k, val in st.items():
                    c = ctr.get(k)
                    if not c or not c["min"] <= val <= c["max"]:
                        r.err(sw, f"cue control {k}={val} unknown or out of range")


def scene_ids(scene):
    p = scene.get("params") or {}
    ids = {scene.get("id")}
    for key in ("events", "levels", "legs", "series", "bands", "markers", "nodes"):
        ids |= {x.get("id") for x in p.get(key, []) if isinstance(x, dict)}
    return ids - {None}


def check_scene(scene, r, w="canvas.scene"):
    if not need(r, scene, ["id", "template", "params"], w):
        return
    t, p = scene["template"], scene["params"]
    if t not in TEMPLATES:
        r.err(w, f"template must be one of {sorted(TEMPLATES)}; propose new templates to the canvas factory")
        return
    if t == "candles":
        bars = p.get("bars") or []
        if len(bars) < 2:
            r.err(w, "candles needs at least 2 bars")
        for i, b in enumerate(bars):
            if not all(k in b for k in "tohlc") or not (b["l"] <= min(b["o"], b["c"]) and b["h"] >= max(b["o"], b["c"])):
                r.err(w, f"bar {i} needs t,o,h,l,c with l <= open/close <= h")
                break
    elif t == "payoff":
        legs = p.get("legs") or []
        if not legs:
            r.err(w, "payoff needs legs")
        for leg in legs:
            if leg.get("type") not in ("call", "put") or leg.get("side") not in ("long", "short") or \
               not all(isinstance(leg.get(k), (int, float)) and leg[k] > 0 for k in ("strike", "premium", "lots")):
                r.err(w, f"leg {leg.get('id')} needs type call|put, side long|short and positive strike/premium/lots")
        rng = p.get("range") or []
        if len(rng) != 2 or not rng[0] < p.get("spot", rng[0]) < rng[1]:
            r.err(w, "payoff needs range [lo, hi] with lo < spot < hi")
        iv = p.get("iv")
        if iv and not all(0 < iv.get(k, 0) < 3 for k in ("before", "after")):
            r.err(w, "iv is a fraction (0.175 = 17.5%), before and after")
        if not isinstance(p.get("lotSize"), (int, float)) or p["lotSize"] <= 0:
            r.err(w, "payoff needs a positive lotSize")
    elif t == "line":
        xs = (p.get("x") or {}).get("values") or []
        if not xs or not p.get("series"):
            r.err(w, "line needs x.values and series")
        for srs in p.get("series", []):
            if len(srs.get("values", [])) != len(xs):
                r.err(w, f"series {srs.get('id')} length differs from x")
        for b in p.get("bands", []):
            if not b.get("from", 0) < b.get("to", 0):
                r.err(w, f"band {b.get('id')} needs from < to")
    elif t == "flow":
        nodes = {n.get("id") for n in p.get("nodes", [])}
        if len(nodes) < 2:
            r.err(w, "flow needs at least 2 nodes")
        for e in p.get("edges", []):
            if e.get("from") not in nodes or e.get("to") not in nodes:
                r.err(w, f"edge {e} points at an unknown node")
    elif t == "ece":
        if p.get("renderer") not in ECE_RENDERERS or not text(p.get("conceptId")):
            r.err(w, f"ece scenes need renderer in {sorted(ECE_RENDERERS)} and a conceptId")
    ids = scene_ids(scene)
    for name, patch in (scene.get("states") or {}).items():
        if set(patch) - PATCH_KEYS:
            r.err(w, f"state '{name}' has unknown keys {sorted(set(patch) - PATCH_KEYS)}")
        for k in ("show", "hide", "highlight"):
            for i in patch.get(k, []):
                if i not in ids:
                    r.err(w, f"state '{name}' {k} '{i}' is not an id in the scene")


def check_canvas(cv, p, objs, mis, r, corner):
    w = "canvas"
    form = cv.get("form")
    if form not in ("widget", "scene"):
        r.err(w, "form must be widget or scene")
        return
    if not need(r, cv, ["purpose", "mustShow", "mustNotImply", "claim", "alt"], w):
        return
    pur = cv["purpose"]
    if not text(pur.get("insight")):
        r.err(w, "purpose.insight is required: what should the learner notice?")
    if not pur.get("objectiveIds"):
        r.err(w, "purpose must name the objective(s) the canvas serves")
    for oid in pur.get("objectiveIds", []):
        if oid not in objs:
            r.err(w, f"purpose objective {oid} not owned")
    for mid in pur.get("misconceptionIds", []):
        if mid not in mis:
            r.err(w, f"purpose misconception {mid} unknown")
    if form == "scene":
        check_scene(cv.get("scene") or {}, r)
        if cv["claim"] not in ("illustrative_case", "ideal_teaching_model"):
            r.err(w, "scene claim must be illustrative_case or ideal_teaching_model")
        if cv["claim"] == "illustrative_case" and not cv.get("illustrative"):
            r.err(w, "illustrative_case scenes must set illustrative: true so the UI labels them")
        if corner != "laws" and not cv["mustNotImply"]:
            r.err(w, f"{corner} scenes must say what they must not imply (for example advice)")
        return
    if not need(r, cv, ["artifactId", "status", "reusesPinnedScene", "kind", "interaction", "controls", "model",
                        "behaviorCases", "placardStates"], w):
        return
    if cv["claim"] != "ideal_teaching_model":
        r.err(w, "widget claim must be ideal_teaching_model")
    if cv["interaction"] not in INTERACTIONS:
        r.err(w, "unknown interaction kind")
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
            r.warn(cw, f"unit '{c['unit']}' is outside the current scene contract")
        names[c["name"]] = c["default"]
    model = cv["model"]
    if not model.get("assumptions"):
        r.err(w, "model.assumptions required")
    outs = model.get("outputs", [])
    if cv["interaction"] == "parameter_sweep" and not outs:
        r.err(w, "parameter_sweep needs model outputs")

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
        if re.search(r"\b(sin|cos|tan)\s*\(", o["formula"]):
            r.warn(f"canvas output {o['name']}", "uses trigonometry; ledger parameter_sweep formulas cannot")
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
        given = case.get("inputs", {})
        if all(given.get(k, v) == v for k, v in names.items()):
            has_default = True
        for k, val in given.items():
            c = next((c for c in ctr if c.get("name") == k), None)
            if not c:
                r.err(cw, f"unknown control {k}")
            elif not c["min"] <= val <= c["max"]:
                r.err(cw, f"{k}={val} outside control range")
        if not text(case.get("observation")):
            r.err(cw, "observation (what the learner sees) required")
        try:
            got = run({**names, **given})
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
    if pur.get("misconceptionIds") and not any(c.get("showsMisconception") for c in cases):
        r.warn(w, "no behaviour case has showsMisconception: true")
    pids = {pl.get("id") for pl in p["placards"]}
    for ps in cv["placardStates"]:
        if ps.get("placardId") not in pids:
            r.err(w, f"placardState for unknown placard {ps.get('placardId')}")
        for k, val in (ps.get("controls") or {}).items():
            c = next((c for c in ctr if c.get("name") == k), None)
            if not c or not c["min"] <= val <= c["max"]:
                r.err(w, f"placardState control {k}={val} unknown or out of range")


def check_reflect(rf, mis, r):
    if rf is None:
        return
    if "graphRef" in rf:
        if not re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", str(rf["graphRef"])):
            r.err("reflect", "graphRef must be '<packId>/<graphId>'")
        return
    seed = rf.get("seed")
    if not need(r, seed, ["problem", "metrics", "insights", "misconceptionIds", "hintLadder"], "reflect.seed"):
        return
    metrics = {m.get("id") for m in seed["metrics"]}
    for m in seed["metrics"]:
        if m.get("dim") not in DIMS:
            r.err("reflect.seed", f"metric {m.get('id')} needs a dim")
    if not 1 <= len(seed["insights"]) <= 4:
        r.err("reflect.seed", "1-4 insights")
    for i in seed["insights"]:
        if i.get("metric") not in metrics:
            r.err("reflect.seed", f"insight {i.get('id')} names an unknown metric")
    for mid in seed["misconceptionIds"]:
        if mid not in mis:
            r.err("reflect.seed", f"unknown misconception {mid}")
    if [h.get("rung") for h in seed["hintLadder"]] != ["question", "nudge", "worked_step", "answer"]:
        r.err("reflect.seed", "hintLadder needs the 4 rungs: question, nudge, worked_step, answer")


# ---------------------------------------------------------------- projections
def cited_refs(used_claims, claims, sources):
    out, seen = [], set()
    for cid in used_claims:
        for sid in claims.get(cid, {}).get("sourceIds", []):
            if sid in sources and sid not in seen:
                seen.add(sid)
                out.append(sources[sid])
    return out


def project_mixed(p, pl, placard_terms, used_claims, claims, sources, glossary, r):
    refs = [{"title": s["label"], "url": s["url"]} for s in cited_refs(used_claims, claims, sources) if s.get("url")]
    if not refs:
        refs = [{"title": s["label"], "url": s["url"]} for s in sources.values() if s.get("url")]
    if not refs:
        r.err(f"placard {pl['id']}", "no https source; mixed-script-input/v1 requires one reference")
        return None
    return {
        "schema": "mixed-script-input/v1", "id": pl["id"],
        "title": f"{p['scope']['title']} — {pl['title'].get('en', pl['kind'])}",
        "source": {"kind": "adapted_reference", "review_status": "pending", "references": refs},
        "mix": {"support_language": "or", "script": "Odia", "level": "odia-led-english-terms"},
        "glossary": [{"id": t["id"], "english": t["term"], "meaning_or": t["glosses"]["or"],
                      "pronunciation_or": t["pronunciations"]["or"], "spoken_en": t["spoken"], "review_status": "pending"}
                     for tid, t in glossary.items() if tid in placard_terms],
        "sentences": [{"id": s["id"], "english": s["english"], "term_ids": s["term_ids"],
                       "literals": [{"text": l["text"], "spoken": l["spoken"]} for l in s["literals"]]}
                      for s in pl["sentences"]],
    }


def mark_terms(sentence, glossary):
    spans, taken = [], [False] * len(sentence)
    for t in sorted(glossary.values(), key=lambda t: -len(t["term"])):
        for m in re.finditer(r"(?<![A-Za-z0-9_])" + re.escape(t["term"]) + r"(?![A-Za-z0-9_])", sentence):
            if not any(taken[m.start():m.end()]):
                spans.append((m.start(), m.end(), t["id"]))
                for i in range(m.start(), m.end()):
                    taken[i] = True
    out, last = [], 0
    for a, b, tid in sorted(spans):
        out += [sentence[last:a], f"[[{tid}]]"]
        last = b
    return "".join(out + [sentence[last:]])


def pack_placard(pl, glossary, used_claims, claims, sources, canvas):
    src = " ".join(mark_terms(s["english"], glossary) for s in pl.get("sentences", []))
    out = {"kind": pl.get("kind"), "text": {"en": src},
           "sources": [{"id": s["id"], "title": s["label"], **({"locator": s["locator"]} if s.get("locator") else {})}
                       for s in cited_refs(used_claims, claims, sources)]}
    if canvas and canvas.get("form") == "scene":
        out["sceneId"] = canvas["scene"]["id"]
    return out


def pack_term(t, d):
    src = d["languages"]["source"]
    return {"id": t["id"], "term": t["term"], "meaning": {src: t["definition"], **t.get("glosses", {})},
            "say": dict(t.get("pronunciations", {}))}


# ---------------------------------------------------------------- plan
def check_plan(p, r):
    if not need(r, p, ["schema", "planId", "domain", "scope", "title", "governingQuestion", "canDo", "request",
                       "sources", "mece", "objectives", "groups", "concepts", "route", "practical", "chapterTest"], "plan"):
        return
    check_domain(p["domain"], r)
    shapes = {"chapter": ((2, 5), (2, 5)), "module": ((1, 1), (2, 5)), "topic": ((1, 1), (2, 5)),
              "concept": ((1, 1), (1, 1))}
    if p["scope"] not in shapes:
        r.err("scope", "chapter|module|topic|concept")
        return
    (g0, g1), (c0, c1) = shapes[p["scope"]]
    groups, cs = p["groups"], {c["id"]: c for c in p["concepts"]}
    if not g0 <= len(groups) <= g1:
        r.err("groups", f"{p['scope']} needs {g0}-{g1}, has {len(groups)}")
    for m in [p["mece"]] + [g.get("mece", {}) for g in groups]:
        if not (text(m.get("dimension")) and text(m.get("rationale"))):
            r.err("mece", "every split states dimension and rationale")
    parent = {}
    for g in groups:
        if not c0 <= len(g["conceptIds"]) <= c1:
            r.err(g["id"], f"needs {c0}-{c1} concepts")
        for cid in g["conceptIds"]:
            if cid not in cs:
                r.err(g["id"], f"unknown concept {cid}")
            if cid in parent:
                r.err(cid, "has two parents")
            parent[cid] = g["id"]
    for cid, c in cs.items():
        if parent.get(cid) != c.get("groupId"):
            r.err(cid, "groupId disagrees with group lists")
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
        req, closure = set(pr.get("requiredConceptIds", [])), set()

        def need_pre(c):
            for pre in cs.get(c, {}).get("prerequisiteIds", []):
                if pre not in closure:
                    closure.add(pre)
                    need_pre(pre)

        for c in req:
            need_pre(c)
        if closure - req:
            r.err("practical", f"required concepts miss prerequisites {sorted(closure - req)}")
    test = p["chapterTest"] or []
    if p["scope"] == "chapter" and (p["domain"].get("assessmentPolicy") or {}).get("chapterTest", True) and len(test) != 10:
        r.err("chapterTest", f"chapter scope needs 10 MCQs, has {len(test)}")
    hit = set()
    for q in test:
        qw = f"chapterTest {q.get('id')}"
        if q.get("type") != "mcq" or q.get("answer") not in (q.get("options") or []):
            r.err(qw, "must be an mcq whose answer is an option")
        if not 3 <= len(q.get("options") or []) <= 4:
            r.err(qw, "use 3 or 4 options")
        if not text(q.get("explanation")):
            r.err(qw, "needs an explanation")
        for c in q.get("conceptIds", []):
            if c not in cs:
                r.err(qw, f"unknown concept {c}")
            hit.add(c)
    if test and len(cs) <= 10 and set(cs) - hit:
        r.err("chapterTest", f"concepts without a test item: {sorted(set(cs) - hit)}")
    r.info.append(f"{p['planId']} [{p['domain'].get('corner')}]: {len(groups)} groups, {len(cs)} concepts, "
                  f"{len(test)} chapter MCQs")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--emit", type=Path, help="write kiki-pack/v0 concept and mixed-script projections here")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    backend = find_backend(Path(__file__).resolve()) or find_backend(Path.cwd().resolve())
    validate, note = None, "kiki-backend not found; Odia projections are not checked against validate_input"
    if backend:
        sys.path.insert(0, str(backend))
        try:
            from prototypes.mixed_script.pipeline import validate_input as validate
            note = f"backend validate_input: {backend / 'prototypes/mixed_script/pipeline.py'}"
        except Exception as exc:  # pragma: no cover
            note = f"backend validate_input unavailable ({exc})"

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
                check_packet(doc, r, validate, a.emit)
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
