"""Validate and assemble the two authored knowledge-worker draft packs. No provider calls.

Run from any directory: python3 -B scripts/build-persona-content.py [--check]
--check is read-only and fails if authored sources or committed exports are inconsistent.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "content/knowledge-workers"
PACKS = {"trading-fno": "trader", "streaming-gta": "streamer"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, f"{path}: duplicate JSON key {key}")
            obj[key] = value
        return obj
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def checker():
    path = ROOT / ".claude/skills/kiki-pedagogy-packets/scripts/check_packet.py"
    spec = importlib.util.spec_from_file_location("kiki_packet_checker", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def unique_ids(items, where):
    result = {}
    for obj in items:
        require(obj["id"] not in result, f"{where}: duplicate id {obj['id']}")
        result[obj["id"]] = obj
    return result


def validate_module(plan, packets):
    """Check cross-file ownership, objective hierarchy and export identities."""
    cs = unique_ids(plan["concepts"], "plan concepts")
    require(set(cs) == {p["scope"]["conceptId"] for p in packets}, "plan/packet concept mismatch")
    require(len(packets) == len(cs), "duplicate concept packets")
    objs = unique_ids(plan["objectives"], "plan objectives")
    roots = [o for o in objs.values() if o["parentId"] is None]
    require(len(roots) == 1 and roots[0]["ownerId"] == plan["planId"], "missing or invalid apex objective")
    groups = unique_ids(plan["groups"], "plan groups")
    for g in groups.values():
        o = objs.get(g["objectiveId"])
        require(o and o["ownerId"] == g["id"] and o["parentId"] == roots[0]["id"], "missing or invalid group objective")
    for obj in objs.values():
        if obj["parentId"] is not None:
            require(obj["parentId"] in objs, f"unknown objective parent {obj['parentId']}")
        seen, current = set(), obj
        while current["parentId"] is not None:
            require(current["id"] not in seen, "objective parent cycle")
            seen.add(current["id"])
            current = objs[current["parentId"]]
    terms = unique_ids([t for p in packets for t in p["terms"]], "owned terms")
    require(len({t["term"] for t in terms.values()}) == len(terms), "duplicate canonical term text")
    unique_ids([pl for p in packets for pl in p["placards"]], "placards")
    unique_ids([s for p in packets for pl in p["placards"] for s in pl["sentences"]], "sentences")
    unique_ids([q for p in packets for q in p["teaching"]["checks"]], "assessment items")
    require(set(plan["route"]) == set(cs) and len(plan["route"]) == len(cs), "invalid route")
    pos = {cid: i for i, cid in enumerate(plan["route"])}
    for p in packets:
        scope = p["scope"]
        cid = scope["conceptId"]
        require(p["domain"] == plan["domain"], f"{cid}: domain differs from plan")
        require(scope["planId"] == plan["planId"] and scope["groupId"] == cs[cid]["groupId"], f"{cid}: wrong plan/group")
        require(scope["order"] == pos[cid] + 1, f"{cid}: wrong route order")
        require(p["learner"]["prerequisiteIds"] == cs[cid]["prerequisiteIds"], f"{cid}: prerequisites differ")
        for pre in p["learner"]["prerequisiteIds"]:
            require(pre in cs and pos[pre] < pos[cid], f"{cid}: missing or later prerequisite {pre}")
        for o in p["objectives"]:
            require(objs.get(o["id"]) == o, f"{cid}: objective not identical in plan")
            require(o["ownerId"] == cid and o["parentId"] == groups[scope["groupId"]]["objectiveId"], f"{cid}: invalid objective owner")
        for t in p["terms"]:
            require(t["ownerConceptId"] == cid, f"{cid}: wrong term owner")
        for t in p["usesTerms"]:
            require(terms.get(t["id"]) == t, f"{cid}: reused term differs from owner")
            require(t["ownerConceptId"] in p["learner"]["prerequisiteIds"], f"{cid}: term used before prerequisite")
        cv = p["canvas"]
        if cv and cv["form"] == "widget":
            outputs = {x["name"] for x in cv["model"]["outputs"]}
            covered = set()
            for case in cv["behaviorCases"]:
                require(case.get("expect"), f"{cid}: canvas case needs expectations")
                require(all(isinstance(v, (int, float)) and math.isfinite(v) for v in case["expect"].values()), "non-finite expectation")
                covered.update(case["expect"])
            require(outputs <= covered, f"{cid}: canvas output without expectations")


def validate_graph(graph, concept_ids, task_ids, mod):
    require(graph["schema"] == "kiki-tutor-graph/v0", "wrong tutor schema")
    nodes = graph["nodes"]
    require(8 <= len(nodes) <= 12 and graph["start"] in nodes, "graph size/start invalid")
    scenes = unique_ids(graph["scenes"], "graph scenes")
    metrics = unique_ids(graph["metrics"], "graph metrics")
    for s in scenes.values():
        report = mod.Report(s["id"])
        mod.check_scene(s, report)
        require(not report.errors, str(report.errors))
    edges = {}
    for nid, n in nodes.items():
        require(n["kind"] in ("probe", "show", "conclusion") and n.get("say", {}).get("en"), f"{nid}: invalid node")
        branches = n.get("expect", []) + n.get("misconceptions", [])
        unique_ids(branches, f"{nid} branches")
        targets = [b["next"] for b in branches]
        for b in branches:
            require(b["metric"] in metrics, f"{nid}: unknown metric")
        if n["kind"] == "show":
            require(n.get("next"), f"{nid}: show has no next node")
        if n.get("next"):
            targets.append(n["next"])
        for field, sentinel in (("onUnclear", "hint"), ("onOffTopic", "redirect")):
            if n.get(field) and n[field] != sentinel:
                targets.append(n[field])
        if n["kind"] == "probe":
            require(n.get("expect") and len(n.get("hints", [])) == 4, f"{nid}: probe needs branches and four hints")
        for canvas in [n.get("canvas")] + [h.get("canvas") for h in n.get("hints", [])]:
            if canvas:
                sid = canvas["sceneId"]
                require(sid in scenes, f"{nid}: unknown scene")
                require(not canvas.get("state") or canvas["state"] in scenes[sid].get("states", {}), f"{nid}: unknown state")
                for a in canvas.get("annotate", []):
                    require(not a.get("target") or a["target"] in mod.scene_ids(scenes[sid]), f"{nid}: unknown annotation target")
        labels = {b["id"] for b in branches}
        for chip in n.get("chips", []):
            require(not chip.get("route") or chip["route"] in labels, f"{nid}: unknown chip route")
        require(all(t in nodes for t in targets), f"{nid}: unknown next node")
        require(n["kind"] == "conclusion" or targets, f"{nid}: dead end")
        edges[nid] = targets
    active, done = set(), set()
    def visit(nid):
        require(nid not in active, "graph transition cycle")
        if nid in done:
            return
        active.add(nid)
        for target in edges[nid]:
            visit(target)
        active.remove(nid)
        done.add(nid)
    visit(graph["start"])
    require(done == set(nodes), "unreachable graph nodes")
    for step in graph["nextSteps"]:
        require(step["id"] in (concept_ids if step["kind"] == "concept" else task_ids), "unresolved graph next step")


def scenario_checks(tr, st):
    leg = tr["trade"]["legs"][0]
    qty = leg["lots"] * tr["underlying"]["lotSize"]
    require(qty == leg["qty"], "case quantity mismatch")
    close = lambda a, b: math.isclose(a, b, abs_tol=0.011)
    require(close((leg["exit"]["price"] - leg["entry"]["price"]) * qty, tr["pnl"]["total"]), "case P&L mismatch")
    require(close(leg["entry"]["price"] * qty, tr["sizing"]["premiumAtRisk"]), "case max loss mismatch")
    require(close(tr["context"]["bookNotionalInr"] * .01, 10000), "case budget mismatch")
    require(math.floor(10000 / (90.25 * 75)) == 1, "case lot limit mismatch")
    require(close(tr["impliedMove"]["atmCall"] + tr["impliedMove"]["atmPut"], 304.30), "case straddle mismatch")
    # Independently reprice the two case endpoints, rather than trusting recorded PASS flags.
    def call(s, k, days, vol):
        t = days / 365
        d1 = (math.log(s/k) + (.065 + vol*vol/2)*t) / (vol*math.sqrt(t))
        d2 = d1 - vol*math.sqrt(t)
        normal = lambda x: (1 + math.erf(x/math.sqrt(2))) / 2
        return s*normal(d1) - k*math.exp(-.065*t)*normal(d2)
    require(close(call(24040, 24200, 3, .175), 90.2263), "before model price mismatch")
    require(close(call(24150, 24200, 2, .11), 59.5543), "after model price mismatch")
    series = st["series"]
    require(series["minute"] == list(range(180)), "stream samples must cover 180 minutes")
    for field in ("ccv", "chatPerMin", "followsPerMin"):
        require(len(series[field]) == 180, f"stream {field} length mismatch")
    for segment in st["segmentStats"]:
        first, last = segment["from"], segment["to"] - 1
        require(series["ccv"][first] == segment["ccvStart"] and series["ccv"][last] == segment["ccvEnd"], "segment endpoint mismatch")
        require(round(series["ccv"][last] / series["ccv"][first], 2) == segment["retention"], "segment ratio mismatch")
    require(series["chatPerMin"][37] == 87 and series["chatPerMin"][41] == 15, "chat anchors mismatch")
    require(round(348/556, 2) == .63 and round(477/351, 2) == 1.36, "lesson ratio mismatch")


def adapt_graph(graph, who, domain):
    """Preserve the prototype topology; make review claims safe for unscripted use."""
    graph = copy.deepcopy(graph)
    mapping = {"iv-before-events": "TR-IV-EVENT", "segment-design": "ST-HOOKS"}
    graph["nextSteps"] = copy.deepcopy(graph["scriptedScorecard"]["next"])
    for step in graph["nextSteps"]:
        step["id"] = mapping.get(step["id"], step["id"])
        # Static content cannot assert which insight a real learner needed help with.
        step["why"] = {"en": "Use another saved case to practise the cited process and explain the reasoning."}
    graph["caseData"]["review"] = {"status": "draft", "illustrative": True, "domainReview": "pending", "languages": {domain["languages"]["targets"][0]: "machine_draft"}}
    graph.pop("scriptedScorecard", None)
    graph.pop("videoScorecard", None)
    edits = {
        "trader": {
            "n2-premium": "In the illustrative case the index rose 110 points, but premium fell from 90.25 to 59.55 rupees. Which other price drivers changed?",
            "s1-payoff": "The model attributes about plus 40 per unit to spot, minus 48 to IV and minus 23 to time. These components are rounded; the fill-based loss is 30.70 per unit.",
            "n3-implied-move": "The desk uses the roughly 304-point straddle as a planning guide, not a universal profit threshold. How does the case's realised move compare?",
        },
        "streamer": {
            "s1-bands": "The segment bands align the decline with the silent grind and the recovery with the next block. This supports a content hypothesis; timing alone cannot rule out outside causes. Check the VOD and context.",
            "s2-compare": "The vote block grew from 351 to 477 concurrent viewers while polls, talk and segment context changed together. Compare it with the grind, but do not attribute the recovery to polls alone.",
        },
    }
    for nid, line in edits[who].items():
        # Old target-language lines no longer match these edits. Do not present them as a rendition.
        graph["nodes"][nid]["say"] = {"en": line}
    conclusion = graph["nodes"]["c1-conclusion"]
    conclusion["say"] = {"en": "Review summary for the illustrative case."}
    conclusion["summary"] = {"en": (
        "The case premium fell despite a favourable spot move because volatility and time effects outweighed it. Entry risk exceeded the desk budget. Review EV-2.1, EV-4.1 and EV-6.1 using the recorded entry-time evidence; this is no live recommendation."
        if who == "trader" else
        "The case notes and timing suggest a missing goal and participation during the grind. They do not prove every viewer's motive or exclude outside causes. Draft one change under LW-6.2, with a prediction, measure and provisional review threshold; log raids and other confounders."
    )}
    return graph


def expected_artifacts():
    mod = checker()
    manifest = load(BASE / "sources/manifest.json")
    for entry in manifest["files"]:
        require(hashlib.sha256((BASE / entry["localPath"]).read_bytes()).hexdigest() == entry["sha256"], f"source hash mismatch: {entry['localPath']}")
    artifacts = {}
    review = ["# Trader and streamer lesson review", "",
              "Draft source content · 20 November 2026 · all people, organisations and case data are illustrative.",
              "English lesson sources; Hindi/Hinglish glosses and unchanged tutor lines are machine drafts. Domain and native review are pending.",
              "", "Eight concepts, 32 placards, 80 source sentences and 64 checks. Practice predictions do not establish observed tool performance.",
              "", "Generated from packet sources by `scripts/build-persona-content.py`; edit the packets and regenerate.", ""]
    scenarios = {who: load(BASE / f"sources/design/personas/{who}/scenario.json") for who in PACKS.values()}
    scenario_checks(scenarios["trader"], scenarios["streamer"])
    for pack_id, who in PACKS.items():
        plan = load(BASE / f"plans/{pack_id}.plan.json")
        packets = [load(p) for p in sorted((BASE / f"packets/{pack_id}").glob("*.packet.json"))]
        require(len(packets) == 4, f"{pack_id}: expected four authored concepts")
        for obj in [plan] + packets:
            report = mod.Report(obj.get("packetId", obj.get("planId")))
            if obj["schema"] == "kiki-chapter-plan/v1":
                mod.check_plan(obj, report)
            else:
                mod.check_packet(obj, report, None, None)
            require(not report.errors and not report.warnings, str(vars(report)))
        validate_module(plan, packets)
        order = {cid: i for i, cid in enumerate(plan["route"])}
        packets.sort(key=lambda p: order[p["scope"]["conceptId"]])
        domain = plan["domain"]
        review += ["## " + plan["title"], "", "Target: " + domain["languages"]["targets"][0] + " · Working language: " + domain["languages"]["workingLanguage"], ""]
        for p in packets:
            cid = p["scope"]["conceptId"]
            review += ["### " + cid + " — " + p["scope"]["title"], "", p["teaching"]["canDo"], "",
                       f"[Authoritative packet](packets/{pack_id}/{cid}.packet.json) · Prerequisites: " + (", ".join(p["learner"]["prerequisiteIds"]) or "external basics only"), ""]
            for pl in p["placards"]:
                review += ["**" + pl["kind"].capitalize() + "**", "", " ".join(s["english"] for s in pl["sentences"]), ""]
            worked = p["teaching"]["workedQuestion"]
            review += ["**Worked question**", "", worked["prompt"], ""]
            review += [f"{i}. {line}" for i, line in enumerate(worked["modelAnswer"], 1)] + [""]
            review += ["**Concept checks — reviewer answer key**", "", "| Question | Key | Why |", "|---|---|---|"]
            for q in p["teaching"]["checks"][:5]:
                review.append("| " + q["prompt"] + " | " + q["answer"] + " | " + q["explanation"] + " |")
            review += ["", "Wrong-option explanations and dimension-specific rubrics are in the packet.", "",
                       "**Expression:** " + p["teaching"]["checks"][-2]["prompt"], "",
                       "**Practice exercise:** " + p["teaching"]["checks"][-1]["prompt"], "",
                       "**Sources:** " + "; ".join(s["label"] + " — " + s.get("locator", s.get("url", "")) for s in p["research"]["sources"]), ""]
        graph = adapt_graph(load(BASE / f"sources/design/personas/{who}/tutor-flow.json"), who, domain)
        task = {k: v for k, v in scenarios[who]["doTask"].items() if k in ("id", "tool", "userAsk", "lookFor", "askAfter", "graphId")}
        if who == "trader":
            task["askAfter"] = {"en": "Which required fields can you verify in this historical note?"}
        tasks = [task]
        if who == "streamer":
            tasks.append({"id": "run-of-show-plan", "tool": {"en": "Saved run-of-show editor"}, "userAsk": {"en": "Does my next-stream plan test one change?"}, "lookFor": [{"id": "one-change", "desc": "One stated change with a prediction"}, {"id": "measure", "desc": "Review measure and provisional threshold"}, {"id": "context", "desc": "Raids and simultaneous changes logged"}], "askAfter": {"en": "What would make this comparison inconclusive?"}, "graphId": pack_id + "/" + graph["id"]})
        validate_graph(graph, set(plan["route"]), {t["id"] for t in tasks}, mod)
        terms = unique_ids([t for p in packets for t in p["terms"]], "pack terms")
        scenes = {}
        for s in graph["scenes"] + [p["canvas"]["scene"] for p in packets]:
            require(s["id"] not in scenes or scenes[s["id"]] == s, "conflicting shared scene")
            scenes[s["id"]] = s
        concepts = []
        cues, assessments = {}, {}
        for p in packets:
            cid = p["scope"]["conceptId"]
            require(p["scope"]["practiceTaskId"] in {t["id"] for t in tasks}, "unresolved practice task")
            require(p["reflect"]["graphRef"] == pack_id + "/" + graph["id"], "unresolved reflect graph")
            glossary = {t["id"]: t for t in p["terms"] + p["usesTerms"]}
            claims = {c["id"]: c for c in p["research"]["claims"]}
            sources = {s["id"]: s for s in p["research"]["sources"]}
            placards = []
            cues[cid] = []
            for pi, pl in enumerate(p["placards"]):
                used = [i for s in pl["sentences"] for i in s["claimIds"]]
                placards.append(mod.pack_placard(pl, glossary, used, claims, sources, p["canvas"]))
                for si, s in enumerate(pl["sentences"]):
                    if s.get("cue"):
                        cues[cid].append({"placard": pi, "sentence": si, "sentenceId": s["id"], "scene": {"id": p["canvas"]["scene"]["id"], **s["cue"]}})
            concepts.append({"id": cid, "title": {"en": p["scope"]["title"]}, "goal": {"en": p["teaching"]["canDo"]}, "placards": placards})
            assessments[cid] = {"policy": domain["assessmentPolicy"], "checks": p["teaching"]["checks"], "workedQuestion": p["teaching"]["workedQuestion"]}
        for c in concepts:
            for pl in c["placards"]:
                require(set(re.findall(r"\[\[([^]]+)\]\]", pl["text"]["en"])) <= set(terms), "unresolved term chip")
                require(pl.get("sceneId") in scenes, "unresolved placard scene")
        target = domain["languages"]["targets"][0]
        pack = {"schema": "kiki-pack/v0", "id": pack_id, "version": "2026-11-20.1", "corner": domain["corner"], "title": {"en": plan["title"]}, "persona": {"name": scenarios[who]["persona"]["name"], "role": {"en": domain["learner"]["role"]}, "transition": {"en": domain["learner"]["transition"]}, "org": {"en": "Illustrative desk" if who == "trader" else "Illustrative creator agency"}},
                "languages": {"source": "en", "learner": "en", "available": ["en"], "review": {"en": "draft", target: "draft"}},
                "dimensionLabels": {k: {"en": v} for k, v in domain["dimensionLabels"].items()},
                "modules": [{"id": g["id"], "title": {"en": g["title"]}, "conceptIds": g["conceptIds"]} for g in plan["groups"]], "concepts": concepts,
                "terms": [mod.pack_term(t, domain) for t in terms.values()], "scenes": list(scenes.values()),
                "tutorGraphs": [{"id": graph["id"], "title": graph["title"], "file": "graphs/" + graph["id"] + ".json"}], "labLite": tasks,
                "provenance": {"generatedBy": "authored-pedagogy-packets/1", "generatedAt": packets[0]["createdAt"], "sources": [{"id": s["id"], "title": s["label"], "locator": s.get("locator", s.get("url", ""))} for s in plan["sources"]], "review": "draft", "notes": f"Illustrative prototype. English lesson source only; {target} glosses and imported tutor lines are machine drafts. No target-language lesson rendition, audio, tool execution, mastery evidence or publication. Design baseline {manifest['revision']}."}}
        dest = BASE / "packs" / pack_id
        artifacts[dest / "pack.json"] = pack
        artifacts[dest / "graphs" / (graph["id"] + ".json")] = graph
        artifacts[dest / "cue-seeds.json"] = {"schema": "kiki-cue-seeds/v1", "timing": "pending_tts", "concepts": cues}
        artifacts[dest / "assessments.json"] = {"schema": "kiki-authored-assessments/v1", "review": "draft", "concepts": assessments}
        artifacts[dest / "review.json"] = {"schema": "kiki-content-review/v1", "review": "draft", "illustrative": True, "domainReview": "pending", "nativeLanguageReview": {target: "pending"}, "guardrails": domain["guardrails"], "lessonLanguagesAvailable": ["en"], "plannedTarget": target, "audio": "not_generated", "practiceEvidence": "not_observed", "tutorAdaptation": "Pinned topology; nextSteps resolved; evidence-assuming copy and causal overclaims corrected; review state added; prototype scorecards removed. Changed dialogue is English-only until translation and native review. Routing/runtime review still pending."}
        for filename in ("playbook-excerpt.md", "scenario.json", "persona.md"):
            artifacts[dest / "sources" / filename] = (BASE / f"sources/design/personas/{who}/{filename}").read_text(encoding="utf-8")
    artifacts[BASE / "REVIEW.md"] = "\n".join(review)
    return artifacts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        artifacts = expected_artifacts()
        for path, obj in artifacts.items():
            body = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
            if args.check:
                require(path.is_file() and path.read_text(encoding="utf-8") == body, f"stale export: {path.relative_to(ROOT)}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")
        print(f"PASS: 8 packets, 2 plans, 2 graphs, scenario arithmetic, source hashes; {len(artifacts)} exports {'verified' if args.check else 'written'}")
    except (ValueError, KeyError, TypeError) as exc:
        ap.exit(1, f"FAIL: {exc}\n")


if __name__ == "__main__":
    main()
