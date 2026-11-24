"""Explicit validation-only hyperparameter selection. No test evaluator is called."""
from copy import deepcopy
from pathlib import Path
import numpy as np
from .experiments import train_backend, assert_full_study_data
from .evaluation import evaluate
from .io import write_json


def tune(dataset, config, candidates, output):
    assert_full_study_data(dataset)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records, means, cache = [], [], {}
    for index, override in enumerate(candidates):
        candidate = deepcopy(config)
        for backend in ("embedding", "anyburl"):
            candidate[backend].update(override.get(backend, {}))
        scores = []
        for seed in config["seeds"]:
            candidate["embedding"]["seed"] = seed
            seed_scores = {}
            for backend in ("embedding", "rules"):
                dest = output / f"candidate-{index}" / f"seed-{seed}" / backend
                section = "embedding" if backend == "embedding" else "anyburl"
                key = (backend, seed, str(sorted(candidate[section].items())))
                if key in cache:
                    seed_scores[backend] = cache[key]
                    records.append({"candidate": index, "seed": seed, "backend": backend,
                                    "reused_equivalent_validation_setting": True, "score": cache[key]})
                    continue
                print(f"Validation candidate {index}, seed {seed}, backend {backend}", flush=True)
                application_config = deepcopy(candidate)
                if backend == "rules":
                    application_config["anyburl"]["evidence_mode"] = "none"
                model, training = train_backend(backend, dataset.graph, application_config, dest)
                _, metrics = evaluate(model, dataset.valid, dataset.graph.entities,
                                      dataset.positives_for_filter("valid"), "valid", config.get("evaluation_limit"))
                # Both models optimized against the same metric, not incompatible MRR.
                seed_scores[backend] = metrics["hits1"]
                cache[key] = metrics["hits1"]
                records.append({"candidate": index, "seed": seed, "backend": backend,
                                "validation": metrics, "training": training})
                write_json(output / "validation_progress.json", records)
            scores.append(seed_scores)
        means.append({backend: float(np.mean([x[backend] for x in scores])) for backend in ("embedding", "rules")})
    if not means:
        raise ValueError("At least one validation candidate is required")
    selected = deepcopy(config)
    winners = {}
    for name, section in (("embedding", "embedding"), ("rules", "anyburl")):
        winner = max(range(len(means)), key=lambda i: (means[i][name], -i))
        selected[section].update(candidates[winner].get(section, {}))
        winners[name] = winner
    selected["selection"] = {"split": "valid", "metric": "Hits@1 (rules: retrieved-list proxy)",
                             "n_candidates": len(candidates), "winners": winners,
                             "validation_sha256": dataset.provenance["sha256"]["valid"],
                             "test_access": "none", "status": "fixed before test evaluation"}
    write_json(output / "validation_search.json", {"records": records, "means": means})
    write_json(output / "selected_config.json", selected)
    return selected
