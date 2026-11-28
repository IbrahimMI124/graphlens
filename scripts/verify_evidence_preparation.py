"""Verify the saved masks, independent training audit and fixed threshold."""
import argparse
from collections import Counter
import csv
import math
from pathlib import Path

import numpy as np

from kgc.data import load_dataset
from kgc.io import digest, triple_digest, write_csv
from kgc.research.evidence_intervention import (
    CONDS, DESIGN, GATE_PP, GREEDY_DESIGN, GREEDY_SEEDS, RETENTION, SEEDS, probe_split, strata,
)
from kgc.research.report import table
from kgc.research.runner import read


def verify(prepared, greedy=False):
    data = load_dataset("data/codex-s")
    graph = data.graph
    status = read(prepared / "preparation-status.json")
    seeds = GREEDY_SEEDS if greedy else SEEDS
    method = GREEDY_DESIGN if greedy else DESIGN
    if status["status"] != "complete" or len(status["draws"]) != len(seeds):
        raise ValueError("Preparation did not complete all declared draws")
    groups = strata(graph)
    rows = []
    for index, (seed, probe_seed) in enumerate(seeds):
        src = prepared / f"draw-{index + 1}"
        plan_path = src / "plan.json"
        plan = read(plan_path)
        stamp = status["draws"][index]
        fit_ids, audit_ids = probe_split(len(graph.triples), index, greedy)
        if (stamp["plan_sha256"] != digest(plan_path) or plan["draw"] != index
                or (plan["removal_seed"], plan["probe_seed"]) != (seed, probe_seed)
                or plan["method"] != method or plan["gate_percentage_points"] != GATE_PP
                or plan["fit_probes"] != fit_ids.tolist() or plan["audit_probes"] != audit_ids.tolist()
                or plan["original_graph_sha256"] != triple_digest(graph.triples)):
            raise ValueError("Unexpected draw provenance")
        expected = Counter({(q["relation"], q["head_log2_degree"], q["tail_log2_degree"]):
                            q["n_removed"] for q in plan["strata_quotas"]})
        arms = []
        for condition in CONDS:
            meta = plan["graph_design"][condition]
            removed = set(meta["removed_indices"])
            arms.append(removed)
            observed = Counter({k: sum(i in removed for i in ids) for k, ids in groups.items()})
            training = tuple(t for i, t in enumerate(graph.triples) if i not in removed)
            if (observed != expected or len(training) != round(RETENTION * len(graph.triples))
                    or len(training) != meta["n_edges"] or triple_digest(training) != meta["training_graph_sha256"]):
                raise ValueError("Training mask or matched quotas are inconsistent")
        with (src / "training-audit.csv").open() as stream:
            audit = [{key: int(v) for key, v in row.items()} for row in csv.DictReader(stream)]
        if [r["train_index"] for r in audit] != audit_ids.tolist():
            raise ValueError("Audit rows differ from the held-apart training probes")
        nonzero = [r for r in audit if r["original_groundings"]]
        if not nonzero or any(not 0 <= r[f"{arm}_lost"] <= r["original_groundings"]
                              for r in audit for arm in ("targeted", "matched")):
            raise ValueError("Audit groundings are invalid")
        targeted, matched = (
            sum(r[f"{arm}_lost"] / r["original_groundings"] for r in nonzero) / len(nonzero)
            for arm in ("targeted", "matched")
        )
        delta = targeted - matched
        passed = 100 * delta >= GATE_PP
        if (not math.isclose(delta, stamp["audit"]["difference"], abs_tol=1e-12)
                or passed != stamp["audit"]["passed"] or stamp["audit"] != plan["audit"]):
            raise ValueError("Saved gate decision disagrees with independent recomputation")
        fact_differences = np.array([
            (r["targeted_lost"] - r["matched_lost"]) / r["original_groundings"] for r in nonzero
        ])
        rng = np.random.default_rng(seed)
        indices = rng.integers(len(nonzero), size=(2000, len(nonzero)))
        low, high = np.quantile(fact_differences[indices].mean(axis=1), (.025, .975))
        rows.append(dict(draw=index + 1, audit_supported_facts=len(nonzero),
                         edges_removed_per_arm=len(arms[0]), removed_edges_in_both_arms=len(arms[0] & arms[1]),
                         targeted_loss_pct=100 * targeted, matched_loss_pct=100 * matched,
                         targeted_facts_losing_all=sum(r["targeted_lost"] == r["original_groundings"] for r in nonzero),
                         matched_facts_losing_all=sum(r["matched_lost"] == r["original_groundings"] for r in nonzero),
                         targeted_score_positive_removed=plan["graph_design"][CONDS[0]]["n_positive_score_removed"],
                         matched_score_positive_removed=plan["graph_design"][CONDS[1]]["n_positive_score_removed"],
                         targeted_isolated=plan["graph_design"][CONDS[0]]["n_isolated"],
                         matched_isolated=plan["graph_design"][CONDS[1]]["n_isolated"],
                         conditional_ci_low_pp=100 * float(low), conditional_ci_high_pp=100 * float(high),
                         difference_pp=100 * delta, passed=passed))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared", type=Path)
    parser.add_argument("--greedy", action="store_true")
    args = parser.parse_args()
    rows = verify(args.prepared, args.greedy)
    write_csv(args.prepared / "verified-training-audit.csv", rows)
    header = "# Training-only audit for direct rule-body removal\n\n"
    scope = ("Method: marginal grounding loss.\n\n" if args.greedy else "Method: additive edge incidence.\n\n")
    outcome = ("All three draws met the five-point training threshold.\n" if all(r["passed"] for r in rows)
               else "The full matrix requires all three draws to meet the five-point training threshold. "
                    "This design failed that criterion.\n")
    body = table(rows, ["draw", "audit_supported_facts", "targeted_loss_pct", "matched_loss_pct",
                        "difference_pp", "conditional_ci_low_pp", "conditional_ci_high_pp", "passed"])
    bounds = ("\nThe 95% intervals pair the two masks for each audit fact and resample facts within "
              "each draw. They condition on the graph, catalog and prepared masks. "
              "The gate uses the point estimate. [Full audit table](verified-training-audit.csv)\n")
    (args.prepared / "audit.md").write_text(header + scope + body + "\n" + outcome + bounds)
    print(body, outcome, sep="\n")


if __name__ == "__main__":
    main()
