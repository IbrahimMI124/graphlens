"""Explicit, seeded training-graph interventions; held-out splits are immutable."""
from collections import defaultdict
import numpy as np
from .io import triple_digest


def select_targets(graph, seed, fraction=.1):
    if not 0 < fraction <= 1:
        raise ValueError("Target fraction must be in (0,1]")
    rng = np.random.default_rng(seed)
    count = max(1, round(len(graph.entities) * fraction))
    return tuple(sorted(rng.choice(graph.entities, size=count, replace=False).tolist()))


def sparsify(graph, retain, seed, strategy="random", targets=()):
    if not 0 < retain <= 1 or strategy not in ("random", "local"):
        raise ValueError("Invalid sparsification setting")
    rng = np.random.default_rng(seed)
    n = len(graph.triples)
    remove_count = n - round(n * retain)
    order = rng.permutation(n).tolist()
    targets = set(targets)
    if strategy == "local":
        if not targets:
            raise ValueError("Local removal requires train-selected targets")
        incident = [i for i in order if graph.triples[i][0] in targets or graph.triples[i][2] in targets]
        incident_set = set(incident)
        other = [i for i in order if i not in incident_set]
        order = incident + other
    removed = set(order[:remove_count])
    kept = tuple(edge for i, edge in enumerate(graph.triples) if i not in removed)
    metadata = {"intervention": "sparsification", "strategy": strategy, "retain_requested": retain,
                "retain_actual": len(kept) / n, "seed": seed, "removed": remove_count,
                "targets": sorted(targets), "target_selection": "training entities only, separate seed",
                "removed_incident_to_targets": sum(h in targets or t in targets for i, (h, _, t) in enumerate(graph.triples) if i in removed),
                "training_graph_sha256": triple_digest(kept)}
    return graph.with_triples(kept), metadata


def inject_noise(graph, fraction, seed, strategy="random", entity_types=None):
    """Add uncertain corruptions, not labelled negatives. Never claim unobserved=false.

    type_consistent uses relation-specific observed domain/range pools. If metadata
    types are supplied it additionally requires shared types with replaced endpoint.
    Collisions with held-out/verified facts are audited by the runner and abort.
    """
    if not 0 <= fraction <= .1 or strategy not in ("random", "type_consistent"):
        raise ValueError("Invalid noise setting")
    rng = np.random.default_rng(seed)
    domains, ranges = defaultdict(set), defaultdict(set)
    for h, r, t in graph.triples:
        domains[r].add(h)
        ranges[r].add(t)
    pools = {(r, d): tuple(sorted(values)) for d, groups in ((0, domains), (2, ranges)) for r, values in groups.items()}
    original = set(graph.triples)
    injected = set()
    desired = round(len(graph.triples) * fraction)
    attempts = 0
    while len(injected) < desired and attempts < max(1000, desired * 200):
        attempts += 1
        edge = graph.triples[int(rng.integers(len(graph.triples)))]
        direction = int(rng.choice([0, 2]))
        pool = graph.entities if strategy == "random" else pools[(edge[1], direction)]
        candidate = str(rng.choice(pool))
        if strategy == "type_consistent" and entity_types is not None:
            if not set(entity_types.get(candidate, ())) & set(entity_types.get(edge[direction], ())):
                continue
        new = list(edge)
        new[direction] = candidate
        new = tuple(new)
        if new not in original:
            injected.add(new)
    if len(injected) != desired:
        raise RuntimeError(f"Cannot produce requested unique corruptions: {len(injected)}/{desired}")
    triples = graph.triples + tuple(sorted(injected))
    return graph.with_triples(triples), {"intervention": "noise injection", "fraction": fraction,
        "strategy": strategy, "seed": seed, "injected_count": len(injected), "attempts": attempts,
        "type_constraint": "shared metadata type + empirical relation domain/range" if entity_types is not None and strategy == "type_consistent" else
                           "empirical relation domain/range (weak type proxy)" if strategy == "type_consistent" else "none",
        "injected_edges": sorted(injected), "truth_status": "unknown; may be valid unobserved facts",
        "training_graph_sha256": triple_digest(triples)}


def audit_intervention(dataset, graph):
    """Split hygiene gate only: fail, never adapt/resample against held-out facts."""
    edges = set(graph.triples)
    leaked = edges & set(dataset.valid + dataset.test)
    verified = edges & set(dataset.valid_negatives + dataset.test_negatives)
    if leaked or verified:
        raise ValueError(f"Intervention rejected before training: held-out positive collisions={len(leaked)}, verified negative collisions={len(verified)}. Do not select a replacement seed using test performance.")
    return {"heldout_positive_collisions": 0, "verified_negative_collisions": 0}
