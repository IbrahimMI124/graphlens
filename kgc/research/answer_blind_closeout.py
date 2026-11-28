"""Close out answer-blind model choice on frozen CoDEx-S predictions."""
from pathlib import Path

import numpy as np
import pandas as pd

from ..data import load_dataset
from ..evaluation import queries
from ..io import digest, write_csv, write_json
from .evidence_advantage import FactBootstrap, ci, pct, points, table
from .runner import read

EVIDENCE = Path("artifacts/evidence-advantage")
RESCUES = Path("artifacts/rule-rescues")
OUTPUT = Path("artifacts/answer-blind-closeout")
KEYS = ["known", "relation", "direction"]
PROFILE_COLUMNS = ["query_id", *KEYS, "all_top", "all_count", "all_margin", "complex_top"]
OUTCOME_COLUMNS = ["query_id", "fact", "gold", "complex_new_hits", "all_new_hits", "complex_hits", "all_hits"]
THRESHOLD = .05
CLOSE, WIDE = "close", "wide"


def profiles(split):
    path = EVIDENCE / f"{split}-evidence-profiles.csv"
    p = pd.read_csv(path, usecols=PROFILE_COLUMNS)
    if p.query_id.duplicated().any() or p.complex_top.isna().any():
        raise ValueError(f"Bad masked profile in {path}")
    if (p.all_margin < -1e-12).any() or (p.all_top.notna() != (p.all_count > 0)).any():
        raise ValueError(f"Inconsistent native candidate summary in {path}")
    p["top_answers_differ"] = p.complex_top != p.all_top
    p["gap_group"] = np.where(p.all_margin <= THRESHOLD + 1e-12, CLOSE, WIDE)
    p.loc[p.all_count < 2, "gap_group"] = "fewer than two candidates"
    p.loc[~p.top_answers_differ, "gap_group"] = "models agree"
    return p


def reveal(p, split):
    """Attach correctness only after the declared decision stage for this split."""
    expected = pd.read_csv(EVIDENCE / f"{split}-outcomes.csv", usecols=OUTCOME_COLUMNS)
    rows = p.merge(expected, on="query_id", validate="one_to_one")
    if len(rows) != len(p) or len(rows) != len(expected):
        raise ValueError(f"Unequal evidence and outcomes for {split}")
    for top_key, hits_key in (("all_top", "all_new_hits"), ("complex_top", "complex_new_hits")):
        if not np.array_equal(rows[top_key] == rows.gold, rows[hits_key]):
            raise ValueError(f"Saved train-only outcome differs for {split} {top_key}")
    return rows


def choose_mapping(validation):
    decisions = {}
    summary = []
    for group in (CLOSE, WIDE):
        v = validation.loc[validation.gap_group == group]
        if v.empty:
            raise ValueError(f"Validation has no eligible {group} cases")
        # Use only validation correctness, with ComplEx as the tie rule.
        winner = "AnyBURL" if v.all_new_hits.sum() > v.complex_new_hits.sum() else "ComplEx"
        decisions[group] = winner
        summary.append(dict(group=group, n=len(v), complex_hits=int(v.complex_new_hits.sum()),
                            anyburl_hits=int(v.all_new_hits.sum()), selected=winner))
    return decisions, summary


def lock_choices(validation, p, mapping):
    saved_path = EVIDENCE / "selector-predictions.csv"
    saved = pd.read_csv(saved_path, usecols=["query_id", "controls", "controls + rule evidence", "tops_differ"])
    choices = p.merge(saved, on="query_id", validate="one_to_one")
    if len(choices) != len(p) or len(choices) != len(saved):
        raise ValueError("Saved selectors and masked query profiles do not align")
    if not np.array_equal(choices.top_answers_differ, choices.tops_differ):
        raise ValueError("Saved selectors used a different disagreement boundary")
    for column in ("controls", "controls + rule evidence"):
        if not choices[column].isin(["AnyBURL", "ComplEx"]).all():
            raise ValueError("Unknown model choice")
        if (choices.loc[~choices.top_answers_differ, column] != "ComplEx").any():
            raise ValueError("Saved selectors changed a shared prediction")
    choices["top-two gap"] = choices.gap_group.map(mapping).fillna("ComplEx")
    validation_inputs = set(zip(*(validation[key] for key in KEYS)))
    choices["unseen_masked_input"] = [key not in validation_inputs for key in zip(*(choices[k] for k in KEYS))]
    columns = ["query_id", *KEYS, "all_top", "complex_top", "all_count", "all_margin", "gap_group",
               "unseen_masked_input", "controls", "controls + rule evidence", "top-two gap"]
    choices[columns].to_csv(OUTPUT / "locked-test-choices.csv", index=False)
    return choices


def evaluate(rows, boot):
    results = []
    gap_groups = []
    for endpoint, cn, rn in (("train-only top", "complex_new_hits", "all_new_hits"),
                             ("benchmark filtered", "complex_hits", "all_hits")):
        anyburl, complex_ = rows[rn].to_numpy(), rows[cn].to_numpy()
        hits = {"ComplEx": complex_, "AnyBURL": anyburl}
        for model in ("controls", "controls + rule evidence", "top-two gap"):
            hits[model] = np.where(rows[model] == "AnyBURL", anyburl, complex_)
        scopes = [("all test queries", np.ones(len(rows), dtype=bool)),
                  ("masked input absent from validation", rows.unseen_masked_input)]
        for scope, mask in scopes:
            for left, right in [("AnyBURL", "ComplEx"), ("controls", "ComplEx"),
                                ("controls + rule evidence", "ComplEx"), ("top-two gap", "ComplEx"),
                                ("controls + rule evidence", "controls"), ("top-two gap", "controls")]:
                results.append(dict(endpoint=endpoint, scope=scope, left_model=left, right_model=right,
                                    **boot.paired(hits[left], hits[right], mask)))
        if endpoint == "train-only top":
            for group in (CLOSE, WIDE):
                mask = rows.gap_group == group
                gap_groups.append(dict(group=group, **boot.paired(complex_, anyburl, mask)))
    return results, gap_groups


def gap_contrast(rows, boot, groups):
    d = rows.complex_new_hits - rows.all_new_hits
    draws = [boot.rates(d, rows.gap_group == name) for name in (CLOSE, WIDE)]
    lo, hi = boot.interval(draws[0] - draws[1])
    return dict(delta=groups[0]["delta"] - groups[1]["delta"], lo=lo, hi=hi)


def verdict(validation_summary, results, groups, contrast, main_stats, previous_rescues, prior):
    def ranked(rows):
        return table(["Model or comparison", "Test queries", "Left", "Right", "Gap pp (95% CI)"], [
            [f"{r['left_model']} vs {r['right_model']}", r["n"], pct(r["left"]), pct(r["right"]),
             f"{points(r['delta'])} {ci(r)}"] for r in rows])

    live = [r for r in results if r["endpoint"] == "train-only top" and r["scope"] == "all test queries"]
    new = [r for r in results if r["endpoint"] == "train-only top"
           and r["scope"] == "masked input absent from validation"
           and (r["left_model"] in ("controls + rule evidence", "top-two gap") and r["right_model"] == "controls")]
    filtered = [r for r in results if r["endpoint"] == "benchmark filtered" and r["scope"] == "all test queries"
                and r["left_model"] in ("controls + rule evidence", "top-two gap") and r["right_model"] == "controls"]
    evidence = next(r for r in live if r["left_model"] == "controls + rule evidence" and r["right_model"] == "controls")
    gap = next(r for r in live if r["left_model"] == "top-two gap" and r["right_model"] == "controls")
    retrospective_close, retrospective_far = previous_rescues["features"][:2]
    reverse = previous_rescues["reverse"][0]
    auc = prior["selector_models"]
    brier_lo, brier_hi = prior["selection"]["brier_change_ci"]
    text = [
        "# Can we choose between AnyBURL and ComplEx before knowing the answer?",
        "",
        "**The measured rule evidence did not establish a reliable way to choose.** On CoDEx-S, the selector "
        f"with rule evidence and the controls-only selector each returned the correct answer on {pct(evidence['left'])} "
        f"of queries. Their paired difference was {points(evidence['delta'])} percentage points {ci(evidence)}. "
        f"The top-two gap policy scored {pct(gap['left'])} by choosing ComplEx in both validation groups.",
        "",
        "## What we can measure before answering",
        "",
        "The earlier error analysis used the rule scores of the correct answer and AnyBURL’s first wrong answer. "
        f"ComplEx rescued {pct(retrospective_close['rescue_rate'])} of strong errors with a close gap and "
        f"{pct(retrospective_far['rescue_rate'])} with a wider gap. Identifying both candidates in that comparison "
        "requires the correct answer. The final check uses the scores of AnyBURL’s first and second candidates "
        "after removing known training positives. Both scores are available from the masked query.",
        "",
        "When the models disagree and AnyBURL returns at least two candidates, a fixed cutoff of .05 separates "
        "close and wide scores. The stronger model in each validation group is selected for that group. "
        "ComplEx handles validation ties and queries with fewer than two candidates. If the models agree, their "
        "shared answer is returned. Choices were written using masked test profiles before joining test outcomes.",
        "",
        table(["Top-two score gap", "Validation disagreements", "ComplEx correct", "AnyBURL correct", "Selected"], [
            [r["group"], r["n"], r["complex_hits"], r["anyburl_hits"], r["selected"]] for r in validation_summary]),
        "",
        "The saved controls-only selector uses relation, direction, entity degree, training relation frequency and "
        "answer multiplicity. Its evidence-aware counterpart also uses native rule confidence, candidate competition, "
        "family agreement and applicable rule structures. Both were fit on validation disagreements. "
        "[Selector methods](../evidence-advantage/report.md)",
        "",
        "## Test results",
        "",
        f"The models disagree on {main_stats['disagreements']:,} of {main_stats['queries']:,} train-only top answers. "
        f"Among those disagreements, only ComplEx was right on {main_stats['complex_only']:,}, only AnyBURL was "
        f"right on {main_stats['anyburl_only']:,}, and both missed on {main_stats['both_wrong']:,}.",
        "",
        ranked(live),
        "",
        "Each accuracy in this table scores the actual answer returned from a training-only candidate list. "
        "Intervals are paired 95% fact-bootstrap intervals with both directions from each fact kept together. "
        f"The two fitted selectors each solved {evidence['left_only']} queries missed by the other.",
        "",
        table(["Top-two score gap", "Test disagreements", "ComplEx correct", "AnyBURL correct",
               "ComplEx minus AnyBURL pp (95% CI)"], [
            [r["group"], r["n"], pct(r["left"]), pct(r["right"]), f"{points(r['delta'])} {ci(r)}"] for r in groups]),
        "",
        f"The ComplEx advantage in the close group minus its advantage in the wide group was "
        f"{points(contrast['delta'])} percentage points {ci(contrast)}.",
        "",
        "As a check for repeated masked questions, the following comparisons use test questions whose masked inputs "
        "never appeared in validation.",
        "",
        ranked(new),
        "",
        "The standard benchmark also scores the selected model’s ranking after filtering other known positive facts. "
        "That endpoint can promote a lower candidate in the chosen ranking. The two comparisons below use this "
        "benchmark endpoint.",
        "",
        ranked(filtered),
        "",
        f"Rule evidence lowered three-class Brier loss from {auc[0]['brier']:.3f} to {auc[1]['brier']:.3f} "
        f"(paired change interval [{brier_lo:+.3f}, {brier_hi:+.3f}]). Among disagreements with exactly one "
        f"correct model, winner AUC was {auc[0]['auc']:.3f} for controls and {auc[1]['auc']:.3f} after adding "
        "rule evidence. The probability scores improved on the Brier measure while the selected answers had "
        "equal overall accuracy.",
        "",
        "## Final research conclusion",
        "",
        f"1. Strong general rules directly supported the correct answers in {reverse['left_only']} cases that only "
        "AnyBURL solved.",
        "2. ComplEx recovered some strongly supported AnyBURL errors, especially when the wrong answer and "
        "the held-out answer had similar rule scores. [Comparative error and rule examples](../rule-rescues/report.md)",
        "3. The answer-blind gap and the richer rule-evidence selector yielded no improvement over the "
        "controls-only selector in actual answer accuracy on this split.",
        "",
        "The CoDEx-S test has been examined throughout the study, so these results are exploratory. "
        "Independent CoDEx-M confirmation remains open.",
        "",
        "[Per-query choices](locked-test-choices.csv) · [Paired results](test-comparisons.csv) · "
        "[Protocol and input hashes](decision-protocol.json)",
        "",
        "Reproduce from the project root with "
        "`OPENBLAS_NUM_THREADS=1 .backend-venv/bin/python -m kgc.research.answer_blind_closeout`.",
        "",
    ]
    (OUTPUT / "report.md").write_text("\n".join(text))


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    val_profiles = profiles("validation")
    val_rows = reveal(val_profiles, "validation")
    mapping, validation = choose_mapping(val_rows)
    choices = lock_choices(val_profiles, profiles("test"), mapping)
    decision_inputs = ["validation-evidence-profiles.csv", "validation-outcomes.csv",
                       "test-evidence-profiles.csv", "selector-predictions.csv"]
    write_json(OUTPUT / "decision-protocol.json", {
        "split_for_fitting": "CoDEx-S validation", "evaluation_split": "CoDEx-S test, exploratory",
        "gap": "native first minus second score after filtering training positives",
        "gap_threshold": THRESHOLD, "gap_model": mapping, "fallback": "ComplEx",
        "validation_groups": validation, "choices_sha256": digest(OUTPUT / "locked-test-choices.csv"),
        "inputs_sha256": {name: digest(EVIDENCE / name) for name in decision_inputs},
    })

    test = reveal(choices, "test")
    dataset = load_dataset("data/codex-s")
    for split, rows in (("valid", val_rows), ("test", test)):
        expected = [(q.query_id, q.model_input.known, q.model_input.relation, q.direction, q.answer, i // 2)
                    for i, q in enumerate(queries(getattr(dataset, split), split))]
        if list(rows[["query_id", *KEYS, "gold", "fact"]].itertuples(index=False, name=None)) != expected:
            raise ValueError(f"Masked inputs and correctness rows differ from the official {split} queries")
    boot = FactBootstrap(test.fact)
    results, gap_groups = evaluate(test, boot)
    contrast = gap_contrast(test, boot, gap_groups)
    d = test[test.top_answers_differ]
    c, a = d.complex_new_hits, d.all_new_hits
    if ((c == 1) & (a == 1)).any():
        raise ValueError("Different top answers cannot both equal the evaluated gold")
    counts = dict(queries=len(test), disagreements=len(d), complex_only=int(c.sum()),
                  anyburl_only=int(a.sum()), both_wrong=int(((c == 0) & (a == 0)).sum()))
    prior = read(EVIDENCE / "results.json")
    improved = next(r for r in results if r["endpoint"] == "train-only top" and r["scope"] == "all test queries"
                    and r["left_model"] == "controls + rule evidence" and r["right_model"] == "controls")
    saved = next(r for r in prior["selector_scores"] if r["outcome"] == "new_hits" and r["group"] == "all queries"
                 and r["selector"] == "rule evidence vs controls")
    if any(improved[k] != saved[k] for k in ("left", "right", "left_only", "right_only", "n")):
        raise ValueError("The prior answer-blind selector result did not reproduce")
    write_csv(OUTPUT / "test-comparisons.csv", results)
    write_csv(OUTPUT / "gap-groups.csv", gap_groups)
    write_json(OUTPUT / "results.json", dict(counts=counts, validation=validation, test=results, groups=gap_groups,
               gap_contrast=contrast,
               test_labels_sha256=digest(EVIDENCE / "test-outcomes.csv"),
               test_split_sha256=dataset.provenance["sha256"]["test"]))
    verdict(validation, results, gap_groups, contrast, counts, read(RESCUES / "results.json"), prior)
    print(f"Saved {OUTPUT / 'report.md'}")


if __name__ == "__main__":
    run()
