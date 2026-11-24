import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from kgc.research.families import describe, make_subsets


class FamilyTests(unittest.TestCase):
    def test_paired_aggregation_rejects_reused_ids_for_other_facts(self):
        from kgc.research.report import paired
        row = {"query_id": "test:0:tail", "triple_id": "test:0", "head": "aa", "relation": "rel", "tail": "bb", "direction": "tail", "hits1": 1}
        with self.assertRaisesRegex(ValueError, "different facts"):
            paired([row], [{**row, "tail": "cc"}], "mismatched facts")
    def test_research_matrix_rejects_other_interactions(self):
        from kgc.research.curves import CurveModel
        from test_core import toy_graph
        with self.assertRaisesRegex(ValueError, "ComplEx only"):
            CurveModel(toy_graph(), {"model": "RotatE", "objective": "1vsAll"})
        with self.assertRaisesRegex(ValueError, "Research objectives"):
            CurveModel(toy_graph(), {"model": "ComplEx", "objective": "unspecified-LCWA"})
    def test_interventions_keep_original_filter_knowledge(self):
        from kgc.data import Dataset
        from test_core import toy_graph
        g = toy_graph()
        d = Dataset(g, (), (), (), (), {})
        removed = d.with_graph(g.with_triples(g.triples[1:]))
        self.assertIn(g.triples[0], removed.positives_for_filter("test"))
        unknown = next((h,r,t) for h in g.entities for r in g.relations for t in g.entities if (h,r,t) not in g.triples)
        noisy = removed.with_graph(removed.graph.with_triples(removed.graph.triples + (unknown,)))
        self.assertNotIn(unknown, noisy.positives_for_filter("test"))
        self.assertEqual(d.positives_for_filter("test"), noisy.positives_for_filter("test"))
    def test_relation_matched_sparsity_controls_and_reproducibility(self):
        from kgc.research.sparsity import interventions
        from test_core import toy_graph
        g = toy_graph()
        a = interventions(g, retain=.9)
        b = interventions(g, retain=.9)
        self.assertEqual(a, b)
        self.assertEqual(a["targeted_local"][1]["removed_by_relation"], a["targeted_relation_matched_control"][1]["removed_by_relation"])
        for graph, metadata in a.values():
            self.assertEqual(graph.entities, g.entities)
            self.assertTrue(set(graph.triples) <= set(g.triples))
        with self.assertRaises(ValueError):
            interventions(g, retain=-.1)
    def test_native_categories_do_not_treat_all_constants_as_priors(self):
        def rule(expr):
            return describe("20\t10\t0.5\t" + expr)
        self.assertEqual(rule("rel(X,Y) <= body(X,Y)")["native_family"], "B")
        uc = rule("rel(X,bb) <= body(X,cc)")
        self.assertTrue(uc["constant_bearing"])
        self.assertFalse(uc["unconditional_prior"])
        self.assertEqual(uc["native_family"], "Uc")
        self.assertEqual(rule("rel(X,bb) <= body(X,A)")["native_family"], "Ud")
        self.assertEqual(rule("rel(X,X) <= body(X,A)")["native_family"], "XXud")
        self.assertTrue(rule("rel(X,bb) <=")["unconditional_prior"])

    def test_frozen_constant_lines_do_not_change_with_cyclic_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.write_text("20\t10\t.5\trel(X,bb) <= body(X,A)\n20\t10\t.5\trel(X,Y) <= body(X,Y)\n20\t10\t.5\trel(X,Y) <= body(X,A), body(A,Y)\n")
            subs = make_subsets(source, Path(tmp) / "subsets")
            a = Path(subs["fixed_constants_general_le1"]["path"]).read_text().splitlines()
            b = Path(subs["fixed_constants_general_le2"]["path"]).read_text().splitlines()
            self.assertEqual(a[0], b[0])
            self.assertEqual(len(a), 2)
            self.assertEqual(len(b), 3)
            self.assertEqual(subs["all"]["sha256"], subs["constants_general"]["sha256"])

    @unittest.skipUnless(importlib.util.find_spec("c_clause"), "PyClause unavailable")
    def test_real_native_scoring_and_no_truncation_contract(self):
        from kgc.research.audit import native_probes
        p = native_probes()
        self.assertEqual(p["topk_probe"]["supported_candidates_returned"], 150)
        self.assertEqual(p["multi_rule_counterexample"]["universe_plus_one_returned"], 300)

    @unittest.skipUnless(importlib.util.find_spec("c_clause"), "PyClause unavailable")
    def test_reused_unfiltered_candidates_preserve_classification_scores(self):
        from kgc.data import TrainGraph
        from kgc.evaluation import ModelQuery
        from kgc.research.families import AuditedRules
        from unittest.mock import patch
        graph = TrainGraph((("aa", "body", "bb"), ("cc", "rel", "aa")), ("aa", "bb", "cc"), ("body", "rel"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules"
            path.write_text("20\t10\t.5\trel(X,Y) <= body(X,Y)\n20\t10\t.5\trel(X,cc) <=\n")
            b = AuditedRules(graph, path, certify_support=True)
            triples = (("aa", "rel", "bb"), ("aa", "rel", "cc"), ("aa", "rel", "aa"))
            expected = b.score_triples(triples)
            p = b.predict(ModelQuery("aa", "rel", "tail"))
            b.reuse_masked_candidates_for_classification([(ModelQuery("aa", "rel", "tail"), p.candidates)])
            with patch.object(b, "predict", side_effect=AssertionError("Cached query must not be recomputed")):
                actual = b.score_triples(triples)
            np.testing.assert_array_equal(actual[0], expected[0])
            np.testing.assert_array_equal(actual[1], expected[1])

    @unittest.skipUnless(importlib.util.find_spec("pykeen"), "PyKEEN unavailable")
    def test_reciprocal_scoring_and_training_matrix_match_pykeen(self):
        from kgc.research.curves import CurveModel, fit_curve, load_curve
        from kgc.data import Dataset
        from kgc.evaluation import ModelQuery
        from test_core import toy_graph
        graph = toy_graph()
        cfg = {"model": "ComplEx", "seed": 0, "embedding_dim": 4, "learning_rate": .01, "device": "cpu",
               "objective": "1vsAll", "reciprocal": True, "budgets": [1, 2], "batch_size": 4,
               "model_kwargs": {"entity_initializer": "xavier_normal_", "relation_initializer": "xavier_normal_", "regularizer": None}}
        b = CurveModel(graph, cfg)
        b.model.eval()
        batch = b.torch.tensor([[0, 0]])
        self.assertTrue(b.torch.allclose(b.training_scores(batch), b.model.score_t(batch), atol=1e-6))
        pair = ModelQuery("bb", "parent", "head")
        predicted = b.predict(pair)
        expected = b.model.score_t(b.torch.tensor([[graph.entity_to_id['bb'], graph.relation_to_id['parent'] + len(graph.relations)]]))
        self.assertTrue(np.allclose([s for _, s in predicted.candidates], expected.detach().numpy()[0]))
        dataset = Dataset(graph, (("aa", "parent", "cc"),), (), (), (), {})
        with tempfile.TemporaryDirectory() as tmp:
            model, record = fit_curve(dataset, cfg, Path(tmp) / "curve")
            restored, _ = load_curve(graph, Path(tmp) / "curve")
            self.assertEqual(record["test_access"], "none")
            self.assertEqual(model.predict(pair).candidates, restored.predict(pair).candidates)
            from kgc.data import TrainGraph
            permuted = TrainGraph(graph.triples, tuple(reversed(graph.entities)), graph.relations)
            with self.assertRaisesRegex(ValueError, "ID map mismatch"):
                load_curve(permuted, Path(tmp) / "curve")
