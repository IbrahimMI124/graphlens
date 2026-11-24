from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from kgc.data import Dataset
from kgc.perturbations import sparsify, inject_noise, select_targets, audit_intervention
from kgc.statistics import paired_bootstrap, complementarity, scenario_summaries
from kgc.experiments import plan_experiment
from kgc.backends.anyburl import parse_rule, mine, AnyBURLBackend
from kgc.backends.embedding import EmbeddingBackend
from kgc.cli import smoke
from kgc.data import load_dataset
from test_core import toy_graph


class PerturbationTests(unittest.TestCase):
    def test_reproducible_sparsification_and_universe(self):
        g = toy_graph()
        for strategy in ("random", "local"):
            a, meta = sparsify(g, .5, 23, strategy, ("aa",))
            b, _ = sparsify(g, .5, 23, strategy, ("aa",))
            self.assertEqual(a.triples, b.triples)
            self.assertEqual(len(a.triples), 4)
            self.assertTrue(set(a.triples) <= set(g.triples))
            self.assertEqual(g.entities, a.entities)
        full, _ = sparsify(g, 1, 0)
        self.assertEqual(full, g)

    def test_local_removes_incident_first(self):
        g = toy_graph()
        changed, meta = sparsify(g, .5, 0, "local", ("aa",))
        removed = set(g.triples) - set(changed.triples)
        self.assertTrue(all("aa" in (h, t) for h, _, t in removed))
        self.assertEqual(meta["removed_incident_to_targets"], 4)

    def test_reproducible_noise_and_domain_range(self):
        g = toy_graph()
        for strategy in ("random", "type_consistent"):
            a, meta = inject_noise(g, .1, 7, strategy)
            b, _ = inject_noise(g, .1, 7, strategy)
            self.assertEqual(a.triples, b.triples)
            self.assertEqual(len(a.triples), 9)
            self.assertTrue(set(g.triples) < set(a.triples))
            if strategy == "type_consistent":
                for h, r, t in set(a.triples) - set(g.triples):
                    self.assertIn(h, {x for x, rel, _ in g.triples if rel == r})
                    self.assertIn(t, {x for _, rel, x in g.triples if rel == r})

    def test_target_seed_separate_and_train_only(self):
        g = toy_graph()
        self.assertEqual(select_targets(g, 10), select_targets(g, 10))
        self.assertTrue(set(select_targets(g, 10)) <= set(g.entities))

    def test_leakage_gate_no_resampling(self):
        g = toy_graph()
        heldout = (("aa", "sym", "dd"),)
        negatives = (("dd", "sym", "aa"),)
        data = Dataset(g, (), heldout, negatives, (), {})
        for forbidden in (heldout[0], negatives[0]):
            with self.assertRaises(ValueError):
                audit_intervention(data, g.with_triples(g.triples + (forbidden,)))
        self.assertEqual(audit_intervention(data, g)["heldout_positive_collisions"], 0)


class StatsTests(unittest.TestCase):
    def rows(self):
        return [{"query_id": f"q{i}:{direction}", "triple_id": f"q{i}", "embedding_hits1": a,
                 "rule_hits1": b, "embedding_hits10": a, "rule_hits10": b,
                 "rule_hits_certified": True, "rule_covered": bool(b), "group": "all", "seed": seed}
                for seed in (0, 1, 2) for i, (a, b) in enumerate([(1, 1), (1, 0), (0, 1), (0, 0)])
                for direction in ("head", "tail")]

    def test_paired_bootstrap_reproducible_and_counts(self):
        a = paired_bootstrap(self.rows(), repetitions=100)
        b = paired_bootstrap(self.rows(), repetitions=100)
        self.assertEqual(a, b)
        self.assertEqual(a["n_queries"], 24)
        self.assertEqual(a["n_unique_queries"], 8)
        self.assertEqual(a["n_triples"], 4)
        self.assertEqual(a["n_seeds"], 3)
        self.assertEqual(a["difference"], 0)
        self.assertLessEqual(a["ci_low"], 0)
        self.assertGreaterEqual(a["ci_high"], 0)
        one = [r for r in self.rows() if r["seed"] == 0]
        bad = self.rows() + one
        with self.assertRaises(ValueError):
            paired_bootstrap(bad)

    def test_complementarity_and_groups(self):
        comp = complementarity(self.rows())
        self.assertEqual(comp["oracle_union_success"], .75)
        self.assertEqual(comp["error_jaccard"], 1/3)
        self.assertEqual(comp["proportions"]["only_rules"], .25)
        groups = scenario_summaries(self.rows(), "group", repetitions=50)
        self.assertEqual(groups[0]["n_queries"], 24)

    def test_seed_dependent_scenario_membership_is_retained(self):
        rows = self.rows()
        for row in rows:
            row["availability"] = "covered" if row["seed"] == 0 or row["query_id"].startswith("q0") else "uncovered"
        groups = scenario_summaries(rows, "availability", repetitions=50)
        self.assertEqual(sum(g["n_queries"] for g in groups), len(rows))
        self.assertTrue(all("conditional" in g["bootstrap"] for g in groups))
        self.assertTrue(all(g["n_seeds"] == 3 for g in groups))


class AdapterTests(unittest.TestCase):
    def test_controlled_experiments_do_not_reuse_baseline_rules(self):
        from unittest.mock import patch
        from kgc.experiments import execute_experiment
        cfg = json.loads(Path("configs/development.json").read_text())
        cfg["anyburl"]["pretrained_rules"] = "fixed-baseline-rules"
        dataset = Dataset(toy_graph(), (), (), (), (), {"excerpt": False})
        captured = []
        with tempfile.TemporaryDirectory() as d, patch("kgc.experiments.run_pair", side_effect=lambda data, config, *args: captured.append(config)):
            execute_experiment("D", dataset, cfg, d)
        self.assertEqual(len(captured), 3)
        self.assertTrue(all("pretrained_rules" not in c["anyburl"] for c in captured))

    def test_reused_rule_checkpoint_requires_matching_checksum(self):
        from kgc.experiments import train_backend
        from kgc.io import write_json, triple_digest
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rules = root / "rules-1"
            rules.write_text("20\t10\t0.5\tancestor(X,Y) <= parent(X,A), parent(A,Y)\n")
            write_json(root / "training.json", {"training_graph_sha256": triple_digest(toy_graph().triples),
                       "rule_file_sha256": "does-not-match", "config": {}})
            with self.assertRaisesRegex(ValueError, "checksum"):
                train_backend("rules", toy_graph(), {"anyburl": {"pretrained_rules": str(rules)}}, root / "out")

    def test_real_anyburl_rule_format(self):
        r = parse_rule("20\t10\t0.5\tancestor(X,Y) <= parent(X,A), parent(A,Y)")
        self.assertEqual((r.support, r.length, r.kind), (10, 2, "relational_path"))
        c = parse_rule("20 10 0.5 speaks(X,Q188) <= lives(X,Q30)")
        self.assertEqual(c.kind, "constant")
        self.assertEqual(parse_rule("20 10 .5 speaks(X,Q188) <=").kind, "entity_prior")
        with self.assertRaises(ValueError):
            parse_rule("bad rule")
        with self.assertRaises(ValueError):
            parse_rule("2 10 5 sym(X,Y) <= parent(X,Y)")

    def test_anyburl_missing_binary_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(RuntimeError, "Real AnyBURL"):
                mine(toy_graph(), {"jar": str(Path(d) / "missing.jar")}, Path(d) / "out")

    def test_experiment_plans_and_control_budgets(self):
        cfg = json.loads(Path("configs/development.json").read_text())
        b = plan_experiment("B", cfg)
        self.assertEqual(len(b), 7)
        self.assertEqual({x["retain"] for x in b}, {1., .9, .7, .5})
        self.assertEqual({x["max_length"] for x in plan_experiment("D", cfg)}, {1, 2, 3})
        self.assertEqual(len(plan_experiment("E", cfg)), 7)

    def test_real_smoke_and_no_fake_metrics(self):
        with tempfile.TemporaryDirectory() as d:
            data = load_dataset("tests/fixtures/codex-s-excerpt", excerpt=True)
            result = smoke(data, d)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["n_checked_queries"], 16)
            self.assertNotIn("mrr", result)


if __name__ == "__main__":
    unittest.main()
