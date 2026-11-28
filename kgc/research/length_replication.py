"""Repeat the length ablation on a previously mined, independent catalog."""
import argparse
from pathlib import Path

from ..data import load_dataset
from ..io import digest, triple_digest, write_csv
from .families import describe
from .intervention_training import atomic_json
from .runner import read
from .structure import apply_rules, native_vocabulary
from .structure_report import checked_rows, effect


def run(mining, output, limit=None):
    dataset = load_dataset("data/codex-s")
    training = read(mining / "training.json")
    source = mining / Path(training["rules_file"]).name
    if (training["rule_file_sha256"] != digest(source)
            or training["training_graph_sha256"] != triple_digest(dataset.graph.triples)
            or training["config"]["seconds"] != 60):
        raise ValueError("Expected a complete independent 60-second catalog on the original training graph")
    output.mkdir(parents=True, exist_ok=True)
    variants = []
    for line in source.read_text().splitlines():
        if line.strip():
            rule = describe(line)
            if rule["native_family"] == "B":
                variants.append((line, "general", rule["length"]))
            elif rule["constant_bearing"] and not rule["unconditional_prior"]:
                variants.append((line, "constant", rule["length"]))
    registry = native_vocabulary(dataset.graph)
    rows = []
    for mode in ("general", "fixed_constants"):
        for length in (1, 2, 3):
            selected = [
                line for line, family, n in variants
                if (family == "general" and n <= length)
                or (mode == "fixed_constants" and family == "constant")
            ]
            root = output / f"{mode}-le{length}"
            root.mkdir(exist_ok=True)
            subset = root / "rules.txt"
            subset.write_text("".join(line + "\n" for line in selected))
            stats = apply_rules(dataset, subset, root, limit, registry, retain_catalog_metadata=False,
                                cache_size=2 * len(dataset.test))
            rows.append(dict(mode=mode, max_general_length=length, n_rules=len(selected),
                             source_sha256=training["rule_file_sha256"], subset_sha256=digest(subset),
                             n_queries=stats["n_queries"], hits1=stats["hits1"], hits10=stats["hits10"],
                             coverage=stats["coverage"], certified_query_fraction=stats["certified_query_fraction"]))
            print(mode, length, stats["n_queries"], stats["hits1"], flush=True)
    comparisons = []
    for mode in ("general", "fixed_constants"):
        before = checked_rows(output / f"{mode}-le1", dataset, limit)
        after = checked_rows(output / f"{mode}-le3", dataset, limit)
        stats = effect([after], [before])
        comparisons.append(dict(mode=mode, source_sha256=training["rule_file_sha256"], **stats))
    write_csv(output / "metrics.csv", rows)
    write_csv(output / "paired-length-3-minus-1.csv", comparisons)
    atomic_json(output / "status.json", dict(status="complete", limit_facts=limit,
                    source_sha256=training["rule_file_sha256"], independent_catalog=str(mining),
                    metrics_sha256=digest(output / "metrics.csv"),
                    effects_sha256=digest(output / "paired-length-3-minus-1.csv")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mining", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    run(args.mining, args.output, args.limit)


if __name__ == "__main__":
    main()
