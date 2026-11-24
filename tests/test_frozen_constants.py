"""Tiny native constant-rule evidence interventions; no model training/mining."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from kgc.data import TrainGraph
from kgc.evaluation import ModelQuery
from kgc.research.families import describe
from kgc.research.structure_cases import inspect_witnesses
from kgc.research.structure_frozen_cases import build


class FrozenConstantTests(unittest.TestCase):
    def test_witness_family_rejects_unconditional_and_unknown_subsets(self):
        for family in ("zero","all","unknown"):
            with self.subTest(family=family):
                with self.assertRaisesRegex(ValueError,"conditional-rule subsets"):
                    build(None,None,None,family=family)

    @unittest.skipUnless(importlib.util.find_spec("c_clause"),"PyClause unavailable")
    def test_native_uc_head_tail_body_deletion_preserves_smoothing(self):
        self._native_deletion("rel(X,cc) <= body(X,dd)","Uc",.4)

    @unittest.skipUnless(importlib.util.find_spec("c_clause"),"PyClause unavailable")
    def test_native_ud_head_tail_body_deletion_preserves_weight(self):
        self._native_deletion("rel(X,cc) <= body(X,A)","Ud",.04)

    def _native_deletion(self,expression,family,expected_score):
        from kgc.research.structure import native_vocabulary
        from kgc.research.families import AuditedRules
        removed=("aa","body","dd")
        graph=TrainGraph((removed,("zz","body","dd"),("cc","anchor","ee"),("zz","rel","cc")),
                         ("aa","zz","cc","dd","ee"),("body","anchor","rel"))
        modified=graph.with_triples(graph.triples[1:])
        indices=native_vocabulary(graph)
        line=f"20\t10\t.5\t{expression}\n"
        category=describe(line)
        self.assertEqual(category["native_family"],family)
        self.assertTrue(category["constant_bearing"])
        self.assertFalse(category["unconditional_prior"])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"conditional.rules";path.write_text(line)
            before=AuditedRules(graph,path,certify_support=True,token_indices=indices)
            after=AuditedRules(modified,path,certify_support=True,token_indices=indices)
            self.assertEqual(len(before.rules),1)
            self.assertTrue(all(r.length>0 for r in before.rules))
            for query,answer in ((ModelQuery("aa","rel","tail"),"cc"),(ModelQuery("cc","rel","head"),"aa")):
                with self.subTest(family=family,direction=query.direction):
                    predicted=before.predict(query);changed=after.predict(query)
                    self.assertTrue(predicted.exhaustive_support)
                    self.assertTrue(changed.exhaustive_support)
                    self.assertAlmostEqual(dict(predicted.candidates)[answer],expected_score)
                    self.assertNotIn(answer,dict(changed.candidates))
            surviving=dict(after.predict(ModelQuery("cc","rel","head")).candidates)
            self.assertEqual(set(surviving),{"zz"})
            self.assertAlmostEqual(surviving["zz"],expected_score)
            target=("aa","rel","cc")
            evidence,_=before.explain([target])
            witnesses=inspect_witnesses(evidence[target],set(graph.triples),set(modified.triples),target)
            self.assertTrue(witnesses)
            self.assertTrue(all(not w["survives"] for w in witnesses))
            self.assertTrue(all(removed in w["missing_training_edges"] for w in witnesses))
            later,_=after.explain([target])
            self.assertEqual(later.get(target,[]),[])
            self.assertEqual(after.training_edges,set(modified.triples))


if __name__=="__main__":
    unittest.main()
