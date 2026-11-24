"""CLI commands deliberately separate planning from costly experiment execution."""
import argparse
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json
import sys
from .data import load_dataset, download_dataset, SPLITS
from .io import environment, write_json, write_csv


def get_dataset(args):
    return load_dataset(args.data, args.size, getattr(args, "excerpt", False))


def load_config(path):
    config = json.loads(Path(path).read_text())
    if config["mode"] not in ("development", "full"):
        raise ValueError("Config mode must be development or full")
    if config["mode"] == "full" and config.get("evaluation_limit") is not None:
        raise ValueError("Full runs cannot truncate evaluation")
    return config


def smoke(dataset, output, neural=False):
    from .evaluation import queries, FilterIndex, ModelQuery
    from .diagnostics import GraphDiagnostics
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    qlist = list(queries(dataset.test[:8]))
    filt = FilterIndex(dataset.positives_for_filter("test"))
    graph = dataset.graph
    mapped = graph.mapped()
    assert mapped.shape == (len(graph.triples), 3)
    assert len(qlist) == 2 * min(8, len(dataset.test))
    for q in qlist:
        assert q.model_input.triple(q.answer) == q.triple
        assert q.answer not in filt.alternatives(q)
        assert not hasattr(q.model_input, "answer")
    diag = GraphDiagnostics(graph)
    assert sum(diag.degree.values()) == len(graph.triples) * 2
    backend_execution = "none; loader, mapping, filtering, degrees, and masked-query checks only"
    if neural:
        from .backends.embedding import EmbeddingBackend
        cfg = {"seed": 0, "model": "ComplEx", "embedding_dim": 8, "epochs": 1,
               "batch_size": 256, "learning_rate": .01, "device": "cpu", "threads": 1, "num_negs_per_pos": 1}
        model = EmbeddingBackend(graph, cfg)
        model.fit(output / "neural_smoke")
        pred = model.predict(qlist[0].model_input)
        assert len(pred.candidates) == len(graph.entities)
        backend_execution = "one-epoch CPU ComplEx smoke; no benchmark metrics or model selection"
    record = {"status": "passed", "kind": "real-data excerpt smoke" if dataset.provenance["excerpt"] else "real-data complete-loader smoke",
              "dataset": dataset.provenance, "n_checked_queries": len(qlist),
              "backend_execution": backend_execution, "environment": environment(),
              "scientific_status": "protocol checks only; no experimental performance findings"}
    write_json(output / "smoke.json", record)
    write_csv(output / "checked_queries.csv", [{"query_id": q.query_id, "direction": q.direction,
        "head": q.triple[0], "relation": q.triple[1], "tail": q.triple[2],
        "masked_known": q.model_input.known} for q in qlist])
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description="AID 851 reproducible KGC comparisons")
    sub = parser.add_subparsers(dest="command", required=True)
    def dataset_args(p, excerpt=False):
        p.add_argument("--data", default="data/codex-s")
        p.add_argument("--size", choices=["s", "m"], default="s")
        if excerpt:
            p.add_argument("--excerpt", action="store_true", help="Only for source-provenanced smoke excerpts, never benchmark runs")
    p = sub.add_parser("download")
    dataset_args(p)
    p.add_argument("--revision", default="master")
    p.add_argument("--metadata", action="store_true")
    p.add_argument("--resume", action="store_true", help="Resume partial files at a pinned revision; verify existing files before reuse")
    p = sub.add_parser("validate")
    dataset_args(p, True)
    p.add_argument("--output", default="artifacts/validation.json")
    p = sub.add_parser("smoke")
    dataset_args(p, True)
    p.add_argument("--neural", action="store_true", help="Optional one-epoch CPU ComplEx; requires PyKEEN")
    p.add_argument("--output", default="artifacts/smoke")
    p = sub.add_parser("diagnose")
    dataset_args(p)
    p.add_argument("--output", default="artifacts/diagnostics")
    for name in ("train", "run", "tune"):
        p = sub.add_parser(name)
        dataset_args(p)
        p.add_argument("--config", default="configs/development.json")
        p.add_argument("--output", required=True)
        if name == "train":
            p.add_argument("--backend", choices=["embedding", "rules"], required=True)
        if name == "tune":
            p.add_argument("--candidates", required=True, help="JSON list of embedding/anyburl parameter overrides")
    p = sub.add_parser("experiment")
    dataset_args(p)
    p.add_argument("letter", choices=list("ABCDEF"))
    p.add_argument("--config", default="configs/development.json")
    p.add_argument("--output", required=True)
    p.add_argument("--execute", action="store_true", help="Explicitly run/retrain variants; otherwise save plan only")
    p = sub.add_parser("analyze")
    p.add_argument("letter", choices=list("ABCDEF"))
    p.add_argument("--runs", required=True)
    p = sub.add_parser("report")
    p.add_argument("--runs", default="artifacts")
    p.add_argument("--output")
    p.add_argument("--no-plots", action="store_true")
    p.add_argument("--focus", choices=["all", "rule-length"], default="all")
    p = sub.add_parser("doctor")
    p.add_argument("--output", default="artifacts/environment.json")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            import shutil
            record = {**environment(), "java": shutil.which("java"),
                      "jar_default_present": Path("vendor/AnyBURL-23-1x.jar").is_file()}
            write_json(args.output, record)
            print(json.dumps(record, indent=2))
        elif args.command == "download":
            dataset = download_dataset(args.data, args.size, args.revision, args.metadata, args.resume)
            print(json.dumps(dataset.provenance, indent=2))
        elif args.command == "validate":
            dataset = get_dataset(args)
            write_json(args.output, dataset.provenance)
            print(json.dumps(dataset.provenance, indent=2))
        elif args.command == "smoke":
            print(json.dumps(smoke(get_dataset(args), args.output, args.neural), indent=2))
        elif args.command == "diagnose":
            from .diagnostics import GraphDiagnostics
            diag = GraphDiagnostics(get_dataset(args).graph)
            patterns = diag.patterns()
            write_json(Path(args.output) / "patterns.json", patterns)
            write_json(Path(args.output) / "relations.json", diag.relation_stats)
        elif args.command == "train":
            from .experiments import train_backend
            from .evaluation import evaluate
            dataset, config = get_dataset(args), load_config(args.config)
            out = Path(args.output)
            out.mkdir(parents=True, exist_ok=False)
            model, training = train_backend(args.backend, dataset.graph, config, out)
            # Training command evaluates VALIDATION only. Testing belongs to fixed-config paired run.
            rows, metrics = evaluate(model, dataset.valid, dataset.graph.entities,
                                     dataset.positives_for_filter("valid"), "valid", config.get("evaluation_limit"))
            write_json(out / "validation.json", {"training": training, "metrics": metrics})
            write_csv(out / "validation_queries.csv", rows)
            print(json.dumps(metrics, indent=2))
        elif args.command == "run":
            from .experiments import run_pair
            dataset, config = get_dataset(args), load_config(args.config)
            for seed in config["seeds"]:
                cfg = deepcopy(config)
                cfg["embedding"]["seed"] = seed
                run_pair(dataset, cfg, Path(args.output) / f"seed-{seed}")
        elif args.command == "tune":
            from .tuning import tune
            selected = tune(get_dataset(args), load_config(args.config), json.loads(Path(args.candidates).read_text()), args.output)
            print(json.dumps(selected["selection"], indent=2))
        elif args.command == "experiment":
            from .experiments import plan_experiment, execute_experiment
            config = load_config(args.config)
            plan = plan_experiment(args.letter, config)
            write_json(Path(args.output) / f"experiment_{args.letter}_plan.json", plan)
            print(f"Saved plan: {len(plan)} entries. " + ("Executing." if args.execute else "No training launched."))
            if args.execute:
                types_file = Path(args.data) / "entity2types.json"
                types = json.loads(types_file.read_text()) if types_file.exists() else None
                execute_experiment(args.letter, get_dataset(args), config, args.output, types)
        elif args.command == "analyze":
            from .experiments import analyze_runs
            groups = analyze_runs(args.runs, args.letter)
            print(f"Saved analysis for {len(groups)} cohorts")
        elif args.command == "report":
            if args.focus == "rule-length":
                from .complexity import build_complexity_report
                print(build_complexity_report(args.runs, args.output or str(Path(args.runs) / "report"), not args.no_plots))
            else:
                from .reporting import build_report
                print(build_report(args.runs, args.output, not args.no_plots))
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"kgc: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
