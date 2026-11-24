import json
from pathlib import Path
import shutil
import tempfile
import unittest
from kgc.data import load_dataset, read_triples, Dataset
from kgc.evaluation import queries
from test_core import toy_graph

FIXTURE = Path(__file__).parent / "fixtures" / "codex-s-excerpt"


class DataTests(unittest.TestCase):
    def test_real_official_excerpt(self):
        data = load_dataset(FIXTURE, excerpt=True)
        self.assertEqual(data.graph.triples[0], ("Q7604", "P1412", "Q188"))
        self.assertEqual(data.test[0], ("Q206832", "P27", "Q142"))
        self.assertEqual(data.valid_negatives[0], ("Q185724", "P27", "Q27"))
        self.assertEqual(len(list(queries(data.test))), 96)
        self.assertFalse(set(data.graph.triples) & set(data.valid_negatives + data.test_negatives))
        self.assertTrue(data.provenance["excerpt"])
        self.assertIsNone(data.provenance["source"]["commit"])

    def test_excerpt_never_silently_benchmark(self):
        with self.assertRaises(ValueError):
            load_dataset(FIXTURE)
        with self.assertRaises(ValueError):
            load_dataset(FIXTURE, "m")

    def test_split_overlap_and_verified_negative_checks(self):
        for destination in ("test", "valid_negatives", "test_negatives"):
            with self.subTest(destination=destination), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                for p in FIXTURE.iterdir():
                    shutil.copy(p, root / p.name)
                with (root / f"{destination}.txt").open("a") as f:
                    f.write((root / "train.txt").read_text().splitlines()[0] + "\n")
                with self.assertRaises(ValueError):
                    load_dataset(root, excerpt=True)

    def test_malformed_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "triples.txt"
            for text in ("aa rr bb\naa rr bb\n", "aa bb\n"):
                p.write_text(text)
                with self.assertRaises(ValueError):
                    read_triples(p)

    def test_validation_filter_excludes_test(self):
        g = toy_graph()
        data = Dataset(g, (("aa", "sym", "cc"),), (("aa", "sym", "dd"),), (), (), {})
        self.assertNotIn(data.test[0], data.positives_for_filter("valid"))
        self.assertIn(data.test[0], data.positives_for_filter("test"))


if __name__ == "__main__":
    unittest.main()
