"""Reproducible Markdown reports and exportable Matplotlib confidence plots."""
from pathlib import Path
from collections import Counter
import json
from .io import write_csv
from .experiments import analyze_runs


def markdown_table(rows, columns):
    if not rows:
        return "No observations available.\n"
    def cell(value):
        if value is None:
            return "unavailable"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "| " + " | ".join(columns) + " |\n| " + " | ".join("---" for _ in columns) + " |\n" + "".join(
        "| " + " | ".join(cell(row.get(c)) for c in columns) + " |\n" for row in rows)


def plot_differences(records, path, title, xlabel="Embedding − rule Hits@1 (paired 95% bootstrap CI)", footer=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = [r for r in records if r.get("difference") is not None]
    if not rows:
        return
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.dpi": 300})
    fig, ax = plt.subplots(figsize=(8, max(2.8, len(rows) * .4)))
    for i, r in enumerate(rows):
        ax.plot([r["ci_low"], r["ci_high"]], [i, i], color="#3568a0", linewidth=1.8)
        ax.plot(r["difference"], i, "o", color="#164577", markersize=5)
    ax.set_yticks(range(len(rows)), [f"{r.get('value', i)} (n={r['n_queries']}, seeds={r.get('n_seeds', 1)})" for i, r in enumerate(rows)])
    ax.axvline(0, color="0.5", linestyle="--", linewidth=.8)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.invert_yaxis()
    if footer:
        fig.text(.5, .01, footer, ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .07, 1, 1) if footer else None)
    fig.savefig(path)
    fig.savefig(Path(path).with_suffix(".pdf"))
    plt.close(fig)


def case_studies(rows, per_category=2):
    """Deterministic first cases, not hand-picked successes; no deployment claims."""
    selected, counts = [], Counter()
    for row in sorted(rows, key=lambda r: (r["error_category_hits1"], r["query_id"])):
        category = row["error_category_hits1"]
        if counts[category] < per_category:
            selected.append(row)
            counts[category] += 1
    return selected


def plot_relation_conditions(records, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, field, label in zip(axes, ("mean_relation_frequency", "mean_symmetry_strength"),
                               ("Training relation frequency (log scale)", "Training symmetry confirmation fraction")):
        valid = [r for r in records if r.get(field) is not None]
        for row in valid:
            ax.plot([row[field], row[field]], [row["ci_low"], row["ci_high"]], color="#9ab4cd", lw=.8, zorder=1)
            ax.scatter(row[field], row["difference"], s=12 + 3 * np.sqrt(row["n_unique_queries"]),
                       color="#285f91", alpha=.7, edgecolors="white", linewidths=.4, zorder=2)
        for index, row in enumerate(sorted(valid, key=lambda r: r["n_unique_queries"], reverse=True)[:3]):
            offset = ((8, 14), (8, 8), (8, -18))[index] if field == "mean_symmetry_strength" else (3, 4)
            ax.annotate(row["value"], (row[field], row["difference"]), xytext=offset, textcoords="offset points", fontsize=8)
        ax.axhline(0, color=".5", ls="--", lw=.7)
        ax.set_xlabel(label)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_xscale("log")
    axes[0].set_ylabel("Embedding − rule retrieved Hits@1\n(paired 95% bootstrap CI)")
    fig.suptitle("Relation conditions (exploratory associations)", fontsize=11)
    n = sum(r["n_unique_queries"] for r in records)
    seeds = max((r["n_seeds"] for r in records), default=0)
    fig.text(.5, .01, f"N={n} unique queries; {seeds} neural seeds. Point area reflects n; rule outcomes may be censored. No causal interpretation.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .96))
    fig.savefig(path, dpi=300)
    fig.savefig(Path(path).with_suffix(".pdf"))
    plt.close(fig)


def build_report(root, output=None, plots=True):
    root = Path(root)
    out = Path(output) if output else root / "report"
    out.mkdir(parents=True, exist_ok=True)
    text = ["# AID 851: embedding–rule comparison\n",
            "This report is generated from saved artifacts. Missing runs remain missing; smoke checks are not benchmark findings.\n"]
    text.append("Training budgets and selection history must be read with the results. Development/CPU-pilot runs use shorter budgets and do not establish final model-family superiority.\n")
    manifests = [(p, json.loads(p.read_text())) for p in sorted(root.rglob("manifest.json")) if out not in p.parents]
    text.append("## Execution status\n")
    for status_path in (root / "verification.json", root / "external_dependencies.json",
                        root / "backend-preflight.json", root / "resumption-2026-11-22.json",
                        root / "installation-recovery.json"):
        if status_path.exists():
            text.append(f"\nEvidence: `{status_path.name}`\n\n```json\n" +
                        json.dumps(json.loads(status_path.read_text()), indent=2) + "\n```\n")
    text.append(markdown_table([{"run": str(p.parent), "status": m["status"], "mode": m.get("run_kind"),
                                 "error": m.get("error")} for p, m in manifests], ["run", "status", "mode", "error"]))
    smoke = [json.loads(p.read_text()) for p in root.rglob("smoke.json")]
    if smoke:
        text.append("\n### Protocol smoke checks\n")
        for s in smoke:
            text.append(f"\n- {s['status']}: {s['dataset']['dataset']}; excerpt={s['dataset']['excerpt']}; "
                        f"{s['n_checked_queries']} masked queries checked. Backend execution: {s['backend_execution']}.\n")
    complete = [(p, m) for p, m in manifests if m["status"] == "complete"]
    if any(m.get("config", {}).get("anyburl", {}).get("pretrained_rules") for _, m in complete):
        text.append("\n**Fixed symbolic baseline:** saved rule models are reused across neural seeds. Bootstrap intervals estimate neural-training and query variation conditional on those rule models; rule-mining variability is not estimated. Repeated symbolic training runtimes refer to the original mining job and must not be summed as new training work.\n")
    text.append("\n## Overall baselines\n")
    baseline_rows = []
    for p, m in complete:
        metrics = json.loads((p.parent / "metrics.json").read_text())
        for name, metric in metrics.items():
            baseline_rows.append({"run": str(p.parent), "mode": m["run_kind"], "backend": name,
                                  **metric["test"], "training_seconds": metric["training"]["training_seconds"]})
    columns = ["run", "mode", "backend", "n_queries", "hits1", "hits10", "mrr_exact", "coverage",
               "covered_hits1", "hits_metric_status", "training_seconds", "inference_seconds"]
    text.append(markdown_table(baseline_rows, columns))
    write_csv(out / "baseline_comparison.csv", baseline_rows)
    text.append("\nExact MRR is shown only for complete entity rankings. Rule Hits and reciprocal-rank proxies from "
                "retrieval lists remain censored; they cannot establish full-ranking superiority. Scores are not probabilities.\n")
    text.append("\n## Scenario performance and complementarity\n")
    if complete:
        for letter in "ABCDEF":
            print(f"Generating experiment {letter} report sections", flush=True)
            groups = analyze_runs(root, letter)
            text.append(f"\n### Experiment {letter}\n")
            if letter in "BDE":
                expected_kind = {"B": "sparsity", "D": "rule_length", "E": "noise"}[letter]
                intervened = any((m.get("intervention") or {}).get("plan", {}).get("kind") == expected_kind for _, m in complete)
                if not intervened:
                    text.append("\n**Controlled intervention unexecuted.** The following strata are baseline diagnostics only; they do not measure the effect of removal, length restrictions, or noise. Hard-negative classification, when present, is reported separately below.\n")
            for group in groups:
                text.append(f"\nCohort {group['cohort']}; runs: {', '.join(group['runs'])}.\n")
                text.append(markdown_table(group["scenarios"], ["group", "value", "n_queries", "n_triples", "n_seeds", "embedding_hits1",
                            "rule_hits1", "rule_coverage", "difference", "ci_low", "ci_high", "metric_status"]))
                text.append("\nOracle complementarity (diagnostic only):\n\n" +
                            "```json\n" + json.dumps(group["complementarity"], indent=2) + "\n```\n")
                if plots:
                    if letter == "C":
                        relations = [r for r in group["scenarios"] if r["group"] == "relation"]
                        filename = f"relation-conditions-{group['cohort']}.png"
                        try:
                            plot_relation_conditions(relations, out / filename)
                            text.append(f"\n![Exploratory relation conditions]({filename})\n")
                        except ImportError:
                            pass
                    for group_key in sorted({r["group"] for r in group["scenarios"]}):
                        records = [r for r in group["scenarios"] if r["group"] == group_key]
                        filename = f"{letter}-{group['cohort']}-{group_key}.png"
                        try:
                            plot_differences(records, out / filename,
                                f"Experiment {letter}: {group_key} (exploratory; rule retrieval outcomes)")
                            text.append(f"\n![{group_key}]({filename})\n")
                        except ImportError:
                            text.append("\nPlots unavailable: install matplotlib. Numerical intervals are saved above.\n")
    else:
        text.append("\nNo paired benchmark runs completed. Experiments A–F are **unexecuted**; no claim about which model wins is justified.\n")
    text.append("\n## Robustness and hard negatives\n")
    robustness, classification = [], []
    for p, m in complete:
        metrics = json.loads((p.parent / "metrics.json").read_text())
        for name, values in metrics.items():
            if "classification" in values:
                classification.append({"run": str(p.parent), "backend": name, **values["classification"]})
            if m.get("intervention"):
                robustness.append({"run": str(p.parent), "backend": name, "intervention": json.dumps(m["intervention"]),
                                   "hits1": values["test"]["hits1"], "coverage": values["test"]["coverage"]})
    text.append(markdown_table(robustness, ["run", "backend", "hits1", "coverage", "intervention"]))
    text.append("\n" + markdown_table(classification, ["run", "backend", "n_test", "coverage", "auroc_raw",
        "average_precision_raw", "accuracy_on_covered", "overall_accuracy_uncovered_miss"]))
    write_csv(out / "robustness.csv", robustness)
    write_csv(out / "classification.csv", classification)
    from .robustness import intervention_effects
    effects = intervention_effects(root)
    text.append("\nPaired changes against matched unperturbed controls:\n\n")
    text.append(markdown_table(effects, ["intervention", "strategy", "fraction_removed_or_added", "backend", "metric",
        "difference", "ci_low", "ci_high", "n_unique_queries", "n_training_seeds", "n_perturbation_seeds"]))
    write_csv(out / "intervention_effects.csv", effects)
    if plots:
        for kind in sorted({r["intervention"] for r in effects}):
            effect_rows = [{**r, "n_seeds": r["n_training_seeds"],
                           "value": f"{r['backend']} / {r['strategy']} / {r['fraction_removed_or_added']:.0%}"}
                          for r in effects if r["intervention"] == kind and r["metric"] == "hits1"]
            try:
                plot_differences(effect_rows, out / f"effects-{kind}.png",
                                 f"{kind}: change from matched control (rule retrieval outcomes)",
                                 xlabel="Perturbed − control Hits@1 (paired 95% bootstrap CI)")
                text.append(f"\n![Paired intervention changes](effects-{kind}.png)\n")
            except ImportError:
                pass
    text.append("\n## Learned rule inventory and complexity\n")
    inventory = []
    for p, manifest in complete:
        rules_file = p.parent / "rules" / "rules.json"
        if not rules_file.exists():
            continue
        rules = json.loads(rules_file.read_text())
        for kind, length in sorted({(r["kind"], r["length"]) for r in rules}):
            items = [r for r in rules if r["kind"] == kind and r["length"] == length]
            inventory.append({"run": str(p.parent), "max_cyclic_length": manifest["config"]["anyburl"]["max_length"],
                "kind": kind, "body_length": length, "n_rules": len(items),
                "mean_raw_confidence": sum(r["confidence"] for r in items) / len(items),
                "mean_support": sum(r["support"] for r in items) / len(items)})
    text.append(markdown_table(inventory, ["run", "max_cyclic_length", "kind", "body_length", "n_rules", "mean_raw_confidence", "mean_support"]))
    write_csv(out / "rule_inventory.csv", inventory)
    from .complexity import complexity_effects
    complexity = complexity_effects(root)
    if complexity:
        text.append("\nPaired maximum-length changes against length 1 (intervals conditional on learned models):\n\n")
        text.append(markdown_table(complexity, ["max_cyclic_length", "backend", "metric", "n_queries", "n_seeds",
                                               "difference", "ci_low", "ci_high"]))
        write_csv(out / "rule_complexity_changes.csv", complexity)
    text.append("\n## Representative cases\n")
    for p, _ in complete:
        rows = json.loads((p.parent / "diagnostics.json").read_text())
        for row in case_studies(rows):
            h, r, t = (row.get(k + "_label", row[k]) for k in ("head", "relation", "tail"))
            query = f"(?, {r}, {t})" if row["direction"] == "head" else f"({h}, {r}, ?)"
            truth = h if row["direction"] == "head" else t
            text.append(f"\n### {p.parent.name} / {row['query_id']} / {row['error_category_hits1']}\n\n"
                        f"Query: `{query}`. Correct answer: `{truth}`. "
                        f"Degrees: head={row['head_degree']}, tail={row['tail_degree']}; "
                        f"relation frequency={row['relation_frequency']}; cardinality={row['cardinality']}.\n")
            evidence = {"embedding_rank": row["embedding_rank"], "embedding_top": row["embedding_top_predictions"],
                        "rule_retrieved_rank": row["rule_rank"], "rule_top": row["rule_top_predictions"],
                        "rule_truth_diagnostic": row["rule_truth_diagnostic"],
                        "rules_and_training_groundings": row.get("case_groundings", row["rule_candidate_evidence"]),
                        "groundings_sampling": row.get("case_groundings_sampling", "see evidence mode and rule_catalog.json")}
            text.append("\n```json\n" + json.dumps(evidence, indent=2) + "\n```\n")
    if not complete:
        text.append("\nPrediction examples require actual trained backends; none are invented here.\n")
    text.append("\n## Interpretation limits\n\nHead/tail outcomes share triples; paired bootstrap clusters them together and resamples "
                "training seeds when available. A single-seed interval captures query variation only. "
                "Scenario groups and frequency/degree strata are exploratory correlations. Controlled removal/noise "
                "requires retraining both models, matching evaluation queries and budgets, and reporting changed graph statistics. "
                "Truth-dependent rule categories, path-to-truth counts, and oracle outcomes are evaluation diagnostics, never selection features. "
                "See `docs/METHODOLOGY.md` for hypotheses, literature grounding, intervention controls, and unverified capabilities.\n")
    (out / "report.md").write_text("\n".join(text))
    return out / "report.md"
