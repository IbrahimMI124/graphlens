"""Paired bootstrap at triple level; both directions stay in the same cluster."""
from collections import defaultdict
import numpy as np


def paired_bootstrap(rows, metric="hits1", seed=2026, repetitions=2000):
    if not rows:
        return {"n_queries": 0, "difference": None, "ci_low": None, "ci_high": None}
    by_seed = defaultdict(dict)
    for row in rows:
        sid = row.get("seed", 0)
        key = row["query_id"]
        if key in by_seed[sid]:
            raise ValueError("Duplicate query within a training seed")
        by_seed[sid][key] = row
    ids = sorted(next(iter(by_seed.values())))
    if any(set(x) != set(ids) for x in by_seed.values()):
        raise ValueError("Repeated seeds must use the same queries")
    reference = next(iter(by_seed.values()))
    for mapping in by_seed.values():
        for qid in ids:
            if any(mapping[qid].get(k) != reference[qid].get(k)
                   for k in ("triple_id", "head", "relation", "tail", "direction")):
                raise ValueError("Query IDs refer to different facts across training seeds")
    clusters = defaultdict(list)
    for i, qid in enumerate(ids):
        clusters[reference[qid]["triple_id"]].append(i)
    blocks = list(clusters.values())
    # Preserve denominators under groups containing only one direction of a triple.
    sums, sizes = [], np.array([len(b) for b in blocks])
    for mapping in by_seed.values():
        delta = np.array([mapping[q][f"embedding_{metric}"] - mapping[q][f"rule_{metric}"] for q in ids], dtype=float)
        sums.append([delta[b].sum() for b in blocks])
    sums = np.asarray(sums)
    rng = np.random.default_rng(seed)
    estimates = np.empty(repetitions)
    for i in range(repetitions):
        sampled_seeds = rng.integers(0, len(sums), size=len(sums))
        sampled_blocks = rng.integers(0, len(blocks), size=len(blocks))
        estimates[i] = sums[np.ix_(sampled_seeds, sampled_blocks)].sum() / (sizes[sampled_blocks].sum() * len(sums))
    lower, upper = np.quantile(estimates, [.025, .975])
    return {"n_queries": len(rows), "n_unique_queries": len(ids), "n_triples": len(blocks),
            "n_seeds": len(by_seed), "difference": float(sums.sum() / (len(ids) * len(sums))),
            "ci_low": float(lower), "ci_high": float(upper), "repetitions": repetitions,
            "bootstrap": "paired hierarchical seed/triple clusters; directions paired", "seed": seed,
            "estimand": f"embedding minus rule {metric}"}


def complementarity(rows, k=1):
    if not rows:
        return {"n_queries": 0}
    a = np.array([r[f"embedding_hits{k}"] for r in rows], dtype=bool)
    b = np.array([r[f"rule_hits{k}"] for r in rows], dtype=bool)
    categories = {"both_correct": a & b, "only_embeddings": a & ~b,
                  "only_rules": ~a & b, "both_incorrect": ~a & ~b}
    error_union = (~a | ~b).sum()
    return {"n_queries": len(rows), "k": k,
            "counts": {k: int(v.sum()) for k, v in categories.items()},
            "proportions": {k: float(v.mean()) for k, v in categories.items()},
            "oracle_union_success": float((a | b).mean()),
            "error_jaccard": float((~a & ~b).sum() / error_union) if error_union else 0.,
            "oracle_status": "diagnostic upper bound for recorded successes; not deployable",
            "ranking_status": "exact" if all(r.get("rule_hits_certified", False) for r in rows) else "rule retrieved-list outcomes, potentially censored"}


def conditional_bootstrap(rows, all_seeds, repetitions=1000, seed=2026):
    """Conditional strata may contain different queries in each learned seed.

    Resample seeds and their within-stratum triple clusters, keeping numerator
    and denominator paired. Never intersect seed-dependent coverage groups.
    """
    rng = np.random.default_rng(seed)
    blocks = {}
    for sid in all_seeds:
        grouped = defaultdict(list)
        for r in rows:
            if r.get("seed", 0) == sid:
                grouped[r["triple_id"]].append(r)
        blocks[sid] = list(grouped.values())
    estimates = []
    seeds = list(all_seeds)
    for _ in range(repetitions):
        numerator = denominator = 0
        for index in rng.integers(len(seeds), size=len(seeds)):
            local = blocks[seeds[index]]
            if not local:
                continue
            for j in rng.integers(len(local), size=len(local)):
                for row in local[j]:
                    numerator += row["embedding_hits1"] - row["rule_hits1"]
                    denominator += 1
        if denominator:
            estimates.append(numerator / denominator)
    low, high = np.quantile(estimates, [.025, .975])
    return {"n_queries": len(rows), "n_unique_queries": len({r["query_id"] for r in rows}),
            "n_triples": len({r["triple_id"] for r in rows}), "n_seeds": len(seeds),
            "observations_per_seed": {str(s): sum(len(x) for x in blocks[s]) for s in seeds},
            "difference": float(np.mean([r["embedding_hits1"] - r["rule_hits1"] for r in rows])),
            "ci_low": float(low), "ci_high": float(high), "repetitions": repetitions,
            "nonempty_bootstrap_replicates": len(estimates),
            "bootstrap": "conditional seed/local-triple clusters; seed-dependent membership retained",
            "estimand": "embedding minus rule Hits@1 conditional on recorded stratum", "seed": seed}


def scenario_summaries(rows, group_key, repetitions=1000):
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_key, "unavailable"))].append(row)
    result = []
    for name, items in sorted(grouped.items()):
        seed_ids = sorted({r.get("seed", 0) for r in rows})
        membership = [{r["query_id"] for r in items if r.get("seed", 0) == sid} for sid in seed_ids]
        interval = (paired_bootstrap(items, repetitions=repetitions) if all(x == membership[0] for x in membership)
                    else conditional_bootstrap(items, seed_ids, repetitions=repetitions))
        record = {"group": group_key, "value": name, **interval,
                  "embedding_hits1": float(np.mean([r["embedding_hits1"] for r in items])),
                  "rule_hits1": float(np.mean([r["rule_hits1"] for r in items])),
                  "rule_coverage": float(np.mean([r["rule_covered"] for r in items])),
                  "metric_status": "exact" if all(r["rule_hits_certified"] for r in items) else "retrieved-list proxy"}
        for field in ("head_degree", "tail_degree", "relation_frequency", "symmetry_strength",
                      "best_inverse_strength", "best_subsumption_strength", "best_composition_strength"):
            values = [r[field] for r in items if r.get(field) is not None]
            record[f"mean_{field}"] = float(np.mean(values)) if values else None
        result.append(record)
    return result
