"""Rule-length sweep summaries and paired changes against maximum cyclic length 1."""
from collections import Counter
from pathlib import Path
import json
import numpy as np
from .io import write_json, write_csv
from .statistics import paired_bootstrap


def complexity_effects(root):
    root = Path(root)
    runs = []
    for path in sorted(root.rglob("manifest.json")):
        manifest = json.loads(path.read_text())
        plan = (manifest.get("intervention") or {}).get("plan", {})
        if manifest["status"] == "complete" and plan.get("kind") == "rule_length":
            runs.append((path.parent, manifest, plan))
    if not runs:
        return []
    baselines = {}
    for path, manifest, plan in runs:
        if plan["max_length"] == 1:
            seed = plan["training_seed"]
            if seed in baselines:
                raise ValueError("Ambiguous length-1 controls")
            baselines[seed] = (path, manifest)
    records = []
    paired = {}
    for path, manifest, plan in runs:
        length, seed = plan["max_length"], plan["training_seed"]
        if seed not in baselines:
            raise ValueError("Missing maximum-length-1 control")
        baseline, control_manifest = baselines[seed]
        if manifest["training_graph_sha256"] != control_manifest["training_graph_sha256"] or manifest["dataset"]["sha256"] != control_manifest["dataset"]["sha256"]:
            raise ValueError("Rule-length sweep changed the graph or held-out splits")
        config, control_config = manifest["config"], control_manifest["config"]
        if config["embedding"] != control_config["embedding"]:
            raise ValueError("Neural configuration changed during rule-length sweep")
        for key in ("seconds", "threads", "top_k", "zero_rules", "min_support"):
            if config["anyburl"].get(key) != control_config["anyburl"].get(key):
                raise ValueError(f"Rule-length sweep changed another setting: {key}")
        metrics = json.loads((path / "metrics.json").read_text())
        rules = json.loads((path / "rules" / "rules.json").read_text())
        if any(r["kind"] == "relational_path" and r["length"] > length for r in rules):
            raise ValueError("Mined path rule exceeds configured cyclic body length")
        if any(r["kind"] == "constant" and r["length"] > 1 for r in rules):
            raise ValueError("Constant rule exceeded its fixed body-length limit")
        rows = json.loads((path / "diagnostics.json").read_text())
        controls = {r["query_id"]: r for r in json.loads((baseline / "diagnostics.json").read_text())}
        if {r["query_id"] for r in rows} != controls.keys():
            raise ValueError("Rule-length queries differ from control")
        for row in rows:
            base = controls[row["query_id"]]
            if any(row[k] != base[k] for k in ("head", "relation", "tail", "direction")):
                raise ValueError("Rule-length query identity mismatch")
            for backend in ("embedding", "rule"):
                for metric in ("hits1", "hits10", "covered"):
                    paired.setdefault((length, backend, metric), []).append({
                        "query_id": row["query_id"], "triple_id": row["triple_id"], "seed": seed,
                        "embedding_hits1": float(row[f"{backend}_{metric}"]),
                        "rule_hits1": float(base[f"{backend}_{metric}"])})
        for kind, body_length in sorted({(r["kind"], r["length"]) for r in rules}):
            items = [r for r in rules if r["kind"] == kind and r["length"] == body_length]
            records.append({"run": str(path), "training_seed": seed, "max_cyclic_length": length,
                "rule_kind": kind, "body_length": body_length, "n_rules": len(items),
                "body_length_counts": dict(Counter(r["length"] for r in items)),
                "median_confidence": float(np.median([r["confidence"] for r in items])),
                "median_support": float(np.median([r["support"] for r in items])),
                "training_seconds": metrics["rules"]["training"]["training_seconds"],
                "inference_seconds": metrics["rules"]["test"]["inference_seconds"],
                "n_queries": metrics["rules"]["test"]["n_queries"],
                "retrieved_hits1": metrics["rules"]["test"]["hits1"],
                "retrieved_hits10": metrics["rules"]["test"]["hits10"],
                "coverage": metrics["rules"]["test"]["coverage"],
                "covered_retrieved_hits1": metrics["rules"]["test"]["covered_hits1"],
                "mrr_exact": metrics["rules"]["test"]["mrr_exact"],
                "classification_auroc": metrics["rules"].get("classification", {}).get("auroc_raw"),
                "note": "Performance columns are whole-model outcomes, repeated by rule kind for inventory context; not isolated rule-kind effects"})
    changes = [{"max_cyclic_length": length, "backend": backend, "metric": metric,
                **paired_bootstrap(rows, repetitions=1000),
                "estimand": "configured maximum length minus maximum length 1; cyclic length only",
                "ranking_status": "symbolic outcomes may be censored; exact symbolic MRR is not inferred",
                "uncertainty_scope": "query/available training-seed bootstrap conditional on learned models; Java mining randomness not estimated"}
               for (length, backend, metric), rows in sorted(paired.items())]
    write_json(root / "rule_complexity_summary.json", {"inventory": records, "paired_changes": changes})
    write_csv(root / "rule_complexity_inventory.csv", records)
    write_csv(root / "rule_complexity_changes.csv", changes)
    return changes


def build_complexity_report(root, output, plots=True):
    from .reporting import markdown_table, plot_differences
    root, out = Path(root), Path(output)
    out.mkdir(parents=True, exist_ok=True)
    changes = complexity_effects(root)
    if not changes:
        raise ValueError("No completed controlled rule-length runs")
    inventory = json.loads((root / "rule_complexity_summary.json").read_text())["inventory"]
    whole = {}
    for row in inventory:
        run = row["run"]
        if run not in whole:
            whole[run] = {k: v for k, v in row.items() if k not in
                          ("rule_kind", "body_length", "n_rules", "body_length_counts", "median_confidence", "median_support", "note")}
            whole[run].update(n_total_rules=0, n_constant_rules=0, n_path_rules=0)
        whole[run]["n_total_rules"] += row["n_rules"]
        if row["rule_kind"] in ("constant", "relational_path"):
            whole[run]["n_constant_rules" if row["rule_kind"] == "constant" else "n_path_rules"] += row["n_rules"]
    text = ["# Experiment D: controlled cyclic rule-length pilot\n",
            "All configured lengths (1, 2, 3) are reported; test performance does not select a winning setting. "
            "Both baselines are retrained for each setting on the same original training graph and unchanged held-out splits. "
            "Neural settings are fixed from validation. Cyclic length varies; acyclic and grounded-cyclic limits stay at 1.\n",
            "## Whole-model outcomes\n",
            markdown_table(list(whole.values()), ["max_cyclic_length", "training_seed", "n_total_rules", "n_path_rules", "n_constant_rules", "n_queries", "retrieved_hits1", "retrieved_hits10", "coverage", "mrr_exact", "classification_auroc", "training_seconds", "inference_seconds"]),
            "\nSymbolic scores are native maxplus scores. Retrieved-list Hits may be censored after evaluator filtering; exact symbolic MRR remains unavailable.\n",
            "## Learned rule inventory\n",
            markdown_table(inventory, ["max_cyclic_length", "training_seed", "rule_kind", "body_length", "n_rules", "median_confidence", "median_support"]),
            "\nConfidence/support are mining statistics, not calibrated probabilities. Whole-model outcomes are not isolated rule-kind effects.\n",
            "## Paired changes from maximum length 1\n",
            markdown_table(changes, ["max_cyclic_length", "backend", "metric", "n_queries", "n_seeds", "difference", "ci_low", "ci_high"])]
    for metric in ("hits1", "hits10", "covered"):
        label = {"hits1": "retrieved Hits@1", "hits10": "retrieved Hits@10", "covered": "candidate coverage"}[metric]
        records = [{**r, "value": f"maximum length {r['max_cyclic_length']}"} for r in changes
                   if r["backend"] == "rule" and r["metric"] == metric]
        if plots:
            filename = f"paired-length-{metric}.png"
            plot_differences(records, out / filename, f"Rule-length pilot: {label} (conditional 95% intervals)",
                             xlabel=f"{label.capitalize()} change from maximum length 1",
                             footer="Intervals conditional on learned rule sets; candidate lists may be truncated.")
            text.append(f"\n![{metric} changes]({filename})\n")
    unchanged = all(r["difference"] == 0 for r in changes if r["backend"] == "embedding")
    text.append(f"\nNeural control check: all paired neural metric differences are zero: **{unchanged}**.\n")
    if len({r["n_constant_rules"] for r in whole.values()}) > 1:
        text.append("\n**Rule-inventory confounding:** constant-rule counts vary across settings even though their body-length limit stays fixed. "
                    "The learned inventories therefore differ beyond the allowed cyclic length. Independent mining repetitions or a further ablation holding the constant-rule inventory fixed are needed to separate these effects.\n")
    text.append("\n## Limits\n\nThis is a short-budget exploratory pilot. Intervals resample paired triple clusters and available neural seeds, "
                "conditional on the particular learned rule sets. With one seed they describe query variation only. "
                "Java random-seed control is not verified, and rule mining was not repeated independently. "
                "Changing allowed length also changes the learner's search at fixed wall-clock budget; differences cannot establish a pure causal benefit of longer rules. "
                "Sparsification and noise interventions are separate unexecuted experiments.\n")
    write_csv(out / "whole_model_outcomes.csv", list(whole.values()))
    write_csv(out / "rule_inventory.csv", inventory)
    write_csv(out / "paired_changes.csv", changes)
    (out / "report.md").write_text("\n".join(text))
    return out / "report.md"
