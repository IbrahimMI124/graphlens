from importlib.util import find_spec

import pytest

from kgc.data import load_dataset
from kgc.research.families import AuditedRules
from kgc.research.removal_replication import CONDITIONS, SEEDS, grounding_keys, make_pair
from kgc.research.structure import native_vocabulary


def test_new_pairs_use_distinct_training_masks():
    data = load_dataset("data/codex-s")
    hashes = set()
    for draw in range(len(SEEDS)):
        pair = make_pair(data, draw)
        assert pair == make_pair(data, draw)
        targeted, control = (pair[name][1] for name in CONDITIONS)
        assert targeted["removed_by_relation"] == control["removed_by_relation"]
        assert targeted["target_incident_removed"] > control["target_incident_removed"]
        hashes.update((targeted["training_graph_sha256"], control["training_graph_sha256"]))
    assert len(hashes) == 2 * len(SEEDS)


@pytest.mark.skipif(find_spec("c_clause") is None, reason="Native PyClause is required")
def test_native_body_enumerates_both_paths_and_loses_one(tmp_path):
    from kgc.data import TrainGraph

    rules = tmp_path / "test.rules"
    rules.write_text("8\t6\t0.75\tgoal(X,Y) <= left(X,A), right(A,Y)\n")
    edges = (
        ("a", "left", "b"), ("b", "right", "e"),
        ("a", "left", "c"), ("c", "right", "e"), ("c", "goal", "d"),
    )
    graph = TrainGraph(edges, tuple("abcde"), ("goal", "left", "right"))
    indices = native_vocabulary(graph)
    original = AuditedRules(graph, rules, token_indices=indices)
    altered = AuditedRules(graph.with_triples(edges[1:]), rules, token_indices=indices)
    fact = ("a", "goal", "e")
    before = grounding_keys(original, [fact])[fact]
    after = grounding_keys(altered, [fact])[fact]
    assert len(before) == 2
    assert len(after) == 1
    assert before - after == {("goal(X,Y)<=left(X,A),right(A,Y)", edges[:2])}


def test_report_contrast_uses_paired_changes_and_equal_draw_weight():
    import numpy as np

    from kgc.research.removal_replication_report import METHODS, bootstrap

    draws = []
    for targeted_hits in ((0, 1), (1, 1), (0, 0)):
        cells = {"query_ids": np.array(["test:0:head", "test:0:tail"])}
        for arm_index, arm in enumerate(CONDITIONS):
            for method in METHODS:
                n_models = 3 if method in ("neural", "fixed_updates") else 2 if method.startswith("fresh_") else 1
                hits = targeted_hits if arm_index == 0 and method == "neural" else (0, 0)
                cells[f"{arm}/{method}"] = np.tile(np.array(hits)[None, :, None], (n_models, 1, 1))
        draws.append(cells)
    rows = [r for r in bootstrap(draws, 0, repetitions=20) if r["method"] == "neural_minus_all"]
    assert [r["difference"] for r in rows] == [.5, 1., 0., .5]
    assert all(r["n_directional_queries"] == 2 and r["n_triples"] == 1 for r in rows)
