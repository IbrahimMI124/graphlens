"""Analyze answer-blind evidence and paired outcomes for frozen CoDEx-S models."""
from collections import Counter, defaultdict
from math import ceil, floor
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ..data import load_dataset
from ..evaluation import FilterIndex, queries
from ..io import digest, environment, write_csv, write_json
from .evidence_inference import FAMILIES, FROZEN, NEURAL, WORK, checked_saved, top
from .runner import load_rows, read, save_rows


OUTPUT = Path("artifacts/evidence-advantage")
N_BOOT = 2500
STRUCTURES = ("symmetry", "inversion", "subsumption", "two-hop composition", "three-hop composition")
MODELS = ("complex", *FAMILIES, "frequency")
CONTROLS = ["relation", "direction", "log_degree", "log_frequency", "log_multiplicity"]


def competition(profile):
    if not profile["count"]:
        return "no candidate"
    if profile["score"] < .5:
        return "leading score below .50"
    if profile["near"] == 1:
        return "strong, 1 near leader"
    if profile["near"] <= 4:
        return "strong, 2–4 near leaders"
    return "strong, 5+ near leaders"


COMPETITION = ("no candidate", "leading score below .50", "strong, 1 near leader",
               "strong, 2–4 near leaders", "strong, 5+ near leaders")


def agreement(general, constants):
    if general and constants:
        return "agree" if general == constants else "disagree"
    if general or constants:
        return "general only" if general else "constants only"
    return "neither"


def features(masked, profiles, degree, relation_frequency, multiplicity):
    fields = dict(known=masked.known, relation=masked.relation, direction=masked.direction,
                  degree=degree, frequency=relation_frequency, multiplicity=multiplicity,
                  log_degree=np.log1p(degree), log_frequency=np.log1p(relation_frequency),
                  log_multiplicity=np.log1p(multiplicity))
    for family, p in profiles.items():
        fields.update({f"{family}_{key}": p[key] for key in
                       ("top", "count", "score", "margin", "near", "tied", "concentration")})
        fields[f"{family}_competition"] = competition(p)
        fields[f"{family}_log_count"] = np.log1p(p["count"])
        fields[f"{family}_log_near"] = np.log1p(p["near"])
        lead = p.get("lead", {})
        for key in ("family", "raw", "support", "length", "expression"):
            fields[f"{family}_lead_{key}"] = lead.get(key)
        fields[f"{family}_log_support"] = np.log1p(lead.get("support", 0))
        fields[f"{family}_lead_strength"] = lead.get("score", 0.)
        fields[f"{family}_lead_rule_count"] = p.get("lead_rule_count", 0)
        fields[f"{family}_has_candidate"] = int(p["count"] > 0)
    fields["agreement"] = agreement(profiles["general"]["top"], profiles["constants"]["top"])
    for kind in STRUCTURES:
        fields[kind] = profiles["general"].get("structures", {}).get(kind, 0.)
    return fields


def assemble(dataset, caches, split):
    degree, frequency = Counter(), Counter()
    side_counts = defaultdict(Counter)
    training = FilterIndex(dataset.graph.triples)
    official = FilterIndex(dataset.positives_for_filter(split))
    for h, r, t in dataset.graph.triples:
        degree.update((h, t))
        frequency[r] += 1
        side_counts[r, "head"][h] += 1
        side_counts[r, "tail"][t] += 1
    by_frequency = {key: sorted(counts, key=lambda e: (-counts[e], e))
                    for key, counts in side_counts.items()}
    profiles, outcomes = [], []
    names = FAMILIES if split == "test" else FAMILIES[:-1]
    for i, q in enumerate(queries(getattr(dataset, split), split)):
        masked = q.model_input
        rows = {name: caches[name][split][i] for name in ("complex", *names)}
        if any(row["query_id"] != q.query_id for row in rows.values()):
            raise ValueError(f"Misaligned query {q.query_id}")
        filtered_training = training.answers[masked]
        rank = by_frequency[masked.relation, masked.direction]
        p = features(masked, {name: rows[name]["profile"] for name in names}, degree[masked.known],
                     frequency[masked.relation], len(filtered_training))
        p["complex_top"] = rows["complex"]["top"]
        p["frequency_top"] = next((e for e in rank if e not in filtered_training), None)
        p["query_id"] = q.query_id
        profiles.append(p)
        # The answer and held-out filter are first used to construct outcomes.
        o = dict(query_id=q.query_id, fact=i // 2, gold=q.answer, generated=rows["all"]["generated"])
        for name, row in rows.items():
            o[f"{name}_official_top"] = row["official_top"]
            o[f"{name}_hits"] = row["hits"]
        o["frequency_official_top"] = next((e for e in rank if e not in official.alternatives(q)), None)
        o["frequency_hits"] = int(o["frequency_official_top"] == q.answer)
        for name in [*rows, "frequency"]:
            o[f"{name}_new_hits"] = int(p[f"{name}_top"] == q.answer)
        outcomes.append(o)
    profiles = pd.DataFrame(profiles)
    outcomes = pd.DataFrame(outcomes)
    return profiles, outcomes


class FactBootstrap:
    def __init__(self, facts):
        self.facts = np.asarray(facts)
        self.n_facts = int(self.facts.max()) + 1
        rng = np.random.default_rng(851)
        self.draws = rng.integers(0, self.n_facts, size=(N_BOOT, self.n_facts))
        self.weights = np.array([np.bincount(draw, minlength=self.n_facts) for draw in self.draws],
                                dtype=np.float32)

    def totals(self, values, mask):
        per_fact = np.bincount(self.facts[mask], np.asarray(values)[mask], minlength=self.n_facts)
        return self.weights @ per_fact.astype(np.float32)

    @staticmethod
    def interval(draws):
        draws = np.asarray(draws)
        valid = draws[np.isfinite(draws)]
        return tuple(map(float, np.quantile(valid, [.025, .975]))) if len(valid) else (None, None)

    def rates(self, values, mask):
        counts = self.totals(np.ones(len(mask)), mask)
        with np.errstate(invalid="ignore", divide="ignore"):
            return self.totals(values, mask) / counts

    def paired(self, a, b, mask):
        a, b, mask = np.asarray(a), np.asarray(b), np.asarray(mask, dtype=bool)
        n = int(mask.sum())
        if not n:
            return dict(n=0, facts=0, left=None, right=None, delta=None, lo=None, hi=None,
                        left_only=0, right_only=0, both=0, neither=0)
        difference = a - b
        lo, hi = self.interval(self.rates(difference, mask))
        return dict(n=n, facts=len(set(self.facts[mask])), left=float(a[mask].mean()),
                    right=float(b[mask].mean()), delta=float(difference[mask].mean()), lo=lo, hi=hi,
                    left_only=int(np.sum(difference[mask] == 1)),
                    right_only=int(np.sum(difference[mask] == -1)),
                    both=int(np.sum((a[mask] == 1) & (b[mask] == 1))),
                    neither=int(np.sum((a[mask] == 0) & (b[mask] == 0))))


def groups(frame, boot, categories, left="complex", right="all", suffix="hits"):
    a, b = frame[f"{left}_{suffix}"], frame[f"{right}_{suffix}"]
    rows = []
    for name, mask in categories:
        row = dict(group=name, **boot.paired(a, b, mask))
        if row["n"]:
            row.update({model: float(frame.loc[mask, f"{model}_{suffix}"].mean()) for model in MODELS})
        rows.append(row)
    return rows


def match_strength(frame, boot):
    strata = pd.DataFrame({
        "relation": frame.relation, "direction": frame.direction,
        "degree_bin": np.floor(np.log2(frame.degree.clip(lower=1))).astype(int),
        "answers_bin": np.floor(np.log2(1 + frame.multiplicity)).astype(int),
    })
    outcomes = (frame.complex_hits - frame.all_hits).to_numpy()
    results = []
    for family in ("general", "constants", "all"):
        decisive, crowded, weights = [], [], []
        for idx in strata.groupby(list(strata)).indices.values():
            a = np.zeros(len(frame), dtype=bool)
            b = a.copy()
            a[idx] = (frame.iloc[idx][f"{family}_competition"] == COMPETITION[2]).to_numpy()
            b[idx] = (frame.iloc[idx][f"{family}_competition"] == COMPETITION[4]).to_numpy()
            if a.any() and b.any():
                decisive.append(a)
                crowded.append(b)
                weights.append(min(a.sum(), b.sum()))
        if not weights:
            continue
        weight = np.asarray(weights)
        decisive_est = np.array([outcomes[a].mean() for a in decisive])
        crowded_est = np.array([outcomes[b].mean() for b in crowded])
        a_draw = np.array([boot.rates(outcomes, a) for a in decisive])
        b_draw = np.array([boot.rates(outcomes, b) for b in crowded])
        usable = np.isfinite(a_draw) & np.isfinite(b_draw)
        draws = np.nansum((b_draw - a_draw) * weight[:, None], axis=0) / (usable.T @ weight)
        lo, hi = boot.interval(draws)
        a, b = np.any(decisive, axis=0), np.any(crowded, axis=0)
        results.append(dict(family=family, strata=len(weight), decisive_n=int(a.sum()),
                            crowded_n=int(b.sum()), facts=len(set(boot.facts[a | b])),
                            decisive=float(np.average(decisive_est, weights=weight)),
                            crowded=float(np.average(crowded_est, weights=weight)),
                            delta=float(np.average(crowded_est - decisive_est, weights=weight)),
                            lo=lo, hi=hi))
    return results


def selector(valid, test, boot):
    cat_controls = ["relation", "direction"]
    cat_rules = ["agreement", "general_lead_family", "constants_lead_family"]
    symbolic = [f"{name}_{key}" for name in ("all", "general", "constants") for key in
                ("score", "margin", "concentration", "log_count", "log_near",
                 "log_support", "has_candidate")] + list(STRUCTURES)
    for frame in (valid, test):
        frame[cat_rules] = frame[cat_rules].fillna("absent")
    train_mask = valid.complex_top != valid.all_top
    test_mask = test.complex_top != test.all_top
    validation_inputs = set(zip(valid.known, valid.relation, valid.direction))
    test_inputs = list(zip(test.known, test.relation, test.direction))
    new_input = np.array([key not in validation_inputs for key in test_inputs])
    train = valid[train_mask]
    evaluation = test[test_mask]
    train_y = train.complex_new_hits - train.all_new_hits
    test_y = (evaluation.complex_new_hits - evaluation.all_new_hits).to_numpy()
    live_mask = np.ones(len(test), dtype=bool)
    exclusive = test_y != 0
    selections, probabilities, metrics = {}, {}, []
    for kind, categories, numbers in (
        ("controls", cat_controls, CONTROLS[2:]),
        ("controls + rule evidence", cat_controls + cat_rules, CONTROLS[2:] + symbolic),
    ):
        preprocessing = ColumnTransformer(
            [("categories", OneHotEncoder(handle_unknown="ignore"), categories),
             ("numbers", StandardScaler(), numbers)])
        model = make_pipeline(preprocessing, LogisticRegression(C=1, max_iter=1000))
        model.fit(train, train_y)
        if not np.array_equal(model.classes_, [-1, 0, 1]):
            raise ValueError("Disagreement requires both exclusive outcomes and both wrong")
        p = model.predict_proba(evaluation)
        probabilities[kind] = p
        chosen = np.ones(len(test), dtype=bool)
        chosen[test_mask] = p[:, 2] >= p[:, 0]
        selections[kind] = chosen
    controls, evidence = probabilities.values()
    auc_draws, brier_draws = [], []
    label = np.eye(3)[test_y + 1]
    diff_brier = np.sum((evidence - label) ** 2 - (controls - label) ** 2, axis=1)
    evaluate_fact = boot.facts[test_mask.to_numpy()]
    margin = {name: p[:, 2] - p[:, 0] for name, p in probabilities.items()}
    for fact_weights in boot.weights:
        weights = fact_weights[evaluate_fact]
        positive_weight = weights[exclusive & (test_y == 1)].sum()
        negative_weight = weights[exclusive & (test_y == -1)].sum()
        if positive_weight and negative_weight:
            aucs = [roc_auc_score(test_y[exclusive] == 1, scores[exclusive],
                                  sample_weight=weights[exclusive]) for scores in margin.values()]
            auc_draws.append(aucs)
        brier_draws.append(np.average(diff_brier, weights=weights))
    auc_draws = np.asarray(auc_draws)
    auc_gains = auc_draws[:, 1] - auc_draws[:, 0]
    for i, (kind, p) in enumerate(probabilities.items()):
        chosen = selections[kind]
        auc_lo, auc_hi = boot.interval(auc_draws[:, i])
        metrics.append(dict(selector=kind, validation_disagreements=int(train_mask.sum()),
                            test_disagreements=int(test_mask.sum()), test_exclusive=int(exclusive.sum()),
                            choose_anyburl=int((~chosen).sum()),
                            auc=float(roc_auc_score(test_y[exclusive] == 1, margin[kind][exclusive])),
                            auc_lo=auc_lo, auc_hi=auc_hi,
                            brier=float(np.sum((p - label) ** 2, axis=1).mean())))
    result = []
    for name, chosen in selections.items():
        for suffix in ("new_hits", "hits"):
            selected_hits = np.where(chosen, test[f"complex_{suffix}"], test[f"all_{suffix}"])
            for group, mask in (("all queries", live_mask), ("train-only top answers differ", test_mask),
                                ("masked input absent from validation", new_input)):
                result.append(dict(selector=name, outcome=suffix, group=group,
                                   **boot.paired(selected_hits, test[f"complex_{suffix}"], mask)))
    for suffix in ("new_hits", "hits"):
        a, b = (np.where(chosen, test[f"complex_{suffix}"], test[f"all_{suffix}"])
                for chosen in (selections["controls + rule evidence"], selections["controls"]))
        result.append(dict(selector="rule evidence vs controls", outcome=suffix, group="all queries",
                           **boot.paired(a, b, live_mask)))
    enabled = test[["query_id"]].copy()
    for name, chosen in selections.items():
        enabled[name] = np.where(chosen, "ComplEx", "AnyBURL")
    enabled["tops_differ"] = test_mask
    for i, name in enumerate(("p_anyburl_only", "p_both_wrong", "p_complex_only")):
        enabled.loc[test_mask, name] = evidence[:, i]
    return metrics, result, enabled, {
        "auc_gain_ci": boot.interval(auc_gains), "brier_change_ci": boot.interval(brier_draws),
        "validation_test_shared_masked_inputs": len(validation_inputs & set(test_inputs)),
    }


def diagnosis_tables(frame, boot, diagnosis):
    index = {q: i for i, q in enumerate(frame.query_id)}
    measures = ("native_score", "max_raw", "rule_count", "pattern_count", "grounding_count",
                "lead_support", "lead_raw")
    by_query = {}
    for pair in diagnosis:
        gold, wrong = pair["candidates"]
        i = index[pair["query_id"]]
        if (gold["entity"], wrong["entity"]) != (frame.gold[i], frame.all_official_top[i]):
            raise ValueError(f"Retrospective candidate mismatch for {pair['query_id']}")
        for candidate in (gold, wrong):
            candidate["lead_support"] = candidate["lead"]["support"]
            candidate["lead_raw"] = candidate["lead"]["raw"]
        first, second = wrong["score_sequence"], gold["score_sequence"]
        if first == second:
            ordering = "same confidence sequence"
        elif first <= second:
            raise ValueError("Native ranking disagrees with attributed confidence sequence")
        elif first[0] != second[0]:
            ordering = "higher leading score"
        elif first[:min(len(first), len(second))] == second[:min(len(first), len(second))]:
            ordering = "same prefix, more rules"
        else:
            ordering = "later score breaks tie"
        pair["ordering"] = ordering
        by_query[i] = pair
    masks = {
        "all generated misranks": np.array([i in by_query for i in range(len(frame))]),
        "ComplEx succeeds": np.array([i in by_query and frame.complex_hits[i] == 1 for i in range(len(frame))]),
        "both miss": np.array([i in by_query and frame.complex_hits[i] == 0 for i in range(len(frame))]),
    }
    summaries, families = [], []
    for label, group in masks.items():
        for key in measures:
            gold_values = np.zeros(len(frame))
            wrong_values = np.zeros(len(frame))
            mask = group.copy()
            for i in np.flatnonzero(mask):
                gold, wrong = by_query[i]["candidates"]
                if key == "grounding_count" and not (gold["grounding_attribution_agrees"] and wrong["grounding_attribution_agrees"]):
                    mask[i] = False
                    continue
                gold_values[i], wrong_values[i] = gold[key], wrong[key]
            diff = wrong_values - gold_values
            lo, hi = boot.interval(boot.rates(diff, mask))
            summaries.append(dict(group=label, measure=key, n=int(mask.sum()), facts=len(set(boot.facts[mask])),
                                  gold_median=float(np.median(gold_values[mask])), wrong_median=float(np.median(wrong_values[mask])),
                                  gold_mean=float(gold_values[mask].mean()), wrong_mean=float(wrong_values[mask].mean()),
                                  delta_mean=float(diff[mask].mean()), lo=lo, hi=hi,
                                  wrong_higher=int(np.sum(diff[mask] > 0)), same=int(np.sum(diff[mask] == 0)),
                                  gold_higher=int(np.sum(diff[mask] < 0))))
        for which, j in (("correct", 0), ("ranked first", 1)):
            for family in ("B", "Uc", "Ud", "Z"):
                values = np.array([int(i in by_query and by_query[i]["candidates"][j]["lead"]["family"] == family)
                                   for i in range(len(frame))])
                lo, hi = boot.interval(boot.rates(values, group))
                families.append(dict(group=label, candidate=which, family=family, n=int(group.sum()),
                                     count=int(values[group].sum()), rate=float(values[group].mean()), lo=lo, hi=hi))
    ordering = []
    for label, group in masks.items():
        for name in ("higher leading score", "later score breaks tie", "same prefix, more rules", "same confidence sequence"):
            values = np.array([int(i in by_query and by_query[i]["ordering"] == name)
                               for i in range(len(frame))])
            lo, hi = boot.interval(boot.rates(values, group))
            ordering.append(dict(group=label, deciding_evidence=name, n=int(group.sum()),
                                 count=int(values[group].sum()), rate=float(values[group].mean()), lo=lo, hi=hi))
    return summaries, families, ordering


def pct(value):
    return "—" if value is None else f"{100 * value:.2f}%"


def points(value):
    return "—" if value is None else f"{100 * value:+.2f}"


def ci(row):
    return "—" if row["lo"] is None else f"[{points(row['lo'])}, {points(row['hi'])}]"


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |",
                      *["| " + " | ".join(str(v).replace("|", "\\|") for v in row) + " |" for row in rows]])


def comparison(rows, a, b, extras=()):
    return table(["Group", "Queries", "Facts", a, b, *[label for _, label in extras],
                  "Δ pp (95% CI)", "Left only / right only", "Both / neither"], [
        [r["group"], r["n"], r["facts"], pct(r["left"]), pct(r["right"]),
         *[pct(r.get(key)) for key, _ in extras],
         f"{points(r['delta'])} {ci(r)}" if r["n"] else "—",
         f"{r['left_only']} / {r['right_only']}", f"{r['both']} / {r['neither']}"] for r in rows])


def render_plot(rows, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharex=True)
    colors = {"general": "#316785", "constants": "#587647", "all": "#8A5043"}
    labels = ["No candidate", "Leading score < .50", "Strong, 1 near leader", "Strong, 2–4 near leaders",
              "Strong, 5+ near leaders"]
    lower = 2 * floor(50 * min(r["lo"] for r in rows if r["lo"] is not None))
    upper = 2 * ceil(50 * max(r["hi"] for r in rows if r["hi"] is not None))
    for i, (ax, family) in enumerate(zip(axes, colors)):
        subset = [r for r in rows if r["family"] == family]
        for y, row in enumerate(subset):
            if row["delta"] is not None:
                x = 100 * row["delta"]
                ax.plot([100 * row["lo"], 100 * row["hi"]], [y, y], color=colors[family], lw=1.8)
                ax.plot(x, y, "o", color=colors[family], ms=6)
            ax.text(.98, y, f"n={row['n']:,}", transform=ax.get_yaxis_transform(),
                    ha="right", va="center", fontsize=8, color="#414850")
        ax.set_title({"general": "General rules", "constants": "Constant-bearing rules",
                      "all": "All rules"}[family], fontsize=11, weight="bold")
        ax.set_yticks(range(len(labels)), labels=labels if i == 0 else [""] * len(labels))
        ax.set_xlim(lower - .5, upper + 4)
        ax.set_xticks(range(lower, upper + 1, 2))
        ax.set_ylim(4.55, -.55)
        ax.axvline(0, linestyle="--", color="#949CA5", linewidth=1)
        ax.grid(axis="x", alpha=.14)
        ax.spines[["top", "left", "right"]].set_visible(False)
        ax.tick_params(length=0, labelsize=9)
    fig.suptitle("Candidate competition and relative accuracy on CoDEx-S", weight="bold")
    fig.supxlabel("ComplEx minus all-rule AnyBURL Hits@1 (percentage points)", fontsize=10)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(destination / f"evidence-versus-advantage.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


def label_map():
    return {k: v["label"] for name in ("relations", "entities")
            for k, v in read(WORK / f"{name}.json").items()}


def select_cases(frame, best_relations, chosen):
    generated_miss = frame.generated & (frame.all_hits == 0)
    improved = (frame.constants_general_hits == 1) & (frame.general_hits == 0)
    worsened = (frame.constants_general_hits == 0) & (frame.general_hits == 1)
    conditions = [
        ("ComplEx rescues an AnyBURL misrank", generated_miss & (frame.complex_hits == 1)),
        ("Both miss despite a generated answer", generated_miss & (frame.complex_hits == 0)),
        ("Adding constants corrects the general prediction", improved),
        ("Adding constants overrides a correct general prediction", worsened),
        ("Constants beat the marginal frequency prediction", (frame.constants_hits == 1) & (frame.frequency_hits == 0)),
        ("Frequency wins where constants miss", (frame.constants_hits == 0) & (frame.frequency_hits == 1)),
        ("Strong and decisive all-rule evidence", (frame.all_competition == COMPETITION[2]) & (frame.all_hits == 1)),
        ("Strong but crowded all-rule evidence", (frame.all_competition == COMPETITION[4]) & generated_miss),
        ("High confidence backed by at most ten training facts",
         (frame.constants_lead_raw >= .8) & (frame.constants_lead_support <= 10) & (frame.constants_new_hits == 0)),
        ("Selector improves the train-only prediction",
         (chosen == "AnyBURL") & (frame.all_new_hits == 1) & (frame.complex_new_hits == 0)),
        ("Selector harms the train-only prediction",
         (chosen == "AnyBURL") & (frame.all_new_hits == 0) & (frame.complex_new_hits == 1)),
    ]
    for kind in STRUCTURES:
        mask = frame[kind] >= .5
        if not mask.any():
            mask = frame[kind] > 0
        conditions.append((f"Applicable {kind} rule", mask))
    for relation in best_relations:
        favorite = "complex_hits" if relation["delta"] > 0 else "all_hits"
        conditions.append((f"Exclusive success on {relation['group']}",
                           (frame.relation == relation["relation"]) & (frame[favorite] == 1) &
                           (frame.complex_hits != frame.all_hits)))
    specs = []
    for title, mask in conditions:
        available = frame.loc[mask]
        if available.empty:
            continue
        used = {c["fact"] for c in specs}
        fresh = available[~available.fact.isin(used)]
        sample = (fresh if len(fresh) else available).iloc[0]
        specs.append({"title": title, "query_id": sample.query_id, "fact": int(sample.fact)})
    return specs


def build_cases(dataset, frame, specs, diagnosis, labels):
    """Find native training witnesses for the cases selected by the tables."""
    from .evidence_inference import groundings, native_rule_info
    from .families import AuditedRules
    from .structure_cases import inspect_witnesses

    backend = AuditedRules(dataset.graph, FROZEN / "subsets/all.rules",
                           qa_options={"collect_rules": True}, retain_catalog_metadata=False)
    info = native_rule_info(backend)
    selected = frame.set_index("query_id")
    retrospective = {d["query_id"]: d for d in diagnosis}
    records = []
    def answer(value):
        return None if pd.isna(value) else value

    for spec in specs:
        row = selected.loc[spec["query_id"]]
        q = next(q for q in queries((dataset.test[spec["fact"]],)) if q.direction == row.direction)
        masked = q.model_input
        answers = {f"{name} top": answer(row[f"{name}_official_top"]) for name in MODELS}
        answers["held-out answer"] = q.answer
        pred = backend.predict(masked)
        ids = backend.qa.get_rules(as_string=False)[0] if pred.candidates else []
        by_candidate = {e: r for (e, _), r in zip(pred.candidates, ids)}
        targets = defaultdict(dict)
        for role, candidate in answers.items():
            active = by_candidate.get(candidate, [])
            allowed = {"general top": {"B"}, "constants top": {"Uc", "Ud"}}.get(role, {"B", "Uc", "Ud", "Z"})
            candidates = [i for i in active if info(i)["family"] in allowed and info(i)["length"]]
            if candidates:
                targets[masked.triple(candidate)][role] = candidates[0]
        if spec["title"].startswith("Applicable "):
            kind = spec["title"].removeprefix("Applicable ").removesuffix(" rule")
            training = FilterIndex(dataset.graph.triples).answers[masked]
            evidence = [(i, e) for e, ids_for_e in by_candidate.items() if e not in training
                        for i in ids_for_e if info(i)["structure"] == kind]
            if evidence:
                best, candidate = max(evidence, key=lambda item: info(item[0])["score"])
                targets[masked.triple(candidate)][kind] = best
        recovered = groundings(backend, targets)
        witnesses = []
        for target, roles in targets.items():
            for i in dict.fromkeys(roles.values()):
                rule = info(i)
                checked = inspect_witnesses(
                    [{"expression": rule["expression"], "groundings": recovered.get(target, {}).get(i, [])[:1]}],
                    backend.training_edges, backend.training_edges, target)
                for witness in checked:
                    witnesses.append(dict(candidate=target[2 if q.direction == "tail" else 0],
                                          roles=[role for role, j in roles.items() if j == i],
                                          **rule, grounding=witness["grounding"]))
        records.append(dict(**spec, triple=q.triple, direction=q.direction, official_answers=answers,
                            train_only_tops={name: answer(row[f"{name}_top"]) for name in MODELS},
                            all_score=row.all_score, all_near=int(row.all_near),
                            degree=int(row.degree), disagreement=row.agreement,
                            ordering=retrospective.get(spec["query_id"], {}).get("ordering"),
                            witnesses=witnesses))
    write_json(OUTPUT / "case-studies.json", records)
    def named(token):
        return f"{labels.get(token, token)} ({token})" if token in labels else (token or "abstained")

    lines = ["# CoDEx-S query examples", "",
             "Each case is the first official query satisfying its stated condition, preferring a fact absent from earlier examples. "
             "Cases illustrate the measured groups. The benchmark top answers below use evaluator filtering. "
             "Each displayed witness was recovered from the frozen catalog and checked against the positive training graph and rule bindings.", ""]
    for record in records:
        h, r, t = record["triple"]
        query = f"?, {named(r)}, {named(t)}" if record["direction"] == "head" else f"{named(h)}, {named(r)}, ?"
        lines += [f"## {record['title']}", "",
                  f"`{record['query_id']}` · ({query}). AnyBURL train-only leading score {record['all_score']:.3f}, "
                  f"{record['all_near']} near leaders, known-entity degree {record['degree']}.", "",
                  table(["Model", "Benchmark top", "Train-only top"], [
                      [n, named(record["official_answers"][n + " top"]), named(record["train_only_tops"][n])]
                      for n in MODELS]), "",
                  f"Held-out answer is **{named(record['official_answers']['held-out answer'])}**.", ""]
        if record["ordering"]:
            lines += [f"Native maxplus comparison against the held-out answer fell in the “{record['ordering']}” category.", ""]
        for w in record["witnesses"]:
            body = " · ".join(f"({named(h)}, {named(r)}, {named(t)})" for h, r, t in w["grounding"])
            lines.append(f"- **{named(w['candidate'])}** ({', '.join(w['roles'])}). "
                         f"`{w['expression']}` has native score {w['score']:.3f} and training support {w['support']}. "
                         f"Training witness {body}.")
        lines.append("")
    (OUTPUT / "case-studies.md").write_text("\n".join(lines) + "\n")
    return records


def make_report(data):
    overall = data["overall"]
    train_only = data["train_only"]
    diagnoses = data["diagnoses"]
    families = data["families"]
    ordering = data["ordering"]
    misranks = data["misranks"]
    evidence = data["evidence"]
    agreement_rows = data["agreement"]
    family_gap = data["family_gap"]
    ablation = data["ablation"]
    frequency = data["frequency"]
    structure = data["structure"]
    calibration = data["calibration"]
    matching = data["matching"]
    relations = data["relations"]
    selector_models = data["selector_models"]
    selector_scores = data["selector_scores"]
    selection = data["selection"]
    base = overall[0]
    ambiguous = next(r for r in evidence if r["family"] == "all" and r["group"] == COMPETITION[4])
    decisive = next(r for r in evidence if r["family"] == "all" and r["group"] == COMPETITION[2])
    rescues = misranks[0]
    incorporation = ablation[0]
    disagree = next(r for r in agreement_rows if r["group"] == "disagree")
    best_selector = next(r for r in selector_scores if r["selector"] == "controls + rule evidence"
                         and r["outcome"] == "new_hits" and r["group"] == "all queries")
    matched_all = next(r for r in matching if r["family"] == "all")
    first_rule = ordering[0]
    text = [
        "# When does rule evidence favor AnyBURL or ComplEx?",
        "",
        "Exploratory follow-up on all 3,656 directional CoDEx-S test queries from 1,828 facts. "
        "The analysis uses the frozen 60-second AnyBURL inventory and ComplEx seed "
        f"{data['seed']}, selected by validation MRR in the original study.",
        "",
        f"**Candidate generation was nearly universal.** AnyBURL generated the correct entity in "
        f"{data['n_generated']:,}/3,656 queries ({pct(data['n_generated'] / 3656)}) and ranked it first in "
        f"{data['n_ranked_first']:,}/3,656 ({pct(base['right'])}). "
        f"ComplEx rescued {rescues['left_only']:,} of the {rescues['n']:,} generated-but-misranked cases "
        f"({pct(rescues['left'])}).",
        "",
        f"**Strong evidence looked different when candidates crowded the top.** With one near leader from all rules, "
        f"the ComplEx–AnyBURL gap was {points(decisive['delta'])} pp {ci(decisive)}. "
        f"With five or more near leaders it was {points(ambiguous['delta'])} pp {ci(ambiguous)}. "
        f"After matching on relation, direction, degree and training answer count, the crowded-minus-decisive shift was "
        f"{points(matched_all['delta'])} pp {ci(matched_all)}.",
        "",
        f"**Both selectors scored {pct(best_selector['left'])} train-only accuracy.** The evidence-aware selector gained "
        f"{points(best_selector['delta'])} pp {ci(best_selector)} over always using ComplEx. "
        "CoDEx-M confirmation remains open.",
        "",
        "## Paired benchmark results",
        "",
        comparison(overall, "ComplEx", "AnyBURL", [("general", "General"), ("constants", "Constants"),
                   ("constants_general", "General + constants"), ("frequency", "Relation frequency")]),
        "",
        comparison(train_only, "ComplEx", "AnyBURL", [("general", "General"), ("constants", "Constants"),
                   ("constants_general", "General + constants"), ("frequency", "Relation frequency")]),
        "",
        "Benchmark Hits@1 filters out other known positive answers. Evidence profiles and top-answer agreement "
        "remove training positives only. Every interval is a pointwise 95% paired bootstrap interval over facts "
        f"({N_BOOT:,} draws), keeping both prediction directions together. The three seeds use the same test facts. "
        "Intervals for groups with few facts can be uninformative, especially when all observed outcomes agree. "
        "The seed-by-seed sensitivity table gives separate results. [Seed sensitivity](seed-sensitivity.csv)",
        "",
        "## 1. Why does AnyBURL misrank generated answers? (Q1–Q3)",
        "",
        comparison(misranks, "ComplEx", "AnyBURL"),
        "",
        f"The first-ranked wrong candidate had a higher leading native score in {first_rule['count']:,} of "
        f"{first_rule['n']:,} misranks ({pct(first_rule['rate'])}). Both models missed {rescues['neither']:,} queries in this cohort.",
        "",
        "The next comparison uses each misrank’s held-out answer and its benchmark-filtered top wrong candidate. "
        "Mean differences are wrong minus correct. Rule patterns retain relation and argument structure while masking "
        "entity-constant identities and variable names. Grounding counts sum native nonempty-body instances across "
        "QA-attributed rules. Each counted edge appears in training. Pairs with an attribution mismatch are excluded "
        f"from the grounding row. The two native interfaces agreed on nonempty-body rule attribution in "
        f"{next(r['n'] for r in diagnoses if r['measure'] == 'grounding_count'):,} pairs.",
        "",
        table(["Candidate evidence", "Pairs", "Correct median", "Wrong median", "Mean difference (95% CI)",
               "Wrong higher / tied / correct higher"], [
            [r["measure"].replace("_", " "), r["n"], f"{r['gold_median']:.3g}", f"{r['wrong_median']:.3g}",
             f"{r['delta_mean']:+.3g} [{r['lo']:+.3g}, {r['hi']:+.3g}]",
             f"{r['wrong_higher']} / {r['same']} / {r['gold_higher']}"]
            for r in diagnoses if r["group"] == "all generated misranks"]),
        "",
        table(["Native comparison", "All misranks", "ComplEx succeeds", "Both miss"], [
            [x, *[f"{r['count']}/{r['n']} ({pct(r['rate'])}, {pct(r['lo'])}–{pct(r['hi'])})"
                    for r in ordering if r["deciding_evidence"] == x]]
            for x in dict.fromkeys(r["deciding_evidence"] for r in ordering)]),
        "",
        table(["Leading family", "Correct candidate", "First-ranked wrong candidate"], [
            [f, *[f"{r['count']} ({pct(r['rate'])}, {pct(r['lo'])}–{pct(r['hi'])})"
                    for r in families if r["group"] == "all generated misranks" and r["family"] == f]]
            for f in ("B", "Uc", "Ud", "Z")]),
        "",
        "B is a general relational rule. Uc and Ud are conditional constant-bearing rules. Z is an unconditional prior. "
        "Identical confidence sequences leave the native frequency and ID tie order to discriminate. The strongest rule "
        "is the first under native adjusted confidence. The maximum raw confidence can belong to a different rule. "
        "[Evidence by rescue outcome](misrank-candidate-evidence.csv) · [Illustrated misranks](case-studies.md)",
        "",
        "![Evidence and model advantage](evidence-versus-advantage.png)",
        "",
        "A strong leading native score is at least .50. A near leader is within .05 of the best scalar score. "
        "These cutoffs were fixed for this follow-up and are descriptive. Scalar scores describe the strength and spread "
        "of evidence. PyClause uses its native maxplus confidence sequence and training-frequency tie handling for ranking. "
        "[Complete plot data](evidence-groups.csv)",
        "",
        "## 2. Do general and constant-bearing rules agree? (Q4–Q6)",
        "",
        f"The train-only family leaders differ on {disagree['n']:,} queries. On those queries, constants score "
        f"{pct(disagree['constants'])} and general rules {pct(disagree['general'])}. ComplEx leads all rules by "
        f"{points(disagree['delta'])} pp {ci(disagree)}.",
        "",
        comparison(agreement_rows, "ComplEx", "AnyBURL", [("general", "General"), ("constants", "Constants")]),
        "",
        f"Where train-only family leaders differ, constants lead general rules by "
        f"{points(family_gap[0]['delta'])} pp {ci(family_gap[0])}.",
        "",
        comparison(ablation, "General + constants", "General"),
        "",
        f"Adding constants corrects {incorporation['left_only']} queries and overrides "
        f"{incorporation['right_only']} correct general predictions, a net change of "
        f"{points(incorporation['delta'])} pp {ci(incorporation)}. The union excludes unconditional priors. "
        "The changed-prediction rows compare benchmark tops after evaluator filtering. "
        "[Examples of corrections and overrides](case-studies.md)",
        "",
        "The popularity baseline ranks entities by their training occurrence on the predicted side of the target relation, "
        "with Wikidata-ID order for tied counts. Groups use train-only predictions. The table scores benchmark top answers.",
        "",
        comparison(frequency, "Constants", "Relation frequency", [("complex", "ComplEx"), ("all", "AnyBURL")]),
        "",
        f"Constants lead the frequency baseline by {points(frequency[0]['delta'])} pp {ci(frequency[0])} overall. "
        "Their lead is larger on queries where their train-only predictions differ. The benchmark filter can remove "
        "a shared train-only top candidate and expose different lower-ranked answers.",
        "",
        "## 3. Which structures and levels of support matter? (Q7–Q8)",
        "",
        "A real applied general rule can enter each applicable group. Groups overlap. Symmetry reverses the argument order "
        "of the same relation, inversion reverses a different relation, and subsumption preserves argument order across "
        "different relations. Two- and three-hop groups use general rule bodies of those lengths. "
        "The strongest applicable rule for a structure may support any train-filtered candidate.",
        "",
        comparison(structure, "ComplEx", "AnyBURL", [("general", "General")]),
        "",
        "Leading-rule reliability uses each family’s train-only top candidate, its strongest native rule’s raw confidence "
        "and training support, and exact held-out target accuracy under train-only top prediction. The two families have "
        "different native weights and may occupy different bins.",
        "",
        table(["Family", "Raw confidence", "Training support", "Queries", "Facts", "Family",
               "ComplEx", "AnyBURL", "ComplEx–AnyBURL pp (95% CI)"], [
            [r["family"], r["confidence"], r["support"], r["n"], r["facts"], pct(r.get(r["family"])),
             pct(r["left"]), pct(r["right"]), f"{points(r['delta'])} {ci(r)}"] for r in calibration]),
        "",
        "The calibration CSV includes family-specific accuracy intervals and paired exclusive counts. "
        "[Calibration data](confidence-support.csv) · [Applied rules and training witnesses](case-studies.md)",
        "",
        "## 4. Does the association survive graph controls? (Q9–Q10)",
        "",
        "Within each family, the matched analysis compares strong queries with one near leader to strong queries with "
        "at least five near leaders. Strata match relation, direction, log₂ known-entity-degree bin, and log₂ training-answer "
        "multiplicity bin. Matching relation fixes training relation frequency. Strata are weighted by the smaller group "
        "size and contribute when both groups are observed in a bootstrap draw. Positive shifts favor ComplEx in crowded queries.",
        "",
        table(["Family", "Matched strata", "Decisive / crowded queries", "Facts", "Decisive gap pp", "Crowded gap pp",
               "Crowded minus decisive pp (95% CI)"], [
            [r["family"], r["strata"], f"{r['decisive_n']} / {r['crowded_n']}", r["facts"],
             points(r["decisive"]), points(r["crowded"]), f"{points(r['delta'])} {ci(r)}"] for r in matching]),
        "",
        "The following relations have at least 100 directional test queries. The table shows two relations from each "
        "end of the observed gap. This is an exploratory comparison across selected relations.",
        "",
        comparison(relations, "ComplEx", "AnyBURL"),
        "",
        table(["Relation", "Family disagreements", "Median near leaders", "Most prevalent strong general structure"], [
            [r["group"], f"{r['families_disagree']} / {r['n']}", r["median_all_near"], r["strongest_structure"] or "—"]
            for r in relations]),
        "",
        "[Relation-level evidence profiles](relations.csv) · [Representative relational predictions](case-studies.md)",
        "",
        "## 5. Can evidence predict which model to use? (Q11)",
        "",
        "Two fixed L2-regularized multinomial logistic models learn on CoDEx-S validation disagreements. Both see "
        "relation, direction, degree, relation frequency and training answer multiplicity. The augmented model also "
        "sees strength, competition, family agreement, family support and logical structure. They estimate the probability "
        "that only AnyBURL succeeds, neither succeeds, or only ComplEx succeeds, using targets scored from train-only "
        "top answers. For disagreements the selector chooses the greater exclusive-success probability. "
        f"The validation and test facts are disjoint and share {selection['validation_test_shared_masked_inputs']} masked inputs.",
        "",
        table(["Selector", "Validation disagreements", "Test disagreements", "Test exclusive wins",
               "Test choices of AnyBURL", "Exclusive-winner AUC (95% CI)", "Three-class Brier"], [
            [r["selector"], r["validation_disagreements"], r["test_disagreements"], r["test_exclusive"],
             r["choose_anyburl"], f"{r['auc']:.3f} [{r['auc_lo']:.3f}, {r['auc_hi']:.3f}]", f"{r['brier']:.3f}"]
            for r in selector_models]),
        "",
        f"The paired evidence-minus-controls AUC interval is "
        f"[{selection['auc_gain_ci'][0]:+.3f}, {selection['auc_gain_ci'][1]:+.3f}]. "
        f"The paired evidence-minus-controls Brier interval is "
        f"[{selection['brier_change_ci'][0]:+.3f}, {selection['brier_change_ci'][1]:+.3f}], with lower Brier preferred.",
        "",
        "The train-only endpoint evaluates the actual candidates that the selector can output. The benchmark endpoint "
        "evaluates the selected model’s ranking after the benchmark evaluator filters other known answers.",
        "",
        comparison([dict(r, group=f"{r['selector']} · {r['group']}") for r in selector_scores if r["outcome"] == "new_hits"],
                   "Train-only left", "Train-only right"),
        "",
        comparison([dict(r, group=f"{r['selector']} · {r['group']}") for r in selector_scores if r["outcome"] == "hits"],
                   "Benchmark left", "Benchmark right"),
        "",
        "The two selector rows compare against always choosing ComplEx. The rule-evidence versus controls row "
        "compares the two selectors directly. [Per-query choices](selector-predictions.csv) · [Selector examples](case-studies.md)",
        "",
        "## Scope and reproducibility",
        "",
        "The comparisons are observational and their intervals describe sampling variation over facts in this benchmark. "
        "The frozen ablation isolates the change in rule inventory under the same ranking engine. "
        "Case studies are illustrative. CoDEx-S test outcomes have been examined repeatedly. "
        "An independent test of the frozen selector needs paired CoDEx-M outcomes from comparable model artifacts.",
        "",
        "The benchmark’s relation labels and popularity motivation come from Safavi and Koutra. The applied-rule "
        "structural comparison follows the question studied by Meilicke et al., and the ranking preserves the installed "
        "AnyBURL/PyClause policy. "
        "[CoDEx paper](https://aclanthology.org/2020.emnlp-main.669/) · "
        "[Fine-grained rule and embedding evaluation](https://madoc.bib.uni-mannheim.de/45092/) · "
        "[AnyBURL methodology](https://link.springer.com/article/10.1007/s00778-023-00800-5)",
        "",
        "Run the following commands from the project root using the installed backend environment. "
        "The analysis requires the saved frozen rankings, original training data and validation-selected checkpoint. "
        "Input hashes are in [provenance.json](provenance.json).",
        "",
        "```bash",
        "mkdir -p runs/evidence-advantage",
        "revision=3132e426c2a6b643b70bad679905a3a6270be440",
        "for kind in entities relations; do",
        "  curl -fsSL \"https://raw.githubusercontent.com/tsafavi/codex/$revision/data/$kind/en/$kind.json\" \\",
        "    -o \"runs/evidence-advantage/$kind.json\"",
        "done",
        "for model in all general constants constants_general complex; do",
        "  OMP_NUM_THREADS=1 .backend-venv/bin/python -m kgc.research.evidence_inference \"$model\"",
        "done",
        "OPENBLAS_NUM_THREADS=1 .backend-venv/bin/python -m kgc.research.evidence_advantage",
        "```",
        "",
    ]
    (OUTPUT / "report.md").write_text("\n".join(text))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    dataset = load_dataset("data/codex-s")
    caches = {name: load_rows(WORK / f"{name}.json.gz") for name in ("complex", *FAMILIES)}
    labels = label_map()
    test_profiles, test_outcomes = assemble(dataset, caches, "test")
    valid_profiles, valid_outcomes = assemble(dataset, caches, "valid")
    test = test_profiles.merge(test_outcomes, on="query_id", validate="one_to_one")
    valid = valid_profiles.merge(valid_outcomes, on="query_id", validate="one_to_one")
    test_profiles.to_csv(OUTPUT / "test-evidence-profiles.csv", index=False)
    valid_profiles.to_csv(OUTPUT / "validation-evidence-profiles.csv", index=False)
    test_outcomes.to_csv(OUTPUT / "test-outcomes.csv", index=False)
    valid_outcomes.to_csv(OUTPUT / "validation-outcomes.csv", index=False)
    boot = FactBootstrap(test.fact)
    all_queries = np.ones(len(test), dtype=bool)
    overall = groups(test, boot, [("All queries", all_queries)])
    train_only = groups(test, boot, [("All queries, train-only tops", all_queries)], suffix="new_hits")
    evidence = []
    for family in ("general", "constants", "all"):
        for row in groups(test, boot, [(g, test[f"{family}_competition"] == g) for g in COMPETITION]):
            evidence.append(dict(family=family, **row))
    diagnostics = caches["all"]["diagnosis"]
    misranked = test.generated & (test.all_hits == 0)
    if misranked.sum() != len(diagnostics):
        raise ValueError("Incomplete generated-misrank diagnosis")
    misranks = groups(test, boot, [("Correct answer generated, ranked below first", misranked),
                                  *[(g, misranked & (test.all_competition == g)) for g in COMPETITION]])
    print("Ranking and answer-blind groups assembled", flush=True)
    diagnoses, families, ordering = diagnosis_tables(test, boot, diagnostics)
    agrees = groups(test, boot, [(g, test.agreement == g) for g in
                                  ("agree", "disagree", "general only", "constants only", "neither")])
    family_gap = groups(test, boot, [("Train-only family leaders differ", test.agreement == "disagree")],
                        "constants", "general")
    changed = test.constants_general_official_top.fillna("") != test.general_official_top.fillna("")
    ablation = groups(test, boot, [("All queries", all_queries), ("Benchmark top changed", changed),
        ("Of changes, family leaders agree", changed & (test.agreement == "agree")),
        ("Of changes, family leaders differ", changed & (test.agreement == "disagree")),
        *[(f"Of changes, {g}", changed & (test.all_competition == g)) for g in COMPETITION[1:]]],
        "constants_general", "general")
    different = test.constants_top.fillna("") != test.frequency_top.fillna("")
    frequency = groups(test, boot, [("All queries", all_queries), ("Train-only tops differ", different),
                                    ("Train-only tops coincide", ~different)], "constants", "frequency")
    structural_groups = [("Any strong general structure", (test[list(STRUCTURES)] >= .5).any(axis=1))]
    for kind in STRUCTURES:
        structural_groups.extend([(kind + " ≥ .50", test[kind] >= .5),
                                  (kind + " > 0 and < .50", (test[kind] > 0) & (test[kind] < .5))])
    structural_groups.extend([("Only weak general evidence, multiple near leaders",
                               (test.general_competition == COMPETITION[1]) & (test.general_near >= 2))])
    structure = groups(test, boot, structural_groups)
    calibration = []
    for family in ("general", "constants"):
        raw, support = test[f"{family}_lead_raw"], test[f"{family}_lead_support"]
        for confidence, mask1 in (("≥ .80", raw >= .8), ("< .80", raw < .8)):
            for bucket, mask2 in (("≤ 10", support <= 10), ("11–50", (support > 10) & (support <= 50)),
                                  ("> 50", support > 50)):
                mask = mask1 & mask2
                row = groups(test, boot, [("", mask)], suffix="new_hits")[0]
                lower, upper = boot.interval(boot.rates(test[f"{family}_new_hits"], mask))
                calibration.append(dict(family=family, confidence=confidence, support=bucket,
                                        family_rate_lo=lower, family_rate_hi=upper, **row))
    matching = match_strength(test, boot)
    relations = []
    for key, group in test.groupby("relation"):
        mask = test.relation == key
        label = f"{labels.get(key, key)} ({key})"
        row = groups(test, boot, [(label, mask)])[0]
        relations.append(dict(relation=key, median_degree=float(group.degree.median()),
                              median_all_near=float(group.all_near.median()),
                              families_disagree=int((group.agreement == "disagree").sum()),
                              strongest_structure=max(STRUCTURES, key=lambda s: (group[s] >= .5).sum())
                              if (group[list(STRUCTURES)] >= .5).any().any() else None, **row))
    eligible = sorted([r for r in relations if r["n"] >= 100], key=lambda r: r["delta"])
    extremes = eligible[:2] + eligible[-2:][::-1]
    print("Running validation-trained selectors and fact bootstrap", flush=True)
    selector_models, selector_scores, choices, selection = selector(valid, test, boot)
    choices.to_csv(OUTPUT / "selector-predictions.csv", index=False)
    seed_summary = []
    for seed in (0, 1, 2):
        saved = checked_saved(dataset, NEURAL / "final" / f"seed-{seed}", "test-queries.json.gz")
        for group, mask in [("All queries", all_queries),
                            *[(g, test.all_competition == g) for g in COMPETITION]]:
            seed_summary.append(dict(seed=seed, group=group, **boot.paired(
                [r["hits1"] for r in saved], test.all_hits, mask)))
    for filename, rows in {
        "overall": overall, "train-only-overall": train_only, "evidence-groups": evidence, "family-conflict": agrees,
        "family-accuracy-gap": family_gap,
        "constants-ablation": ablation, "frequency-baseline": frequency, "logical-structures": structure,
        "confidence-support": calibration, "matched-competition": matching, "relations": relations,
        "misrank-rescues": misranks, "misrank-candidate-evidence": diagnoses, "misrank-families": families,
        "misrank-native-ordering": ordering, "selector-metrics": selector_models,
        "selector-outcomes": selector_scores, "seed-sensitivity": seed_summary,
    }.items():
        write_csv(OUTPUT / f"{filename}.csv", rows)
    render_plot(evidence, OUTPUT)
    report = dict(seed=caches["complex"]["seed"], overall=overall, train_only=train_only,
                  diagnoses=diagnoses, families=families,
                  ordering=ordering, misranks=misranks, evidence=evidence, agreement=agrees,
                  family_gap=family_gap, ablation=ablation,
                  frequency=frequency, structure=structure, calibration=calibration, matching=matching,
                  relations=extremes, selector_models=selector_models, selector_scores=selector_scores,
                  selection=selection, n_generated=int(test.generated.sum()),
                  n_ranked_first=int(test.all_hits.sum()))
    write_json(OUTPUT / "results.json", report)
    make_report(report)
    print("Verifying concrete native rule witnesses", flush=True)
    chosen = choices["controls + rule evidence"]
    case_specs = select_cases(test, extremes, chosen)
    cases = build_cases(dataset, test, case_specs, diagnostics, labels)
    if not cases or not all(c["witnesses"] for c in cases):
        raise ValueError("Every concrete case needs a verified native training witness")
    source_files = [
        *[WORK / f"{name}.json.gz" for name in ("complex", *FAMILIES)],
        *[WORK / f"{name}.json" for name in ("entities", "relations")],
        *[FROZEN / "subsets" / f"{name}.rules" for name in FAMILIES],
        *[FROZEN / "evaluations" / name / "queries.json.gz" for name in FAMILIES],
        *[NEURAL / "final" / f"seed-{i}" / "test-queries.json.gz" for i in (0, 1, 2)],
        Path(read(NEURAL / "final-summary.json")["strongest_checkpoint_by_validation"]["checkpoint"]),
    ]
    write_json(OUTPUT / "provenance.json", dict(
        dataset=dataset.provenance, selected_seed=caches["complex"]["seed"],
        checkpoint_sha256=caches["complex"]["checkpoint_sha256"],
        files={str(p): digest(p) for p in source_files}, bootstrap_seed=851, bootstrap_draws=N_BOOT,
        verified_cases=len(cases), witness_count=sum(len(c["witnesses"]) for c in cases),
        environment=environment(), external_replication="pending",
    ))
    save_rows(OUTPUT / "misrank-diagnosis.json.gz", diagnostics)
    print(f"Saved report and {len(cases)} verified examples in {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
