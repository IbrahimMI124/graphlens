# Phase 5: graph-perturbation validation

All five prepared graphs were reconstructed from training-only seeds and matched exactly. Original held-out queries, candidate vocabularies and evaluator positive filters are fixed.

| condition | n_edges | n_isolated | mean_degree | relation_frequency_total_variation | global_typed_twohop_walks | target_incident_edges_removed |
| --- | --- | --- | --- | --- | --- | --- |
| original | 32888 | 0 | 32.338250 | 0.000000 | 688733 | 0 |
| random_global | 29599 | 0 | 29.104228 | 0.003038 | 560486 | 654 |
| random_relation_stratified | 29599 | 0 | 29.104228 | 0.000195 | 560470 | 634 |
| targeted_local | 29599 | 0 | 29.104228 | 0.016060 | 507626 | 3289 |
| targeted_relation_matched_control | 29599 | 0 | 29.104228 | 0.016060 | 546113 | 787 |

Targeted and relation-matched control graphs remove exactly the same number of edges per relation. Their endpoint/degree/path distributions may differ; matching relation counts does not hold every entity-specific regularity fixed.

Random relation-stratified removal preserves relation proportions up to integer rounding. Global-random removal does not constrain those proportions. None of the graphs isolates an entity in this prepared 90% cohort.

Typed walk counts include different edge-label sequences and may revisit nodes. They follow only forward h-to-t edges and exclude inverse-oriented rule bodies, so they do not measure all relational evidence or native groundings. Query-endpoint counts require the held-out answer and are diagnostic only. Actual native rule groundings are checked separately against the training edge sets. See graph-query-features.csv for every original/modified test fact.
