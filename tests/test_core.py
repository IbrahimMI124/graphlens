import unittest
from kgc.data import TrainGraph
from kgc.evaluation import ModelQuery, Prediction, FilterIndex, queries, rank_prediction, evaluate, summarize
from kgc.diagnostics import GraphDiagnostics, compare_rows


def toy_graph():
    triples = (("aa", "sym", "bb"), ("bb", "sym", "aa"),
               ("aa", "parent", "bb"), ("bb", "child", "aa"),
               ("bb", "parent", "cc"), ("cc", "child", "bb"),
               ("aa", "ancestor", "cc"), ("aa", "ancestor", "bb"))
    return TrainGraph(triples, ("aa", "bb", "cc", "dd"), ("ancestor", "child", "parent", "sym"))


class CoreTests(unittest.TestCase):
    def test_mapping_roundtrip(self):
        g = toy_graph()
        decoded = tuple((g.entities[h], g.relations[r], g.entities[t]) for h, r, t in g.mapped())
        self.assertEqual(decoded, g.triples)
        self.assertEqual(g.with_triples(g.triples[:2]).entities, g.entities)
        with self.assertRaises(KeyError):
            g.mapped((("unknown", "sym", "aa"),))

    def test_query_directions_answer_blind(self):
        head, tail = list(queries((("aa", "parent", "bb"),)))
        self.assertEqual(head.model_input, ModelQuery("bb", "parent", "head"))
        self.assertEqual(tail.model_input, ModelQuery("aa", "parent", "tail"))
        self.assertFalse(hasattr(head.model_input, "answer"))
        self.assertFalse(hasattr(head.model_input, "triple_id"))

    def test_cached_predictions_filter_each_gold_answer_independently(self):
        calls = []
        class Model:
            def predict(self, q):
                calls.append(q)
                return Prediction([("aa", 0), ("bb", 3), ("cc", 2), ("dd", 1)], full_ranking=True)
        triples = (("aa", "parent", "bb"), ("aa", "parent", "cc"))
        rows, summary = evaluate(Model(), triples, toy_graph().entities, triples, cache_size=8)
        self.assertEqual(summary["prediction_cache_hits"], 1)
        self.assertEqual(len(calls), 3)
        self.assertEqual([r["rank"] for r in rows if r["direction"] == "tail"], [1, 1])

    def test_filtered_rank_and_ties(self):
        q = list(queries((("aa", "parent", "cc"),)))[1]
        pred = Prediction([("aa", 0), ("bb", 5), ("cc", 3), ("dd", 3)], full_ranking=True)
        filt = FilterIndex((("aa", "parent", "bb"), ("aa", "parent", "cc")))
        result = rank_prediction(q, pred, toy_graph().entities, filt)
        self.assertEqual(result["rank"], 1.5)
        self.assertAlmostEqual(result["reciprocal_rank"], 2/3)
        self.assertEqual(result["hits1"], 0)

    def test_rule_coverage_not_correctness(self):
        q = list(queries((("aa", "parent", "cc"),)))[1]
        filt = FilterIndex(())
        covered = rank_prediction(q, Prediction([("bb", .9)], exhaustive_support=True), toy_graph().entities, filt)
        self.assertTrue(covered["covered"])
        self.assertFalse(covered["true_returned"])
        self.assertIsNone(covered["reciprocal_rank"])
        unsupported = rank_prediction(q, Prediction([], exhaustive_support=True), toy_graph().entities, filt)
        self.assertFalse(unsupported["covered"])
        self.assertEqual(unsupported["hits10"], 0)
        self.assertIsNone(unsupported["score"])
        truncated = rank_prediction(q, Prediction([("bb", .9)]), toy_graph().entities, filt)
        self.assertFalse(truncated["hits_certified"])

    def test_invalid_candidates_and_fake_full_rank(self):
        q = next(queries((("aa", "parent", "cc"),)))
        for pred in [Prediction([("unknown", .5)]), Prediction([("aa", 1)], full_ranking=True),
                     Prediction([("aa", float("nan"))]), Prediction([("aa", 1), ("aa", 2)])]:
            with self.assertRaises(ValueError):
                rank_prediction(q, pred, toy_graph().entities, FilterIndex(()))

    def test_degrees(self):
        diag = GraphDiagnostics(toy_graph())
        self.assertEqual(sum(diag.degree.values()), 2 * len(toy_graph().triples))
        self.assertEqual(diag.degree["dd"], 0)
        self.assertEqual(diag.out_degree["aa"], 4)

    def test_known_patterns(self):
        diag = GraphDiagnostics(toy_graph())
        patterns = diag.patterns()
        self.assertEqual(diag.relation_stats["sym"]["symmetry_strength"], 1)
        inv = next(x for x in patterns if x["pattern"] == "inverse" and x["body"] == "parent" and x["head"] == "child")
        self.assertEqual(inv["strength"], 1)
        comp = next(x for x in patterns if x["pattern"] == "composition" and x["body"] == ["parent", "parent"] and x["head"] == "ancestor")
        self.assertEqual(comp["strength"], 1)
        self.assertEqual(comp["body_pairs"], 1)
        sub = next(x for x in patterns if x["pattern"] == "subsumption" and x["body"] == "parent" and x["head"] == "ancestor")
        self.assertEqual(sub["strength"], .5)

    def test_inference_never_receives_targets_or_filters(self):
        observed = []
        class Spy:
            def predict(self, q):
                observed.append(q)
                return Prediction([(e, i) for i, e in enumerate(toy_graph().entities)], full_ranking=True)
        triples = (("aa", "parent", "cc"),)
        rows, summary = evaluate(Spy(), triples, toy_graph().entities, triples)
        self.assertEqual(observed, [ModelQuery("cc", "parent", "head"), ModelQuery("aa", "parent", "tail")])
        self.assertEqual(summary["n_queries"], 2)
        self.assertIsNotNone(summary["mrr_exact"])
        compared = compare_rows(rows, rows, toy_graph())
        self.assertEqual(len(compared), 2)
        self.assertIn("head_degree", compared[0])
        with self.assertRaises(ValueError):
            compare_rows(rows, rows[:1], toy_graph())


if __name__ == "__main__":
    unittest.main()
