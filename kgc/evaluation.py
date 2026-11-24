"""Answer-blind inference; evaluator-owned filtering; honest censored rankings."""
from dataclasses import dataclass, field
from collections import defaultdict
from collections import OrderedDict
import math
import time
import numpy as np


@dataclass(frozen=True)
class ModelQuery:
    known: str
    relation: str
    direction: str

    def __post_init__(self):
        if self.direction not in ("head", "tail"):
            raise ValueError(self.direction)

    def triple(self, candidate):
        return ((candidate, self.relation, self.known) if self.direction == "head"
                else (self.known, self.relation, candidate))


@dataclass(frozen=True)
class Query:
    query_id: str
    triple_id: str
    triple: tuple
    direction: str

    @property
    def model_input(self):
        h, r, t = self.triple
        return ModelQuery(t if self.direction == "head" else h, r, self.direction)

    @property
    def answer(self):
        return self.triple[0 if self.direction == "head" else 2]


def queries(triples, split="test"):
    for i, triple in enumerate(triples):
        for direction in ("head", "tail"):
            yield Query(f"{split}:{i}:{direction}", f"{split}:{i}", triple, direction)


@dataclass
class Prediction:
    candidates: list  # (original entity ID, RAW score), higher = better
    full_ranking: bool = False
    exhaustive_support: bool = False
    evidence: dict = field(default_factory=dict)  # entity -> list of rule records
    metadata: dict = field(default_factory=dict)
    order_is_ranking: bool = False  # E.g. native AnyBURL maxplus lexicographic order


class FilterIndex:
    def __init__(self, positives):
        self.answers = defaultdict(set)
        for h, r, t in positives:
            self.answers[ModelQuery(h, r, "tail")].add(t)
            self.answers[ModelQuery(t, r, "head")].add(h)

    def alternatives(self, query):
        return self.answers[query.model_input] - {query.answer}


def rank_prediction(query, prediction, entities, filters):
    universe = set(entities)
    if query.answer not in universe:
        raise ValueError("Target answer is outside the declared entity universe")
    pairs = prediction.candidates
    ids = [e for e, _ in pairs]
    if len(set(ids)) != len(ids) or not set(ids) <= universe:
        raise ValueError("Duplicate or out-of-universe candidate")
    if any(not math.isfinite(float(s)) for _, s in pairs):
        raise ValueError("Scores must be finite")
    if prediction.full_ranking and set(ids) != universe:
        raise ValueError("A full ranking must score the entire shared entity universe")
    alternatives = filters.alternatives(query)
    filtered = [(e, float(s)) for e, s in pairs if e not in alternatives]
    scores = dict(filtered)
    covered = bool(pairs)  # before filtering, independent of correctness
    returned_true = query.answer in scores
    rank = None
    if returned_true:
        if prediction.order_is_ranking:
            rank = next(i for i, (e, _) in enumerate(filtered, 1) if e == query.answer)
        else:
            target = scores[query.answer]
            greater = sum(s > target for s in scores.values())
            equal = sum(s == target for s in scores.values())
            rank = 1 + greater + (equal - 1) / 2  # realistic (average) tie rank
    exact = prediction.full_ranking
    # A truncated retrieval ranking cannot certify misses after evaluator-side filtering.
    # Display retrieved-list outcomes, never call these full-ranking metrics.
    hits = {k: int(rank is not None and rank <= k) for k in (1, 10)}
    support_complete = prediction.exhaustive_support or exact
    return {"rank": rank, "score": scores.get(query.answer), "covered": covered,
            "true_returned": returned_true, "ranking_exact": exact,
            "support_complete": support_complete, "returned_count": len(pairs),
            "filtered_returned_count": len(filtered),
            "hits1": hits[1], "hits10": hits[10],
            "hits_certified": exact or support_complete,
            "reciprocal_rank": (1 / rank) if exact else None,
            "retrieved_reciprocal_rank": (1 / rank) if rank else 0.0,
            "rank_policy": "backend native lexicographic" if prediction.order_is_ranking else "realistic average-score ties",
            "top_predictions": (filtered if prediction.order_is_ranking else sorted(filtered, key=lambda x: (-x[1], x[0])))[:10]}


def evaluate(backend, triples, entities, positives_for_filter, split="test", limit=None, cache_size=0, progress_every=0):
    """Only masked ModelQuery objects, never target triples, reach predict()."""
    filters = FilterIndex(positives_for_filter)
    results = []
    inference_seconds = 0.0
    cache, cache_hits = OrderedDict(), 0
    for index, q in enumerate(queries(triples[:limit] if limit is not None else triples, split), 1):
        start = time.perf_counter()
        if q.model_input in cache:
            pred = cache.pop(q.model_input)
            cache[q.model_input] = pred
            cache_hits += 1
        else:
            pred = backend.predict(q.model_input)
            if cache_size:
                cache[q.model_input] = pred
                if len(cache) > cache_size:
                    cache.popitem(last=False)
        inference_seconds += time.perf_counter() - start
        row = {"query_id": q.query_id, "triple_id": q.triple_id, "head": q.triple[0],
               "relation": q.triple[1], "tail": q.triple[2], "direction": q.direction}
        row.update(rank_prediction(q, pred, entities, filters))
        row["candidate_evidence"] = pred.evidence
        row["backend_metadata"] = pred.metadata
        row["returned_candidates"] = pred.candidates if not pred.full_ranking else row["top_predictions"]
        results.append(row)
        if progress_every and index % progress_every == 0:
            print(f"{type(backend).__name__}: evaluated {index} {split} queries", flush=True)
    return results, {**summarize(results), "inference_seconds": inference_seconds,
                     "prediction_cache_size": cache_size, "prediction_cache_hits": cache_hits,
                     "backend_calls": len(results) - cache_hits,
                     "inference_timing_scope": "backend prediction plus answer-blind cache lookups; excludes filtering and serialization"}


def summarize(rows):
    if not rows:
        return {"n_queries": 0}
    n = len(rows)
    exact = all(r["ranking_exact"] for r in rows)
    certified = all(r["hits_certified"] for r in rows)
    covered = [r for r in rows if r["covered"]]
    return {"n_queries": n, "hits_metric_status": "exact" if certified else "retrieved-list only; censored",
            "hits1": sum(r["hits1"] for r in rows) / n,
            "hits10": sum(r["hits10"] for r in rows) / n,
            "mrr_exact": float(np.mean([r["reciprocal_rank"] for r in rows])) if exact else None,
            "retrieved_rr_proxy": float(np.mean([r["retrieved_reciprocal_rank"] for r in rows])),
            "coverage": len(covered) / n,
            "n_covered": len(covered),
            "covered_hits1": float(np.mean([r["hits1"] for r in covered])) if covered else None,
            "overall_hits1_uncovered_miss": sum(r["hits1"] for r in rows) / n}
