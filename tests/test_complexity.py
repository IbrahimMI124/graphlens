"""Synthetic artifact tests for length-sweep pairing, not model results."""
from pathlib import Path
import tempfile
import unittest
from kgc.io import write_json
from kgc.complexity import complexity_effects, build_complexity_report


class ComplexityTests(unittest.TestCase):
    def build(self, root):
        for length, hits in ((1, [1, 0, 0, 0]), (2, [1, 1, 1, 0]), (3, [1, 1, 1, 1])):
            p = root / f"length-{length}"
            write_json(p / "manifest.json", {"status": "complete", "training_graph_sha256": "synthetic",
                "dataset": {"sha256": {"test": "unchanged"}},
                "config": {"embedding": {"seed": 0}, "anyburl": {"seconds": 1, "max_length": length}},
                "intervention": {"plan": {"kind": "rule_length", "max_length": length, "training_seed": 0}}})
            write_json(p / "rules" / "rules.json", [{"kind": "relational_path", "length": length, "confidence": .5, "support": 5}])
            write_json(p / "metrics.json", {"rules": {"training": {"training_seconds": 1},
                "test": {"n_queries": 4, "inference_seconds": .1, "hits1": sum(hits) / 4, "hits10": 1,
                         "coverage": 1, "covered_hits1": sum(hits) / 4, "mrr_exact": None}}})
            write_json(p / "diagnostics.json", [{"query_id": f"q{i}", "triple_id": f"t{i//2}",
                "head": "aa", "relation": "rr", "tail": "bb", "direction": "head" if i % 2 == 0 else "tail",
                "embedding_hits1": int(i == 0), "embedding_hits10": 1, "embedding_covered": True,
                "rule_hits1": hit, "rule_hits10": 1, "rule_covered": True} for i, hit in enumerate(hits)])

    def test_paired_length_changes_keep_neural_control_identical(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.build(root)
            changes = complexity_effects(root)
            neural = [r for r in changes if r["backend"] == "embedding"]
            self.assertTrue(all(r["difference"] == 0 for r in neural))
            rules = {r["max_cyclic_length"]: r for r in changes if r["backend"] == "rule" and r["metric"] == "hits1"}
            self.assertEqual(rules[2]["difference"], .5)
            self.assertEqual(rules[3]["difference"], .75)
            self.assertTrue((root / "rule_complexity_summary.json").exists())
            report = build_complexity_report(root, root / "report", plots=False)
            self.assertIn("query variation only", report.read_text())
            import csv
            with (root / "report" / "whole_model_outcomes.csv").open() as f:
                self.assertTrue(all(int(r["n_total_rules"]) == 1 for r in csv.DictReader(f)))

    def test_changed_graph_is_rejected(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.build(root)
            path = root / "length-2" / "manifest.json"
            m = json.loads(path.read_text())
            m["training_graph_sha256"] = "changed"
            write_json(path, m)
            with self.assertRaisesRegex(ValueError, "changed the graph"):
                complexity_effects(root)
