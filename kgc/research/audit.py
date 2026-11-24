"""Executable audit of saved runs plus real native-backend contract probes."""
from pathlib import Path
import json
import tempfile
from collections import Counter
import math
import csv
import sys
from ..data import TrainGraph, load_dataset
from ..evaluation import ModelQuery, Query, Prediction, FilterIndex, rank_prediction, queries
from ..backends.anyburl import AnyBURLBackend
from ..io import write_json, digest, triple_digest
from .families import describe


def native_probes():
    from clause import Options
    expected = {"B": .4, "Uc": .4, "Ud": .04, "Z": .004, "XXuc": .4, "XXud": .4}
    expressions = {"B": "rel(X,Y) <= body(X,Y)", "Uc": "rel(X,bb) <= body(X,cc)",
        "Ud": "rel(X,bb) <= body(X,A)", "Z": "rel(X,bb) <=", "XXuc": "rel(X,X) <= body(X,cc)",
        "XXud": "rel(X,X) <= body(X,A)"}
    graph = TrainGraph((("aa", "body", "bb"), ("aa", "body", "cc"), ("dd", "rel", "cc")),
                       ("aa", "bb", "cc", "dd"), ("body", "rel"))
    observations = {}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for family, expression in expressions.items():
            path = root / family
            path.write_text(f"20\t10\t0.5\t{expression}\n")
            b = AnyBURLBackend(graph, path, evidence_mode="none")
            pred = b.predict(ModelQuery("aa", "rel", "tail"))
            answer = "aa" if family.startswith("XX") else "bb"
            qa_score = dict(pred.candidates).get(answer)
            score = qa_score
            if family.startswith("XX") and score is None:
                score = float(b.score_triples((("aa", "rel", answer),))[0][0])
            assert math.isclose(score, expected[family], rel_tol=1e-6), (family, score)
            assert describe(path.read_text())["native_family"] == family
            observations[family] = {"raw_confidence": .5, "native_score": score, "expected_score": expected[family],
                                    "qa_score": qa_score,
                                    "qa_generation_discrepancy": family.startswith("XX") and qa_score is None,
                                    "classification_via_prediction_handler_supported": family != "Z"}
        edges = tuple(("aa", "body", f"ee{i:03}") for i in range(150)) + (("dd", "rel", "cc"),)
        many = TrainGraph(edges, tuple(sorted({e for h, r, t in edges for e in (h, t)})), ("body", "rel"))
        path = root / "many"
        path.write_text("200\t150\t0.75\trel(X,Y) <= body(X,Y)\n")
        small = AnyBURLBackend(many, path, top_k=10, evidence_mode="none").predict(ModelQuery("aa", "rel", "tail"))
        large = AnyBURLBackend(many, path, top_k=1000, evidence_mode="none").predict(ModelQuery("aa", "rel", "tail"))
        assert small.candidates == large.candidates and len(small.candidates) == 150
        # Filtering keeps the evaluated gold but removes alternative positives.
        q = Query("toy", "toy", ("aa", "rel", "ee149"), "tail")
        filtered = rank_prediction(q, small, many.entities, FilterIndex(tuple(("aa", "rel", f"ee{i:03}") for i in range(150))))
        assert filtered["rank"] == 1
        # One rule can overrun topk, while a later rule can still be skipped.
        # This distinguishes "not a strict truncation" from exhaustive support.
        more_edges = edges + tuple(("aa", "late", f"ee{i:03}") for i in range(150, 300))
        multi = TrainGraph(more_edges, tuple(sorted({e for h, r, t in more_edges for e in (h, t)})), ("body", "late", "rel"))
        path.write_text("200\t150\t0.75\trel(X,Y) <= body(X,Y)\n300\t150\t0.5\trel(X,Y) <= late(X,Y)\n")
        limited = AnyBURLBackend(multi, path, top_k=10, evidence_mode="none").predict(ModelQuery("aa", "rel", "tail"))
        complete = AnyBURLBackend(multi, path, top_k=len(multi.entities) + 1, evidence_mode="none").predict(ModelQuery("aa", "rel", "tail"))
        assert len(limited.candidates) < len(complete.candidates) == 300
    return {"family_confidence_probes": observations,
            "topk_probe": {"top_k_requested": 10, "supported_candidates_returned": 150,
                           "matches_top_k_1000": True, "interpretation": "single-rule overrun is not proof of exhaustive multi-rule search"},
            "multi_rule_counterexample": {"topk10_returned": len(limited.candidates), "universe_plus_one_returned": len(complete.candidates),
                                           "interpretation": "topk can stop processing later rules even when one rule overruns it; old lists remain censored"},
            "filter_probe": "gold kept, 149 alternative positives removed", "loader_defaults": Options().get("loader", as_string=False),
            "source_references": ["https://github.com/symbolic-kg/PyClause/blob/master/src/c_clause/features/Application.cpp",
                                  "https://github.com/symbolic-kg/PyClause/blob/master/clause/config-default.yaml"]}


def audit(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    d = load_dataset("data/codex-s")
    expected = {q.query_id: (*q.triple, q.direction) for q in queries(d.test)}
    csv.field_size_limit(sys.maxsize)
    runs = []
    for root in ("runs/codex-s-cpu-pilot-refined", "runs/codex-s-rule-length-pilot-retry"):
        for path in sorted(Path(root).rglob("manifest.json")):
            m = json.loads(path.read_text())
            assert m["status"] == "complete"
            assert m["dataset"]["sha256"] == d.provenance["sha256"]
            mapping = json.loads((path.parent / "mapping.json").read_text())
            assert mapping["entities"] == list(d.graph.entities) and mapping["relations"] == list(d.graph.relations)
            assert m["training_graph_sha256"] == triple_digest(d.graph.triples)
            for backend in ("embedding", "rules"):
                training = json.loads((path.parent / backend / "training.json").read_text())
                assert training["training_graph_sha256"] == triple_digest(d.graph.triples)
                with (path.parent / backend / "test_queries.csv").open() as handle:
                    observed = {}
                    for row in csv.DictReader(handle):
                        assert row["query_id"] not in observed
                        observed[row["query_id"]] = (row["head"], row["relation"], row["tail"], row["direction"])
                assert observed == expected
            runs.append({"path": str(path.parent), "status": "matching official splits, positive training graph hashes, test-query identities and vocabulary", "mode": m["run_kind"],
                         "n_unique_test_queries": len(expected), "n_test_triples": len(d.test),
                         "n_distinct_masked_inputs": len({q.model_input for q in queries(d.test)})})
    probes = native_probes()
    records = {"dataset": d.provenance, "runs": runs, "probes": probes,
        "legacy_definitions": {"rule_covered": "nonempty candidates before evaluator filtering, independent of correctness",
         "relational_path": "legacy all-terms-single-uppercase-variable syntax; includes reflexive XXud and does not identify native B family",
         "mixed": "more than one legacy kind among rules attributed to returned candidates, not an intrinsic query category",
         "truth_dependencies": ["rule_truth_diagnostic", "true_returned", "best truth confidence/support", "target degree", "paths to truth", "error category", "oracle"],
         "confidence": "legacy strong evidence uses raw mining confidence/support; native ranking uses smoothed, weighted confidence",
         "uncertainty": "head/tail kept within triple clusters; neural seeds resampled; fixed symbolic model gives no mining-variability estimate; conditional strata may vary by seed",
         "remaining_dependence": "shared entities, relations and masked queries across different test triples are not independent graph samples; triple bootstrap does not model all graph dependence"},
            "ranking_conclusion": "Old lists correctly remain censored. A single-rule synthetic probe returning 150 candidates under topk=10 DOES NOT prove completeness: real multi-rule queries returned different supports at topk100/1000. New runs require topk greater than the entire entity universe, disabled pruning/stopping, plus enlarged-limit equality checks before certifying abstaining supported-candidate Hits. This is not full-universe zero-tie MRR. Legacy files remain unchanged.",
        "grounded_cyclic": "serialized rules do not establish mining provenance; native Uc/Ud and explicit structural proxies are separate, not interchangeable labels",
        "previous_artifacts_modified": False}
    write_json(output / "audit.json", records)
    return records
