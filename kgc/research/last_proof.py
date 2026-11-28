"""Bounded training-only audit for complete loss of scarce two-hop proofs."""
import argparse
from collections import Counter
from itertools import product
from pathlib import Path

import numpy as np

from ..backends.anyburl import parse_rule
from ..data import load_dataset
from ..io import digest, triple_digest, write_csv
from .evidence_intervention import SEEDS as PRIOR_SEEDS, catalog_info, probe_groundings, probe_split, strata
from .families import AuditedRules
from .intervention_training import atomic_json
from .structure import native_vocabulary

SEEDS = (1911, 1912, 1913)
N_FIT = 768
N_AUDIT = 640
MAX_PROOFS = 3
MAX_REMOVAL_FRACTION = .01
MIN_SUPPORTED_AUDIT = 60
MIN_LOSS_DIFFERENCE = .08


def samples(n):
    """Three fresh, mutually disjoint fit and audit samples."""
    excluded = set()
    for previous_draw in range(len(PRIOR_SEEDS)):
        for greedy in (False, True):
            for ids in probe_split(n, previous_draw, greedy):
                excluded.update(ids)
    for seed in SEEDS:
        order = np.random.default_rng(seed).permutation(n)
        fresh = [int(i) for i in order if i not in excluded][:N_FIT + N_AUDIT]
        if len(fresh) != N_FIT + N_AUDIT:
            raise ValueError("Too few unused training triples for the declared disjoint probes")
        excluded.update(fresh)
        yield fresh[:N_FIT], fresh[N_FIT:]


def choose_removals(graph, fit, seed, budget):
    """Complete low-cost proof cuts before moving to the next fitting fact."""
    groups = strata(graph)
    membership = {i: key for key, group in groups.items() for i in group}
    choice_rng, control_rng = (np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(2))
    tie = choice_rng.permutation(len(graph.triples))
    targeted = set()
    for _, proofs in sorted(fit, key=lambda item: (len(item[1]), tie[item[0]])):
        surviving = {proof for proof in proofs if targeted.isdisjoint(proof)}
        if not surviving:
            continue
        cuts = [frozenset(cut) for cut in product(*(sorted(proof) for proof in surviving))]
        selected = min(cuts, key=lambda cut: (len(cut), sorted(tie[i] for i in cut)))
        if len(targeted) + len(selected) <= budget:
            targeted.update(selected)
    quotas = Counter(membership[i] for i in targeted)
    matched = {
        int(i) for key, count in sorted(quotas.items())
        for i in control_rng.choice(groups[key], size=count, replace=False)
    }
    if Counter(membership[i] for i in matched) != quotas:
        raise ValueError("Cut and control differ by relation or endpoint degree bin")
    return targeted, matched, quotas


def eligible(native, graph, indices, edge_ids):
    return [(i, proofs) for i, proofs in probe_groundings(native, graph, indices, edge_ids)
            if 1 <= len(proofs) <= MAX_PROOFS]


def audit_counts(audit, targeted, matched):
    rows = []
    for i, proofs in audit:
        left = sum(not proof.isdisjoint(targeted) for proof in proofs)
        right = sum(not proof.isdisjoint(matched) for proof in proofs)
        rows.append(dict(train_index=i, original_two_hop_proofs=len(proofs),
                         targeted_proofs_lost=left, matched_proofs_lost=right,
                         targeted_all_lost=int(left == len(proofs)),
                         matched_all_lost=int(right == len(proofs))))
    n = len(rows)
    left = sum(row["targeted_all_lost"] for row in rows)
    right = sum(row["matched_all_lost"] for row in rows)
    delta = (left - right) / n if n else None
    return rows, dict(n_eligible_audit=n, targeted_all_lost=left, matched_all_lost=right,
                      difference=delta, passed=(n >= MIN_SUPPORTED_AUDIT and delta >= MIN_LOSS_DIFFERENCE))


def alternative_support(graph, removed, exhausted, sources, registry):
    """Score only facts whose scoped proofs are exhausted by the fixed mask."""
    if not exhausted:
        return {}
    altered = graph.with_triples(t for i, t in enumerate(graph.triples) if i not in removed)
    alternatives = {i: {} for i in exhausted}
    indices = {graph.triples[i]: i for i in exhausted}
    for family in ("general", "constants"):
        backend = AuditedRules(altered, sources[family]["path"], token_indices=registry,
                               retain_catalog_metadata=False, collect_evidence=False)
        backend.scorer.calculate_scores(triples=list(indices), loader=backend.loader)
        targets, _, explanations = backend.scorer.get_explanations(as_string=True)
        if set(map(tuple, targets)) != set(indices):
            raise ValueError("Alternative proof targets differ from the audited facts")
        for target, rules in zip(targets, explanations):
            fact = tuple(target)
            supported = False
            for rule in rules:
                for grounding in rule:
                    edges = tuple(map(tuple, grounding))
                    if any(edge not in backend.training_edges for edge in edges):
                        raise ValueError("Alternative proof uses a non-training edge")
                    supported |= bool(edges) and fact not in edges
            alternatives[indices[fact]][family] = int(supported)
        del backend
    return alternatives


def run(graph, output):
    output.mkdir(parents=True, exist_ok=True)
    status = output / "status.json"
    record = dict(status="running", draws=[])
    atomic_json(status, record)
    try:
        sources = catalog_info()
        two_hop = output / "two-hop.rules"
        lines = Path(sources["general"]["path"]).read_text().splitlines()
        two_hop.write_text("".join(line + "\n" for line in lines if line.strip() and parse_rule(line).length == 2))
        registry = native_vocabulary(graph)
        native = AuditedRules(graph, two_hop, token_indices=registry, collect_evidence=False)
        if not len(native.rules) or native.native_loaded_count != len(native.rules):
            raise ValueError("Incomplete two-hop catalog load")
        if (native.options.get("prediction_handler", as_string=False)["num_top_rules"] != -1
                or native.effective_loader_options["b_max_branching_factor"] != -1):
            raise ValueError("Grounding enumeration must be unpruned")
        budget = round(len(graph.triples) * MAX_REMOVAL_FRACTION)
        edge_ids = {triple: i for i, triple in enumerate(graph.triples)}
        plan = dict(seeds=list(SEEDS), n_fit=N_FIT, n_audit=N_AUDIT, max_proofs=MAX_PROOFS,
                    max_removals=budget, min_eligible_audit=MIN_SUPPORTED_AUDIT,
                    min_difference=MIN_LOSS_DIFFERENCE, scope="training only; body excludes proof head",
                    graph_sha256=triple_digest(graph.triples), two_hop_sha256=digest(two_hop),
                    catalog_sha256=sources["general"]["sha256"], n_rules=len(native.rules))
        atomic_json(output / "protocol.json", plan)
        for draw, (seed, (fit_ids, audit_ids)) in enumerate(zip(SEEDS, samples(len(graph.triples))), 1):
            fit = eligible(native, graph, fit_ids, edge_ids)
            targeted, matched, quotas = choose_removals(graph, fit, seed, budget)
            probe_list = eligible(native, graph, audit_ids, edge_ids)
            rows, outcome = audit_counts(probe_list, targeted, matched)
            for label, removed in (("targeted", targeted), ("matched", matched)):
                exhausted = [row["train_index"] for row in rows if row[f"{label}_all_lost"]]
                backup = alternative_support(graph, removed, exhausted, sources, registry)
                for row in rows:
                    for family in ("general", "constants"):
                        row[f"{label}_remaining_{family}"] = backup.get(row["train_index"], {}).get(family)
            root = output / f"draw-{draw}"
            write_csv(root / "audit.csv", rows)
            detail = dict(seed=seed, draw=draw, n_eligible_fit=len(fit), n_removed=len(targeted),
                          fit_ids=fit_ids, audit_ids=audit_ids, removed_targeted=sorted(targeted),
                          removed_matched=sorted(matched), quota=[(*key, count) for key, count in sorted(quotas.items())],
                          audit=outcome)
            atomic_json(root / "plan.json", detail)
            record["draws"].append(dict(draw=draw, n_eligible_fit=len(fit), n_removed=len(targeted),
                                        plan_sha256=digest(root / "plan.json"),
                                        audit_sha256=digest(root / "audit.csv"), **outcome))
            atomic_json(status, record)
            print(f"Draw {draw}: {outcome}", flush=True)
        record.update(status="complete", gate_passed=all(row["passed"] for row in record["draws"]),
                      protocol_sha256=digest(output / "protocol.json"))
        atomic_json(status, record)
    except BaseException as error:
        record.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed", error=repr(error))
        atomic_json(status, record)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(load_dataset("data/codex-s").graph, args.output)


if __name__ == "__main__":
    main()
