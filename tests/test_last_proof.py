from kgc.data import TrainGraph
from kgc.research.evidence_intervention import strata
from kgc.research.last_proof import audit_counts, choose_removals, samples


def test_fresh_probes_are_disjoint_and_reproducible():
    draws = list(samples(32888))
    assert draws == list(samples(32888))
    flat = [i for pair in draws for group in pair for i in group]
    assert len(flat) == len(set(flat))


def test_cut_breaks_the_complete_small_proof_set_under_budget():
    labels = tuple("abcdef")
    triples = tuple((a, "r", labels[(i + 1) % len(labels)]) for i, a in enumerate(labels))
    graph = TrainGraph(triples, labels, ("r",))
    fit = [(5, [frozenset((0, 1)), frozenset((1, 2))])]
    targeted, matched, quotas = choose_removals(graph, fit, 1911, 1)
    assert targeted == {1}
    assert len(matched) == sum(quotas.values()) == 1
    assert all(len(targeted.intersection(g)) == len(matched.intersection(g)) for g in strata(graph).values())
    rows, audit = audit_counts(fit, targeted, {3})
    assert rows[0]["targeted_all_lost"] == 1 and rows[0]["matched_all_lost"] == 0
    assert audit["difference"] == 1 and not audit["passed"]  # insufficient eligible probes
