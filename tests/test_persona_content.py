"""Offline regressions for content failures that the upstream packet checker can miss."""
import copy
import importlib.util
import unittest

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("persona_builder", ROOT / "scripts/build-persona-content.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class PersonaContentTests(unittest.TestCase):
    def setUp(self):
        self.plan = builder.load(builder.BASE / "plans/trading-fno.plan.json")
        self.packets = [builder.load(p) for p in sorted((builder.BASE / "packets/trading-fno").glob("*.json"))]

    def test_both_bundles_build_with_resolved_references(self):
        exports = builder.expected_artifacts()
        packs = [obj for path, obj in exports.items() if path.name == "pack.json"]
        self.assertEqual(len(packs), 2)
        for pack in packs:
            self.assertEqual(len(pack["concepts"]), 4)
            self.assertEqual(pack["languages"]["available"], ["en"])
            self.assertEqual(pack["provenance"]["review"], "draft")

    def test_duplicate_placards_rejected_before_export(self):
        self.packets[0]["placards"][1]["id"] = self.packets[0]["placards"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate id"):
            builder.validate_module(self.plan, self.packets)

    def test_missing_plan_objective_rejected(self):
        self.plan["objectives"] = []
        with self.assertRaisesRegex(ValueError, "apex objective"):
            builder.validate_module(self.plan, self.packets)

    def test_reused_term_must_match_owning_packet(self):
        packet = next(p for p in self.packets if p["usesTerms"])
        packet["usesTerms"][0]["definition"] = "Conflicting alternate definition"
        with self.assertRaisesRegex(ValueError, "reused term differs"):
            builder.validate_module(self.plan, self.packets)

    def test_empty_widget_expectations_rejected(self):
        self.packets[0]["canvas"] = {"form": "widget", "model": {"outputs": [{"name": "wrong"}]},
                                      "behaviorCases": [{"expect": {}}]}
        with self.assertRaisesRegex(ValueError, "needs expectations"):
            builder.validate_module(self.plan, self.packets)

    def test_scenario_numbers_recomputed(self):
        tr = builder.load(builder.BASE / "sources/design/personas/trader/scenario.json")
        st = builder.load(builder.BASE / "sources/design/personas/streamer/scenario.json")
        broken = copy.deepcopy(tr)
        broken["pnl"]["total"] += 100
        with self.assertRaisesRegex(ValueError, "P&L mismatch"):
            builder.scenario_checks(broken, st)
        st["segmentStats"][0]["retention"] = 99
        with self.assertRaisesRegex(ValueError, "segment ratio mismatch"):
            builder.scenario_checks(tr, st)

    def test_adapted_graph_does_not_invent_learner_evidence(self):
        source = builder.load(builder.BASE / "sources/design/personas/streamer/tutor-flow.json")
        domain = builder.load(builder.BASE / "plans/streaming-gta.plan.json")["domain"]
        graph = builder.adapt_graph(source, "streamer", domain)
        self.assertNotIn("scriptedScorecard", graph)
        self.assertNotIn("videoScorecard", graph)
        self.assertNotIn("You first blamed", str(graph["nextSteps"]))
        self.assertIn("cannot rule out", graph["nodes"]["s1-bands"]["say"]["en"])
        self.assertNotIn("hi-Latn", graph["nodes"]["s1-bands"]["say"])
        self.assertIn("outside cause", source["nodes"]["s1-bands"]["say"]["en"])


if __name__ == "__main__":
    unittest.main()
