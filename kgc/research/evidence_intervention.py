"""Training-only selection of rule-body deletions with matched controls."""
import argparse
from collections import Counter, defaultdict
import heapq
from pathlib import Path
import signal

import numpy as np

from ..data import load_dataset, write_triples
from ..io import digest, triple_digest, write_csv
from .families import AuditedRules, describe
from .intervention_training import atomic_json
from .removal_replication import FAMILIES, SUBSETS, execute_pair, grounding_keys
from .runner import read
from .structure import native_vocabulary

CONDS = ("evidence_targeted", "evidence_matched")
# (control/tie randomization seed, independent training probe split seed)
SEEDS = ((751, 1711), (752, 1712), (753, 1713))
PROBES_PER_GROUP = 384
RETENTION = .9
GATE_PP = 5
DESIGN = "B-body source-edge incidence; per-fit-fact normalization; relation/head-degree-bin/tail-degree-bin matched v1"
GREEDY_DESIGN = "B-body weighted grounding coverage; per-fit-fact normalization; relation/head-degree-bin/tail-degree-bin matched v2"
GREEDY_SEEDS = ((851, 1811), (852, 1812), (853, 1813))
GREEDY_FIT = 1152


def strata(graph):
    degree = Counter(x for h, _, t in graph.triples for x in (h, t))
    groups = defaultdict(list)
    for i, (h, r, t) in enumerate(graph.triples):
        groups[(r, degree[h].bit_length() - 1, degree[t].bit_length() - 1)].append(i)
    return groups


def masks(graph, scores, seed, retain=RETENTION):
    """Fix quotas before scoring. Random control samples within the same strata."""
    if not 0 < retain <= 1 or len(scores) != len(graph.triples) or not np.isfinite(scores).all():
        raise ValueError("Invalid retention or scores")
    groups = strata(graph)
    n = len(graph.triples)
    n_remove = n - round(retain * n)
    quota = {key: len(group) * n_remove // n for key, group in groups.items()}
    priority = sorted(groups, key=lambda k: (-(len(groups[k]) * n_remove % n), k))
    for key in priority[:n_remove - sum(quota.values())]:
        quota[key] += 1

    ties, control = (np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(2))
    tie_order = ties.permutation(n)
    targeted, matched = set(), set()
    for key, group in sorted(groups.items()):
        count = quota[key]
        if count:
            targeted.update(sorted(group, key=lambda i: (-scores[i], tie_order[i]))[:count])
            matched.update(map(int, control.choice(group, size=count, replace=False)))
    expected = Counter({k: v for k, v in quota.items() if v})
    for arm in (targeted, matched):
        observed = Counter({k: sum(i in arm for i in group) for k, group in groups.items()})
        if len(arm) != n_remove or observed != expected:
            raise ValueError("Removal quotas differ across arms")
    return targeted, matched, expected


def probe_groundings(backend, graph, ids, edge_ids):
    """Enumerate real native B groundings; omit proofs using their own head fact."""
    for start in range(0, len(ids), 24):
        batch = [graph.triples[idx] for idx in ids[start:start + 24]]
        evidence = grounding_keys(backend, batch)
        for index, fact in zip(ids[start:start + 24], batch):
            instances = [
                frozenset(edge_ids[edge] for edge in edges)
                for _, edges in evidence[fact] if fact not in edges
            ]
            yield int(index), instances


def evidence_scores(graph, probe_iterator):
    scores = np.zeros(len(graph.triples))
    for _, proofs in probe_iterator:
        if proofs:
            weights = Counter()
            for proof in proofs:
                if not 1 <= len(proof) <= 3:
                    raise ValueError("Expected a nonempty body of at most three distinct training edges")
                for i in proof:
                    weights[i] += 6 // len(proof)
            for i, weight in weights.items():
                scores[i] += weight / (6 * len(proofs))
    return scores


def greedy_masks(graph, probe_iterator, seed, retain=RETENTION):
    """Choose the next edge by newly destroyed grounding mass at fixed quotas."""
    from scipy.sparse import coo_matrix

    n = len(graph.triples)
    _, matched, quota = masks(graph, np.zeros(n), seed, retain)
    edge_stratum = {i: key for key, edges in strata(graph).items() for i in edges}
    edge_ids, proof_ids, weights = [], [], []
    for _, proofs in probe_iterator:
        counts = Counter(proofs)
        for proof, count in sorted(counts.items(), key=lambda item: sorted(item[0])):
            edge_ids.extend(sorted(proof))
            proof_ids.extend([len(weights)] * len(proof))
            weights.append(count / len(proofs))
    if not weights:
        raise ValueError("The fit probes have no nontrivial rule groundings")
    membership = coo_matrix((np.ones(len(edge_ids), dtype=np.int8), (edge_ids, proof_ids)),
                            shape=(n, len(weights))).tocsr()
    mass = np.array(weights)
    scores = membership @ mass
    ties = np.random.default_rng(np.random.SeedSequence(seed).spawn(2)[0]).permutation(n)
    heap = [(-score, ties[i], i) for i, score in enumerate(scores) if quota[edge_stratum[i]]]
    heapq.heapify(heap)
    targeted, used = set(), Counter()
    while len(targeted) < len(matched):
        previous, tie, edge = heapq.heappop(heap)
        group = edge_stratum[edge]
        if used[group] == quota[group]:
            continue
        member_ids = membership.indices[membership.indptr[edge]:membership.indptr[edge + 1]]
        gain = mass[member_ids].sum()
        if gain < -previous and not np.isclose(gain, -previous, rtol=1e-12, atol=1e-14):
            heapq.heappush(heap, (-gain, tie, edge))
            continue
        targeted.add(edge)
        used[group] += 1
        mass[member_ids] = 0
    if used != quota:
        raise ValueError("Greedy removal failed to match the declared quotas")
    return targeted, matched, quota, scores


def probe_split(n, draw, greedy=False):
    _, seed = (GREEDY_SEEDS if greedy else SEEDS)[draw]
    order = np.random.default_rng(seed).permutation(n)
    if greedy:
        previous = set()
        for _, previous_seed in SEEDS:
            previous.update(np.random.default_rng(previous_seed).permutation(n)[:2 * PROBES_PER_GROUP])
        order = np.array([i for i in order if i not in previous])
    n_fit = GREEDY_FIT if greedy else PROBES_PER_GROUP
    if len(order) < n_fit + PROBES_PER_GROUP:
        raise ValueError("Training graph is too small for the declared probe split")
    return order[:n_fit], order[n_fit:n_fit + PROBES_PER_GROUP]


def training_audit(probe_iterator, targeted, matched):
    rows = []
    for index, proofs in probe_iterator:
        rows.append(dict(train_index=index, original_groundings=len(proofs),
                         targeted_lost=sum(not targeted.isdisjoint(p) for p in proofs),
                         matched_lost=sum(not matched.isdisjoint(p) for p in proofs)))
    supported = [row for row in rows if row["original_groundings"] > 0]
    if not supported:
        raise ValueError("No supported training audit facts")
    loss = {arm: float(np.mean([row[f"{arm}_lost"] / row["original_groundings"] for row in supported]))
            for arm in ("targeted", "matched")}
    total_loss = loss["targeted"] - loss["matched"]
    return rows, dict(n_facts=len(rows), n_supported=len(supported), **loss,
                      difference=total_loss, passed=100 * total_loss >= GATE_PP)


def catalog_info():
    sources = read(SUBSETS)["subsets"]
    for family in FAMILIES:
        if digest(sources[family]["path"]) != sources[family]["sha256"]:
            raise ValueError("Frozen rule inventory hash mismatch")
    return sources


def prepare_draw(graph, backend, draw, output, greedy=False):
    if not 0 <= draw < len(SEEDS):
        raise ValueError("Draw outside the fixed seed list")
    seed, probe_seed = (GREEDY_SEEDS if greedy else SEEDS)[draw]
    select, audit = probe_split(len(graph.triples), draw, greedy)
    edge_ids = {t: i for i, t in enumerate(graph.triples)}
    fits = probe_groundings(backend, graph, select, edge_ids)
    if greedy:
        targeted, matched, quotas, scores = greedy_masks(graph, fits, seed)
    else:
        scores = evidence_scores(graph, fits)
        targeted, matched, quotas = masks(graph, scores, seed)
    rows, check = training_audit(probe_groundings(backend, graph, audit, edge_ids), targeted, matched)
    graph_design = {}
    for condition, removed in zip(CONDS, (targeted, matched)):
        kept = tuple(t for i, t in enumerate(graph.triples) if i not in removed)
        degree = Counter(x for h, _, t in kept for x in (h, t))
        relations = Counter(graph.triples[i][1] for i in removed)
        write_triples(output / condition / "train.txt", kept)
        graph_design[condition] = dict(seed=seed, target_seed=probe_seed, n_edges=len(kept),
                                      removed_indices=sorted(removed), removed_by_relation=dict(relations),
                                      training_graph_sha256=triple_digest(kept),
                                      n_isolated=len(graph.entities) - len(degree),
                                      n_positive_score_removed=int((scores[sorted(removed)] > 0).sum()))
    metadata = dict(draw=draw, method=GREEDY_DESIGN if greedy else DESIGN, removal_seed=seed, probe_seed=probe_seed,
                    original_graph_sha256=triple_digest(graph.triples),
                    catalog_sha256=digest(backend.rules_file), gate_percentage_points=GATE_PP,
                    fit_probes=select.tolist(), audit_probes=audit.tolist(), audit=check,
                    overlap_removed=len(targeted & matched),
                    strata_quotas=[{"relation": r, "head_log2_degree": h, "tail_log2_degree": t, "n_removed": n}
                                   for (r, h, t), n in sorted(quotas.items())], graph_design=graph_design)
    write_csv(output / "training-audit.csv", rows)
    atomic_json(output / "plan.json", metadata)
    print(f"Draw {draw + 1}: training audit delta {100 * check['difference']:+.2f} pp, "
          f"{'passed' if check['passed'] else 'below gate'}", flush=True)
    return metadata


def prepare(graph, output, greedy=False):
    sources = catalog_info()
    source = sources["general"]["path"]
    backend = AuditedRules(graph, source, token_indices=native_vocabulary(graph), collect_evidence=False)
    options = backend.options.get("prediction_handler", as_string=False)
    if (options["num_top_rules"] != -1 or backend.effective_loader_options["b_max_branching_factor"] != -1
            or backend.native_loaded_count != len(backend.rules)
            or any(describe(line)["native_family"] != "B" for line in Path(source).read_text().splitlines()
                   if line.strip())):
        raise ValueError("Selection requires the complete frozen general B catalog")
    completed = []
    for draw, _ in enumerate(SEEDS):
        dest = output / f"draw-{draw + 1}"
        plan = prepare_draw(graph, backend, draw, dest, greedy)
        completed.append(dict(draw=draw, audit=plan["audit"], plan_sha256=digest(dest / "plan.json")))
    atomic_json(output / "preparation-status.json", dict(status="complete", draws=completed))


def load_pair(dataset, prepared, draw, smoke, greedy=False):
    status = read(prepared / "preparation-status.json")
    dest = prepared / f"draw-{draw + 1}"
    plan = read(dest / "plan.json")
    stamp = status["draws"][draw]
    seed, probe_seed = (GREEDY_SEEDS if greedy else SEEDS)[draw]
    design = GREEDY_DESIGN if greedy else DESIGN
    if (status["status"] != "complete" or stamp["draw"] != draw or plan["draw"] != draw
            or (plan["removal_seed"], plan["probe_seed"]) != (seed, probe_seed)
            or plan["method"] != design or stamp["plan_sha256"] != digest(dest / "plan.json")
            or plan["original_graph_sha256"] != triple_digest(dataset.graph.triples)
            or plan["catalog_sha256"] != catalog_info()["general"]["sha256"]):
        raise ValueError("Prepared rule evidence provenance mismatch")
    if not plan["audit"]["passed"] or (not smoke and not all(d["audit"]["passed"] for d in status["draws"])):
        raise ValueError("The fixed training evidence gate did not pass for the required draws")
    groups = strata(dataset.graph)
    pair, counts = {}, []
    for condition in CONDS:
        metadata = plan["graph_design"][condition]
        removed = set(metadata["removed_indices"])
        triples = tuple(t for i, t in enumerate(dataset.graph.triples) if i not in removed)
        graph = dataset.graph.with_triples(triples)
        if (len(removed) != len(dataset.graph.triples) - round(RETENTION * len(dataset.graph.triples))
                or triple_digest(triples) != metadata["training_graph_sha256"]):
            raise ValueError("Prepared training mask changed")
        modified = dataset.with_graph(graph)
        if modified.valid != dataset.valid or modified.test != dataset.test or any(
                modified.positives_for_filter(s) != dataset.positives_for_filter(s) for s in ("valid", "test")):
            raise ValueError("Held-out split or evaluator filters changed")
        pair[condition] = (graph, metadata)
        counts.append({k: sum(i in removed for i in values) for k, values in groups.items()})
    if counts[0] != counts[1]:
        raise ValueError("Matched strata fail verification")
    return pair, dict(method=design, preparation_sha256=stamp["plan_sha256"],
                      gate_percentage_points=GATE_PP, training_audit=plan["audit"])


def main():
    def terminated(signum, _frame):
        raise KeyboardInterrupt(f"Received signal {signum}")

    signal.signal(signal.SIGTERM, terminated)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "smoke", "run"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--draw", type=int, choices=range(len(SEEDS)), default=0)
    parser.add_argument("--greedy", action="store_true")
    args = parser.parse_args()
    if args.stage == "prepare":
        # The mask constructor never receives a validation or test triple.
        prepare(load_dataset("data/codex-s").graph, args.output, args.greedy)
    else:
        dataset = load_dataset("data/codex-s")
        smoke = args.stage == "smoke"
        pair, protocol = load_pair(dataset, args.prepared, args.draw, smoke, args.greedy)
        seed_pair = (GREEDY_SEEDS if args.greedy else SEEDS)[args.draw]
        execute_pair(dataset, args.draw, args.output, smoke, pair, seed_pair, protocol)


if __name__ == "__main__":
    main()
