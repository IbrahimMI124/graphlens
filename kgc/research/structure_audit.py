"""Audit immutable prepared graphs; exact typed-walk diagnostics, no fitting."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import numpy as np
from ..data import read_triples, load_dataset
from ..diagnostics import GraphDiagnostics
from ..evaluation import queries
from ..io import digest, triple_digest, write_json, write_csv
from .sparsity import interventions

CONDITIONS = ("original", "random_global", "random_relation_stratified", "targeted_local", "targeted_relation_matched_control")


def typed_paths(graph, triples):
    """Exact directed relation-labelled walks, not necessarily simple paths.

    Endpoints are held-out answers in evaluator diagnostics only. Selection of
    graph interventions never receives these triples. Only consistently forward
    directed walks are counted. Inverse-oriented native bodies (h<-a->t, for
    example) are excluded; these counts are neither all rule paths nor a superset
    of native groundings, which may also enforce additional constraints.
    """
    pairs = Counter((h, t) for h, _, t in graph.triples)
    outgoing, incoming = defaultdict(set), defaultdict(set)
    for h, _, t in graph.triples:
        outgoing[h].add(t)
        incoming[t].add(h)
    result = []
    for h, r, t in triples:
        middle = outgoing[h] & incoming[t]
        two = sum(pairs[h, m] * pairs[m, t] for m in middle)
        three = sum(pairs[h, a] * pairs[a, b] * pairs[b, t]
                    for a in outgoing[h] for b in outgoing[a] & incoming[t])
        result.append({"typed_twohop_walks_to_truth": two, "typed_threehop_walks_to_truth": three,
                       "untyped_twohop_intermediates_to_truth": len(middle)})
    return result


def prepared_graphs(dataset, prepared):
    prepared = Path(prepared)
    plan = json.loads((prepared / "plan.json").read_text())
    expected = interventions(dataset.graph, retain=.9, seed=11, target_seed=101)
    result = {}
    for name in CONDITIONS:
        rows = read_triples(prepared / name / "train.txt")
        graph, meta = expected[name]
        if rows != graph.triples:
            raise ValueError(f"Prepared {name} differs from reproducible training-only removal")
        saved = plan["interventions"][name]
        for key in ("training_graph_sha256", "removed_indices", "removed_by_relation", "targets", "seed", "target_seed"):
            if saved[key] != meta[key]:
                raise ValueError(f"Prepared metadata mismatch: {name}/{key}")
        if saved["held_out_split_hashes"] != dataset.provenance["sha256"]:
            raise ValueError("Prepared graphs refer to other official splits")
        modified = dataset.with_graph(graph)
        assert modified.valid == dataset.valid and modified.test == dataset.test
        assert modified.graph.entities == dataset.graph.entities and modified.graph.relations == dataset.graph.relations
        assert modified.positives_for_filter("test") == dataset.positives_for_filter("test")
        assert modified.positives_for_filter("valid") == dataset.positives_for_filter("valid")
        result[name] = (graph, saved)
    assert Counter(r for _, r, _ in result["targeted_local"][0].triples) == Counter(r for _, r, _ in result["targeted_relation_matched_control"][0].triples)
    return result


def audit(dataset, prepared, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    graphs = prepared_graphs(dataset, prepared)
    original_frequency = Counter(r for _, r, _ in dataset.graph.triples)
    original_diag = GraphDiagnostics(dataset.graph)
    original_paths = typed_paths(dataset.graph, dataset.test)
    comparisons, all_features = [], []
    target_set = set(graphs["original"][1]["targets"])
    for name, (graph, metadata) in graphs.items():
        diag = GraphDiagnostics(graph)
        paths = typed_paths(graph, dataset.test) if name != "original" else original_paths
        for i, ((h, r, t), p, base) in enumerate(zip(dataset.test, paths, original_paths)):
            assert p["typed_twohop_walks_to_truth"] <= base["typed_twohop_walks_to_truth"]
            assert p["typed_threehop_walks_to_truth"] <= base["typed_threehop_walks_to_truth"]
            row = {"condition": name, "triple_id": f"test:{i}", "head": h, "relation": r, "tail": t,
                   "head_targeted": h in target_set, "tail_targeted": t in target_set,
                   "original_head_degree": original_diag.degree[h], "modified_head_degree": diag.degree[h],
                   "original_tail_degree": original_diag.degree[t], "modified_tail_degree": diag.degree[t],
                   "original_relation_frequency": original_frequency[r], "modified_relation_frequency": diag.frequency[r],
                   "relation_cardinality_original": original_diag.relation_stats[r]["cardinality"],
                   "relation_cardinality_modified": diag.relation_stats[r]["cardinality"],
                   **{f"original_{k}": v for k, v in base.items()}, **{f"modified_{k}": v for k, v in p.items()}}
            all_features.append(row)
        degrees = np.array(list(diag.degree.values()))
        global_two = sum(diag.in_degree[e] * diag.out_degree[e] for e in graph.entities)
        global_three = sum(diag.in_degree[h] * diag.out_degree[t] for h, _, t in graph.triples)
        record = {"condition": name, "n_edges": len(graph.triples), "retention": len(graph.triples)/len(dataset.graph.triples),
            "n_entities_in_universe": len(graph.entities), "n_relations_in_universe": len(graph.relations),
            "n_active_relations": len(diag.frequency), "n_isolated": int((degrees == 0).sum()),
            "mean_degree": float(degrees.mean()), "median_degree": float(np.median(degrees)),
            "degree_quantiles": np.quantile(degrees, [0, .25, .5, .75, 1]).tolist(),
            "target_incident_edges_removed": metadata["target_incident_removed"],
            "relation_frequency_total_variation": sum(abs(diag.frequency[r]/len(graph.triples) - original_frequency[r]/len(dataset.graph.triples)) for r in graph.relations)/2,
            "global_typed_twohop_walks": global_two, "global_typed_threehop_walks": global_three,
            "mean_test_endpoint_typed_twohop_walks": float(np.mean([p["typed_twohop_walks_to_truth"] for p in paths])),
            "mean_test_endpoint_typed_threehop_walks": float(np.mean([p["typed_threehop_walks_to_truth"] for p in paths])),
            "n_test_facts_losing_twohop_walks": sum(p["typed_twohop_walks_to_truth"] < b["typed_twohop_walks_to_truth"] for p, b in zip(paths, original_paths)),
            "training_graph_sha256": triple_digest(graph.triples)}
        comparisons.append(record)
    write_csv(output / "graph-comparison.csv", comparisons)
    write_csv(output / "graph-query-features.csv", all_features)
    write_json(output / "audit.json", {"conditions": comparisons, "prepared_root": str(prepared),
        "prepared_plan_sha256": digest(Path(prepared)/"plan.json"), "official_splits": dataset.provenance,
        "query_sequence_sha256": triple_digest(tuple((q.query_id, q.direction, "\t".join(q.triple)) for q in queries(dataset.test))),
        "checks": {"reproduced_training_only_masks": True, "held_out_splits_unchanged": True,
                   "candidate_vocabulary_unchanged": True, "original_positive_evaluator_filters_fixed": True,
                   "exact_relation_counts_match_targeted_control": True},
        "path_definition": "exact forward-directed typed length2/3 walks, repeated entities allowed; excludes inverse-oriented rule bodies; held-out endpoints used only for diagnostics; not total relational evidence or native rule groundings",
        "selection_scope": "interventions(graph: TrainGraph) receives no held-out facts; target_seed101, removal_seed11",
        "replication_limit": "one prepared perturbation realization; no population-level causal generalization"})
    fields = ("condition", "n_edges", "n_isolated", "mean_degree", "relation_frequency_total_variation", "global_typed_twohop_walks", "target_incident_edges_removed")
    lines = ["# Phase 5: graph-perturbation validation", "", "All five prepared graphs were reconstructed from training-only seeds and matched exactly. Original held-out queries, candidate vocabularies and evaluator positive filters are fixed.", "",
             "| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in comparisons:
        lines.append("| " + " | ".join(f"{row[k]:.6f}" if isinstance(row[k], float) else str(row[k]) for k in fields) + " |")
    lines += ["", "Targeted and relation-matched control graphs remove exactly the same number of edges per relation. Their endpoint/degree/path distributions may differ; matching relation counts does not hold every entity-specific regularity fixed.", "",
              "Random relation-stratified removal preserves relation proportions up to integer rounding. Global-random removal does not constrain those proportions. None of the graphs isolates an entity in this prepared 90% cohort.", "",
              "Typed walk counts include different edge-label sequences and may revisit nodes. They follow only forward h-to-t edges and exclude inverse-oriented rule bodies, so they do not measure all relational evidence or native groundings. Query-endpoint counts require the held-out answer and are diagnostic only. Actual native rule groundings are checked separately against the training edge sets. See graph-query-features.csv for every original/modified test fact."]
    (output / "validation-report.md").write_text("\n".join(lines)+"\n")
    return comparisons
