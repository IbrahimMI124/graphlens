"""Paired execution and explicit A–F experiment orchestration."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json
import time
import traceback
import numpy as np
from .data import load_dataset, write_triples
from .diagnostics import GraphDiagnostics, compare_rows
from .evaluation import evaluate, queries
from .io import environment, write_json, write_csv, triple_digest
from .perturbations import sparsify, select_targets, inject_noise, audit_intervention
from .statistics import scenario_summaries, complementarity, paired_bootstrap


def assert_full_study_data(dataset):
    if dataset.provenance["excerpt"]:
        raise ValueError("Official excerpts are only for smoke checks, not comparative experiments")


def train_backend(name, graph, config, output):
    if name == "embedding":
        from .backends.embedding import EmbeddingBackend
        print(f"Initializing {config['embedding']['model']} on {config['embedding'].get('device', 'cpu')}", flush=True)
        backend = EmbeddingBackend(graph, config["embedding"])
        record = backend.fit(output)
    elif name == "rules":
        from .backends.anyburl import AnyBURLBackend, mine
        if config["anyburl"].get("pretrained_rules"):
            rules_file = Path(config["anyburl"]["pretrained_rules"]).resolve()
            record = json.loads((rules_file.parent / "training.json").read_text())
            if record["training_graph_sha256"] != triple_digest(graph.triples):
                raise ValueError("Reused rule model was trained on a different graph")
            from .io import digest
            if digest(rules_file) != record["rule_file_sha256"]:
                raise ValueError("Reused learned rule file checksum differs")
            for key in ("seconds", "max_length", "min_support", "threads", "zero_rules"):
                if record["config"].get(key) != config["anyburl"].get(key):
                    raise ValueError(f"Reused rule mining configuration differs: {key}")
            record["artifact_reused_from"] = str(rules_file)
            Path(output).mkdir(parents=True, exist_ok=True)
            write_json(Path(output) / "training.json", record)
            import shutil
            shutil.copyfile(rules_file.parent / "rules.json", Path(output) / "rules.json")
        else:
            rules_file, record = mine(graph, config["anyburl"], output)
        backend = AnyBURLBackend(graph, rules_file, config["anyburl"]["top_k"],
                                evidence_mode=config["anyburl"].get("evidence_mode", "groundings"))
    else:
        raise ValueError(name)
    return backend, record


def run_pair(dataset, config, output, intervention=None):
    """Retrain BOTH backends for every graph variant; no test-informed selection."""
    assert_full_study_data(dataset)
    audit_intervention(dataset, dataset.graph)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "running", "run_kind": config["mode"], "config": deepcopy(config),
                "dataset": dataset.provenance, "intervention": intervention,
                "training_graph_sha256": triple_digest(dataset.graph.triples), "environment": environment()}
    write_json(output / "manifest.json", manifest)
    write_triples(output / "training_edges.txt", dataset.graph.triples)
    write_json(output / "mapping.json", {"entities": dataset.graph.entities, "relations": dataset.graph.relations})
    diag = GraphDiagnostics(dataset.graph)
    patterns = diag.patterns(config.get("composition_budget", 2_000_000))
    write_json(output / "graph_statistics.json", {"n_edges": len(dataset.graph.triples),
        "n_entities": len(dataset.graph.entities), "n_active_entities": sum(d > 0 for d in diag.degree.values()),
        "degree_thresholds": diag.thresholds, "relation_statistics": diag.relation_stats})
    write_json(output / "patterns.json", patterns)
    results = {}
    summaries = {}
    try:
        rule_catalog = None
        for name in ("embedding", "rules"):
            backend, training = train_backend(name, dataset.graph, config, output / name)
            if name == "rules" and hasattr(backend, "rule_catalog"):
                rule_catalog = backend.rule_catalog
                write_json(output / name / "rule_catalog.json", rule_catalog)
            summaries[name] = {"training": training}
            for split in ("valid", "test"):
                triples = getattr(dataset, split)
                rows, summary = evaluate(backend, triples, dataset.graph.entities,
                                         dataset.positives_for_filter(split), split,
                                         config.get("evaluation_limit"), config.get("prediction_cache_size", 0),
                                         config.get("progress_every", 0))
                write_json(output / name / f"{split}_queries.json", rows)
                write_csv(output / name / f"{split}_queries.csv", rows)
                summaries[name][split] = summary
                if split == "test":
                    results[name] = rows
            if config.get("classification", True):
                from .classification import calibrate_and_evaluate
                cls_summary, cls_rows = calibrate_and_evaluate(backend, dataset)
                summaries[name]["classification"] = cls_summary
                write_csv(output / name / "classification_test.csv", cls_rows)
            write_json(output / name / "metrics.json", summaries[name])
        rows = compare_rows(results["embedding"], results["rules"], dataset.graph,
                            config.get("strong_confidence", .5), config.get("strong_support", 5), rule_catalog)
        targets = set((intervention or {}).get("targets", []))
        freq_values = [diag.frequency[r] for r in dataset.graph.relations]
        freq_thresholds = np.quantile(freq_values, [1/3, 2/3])
        for row in rows:
            row.update({"seed": config["embedding"]["seed"], "run": str(output),
                        "intervention_seed": (intervention or {}).get("seed"),
                        "known_entity_targeted": (row["tail"] if row["direction"] == "head" else row["head"]) in targets})
            freq = row["relation_frequency"]
            row["relation_frequency_group"] = "low" if freq <= freq_thresholds[0] else "medium" if freq <= freq_thresholds[1] else "high"
            row["frequency_degree_stratum"] = row["relation_frequency_group"] + "/" + row["known_degree_group"]
            if dataset.labels:
                for k in ("head", "relation", "tail"):
                    row[f"{k}_label"] = dataset.labels.get(row[k], row[k])
        if config.get("case_groundings", False) and hasattr(backend, "explain"):
            from .evaluation import ModelQuery
            seen_cases = Counter()
            for row in sorted(rows, key=lambda x: x["query_id"]):
                category = row["error_category_hits1"]
                if seen_cases[category] >= 2:
                    continue
                seen_cases[category] += 1
                query = ModelQuery(row["tail"] if row["direction"] == "head" else row["head"],
                                   row["relation"], row["direction"])
                candidates = [e for e, _ in row["rule_top_predictions"][:3]]
                evidence, _ = backend.explain([query.triple(e) for e in candidates])
                row["case_groundings"] = {e: [{**rule, "groundings": rule.get("groundings", [])[:1]}
                                               for rule in evidence.get(query.triple(e), [])[:3]] for e in candidates}
                row["case_groundings_sampling"] = "first 2 query IDs per error category; top 3 candidates, first 3 rules and first grounding each; illustrative, not exhaustive"
        write_json(output / "diagnostics.json", rows)
        write_csv(output / "diagnostics.csv", rows)
        write_json(output / "metrics.json", summaries)
        manifest["status"] = "complete"
    except BaseException as exc:
        manifest.update({"status": "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed_or_dependency_blocked", "error": str(exc),
                         "traceback": traceback.format_exc()})
        write_json(output / "manifest.json", manifest)
        raise
    write_json(output / "manifest.json", manifest)
    return rows


def plan_experiment(letter, config):
    letter = letter.upper()
    if letter not in "ABCDEF" or len(letter) != 1:
        raise ValueError("Experiment must be A, B, C, D, E, or F")
    if letter in "ACF":
        return [{"action": "analyze_existing_paired_runs", "experiment": letter,
                 "required": "diagnostics.json from matching baseline runs"}]
    variants = []
    for train_seed in config["seeds"]:
        if letter == "D":
            for length in (1, 2, 3):
                variants.append({"name": f"D-length{length}-s{train_seed}", "kind": "rule_length",
                                 "max_length": length, "training_seed": train_seed})
        else:
            for pseed in config["perturbation_seeds"]:
                if letter == "B":
                    variants.append({"name": f"B-baseline-p{pseed}-s{train_seed}", "kind": "sparsity",
                                     "retain": 1., "strategy": "random", "perturbation_seed": pseed,
                                     "training_seed": train_seed})
                    for retain in (.9, .7, .5):
                        for strategy in ("random", "local"):
                            variants.append({"name": f"B-{strategy}-{retain}-p{pseed}-s{train_seed}",
                                "kind": "sparsity", "retain": retain, "strategy": strategy,
                                "perturbation_seed": pseed, "training_seed": train_seed})
                else:
                    for fraction in (0., .01, .05, .1):
                        for strategy in (("random",) if fraction == 0 else ("random", "type_consistent")):
                            variants.append({"name": f"E-{strategy}-{fraction}-p{pseed}-s{train_seed}",
                                "kind": "noise", "fraction": fraction, "strategy": strategy,
                                "perturbation_seed": pseed, "training_seed": train_seed})
    return variants


def execute_experiment(letter, dataset, config, output, entity_types=None):
    assert_full_study_data(dataset)
    output = Path(output)
    plans = plan_experiment(letter, config)
    if letter.upper() in "ACF":
        return analyze_runs(output, letter)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / f"experiment_{letter.upper()}_plan.json", plans)
    status = []
    for plan in plans:
        cfg = deepcopy(config)
        # Controlled graph/length experiments must mine anew, including controls.
        cfg["anyburl"].pop("pretrained_rules", None)
        cfg["embedding"]["seed"] = plan["training_seed"]
        graph = dataset.graph
        metadata = dict(plan)
        if plan["kind"] == "rule_length":
            cfg["anyburl"]["max_length"] = plan["max_length"]
        else:
            pseed = plan["perturbation_seed"]
            if plan["kind"] == "sparsity":
                targets = select_targets(graph, pseed + 100_000, config.get("local_target_fraction", .1))
                graph, metadata = sparsify(graph, plan["retain"], pseed, plan["strategy"], targets)
                metadata["control"] = "random edge removal at exactly the same edge budget and seed"
            else:
                graph, metadata = inject_noise(graph, plan["fraction"], pseed, plan["strategy"], entity_types)
        original_diag = GraphDiagnostics(dataset.graph)
        changed_diag = GraphDiagnostics(graph)
        for prefix, diag in (("original", original_diag), ("changed", changed_diag)):
            metadata[f"{prefix}_graph_statistics"] = {
                "n_edges": len(diag.graph.triples), "n_entities": len(diag.graph.entities),
                "isolated_entities": sum(d == 0 for d in diag.degree.values()),
                "mean_degree": float(np.mean(list(diag.degree.values()))),
                "degree_tertiles": diag.thresholds,
                "relation_frequency": dict(diag.frequency)}
        try:
            audit_intervention(dataset, graph)
            run_pair(dataset.with_graph(graph), cfg, output / plan["name"], {**metadata, "plan": plan})
            status.append({"name": plan["name"], "status": "complete"})
        except Exception as e:
            status.append({"name": plan["name"], "status": "failed_or_blocked", "error": str(e)})
            write_json(output / "execution_status.json", status)
            raise  # Do not quietly skip failed variants and report a selected subset
        write_json(output / "execution_status.json", status)
    return status


GROUPS = {"A": ["rule_covered", "rule_evidence_kind", "rule_truth_diagnostic"],
          "B": ["known_degree_group", "target_degree_group", "known_entity_targeted"],
          "C": ["relation", "cardinality", "relation_frequency_group", "frequency_degree_stratum"],
          "D": ["rule_min_truth_length"],
          "E": ["known_degree_group"],
          "F": ["error_category_hits1", "known_degree_group", "cardinality"]}


def analyze_runs(root, letter="A"):
    paths = sorted(Path(root).rglob("diagnostics.json"))
    runs = [(p, json.loads(p.read_text())) for p in paths]
    if not runs:
        raise ValueError("No completed paired runs with diagnostics.json found")
    # Pool ONLY repeated training seeds of the same graph and hyperparameters.
    # Intervention replicates and rule lengths stay separate and keep a baseline key.
    cohorts = {}
    for path, rows in runs:
        manifest = json.loads((path.parent / "manifest.json").read_text())
        if manifest["status"] != "complete":
            continue
        config = deepcopy(manifest["config"])
        config["embedding"].pop("seed", None)
        config.pop("seeds", None)
        intervention = manifest.get("intervention")
        cohort_intervention = deepcopy(intervention)
        if cohort_intervention:
            cohort_intervention.pop("training_seed", None)
            cohort_intervention.pop("name", None)
        if cohort_intervention and "plan" in cohort_intervention:
            cohort_intervention["plan"].pop("training_seed", None)
            cohort_intervention["plan"].pop("name", None)
        key = json.dumps({"graph": manifest["training_graph_sha256"], "splits": manifest["dataset"].get("sha256"), "config": config,
                          "intervention": cohort_intervention}, sort_keys=True)
        cohorts.setdefault(key, {"rows": [], "paths": [], "manifest": manifest})
        cohorts[key]["rows"].extend(rows)
        cohorts[key]["paths"].append(str(path.parent))
    output = []
    for i, group in enumerate(cohorts.values()):
        rows = group["rows"]
        scenarios = [record for key in GROUPS[letter.upper()] for record in scenario_summaries(rows, key)]
        comp = complementarity(rows)
        output.append({"cohort": i, "runs": group["paths"], "n_queries": len(rows),
                       "intervention": group["manifest"].get("intervention"),
                       "paired_difference": paired_bootstrap(rows), "complementarity": comp,
                       "scenarios": scenarios,
                       "embedding_success_without_rule": {
                           "n_queries": sum(not r["rule_covered"] for r in rows),
                           "n_embedding_hits1": sum(r["embedding_hits1"] for r in rows if not r["rule_covered"])},
                       "interpretation": "Exploratory strata; censored rule outcomes retain retrieval status; truth-dependent strata are diagnostic only"})
    write_json(Path(root) / f"analysis_{letter.upper()}.json", output)
    write_csv(Path(root) / f"analysis_{letter.upper()}.csv", [
        {"cohort": g["cohort"], **r} for g in output for r in g["scenarios"]])
    return output
