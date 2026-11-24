"""Native rule families and frozen physical subsets; no custom rule mining."""
from dataclasses import asdict
from pathlib import Path
import re
from ..backends.anyburl import ATOM, parse_rule, AnyBURLBackend
from ..io import digest, write_json
from .resources import CoolingBreaks

VARIABLE = re.compile(r"^[A-Z]$")
FAMILIES = ("B", "Uc", "Ud", "XXuc", "XXud", "Z")
FLAGS = dict(zip(FAMILIES, ("load_b_rules", "load_u_c_rules", "load_u_d_rules", "load_u_xxc_rules", "load_u_xxd_rules", "load_zero_rules")))


def describe(line):
    rule = parse_rule(line)
    head_text, body_text = rule.expression.split("<=", 1)
    head = ATOM.findall(head_text)[0]
    body = ATOM.findall(body_text)
    terms = [t for atom in [head] + body for t in atom[1:]]
    constants = {t for t in terms if not VARIABLE.fullmatch(t) and t != "me_myself_i"}
    body_constants = {t for atom in body for t in atom[1:] if not VARIABLE.fullmatch(t) and t != "me_myself_i"}
    if not body:
        family = "Z"
    elif head[1] == head[2] or "me_myself_i" in head[1:]:
        family = "XXuc" if body_constants else "XXud"
    elif all(VARIABLE.fullmatch(t) for t in head[1:]) and not body_constants:
        family = "B"
    elif any(not VARIABLE.fullmatch(t) for t in head[1:]):
        family = "Uc" if body_constants else "Ud"
    else:
        raise ValueError(f"Unrecognized native rule shape: {rule.expression}")
    # Mining provenance is not encoded by the serialized implication. These are
    # structural tags, never claims that MAX_LENGTH_GROUNDED_CYCLIC produced it.
    vertices = {t for atom in body for t in atom[1:]}
    edges = [(a[1], a[2]) for a in body]
    parent = {v: v for v in vertices}
    def find(v):
        while parent[v] != v:
            v = parent[v]
        return v
    cycle = False
    for a, b in edges:
        x, y = find(a), find(b)
        if x == y:
            cycle = True
        else:
            parent[x] = y
    return {**asdict(rule), "native_family": family, "constant_bearing": bool(constants),
            "unconditional_prior": family == "Z", "general_relational": family == "B",
            "reflexive_head": family in ("XXuc", "XXud"), "body_has_cycle": cycle,
            "head_constant_in_body": bool(set(head[1:]) & body_constants),
            "grounded_cyclic_mining_origin": "not identifiable from serialized rules"}


def make_subsets(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    lines = [x for x in source.read_text().splitlines() if x.strip()]
    catalog = [describe(x) for x in lines]
    conditions = {"all": lambda r: True,
                  "constants": lambda r: r["constant_bearing"] and not r["unconditional_prior"],
                  "general": lambda r: r["general_relational"],
                  "constants_general": lambda r: (r["constant_bearing"] and not r["unconditional_prior"]) or r["general_relational"],
                  "zero": lambda r: r["native_family"] == "Z",
                  "reflexive": lambda r: r["reflexive_head"],
                  "shared_constant_structure": lambda r: r["head_constant_in_body"],
                  "closed_body_structure": lambda r: r["body_has_cycle"]}
    for family in FAMILIES:
        conditions[family] = lambda r, f=family: r["native_family"] == f
    for length in (1, 2, 3):
        conditions[f"general_le{length}"] = lambda r, n=length: r["general_relational"] and r["length"] <= n
        conditions[f"fixed_constants_general_le{length}"] = lambda r, n=length: (
            r["constant_bearing"] and not r["unconditional_prior"]) or (r["general_relational"] and r["length"] <= n)
    manifests = {}
    for name, predicate in conditions.items():
        indices = [i for i, r in enumerate(catalog) if predicate(r)]
        p = output / f"{name}.rules"
        p.write_text("".join(lines[i] + "\n" for i in indices))
        manifests[name] = {"path": str(p), "n_rules": len(indices), "sha256": digest(p), "source_indices": indices}
    fixed = [{i for i in manifests[f"fixed_constants_general_le{n}"]["source_indices"] if catalog[i]["constant_bearing"]} for n in (1, 2, 3)]
    assert fixed[0] == fixed[1] == fixed[2]
    write_json(output / "catalog.json", catalog)
    write_json(output / "subsets.json", {"source": str(source), "source_sha256": digest(source),
              "subsets": manifests, "constant_inventory_identical_across_length_ablations": True,
              "classification": "native-family shape mapping; independently check with PyClause family loader flags"})
    return manifests


class AuditedRules(AnyBURLBackend):
    """Same maxplus and confidence defaults; completeness is an explicit policy.

    This does not turn abstention into a full-universe zero-score ranking or MRR.
    """
    def __init__(self, graph, rules_file, top_k=None, certify_support=False, **kwargs):
        if top_k is None:
            top_k = len(graph.entities) + 1
        super().__init__(graph, rules_file, top_k=top_k, evidence_mode="none", **kwargs)
        self.cooling = CoolingBreaks()
        self.native_loaded_count = len(self.loader.get_rules())
        self.certify_support = certify_support
        def reflexive_nonzero(rule):
            if not rule.length:
                return False
            _, first, second = ATOM.findall(rule.expression.split("<=", 1)[0])[0]
            return first == second or "me_myself_i" in (first, second)
        if certify_support and any(reflexive_nonzero(r) for r in self.rules):
            self.certify_support = False  # Native QA/PredictionHandler discrepancy found by executable audit.
        if certify_support:
            if top_k <= len(graph.entities):
                raise ValueError("Certification requires topk greater than the entire entity universe")
            q, l = self.effective_qa_options, self.effective_loader_options
            if any(q[k] != -1 for k in ("disc_at_least", "hard_stop_at", "num_top_rules")) or any(l[k] != -1 for k in ("b_max_branching_factor", "d_max_branching_factor")):
                raise ValueError("Cannot certify support while pruning/stopping is active")

    def predict(self, query):
        result = super().predict(query)
        result.exhaustive_support = self.certify_support and result.metadata.get("query_representable", True)
        result.metadata["support_policy"] = ("exhaustive loaded-rule candidate set, verified by smoke/prefix checks; uncovered=abstain/miss, not a full-universe tie ranking" if result.exhaustive_support else "uncertified")
        result.metadata["ranking"] = "exhaustive supported candidates; abstain=miss" if result.exhaustive_support else "potentially incomplete"
        self.cooling.rest()
        return result

    def score_triples(self, triples):
        # PredictionHandler does not support Z rules. Native QA scoring preserves
        # their weights; the score convention for this case is tail-query maxplus.
        # Use exactly the same QA score convention in EVERY new subset, even
        # those with no Z rules. This is versioned separately from legacy scoring.
        import numpy as np
        from ..evaluation import ModelQuery
        cached, scores, support = dict(getattr(self, "classification_query_cache", {})), [], []
        for h, r, t in triples:
            q = ModelQuery(h, r, "tail")
            if q not in cached:
                cached[q] = dict(self.predict(q).candidates)
            scores.append(cached[q].get(t, 0.))
            support.append(t in cached[q])
        return np.asarray(scores), np.asarray(support)

    def reuse_masked_candidates_for_classification(self, predictions):
        """Reuse raw answer-blind tail outputs from this backend's evaluation.

        No evaluator-filtered list, gold answer, rank or label enters the cache.
        The caller supplies (ModelQuery, raw candidates) pairs from this instance,
        never evaluator rows or held-out answers. Scores/calibration are unchanged.
        """
        from ..evaluation import ModelQuery
        cached = {}
        for query, candidates in predictions:
            if not isinstance(query, ModelQuery) or query.direction != "tail":
                raise ValueError("Classification reuse accepts masked tail queries only")
            cached[query] = dict(candidates)
        self.classification_query_cache = cached
