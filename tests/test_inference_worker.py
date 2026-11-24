import importlib.util
from pathlib import Path
import tempfile
import unittest
from kgc.io import digest
from kgc.research.structure_inference import resolve_file


class InferenceWorkerTests(unittest.TestCase):
    def test_raw_cache_does_not_share_answer_specific_filtering(self):
        from kgc.evaluation import evaluate,Prediction,ModelQuery
        facts=(("aa","rel","bb"),("cc","rel","bb"));entities=("aa","bb","cc","dd")
        class Backend:
            def __init__(self):self.calls=[];self.raw=[]
            def predict(self,query):
                self.calls.append(query)
                self.assert_masked=isinstance(query,ModelQuery)
                scores={"aa":.9,"bb":.1,"cc":.8,"dd":.7} if query.direction=="head" else {e:float(e=="bb") for e in entities}
                pred=Prediction(list(scores.items()),full_ranking=True);self.raw.append(pred);return pred
        cached=Backend();a,metrics=evaluate(cached,facts,entities,facts,cache_size=4)
        ordinary=Backend();b,_=evaluate(ordinary,facts,entities,facts,cache_size=0)
        self.assertEqual(len(cached.calls),3);self.assertEqual(metrics["prediction_cache_hits"],1)
        self.assertEqual([r["rank"] for r in a],[r["rank"] for r in b])
        self.assertEqual([r["rank"] for r in a if r["direction"]=="head"],[1.,1.])
        self.assertTrue(cached.assert_masked)
        self.assertIn(("cc",.8),cached.raw[0].candidates)
        self.assertIn(("aa",.9),cached.raw[0].candidates)

    def test_relocated_artifact_requires_exact_content_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);local=p/"rules";local.write_text("verified contents\n")
            expected=digest(local)
            self.assertEqual(resolve_file(p/"missing",local,expected),local)
            local.write_text("changed contents\n")
            with self.assertRaisesRegex(ValueError,"content-verified"):
                resolve_file(p/"missing",local,expected)

    @unittest.skipUnless(importlib.util.find_spec("c_clause"),"PyClause unavailable")
    def test_metadata_light_predictions_preserve_native_order_and_scores(self):
        from kgc.data import TrainGraph
        from kgc.evaluation import ModelQuery
        from kgc.research.families import AuditedRules
        graph=TrainGraph((("aa","body","dd"),("bb","body","aa")),("aa","bb","cc","dd"),("body","rel"))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"rules"
            path.write_text("20\t10\t.5\trel(X,cc) <= body(X,dd)\n20\t10\t.5\trel(X,cc) <= body(X,A)\n20\t10\t.5\trel(X,Y) <= body(X,Y)\n")
            indices={"entities":list(graph.entities),"relations":list(graph.relations)}
            ordinary=AuditedRules(graph,path,certify_support=True,token_indices=indices)
            lite=AuditedRules(graph,path,certify_support=True,token_indices=indices,retain_catalog_metadata=False)
            for q in (ModelQuery("aa","rel","tail"),ModelQuery("bb","rel","tail"),ModelQuery("cc","rel","head")):
                with self.subTest(query=q):
                    self.assertEqual(ordinary.predict(q).candidates,lite.predict(q).candidates)
            self.assertEqual(len(ordinary.rules),len(lite.rules))
            self.assertEqual(lite.rule_catalog,{})
            self.assertEqual(lite.by_expression,{})
            with self.assertRaisesRegex(RuntimeError,"retained catalog metadata"):
                lite.explain([("aa","rel","cc")])
