"""Deterministic illustrative cases, with native training-checked groundings."""
from pathlib import Path
from collections import defaultdict
from dataclasses import asdict
import re
from ..io import write_json
from ..diagnostics import GraphDiagnostics
from .families import AuditedRules, describe
from .runner import read, load_rows
from .report import condition


def build_cases(dataset, output):
    root = Path("runs/next-phase-frozen")
    neural = Path("runs/next-phase-neural/final/seed-0/test-queries.json.gz")
    if not neural.exists():
        raise RuntimeError("Final seed-0 neural predictions must exist before choosing cases")
    embed = {r["query_id"]: r for r in load_rows(neural)}
    _, general = condition(root, "general")
    _, constants = condition(root, "constants")
    if general is None or constants is None:
        raise RuntimeError("General and constant subset evaluations must be complete")
    chosen = []
    buckets = defaultdict(list)
    const_by_id = {r["query_id"]: r for r in constants}
    for g in sorted(general, key=lambda r: r["query_id"]):
        e, c = embed[g["query_id"]], const_by_id[g["query_id"]]
        if g["hits1"] and not e["hits1"]:
            buckets["general_rule_only_vs_embedding"].append(("general", g, e))
        if e["hits1"] and not g["hits1"]:
            buckets["embedding_only_vs_general_rule"].append(("general", g, e))
        if c["hits1"] and not g["hits1"]:
            buckets["constant_only_vs_general"].append(("constants", c, e))
        if g["hits1"] and not c["hits1"]:
            buckets["general_only_vs_constant"].append(("general", g, e))
    for category, records in buckets.items():
        for subset, row, embedding in records[:2]:
            chosen.append({"category": category, "subset": subset, "rule": row, "embedding": embedding})
    # Length examples are selected by changes, not by an expected direction.
    for prefix, reference in (("general", 1), ("fixed_constants_general", 1), ("fixed_constants_general", 2)):
        _, short = condition(root, prefix + f"_le{reference}")
        _, long = condition(root, prefix + "_le3")
        if short is not None and long is not None:
            for outcome, predicate in (("improves", lambda a, b: a["hits1"] > b["hits1"]),
                                       ("hurts", lambda a, b: a["hits1"] < b["hits1"])):
                options = [(a, b) for a, b in zip(long, short) if predicate(a, b)]
                for a, b in options[:1]:
                    chosen.append({"category": f"longer_{prefix}_{reference}_to_3_{outcome}", "subset": prefix + "_le3", "rule": a,
                                   "short_rule": b, "short_max_length": reference, "embedding": embed[a["query_id"]]})
    subsets = read(root / "subsets/subsets.json")["subsets"]
    diag = GraphDiagnostics(dataset.graph)
    for subset in sorted({r["subset"] for r in chosen}):
        backend = AuditedRules(dataset.graph, subsets[subset]["path"], certify_support=True)
        normalized = {re.sub(r"\s+", "", rule.expression): asdict(rule) for rule in backend.rules}
        for case in [r for r in chosen if r["subset"] == subset]:
            row = case["rule"]
            truth = (row["head"], row["relation"], row["tail"])
            candidates = [row["head"] if row["direction"] == "head" else row["tail"]]
            candidates += [e for e, _ in row["top_predictions"][:2]]
            if "short_rule" in case:
                candidates += [e for e, _ in case["short_rule"]["top_predictions"][:1]]
            triples = [(e, truth[1], truth[2]) if row["direction"] == "head" else (truth[0], truth[1], e) for e in dict.fromkeys(candidates)]
            evidence, _ = backend.explain(triples)
            case["predictions"] = []
            for triple in triples:
                items = []
                native_rules = evidence.get(triple, [])
                if "short_rule" in case:
                    longer = [r for r in native_rules if len(re.findall(r"[^\s(),]+\([^,()]+,[^,()]+\)", r["expression"].split("<=", 1)[1])) > 1]
                    native_rules = longer[:1] + [r for r in native_rules if r not in longer[:1]]
                for rule in native_rules[:3]:
                    expression = rule["expression"]
                    source_rule = normalized.get(re.sub(r"\s+", "", expression))
                    if source_rule:
                        parsed = describe(f"{source_rule['predictions']}\t{source_rule['support']}\t{source_rule['confidence']}\t{expression}")
                        parsed["statistics_status"] = "resolved against frozen source expression"
                    else:
                        parsed = describe(f"0\t0\t0\t{expression}")
                        parsed.update({"predictions": None, "support": None, "confidence": None,
                                       "statistics_status": "native expression not resolved to source statistics"})
                    items.append({**parsed, "groundings": rule.get("groundings", [])[:2]})
                case["predictions"].append({"triple": triple, "labels": [dataset.labels.get(x, x) for x in triple],
                                            "rules": items, "all_groundings_training_checked": True})
            case["graph_features"] = diag.query_features(row)
            case["sampling"] = "first two query IDs per complementarity category; first query per length gain/loss; up to three native supporting rules (prioritize one longer rule in length cases) and first two groundings; illustrative not exhaustive; neural seed0"
        del backend
    output = Path(output)
    write_json(output / "case-studies.json", chosen)
    lines = ["# Representative cases", "", "Deterministic illustrative cases, not an estimate of group prevalence. All displayed grounding edges were checked against training positives. Original IDs are retained where labels were not downloaded.", ""]
    for case in chosen:
        r, e = case["rule"], case["embedding"]
        lines += [f"## {case['category']}: {r['query_id']}", "", f"Triple `{r['head']} {r['relation']} {r['tail']}`; predict **{r['direction']}**. Rule subset `{case['subset']}`; rule rank `{r['rank']}`, embedding seed-0 rank `{e['rank']}`. Raw scores: rule `{r['score']}`, embedding `{e['score']}`. These are not calibrated probabilities.", "",
                  f"Rule top predictions: `{r['top_predictions'][:3]}`. Embedding top predictions: `{e['top_predictions'][:3]}`.", "", f"Training graph characteristics: `{case['graph_features']}`.", ""]
        if "short_rule" in case:
            lines += [f"Length-{case['short_max_length']}-capped rule rank: `{case['short_rule']['rank']}`; top predictions: `{case['short_rule']['top_predictions'][:3]}`.", ""]
        for prediction in case["predictions"]:
            lines += ["Prediction `" + " ".join(prediction["labels"]) + "`:", ""]
            for rule in prediction["rules"]:
                confidence = f"{rule['confidence']:.4f}" if rule['confidence'] is not None else "unavailable"
                lines += [f"- `{rule['expression']}` ({rule['native_family']}, length {rule['length']}, raw confidence {confidence}, support {rule['support']}); training grounding examples: `{rule['groundings']}`."]
            if not prediction["rules"]:
                lines += ["No native supporting rule returned for this candidate."]
            lines.append("")
    (output / "cases.md").write_text("\n".join(lines))
    return chosen
