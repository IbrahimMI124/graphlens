"""Training-only structural statistics. Pattern strengths are empirical ratios."""
from collections import Counter, defaultdict
from itertools import product
import numpy as np


class GraphDiagnostics:
    def __init__(self, graph):
        self.graph = graph
        self.edges = set(graph.triples)
        self.in_degree = Counter(t for _, _, t in graph.triples)
        self.out_degree = Counter(h for h, _, _ in graph.triples)
        self.degree = {e: self.in_degree[e] + self.out_degree[e] for e in graph.entities}
        self.frequency = Counter(r for _, r, _ in graph.triples)
        self.pairs = {r: set() for r in graph.relations}
        self.out = defaultdict(set)
        self.neighbors = defaultdict(set)
        for h, r, t in graph.triples:
            self.pairs[r].add((h, t))
            self.out[h].add(t)
            self.neighbors[h].add(t)
            self.neighbors[t].add(h)
        self.thresholds = np.quantile(list(self.degree.values()), [1/3, 2/3]).tolist()
        self.relation_stats = {}
        for r, pairs in self.pairs.items():
            tph = len(pairs) / len({h for h, _ in pairs}) if pairs else 0
            hpt = len(pairs) / len({t for _, t in pairs}) if pairs else 0
            cardinality = (("many" if hpt >= 1.5 else "one") + "-to-" + ("many" if tph >= 1.5 else "one")) if pairs else "unobserved"
            reverse = {(t, h) for h, t in pairs}
            self.relation_stats[r] = {"relation_frequency": len(pairs), "tails_per_head": tph,
                "heads_per_tail": hpt, "cardinality": cardinality,
                "symmetry_strength": len(pairs & reverse) / len(pairs) if pairs else None,
                "symmetry_support": len(pairs & reverse)}

    def degree_group(self, entity):
        d = self.degree[entity]
        return "low" if d <= self.thresholds[0] else "medium" if d <= self.thresholds[1] else "high"

    def query_features(self, row):
        h, r, t = row["head"], row["relation"], row["tail"]
        known = t if row["direction"] == "head" else h
        target = h if row["direction"] == "head" else t
        return {"head_degree": self.degree[h], "tail_degree": self.degree[t],
                "head_in_degree": self.in_degree[h], "head_out_degree": self.out_degree[h],
                "tail_in_degree": self.in_degree[t], "tail_out_degree": self.out_degree[t],
                "known_degree_group": self.degree_group(known),
                "target_degree_group": self.degree_group(target),
                "directed_twohop_paths_to_truth": sum(t in self.out[m] for m in self.out[h]),
                "undirected_common_neighbors_to_truth": len(self.neighbors[h] & self.neighbors[t]),
                **self.relation_stats[r]}

    def patterns(self, composition_budget=2_000_000):
        """All ordered inverse/subsumption pairs; composition skipped explicitly if too big.

        Composition confidence = observed head pairs / distinct body endpoint pairs.
        No held-out edges, no implication that absent endpoints are false.
        """
        records = []
        for r, s in product(self.graph.relations, repeat=2):
            a, b = self.pairs[r], self.pairs[s]
            if not a:
                continue
            if r != s:
                for kind, comparison in (("inverse", {(t, h) for h, t in b}), ("subsumption", b)):
                    support = len(a & comparison)
                    records.append({"pattern": kind, "body": r, "head": s,
                                    "support": support, "body_pairs": len(a), "strength": support / len(a)})
        adjacency = {}
        for r in self.graph.relations:
            adj = defaultdict(set)
            for h, t in self.pairs[r]:
                adj[h].add(t)
            adjacency[r] = adj
        for r, s in product(self.graph.relations, repeat=2):
            wedge_count = sum(len(adjacency[s][m]) for _, m in self.pairs[r])
            if wedge_count > composition_budget:
                records.append({"pattern": "composition", "body": [r, s], "head": None,
                                "status": "skipped_budget", "wedges": wedge_count, "strength": None})
                continue
            body = {(h, t) for h, m in self.pairs[r] for t in adjacency[s][m]}
            if not body:
                continue
            for head in self.graph.relations:
                support = len(body & self.pairs[head])
                records.append({"pattern": "composition", "body": [r, s], "head": head,
                                "support": support, "body_pairs": len(body), "strength": support / len(body),
                                "status": "exact"})
        for r, stats in self.relation_stats.items():
            inv = [x for x in records if x["pattern"] == "inverse" and x["body"] == r]
            sub = [x for x in records if x["pattern"] == "subsumption" and x["body"] == r]
            comp = [x for x in records if x["pattern"] == "composition" and x["head"] == r]
            for name, group in (("inverse", inv), ("subsumption", sub), ("composition", comp)):
                best = max(group, key=lambda x: x["strength"], default=None)
                stats[f"best_{name}_strength"] = best["strength"] if best else None
                stats[f"best_{name}_support"] = best["support"] if best else None
        return records


def compare_rows(embedding_rows, rule_rows, graph, strong_confidence=0.5, strong_support=5, rule_catalog=None):
    """Merge one-to-one; missing queries are errors, not silently excluded observations."""
    embed = {x["query_id"]: x for x in embedding_rows}
    rule = {x["query_id"]: x for x in rule_rows}
    if len(embed) != len(embedding_rows) or len(rule) != len(rule_rows) or embed.keys() != rule.keys():
        raise ValueError("Baselines must have exactly the same unique query IDs")
    diag = GraphDiagnostics(graph)
    diag.patterns()
    rows = []
    for qid, e in embed.items():
        r = rule[qid]
        identity = ("head", "relation", "tail", "direction", "triple_id")
        if any(e[k] != r[k] for k in identity):
            raise ValueError("Mismatched query identity")
        row = {k: e[k] for k in ("query_id", *identity)}
        row.update(diag.query_features(row))
        for prefix, source in (("embedding", e), ("rule", r)):
            row.update({f"{prefix}_{k}": v for k, v in source.items() if k not in row})
        answer = row["head"] if row["direction"] == "head" else row["tail"]
        def resolve(items):
            return [rule_catalog[x] if isinstance(x, int) else rule_catalog[x["rule_id"]] if "rule_id" in x else x for x in items]
        evidence = resolve(r.get("candidate_evidence", {}).get(answer, []))
        strong = any(x.get("confidence", 0) >= strong_confidence and x.get("support", 0) >= strong_support
                     for x in evidence)
        state = ("backend_cannot_represent_query" if r.get("backend_metadata", {}).get("query_representable") is False else
                 "no_rule_applies" if not r["covered"] else
                 "strong_rule_supports_truth" if strong else
                 "rule_generates_truth" if r["true_returned"] else
                 "rules_omit_truth" if r["support_complete"] else "truth_not_returned_support_unknown")
        row["rule_truth_diagnostic"] = state
        row["rule_best_truth_confidence"] = max((x.get("confidence", 0) for x in evidence), default=None)
        row["rule_best_truth_support"] = max((x.get("support", 0) for x in evidence), default=None)
        row["rule_min_truth_length"] = min((x["length"] for x in evidence if x.get("length") is not None), default=None)
        kinds = {x.get("kind", "unknown") for items in r.get("candidate_evidence", {}).values() for x in resolve(items)}
        row["rule_evidence_kind"] = ("mixed" if len(kinds) > 1 else next(iter(kinds), "unknown"))
        for k in (1, 10):
            a, b = e[f"hits{k}"], r[f"hits{k}"]
            row[f"error_category_hits{k}"] = ("both_correct" if a and b else "only_embeddings" if a else
                                               "only_rules" if b else "both_incorrect")
        rows.append(row)
    return rows
