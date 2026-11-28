"""Aggregate the new independent matched deletion draws."""
import argparse
import csv
from pathlib import Path

import numpy as np

from ..io import digest, write_csv
from .removal_replication import CONDITIONS, SEEDS
from .report import table
from .runner import read

METHODS = ("neural", "fixed_updates", "fresh_all", "fresh_general",
           "fresh_constants", "frozen_general", "frozen_constants")
CONTRASTS = (*METHODS, "neural_minus_all")


def load_draw(path, index, seed_pairs=SEEDS):
    state = read(path / "replication-status.json")
    declaration = read(path / "replication-protocol.json")
    if state["status"] != "complete" or state["smoke"] or declaration["draw"] != index:
        raise ValueError(f"Draw {index + 1} is missing a complete full run")
    if (state["protocol_sha256"] != digest(path / "replication-protocol.json")
            or state["outcomes_sha256"] != digest(path / "outcomes.npz")):
        raise ValueError("Completed draw files do not match their recorded hashes")
    if (declaration["removal_seed"], declaration["target_seed"]) != seed_pairs[index]:
        raise ValueError("Completed draw is outside the declared seed design")
    with np.load(path / "outcomes.npz", allow_pickle=False) as saved:
        arrays = {k: saved[k] for k in saved.files}
    with (path / "grounding-loss.csv").open() as f:
        grounding = list(csv.DictReader(f))
    if tuple(arrays["query_ids"]) != tuple(f"{row['triple_id']}:{side}"
                                         for row in grounding for side in ("head", "tail")):
        raise ValueError("Ranking and body grounding results refer to different facts")
    return declaration, state, arrays, grounding


def bootstrap(cells, metric, repetitions=2000, seed=4137, *, conditions=CONDITIONS):
    """Share triples and neural seeds across draws. Sample miners by graph arm."""
    # Keep each method separate because the number of fitted realizations varies.
    series = {
        method: np.stack([
            np.stack([d[f"{arm}/{method}"][:, :, metric].reshape(
                (-1, d["query_ids"].size // 2, 2)).mean(axis=2) for arm in conditions])
            for d in cells
        ])
        for method in METHODS
        if all(np.isfinite(d[f"{arm}/{method}"][:, :, metric]).all() for d in cells for arm in conditions)
    }
    names = [m for m in CONTRASTS if m in series or (m == "neural_minus_all"
             and "neural" in series and "fresh_all" in series and metric in (0, 1))]
    ndraw = len(cells)
    nfact = cells[0]["query_ids"].size // 2
    per_draw = {m: a[:, 0].mean(axis=(1, 2)) - a[:, 1].mean(axis=(1, 2)) for m, a in series.items()}
    if "neural_minus_all" in names:
        per_draw["neural_minus_all"] = per_draw["neural"] - per_draw["fresh_all"]
    rng = np.random.default_rng(seed)
    sampled = {m: np.empty((repetitions, ndraw)) for m in names}
    pooled = {m: np.empty(repetitions) for m in names}
    for rep in range(repetitions):
        facts = rng.integers(nfact, size=nfact)
        multiplicity = np.bincount(facts, minlength=nfact) / nfact
        draws = rng.integers(ndraw, size=ndraw)
        neural = rng.integers(series["neural"].shape[2], size=series["neural"].shape[2])
        # The three rule families share each freshly mined catalog.
        miners = rng.integers(series["fresh_all"].shape[2], size=series["fresh_all"].shape[:3]) if "fresh_all" in series else None
        for method, a in series.items():
            scores = a @ multiplicity
            if method.startswith("fresh_"):
                scores = np.take_along_axis(scores, miners, axis=2)
            elif method in ("neural", "fixed_updates"):
                scores = scores[:, :, neural]
            sampled[method][rep] = scores[:, 0].mean(axis=1) - scores[:, 1].mean(axis=1)
        if "neural_minus_all" in names:
            sampled["neural_minus_all"][rep] = sampled["neural"][rep] - sampled["fresh_all"][rep]
        for method in names:
            pooled[method][rep] = sampled[method][rep, draws].mean()
    rows = []
    for method in names:
        for label, point, samples in zip([*range(1, ndraw + 1), "averaged"],
                                         [*per_draw[method], per_draw[method].mean()],
                                         [*sampled[method].T, pooled[method]]):
            low, high = np.quantile(samples, [.025, .975])
            rows.append(dict(draw=label, method=method, difference=float(point), low=float(low), high=float(high),
                             n_triples=nfact, n_directional_queries=2 * nfact))
    return rows


def grounding_summary(groundings, repetitions=2000, seed=4137):
    before = np.array([[int(r["original_groundings"]) for r in rows] for rows in groundings])
    if not np.all(before == before[0]):
        raise ValueError("Original frozen grounding counts differ between draws")
    eligible = before[0] > 0
    if not eligible.any():
        raise ValueError("No eligible test facts for the grounding loss estimand")
    rows, losses = [], []
    for i, facts in enumerate(groundings):
        targeted, matched = (np.array([int(r[f"{arm}_lost"]) for r in facts])
                             for arm in ("targeted", "matched"))
        scores = (targeted[eligible] - matched[eligible]) / before[i, eligible]
        losses.append(scores)
        rows.append(dict(draw=i + 1, n_facts=len(facts), n_original_supported=int(eligible.sum()),
                         n_original_groundings=int(before[i].sum()), targeted_lost=int(targeted.sum()),
                         matched_lost=int(matched.sum()), targeted_any=int((targeted > 0).sum()),
                         matched_any=int((matched > 0).sum()),
                         targeted_all=int(((targeted == before[i]) & eligible).sum()),
                         matched_all=int(((matched == before[i]) & eligible).sum()),
                         targeted_mean_loss=float((targeted[eligible] / before[i, eligible]).mean()),
                         matched_mean_loss=float((matched[eligible] / before[i, eligible]).mean()),
                         difference=float(scores.mean())))
    losses = np.array(losses)
    rng = np.random.default_rng(seed)
    samples = np.empty((repetitions, len(losses)))
    pooled_samples = np.empty(repetitions)
    for rep in range(repetitions):
        draw = rng.integers(len(losses), size=len(losses))
        ids = rng.integers(losses.shape[1], size=losses.shape[1])
        samples[rep] = losses[:, ids].mean(axis=1)
        pooled_samples[rep] = samples[rep, draw].mean()
    bounds = np.quantile(samples, [.025, .975], axis=0)
    for row, (low, high) in zip(rows, bounds.T):
        row.update(low=float(low), high=float(high))
    low, high = np.quantile(pooled_samples, [.025, .975])
    pooled = dict(difference=float(losses.mean()), low=float(low), high=float(high),
                  n_original_supported=int(eligible.sum()))
    return rows, pooled


def build(paths, output, evidence=False, greedy=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    conditions, seed_pairs = CONDITIONS, SEEDS
    if evidence:
        from .evidence_intervention import CONDS, DESIGN, GATE_PP, GREEDY_DESIGN, GREEDY_SEEDS
        from .evidence_intervention import SEEDS as EVIDENCE_SEEDS
        conditions = CONDS
        seed_pairs = GREEDY_SEEDS if greedy else EVIDENCE_SEEDS
        evidence_design = GREEDY_DESIGN if greedy else DESIGN
    draws = [load_draw(path, i, seed_pairs) for i, path in enumerate(paths)]
    declarations, states, arrays, grounding = zip(*draws)
    reference = declarations[0]
    for declaration, array in zip(declarations, arrays):
        for key in ("splits", "catalogs", "vocabulary", "selection_curve_sha256", "neural_seeds", "independent_miners"):
            if declaration[key] != reference[key]:
                raise ValueError(f"Inconsistent replication provenance for {key}")
        if any(not np.array_equal(array[key], arrays[0][key]) for key in ("query_ids", "metrics")):
            raise ValueError("Query identities or metric definitions differ across draws")
        if set(declaration["graph_design"]) != set(conditions):
            raise ValueError("Unexpected graph arms")
        if evidence:
            intervention = declaration["intervention"]
            if (intervention["method"] != evidence_design or intervention["gate_percentage_points"] != GATE_PP
                    or not intervention["training_audit"]["passed"]):
                raise ValueError("Run differs from the declared rule evidence protocol")
    output.mkdir(parents=True, exist_ok=True)
    overall = []
    for i, path in enumerate(paths, 1):
        with (path / "overall.csv").open() as stream:
            overall.extend(dict(draw=i, **r) for r in csv.DictReader(stream))
    write_csv(output / "overall.csv", overall)
    arm_means = []
    for i in range(1, len(paths) + 1):
        for condition in conditions:
            for method in ("neural", "fresh_all", "fresh_general", "fresh_constants",
                           "frozen_general", "frozen_constants"):
                cells = [r for r in overall if (r["draw"], r["condition"], r["method"]) == (i, condition, method)]
                if not cells:
                    raise ValueError(f"Missing summary for draw {i}/{condition}/{method}")
                means = {}
                for key in ("hits1", "hits10", "mrr_exact", "coverage", "correct_answer_generation_coverage"):
                    observed = [float(r[key]) for r in cells if r.get(key)]
                    means[key] = float(np.mean(observed)) if observed else None
                arm_means.append(dict(draw=i, condition=condition, method=method, n_fits=len(cells),
                                      n_queries=int(cells[0]["n_queries"]), **means))
    write_csv(output / "arm-means.csv", arm_means)
    effects = [dict(metric=metric, **r)
               for index, metric in enumerate(arrays[0]["metrics"])
               for r in bootstrap(arrays, index, conditions=conditions)]
    write_csv(output / "paired-effects.csv", effects)
    ground_rows, pooled_ground = grounding_summary(grounding)
    write_csv(output / "grounding-summary.csv", [*ground_rows, dict(draw="averaged", **pooled_ground)])
    graph_fields = ("n_edges", "n_isolated", "n_positive_score_removed") if evidence else (
        "n_edges", "n_isolated", "target_incident_removed", "directed_two_hop_walks", "degree_quantiles",
    )
    graph_rows = [dict(draw=i + 1, condition=condition, **{k: meta[k] for k in graph_fields})
                  for i, d in enumerate(declarations) for condition, meta in d["graph_design"].items()]
    write_csv(output / "graph-audit.csv", graph_rows)
    outcomes = [r for r in effects if r["metric"] == "hits1" and r["method"] == "neural_minus_all"]
    fig, ax = plt.subplots(figsize=(6.7, 3.3), layout="constrained")
    points = np.array([r["difference"] * 100 for r in outcomes])
    y = np.arange(len(outcomes))
    for pos, r in zip(y, outcomes):
        ax.hlines(pos, 100 * r["low"], 100 * r["high"], color="tab:blue")
    ax.plot(points, y, "o", color="tab:blue")
    ax.set(yticks=y, yticklabels=[f"Draw {r['draw']}" if isinstance(r["draw"], int) else "Across draws" for r in outcomes],
           xlabel="Targeted minus matched change in ComplEx–AnyBURL Hits@1 gap (pp)")
    ax.invert_yaxis()
    ax.axvline(0, linewidth=.9, linestyle=":", color="black")
    ax.set_title("1,828 test facts per graph draw", loc="left", fontsize=10)
    fig.savefig(output / "paired-gap.pdf")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.7, 3.3), layout="constrained")
    ground_contrasts = [*ground_rows, pooled_ground]
    y = np.arange(len(ground_contrasts))
    for pos, row in zip(y, ground_contrasts):
        ax.hlines(pos, 100 * row["low"], 100 * row["high"], color="tab:green")
        ax.plot(100 * row["difference"], pos, "o", color="tab:green")
    ax.set(yticks=y, yticklabels=[*(f"Draw {row['draw']}" for row in ground_rows), "Across draws"],
           xlabel="Targeted minus matched mean per-fact grounding loss (pp)")
    ax.invert_yaxis()
    ax.axvline(0, linewidth=.9, linestyle=":", color="black")
    ax.set_title(f"{pooled_ground['n_original_supported']:,} originally supported facts per draw", loc="left", fontsize=10)
    fig.savefig(output / "grounding-loss.pdf")
    plt.close(fig)
    primary_keys = ["draw", "difference", "low", "high", "n_triples"]
    status = "All ranks used in Hits outcomes were certified for the available supported candidates." if all(
        s["certified_hits"] for s in states) else "Some rule outcomes are retrieved-list results. Verify certification in the overall table before claiming exact Hits."
    text = """# CoDEx-S structural sensitivity across three matched graph draws

Each draw pairs targeted deletion with a random deletion with exactly the same retained relation counts. Each arm has three fitted ComplEx seeds and two independently mined rule inventories. The validation-selected models are used for the primary contrast. The official evaluation contains 1,828 facts and 3,656 directional queries shared by all draws.

## Change in the neural versus rule gap

Positive values mean targeted removal favors ComplEx relative to all-rule AnyBURL more than the matched deletion does. Effects and interval endpoints in the table are proportions. The per-draw intervals share paired head and tail clusters and resample the fitted learning replicates. The aggregate also resamples graph draws. Three graph draws give limited uncertainty information. These estimates are exploratory on CoDEx-S.

"""
    text += table(outcomes, primary_keys) + "\n\n" + status
    primary_methods = ("neural", "fixed_updates", "fresh_all", "frozen_general", "frozen_constants")
    effects_summary = [
        row for row in effects if row["draw"] == "averaged" and row["metric"] == "hits1"
        and row["method"] in primary_methods
    ]
    text += "\n\n### Targeted minus matched Hits@1 for each method\n\n"
    text += table(effects_summary, ["method", "difference", "low", "high"])
    text += ("\n\n[Arm-level metrics](arm-means.csv) · [All paired effects](paired-effects.csv) · "
             "[Graph audit](graph-audit.csv) · [Gap plot](paired-gap.pdf)\n\n")
    text += "## Frozen general-rule groundings\n\n"
    text += table(ground_rows, list(ground_rows[0])) + "\n\n"
    text += (f"Across draws, the mean per-fact loss fraction changed by {pooled_ground['difference']:+.4f} "
             f"for targeted minus matched deletion, with exploratory 95% interval "
             f"[{pooled_ground['low']:+.4f}, {pooled_ground['high']:+.4f}]. "
             f"The denominator includes {pooled_ground['n_original_supported']} originally supported facts per draw. "
             "All retained groundings were verified against independent native enumeration on the modified graphs.\n\n"
             "Fixed-catalog ranking responses also reflect native frequency tie breaking. Matching relation totals leaves "
             "local degree, particular endpoints and paths free to change. The intervention cannot identify independent "
             "mediating effects of those variables on either model.\n\n"
             "[Grounding counts](grounding-summary.csv) · [Grounding loss plot](grounding-loss.pdf)\n")
    gap = outcomes[-1]
    if gap["low"] <= 0 <= gap["high"]:
        text += ("\n## Interpretation\n\n"
                 "The interval for the primary change in the ComplEx–AnyBURL gap includes zero. "
                 "The comparison leaves the relative Hits@1 advantage uncertain. ")
        if not evidence and all(row["difference"] < 0 for row in ground_rows):
            text += ("Relation-matched random removal erased a larger share of general-rule body "
                     "groundings in every draw. Local targeting therefore cannot be used as a proxy "
                     "for stronger removal of rule evidence in this design. ")
        all_lost = sum(row["targeted_all"] + row["matched_all"] for row in ground_rows)
        evaluated = 2 * sum(row["n_original_supported"] for row in ground_rows)
        text += (f"Across the {evaluated:,} originally supported fact-by-arm-by-draw observations, "
                 f"{all_lost:,} lost every general-rule grounding. These observations reuse the same "
                 "benchmark facts across draws and arms.\n")
        if not evidence:
            text += ("A replication with an intervention defined by training rule-body edges "
                     "would test sensitivity to evidence more directly.\n")
    if evidence:
        gates = [dict(draw=i, **d["intervention"]["training_audit"]) for i, d in enumerate(declarations, 1)]
        write_csv(output / "training-gates.csv", gates)
        objective = ("The targeted arm chose edges by their marginal impact on surviving training groundings."
                     if greedy else "The targeted arm removed high-scoring training rule-body edges.")
        intro = ("# Direct rule-body deletion on CoDEx-S\n\n" + objective + " The control "
                 "removed the same count in every stratum of relation, head degree bin, and tail "
                 "degree bin. Neither validation nor test facts entered the scoring or audit.\n\n"
                 "## Training-only intervention check\n\n"
                 + table(gates, ["draw", "n_facts", "n_supported", "targeted", "matched", "difference"])
                 + "\nThe declared gate was a five percentage point increase in mean per-fact "
                   "grounding loss on disjoint audit probes. The table uses fractions.\n\n")
        text = intro + text.split("\n\n", 1)[1]
    (output / "report.md").write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draws", type=Path, nargs=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", action="store_true")
    parser.add_argument("--greedy", action="store_true")
    args = parser.parse_args()
    if args.greedy and not args.evidence:
        parser.error("--greedy requires --evidence")
    build(args.draws, args.output, evidence=args.evidence, greedy=args.greedy)


if __name__ == "__main__":
    main()
