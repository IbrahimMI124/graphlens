# Phase 5: measured changes and training-only rule witnesses

Cases are illustrative. Predictions come from the fresh paired experiment, while witness catalogs are explicitly labelled. A missing training edge is not a false fact: original positives remain evaluator filters. Neural rank changes are measured sensitivity, not invented internal explanations. Zero-body priors have no body grounding and are excluded from this witness collection.

## targeted_local — targeted_known_endpoint_changed — test:0:head

Query `(?, P27, Q142)`; correct triple `Q206832 P27 Q142`.

ComplEx rank: 1225.0 → 1729.0; all-rule rank: None → 5. Native rule abstentions have no rank.

Original/new neural top predictions: `[['Q159642', 0.05248230695724487], ['Q184535', 0.05245891213417053]]` → `[['Q55796', 0.037404678761959076], ['Q310048', 0.036082059144973755]]`.

Original/new rule top predictions: `[]` → `[['Q152824', 0.30339805825242716], ['Q112307', 0.30339805825242716]]`.

Training head/tail degrees: 13/325 → 12/176; relation frequency 1648 → 1198. Directed typed two-/three-hop walks to the correct endpoint: 2/3 → 1/1. Endpoint walk counts use the answer and are evaluation diagnostics.

No sampled native conditional-rule witness was available; this is not a negative logical judgment.

Witnesses are sampled (first three rules, first two groundings per candidate/catalog), not a complete count of supporting instantiations.

## targeted_relation_matched_control — targeted_known_endpoint_changed — test:0:head

Query `(?, P27, Q142)`; correct triple `Q206832 P27 Q142`.

ComplEx rank: 1225.0 → 1832.0; all-rule rank: None → 2. Native rule abstentions have no rank.

Original/new neural top predictions: `[['Q159642', 0.05248230695724487], ['Q184535', 0.05245891213417053]]` → `[['Q184535', 0.04139915853738785], ['Q188111', 0.03864346444606781]]`.

Original/new rule top predictions: `[]` → `[['Q8772', 0.6285714285714286], ['Q206832', 0.6285714285714286]]`.

Training head/tail degrees: 13/325 → 13/289; relation frequency 1648 → 1198. Directed typed two-/three-hop walks to the correct endpoint: 2/3 → 2/3. Endpoint walk counts use the answer and are evaluation diagnostics.

No sampled native conditional-rule witness was available; this is not a negative logical judgment.

Witnesses are sampled (first three rules, first two groundings per candidate/catalog), not a complete count of supporting instantiations.

