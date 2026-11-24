"""Regenerate the next-phase report from executed artifacts; missing stays pending."""
from pathlib import Path
from collections import Counter, defaultdict
import json
import numpy as np
from ..io import write_json, write_csv, digest, triple_digest
from ..statistics import paired_bootstrap, complementarity, scenario_summaries
from ..diagnostics import GraphDiagnostics
from ..evaluation import queries
from .runner import read, load_rows


def condition(root, name):
    path = root / "evaluations" / name
    if name in ("B", "Z") and not (path / "metrics.json").exists():
        return condition(root, {"B": "general", "Z": "zero"}[name])
    if (path / "alias.json").exists():
        return condition(root, read(path / "alias.json")["same_subset_as"])
    if not (path / "metrics.json").exists():
        return None, None
    rows = load_rows(path / "queries.json.gz")
    metric = read(path / "metrics.json")
    if len(rows) != metric["n_queries"]:
        raise ValueError("Saved query count disagrees with completed metrics")
    # Candidate sets remain in the source compressed artifact. Keep report
    # aggregation memory bounded across the many frozen-inventory subsets.
    for row in rows:
        for key in ("returned_candidates", "candidate_evidence", "backend_metadata"):
            row.pop(key, None)
    return metric, rows


def paired(first, second, label, metric="hits1"):
    if [r["query_id"] for r in first] != [r["query_id"] for r in second]:
        raise ValueError("Ablations must use identical ordered query IDs")
    if any(any(x.get(k) != y.get(k) for k in ("triple_id", "head", "relation", "tail", "direction")) for x, y in zip(first, second)):
        raise ValueError("Ablations pair different facts under reused query IDs")
    rows = [{**a, f"embedding_{metric}": a[metric], f"rule_{metric}": b[metric]} for a, b in zip(first, second)]
    result = paired_bootstrap(rows, metric=metric, repetitions=2000)
    result["estimand"] = label
    result["scope"] = "paired query/triple uncertainty conditional on one frozen inventory; no mining replication"
    return result


def table(rows, keys):
    def fmt(x):
        if isinstance(x, float):
            return f"{x:.4f}"
        return str(x if x is not None else "n/a")
    return "| " + " | ".join(keys) + " |\n| " + " | ".join("---" for _ in keys) + " |\n" + "\n".join("| " + " | ".join(fmt(r.get(k)) for k in keys) + " |" for r in rows) + "\n"


def figures(output, neural, metrics, rows_by_name):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 220})
    if (neural / "protocol.json").exists():
        fig, ax = plt.subplots(figsize=(7, 4))
        for recipe in read(neural / "protocol.json")["recipes"]:
            path = neural / "search" / recipe["name"] / "curve.json"
            if path.exists():
                history = read(path)["history"]
                ax.plot([r["epoch"] for r in history], [r["validation"]["mrr_exact"] for r in history], marker="o", label=recipe["name"])
        ax.set(xlabel="Training epochs", ylabel="Validation filtered MRR", title="CoDEx-S: bounded validation search (one training seed)")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(output / "learning-curves.png")
        fig.savefig(output / "learning-curves.pdf")
        plt.close(fig)
    chosen = [r for r in metrics if r["condition"] in ("all", "constants", "general", "zero")]
    if chosen:
        fig, ax = plt.subplots(figsize=(8, 5))
        x = np.arange(len(chosen))
        ax.bar(x - .2, [r["coverage"] for r in chosen], .2, label="Candidate coverage")
        ax.bar(x, [r["correct_answer_generation_coverage"] for r in chosen], .2, label="Correct-answer generation")
        ax.bar(x + .2, [r["hits1"] for r in chosen], .2, label="Filtered Hits@1 (abstain=miss)")
        for offset, field, metric_field in ((-.2, "coverage", "covered"), (0, "correct_answer_generation_coverage", "true_returned"), (.2, "hits1", "hits1")):
            for i, row in enumerate(chosen):
                query_rows = rows_by_name[row["condition"]]
                groups = defaultdict(list)
                for q in query_rows:
                    groups[q["triple_id"]].append(float(q[metric_field]))
                block_means = np.array([np.mean(v) for v in groups.values()])
                rng = np.random.default_rng(2026)
                means = block_means[rng.integers(0, len(block_means), size=(1000, len(block_means)))].mean(axis=1)
                low, high = np.quantile(means, [.025, .975])
                value = row[field]
                ax.errorbar(i + offset, value, yerr=[[max(0, value-low)], [max(0, high-value)]], color="black", capsize=2, linewidth=.8)
        ax.set_xticks(x, [r["condition"] for r in chosen])
        ax.set(ylabel="Fraction of queries", ylim=(0, 1.06), title="Frozen inventory: rule-family contributions")
        for i, row in enumerate(chosen):
            ax.text(i, 1.015, f"n={row['n_queries']:,}", ha="center", fontsize=8)
        ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(.5, -.13), frameon=False)
        fig.tight_layout()
        fig.savefig(output / "family-contributions.png")
        fig.savefig(output / "family-contributions.pdf")
        plt.close(fig)
    intervals_path = output / "length-paired-intervals.json"
    if intervals_path.exists() and read(intervals_path):
        intervals = read(intervals_path)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        for ax, prefix, title in zip(axes, ("general_le", "fixed_constants_general_le"),
                                      ("General relational rules only", "With all constant implications fixed")):
            group = [r for r in intervals if r["comparison"].startswith(prefix)]
            for i, row in enumerate(group):
                value = row["difference"]
                ax.errorbar(value, i, xerr=[[value-row["ci_low"]], [row["ci_high"]-value]], fmt="o", capsize=3)
            ax.axvline(0, color="grey", linewidth=.8)
            ax.set_yticks(range(len(group)), [r["comparison"].replace(prefix, "").replace(" minus ", " vs ") for r in group])
            ax.set(xlabel="Change in filtered Hits@1 (95% paired CI)", ylabel="Maximum body-length contrast", title=title)
            ax.margins(y=.25)
        fig.suptitle("One frozen catalog; 1,828 paired test-triple clusters", fontsize=10)
        fig.tight_layout()
        fig.savefig(output / "length-effects.png")
        fig.savefig(output / "length-effects.pdf")
        plt.close(fig)


def build(dataset, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    root, neural = Path("runs/next-phase-frozen"), Path("runs/next-phase-neural")
    manifest = read(root / "subsets" / "subsets.json")
    expected_queries = [(q.query_id, *q.triple, q.direction) for q in queries(dataset.test)]
    metrics, rows_by_name, classification = [], {}, []
    for name in manifest["subsets"]:
        metric, rows = condition(root, name)
        if metric is None:
            continue
        if [(r["query_id"], r["head"], r["relation"], r["tail"], r["direction"]) for r in rows] != expected_queries:
            raise ValueError("Ablation does not match the complete official test query sequence")
        metrics.append({**metric, "condition": name, "inventory_count": manifest["subsets"][name]["n_rules"],
                        "hits_metric_status": "certified supported-candidate Hits; abstain=miss" if all(r["hits_certified"] for r in rows) else metric["hits_metric_status"]})
        rows_by_name[name] = rows
        path = root / "evaluations" / name
        if (path / "alias.json").exists():
            path = root / "evaluations" / read(path / "alias.json")["same_subset_as"]
        if (path / "classification.json").exists():
            classification.append({"condition": name, **read(path / "classification.json")})
    write_csv(output / "rule-family-metrics.csv", metrics)
    write_csv(output / "classification-metrics.csv", classification)
    differences = []
    changed = []
    for prefix in ("general_le", "fixed_constants_general_le"):
        for cap, reference in ((2, 1), (3, 1), (3, 2)):
            a, b = f"{prefix}{cap}", f"{prefix}{reference}"
            if a not in rows_by_name or b not in rows_by_name:
                continue
            top10 = paired(rows_by_name[a], rows_by_name[b], f"{a} minus {b} Hits@10", metric="hits10")
            differences.append({"comparison": f"{a} minus {b}", **paired(rows_by_name[a], rows_by_name[b], f"{a} minus {b} Hits@1"),
                "difference_hits10": top10["difference"], "ci_low_hits10": top10["ci_low"], "ci_high_hits10": top10["ci_high"],
                "n_hits1_gains": sum(x["hits1"] > y["hits1"] for x, y in zip(rows_by_name[a], rows_by_name[b])),
                "n_hits1_losses": sum(x["hits1"] < y["hits1"] for x, y in zip(rows_by_name[a], rows_by_name[b])),
                "n_hits10_gains": sum(x["hits10"] > y["hits10"] for x, y in zip(rows_by_name[a], rows_by_name[b])),
                "n_hits10_losses": sum(x["hits10"] < y["hits10"] for x, y in zip(rows_by_name[a], rows_by_name[b]))})
            for x, y in zip(rows_by_name[a], rows_by_name[b]):
                if x["top_predictions"][:1] != y["top_predictions"][:1] or any(x[k] != y[k] for k in ("rank", "hits1", "hits10", "covered", "true_returned")):
                    changed.append({"comparison": f"{a} vs {b}", "query_id": x["query_id"], "head": x["head"],
                        "relation": x["relation"], "tail": x["tail"], "direction": x["direction"],
                        "new_hits1": x["hits1"], "old_hits1": y["hits1"], "new_rank": x["rank"], "old_rank": y["rank"],
                        "new_hits10": x["hits10"], "old_hits10": y["hits10"],
                        "new_true_generated": x["true_returned"], "old_true_generated": y["true_returned"],
                        "top_entity_changed": [e for e, _ in x["top_predictions"][:1]] != [e for e, _ in y["top_predictions"][:1]],
                        "new_top": x["top_predictions"][:1], "old_top": y["top_predictions"][:1]})
    write_json(output / "length-paired-intervals.json", differences)
    write_csv(output / "changed-predictions.csv", changed)
    family_differences = []
    for first, second in (("constants_general", "constants"), ("constants_general", "general"),
                          ("all", "constants_general"), ("constants", "general")):
        if first not in rows_by_name or second not in rows_by_name:
            continue
        a, b = rows_by_name[first], rows_by_name[second]
        family_differences.append({"comparison": f"{first} minus {second}",
            **paired(a, b, f"{first} minus {second} Hits@1"),
            "n_query_gains": sum(x["hits1"] > y["hits1"] for x, y in zip(a, b)),
            "n_query_losses": sum(x["hits1"] < y["hits1"] for x, y in zip(a, b)),
            "n_top_entity_changes": sum([e for e, _ in x["top_predictions"][:1]] != [e for e, _ in y["top_predictions"][:1]] for x, y in zip(a, b))})
    write_json(output / "family-paired-intervals.json", family_differences)
    overlap = None
    if all(n in rows_by_name for n in ("constants", "general")):
        c, g = rows_by_name["constants"], rows_by_name["general"]
        overlap = complementarity([{**a, "embedding_hits1": a["hits1"], "rule_hits1": b["hits1"],
                    "rule_hits_certified": b["hits_certified"]} for a, b in zip(c, g)])
        overlap["labels"] = {"embedding": "constant-bearing implications", "rules": "general variable-only relational"}
        overlap["interpretation"] = "unique standalone successes within these two subsets, not additive credit in their maxplus union"
        # Candidate-set overlap uses answer-blind, pre-filter output sets.
        raw_c = load_rows(root / "evaluations/constants/queries.json.gz")
        raw_g = load_rows(root / "evaluations/general/queries.json.gz")
        overlaps = []
        for a, b in zip(raw_c, raw_g):
            if a["query_id"] != b["query_id"]:
                raise ValueError("Overlap query mismatch")
            sa = {e for e, _ in a["returned_candidates"]}
            sb = {e for e, _ in b["returned_candidates"]}
            overlaps.append(len(sa & sb) / len(sa | sb) if sa | sb else 1.)
        overlap["mean_candidate_jaccard_including_empty_both_as_one"] = float(np.mean(overlaps))
        overlap["n_unique_queries"] = len(overlaps)
        del raw_c, raw_g
        write_json(output / "constant-general-overlap.json", overlap)
    comparison = []
    if (neural / "final-summary.json").exists():
        final = read(neural / "final-summary.json")
        strongest = final["strongest_checkpoint_by_validation"]
        checkpoint = Path(strongest["checkpoint"])
        training = read(checkpoint.parent / "curve.json")
        write_json(output / "strongest-complex.json", {"selection": "highest validation MRR among the selected recipe's planned seeds; never test",
            "checkpoint": str(checkpoint), "checkpoint_sha256": digest(checkpoint),
            "validation_mrr": strongest["validation_mrr"], "seed": strongest["seed"], "best_epoch": strongest["best_epoch"],
            "config": training["config"], "learned_model": training["learned_model"],
            "entities": list(dataset.graph.entities), "relations": list(dataset.graph.relations),
            "training_graph_sha256": triple_digest(dataset.graph.triples), "source_split_hashes": dataset.provenance["sha256"],
            "batch_unit": "directional training examples; original plus explicit inverse examples, shuffled together",
            "directional_examples_per_epoch": len(dataset.graph.triples) * (2 if training["config"].get("reciprocal") else 1),
            "optimizer_steps_per_full_epoch": int(np.ceil(len(dataset.graph.triples) * (2 if training["config"].get("reciprocal") else 1) / training["config"]["batch_size"])),
            "load_command": "from kgc.research.curves import load_curve; model, metadata = load_curve(dataset.graph, checkpoint.parent)",
            "mapping_provenance": "canonical sorted training-only vocabulary verified by loader; explicit inverse offset = number of original relations"})
        diag = GraphDiagnostics(dataset.graph)
        # Reuse the already computed training-only patterns after checking their
        # graph provenance; avoid repeating a large composition enumeration.
        previous = Path("runs/codex-s-cpu-pilot-refined/seed-0")
        if (previous / "graph_statistics.json").exists():
            if read(previous / "manifest.json")["training_graph_sha256"] != triple_digest(dataset.graph.triples):
                raise ValueError("Cached pattern statistics belong to another graph")
            cached_statistics = read(previous / "graph_statistics.json")["relation_statistics"]
            for relation, values in cached_statistics.items():
                if values["relation_frequency"] != diag.relation_stats[relation]["relation_frequency"]:
                    raise ValueError("Cached relation frequencies disagree")
                diag.relation_stats[relation].update(values)
            write_json(output / "pattern-feature-provenance.json", {"source": str(previous / "graph_statistics.json"),
                "source_sha256": digest(previous / "graph_statistics.json"), "training_graph_sha256": triple_digest(dataset.graph.triples),
                "policy": "training-only cached graph statistics; hash/frequency checks; no test outcomes in features"})
        frequency_thresholds = np.quantile([diag.frequency[r] for r in dataset.graph.relations], [1/3, 2/3])
        write_json(output / "scenario-thresholds.json", {"degree_tertiles_over_training_entities": diag.thresholds,
            "relation_frequency_tertiles_over_training_relations": frequency_thresholds.tolist(),
            "group_rule": "low <= first cutoff; medium <= second cutoff; high otherwise; cutoffs never use held-out outcomes"})
        write_csv(output / "training-relation-properties.csv", [{"relation": r, **s} for r, s in diag.relation_stats.items()])
        for seed_record in final["seeds"]:
            sid = seed_record["seed"]
            classification.append({"condition": f"ComplEx seed-{sid}", **read(neural / "final" / f"seed-{sid}" / "classification.json")})
            embed = load_rows(neural / "final" / f"seed-{sid}" / "test-queries.json.gz")
            for family in ("all", "general", "constants"):
                if family not in rows_by_name:
                    continue
                if len(embed) != len(rows_by_name[family]):
                    raise ValueError("Neural/rule query counts differ")
                for e, r in zip(embed, rows_by_name[family]):
                    if any(e[k] != r[k] for k in ("query_id", "triple_id", "head", "relation", "tail", "direction")):
                        raise ValueError("Neural/rule queries differ")
                    frequency = diag.frequency[e["relation"]]
                    frequency_group = "low" if frequency <= frequency_thresholds[0] else "medium" if frequency <= frequency_thresholds[1] else "high"
                    features = diag.query_features(e)
                    comparison.append({"seed": sid, "rule_subset": family, "query_id": e["query_id"], "triple_id": e["triple_id"],
                        "head": e["head"], "relation": e["relation"], "tail": e["tail"], "direction": e["direction"],
                        "embedding_hits1": e["hits1"], "embedding_hits10": e["hits10"], "embedding_rank": e["rank"],
                        "embedding_score": e["score"], "rule_hits1": r["hits1"], "rule_hits10": r["hits10"], "rule_rank": r["rank"],
                        "rule_score": r["score"], "rule_covered": r["covered"], "rule_true_generated": r["true_returned"],
                        "rule_hits_certified": r["hits_certified"],
                        "error_category": ("both_correct" if e["hits1"] and r["hits1"] else "only_embeddings" if e["hits1"] else "only_rules" if r["hits1"] else "both_incorrect"),
                        "rule_truth_diagnostic": ("rule_generates_truth" if r["true_returned"] else "no_supported_candidates" if not r["covered"] else "rules_generate_candidates_but_omit_truth" if r["hits_certified"] else "truth_not_returned_support_unknown"),
                        "relation_frequency_group": frequency_group,
                        "frequency_x_known_degree": frequency_group + " / " + features["known_degree_group"],
                        **features})
        write_csv(output / "neural-rule-diagnostics.csv", comparison)
        aggregate = {}
        complementary_features = []
        for family in ("all", "general", "constants"):
            group = [r for r in comparison if r["rule_subset"] == family]
            if group:
                aggregate[family] = {"difference": paired_bootstrap(group), "complementarity": complementarity(group),
                    "known_degree_scenarios": scenario_summaries(group, "known_degree_group"),
                    "cardinality_scenarios": scenario_summaries(group, "cardinality"),
                    "relation_frequency_scenarios": scenario_summaries(group, "relation_frequency_group"),
                    "frequency_degree_strata": scenario_summaries(group, "frequency_x_known_degree"),
                    "relation_specific": scenario_summaries(group, "relation")}
                for category in ("both_correct", "only_embeddings", "only_rules", "both_incorrect"):
                    selected_rows = [r for r in group if r["error_category"] == category]
                    complementary_features.append({"rule_subset": family, "error_category": category,
                        "n_observations": len(selected_rows), "n_unique_directional_queries": len({r["query_id"] for r in selected_rows}),
                        "n_triples": len({r["triple_id"] for r in selected_rows}), "n_neural_seeds": len({r["seed"] for r in selected_rows}),
                        **{f"mean_{key}": float(np.mean([r[key] for r in selected_rows])) if selected_rows else None
                           for key in ("head_degree", "tail_degree", "relation_frequency", "symmetry_strength", "directed_twohop_paths_to_truth")},
                        "interpretation": "exploratory associations; memberships vary by neural seed; target/path features require the answer; no causal identification"})
        write_json(output / "neural-rule-comparison.json", aggregate)
        write_csv(output / "complementary-success-properties.csv", complementary_features)
        write_csv(output / "scenario-diagnostics.csv", [{"rule_subset": family, "scenario": scenario, **row}
            for family, values in aggregate.items()
            for scenario in ("known_degree_scenarios", "cardinality_scenarios", "relation_frequency_scenarios", "frequency_degree_strata", "relation_specific")
            for row in values[scenario]])
    else:
        final, aggregate = None, {}
    figures(output, neural, metrics, rows_by_name)
    write_csv(output / "classification-metrics.csv", classification)
    inventory = read(root / "inventory.json")
    grouped_inventory = defaultdict(list)
    for rule in read(root / "subsets/catalog.json"):
        grouped_inventory[(rule["native_family"], rule["length"])].append(rule)
    inventory_statistics = [{"family": family, "body_length": length, "n_rules": len(rules),
        "mean_raw_confidence": float(np.mean([r["confidence"] for r in rules])),
        "median_raw_confidence": float(np.median([r["confidence"] for r in rules])),
        "mean_support": float(np.mean([r["support"] for r in rules])),
        "median_support": float(np.median([r["support"] for r in rules]))}
        for (family, length), rules in sorted(grouped_inventory.items())]
    del grouped_inventory
    write_csv(output / "inventory-confidence-support.csv", inventory_statistics)
    text = """# AID 851 — audited embedding–rule comparison, next phase

This report is regenerated from saved outputs. Earlier pilot reports and checkpoints remain unchanged. The new studies are bounded development experiments, not a final benchmark reproduction. No hybrid or GAT work was added.

## Audit and corrected interpretation

The six completed prior runs have matching official file hashes, entity/relation maps and candidate universes. Models receive training positives and masked queries only. Validation filtering uses train+validation; final test filtering uses train+validation+test. Verified negatives are excluded from graph edges and ranking filters. Average-score neural tie ranks and native maxplus rule ordering remain distinct policies.

The executable audit is in `audit/audit.json`. PyClause applies smoothing and family weights: with 10 correct out of 20 predictions, raw confidence 0.5 becomes 0.4 for B/Uc, 0.04 for Ud and 0.004 for Z under the installed defaults. Scores are not probabilities. Maxplus uses a lexicographic sequence of supporting rule confidences; re-sorting by the first scalar score changes ranking semantics.

One native rule returned 150 supported candidates despite topk=10, but that overrun did NOT establish completeness. A two-rule counterexample returned only the first rule's candidates, and real queries returned different supports at K=100/1000. New runs explicitly set K above the entire entity universe (2,035 here), disable pruning/stopping, and compare against K=4,069 on eight masked validation queries. This changes retrieval completeness, not rule confidence or maxplus semantics. Certified Hits describe this exhaustive **loaded-rule candidate ranking with abstentions counted as misses**; they are not a ranking of unsupported zero-score entities. Exact full-universe rule MRR remains null. Old retrieved-list/censored labels are correct and are preserved. The preliminary inference from the single-rule probe was rejected and its correction retained.

Reflexive XX-family QA output disagreed with native triple scoring in executable synthetic probes; the failure depended on preceding native calls. Both synthetic observations are retained in the regression log. Completeness certification is disabled for inventories containing these families. This frozen catalog contains none. Z rules cannot use native PredictionHandler classification, so every NEW subset uses the same tail-query maxplus scalar for classification; calibration and threshold fitting remain validation-only. This versioned score policy is explicit and leaves legacy scores untouched.

Legacy `rule_covered` means nonempty pre-filter candidates, not correct-answer support. Legacy `relational_path` includes any variable-only syntax, not just native B rules; `mixed` means multiple coarse kinds appear among evidence for returned candidates. New subsets distinguish B, Uc, Ud, reflexive families and Z. Constant-bearing implications have nonempty bodies and are not unconditional entity-frequency priors. Every subset retains the native training-frequency tie policy: general-only removes constant implications and Z rules, but does not remove this implicit frequency-based tie breaker. Serialized text cannot establish grounded-cyclic mining provenance: structural proxies are cataloged separately and are not relabeled mining families.

Truth-generation, strong support for truth, target degree, paths to truth, error categories and the oracle require the held-out answer. They are diagnostic labels only. Paired uncertainty clusters both directions by original test triple and resamples neural training seeds. Repeating a fixed symbolic model across neural seeds does not create independent rule-mining replicates. Shared entities, relations and repeated masked inputs across different triples remain dependent; the triple bootstrap is a conditional benchmark uncertainty estimate, not a model of all graph dependence.

The query-level two-hop diagnostic counts distinct intermediate entities with relation labels collapsed. It is not a count of all typed paths. Training-only typed relation-composition statistics and native rule groundings are provided separately. Empty-inventory families are availability diagnostics, not estimates of trained-family quality.

## ComplEx training and selection

The [official CoDEx configuration](https://github.com/tsafavi/codex/blob/master/models/link-prediction/codex-s/complex/config.yaml) uses reciprocal relations, per-triple 1vsAll, a 512-real-coordinate representation, dropout, Adam at approximately 0.000339, a plateau scheduler and up to 400 epochs. Its regularization selector is empty despite stored regularization weights. The pilot used 128 complex coordinates, 2-negative sLCWA/Softplus, no reciprocals, PyKEEN's default regularizer, Adam 0.01 and ten epochs. These multiple changes prevent attributing the gap solely to epoch count.

The new recipe uses 256 PyKEEN complex coordinates, explicit inverse IDs and per-triple cross entropy against all original entities. PyKEEN grouped LCWA is not assumed equivalent to LibKGE per-triple 1vsAll. Training scores are tested against PyKEEN's ComplEx interaction. This is a documented port, not bitwise reproduction: real/imaginary dropout/initializer implementation, batch ordering/loss scaling and validation frequency differ. The [CoDEx paper, Tables 5 and 11](https://aclanthology.org/2020.emnlp-main.669.pdf) confirms CE, no regularization, reciprocals and reference MRR/Hits@1/Hits@10 of 0.465/0.372/0.646. These reference values are not measured here. The [setup script](https://github.com/tsafavi/codex/blob/master/libkge_setup.sh) pins historic LibKGE `a9ecd249ec2d205df59287f64553a1536add4a43`; its files could not be fetched. [Current defaults](https://github.com/uma-pi1/kge/blob/master/kge/config-default.yaml) expose extra test-filtered validation metrics and rounded mean tie ranks. Our validation excludes test filtering and uses unrounded realistic ties. Historic inherited defaults remain unverified.

The protocol `configs/next_phase_curves.json` fixes three recipes and a maximum of forty epochs. One real-data one-epoch CPU smoke preceded it and accessed validation only. The search uses full-validation filtered MRR; selection is saved before new test scoring. The selected recipe uses three seeds and per-seed validation checkpoint selection. The strongest saved checkpoint is chosen by validation, never by test score. Schedules/early stopping count validation checks, so they do not reproduce a 400-epoch schedule.

There are four validation checkpoints (epochs 5/10/20/40). Scheduler patience is seven checks, so no learning-rate decay was triggered within these runs. The epoch ceiling, rather than demonstrated convergence, limits the selected recipe. Checkpoint improvements use a fixed 0.0001 margin, retaining the earlier checkpoint for smaller changes. Objective, reciprocals, dimensionality, regularization, dropout and initialization change together across the sLCWA/CE recipes; isolating their individual mechanisms requires further controlled ablations.

Our batch size 1,024 counts directional examples in the augmented train set (65 optimizer steps per full epoch). LibKGE's paired 1vsAll batch counts 1,024 original triples and evaluates both directions per step (33 steps for this training split). Each epoch covers both directions in either setup, but gradient grouping, update count and loss scaling differ. Thus forty epochs here are not an exactly matched optimizer/computation budget or a bitwise reproduction of the published training loop.

"""
    if final:
        text += "Selected recipe: `" + final["selection"]["winner"]["name"] + "`.\n\n"
        text += table([{"seed": r["seed"], "best_epoch": r["best_epoch"], "validation_MRR": r["validation_mrr"], "training_seconds": r["training_seconds"], **r["metrics"]} for r in final["seeds"]],
                      ["seed", "best_epoch", "validation_MRR", "mrr_exact", "hits1", "hits10", "n_queries", "training_seconds", "inference_seconds"])
        means = {k: float(np.mean([r["metrics"][k] for r in final["seeds"]])) for k in ("mrr_exact", "hits1", "hits10")}
        checkpoint_info = final["strongest_checkpoint_by_validation"]
        text += "\nStrongest checkpoint by validation: `" + checkpoint_info["checkpoint"] + "`; seed " + str(checkpoint_info["seed"]) + ", epoch " + str(checkpoint_info["best_epoch"]) + ". Hash, full configuration, original ID maps and load instructions are in `strongest-complex.json`.\n"
        text += f"\nDirect observation: selected-recipe test means are MRR {means['mrr_exact']:.4f}, Hits@1 {means['hits1']:.4f}, Hits@10 {means['hits10']:.4f}. Compare the old pilot mean MRR 0.2046 with these bounded, differently configured runs cautiously. The same-recipe sLCWA learning curve tests extra training; the recipe search changes several factors together. A higher score does not isolate which change caused improvement.\n\n"
    else:
        text += "Final neural runs remain pending; partial validation curves are shown without inventing final test results.\n\n"
    text += "![Validation learning curves](learning-curves.png)\n\n## Frozen rule-family and length ablations\n\n"
    if (neural / "retrospective-filter-audit.json").exists():
        sensitivity = read(neural / "retrospective-filter-audit.json")
        text += f"Retrospective evaluator-only filtering sensitivity for the already-selected seed-0 checkpoint: validation MRR {sensitivity['train_valid_only']['mrr_exact']:.4f} with train+validation filters, versus {sensitivity['add_test_positives_evaluator_only']['mrr_exact']:.4f} when test positives additionally filter alternative answers. The latter metric did not select recipes/checkpoints and is not a new tuning target. It quantifies a protocol difference without giving test triples to the model.\n\n"
    text += "One 60-second native mining run produced " + str(sum(inventory["native_families"].values())) + " rules: `" + json.dumps(inventory["native_families"]) + "`. This exceeds the earlier ten-second budget but does not establish mining convergence. Only one learned inventory was sampled; independent mining stability remains unresolved. Native min-confidence/loading filters can further reduce effective inventories; both file and loaded counts are saved.\n\n"
    text += table(metrics, ["condition", "inventory_count", "native_loaded_count", "n_queries", "coverage", "correct_answer_generation_coverage", "hits1", "hits10", "inference_seconds", "hits_metric_status"])
    text += "\nRule inventory confidence/support (raw mining statistics, not calibrated or type-adjusted scores):\n\n" + table(inventory_statistics, ["family", "body_length", "n_rules", "mean_raw_confidence", "median_raw_confidence", "mean_support", "median_support"])
    text += "\n![Rule-family contributions](family-contributions.png)\n\nThe all-rules, constant-only, general-only, union and supported other-family conditions use identical official queries. Empty families have zero candidate coverage. Native smoothing, weights, maxplus aggregation and tie policy remain unchanged; there is no category-specific retuning or score normalization. Inventories and original-line indices are frozen and hashed.\n\n"
    text += table(family_differences, ["comparison", "difference", "ci_low", "ci_high", "n_query_gains", "n_query_losses", "n_top_entity_changes"])
    text += "\nAdding general rules to fixed constants, adding constants to fixed general rules, and adding zero rules to their union are separate controlled subset interventions. Gains and losses count directional query outcomes, not independent graph samples. They measure net ranking effects under the original maxplus policy, rather than assigning additive credit to the winning rule family.\n\n"
    if overlap:
        counts = overlap["counts"]
        text += f"Standalone Hits@1 successes: both subsets correct {counts['both_correct']}; only constant implications correct {counts['only_embeddings']}; only general relational rules correct {counts['only_rules']}; neither correct {counts['both_incorrect']}. These unique successes are relative to the other standalone subset, not additive causal credit in the combined maxplus ranking. Candidate-set Jaccard averaged {overlap['mean_candidate_jaccard_including_empty_both_as_one']:.4f}.\n\n"
    text += table(classification, ["condition", "n_test", "coverage", "auroc_raw", "average_precision_raw", "accuracy_on_covered", "overall_accuracy_uncovered_miss"])
    text += "\nRanking uses 3,656 directional observations from 1,828 positive facts. Classification instead scores 1,828 positives plus 1,828 verified negatives once each. Neural classification averages forward/inverse raw scores; every rule subset uses the native tail-query maxplus scalar. Each backend is calibrated separately on validation. These conventions do not numerically reproduce CoDEx's relation-specific classification thresholds. Hard-negative AUROC/AP include documented zero scores for unsupported cases; these are abstentions, not learned negative judgments. Covered accuracy and total accuracy remain separate.\n\n"
    text += table(differences, ["comparison", "difference", "ci_low", "ci_high", "n_queries", "n_triples", "n_seeds"])
    text += "\nDirectional query gains/losses (paired by original fact for uncertainty):\n\n" + table(differences, ["comparison", "n_hits1_gains", "n_hits1_losses", "n_hits10_gains", "n_hits10_losses"])
    text += "\nSecondary Hits@10 differences for the same paired triple bootstrap:\n\n" + table(differences, ["comparison", "difference_hits10", "ci_low_hits10", "ci_high_hits10"])
    text += "\n![Paired length effects](length-effects.png)\n\nFamily-plot error bars and length-effect intervals use paired triple-cluster bootstrap uncertainty conditional on one learned rule inventory. They do not quantify mining instability.\n\n"
    text += "\nThese are controlled **inference-time subset interventions**: no re-mining occurs between caps; every constant-bearing nonzero rule is held fixed across the fixed-constant length conditions. Rules are reapplied and scores recomputed for each subset. Intervals pair head/tail within 1,828 triples and condition on the one frozen catalog. Changed predictions, including losses as well as gains, are saved in `changed-predictions.csv`. This does not establish the effect of changing a mining length parameter or the stability of another mined inventory. The previous remine sweep remains exploratory and confounded by changing constant inventories.\n\n"
    text += "## Complementarity, mechanisms and remaining evidence\n\n"
    for name, result in aggregate.items():
        text += f"Against `{name}`: neural-minus-rule Hits@1 difference {result['difference']['difference']:.4f}, paired 95% interval [{result['difference']['ci_low']:.4f}, {result['difference']['ci_high']:.4f}], {result['difference']['n_unique_queries']} unique queries × {result['difference']['n_seeds']} neural seeds. Oracle union {result['complementarity']['oracle_union_success']:.4f} is diagnostic only.\n\n"
    if aggregate:
        text += "### Structural and relational scenarios\n\nThe following exploratory means average the three neural seeds against one fixed rule inventory. Sample sizes count unique directional queries and original test facts, not the duplicated seed observations. Degree tertiles are computed across training entities, and frequency tertiles across training relations; their query groups therefore have unequal sizes.\n\n"
        degree_rows = [{"rule_subset": family, **row} for family in ("all", "general", "constants") for row in aggregate.get(family, {}).get("known_degree_scenarios", [])]
        text += table(degree_rows, ["rule_subset", "value", "n_unique_queries", "n_triples", "embedding_hits1", "rule_hits1", "difference", "ci_low", "ci_high"])
        for label, scenario in (("Relation-frequency groups, all rules", "relation_frequency_scenarios"), ("Relation cardinality, all rules", "cardinality_scenarios")):
            text += "\n" + label + ":\n\n" + table(aggregate.get("all", {}).get(scenario, []),
                ["value", "n_unique_queries", "n_triples", "embedding_hits1", "rule_hits1", "difference", "ci_low", "ci_high"])
        if aggregate.get("all"):
            degrees = {r["value"]: r for r in aggregate["all"]["known_degree_scenarios"]}
            medium, high = degrees.get("medium"), degrees.get("high")
            if medium and high:
                text += f"\nDirect observation: on medium-known-degree queries the neural-minus-all-rules difference is {medium['difference']:+.4f} [{medium['ci_low']:+.4f}, {medium['ci_high']:+.4f}], compared with {high['difference']:+.4f} [{high['ci_low']:+.4f}, {high['ci_high']:+.4f}] on high-degree queries. This is an association under the recorded budgets, not an intervention on degree.\n\n"
        text += "Tiny cardinality/frequency groups cannot establish a general rule-family advantage; a degenerate bootstrap interval in a one-fact group is not population-level certainty. Frequency-by-known-degree strata, all relation-specific outcomes, and train-only symmetry/inverse/subsumption/composition measures are provided in `scenario-diagnostics.csv` and `training-relation-properties.csv`. These descriptive controls do not remove all confounding, and intervals are exploratory rather than multiple-comparison-adjusted hypothesis tests.\n\n"
    text += "Query-level joins, degree/cardinality scenario sample sizes, seed/triple intervals and category counts are in `neural-rule-diagnostics.csv` and `neural-rule-comparison.json`. General-rule-only successes and embedding-only successes identify cases for explanation, not a deployable selector. Representative training-checked groundings and rankings, when generated, are in `case-studies.json` and `cases.md`.\n\n"
    text += "After a user-requested pause for laptop heat, the interrupted seed-2 run was archived and restarted from the same seed/configuration, because optimizer/RNG state was not checkpointed. This was not a warm continuation or a new validation search. Completed seeds and rule conditions were retained. Resumed work uses one CPU process/thread and explicit cooling breaks; resource metadata records them. Native inference wall time may include these breaks, and classification may reuse answer-blind raw candidate outputs. Timing differences across paced/unpaced or cached/uncached runs do not by themselves measure algorithmic speed.\n\n"
    text += """| Research question | Current evidential status | Interpretation / next requirement |
| --- | --- | --- |
| Was the pilot undertrained? | Validation curves and bounded recipe comparison executed where shown above | Extra epochs and recipe quality are different explanations; rising curves do not prove convergence or isolate a single cause. |
| Do constant implications explain rule success? | Frozen family-subset interventions, counts and overlap above | Quantifies standalone and combined contributions conditional on one catalog; counts alone are not evidence of importance. |
| Does longer relational evidence help? | Fixed-inventory length interventions above | Tests inference-time availability with identical constants, not a change in mining search; independent catalogs pending. |
| What do general rules predict that embeddings miss, and vice versa? | Paired seed/query complementarity and structural diagnostics where present | Descriptive complementary cases; degree, frequency and relation properties may confound associations. |
| Does sparsity/connectivity explain the differences? | Training graphs and matched relation-count controls prepared | Retrain both systems on each graph before claiming an intervention effect; no perturbed-model result is asserted. |
| Do symmetry/inverse/subsumption/composition/cardinality predict reliability? | Train-only descriptive statistics and earlier pilot associations | Multivariable or matched interventions remain necessary for causal claims. |
| Do longer rules generalize better on hard negatives? | Same-query classification by frozen subset above | Validation calibration only; single inventory and zero-score convention qualify discrimination. |
| Does edge noise change relative robustness? | Original protocol implemented, unexecuted | Both-model retraining and replicated corruption controls required. |
| Are effects stable across mining samples, neural seeds and CoDEx-M? | Three neural seeds where complete; one rule inventory; CoDEx-S only | Independent mining repeats, stronger final budgets and CoDEx-M remain pending. |
| Can graph features select the more reliable model? | Unverified research hypothesis | No hybrid/selector trained; answer-dependent diagnostics cannot be deployment features. |

Direct observations are the saved metrics and curves. Controlled evidence comes only from frozen-subset interventions with fixed queries/inventory; it is conditional on those trained systems. Mechanistic claims about distributed representations, entity memorization or relational connectivity remain plausible explanations until tested with matched graph interventions. No universal logical laws or novelty are claimed.

## Phase 5 and execution boundary

`runs/next-phase-sparsity-prepared` contains original, global-random, relation-stratified random, targeted-local and exactly relation-count-matched targeted-control graphs at 90% retention, with seeds, masks, degree distributions, relation frequencies and available truth-path diagnostics. Target selection and masks use training information only; held-out path measurements are evaluation diagnostics. Official evaluation queries and candidate vocabulary are fixed. Both-model perturbed retraining smoke is pending, not reported as executed. A large perturbation matrix and a 400-epoch benchmark run were not launched.

## Research grounding

[Meilicke et al. (2018)](https://web.informatik.uni-mannheim.de/RuleN/meilicke18.pdf) motivate explanation-based fine-grained comparison; this is a conceptual replication using different systems/data. [CoDEx](https://aclanthology.org/2020.emnlp-main.669/) supplies the benchmark tasks, official splits and verified negatives; its published training/search and relation-specific classification thresholds are not reproduced exactly. [Anil et al. (2024)](https://aclanthology.org/2024.lrec-main.792/) motivate attention to rule evidence and unranked cases in an inductive setting; that setting is not reproduced here. Frozen-family/length subsets and relation-matched sparsity controls extend this project's analysis; no literature-wide novelty claim is made. The [PyClause defaults](https://github.com/symbolic-kg/PyClause/blob/master/clause/config-default.yaml) and [application source](https://github.com/symbolic-kg/PyClause/blob/master/src/c_clause/features/Application.cpp) ground the executable native-scoring/completeness audit. Historic LibKGE inheritance and mining convergence remain explicitly unverified.
"""
    answers = []
    if final:
        neural_mean = float(np.mean([r["metrics"]["mrr_exact"] for r in final["seeds"]]))
        control = read(neural / "search/slcwa-control/curve.json")
        first, last = control["history"][0], control["history"][-1]
        answers.append({"question": "Was the original ComplEx pilot undertrained?", "evidence_class": "Direct learning-curve observation; bounded validation-selected comparison",
            "answer": f"The stronger recipe reaches mean test MRR {neural_mean:.4f} versus pilot 0.2046. Extra epochs alone did not repair the sLCWA control: validation MRR fell from {first['validation']['mrr_exact']:.4f} at epoch {first['epoch']} to {last['validation']['mrr_exact']:.4f} at epoch {last['epoch']}. The original comparison used a weak recipe/budget; no single changed setting is identified as the cause.",
            "source": "learning-curves.png; strongest-complex.json; runs/next-phase-neural/final-summary.json"})
    metric_map = {r["condition"]: r for r in metrics}
    if all(n in metric_map for n in ("all", "constants", "general")):
        answers.append({"question": "How much rule success comes from constant implications?", "evidence_class": "Controlled frozen-rule-family subset evidence, one inventory",
            "answer": f"Standalone constant Hits@1 {metric_map['constants']['hits1']:.4f}, general-rule Hits@1 {metric_map['general']['hits1']:.4f}, all-rules Hits@1 {metric_map['all']['hits1']:.4f}. Both families contribute; union contrasts and unique successes quantify contribution without equating rule count with importance.",
            "source": "family-paired-intervals.json; constant-general-overlap.json"})
    for difference in differences:
        if difference["comparison"] == "fixed_constants_general_le3 minus fixed_constants_general_le1":
            relational = next((r for r in differences if r["comparison"] == "general_le3 minus general_le1"), None)
            qualification = " The interval includes zero; a clear net improvement is not established." if difference["ci_low"] <= 0 <= difference["ci_high"] else ""
            if relational:
                qualification += f" Without constants, the corresponding relational-only change is {relational['difference']:+.4f}."
            answers.append({"question": "Does greater available relational rule length help with fixed constants?", "evidence_class": "Controlled inference-time subset intervention, one inventory",
                "answer": f"Maximum length 3 minus 1 changes Hits@1 by {difference['difference']:+.4f}, paired 95% interval [{difference['ci_low']:+.4f}, {difference['ci_high']:+.4f}], with {difference['n_hits1_gains']} gains and {difference['n_hits1_losses']} losses. This holds constants fixed and does not re-mine." + qualification + " Mining-budget effects and inventory stability remain unresolved.",
                "source": "length-paired-intervals.json; changed-predictions.csv"})
    if aggregate.get("general"):
        proportions = aggregate["general"]["complementarity"]["proportions"]
        answers.append({"question": "Which cases are complementary?", "evidence_class": "Direct paired outcomes and exploratory graph associations",
            "answer": f"Across the three neural seeds, only general rules succeed on {proportions['only_rules']:.4f} of directional observations, and only embeddings on {proportions['only_embeddings']:.4f}. Training-only degree/frequency/pattern associations and native groundings describe these cases; they do not identify causal mechanisms or provide a deployable oracle.",
            "source": "neural-rule-comparison.json; complementary-success-properties.csv; cases.md"})
    answers.append({"question": "Which claims still need controlled interventions?", "evidence_class": "Unresolved uncertainty; prepared design",
        "answer": "Connectivity, sparsity and noise mechanisms require both-model retraining with matched graph controls. Independent mining replication and CoDEx-M generalization remain pending. Frequency/degree-adjusted strata are descriptive, not causal identification.",
        "source": "runs/next-phase-sparsity-prepared/plan.json; execution.json"})
    write_json(output / "research-answers.json", answers)
    insertion = "## Current answers and evidence labels\n\n" + table(answers, ["question", "evidence_class", "answer"]) + "\n"
    text = text.replace("## Audit and corrected interpretation\n", insertion + "## Audit and corrected interpretation\n", 1)
    (output / "report.md").write_text(text)
    write_json(output / "execution.json", {"neural_complete": final is not None, "evaluated_conditions": [r["condition"] for r in metrics],
        "pending_conditions": sorted(set(manifest["subsets"]) - set(rows_by_name)), "n_length_changes": len(changed),
        "previous_results_overwritten": False, "independent_rule_mining_repeats": 0, "perturbed_models_trained": False})
    return output / "report.md"
