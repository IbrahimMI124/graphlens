"""Replicate the CoDEx-S targeted vs relation-matched deletion contrast."""
import argparse
from collections import Counter
from pathlib import Path
import re
import signal

import numpy as np

from ..data import load_dataset, write_triples
from ..evaluation import queries
from ..io import digest, environment, write_csv
from .families import AuditedRules
from .intervention_training import atomic_json
from .runner import read
from .sparsity import interventions
from .structure import apply_rules, native_vocabulary, run
from .structure_cases import valid_native_grounding
from .structure_report import checked_rows

TARGETED = "targeted_local"
MATCHED = "targeted_relation_matched_control"
CONDITIONS = (TARGETED, MATCHED)
SEEDS = ((231, 940), (232, 941), (233, 942))
NEURAL_SEEDS = (0, 1, 2)
RULE_REPETITIONS = 2
FAMILIES = ("general", "constants")
SUBSETS = Path("runs/next-phase-frozen/subsets/subsets.json")
METRICS = ("hits1", "hits10", "covered", "true_returned", "reciprocal_rank")


def make_pair(dataset, draw):
    removal_seed, target_seed = SEEDS[draw]
    graphs = interventions(dataset.graph, seed=removal_seed, target_seed=target_seed)
    result = {name: graphs[name] for name in CONDITIONS}
    left, right = (Counter(r for _, r, _ in result[name][0].triples) for name in CONDITIONS)
    if left != right:
        raise ValueError("Relation counts differ within a matched pair")
    original = set(dataset.graph.triples)
    for graph, metadata in result.values():
        modified = dataset.with_graph(graph)
        if (not set(graph.triples) <= original or graph.entities != dataset.graph.entities
                or graph.relations != dataset.graph.relations
                or modified.test != dataset.test or modified.valid != dataset.valid
                or any(modified.positives_for_filter(s) != dataset.positives_for_filter(s)
                       for s in ("valid", "test"))):
            raise ValueError("Deletion violated the fixed benchmark protocol")
        incoming = Counter(t for _, _, t in graph.triples)
        outgoing = Counter(h for h, _, _ in graph.triples)
        degrees = [incoming[e] + outgoing[e] for e in graph.entities]
        metadata.update(n_edges=len(graph.triples), n_isolated=degrees.count(0),
                        directed_two_hop_walks=sum(incoming[e] * outgoing[e] for e in graph.entities),
                        degree_quantiles=np.quantile(degrees, [0, .25, .5, .75, 1]).tolist())
    return result


def grounding_keys(backend, facts):
    evidence, _ = backend.explain(facts)
    if set(evidence) != set(facts):
        raise ValueError("Native grounding targets do not match the diagnostic facts")
    result = {}
    for fact, items in evidence.items():
        keys = set()
        for item in items:
            expression = item["expression"]
            key = re.sub(r"\s+", "", expression)
            for ground in item["groundings"]:
                edges = tuple(map(tuple, ground))
                if not valid_native_grounding(expression, edges, fact):
                    raise ValueError(f"Invalid native grounding for {fact}: {expression}")
                keys.add((key, edges))
        result[fact] = keys
    return result


def grounding_diagnostics(dataset, graphs, source, indices, output, limit, conditions=CONDITIONS):
    """Count unique native B rule/ordered-body witnesses per gold triple.

    Native prediction explanations run only after masked ranking. The source
    graph is always training-only, including for these gold-bound diagnostics.
    """
    facts = dataset.test[:limit]
    backends = {
        name: AuditedRules(graph, source, token_indices=indices, collect_evidence=False)
        for name, graph in {"original": dataset.graph, **graphs}.items()
    }
    for backend in backends.values():
        options = backend.options.get("prediction_handler", as_string=False)
        if (options["num_top_rules"] != -1
                or backend.effective_loader_options["b_max_branching_factor"] != -1
                or backend.native_loaded_count != len(backend.rules)):
            raise ValueError("Grounding diagnostics require the unpruned B inventory")
    rows, examples = [], []
    for offset in range(0, len(facts), 24):
        batch = facts[offset:offset + 24]
        results = {name: grounding_keys(backend, batch) for name, backend in backends.items()}
        for j, fact in enumerate(batch, offset):
            before = results["original"][fact]
            row = dict(triple_id=f"test:{j}", head=fact[0], relation=fact[1], tail=fact[2],
                       original_groundings=len(before))
            for label, condition in zip(("targeted", "matched"), conditions):
                backend = backends[condition]
                survivors = {key for key in before if all(e in backend.training_edges for e in key[1])}
                if survivors != results[condition][fact]:
                    raise ValueError(f"Native grounding enumeration disagrees with edge survival for {condition} {fact}")
                lost = before - survivors
                row[f"{label}_groundings"] = len(survivors)
                row[f"{label}_lost"] = len(lost)
                if lost and len(examples) < 20:
                    expression, edges = min(lost)
                    examples.append(dict(condition=condition, triple_id=row["triple_id"], fact=fact,
                                         expression=expression, body=edges,
                                         missing=[e for e in edges if e not in backend.training_edges]))
            rows.append(row)
    write_csv(output / "grounding-loss.csv", rows)
    atomic_json(output / "grounding-examples.json", examples)
    return rows


def compact_outputs(dataset, root, limit, smoke=False, conditions=CONDITIONS):
    """One small, aligned matrix for all completed outcome series."""
    arrays, overall = {}, []
    for condition in conditions:
        paths = dict(
            neural=[root / "fresh" / condition / f"neural-{s}" / "validation-best"
                    for s in ((0,) if smoke else NEURAL_SEEDS)],
            fixed_updates=[root / "fresh" / condition / f"neural-{s}" / "fixed-updates"
                           for s in ((0,) if smoke else NEURAL_SEEDS)],
        )
        for family in ("all", *FAMILIES):
            paths[f"fresh_{family}"] = [
                root / "fresh" / condition / f"rules-{r}" / family
                for r in range(1 if smoke else RULE_REPETITIONS)
            ]
        for family in FAMILIES:
            paths[f"frozen_{family}"] = [root / "frozen" / condition / family]
        for method, cells in paths.items():
            series = []
            for replicate, path in enumerate(cells):
                rows = checked_rows(path, dataset, limit)
                series.append([[float(row[key]) if row.get(key) is not None else np.nan
                                for key in METRICS] for row in rows])
                metrics = read(path / "metrics.json")
                overall.append(dict(condition=condition, method=method, replicate=replicate,
                                    certified=all(row["hits_certified"] for row in rows), **metrics))
            arrays[f"{condition}/{method}"] = np.asarray(series)
    for family in FAMILIES:
        path = root / "frozen" / "original" / family
        rows = checked_rows(path, dataset, limit)
        overall.append(dict(condition="original", method=f"frozen_{family}", replicate=0,
                            certified=all(row["hits_certified"] for row in rows), **read(path / "metrics.json")))
    arrays["query_ids"] = np.array([q.query_id for q in queries(dataset.test[:limit])])
    arrays["metrics"] = np.array(METRICS)
    with (root / "outcomes.tmp").open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    (root / "outcomes.tmp").replace(root / "outcomes.npz")
    write_csv(root / "overall.csv", overall)
    return overall


def execute_pair(dataset, draw, root, smoke, pair, seed_pair, extra_protocol=None):
    root.mkdir(parents=True, exist_ok=True)
    limit = 16 if smoke else None
    indices = native_vocabulary(dataset.graph)
    sources = read(SUBSETS)["subsets"]
    for family in FAMILIES:
        if digest(sources[family]["path"]) != sources[family]["sha256"]:
            raise ValueError("Frozen rule inventory hash mismatch")
    selection = read("runs/next-phase-neural/selection.json")["winner"]["path"]
    protocol = dict(draw=draw, smoke=smoke, removal_seed=seed_pair[0], target_seed=seed_pair[1],
                    neural_seeds=[0] if smoke else list(NEURAL_SEEDS),
                    independent_miners=1 if smoke else RULE_REPETITIONS, limit_facts=limit,
                    graph_design={name: metadata for name, (_, metadata) in pair.items()},
                    splits=dataset.provenance["sha256"],
                    catalogs={family: sources[family]["sha256"] for family in FAMILIES},
                    vocabulary=indices["source_training_graph_sha256"],
                    selection_curve_sha256=digest(Path(selection) / "curve.json"))
    if extra_protocol is not None:
        protocol["intervention"] = extra_protocol
    declaration = root / "replication-protocol.json"
    if declaration.exists() and read(declaration) != protocol:
        raise ValueError("Refusing to change an existing draw protocol")
    atomic_json(declaration, protocol)
    state_path = root / "replication-status.json"
    state = dict(status="running", draw=draw, smoke=smoke, completed=[], environment=environment())

    def checkpoint(stage):
        state["completed"].append(stage)
        atomic_json(state_path, state)
        print(f"Draw {draw + 1}: {stage} complete", flush=True)

    atomic_json(state_path, state)
    try:
        for name, (graph, _) in pair.items():
            write_triples(root / "graphs" / name / "train.txt", graph.triples)
        print(f"Draw {draw + 1}: starting fresh models", flush=True)
        run(dataset, None, root / "fresh", smoke, seeds=(0,) if smoke else NEURAL_SEEDS,
            rule_repetitions=1 if smoke else RULE_REPETITIONS, graph_pair=pair, lightweight_rules=True)
        if read(root / "fresh" / "execution.json")["status"] != "complete":
            raise ValueError("Fresh run matrix incomplete")
        checkpoint("fresh comparisons")
        graphs = {name: pair[name][0] for name in CONDITIONS}
        for name, graph in {"original": dataset.graph, **graphs}.items():
            for family in FAMILIES:
                apply_rules(dataset.with_graph(graph), sources[family]["path"],
                            root / "frozen" / name / family, limit, indices,
                            retain_catalog_metadata=False, cache_size=2 * len(dataset.test))
        checkpoint("frozen ranking")
        grounding_diagnostics(dataset, graphs, sources["general"]["path"], indices, root, limit, tuple(pair))
        checkpoint("grounding loss")
        overall = compact_outputs(dataset, root, limit, smoke, tuple(pair))
        checkpoint("paired query outputs")
        state.update(status="complete", certified_hits=all(row["certified"] for row in overall),
                     protocol_sha256=digest(declaration), outcomes_sha256=digest(root / "outcomes.npz"))
        atomic_json(state_path, state)
    except BaseException as error:
        state.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed", error=repr(error))
        atomic_json(state_path, state)
        raise


def execute(draw, root, smoke):
    dataset = load_dataset("data/codex-s")
    execute_pair(dataset, draw, root, smoke, make_pair(dataset, draw), SEEDS[draw])


def main():
    def terminated(signum, _frame):
        raise KeyboardInterrupt(f"Received signal {signum}")

    signal.signal(signal.SIGTERM, terminated)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draw", type=int, choices=range(len(SEEDS)), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    execute(args.draw, args.output, args.smoke)


if __name__ == "__main__":
    main()
