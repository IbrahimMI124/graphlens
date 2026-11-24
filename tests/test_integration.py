"""Optional tests skip explicitly when real backends/data are unavailable."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
import numpy as np
from kgc.data import load_dataset
from kgc.evaluation import ModelQuery
from test_core import toy_graph


def available(name):
    return importlib.util.find_spec(name) is not None


class IntegrationTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("KGC_DATA_S"), "KGC_DATA_S: complete official CoDEx-S not available")
    def test_complete_codex_s(self):
        data = load_dataset(os.environ["KGC_DATA_S"], "s")
        self.assertEqual(len(data.graph.entities), 2034)
        self.assertEqual(len(data.graph.relations), 42)

    @unittest.skipUnless(os.environ.get("KGC_DATA_M"), "KGC_DATA_M: complete official CoDEx-M not available")
    def test_complete_codex_m(self):
        data = load_dataset(os.environ["KGC_DATA_M"], "m")
        self.assertEqual(len(data.graph.entities), 17050)
        self.assertEqual(len(data.graph.relations), 51)

    @unittest.skipUnless(available("pykeen") and available("torch"), "PyKEEN/PyTorch not installed")
    def test_neural_training_scoring_checkpoint(self):
        from kgc.backends.embedding import EmbeddingBackend
        graph = toy_graph()
        for name in ("ComplEx", "RotatE"):
            cfg = {"model": name, "embedding_dim": 4, "seed": 0, "learning_rate": .01,
                   "epochs": 1, "batch_size": 4, "num_negs_per_pos": 1, "log_epochs": True}
            with self.subTest(model=name), tempfile.TemporaryDirectory() as d:
                backend = EmbeddingBackend(graph, cfg)
                backend.fit(d)
                a = backend.predict(ModelQuery("aa", "parent", "tail"))
                restored = EmbeddingBackend.load(graph, d)
                b = restored.predict(ModelQuery("aa", "parent", "tail"))
                self.assertEqual(a.candidates, b.candidates)
                self.assertEqual(len(a.candidates), 4)
                self.assertTrue(np.isfinite([s for _, s in a.candidates]).all())

    @unittest.skipUnless(available("c_clause"), "PyClause C++ backend not installed")
    def test_pyclause_qa_and_groundings(self):
        from kgc.backends.anyburl import AnyBURLBackend
        with tempfile.TemporaryDirectory() as d:
            rules = Path(d) / "rules"
            # Hand-authored rule APPLICATION fixture, explicitly not learned AnyBURL results.
            rules.write_text("20\t10\t0.5\tancestor(X,Y) <= parent(X,A), parent(A,Y)\n")
            backend = AnyBURLBackend(toy_graph(), rules)
            pred = backend.predict(ModelQuery("aa", "ancestor", "tail"))
            self.assertIn("cc", dict(pred.candidates))
            self.assertTrue(pred.evidence["cc"])
            scores, covered = backend.score_triples((("aa", "ancestor", "cc"), ("dd", "ancestor", "aa")))
            self.assertTrue(covered[0])
            self.assertFalse(covered[1])
            self.assertEqual(scores[1], 0)
            compact = AnyBURLBackend(toy_graph(), rules, evidence_mode="references")
            compact_pred = compact.predict(ModelQuery("aa", "ancestor", "tail"))
            self.assertEqual(pred.candidates, compact_pred.candidates)
            refs = compact_pred.evidence["cc"]
            self.assertTrue(refs)
            self.assertEqual(compact.rule_catalog[refs[0]]["length"], 2)
            no_evidence = AnyBURLBackend(toy_graph(), rules, evidence_mode="none")
            self.assertEqual(no_evidence.predict(ModelQuery("aa", "ancestor", "tail")).candidates, pred.candidates)

    @unittest.skipUnless(os.environ.get("KGC_ANYBURL_JAR"), "KGC_ANYBURL_JAR: real miner not installed")
    def test_real_java_mining(self):
        from kgc.backends.anyburl import mine
        with tempfile.TemporaryDirectory() as d:
            path, record = mine(toy_graph(), {"jar": os.environ["KGC_ANYBURL_JAR"], "seconds": 1,
                                            "max_length": 2, "min_support": 1}, d)
            self.assertTrue(path.is_file())
            self.assertIn("jar_sha256", record)


if __name__ == "__main__":
    unittest.main()
