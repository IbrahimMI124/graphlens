import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from kgc.data import Dataset
from kgc.evaluation import Prediction
from kgc.experiments import run_pair, analyze_runs
from kgc.reporting import build_report, plot_differences
from kgc.robustness import crossed_bootstrap
from test_core import toy_graph


class CrossedTests(unittest.TestCase):
    def test_crossed_seed_pairs(self):
        rows = [{"query_id": f"q{i}:{d}", "triple_id": f"q{i}", "training_seed": ts,
                 "perturbation_seed": ps, "difference": -.25}
                for ts in (0, 1) for ps in (11, 23) for i in (0, 1) for d in ("head", "tail")]
        result = crossed_bootstrap(rows, repetitions=50)
        self.assertEqual(result["difference"], -.25)
        self.assertEqual(result["ci_low"], -.25)
        self.assertEqual(result["n_queries"], 16)
        self.assertEqual(result["n_unique_queries"], 4)
        with self.assertRaises(ValueError):
            crossed_bootstrap(rows[:-1])


class DriverTests(unittest.TestCase):
    def test_mocked_pipeline_and_report_not_backend_integration(self):
        """Exercise orchestration with explicit test doubles, never benchmark findings."""
        graph = toy_graph()
        dataset = Dataset(graph, (("aa", "sym", "cc"),), (("dd", "parent", "aa"),), (), (),
                          {"excerpt": False, "dataset": "SYNTHETIC UNIT TEST ONLY", "sha256": {"valid": "test"}})
        cfg = json.loads(Path("configs/development.json").read_text())
        cfg["classification"] = False
        class ModelDouble:
            def predict(self, query):
                return Prediction([(e, i) for i, e in enumerate(graph.entities)], full_ranking=True)
        def fake_train(name, received_graph, config, output):
            self.assertEqual(received_graph.triples, graph.triples)
            self.assertFalse(hasattr(received_graph, "test"))
            return ModelDouble(), {"training_seconds": 0., "test_double": True}
        with tempfile.TemporaryDirectory() as d, patch("kgc.experiments.train_backend", side_effect=fake_train):
            rows = run_pair(dataset, cfg, Path(d) / "mock-seed0")
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["embedding_hits1"], rows[0]["rule_hits1"])
            result = analyze_runs(d, "A")
            self.assertEqual(result[0]["paired_difference"]["difference"], 0.)
            report = build_report(d, plots=False)
            self.assertIn("Overall baselines", report.read_text())
            self.assertIn("Correct answer", report.read_text())

    def test_empty_report_does_not_invent_results(self):
        with tempfile.TemporaryDirectory() as d:
            p = build_report(d, plots=False)
            self.assertIn("unexecuted", p.read_text())
            self.assertIn("none are invented", p.read_text())

    @unittest.skipUnless(importlib.util.find_spec("matplotlib"), "Matplotlib unavailable")
    def test_scientific_plot_exports(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "synthetic-test.png"
            plot_differences([{"value": "synthetic", "difference": .1, "ci_low": -.1, "ci_high": .3,
                              "n_queries": 10, "n_seeds": 1}], p, "SYNTHETIC UNIT TEST ONLY")
            self.assertGreater(p.stat().st_size, 1000)
            self.assertTrue(p.with_suffix(".pdf").exists())


@unittest.skipUnless(importlib.util.find_spec("sklearn"), "scikit-learn unavailable")
class ClassificationTests(unittest.TestCase):
    def test_calibration_uses_validation_only_and_missing_rule_abstains(self):
        from kgc.classification import calibrate_and_evaluate
        graph = toy_graph()
        valid = (("aa", "sym", "cc"), ("cc", "sym", "aa"))
        vn = (("aa", "sym", "dd"), ("dd", "sym", "aa"))
        test = (("aa", "parent", "cc"), ("bb", "sym", "cc"))
        tn = (("dd", "parent", "aa"), ("cc", "parent", "aa"))
        dataset = Dataset(graph, valid, test, vn, tn, {})
        class ScorerDouble:
            def __init__(self, test_sign):
                self.calls = []
                self.test_sign = test_sign
            def score_triples(self, triples):
                self.calls.append(triples)
                if triples == valid + vn:
                    return np.array([2., 1., -1., -2.]), np.array([True] * 4)
                return self.test_sign * np.array([1.5, .5, -.5, -1.5]), np.array([True, True, True, False])
        a, b = ScorerDouble(1), ScorerDouble(-1)
        ma, rows = calibrate_and_evaluate(a, dataset)
        mb, _ = calibrate_and_evaluate(b, dataset)
        self.assertEqual(ma["threshold"], mb["threshold"])
        self.assertEqual(ma["calibration"], mb["calibration"])
        self.assertEqual(ma["coverage"], .75)
        self.assertEqual(rows[-1]["prediction"], "abstain")
        self.assertEqual(a.calls, [valid + vn, test + tn])
        self.assertGreater(ma["auroc_raw"], mb["auroc_raw"])


if __name__ == "__main__":
    unittest.main()
