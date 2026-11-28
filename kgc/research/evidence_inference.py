"""Recover query-level evidence from the frozen CoDEx-S models."""
import argparse
from collections import defaultdict
from functools import lru_cache
from itertools import permutations
from pathlib import Path

import numpy as np

from ..backends.anyburl import ATOM
from ..data import load_dataset
from ..evaluation import FilterIndex, rank_prediction, queries
from ..io import digest, triple_digest
from .curves import load_curve
from .families import AuditedRules, VARIABLE
from .runner import load_rows, read, save_rows


FAMILIES = ("all", "general", "constants", "constants_general")
FROZEN = Path("runs/next-phase-frozen")
NEURAL = Path("runs/next-phase-neural")
WORK = Path("runs/evidence-advantage")


def top(row):
    predictions = row["top_predictions"]
    return predictions[0][0] if predictions else None


def checked_saved(dataset, folder, filename="queries.json.gz"):
    rows = load_rows(folder / filename)
    expected = list(queries(dataset.test))
    if len(rows) != len(expected):
        raise ValueError(f"Incomplete test set in {folder}")
    for q, row in zip(expected, rows):
        if (row["query_id"], (row["head"], row["relation"], row["tail"]), row["direction"]) != (
                q.query_id, q.triple, q.direction) or not row["hits_certified"]:
            raise ValueError(f"Uncertified or mismatched test query in {folder}: {q.query_id}")
    return rows


def summarize_candidates(candidates):
    scores = np.array([s for _, s in candidates])
    if not len(scores):
        return dict(top=None, count=0, score=0., margin=0., near=0, tied=0, concentration=0.)
    return dict(top=candidates[0][0], count=len(scores), score=float(scores[0]),
                margin=float(scores[0] - scores[1]) if len(scores) > 1 else float(scores[0]),
                near=int(np.count_nonzero(scores >= scores[0] - .05 - 1e-12)),
                tied=int(np.count_nonzero(scores == scores[0])),
                concentration=float(scores[0] / scores.sum()) if scores.sum() else 0.)


def syntax(rule):
    head, body = rule.expression.split("<=", 1)
    return ATOM.findall(head)[0], ATOM.findall(body)


def rule_structure(rule):
    head, body = syntax(rule)
    if len(body) == 2:
        return "two-hop composition"
    if len(body) != 1:
        return "three-hop composition" if len(body) == 3 else "other"
    atom = body[0]
    if atom[1:] == head[:0:-1]:
        return "symmetry" if atom[0] == head[0] else "inversion"
    if atom[1:] == head[1:] and atom[0] != head[0]:
        return "subsumption"
    return "other"


def pattern(rule):
    """Canonical relation/argument shape, masking constant identities."""
    head, body = syntax(rule)
    def encode(atoms):
        variables, constants = {}, {}
        terms = []
        for rel, a, b in atoms:
            pair = []
            for token in (a, b):
                vocab, prefix = (variables, "v") if VARIABLE.fullmatch(token) else (constants, "c")
                pair.append(prefix + str(vocab.setdefault(token, len(vocab))))
            terms.append((rel, *pair))
        return tuple(terms)
    return min(encode((head, *atoms)) for atoms in permutations(body))


def native_rule_info(backend):
    native_lines = backend.loader.get_rules()
    if len(native_lines) != len(backend.rules):
        raise ValueError("Native rule IDs differ from the frozen catalog")
    for line, rule in zip(native_lines, backend.rules):
        fields = line.split("\t")
        if fields[-1].strip() != rule.expression or tuple(map(int, fields[:2])) != (rule.predictions, rule.support):
            raise ValueError("Native rule ID mapping differs from the frozen catalog")
    options = backend.effective_loader_options

    @lru_cache(maxsize=None)
    def info(i):
        rule = backend.rules[i]
        head, body = syntax(rule)
        if not body:
            family, prefix = "Z", "z"
        elif rule.kind == "relational_path":
            family, prefix = "B", "b"
        elif head[1] == head[2] or "me_myself_i" in head[1:]:
            raise ValueError("Reflexive rule confidence needs a separate native audit")
        elif any(not VARIABLE.fullmatch(t) for atom in body for t in atom[1:]):
            family, prefix = "Uc", "c"
        else:
            family, prefix = "Ud", "d"
        confidence = rule.support / (rule.predictions + options[prefix + "_num_unseen"])
        score = options.get(prefix + "_weight", 1) * confidence
        return dict(expression=rule.expression, family=family, score=score, raw=rule.confidence,
                    support=rule.support, predictions=rule.predictions, length=rule.length,
                    structure=rule_structure(rule) if family == "B" else None)
    return info


def query_rows(dataset):
    for split in ("valid", "test"):
        qs = list(queries(getattr(dataset, split), split))
        yield split, qs, FilterIndex(dataset.positives_for_filter(split))


def groundings(backend, triples):
    """Get native nonempty-body groundings for requested triples."""
    results = {}
    triples = sorted(set(triples))
    id_to_entity = {v: k for k, v in backend.loader.get_entity_index().items()}
    id_to_relation = {v: k for k, v in backend.loader.get_relation_index().items()}

    def edge(tokens):
        h, r, t = tokens
        return id_to_entity[h], id_to_relation[r], id_to_entity[t]

    for start in range(0, len(triples), 32):
        backend.scorer.calculate_scores(triples=triples[start:start + 32], loader=backend.loader)
        targets, ids, grounds = backend.scorer.get_explanations(as_string=False)
        for target, rule_ids, rule_grounds in zip(targets, ids, grounds):
            by_rule = {}
            for i, instances in zip(rule_ids, rule_grounds):
                decoded = [tuple(edge(tokens) for tokens in instance) for instance in instances]
                if any(e not in backend.training_edges for instance in decoded for e in instance):
                    raise ValueError("Native grounding has a non-training edge")
                by_rule[i] = decoded
            results[edge(target)] = by_rule
    return results


def infer_rules(dataset, family):
    path = FROZEN / "subsets" / f"{family}.rules"
    folder = FROZEN / "evaluations" / family
    metrics = read(folder / "metrics.json")
    training = read(FROZEN / "mining/training.json")
    if training["training_graph_sha256"] != triple_digest(dataset.graph.triples):
        raise ValueError("Rule inventory was mined on a different training graph")
    if metrics["subset_sha256"] != digest(path):
        raise ValueError(f"Frozen subset changed: {path}")
    saved = checked_saved(dataset, folder)
    if family == "constants_general":
        # Only the test ablation is used. Its training-only top comes from the
        # original, unfiltered candidate list.
        training_filters = FilterIndex(dataset.graph.triples)
        return {"test": [
            dict(query_id=q.query_id,
                 profile=summarize_candidates([(e, s) for e, s in row["returned_candidates"]
                                               if e not in training_filters.answers[q.model_input]]),
                 official_top=top(row), hits=row["hits1"], generated=row["true_returned"])
            for q, row in zip(queries(dataset.test), saved)]}

    qa_options = {"collect_rules": True}
    backend = AuditedRules(dataset.graph, path, certify_support=True, qa_options=qa_options,
                          retain_catalog_metadata=False)
    if (backend.effective_loader_options != metrics["effective_loader_options"]
            or {**backend.effective_qa_options, "collect_rules": False} != metrics["effective_qa_options"]
            or not backend.certify_support):
        raise ValueError("Native ranking options differ from the saved run")
    info = native_rule_info(backend)
    train = FilterIndex(dataset.graph.triples)
    output, diagnosis = {}, []
    requested = defaultdict(set)

    for split, qs, official in query_rows(dataset):
        grouped = defaultdict(list)
        for index, q in enumerate(qs):
            grouped[q.model_input].append((index, q))
        rows = [None] * len(qs)
        for index, (masked, siblings) in enumerate(grouped.items(), 1):
            pred = backend.predict(masked)
            ids = backend.qa.get_rules(as_string=False)[0] if pred.candidates else []
            if len(ids) != len(pred.candidates):
                raise ValueError("Native rules/candidates alignment mismatch")
            unseen = [(e, s) for e, s in pred.candidates if e not in train.answers[masked]]
            profile = summarize_candidates(unseen)
            rules_by_candidate = {e: r for (e, _), r in zip(pred.candidates, ids)}
            first = profile["top"]
            if first:
                best = info(rules_by_candidate[first][0])
                if not np.isclose(best["score"], profile["score"], atol=1e-12, rtol=1e-12):
                    raise ValueError("Strongest native rule does not match the QA scalar")
                profile["lead"] = best
                profile["lead_rule_count"] = len(rules_by_candidate[first])
            if family == "general":
                strongest = {}
                for i in {i for e, _ in unseen for i in rules_by_candidate[e]}:
                    rule = info(i)
                    kind = rule["structure"]
                    if rule["score"] > strongest.get(kind, 0):
                        strongest[kind] = rule["score"]
                profile["structures"] = strongest
            for row_index, q in siblings:
                if split == "test":
                    row = saved[row_index]
                    if pred.candidates != [tuple(pair) for pair in row["returned_candidates"]]:
                        raise ValueError(f"Frozen replay differs for {family} {q.query_id}")
                else:
                    row = rank_prediction(q, pred, dataset.graph.entities, official)
                winner = top(row)
                rows[row_index] = dict(query_id=q.query_id, profile=profile, official_top=winner,
                                       hits=row["hits1"], generated=row["true_returned"])
                if split == "test" and family == "all" and row["true_returned"] and not row["hits1"]:
                    candidates = []
                    for entity in (q.answer, winner):
                        rule_ids = rules_by_candidate[entity]
                        target = masked.triple(entity)
                        requested[target].update(rule_ids)
                        candidates.append(dict(entity=entity, native_score=dict(pred.candidates)[entity],
                                               native_rule_ids=rule_ids, triple=target))
                    diagnosis.append(dict(query_id=q.query_id, candidates=candidates))
            if index % 500 == 0:
                print(f"{family} {split}: {index}/{len(grouped)} masked queries", flush=True)
        output[split] = rows
    if diagnosis:
        print(f"{family}: recovering explanations for {len(requested)} candidate triples", flush=True)
        grounded = groundings(backend, requested)
        @lru_cache(maxsize=None)
        def rule_pattern(i):
            return pattern(backend.rules[i])

        for pair in diagnosis:
            for candidate in pair["candidates"]:
                rule_ids = candidate.pop("native_rule_ids")
                native_groundings = {i: grounds for i, grounds in grounded.get(tuple(candidate["triple"]), {}).items()
                                     if backend.rules[i].length}
                attributed = {i for i in rule_ids if backend.rules[i].length}
                candidate.update(lead=info(rule_ids[0]), max_raw=max(info(i)["raw"] for i in rule_ids),
                                 rule_count=len(set(rule_ids)), pattern_count=len({rule_pattern(i) for i in rule_ids}),
                                 grounding_count=sum(len(native_groundings.get(i, ())) for i in attributed),
                                 grounding_attribution_agrees=attributed == set(native_groundings),
                                 score_sequence=[info(i)["score"] for i in rule_ids],
                                 witnesses=[dict(**info(i), groundings=native_groundings.get(i, [])[:2])
                                            for i in rule_ids[:3]])
        output["diagnosis"] = sorted(diagnosis, key=lambda row: tuple(int(v) if j == 1 else v
                                      for j, v in enumerate(row["query_id"].split(":"))))
    return output


def infer_complex(dataset):
    import torch

    torch.set_num_threads(1)
    summary = read(NEURAL / "final-summary.json")
    chosen = summary["strongest_checkpoint_by_validation"]
    source = Path(chosen["checkpoint"])
    backend, _ = load_curve(dataset.graph, source.parent)
    seed = chosen["seed"]
    saved = checked_saved(dataset, NEURAL / "final" / f"seed-{seed}", "test-queries.json.gz")
    training = FilterIndex(dataset.graph.triples)
    output = {"seed": seed, "checkpoint_sha256": digest(source)}
    for split, qs, official in query_rows(dataset):
        cache, rows = {}, []
        for i, q in enumerate(qs):
            masked = q.model_input
            if masked not in cache:
                pred = backend.predict(masked)
                unseen = sorted(((e, s) for e, s in pred.candidates if e not in training.answers[masked]),
                                key=lambda x: (-x[1], x[0]))
                tied = len(unseen) > 1 and unseen[0][1] == unseen[1][1]
                cache[masked] = pred, unseen[0][0], tied
            pred, first, tied = cache[masked]
            if split == "test":
                row = saved[i]
                replay = rank_prediction(q, pred, dataset.graph.entities, official)
                if (top(row), row["rank"]) != (top(replay), replay["rank"]):
                    raise ValueError(f"ComplEx checkpoint replay differs for {q.query_id}")
            else:
                row = rank_prediction(q, pred, dataset.graph.entities, official)
            rows.append(dict(query_id=q.query_id, top=first, tied=tied, official_top=top(row), hits=row["hits1"]))
        output[split] = rows
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=(*FAMILIES, "complex"))
    args = parser.parse_args()
    dataset = load_dataset("data/codex-s")
    WORK.mkdir(parents=True, exist_ok=True)
    result = infer_complex(dataset) if args.model == "complex" else infer_rules(dataset, args.model)
    destination = WORK / f"{args.model}.json.gz"
    temporary = destination.with_suffix(".tmp")
    save_rows(temporary, result)
    temporary.replace(destination)
    print(f"Saved {destination}", flush=True)


if __name__ == "__main__":
    main()
