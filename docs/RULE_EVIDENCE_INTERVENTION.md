# Direct rule-body evidence intervention on CoDEx-S

The neighbourhood deletion study found that graph targeting alone did not reliably remove rule evidence. This design targets training edges that instantiate the frozen AnyBURL variable-only general rules. It compares against deletion with exactly the same number of removed edges in each joint stratum of relation and the two original endpoint log2 degree bins. The control samples uniformly within those strata. The design fixes 90% retention for both arms.

For each of three fixed draws, sample 384 original training facts to score edges, and 384 different training facts for the audit. A grounding that includes its own head fact is excluded. Each scoring fact has equal weight. Its weight is split over native B groundings, then over the distinct body edges in each grounding. Within each stratum, delete the highest scoring edges. Quotas are proportional to original stratum sizes and rounded by largest remainder. Control randomness and ties are seeded independently. The three (removal, training probe split) seed pairs are (751, 1711), (752, 1712), and (753, 1713). No test or validation facts are provided to edge selection or the audit.

The audit measures the mean per-fact fraction of original groundings destroyed, with equal weight for facts with at least one nontrivial grounding. Require at least a five percentage point targeted-minus-matched difference on each independent training audit before starting the full matrix. A failed gate is reported as a result about this design. Smoke and full run directories are separate.

For each eligible graph pair, retrain three ComplEx seeds and mine two independent AnyBURL inventories on each arm with the prior validated budgets. Evaluate original held-out queries and evaluator filters. Report the paired change in the ComplEx minus all-rule AnyBURL Hits@1 gap, alongside individual and family-specific ranking outcomes. Reapply the frozen general and constant catalogs to both graphs and the original. After masked ranking, measure actual lost general rule groundings for held-out facts and verify that surviving groundings equal fresh native enumeration. Report any difference between grounding loss and loss of all generated evidence. The test grounding diagnostic never determines deletions or the training gate.

Matching relation and endpoint degree bins leaves within-bin degree, individual entity frequencies, other paths, and score tie breaking free to change. The contrast estimates this intervention under the paired protocol. The test comparisons remain exploratory because CoDEx-S has already been inspected.

## Second design after the incidence pilot

The first pilot's additive edge scores can prioritize multiple edges in the same
grounding. A second, separate pilot scores how much **still-surviving grounding
mass** each edge would destroy. Select the edge with greatest marginal loss
among strata whose quotas have room, update surviving mass, and repeat. An
instance with two deleted body edges is counted once. Each fitting fact has
unit mass shared across its native groundings. The design uses 1,152 fitting
facts and 384 disjoint audit facts per draw and excludes every fact sampled as
a fit or audit probe in the incidence pilot. The fixed (removal, probe) seeds
are (851, 1811), (852, 1812), and (853, 1813). The same retention, matching and
five-point gate apply. This is a training-only revision motivated by the first
pilot. It uses the same fixed catalog and no validation or test outcomes.
