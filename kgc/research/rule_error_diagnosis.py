"""Separate rule-confidence and aggregation interventions on frozen CoDEx-S candidates."""
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from ..data import load_dataset
from ..evaluation import FilterIndex, queries
from ..io import digest, triple_digest, write_csv, write_json
from .evidence_advantage import FactBootstrap, comparison, pct, ci, points, table
from .evidence_inference import FROZEN, checked_saved, native_rule_info, query_rows, top
from .families import AuditedRules
from .runner import load_rows, read, save_rows

OUTPUT = Path("artifacts/rule-error-diagnosis")
PREVIOUS = Path("artifacts/evidence-advantage")
# Unseen predictions are added to the denominator. Optional family multipliers
# shrink one type without altering the set of applicable rules or candidates.
NATIVE = (5, 1., 1.)
CONFIDENCE_SETTINGS = [(s, b, c) for s in (5, 20, 50)
                       for b, c in ((1., 1.), (.7, 1.), (1., .7))]
VARIANTS = ("native", "reweighted maxplus", "native confidence + noisy-or", "reweighted + noisy-or")


def name(setting):
    unseen, general, constants = setting
    return f"unseen={unseen}, B × {general:g}, Uc/Ud × {constants:g}"


def confidence_tables(backend):
    info = native_rule_info(backend)
    counts = np.empty((len(backend.rules), 2), dtype=np.float64)
    families = np.empty(len(backend.rules), dtype=np.uint8)
    family_ids = {"B": 0, "Uc": 1, "Ud": 2, "Z": 3}
    for i in range(len(backend.rules)):
        rule = info(i)
        counts[i] = rule["support"], rule["predictions"]
        families[i] = family_ids[rule["family"]]
    # The original zero-body prior stays fixed in every intervention.
    def scores(setting):
        unseen, b, c = setting
        penalty = np.where(families == 3, 5, unseen)
        return (counts[:, 0] / (counts[:, 1] + penalty)) * np.array([b, c, .1 * c, .01])[families]
    return {s: scores(s) for s in CONFIDENCE_SETTINGS}, families, counts[:, 0]


def negative_index(dataset, split):
    index = FilterIndex(getattr(dataset, split + "_negatives"))
    return index.answers


def masked_groups(qs):
    grouped = defaultdict(list)
    for i, q in enumerate(qs):
        grouped[q.model_input].append((i, q))
    return grouped


def native_answers(backend, masked, native_scores):
    pred = backend.predict(masked)
    ids = backend.qa.get_rules(as_string=False)[0] if pred.candidates else []
    if len(ids) != len(pred.candidates) or any(not rule_ids for rule_ids in ids):
        raise ValueError("Native candidate and rule-ID attribution mismatch")
    if not np.array_equal(native_scores[[r[0] for r in ids]], [s for _, s in pred.candidates]):
        raise ValueError("Reconstructed rule confidence disagrees with native score")
    return pred.candidates, ids


def rank_competitors(candidates, ids, native_scores, revised_scores, frequency, entity_index):
    """Rank the identical candidate inventory under three scoring changes."""
    if not ids:
        return [[], [], []]
    # The fallback mirrors PyClause frequency and then native entity-ID order.
    tiebreak = [(frequency[e], -entity_index[e]) for e, _ in candidates]
    rules = [np.asarray(x) for x in ids]
    recalibrated = [tuple(sorted(revised_scores[x], reverse=True)) for x in rules]
    n = len(candidates)
    revised = sorted(range(n), key=lambda i: (recalibrated[i], tiebreak[i]), reverse=True)
    flat = np.concatenate(rules)
    start = np.cumsum([0] + [len(r) for r in rules[:-1]])
    native_votes = np.add.reduceat(-np.log1p(-native_scores[flat]), start)
    revised_votes = np.add.reduceat(-np.log1p(-revised_scores[flat]), start)
    pooling = [sorted(range(n), key=lambda i: (values[i], tiebreak[i]), reverse=True)
               for values in (native_votes, revised_votes)]
    return [[candidates[i][0] for i in order] for order in (revised, *pooling)]


def pair_score(gold_ids, negative_ids, scores):
    a = max(scores[gold_ids], default=0.)
    b = max(scores[negative_ids], default=0.)
    return int(a > b) + .5 * int(a == b)


def replay(dataset):
    folder = FROZEN / "evaluations/all"
    path = FROZEN / "subsets/all.rules"
    prior = checked_saved(dataset, folder)
    metrics = read(folder / "metrics.json")
    mining = read(FROZEN / "mining/training.json")
    if (metrics["subset_sha256"] != digest(path)
            or mining["training_graph_sha256"] != triple_digest(dataset.graph.triples)):
        raise ValueError("Frozen inventory or training graph mismatch")
    backend = AuditedRules(dataset.graph, path, certify_support=True, qa_options={"collect_rules": True},
                          retain_catalog_metadata=False)
    if (not backend.certify_support or backend.effective_loader_options != metrics["effective_loader_options"]
            or {**backend.effective_qa_options, "collect_rules": False} != metrics["effective_qa_options"]):
        raise ValueError("Native options differ from frozen evaluation")
    tables, families, support = confidence_tables(backend)
    native = tables[NATIVE]
    entity_index = backend.loader.get_entity_index()
    frequency = Counter(e for h, _, t in dataset.graph.triples for e in (h, t))
    train = FilterIndex(dataset.graph.triples)
    output = {}
    for split, qs, official in query_rows(dataset):
        print(f"{split}: applying frozen rules", flush=True)
        negative = negative_index(dataset, split)
        by_query = masked_groups(qs)
        predictions, paired = [None] * len(qs), []
        for index, (masked, siblings) in enumerate(by_query.items(), 1):
            candidates, ids = native_answers(backend, masked, native)
            native_order = [e for e, _ in candidates]
            by_candidate = dict(zip(native_order, ids))
            # Candidate generation uses only the masked input. Verified negatives
            # determine the diagnostic comparison after the backend call.
            verified = negative.get(masked, set())
            hard_negative = next((e for e in native_order if e in verified), None)
            if split == "test":
                alternatives = rank_competitors(candidates, ids, native, tables[selected], frequency, entity_index)
                orders = [native_order, *alternatives]
                if any(set(order) != set(native_order) for order in orders):
                    raise ValueError("A counterfactual changed the candidate set")
            for i, q in siblings:
                if split == "test":
                    if candidates != [tuple(pair) for pair in prior[i]["returned_candidates"]]:
                        raise ValueError(f"Candidate replay mismatch: {q.query_id}")
                    blocked = official.alternatives(q)
                    filtered_tops = [next((e for e in order if e not in blocked), None) for order in orders]
                    live_tops = [next((e for e in order if e not in train.answers[masked]), None) for order in orders]
                    if filtered_tops[0] != top(prior[i]):
                        raise ValueError(f"Benchmark rank replay mismatch: {q.query_id}")
                    predictions[i] = dict(query_id=q.query_id, fact=i // 2, gold=q.answer,
                                          gold_generated=q.answer in by_candidate,
                                          official_tops=filtered_tops, train_only_tops=live_tops,
                                          verified_negative_top=filtered_tops[0] in verified,
                                          candidate_count=len(native_order), head=q.triple[0], relation=q.triple[1],
                                          tail=q.triple[2], direction=q.direction)
                # Restrict the reliability comparison to cases with two supported
                # choices sharing the same masked query and known opposite labels.
                if hard_negative is None or q.answer not in by_candidate:
                    continue
                a_ids, b_ids = by_candidate[q.answer], by_candidate[hard_negative]
                row = dict(query_id=q.query_id, fact=i // 2, gold=q.answer, negative=hard_negative,
                           native_gold=float(native[a_ids[0]]), native_negative=float(native[b_ids[0]]),
                           gold_family=int(families[a_ids[0]]), negative_family=int(families[b_ids[0]]),
                           gold_support=int(support[a_ids[0]]), negative_support=int(support[b_ids[0]]))
                settings = list(tables) if split == "valid" else [NATIVE, selected]
                row["pair_scores"] = [pair_score(a_ids, b_ids, tables[s]) for s in settings]
                paired.append(row)
            if index % 400 == 0:
                print(f"{split}: {index}/{len(by_query)} masked inputs", flush=True)
        if split == "valid":
            performances = np.array([r["pair_scores"] for r in paired]).mean(axis=0)
            # Select a genuine confidence intervention for the test factorial.
            # The native setting is the independent control in every comparison.
            best = 1 + int(np.argmax(performances[1:]))
            selected = list(tables)[best]
            output["validation"] = [dict(setting=name(s), agreement=float(rate), eligible_pairs=len(paired),
                                         selected=s == selected) for s, rate in zip(tables, performances)]
            output["selected"] = name(selected)
            print(f"Validation-selected confidence intervention: {name(selected)}", flush=True)
        else:
            output.update(predictions=predictions, pairs=paired)
    output["sources"] = {"rule_sha256": digest(path), "saved_test_sha256": digest(folder / "queries.json.gz"),
                         "splits": dataset.provenance["sha256"]}
    return output


def summarize(replayed, earlier):
    rows = replayed["predictions"]
    pairs = replayed["pairs"]
    n = len(rows)
    bootstrap = FactBootstrap([r["fact"] for r in rows])
    generated = np.array([r["gold_generated"] for r in rows])
    all_queries = np.ones(n, dtype=bool)
    verified = np.array([r["verified_negative_top"] for r in rows])
    gold = np.array([r["gold"] for r in rows])[:, None]
    official = (np.array([r["official_tops"] for r in rows], dtype=object) == gold).astype(int)
    train_only = (np.array([r["train_only_tops"] for r in rows], dtype=object) == gold).astype(int)
    native_errors = official[:, 0] == 0
    misranks = native_errors & generated
    earlier_index = {r["query_id"]: r for r in earlier}
    if set(earlier_index) != {rows[i]["query_id"] for i in np.flatnonzero(misranks)}:
        raise ValueError("Earlier diagnosis and replay contain different generated misses")
    if np.any(official[~generated]) or np.any(verified & ~native_errors):
        raise ValueError("An unavailable answer won or a verified false candidate counted as correct")

    comparisons = []
    for endpoint, scores in (("Benchmark", official), ("Training-only filter", train_only)):
        for j, label in enumerate(VARIANTS):
            stats = bootstrap.paired(scores[:, j], scores[:, 0], all_queries)
            comparisons.append(dict(endpoint=endpoint, group=label,
                                    rescued_official_misranks=int(official[misranks, j].sum()), **stats))
    only_weights = misranks & (official[:, 1] == 1) & (official[:, 2] == 0)
    only_aggregate = misranks & (official[:, 1] == 0) & (official[:, 2] == 1)
    either = misranks & (official[:, 1] == 1) & (official[:, 2] == 1)
    combined_only = misranks & (official[:, 1] == 0) & (official[:, 2] == 0) & (official[:, 3] == 1)
    neither = misranks & (official[:, 1:].sum(axis=1) == 0)
    masks = {"Reweighting only among single changes": only_weights,
             "Aggregation only among single changes": only_aggregate, "Both single changes recover it": either,
             "Only the combined change": combined_only, "None of the changes": neither}
    rescued = []
    for label, mask in masks.items():
        lower, upper = bootstrap.interval(bootstrap.rates(mask, misranks))
        rescued.append(dict(group=label, count=int(mask.sum()), total=int(misranks.sum()),
                            rate=float(mask.sum() / misranks.sum()), lo=lower, hi=upper))
    if sum(r["count"] for r in rescued) != int(misranks.sum()):
        raise ValueError("Recovery categories do not partition the generated misses")

    pair_mask = np.zeros(n, dtype=bool)
    pair_values = np.zeros((n, 2))
    by_id = {row["query_id"]: i for i, row in enumerate(rows)}
    for pair in pairs:
        i = by_id[pair["query_id"]]
        pair_mask[i] = True
        pair_values[i] = pair["pair_scores"]
    diff = pair_values[:, 1] - pair_values[:, 0]
    lo, hi = bootstrap.interval(bootstrap.rates(diff, pair_mask))
    pair_report = dict(n=int(pair_mask.sum()), facts=len(set(bootstrap.facts[pair_mask])),
                       native=float(pair_values[pair_mask, 0].mean()), reweighted=float(pair_values[pair_mask, 1].mean()),
                       delta=float(diff[pair_mask].mean()), lo=lo, hi=hi,
                       false_scored_higher=sum(p["native_negative"] > p["native_gold"] for p in pairs),
                       equal=sum(p["native_negative"] == p["native_gold"] for p in pairs))
    verified_misranks = [earlier_index[r["query_id"]] for r, v in zip(rows, verified & misranks) if v]
    if any(d["candidates"][1]["entity"] != rows[by_id[d["query_id"]]]["official_tops"][0]
           for d in verified_misranks):
        raise ValueError("Earlier witnesses differ from the verified-negative top")
    rule_counts = Counter(d["candidates"][1]["lead"]["expression"] for d in verified_misranks)
    false_leads = [d["candidates"][1]["lead"] for d in verified_misranks]
    native_ordering = Counter(d["ordering"] for d in earlier)
    identified = dict(queries=n, n_native_errors=int(native_errors.sum()),
                      n_missing=int((native_errors & ~generated).sum()),
                      n_misranked=int(misranks.sum()), n_verified_false=int(verified.sum()),
                      n_verified_false_misranked=len(verified_misranks), n_distinct_false_leads=len(rule_counts),
                      verified_leads_high=float(sum(r["score"] >= .5 for r in false_leads)),
                      verified_leads_by_family=dict(Counter(r["family"] for r in false_leads)),
                      verified_lead_rules_by_frequency=dict(rule_counts.most_common()),
                      ordering=dict(native_ordering))
    sample_masks = [
        ("A strong rule supports a verified false answer", verified & misranks),
        ("Changing aggregation alone picks the correct answer", only_aggregate),
        ("Changing rule weights alone picks the correct answer", only_weights),
    ]
    cases = []
    for title, mask in sample_masks:
        eligible = np.flatnonzero(mask)
        if not len(eligible):
            continue
        # Prefer verified errors and distinct relations. Use native witness
        # strength and query order as deterministic tie-breakers.
        i = max(eligible, key=lambda j: (bool(verified[j]),
                rows[j]["relation"] not in {s["query"]["relation"] for s in cases},
                earlier_index[rows[j]["query_id"]]["candidates"][1]["native_score"], -int(j)))
        row = rows[i]
        annotation = earlier_index[row["query_id"]]
        if any(c["entity"] != e for c, e in zip(annotation["candidates"], (row["gold"], row["official_tops"][0]))):
            raise ValueError("Case witness does not match the frozen candidates")
        cases.append(dict(title=title, query=row, **annotation))
    return comparisons, rescued, pair_report, identified, cases


def render_cases(cases, labels):
    def label(token):
        return f"{labels.get(token, token)} ({token})" if token else "abstained"

    lines = []
    for case in cases:
        row = case["query"]
        h, r, t = (label(row[k]) for k in ("head", "relation", "tail"))
        query = f"?, {r}, {t}" if row["direction"] == "head" else f"{h}, {r}, ?"
        status = "The benchmark independently verifies the native top as false." if row["verified_negative_top"] else (
            "The native top misses this target. The hard-negative file does not label that candidate.")
        lines += [f"### {case['title']}", "", f"`{row['query_id']}` · ({query}). {status}", "",
                  f"The held-out answer is **{label(row['gold'])}**.", "",
                  table(["Ranking", "First answer"], [[v, label(e)] for v, e in zip(VARIANTS, row["official_tops"])]), ""]
        for candidate in case["candidates"]:
            rule = candidate["lead"]
            sampled = next((w["groundings"][0] for w in candidate["witnesses"]
                            if w["expression"] == rule["expression"] and w["groundings"]), None)
            witness = " · ".join("(" + ", ".join(map(label, triple)) + ")" for triple in sampled) if sampled else ""
            lines += [f"- **{label(candidate['entity'])}** had leading score {candidate['native_score']:.3f}. "
                      f"`{rule['expression']}` had {rule['support']} supported training predictions."
                      + (f" Training witness {witness}." if witness else "")]
        lines += [""]
    return lines


def report(replayed, labels):
    source = PREVIOUS / "misrank-diagnosis.json.gz"
    earlier = load_rows(source)
    comparisons, rescued, pair, counts, cases = summarize(replayed, earlier)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    verified = counts["n_verified_false_misranked"]
    native = comparisons[0]
    weights, pooling, joint = comparisons[1:4]
    order = counts["ordering"]
    write_csv(OUTPUT / "ranking-comparisons.csv", comparisons)
    write_csv(OUTPUT / "misrank-recovery.csv", rescued)
    write_csv(OUTPUT / "verified-negative-pairs.csv", replayed["pairs"])
    write_csv(OUTPUT / "validation-confidence-settings.csv", replayed["validation"])
    save_rows(OUTPUT / "per-query-rankings.json.gz", replayed["predictions"])
    write_json(OUTPUT / "results.json", dict(comparisons=comparisons, recovery=rescued, verified_pair=pair,
               counts=counts, examples=cases, sources={**replayed["sources"], "earlier_diagnosis_sha256": digest(source)},
               selected_confidence_settings=replayed["selected"]))
    text = [
        "# Why does AnyBURL put the wrong answer first?",
        "",
        "**Both mechanisms show up.** Strong rules sometimes support answers the benchmark verifies as false. "
        "Changing how AnyBURL combines those same rule scores also recovers some answers. "
        "The original ranking has the highest overall accuracy among the tested variants.",
        "",
        f"AnyBURL missed {counts['n_native_errors']:,} of {counts['queries']:,} CoDEx-S queries. It generated the correct "
        f"candidate in {counts['n_misranked']:,} of those misses and failed to generate it in {counts['n_missing']}. "
        "So the main bottleneck is choosing among generated candidates.",
        "",
        f"In {order['higher leading score']:,} generated misses, the wrong candidate had a higher confidence on its "
        f"strongest rule. Later rule scores broke an initial tie in {order['later score breaks tie']:,} cases. "
        f"The full score sequences tied once. This comparison describes how the native ranking made its choice.",
        "",
        f"We also found {verified:,} such misses where the first answer is explicitly verified false. In "
        f"{int(counts['verified_leads_high']):,} of those, the leading rule still had adjusted confidence of at least .50. "
        f"The verified false answers were led by {counts['n_distinct_false_leads']:,} distinct rules. "
        "These cases directly show that reliable-looking rules can be wrong on new facts.",
        "",
        "## Two changes to the same candidate lists",
        "",
        f"**Rule confidence.** We kept maxplus order and changed the individual confidences. "
        f"Compared with native `{name(NATIVE)}`, the selected setting was `{replayed['selected']}`. "
        "We chose it on validation by asking how often the best rule score favored the known true answer over the "
        "highest native-ranked verified false answer for the same masked query. Score ties receive half credit. "
        "Both candidates had to be generated. [Validation settings](validation-confidence-settings.csv)",
        "",
        "**Candidate aggregation.** We kept the original individual confidences and replaced maxplus with noisy-or. "
        "Maxplus compares candidates’ rule scores from highest to lowest. Noisy-or pools all supporting rule scores, "
        "which can give repeated or correlated rules extra influence. The fourth variant combines both changes. "
        "The frozen native replay matched all saved candidate lists in their exact order. "
        "Every variant reranks precisely the same candidates. The evaluator applies the benchmark filter afterward.",
        "",
        comparison(comparisons[:4], "Variant Hits@1", "Native Hits@1"),
        "",
        comparison(comparisons[4:], "Variant accuracy", "Native accuracy"),
        "",
        f"The second table keeps the actual top answer after filtering training positives only. Intervals are paired "
        f"95% percentile intervals from 2,500 bootstrap samples of facts, with both directions kept together. "
        f"The native benchmark Hits@1 was {pct(native['left'])}. Compared with it, reweighting changed Hits@1 by "
        f"{points(weights['delta'])} pp {ci(weights)}, pooling changed it by {points(pooling['delta'])} pp {ci(pooling)}, "
        f"and the combined change shifted it by {points(joint['delta'])} pp {ci(joint)}.",
        "",
        "## Which generated misses changed?",
        "",
        table(["Change that recovered the answer", "Queries", "Share (95% CI)"], [
            [r["group"], f"{r['count']:,} / {r['total']:,}",
             f"{pct(r['rate'])} [{pct(r['lo'])}, {pct(r['hi'])}]"] for r in rescued]),
        "",
        "These counts measure sensitivity to the specific interventions. The paired accuracy table shows new errors "
        "elsewhere as native-only successes. "
        "Failures that remain can reflect the rules, the ranking policy, or both.",
        "",
        "## Check against verified false answers",
        "",
        f"On {pair['n']:,} test comparisons from {pair['facts']:,} facts, the native leading rule scored the verified "
        f"false candidate higher in {pair['false_scored_higher']:,} comparisons and tied it in {pair['equal']:,}. "
        f"Giving ties half credit, the best rule scores favored the correct candidate {pct(pair['native'])} of the "
        f"time with native confidences and {pct(pair['reweighted'])} with reweighting "
        f"({points(pair['delta'])} pp {ci(pair)}). This comparison targets the hardest available verified rival under "
        "the original ranker. It estimates performance on that selected cohort. Many other benchmark misses lack "
        "independent false labels. [Per-query verified comparisons](verified-negative-pairs.csv)",
        "",
        "## Concrete queries",
        "",
        *render_cases(cases, labels),
        "## Scope",
        "",
        "The experiment separates changes to confidence from changes to aggregation while holding rule applicability "
        "fixed. The two mechanisms can act on the same query, and a tested reranker’s gains and losses cannot "
        "assign a unique cause to every miss. This is a follow-up on the previously examined CoDEx-S test split.",
        "",
        "Reproduce from the project root with the existing frozen rules, saved rankings, and the English labels "
        "cached by the query evidence analysis.",
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .backend-venv/bin/python -m kgc.research.rule_error_diagnosis",
        "```",
    ]
    (OUTPUT / "report.md").write_text("\n".join(text) + "\n")
    print(f"Saved {OUTPUT / 'report.md'}", flush=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-cache", type=Path, help="Generate the report from a completed frozen replay")
    args = parser.parse_args()
    if args.replay_cache:
        results = load_rows(args.replay_cache)
    else:
        results = replay(load_dataset("data/codex-s"))
    metadata = Path("runs/evidence-advantage")
    labels = {k: v["label"] for name in ("entities", "relations")
              for k, v in read(metadata / f"{name}.json").items()}
    report(results, labels)


if __name__ == "__main__":
    main()
