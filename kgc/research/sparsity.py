"""Prepare graph interventions and relation-distribution-matched controls.

This module writes graphs/plans only. It never reuses a pre-perturbation model.
"""
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from ..data import write_triples
from ..diagnostics import GraphDiagnostics
from ..perturbations import select_targets
from ..io import write_json, write_csv, triple_digest


def interventions(graph, retain=.9, seed=11, target_seed=101):
    if not 0 < retain <= 1:
        raise ValueError("Retention must be in (0,1]")
    rng = np.random.default_rng(seed)
    n_remove = len(graph.triples) - round(retain * len(graph.triples))
    by_relation = defaultdict(list)
    for i, (_, r, _) in enumerate(graph.triples):
        by_relation[r].append(i)
    targets = set(select_targets(graph, target_seed, .1))
    order = rng.permutation(len(graph.triples)).tolist()
    incident = [i for i in order if graph.triples[i][0] in targets or graph.triples[i][2] in targets]
    if len(incident) < n_remove:
        raise ValueError("Too few targeted edges; change declared target fraction, not silent fallback")
    local = set(incident[:n_remove])
    local_counts = Counter(graph.triples[i][1] for i in local)
    # Exact same number removed per relation, randomized across its edges.
    matched = set()
    for r, count in local_counts.items():
        matched.update(rng.choice(by_relation[r], size=count, replace=False).tolist())
    expected = {r: len(ids) * n_remove / len(graph.triples) for r, ids in by_relation.items()}
    quotas = {r: int(np.floor(v)) for r, v in expected.items()}
    for r in sorted(expected, key=lambda r: (-(expected[r] - quotas[r]), r))[:n_remove - sum(quotas.values())]:
        quotas[r] += 1
    stratified = set()
    for r, count in quotas.items():
        stratified.update(rng.choice(by_relation[r], size=count, replace=False).tolist())
    masks = {"original": set(), "random_global": set(order[:n_remove]),
             "random_relation_stratified": stratified, "targeted_local": local,
             "targeted_relation_matched_control": matched}
    result = {}
    for name, removed in masks.items():
        kept = tuple(t for i, t in enumerate(graph.triples) if i not in removed)
        result[name] = (graph.with_triples(kept), {"seed": seed, "target_seed": target_seed,
            "removed_indices": sorted(removed), "removed_by_relation": dict(Counter(graph.triples[i][1] for i in removed)),
            "targets": sorted(targets), "target_incident_removed": sum(graph.triples[i][0] in targets or graph.triples[i][2] in targets for i in removed),
            "training_graph_sha256": triple_digest(kept), "n_removed": len(removed),
            "retain_actual": len(kept) / len(graph.triples)})
    assert result["targeted_local"][1]["removed_by_relation"] == result["targeted_relation_matched_control"][1]["removed_by_relation"]
    return result


def prepare(dataset, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = {}
    for name, (graph, record) in interventions(dataset.graph).items():
        path = output / name
        write_triples(path / "train.txt", graph.triples)
        diag = GraphDiagnostics(graph)
        degrees = np.array(list(diag.degree.values()))
        record.update({"n_edges": len(graph.triples), "n_isolated": int((degrees == 0).sum()),
                       "degree_quantiles": np.quantile(degrees, [0, .25, .5, .75, 1]).tolist(),
                       "mean_degree": float(degrees.mean()), "relation_frequencies": dict(diag.frequency),
                       "candidate_universe_preserved": graph.entities == dataset.graph.entities,
                       "held_out_split_hashes": dataset.provenance["sha256"],
                       "models_retrained": False, "status": "prepared; inference/training not executed"})
        # Gold-dependent path features are evaluation diagnostics only; selection
        # of targets/removal masks above receives no held-out triples.
        write_csv(path / "held-out-path-diagnostics.csv", [{"triple_id": f"test:{i}", "head": h, "relation": r, "tail": t,
                  **diag.query_features({"head": h, "relation": r, "tail": t, "direction": "tail"})}
                  for i, (h, r, t) in enumerate(dataset.test)])
        write_json(path / "intervention.json", record)
        records[name] = record
    write_json(output / "plan.json", {"interventions": records,
        "comparison": "targeted_local vs targeted_relation_matched_control holds exact retained relation counts fixed; random_relation_stratified vs original approximately preserves relation proportions",
        "next_execution": "retrain selected ComplEx recipe for three seeds and fresh AnyBURL inventory per graph; apply the same native family subsets; never load full-graph rules/checkpoints",
        "primary_estimand": "paired change in filtered Hits, constant/general coverage and supported-only accuracy on unchanged official queries",
        "filter_protocol": "fixed original positive training facts plus held-out positives in evaluator only; removed facts remain true and injected uncertain edges never automatically become filtering positives",
        "bootstrap": "cluster head/tail by test triple, resample training and perturbation seeds separately when replicated",
        "limitations": "one prepared removal seed; connectivity remains entangled with entity-local frequencies; type distribution matching does not identify all causal mechanisms",
        "execution_status": "graphs/diagnostics prepared only; both-model retraining smoke pending"})
