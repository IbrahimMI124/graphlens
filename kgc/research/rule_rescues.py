"""Compare ComplEx and AnyBURL on supported errors and strong rule successes."""
from pathlib import Path

import numpy as np
import pandas as pd

from ..data import load_dataset
from ..evaluation import queries
from ..io import digest, write_csv, write_json
from .evidence_advantage import FactBootstrap, comparison, label_map, pct, points, ci, table
from .evidence_inference import FROZEN, NEURAL, checked_saved, groundings, native_rule_info, top
from .families import AuditedRules
from .rule_error_diagnosis import OUTPUT as ERROR_OUTPUT, PREVIOUS
from .runner import load_rows, read
from .structure_cases import inspect_witnesses


OUTPUT = Path("artifacts/rule-rescues")
STRONG = .50
CLOSE = .05


def assemble(dataset):
    seed = read(NEURAL / "final-summary.json")["strongest_checkpoint_by_validation"]["seed"]
    columns = ["query_id", "known", "relation", "direction", "degree", "agreement", "all_near"]
    profiles_path = PREVIOUS / "test-evidence-profiles.csv"
    profiles = pd.read_csv(profiles_path, usecols=columns)
    native = checked_saved(dataset, FROZEN / "evaluations/all")
    general = checked_saved(dataset, FROZEN / "evaluations/general")
    diagnosis_path = PREVIOUS / "misrank-diagnosis.json.gz"
    diagnosis = {d["query_id"]: d for d in load_rows(diagnosis_path)}
    replay_path = ERROR_OUTPUT / "per-query-rankings.json.gz"
    replay = load_rows(replay_path)
    neural_paths = [NEURAL / "final" / f"seed-{i}" for i in (0, 1, 2)]
    neural = [checked_saved(dataset, p, "test-queries.json.gz") for p in neural_paths]
    official = list(queries(dataset.test))
    if len(replay) != len(official):
        raise ValueError("Frozen intervention and comparison cover different ranges")
    rows = []
    for i, q in enumerate(official):
        a, g, r = native[i], general[i], replay[i]
        selected = neural[seed][i]
        wrong = top(a)
        is_misrank = not a["hits1"] and a["true_returned"]
        d = diagnosis.get(q.query_id)
        if ((r["query_id"], r["gold"], r["gold_generated"], r["official_tops"][0]) !=
                (q.query_id, q.answer, a["true_returned"], wrong) or is_misrank != bool(d)):
            raise ValueError(f"Frozen error diagnosis differs for {q.query_id}")
        row = dict(query_id=q.query_id, fact=i // 2, head=q.triple[0], tail=q.triple[2], gold=q.answer,
                   anyburl_top=wrong, complex_top=top(selected), anyburl_hit=a["hits1"],
                   complex_hit=selected["hits1"], complex_rank=selected["rank"],
                   general_hit=g["hits1"], general_gold_score=g["score"], gold_generated=a["true_returned"],
                   verified_false_top=r["verified_negative_top"],
                   same_wrong_top=bool(wrong and not a["hits1"] and not selected["hits1"] and top(selected) == wrong))
        if a["top_predictions"] and not a["hits1"]:
            row["wrong_score"] = a["top_predictions"][0][1]
        for j, predictions in enumerate(neural):
            row[f"complex_hit_seed_{j}"] = predictions[i]["hits1"]
            row[f"complex_top_seed_{j}"] = top(predictions[i])
        if d:
            gold, wrong_candidate = d["candidates"]
            if (gold["entity"], wrong_candidate["entity"], wrong_candidate["native_score"]) != (
                    q.answer, wrong, row["wrong_score"]):
                raise ValueError(f"Candidate evidence mismatch: {q.query_id}")
            row.update(gold_score=gold["native_score"], score_gap=row["wrong_score"] - gold["native_score"],
                       winning_rule_family=wrong_candidate["lead"]["family"],
                       winning_rule_support=wrong_candidate["lead"]["support"],
                       winning_rule=wrong_candidate["lead"]["expression"],
                       gold_rule=gold["lead"]["expression"],
                       gold_rule_family=gold["lead"]["family"])
        rows.append(row)
    outcomes = pd.DataFrame(rows)
    frame = outcomes.merge(profiles, on="query_id", validate="one_to_one")
    if (len(frame) != len(official)
            or any((r.known, r.relation, r.direction) != (q.model_input.known, q.model_input.relation, q.direction)
                   for r, q in zip(frame.itertuples(), official))):
        raise ValueError("Evidence profiles differ from the official masked queries")
    frame["different_miss"] = ~(frame.same_wrong_top | frame.complex_hit.astype(bool))
    paths = [profiles_path, diagnosis_path, replay_path, FROZEN / "evaluations/all/queries.json.gz",
             FROZEN / "evaluations/general/queries.json.gz", FROZEN / "subsets/general.rules",
             NEURAL / "final-summary.json", *[p / "test-queries.json.gz" for p in neural_paths]]
    return frame, diagnosis, seed, {str(p): digest(p) for p in paths}


def rescue_table(frame, boot, groups, seed=None):
    hit = frame["complex_hit" if seed is None else f"complex_hit_seed_{seed}"].astype(bool)
    top_key = "complex_top" if seed is None else f"complex_top_seed_{seed}"
    same = ((frame[top_key] == frame.anyburl_top) & ~hit).to_numpy()
    rows = []
    for name, mask in groups:
        n = int(mask.sum())
        lo, hi = boot.interval(boot.rates(hit, mask))
        same_lo, same_hi = boot.interval(boot.rates(same, mask))
        recovered = int(hit[mask].sum())
        same_wrong = int(same[mask].sum())
        rows.append(dict(group=name, n=n, facts=int(frame.loc[mask, "fact"].nunique()), recovered=recovered,
                         same_wrong=same_wrong, different_miss=n - recovered - same_wrong,
                         rescue_rate=recovered / n if n else None, lo=lo, hi=hi,
                         same_rate=same_wrong / n if n else None, same_lo=same_lo, same_hi=same_hi))
    return rows


def matched_rescue(frame, boot, cohort, first, second, label):
    """Contrast rescue rates within shared relation/direction/degree strata."""
    degree_bin = np.floor(np.log2(frame.degree.clip(lower=1))).astype(int)
    grouped = frame.groupby(["relation", "direction", degree_bin]).indices
    y = frame.complex_hit.to_numpy()
    estimates, draws, weights, counts = [], [], [], []
    for ids in grouped.values():
        a = np.zeros(len(frame), dtype=bool)
        b = a.copy()
        a[ids] = (cohort & first).to_numpy()[ids]
        b[ids] = (cohort & second).to_numpy()[ids]
        na, nb = int(a.sum()), int(b.sum())
        if not na or not nb:
            continue
        counts.append((na, nb))
        weights.append(min(na, nb))
        estimates.append((y[a].mean(), y[b].mean()))
        draws.append(boot.rates(y, a) - boot.rates(y, b))
    if not weights:
        raise ValueError("No common strata for comparative diagnosis")
    draws, weights = np.asarray(draws), np.asarray(weights)
    present_weight = np.isfinite(draws).T @ weights
    pooled = np.full(len(present_weight), np.nan)
    np.divide(np.nansum(draws * weights[:, None], axis=0), present_weight, out=pooled, where=present_weight > 0)
    lo, hi = boot.interval(pooled)
    a, b = np.average(estimates, weights=weights, axis=0)
    na, nb = np.sum(counts, axis=0)
    return dict(group=label, strata=len(weights), first_n=int(na), second_n=int(nb), first=float(a),
                second=float(b), delta=float(a - b), lo=lo, hi=hi)


def case_examples(dataset, frame, diagnosis, strong, rule_only, labels):
    def named(token):
        return f"{labels.get(token, token)} ({token})"

    train = set(dataset.graph.triples)

    def facts(candidate):
        expression = candidate["lead"]["expression"]
        strongest = [w for w in candidate["witnesses"] if w["expression"] == expression]
        checked = inspect_witnesses(strongest, train, train, tuple(candidate["triple"]))
        if not checked:
            raise ValueError(f"Example lacks a witness for its leading rule: {candidate['triple']}")
        return expression, " · ".join(
            "(" + ", ".join(named(t) for t in triple) + ")" for triple in checked[0]["grounding"])

    def describe(row, title):
        h, r, t = (named(row[key]) for key in ("head", "relation", "tail"))
        masked = f"?, {r}, {t}" if row.direction == "head" else f"{h}, {r}, ?"
        truth = named(row.gold)
        return [f"### {title}", "", f"`{row.query_id}` · ({masked}). The held-out answer is **{truth}**. "
                f"AnyBURL puts **{named(row.anyburl_top)}** first and ComplEx puts **{named(row.complex_top)}** first.", ""]

    cohort = frame[strong & frame.verified_false_top]
    lines, records = [], []
    for title, condition in (
        ("ComplEx avoids a verified false answer", cohort.complex_hit == 1),
        ("Both models choose the same verified false answer", cohort.same_wrong_top),
        ("Both models miss and choose different answers", cohort.different_miss),
    ):
        group = cohort[condition]
        if group.empty:
            continue
        row = group.sort_values(["wrong_score", "query_id"], ascending=[False, True]).iloc[0]
        d = diagnosis[row.query_id]
        lines += describe(row, title)
        lines += ["The benchmark explicitly labels AnyBURL’s top answer false.", ""]
        for c in d["candidates"]:
            expression, body = facts(c)
            lines += [f"- **{named(c['entity'])}** had leading score {c['native_score']:.3f}. "
                      f"`{expression}`. Training witness {body}."]
        lines.append("")
        records.append(d)

    options = frame[rule_only & frame.general_hit.astype(bool)].sort_values(
        ["general_gold_score", "query_id"], ascending=[False, True])
    row = options.iloc[0]
    q = next(q for q in queries([dataset.test[int(row.fact)]]) if q.direction == row.direction)
    backend = AuditedRules(dataset.graph, FROZEN / "subsets/general.rules", certify_support=True,
                           qa_options={"collect_rules": True}, retain_catalog_metadata=False)
    pred = backend.predict(q.model_input)
    rule_ids = dict(zip((e for e, _ in pred.candidates), backend.qa.get_rules(as_string=False)[0]))[q.answer]
    info = native_rule_info(backend)
    best = info(rule_ids[0])
    target = q.model_input.triple(q.answer)
    if best["score"] != row.general_gold_score or best["family"] != "B":
        raise ValueError("The positive witness differs from the saved general support")
    found = groundings(backend, [target])[target][rule_ids[0]]
    verified = inspect_witnesses([dict(**best, groundings=found[:1])], backend.training_edges,
                                 backend.training_edges, target)
    proof = verified[0]["grounding"]
    body = " · ".join("(" + ", ".join(named(t) for t in triple) + ")" for triple in proof)
    lines += describe(row, "A general rule supports AnyBURL’s correct answer")
    lines += [f"`{best['expression']}` had a native score of {best['score']:.3f} and "
              f"general rules alone also put the correct answer first. Training witness {body}.", ""]
    records.append(dict(query_id=row.query_id, candidate=row.gold, competing_complex_answer=row.complex_top,
                        rule=best, grounding=proof))
    return lines, records


def run():
    OUTPUT.mkdir(exist_ok=True, parents=True)
    dataset = load_dataset("data/codex-s")
    frame, diagnosis, seed, sources = assemble(dataset)
    boot = FactBootstrap(frame.fact)
    miss = frame.anyburl_hit == 0
    misrank = miss & frame.gold_generated
    strong = miss & (frame.wrong_score >= STRONG)
    if (strong & ~misrank).any():
        raise ValueError("Strongly supported errors include an unavailable gold answer")
    verified = frame.verified_false_top
    close = frame.score_gap <= CLOSE + 1e-12
    few = frame.all_near.between(1, 4)
    crowded = frame.all_near >= 5
    general_gold = frame.general_gold_score >= STRONG
    rule_only = general_gold & frame.anyburl_hit.astype(bool) & (frame.complex_hit == 0)
    main_groups = [("All generated misses", misrank), ("Leading wrong rule ≥ .50", strong),
                   ("Leading wrong rule ≥ .75", strong & (frame.wrong_score >= .75)),
                   ("Leading wrong rule < .50", misrank & ~strong),
                   ("Leading wrong rule ≥ .50, verified false", strong & verified)]
    conditions = [
        ("Wrong–correct leading score gap ≤ .05", close),
        ("Wrong–correct leading score gap > .05", ~close),
        ("Wrong answer led by a general rule", frame.winning_rule_family == "B"),
        ("Wrong answer led by a constant rule", frame.winning_rule_family.isin(["Uc", "Ud"])),
        ("One near leader from all rules", frame.all_near == 1),
        ("Two to four near leaders from all rules", frame.all_near.between(2, 4)),
        ("Five or more near leaders from all rules", crowded),
        ("General and constant train-only tops agree", frame.agreement == "agree"),
        ("General and constant train-only tops disagree", frame.agreement == "disagree"),
    ]
    main = rescue_table(frame, boot, main_groups)
    feature_rows = rescue_table(frame, boot, [(g, strong & m) for g, m in conditions])
    matched = [
        matched_rescue(frame, boot, strong, close, ~close, "Score gap ≤ .05 versus > .05"),
        matched_rescue(frame, boot, strong, few, crowded, "1–4 near leaders versus 5 or more"),
    ]
    reverse = [dict(group=name, **boot.paired(frame.anyburl_hit, frame.complex_hit, mask))
               for name, mask in (("General rule supports gold at ≥ .50", general_gold),
                                  ("General support for gold is weaker or absent", ~general_gold),
                                  ("Strong general support and general rules alone rank gold first",
                                   general_gold & frame.general_hit.astype(bool)))]
    sensitivity = [dict(seed=s, **r) for s in (0, 1, 2)
                   for r in rescue_table(frame, boot, [main_groups[1], main_groups[-1]], seed=s)]
    for basename, rows in (("rescue-outcomes", main), ("rescue-by-evidence", feature_rows),
                           ("matched-contrasts", matched), ("general-rule-comparisons", reverse),
                           ("seed-sensitivity", sensitivity)):
        write_csv(OUTPUT / f"{basename}.csv", rows)
    frame[strong | rule_only].to_csv(OUTPUT / "query-level-outcomes.csv", index=False)
    case_lines, cases = case_examples(dataset, frame, diagnosis, strong, rule_only, label_map())
    write_json(OUTPUT / "results.json", dict(seed=seed, outcomes=main, features=feature_rows,
               matching=matched, reverse=reverse, sensitivity=sensitivity, cases=cases,
               sources=sources, splits=dataset.provenance["sha256"]))
    make_report(seed, main, feature_rows, matched, reverse, case_lines)


def make_report(seed, main, feature_rows, matched, reverse, case_lines):
    def outcomes(rows):
        return table(["Group", "Queries (facts)", "ComplEx correct", "Same wrong top", "Different miss"], [
            [r["group"], f"{r['n']:,} ({r['facts']:,})",
             f"{r['recovered']:,} · {pct(r['rescue_rate'])} [{pct(r['lo'])}, {pct(r['hi'])}]",
             f"{r['same_wrong']:,} · {pct(r['same_rate'])}", f"{r['different_miss']:,}"] for r in rows])

    entire, strong, _, _, verified = main
    close, far = feature_rows[:2]
    matched_gap = matched[0]
    reciprocal = reverse[0]
    text = [
        "# When does ComplEx rescue a strongly supported AnyBURL error?",
        "",
        f"ComplEx recovered **{strong['recovered']:,} of {strong['n']:,}** CoDEx-S errors where AnyBURL’s wrong "
        f"answer had a leading native rule score of at least .50. It picked the same wrong answer in "
        f"**{strong['same_wrong']:,}** cases. Among the {verified['n']} explicitly verified false top answers in "
        f"this group, ComplEx was correct in **{verified['recovered']}**, repeated the same verified false answer "
        f"in **{verified['same_wrong']}**, and missed with a different answer in **{verified['different_miss']}**.",
        "",
        f"**The rule score gap best separated the two groups among the contrasts tested.** ComplEx recovered "
        f"{pct(close['rescue_rate'])} of strong errors when the wrong and correct candidates’ leading scores "
        f"were within .05, and {pct(far['rescue_rate'])} when the gap was larger. After matching on relation, "
        f"direction and known-entity degree, the estimate was {points(matched_gap['delta'])} percentage points "
        f"{ci(matched_gap)}. Both leading scores come from rule evidence. The gap is available once the correct "
        "answer is known.",
        "",
        f"The reverse pattern also occurs. In **{reciprocal['left_only']}** queries, AnyBURL alone was correct "
        "and a strong general rule directly supported the held-out answer. These comparisons describe when the "
        "models differ on this benchmark. They leave the mechanisms inside ComplEx unresolved.",
        "",
        "## Strongly supported AnyBURL errors",
        "",
        outcomes(main),
        "",
        f"All rows use the same {entire['n']:,} generated-miss population or a subset of it. Strong errors use "
        "the highest rule score for AnyBURL’s benchmark-filtered top wrong answer. The instances without a "
        "generated gold answer had no leading score reaching .50. Correctness uses the benchmark-filtered "
        f"rankings. ComplEx seed {seed} was selected by validation MRR in the original study. "
        "Some wrong answers have independent false labels from the hard-negative file. The other misses simply "
        "differ from the benchmark target. The verified cohort is small. Each interval is a pointwise 95% paired "
        "fact-bootstrap interval with 2,500 draws. [Other ComplEx seeds](seed-sensitivity.csv) · "
        "[Query-level results](query-level-outcomes.csv)",
        "",
        "## What distinguishes rescues from shared failures?",
        "",
        outcomes(feature_rows),
        "",
        "A near leader has a native scalar score within .05 of the strongest all-rule candidate after removing "
        "training positives. The score-gap comparison instead uses the two benchmark candidates in the error diagnosis. "
        "Groups can overlap across features.",
        "",
        table(["Within-stratum contrast", "Strata", "Queries first / second", "Adjusted rescue first / second",
               "Difference pp (95% CI)"], [
            [r["group"], r["strata"], f"{r['first_n']} / {r['second_n']}", f"{pct(r['first'])} / {pct(r['second'])}",
             f"{points(r['delta'])} {ci(r)}"] for r in matched]),
        "",
        "Strata match exact relation and direction and the same log₂ degree bin. Each stratum contributes in "
        "proportion to its smaller group. Matched estimates apply to groups with shared strata. The matched "
        "interval for the number of near leaders spans zero.",
        "",
        "## When strong general rules support the correct answer",
        "",
        comparison(reverse, "AnyBURL Hits@1", "ComplEx Hits@1"),
        "",
        "The strongest applicable general rule for the held-out answer must score at least .50. This is "
        "a retrospective test of direct support. The final row further requires that general rules alone ranked the gold first.",
        "",
        "## Worked examples",
        "",
        *case_lines,
        "## Ranking experiment correction",
        "",
        "In the previous recovery table, the eight queries in “Both single changes recover it” were recovered "
        "by either intervention independently. The 7 and 126 rows count queries recovered by exactly one of the two interventions. "
        "The reweighted scores improved the selected true-versus-false matchup from 59.92% to 62.89%. "
        "Full ranking requires beating all eligible rivals, and Hits@1 fell from 34.08% to 32.58%. "
        "[Corrected ranking experiment](../rule-error-diagnosis/report.md)",
        "",
        "Reproduce the analysis with the saved runs and English labels using "
        "`OPENBLAS_NUM_THREADS=1 .backend-venv/bin/python -m kgc.research.rule_rescues`.",
        "",
    ]
    (OUTPUT / "report.md").write_text("\n".join(text))


if __name__ == "__main__":
    run()
