import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from kgc.data import Dataset, TrainGraph
from kgc.research.structure_audit import typed_paths, prepared_graphs
from kgc.research.sparsity import prepare
from test_core import toy_graph


class StructureTests(unittest.TestCase):
    def test_resource_stopped_cohort_does_not_restart_training(self):
        from kgc.research.structure import run
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/"resource-stop.json").write_text('{"reason":"thermal resource stop"}')
            with self.assertRaisesRegex(RuntimeError,"resource-stopped"):
                run(None,None,path)
            self.assertFalse((path/"protocol.json").exists())

    @unittest.skipUnless(importlib.util.find_spec("c_clause"),"PyClause unavailable")
    def test_fixed_native_vocabulary_allows_absent_relation_and_isolated_prior(self):
        from kgc.research.structure import native_vocabulary
        from kgc.research.families import AuditedRules
        from kgc.evaluation import ModelQuery
        full=TrainGraph((("aa","body","bb"),("cc","rel","dd")),("aa","bb","cc","dd"),("body","rel"))
        reduced=full.with_triples(full.triples[:1])
        indices=native_vocabulary(full)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"rules"
            path.write_text("20\t10\t.5\trel(X,Y) <= body(X,Y)\n20\t10\t.5\trel(X,dd) <=\n")
            ordinary=AuditedRules(full,path,certify_support=True)
            fixed=AuditedRules(full,path,certify_support=True,token_indices=indices)
            q=ModelQuery("aa","rel","tail")
            self.assertEqual(ordinary.predict(q).candidates,fixed.predict(q).candidates)
            changed=AuditedRules(reduced,path,certify_support=True,token_indices=indices)
            self.assertAlmostEqual(dict(changed.predict(q).candidates)["bb"],.4)
            isolated=changed.predict(ModelQuery("cc","rel","tail"))
            self.assertAlmostEqual(dict(isolated.candidates)["dd"],.004)
            self.assertTrue(isolated.exhaustive_support)
            self.assertEqual(changed.training_edges,set(reduced.triples))
    def test_paired_effects_cluster_directions_and_reject_mismatched_facts(self):
        from kgc.research.structure_report import effect,gap_effect
        base=[{"query_id":f"test:{i}:{d}","triple_id":f"test:{i}","head":"aa","relation":"p","tail":"bb","direction":d,"hits1":0}
              for i in range(3) for d in ("head","tail")]
        changed=[{**r,"hits1":1} for r in base]
        result=effect([changed],[base],repetitions=50)
        self.assertEqual(result["difference"],1)
        self.assertEqual(result["ci_low"],1)
        self.assertEqual(result["n_triples"],3)
        self.assertEqual(result["n_unique_queries"],6)
        self.assertFalse(result["all_rankings_certified"])
        certified=effect([[{**r,"hits_certified":True} for r in changed]],[[{**r,"hits_certified":True} for r in base]],repetitions=5)
        self.assertTrue(certified["all_rankings_certified"])
        mismatch=[{**r,"tail":"cc"} for r in changed]
        with self.assertRaisesRegex(ValueError,"identities"):
            effect([mismatch],[base],repetitions=5)
        independent=effect([changed,changed],[base,base],independent_models=True,repetitions=50)
        self.assertEqual(independent["difference"],1)
        paired=effect([base,changed],[base,changed],repetitions=100)
        independent=effect([base,changed],[base,changed],independent_models=True,repetitions=100)
        self.assertEqual(paired["ci_low"],0)
        self.assertLess(independent["ci_low"],0)
        self.assertGreater(independent["ci_high"],0)
        gap=gap_effect([changed],[base],[changed],[base],repetitions=50)
        self.assertEqual(gap["difference"],0)

    def test_native_witness_loss_is_sampled_and_training_only(self):
        from kgc.research.structure_cases import inspect_witnesses
        a=("aa","p","bb");b=("bb","q","cc");held=("aa","r","cc")
        rules=[{"expression":"r(X,Y) <= p(X,A), q(A,Y)","groundings":[[a,b]]}]
        result=inspect_witnesses(rules,{a,b},{a})
        self.assertFalse(result[0]["survives"])
        self.assertEqual(result[0]["missing_training_edges"],[b])
        with self.assertRaisesRegex(ValueError,"non-training"):
            inspect_witnesses([{**rules[0],"groundings":[[held]]}],{a,b},{a,b})
        with self.assertRaisesRegex(ValueError,"inconsistent"):
            inspect_witnesses(rules,{a,b},{a,b},("aa","r","dd"))
        checked=inspect_witnesses(rules,{a,b},{a,b},held)
        self.assertTrue(checked[0]["survives"])
    def test_typed_walks_count_parallel_relation_labels(self):
        graph=TrainGraph((("aa","p","bb"),("aa","q","bb"),("bb","p","cc"),("bb","q","cc"),("cc","p","dd")),
                         ("aa","bb","cc","dd"),("p","q"))
        values=typed_paths(graph,(("aa","p","cc"),("aa","p","dd")))
        self.assertEqual(values[0]["typed_twohop_walks_to_truth"],4)
        self.assertEqual(values[0]["untyped_twohop_intermediates_to_truth"],1)
        self.assertEqual(values[1]["typed_threehop_walks_to_truth"],4)
        reduced=typed_paths(graph.with_triples(graph.triples[1:]),(("aa","p","cc"),))[0]
        self.assertEqual(reduced["typed_twohop_walks_to_truth"],2)

    def test_removed_relation_cardinality_is_unobserved(self):
        from kgc.diagnostics import GraphDiagnostics
        graph=TrainGraph((("aa","present","bb"),),("aa","bb"),("present","removed"))
        stats=GraphDiagnostics(graph).relation_stats
        self.assertEqual(stats["present"]["cardinality"],"one-to-one")
        self.assertEqual(stats["removed"]["cardinality"],"unobserved")
        self.assertEqual(stats["removed"]["relation_frequency"],0)

    def test_prepared_graph_audit_rejects_tampering(self):
        graph=toy_graph()
        data=Dataset(graph,(),(("aa","parent","cc"),),(),(),{"sha256":{"test":"unit"}})
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"prepared"
            prepare(data,path)
            graphs=prepared_graphs(data,path)
            self.assertEqual(len(graphs),5)
            self.assertEqual(data.with_graph(graphs["targeted_local"][0]).positives_for_filter("test"),data.positives_for_filter("test"))
            target=path/"random_global/train.txt"
            target.write_text(target.read_text().splitlines()[0]+"\n")
            with self.assertRaisesRegex(ValueError,"differs"):
                prepared_graphs(data,path)

    @unittest.skipUnless(importlib.util.find_spec("pykeen"),"PyKEEN unavailable")
    def test_interrupted_training_restores_optimizer_and_random_streams(self):
        from kgc.research.intervention_training import fit
        graph=toy_graph()
        data=Dataset(graph,(("aa","parent","cc"),),(),(),(),{})
        cfg={"model":"ComplEx","seed":3,"embedding_dim":4,"learning_rate":.01,"device":"cpu","objective":"1vsAll",
             "reciprocal":True,"budgets":[1,2,3],"batch_size":4,"entity_dropout":.2,"relation_dropout":.1,"diagnostic_common_updates":4,
             "model_kwargs":{"regularizer":None,"entity_initializer":"xavier_normal_","relation_initializer":"xavier_normal_"}}
        with tempfile.TemporaryDirectory() as tmp:
            a,ra=fit(data,cfg,Path(tmp)/"continuous")
            with self.assertRaises(KeyboardInterrupt):
                fit(data,cfg,Path(tmp)/"resumed",stop_after_epoch=1)
            state=json.loads((Path(tmp)/"resumed/training-state.json").read_text())
            self.assertEqual(state["status"],"interrupted")
            self.assertFalse((Path(tmp)/"resumed/curve.json").exists())
            b,rb=fit(data,cfg,Path(tmp)/"resumed")
            self.assertEqual(ra["epoch_losses"],rb["epoch_losses"])
            self.assertEqual(ra["best_epoch"],rb["best_epoch"])
            self.assertEqual(ra["optimizer_updates"],rb["optimizer_updates"])
            for key,value in a.model.state_dict().items():
                self.assertTrue(a.torch.equal(value,b.model.state_dict()[key]))
            self.assertTrue((Path(tmp)/"resumed/matched-updates.pt").exists())
            with self.assertRaisesRegex(ValueError,"graph/config"):
                fit(data,{**cfg,"learning_rate":.02},Path(tmp)/"resumed")
