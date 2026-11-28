import numpy as np

from kgc.data import TrainGraph, load_dataset
from kgc.research.evidence_intervention import evidence_scores, masks, strata, training_audit


def test_masks_exactly_match_relation_and_both_endpoint_degree_strata():
    graph = load_dataset("data/codex-s").graph
    scores = np.random.default_rng(41).random(len(graph.triples))
    targeted, matched, quota = masks(graph, scores, 751)
    assert (targeted, matched, quota) == masks(graph, scores, 751)
    assert len(targeted) == len(matched) == 3289
    for key, ids in strata(graph).items():
        self_targeted = set(ids) & targeted
        assert len(self_targeted) == len(set(ids) & matched) == quota[key]
        chosen = sorted((scores[i] for i in self_targeted), reverse=True)
        assert chosen == sorted((scores[i] for i in ids), reverse=True)[:len(chosen)]


def test_probe_normalization_and_count_each_lost_grounding_once():
    graph = TrainGraph((("a", "r", "b"), ("b", "r", "c"), ("a", "r", "c")), tuple("abc"), ("r",))
    probes = [(0, [frozenset((0, 1)), frozenset((1, 2))]), (2, [frozenset((0,))])]
    assert np.allclose(evidence_scores(graph, iter(probes)), [1.25, .5, .25])
    rows, stats = training_audit(iter(probes), {0, 1}, {2})
    assert rows[0]["targeted_lost"] == 2
    assert rows[0]["matched_lost"] == 1
    assert stats["difference"] == .75 and stats["passed"]


def test_greedy_edge_selection_skips_the_redundant_edge():
    from kgc.research.evidence_intervention import greedy_masks

    labels = tuple("abcdef")
    triples = tuple((h, "r", labels[(i + 1) % len(labels)]) for i, h in enumerate(labels))
    graph = TrainGraph(triples, labels, ("r",))
    probes = [
        (0, [frozenset((0, 1))]), (1, [frozenset((0, 1))]), (2, [frozenset((2,))]),
    ]
    targeted, matched, quota, scores = greedy_masks(graph, iter(probes), 851, retain=2 / 3)
    assert len(set((0, 1)) & targeted) == 1
    assert 2 in targeted
    assert len(matched) == sum(quota.values()) == 2
    assert scores[0] == scores[1] == 2


def test_greedy_probes_exclude_the_previous_pilot():
    from kgc.research.evidence_intervention import GREEDY_FIT, PROBES_PER_GROUP, SEEDS, probe_split

    n = 32888
    prior = set(np.concatenate([ids for draw in range(len(SEEDS)) for ids in probe_split(n, draw)]))
    fit, audit = map(set, probe_split(n, 0, greedy=True))
    assert len(fit) == GREEDY_FIT and len(audit) == PROBES_PER_GROUP
    assert fit.isdisjoint(audit) and prior.isdisjoint(fit | audit)
