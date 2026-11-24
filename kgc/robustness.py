"""Paired intervention effects against matched 100%-edge / zero-noise controls."""
from collections import defaultdict
from pathlib import Path
import json
import numpy as np
from .io import write_json, write_csv


def crossed_bootstrap(rows, repetitions=1000, seed=2026):
    """Resample training seeds, perturbation seeds, and triple clusters separately.

    Input difference is already paired to the same baseline query. Requiring a
    rectangular grid prevents quiet exclusion of failed experiment cells.
    """
    if not rows:
        raise ValueError("No paired intervention observations")
    train_seeds = sorted({r["training_seed"] for r in rows})
    perturb_seeds = sorted({r["perturbation_seed"] for r in rows})
    cells = defaultdict(dict)
    for row in rows:
        cell = cells[(row["training_seed"], row["perturbation_seed"])]
        if row["query_id"] in cell:
            raise ValueError("Duplicate intervention query")
        cell[row["query_id"]] = row
    ids = sorted(next(iter(cells.values())))
    if len(cells) != len(train_seeds) * len(perturb_seeds) or any(set(c) != set(ids) for c in cells.values()):
        raise ValueError("Missing intervention cell or mismatched query set")
    blocks = defaultdict(list)
    reference = next(iter(cells.values()))
    for i, qid in enumerate(ids):
        blocks[reference[qid]["triple_id"]].append(i)
    blocks = list(blocks.values())
    sizes = np.array([len(b) for b in blocks])
    sums = np.zeros((len(train_seeds), len(perturb_seeds), len(blocks)))
    for i, ts in enumerate(train_seeds):
        for j, ps in enumerate(perturb_seeds):
            differences = np.array([cells[(ts, ps)][q]["difference"] for q in ids])
            sums[i, j] = [differences[b].sum() for b in blocks]
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(repetitions):
        a = rng.integers(len(train_seeds), size=len(train_seeds))
        b = rng.integers(len(perturb_seeds), size=len(perturb_seeds))
        c = rng.integers(len(blocks), size=len(blocks))
        estimates.append(sums[np.ix_(a, b, c)].sum() / (len(a) * len(b) * sizes[c].sum()))
    low, high = np.quantile(estimates, [.025, .975])
    return {"difference": float(sums.sum() / len(rows)), "ci_low": float(low), "ci_high": float(high),
            "n_queries": len(rows), "n_unique_queries": len(ids), "n_triples": len(blocks),
            "n_training_seeds": len(train_seeds), "n_perturbation_seeds": len(perturb_seeds),
            "bootstrap": "paired query; crossed training/perturbation seed resampling; triple clusters",
            "repetitions": repetitions, "seed": seed}


def intervention_effects(root):
    root = Path(root)
    variants = []
    controls = {}
    for path in sorted(root.rglob("manifest.json")):
        manifest = json.loads(path.read_text())
        intervention = manifest.get("intervention") or {}
        plan = intervention.get("plan", {})
        if manifest["status"] != "complete" or plan.get("kind") not in ("sparsity", "noise"):
            continue
        key = (plan["kind"], plan["training_seed"], plan["perturbation_seed"])
        severity = 1 - plan["retain"] if plan["kind"] == "sparsity" else plan["fraction"]
        item = (path.parent, manifest, plan, severity)
        if severity == 0:
            if key in controls:
                raise ValueError("Ambiguous controls: analyze one experiment directory at a time")
            controls[key] = item
        else:
            variants.append(item)
    grouped = defaultdict(list)
    for path, manifest, plan, severity in variants:
        key = (plan["kind"], plan["training_seed"], plan["perturbation_seed"])
        if key not in controls:
            raise ValueError(f"Missing matched unperturbed control for {path}")
        control_path = controls[key][0]
        perturbed = {r["query_id"]: r for r in json.loads((path / "diagnostics.json").read_text())}
        baseline = {r["query_id"]: r for r in json.loads((control_path / "diagnostics.json").read_text())}
        if perturbed.keys() != baseline.keys():
            raise ValueError("Intervention/control evaluated different queries")
        for backend in ("embedding", "rule"):
            for metric in ("hits1", "hits10", "covered"):
                group = (plan["kind"], plan["strategy"], severity, backend, metric)
                for qid, row in perturbed.items():
                    base = baseline[qid]
                    if any(row[k] != base[k] for k in ("head", "relation", "tail", "direction")):
                        raise ValueError("Control/intervention query ID refers to different facts")
                    grouped[group].append({"query_id": qid, "triple_id": row["triple_id"],
                        "training_seed": plan["training_seed"], "perturbation_seed": plan["perturbation_seed"],
                        "difference": float(row[f"{backend}_{metric}"]) - float(base[f"{backend}_{metric}"])})
    effects = [{"intervention": kind, "strategy": strategy, "fraction_removed_or_added": fraction,
                "backend": backend, "metric": metric, **crossed_bootstrap(rows),
                "estimand": "perturbed minus matched unperturbed; negative is degradation",
                "rule_metric_status": "retrieved-list outcomes may be censored"}
               for (kind, strategy, fraction, backend, metric), rows in grouped.items()]
    write_json(root / "intervention_effects.json", effects)
    write_csv(root / "intervention_effects.csv", effects)
    return effects
