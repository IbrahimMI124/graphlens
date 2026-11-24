"""Bounded, resumable next-phase commands. Never overwrite earlier studies."""
import argparse
from collections import Counter
from pathlib import Path
import json
import gzip
import time
from ..data import load_dataset
from ..io import write_json, write_csv, digest, triple_digest
from ..evaluation import evaluate, ModelQuery
from ..backends.anyburl import mine
from ..classification import calibrate_and_evaluate
from .audit import audit
from .families import make_subsets, AuditedRules
from .curves import fit_curve, load_curve


def read(path):
    return json.loads(Path(path).read_text())


def save_rows(path, rows):
    with gzip.open(path, "wt") as f:
        json.dump(rows, f, allow_nan=False)


def load_rows(path):
    with gzip.open(path, "rt") as f:
        return json.load(f)


def neural_search(dataset, root, protocol):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    protocol_path = root / "protocol.json"
    if protocol_path.exists() and read(protocol_path) != protocol:
        raise ValueError("Cannot resume with a different search protocol")
    write_json(protocol_path, protocol)
    candidates = []
    for recipe in protocol["recipes"]:
        path = root / "search" / recipe["name"]
        record = read(path / "curve.json") if (path / "curve.json").exists() else None
        if not record or record.get("status") != "complete":
            _, record = fit_curve(dataset, recipe, path)
        candidates.append({"name": recipe["name"], "validation_mrr": record["best_validation_mrr"], "path": str(path)})
    winner = max(candidates, key=lambda r: r["validation_mrr"])
    # Freeze before the first new test scoring call. Equal validation scores use
    # pre-specified recipe order. No test value is read for selection.
    selection = {"candidates": candidates, "winner": winner, "criterion": "maximum full-validation filtered MRR",
                 "test_used_for_selection": False, "split_hashes": dataset.provenance["sha256"]}
    if (root / "selection.json").exists() and read(root / "selection.json") != selection:
        raise ValueError("A previous selection differs; use a new output directory")
    write_json(root / "selection.json", selection)
    selected = next(r for r in protocol["recipes"] if r["name"] == winner["name"])
    final = []
    for seed in protocol["final_seeds"]:
        path = root / "final" / f"seed-{seed}"
        if seed == selected["seed"]:
            model, record = load_curve(dataset.graph, winner["path"])
            path.mkdir(parents=True, exist_ok=True)
            write_json(path / "checkpoint-reference.json", {"source": winner["path"], "reason": "reuse identical selected seed; no duplicate training"})
        elif (path / "curve.json").exists() and read(path / "curve.json").get("status") == "complete":
            model, record = load_curve(dataset.graph, path)
        else:
            model, record = fit_curve(dataset, {**selected, "seed": seed}, path)
        if (path / "test-metrics.json").exists():
            metrics = read(path / "test-metrics.json")
        else:
            rows, metrics = evaluate(model, dataset.test, dataset.graph.entities, dataset.positives_for_filter("test"), cache_size=256)
            save_rows(path / "test-queries.json.gz", rows)
            write_csv(path / "test-queries.csv", [{k: v for k, v in r.items() if k not in ("candidate_evidence", "returned_candidates")} for r in rows])
            classification, classified = calibrate_and_evaluate(model, dataset)
            write_json(path / "classification.json", classification)
            write_csv(path / "classification.csv", classified)
            write_json(path / "test-metrics.json", metrics)
        final.append({"seed": seed, "metrics": metrics, "checkpoint": record["checkpoint"],
                      "best_epoch": record["best_epoch"], "validation_mrr": record["best_validation_mrr"], "training_seconds": record["training_seconds"]})
    # Strongest means validation-selected seed, never highest test outcome.
    best = max(final, key=lambda r: r["validation_mrr"])
    write_json(root / "final-summary.json", {"selection": selection, "seeds": final,
               "strongest_checkpoint_by_validation": best, "scope": "bounded development search; not a 400-epoch benchmark reproduction"})


def frozen_catalog(dataset, root, seconds=60):
    root = Path(root)
    if not (root / "mining" / "training.json").exists():
        mine(dataset.graph, {"jar": "vendor/AnyBURL-23-1x.jar", "seconds": seconds, "max_length": 3,
             "threads": 1, "heap": "2G", "min_support": 2, "zero_rules": True}, root / "mining")
    record = read(root / "mining" / "training.json")
    if record["training_graph_sha256"] != triple_digest(dataset.graph.triples):
        raise ValueError("Frozen catalog trained on a different graph")
    if not (root / "subsets" / "subsets.json").exists():
        make_subsets(record["rules_file"], root / "subsets")
    catalog = read(root / "subsets" / "catalog.json")
    write_json(root / "inventory.json", {"native_families": dict(Counter(r["native_family"] for r in catalog)),
        "body_lengths": dict(Counter(str(r["length"]) for r in catalog)), "mining": record,
        "sufficiency": "longer bounded inventory, not a verified converged rule distribution; independent inventory replication pending"})


def ablate(dataset, root, names=None, limit=None):
    root = Path(root)
    manifest = read(root / "subsets" / "subsets.json")
    subsets = manifest["subsets"]
    defaults = ["all", "constants", "general", "zero", "reflexive", "Uc", "Ud", "XXuc", "XXud",
                "constants_general"] + [f"{prefix}{length}" for prefix in ("general_le", "fixed_constants_general_le") for length in (1, 2, 3)]
    names = names or defaults
    namespace = root / ("smoke" if limit is not None else "evaluations")
    namespace.mkdir(parents=True, exist_ok=True)
    completed_by_hash = {}
    for name in names:
        sub = subsets[name]
        if digest(sub["path"]) != sub["sha256"]:
            raise ValueError("Frozen subset modified")
        path = namespace / name
        if (path / "metrics.json").exists():
            completed_by_hash[sub["sha256"]] = name
            continue
        path.mkdir(parents=True, exist_ok=True)
        if sub["sha256"] in completed_by_hash:
            write_json(path / "alias.json", {"same_subset_as": completed_by_hash[sub["sha256"]], "sha256": sub["sha256"]})
            continue
        print(f"Ablation {name}: {sub['n_rules']} frozen rules", flush=True)
        start = time.perf_counter()
        backend = AuditedRules(dataset.graph, sub["path"], certify_support=True)
        # Compare actual held-out masked queries under a larger requested topk;
        # targets never enter candidate generation. This is a contract check,
        # not a quality-tuning operation.
        wide = AuditedRules(dataset.graph, sub["path"], top_k=2 * len(dataset.graph.entities) + 1, certify_support=True)
        probe_equal = True
        for h, r, t in dataset.valid[:4]:
            for q in (ModelQuery(h, r, "tail"), ModelQuery(t, r, "head")):
                probe_equal &= backend.predict(q).candidates == wide.predict(q).candidates
        del wide
        if not probe_equal:
            backend.certify_support = False
        rows, metrics = evaluate(backend, dataset.test, dataset.graph.entities, dataset.positives_for_filter("test"),
                                 limit=limit, cache_size=256, progress_every=1000)
        save_rows(path / "queries.json.gz", rows)
        write_csv(path / "queries.csv", [{k: v for k, v in r.items() if k not in ("candidate_evidence", "returned_candidates")} for r in rows])
        metrics.update({"condition": name, "inventory_count": sub["n_rules"], "subset_sha256": sub["sha256"],
                        "native_loaded_count": backend.native_loaded_count,
                        "correct_answer_generation_coverage": sum(r["true_returned"] for r in rows) / len(rows),
                        "topk_universe_plus_1_vs_twice_universe_plus_1_equality_8_validation_queries": bool(probe_equal),
                        "effective_loader_options": backend.effective_loader_options,
                        "effective_qa_options": backend.effective_qa_options,
                        "total_application_seconds": time.perf_counter() - start,
                        "scope": "smoke, first official test triples" if limit is not None else "all official test queries",
                        "classification_score_policy": "native tail-query maxplus scalar for every subset; supports Z rules; validation calibration; zero=abstention",
                        "score_semantics": "native maxplus lexicographic; original smoothed/type-weighted confidence; no renormalization"})
        if limit is None:
            backend.reuse_masked_candidates_for_classification(
                (ModelQuery(row["head"], row["relation"], "tail"), row["returned_candidates"])
                for row in rows if row["direction"] == "tail")
            classification, classified = calibrate_and_evaluate(backend, dataset)
            classification["candidate_reuse"] = {"cached_masked_tail_queries": len(backend.classification_query_cache),
                "policy": "same-backend unfiltered raw candidates only; no gold/label/rank cache keys; validation-only calibration unchanged",
                "timing": "score call timings include cache retrieval; initial ranking inference is reported separately"}
            write_json(path / "classification.json", classification)
            write_csv(path / "classification.csv", classified)
        metrics["resource_policy"] = backend.cooling.record()
        metrics["inference_timing_note"] = "backend-call wall time includes optional cooling pauses; see resource_policy; older unpaced results are retained"
        write_json(path / "metrics.json", metrics)
        completed_by_hash[sub["sha256"]] = name


def filter_audit(dataset, root):
    """Retrospective evaluator-only sensitivity; never a selection input."""
    root = Path(root)
    selection = read(root / "selection.json")
    source = selection["winner"]["path"]
    model, record = load_curve(dataset.graph, source)
    _, stricter = evaluate(model, dataset.valid, dataset.graph.entities, dataset.positives_for_filter("valid"), "valid", cache_size=256)
    _, with_test = evaluate(model, dataset.valid, dataset.graph.entities, dataset.positives_for_filter("test"), "valid", cache_size=256)
    write_json(root / "retrospective-filter-audit.json", {"selection_sha256": digest(root / "selection.json"),
        "checkpoint": record["checkpoint"], "checkpoint_sha256": digest(record["checkpoint"]),
        "train_valid_only": stricter, "add_test_positives_evaluator_only": with_test,
        "model_selection_affected": False, "scope": "retrospective sensitivity after recipe selection; only evaluator filters receive test positives; do not use this metric for further tuning"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "curves", "mine", "ablate", "report", "cases", "filter-audit", "prepare-sparsity"))
    parser.add_argument("--data", default="data/codex-s")
    parser.add_argument("--output", default="runs/next-phase-frozen")
    parser.add_argument("--protocol", default="configs/next_phase_curves.json")
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--conditions", nargs="+")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    dataset = load_dataset(args.data)
    if args.command == "audit":
        audit(args.output)
    elif args.command == "curves":
        neural_search(dataset, args.output, read(args.protocol))
    elif args.command == "mine":
        frozen_catalog(dataset, args.output, args.seconds)
    elif args.command == "ablate":
        ablate(dataset, args.output, args.conditions, args.limit)
    elif args.command == "prepare-sparsity":
        from .sparsity import prepare
        prepare(dataset, args.output)
    elif args.command == "report":
        from .report import build
        build(dataset, args.output)
    elif args.command == "cases":
        from .cases import build_cases
        build_cases(dataset, args.output)
    elif args.command == "filter-audit":
        filter_audit(dataset, args.output)


if __name__ == "__main__":
    main()
